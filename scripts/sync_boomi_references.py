#!/usr/bin/env python3
"""
sync_boomi_references.py
--------------------------
Checks the official OfficialBoomi/bc-integration repository for updates to the
Boomi Companion reference files and syncs any changes into the local references/ folder.

How it works:
  1. Calls GitHub's tree API (1 request) to get the SHA of every file in the
     official repo's references/ folder.
  2. Compares those SHAs against a local state file (.references-sync-state.json).
  3. Reports: ADDED (new files), MODIFIED (content changed), DELETED (removed upstream).
  4. With --apply: downloads changed files via raw.githubusercontent.com and updates state.

GitHub SHA note: these are git blob SHAs — they change only when the file content
changes. Unchanged files have the same SHA regardless of when you check.

Usage:
  # Check what has changed since last sync (no downloads)
  python scripts/sync_boomi_references.py --check

  # Check AND download all changes
  python scripts/sync_boomi_references.py --apply

  # Re-download every file regardless of SHA (full refresh)
  python scripts/sync_boomi_references.py --apply --force

  # Use a GitHub token to avoid the 60 req/hour anonymous rate limit
  python scripts/sync_boomi_references.py --check --token ghp_yourtoken

  # Or set GITHUB_TOKEN in your .env / environment
  export GITHUB_TOKEN=ghp_yourtoken

Requirements: pip install requests python-dotenv
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ─── Config ──────────────────────────────────────────────────────────────────

PROJECT_ROOT   = Path(__file__).parent.parent
LOCAL_REF_ROOT = PROJECT_ROOT / "references"
STATE_FILE     = LOCAL_REF_ROOT / ".sync-state.json"

REPO_OWNER     = "OfficialBoomi"
REPO_NAME      = "bc-integration"
BRANCH         = "main"
# Path inside the repo where the skill references live
SKILL_REF_PATH = "skills/boomi-integration/references"

GITHUB_API     = "https://api.github.com"
RAW_BASE       = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


# ─── GitHub helpers ───────────────────────────────────────────────────────────

def _api_headers(token: str | None) -> dict:
    h = {"Accept": "application/vnd.github+json"}
    tok = token or os.getenv("GITHUB_TOKEN", "")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def get_remote_tree(token: str | None) -> list[dict] | None:
    """
    Fetch the full recursive git tree for the repo.
    Returns only the .md files inside SKILL_REF_PATH.
    Uses 1 GitHub API request regardless of how many files exist.
    """
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{BRANCH}?recursive=1"
    resp = requests.get(url, headers=_api_headers(token), timeout=20)

    if resp.status_code == 200:
        data = resp.json()
        if data.get("truncated"):
            print("  ⚠️  GitHub tree response was truncated (very large repo). "
                  "Some files may be missed. Use --token to increase rate limits.")
        return [
            item for item in data.get("tree", [])
            if item["type"] == "blob"
            and item["path"].startswith(f"{SKILL_REF_PATH}/")
            and item["path"].endswith(".md")
        ]
    elif resp.status_code == 403:
        print("  ❌ GitHub API rate limit hit.")
        print("     Set GITHUB_TOKEN in your .env or pass --token to use authenticated requests.")
        print("     Anonymous limit: 60 req/hour. Authenticated: 5,000 req/hour.")
        return None
    else:
        print(f"  ❌ GitHub API error: HTTP {resp.status_code}")
        print(f"     {resp.text[:300]}")
        return None


def download_file(skill_relative_path: str) -> str | None:
    """Download raw file content from GitHub. No rate limit on raw.githubusercontent.com."""
    url = f"{RAW_BASE}/{SKILL_REF_PATH}/{skill_relative_path}"
    resp = requests.get(url, timeout=20)
    if resp.status_code == 200:
        return resp.text
    print(f"  ❌ Download failed ({resp.status_code}): {skill_relative_path}")
    return None


# ─── State management ─────────────────────────────────────────────────────────

def load_state() -> dict:
    """Load the last-sync state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "last_synced": None,
        "repo": f"{REPO_OWNER}/{REPO_NAME}",
        "branch": BRANCH,
        "files": {}
    }


def save_state(state: dict):
    """Write the sync state to disk."""
    state["last_synced"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def skill_path_to_local(skill_path: str) -> Path:
    """
    Convert a skill-repo path like
    'skills/boomi-integration/references/components/map_component.md'
    to our local path like
    references/components/map_component.md
    """
    rel = skill_path[len(f"{SKILL_REF_PATH}/"):]   # strip the skill prefix
    return LOCAL_REF_ROOT / rel


# ─── Diff logic ──────────────────────────────────────────────────────────────

def compute_diff(
    remote_files: list[dict],
    local_state: dict,
    force: bool
) -> dict:
    """
    Compare remote tree SHAs against local state.
    Returns:
      {
        "added":    [(skill_path, sha), ...],   # in remote, not in state
        "modified": [(skill_path, sha), ...],   # SHA changed
        "deleted":  [skill_path, ...],          # in state, not in remote
        "unchanged": int,
      }
    """
    remote_map = {
        item["path"]: item["sha"]
        for item in remote_files
    }
    local_map  = local_state.get("files", {})

    added    = []
    modified = []
    deleted  = []
    unchanged = 0

    for path, sha in remote_map.items():
        if path not in local_map:
            added.append((path, sha))
        elif local_map[path] != sha or force:
            modified.append((path, sha))
        else:
            unchanged += 1

    for path in local_map:
        if path not in remote_map:
            deleted.append(path)

    return {
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "unchanged": unchanged,
    }


def print_diff_report(diff: dict, last_synced: str | None):
    print(f"\n  Last synced : {last_synced or 'never'}")
    print(f"  Unchanged   : {diff['unchanged']} file(s)")
    print()

    if diff["added"]:
        print(f"  ✨ ADDED ({len(diff['added'])} new file(s) in official repo):")
        for path, _ in sorted(diff["added"]):
            rel = path[len(f"{SKILL_REF_PATH}/"):]
            print(f"     + {rel}")

    if diff["modified"]:
        print(f"\n  📝 MODIFIED ({len(diff['modified'])} file(s) changed upstream):")
        for path, _ in sorted(diff["modified"]):
            rel = path[len(f"{SKILL_REF_PATH}/"):]
            print(f"     ~ {rel}")

    if diff["deleted"]:
        print(f"\n  🗑️  DELETED ({len(diff['deleted'])} file(s) removed from official repo):")
        for path in sorted(diff["deleted"]):
            rel = path[len(f"{SKILL_REF_PATH}/"):]
            print(f"     - {rel}")

    if not diff["added"] and not diff["modified"] and not diff["deleted"]:
        print("  ✅ Everything is up to date. No changes in the official repo.")


# ─── Apply changes ────────────────────────────────────────────────────────────

def apply_diff(diff: dict, state: dict, dry_run: bool = False):
    """Download added/modified files and update state."""
    files_to_download = diff["added"] + diff["modified"]

    if not files_to_download and not diff["deleted"]:
        return

    downloaded = 0
    failed     = 0

    for skill_path, sha in files_to_download:
        rel = skill_path[len(f"{SKILL_REF_PATH}/"):]
        local = skill_path_to_local(skill_path)

        if dry_run:
            print(f"  [DRY RUN] Would download: {rel}")
            continue

        content = download_file(rel)
        if content is not None:
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(content, encoding="utf-8")
            state["files"][skill_path] = sha
            downloaded += 1
            action = "added" if skill_path in [p for p, _ in diff["added"]] else "updated"
            print(f"  ✅ {action}: {rel}")
            time.sleep(0.2)   # polite delay
        else:
            failed += 1

    # Handle deleted files — remove from state but keep local file
    # (user should decide whether to delete local copies of removed upstream files)
    for skill_path in diff["deleted"]:
        rel = skill_path[len(f"{SKILL_REF_PATH}/"):]
        local = skill_path_to_local(skill_path)
        if skill_path in state["files"]:
            del state["files"][skill_path]
        if not dry_run:
            print(f"  ⚠️  Upstream DELETED: {rel}")
            print(f"     Local copy kept at: references/{rel}")
            print(f"     Delete manually if no longer needed.")

    if not dry_run:
        print(f"\n  Downloaded : {downloaded} file(s)")
        if failed:
            print(f"  Failed     : {failed} file(s)")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Check OfficialBoomi/bc-integration for reference updates and sync locally"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="Show what has changed since last sync (no downloads)")
    mode.add_argument("--apply", action="store_true",
                      help="Download all changes from the official repo")

    parser.add_argument("--force", action="store_true",
                        help="Re-download every file even if SHA matches (full refresh)")
    parser.add_argument("--token",
                        help="GitHub Personal Access Token (or set GITHUB_TOKEN in .env). "
                             "Increases rate limit from 60 to 5,000 requests/hour.")
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  🔄 Boomi Reference Sync")
    print(f"     Source: github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"     Path  : {SKILL_REF_PATH}/")
    print(f"     Mode  : {'CHECK only' if args.check else 'APPLY changes'}")
    if args.force:
        print(f"     Force : re-download all files")
    print(f"{'='*65}\n")

    # 1. Get the remote tree (1 API call)
    print("  Fetching file tree from official repo...")
    remote_files = get_remote_tree(args.token)
    if remote_files is None:
        sys.exit(1)
    print(f"  Found {len(remote_files)} reference file(s) in official repo.")

    # 2. Load local state
    state = load_state()

    # 3. Compute diff
    diff = compute_diff(remote_files, state, force=args.force)

    # 4. Report
    print_diff_report(diff, state.get("last_synced"))

    total_changes = len(diff["added"]) + len(diff["modified"]) + len(diff["deleted"])

    if args.check:
        if total_changes:
            print(f"\n  Run with --apply to download these {total_changes} change(s).")
        print()
        return

    # 5. Apply if requested
    if total_changes == 0 and not args.force:
        print("\n  Nothing to download.\n")
        return

    print(f"\n  Downloading {len(diff['added']) + len(diff['modified'])} file(s)...")
    apply_diff(diff, state, dry_run=False)

    # 6. Save updated state
    # Add any files not yet in state (first-time run)
    for item in remote_files:
        if item["path"] not in state["files"]:
            state["files"][item["path"]] = item["sha"]
    save_state(state)

    print(f"\n  State saved to: references/.sync-state.json")
    print(f"\n  ✅ Sync complete. Restart VS Code to re-index the updated reference files.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
