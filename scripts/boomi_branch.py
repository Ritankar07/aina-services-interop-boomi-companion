#!/usr/bin/env python3
"""
boomi_branch.py
-----------------
Manage AtomSphere Git branches for component version control.

Usage:
  python scripts/boomi_branch.py --list
  python scripts/boomi_branch.py --create "feature/claims-v2"
  python scripts/boomi_branch.py --current
  python scripts/boomi_branch.py --set "feature/claims-v2"
  python scripts/boomi_branch.py --status
"""

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc

BRANCH_STATE_FILE = bc.PROJECT_ROOT / ".active-branch.json"


def read_branch_state() -> dict:
    if BRANCH_STATE_FILE.exists():
        try:
            return json.loads(BRANCH_STATE_FILE.read_text())
        except Exception:
            pass
    return {"branchName": "main", "branchId": None}


def write_branch_state(name: str, branch_id: str | None):
    BRANCH_STATE_FILE.write_text(json.dumps({"branchName": name, "branchId": branch_id}, indent=2))


def list_branches() -> list[dict]:
    resp = requests.get(bc.api_url("Branch/"), headers=bc.headers(), **bc.requests_kwargs())
    if resp.status_code == 200:
        return resp.json().get("result", [])
    resp2 = requests.post(bc.api_url("Branch/query"), headers=bc.headers(), json={"QueryFilter": {}}, **bc.requests_kwargs())
    return resp2.json().get("result", []) if resp2.status_code == 200 else []


def find_branch_by_name(name: str) -> dict | None:
    for b in list_branches():
        if b.get("name", "").lower() == name.lower():
            return b
    return None


def create_branch(name: str, source_branch_name: str) -> dict:
    source = find_branch_by_name(source_branch_name)
    payload = {"name": name}
    if source:
        payload["parentBranchId"] = source.get("id")
    resp = requests.post(bc.api_url("Branch/"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code in (200, 201):
        return resp.json()
    print(f"❌ Failed to create branch '{name}': HTTP {resp.status_code}\n   {resp.text[:300]}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Manage AtomSphere branches")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--current", action="store_true")
    group.add_argument("--create", metavar="BRANCH_NAME")
    group.add_argument("--set", metavar="BRANCH_NAME")
    group.add_argument("--status", action="store_true")
    parser.add_argument("--from", dest="from_branch", default="main")
    args = parser.parse_args()

    bc.validate_env()
    print(f"\n{'='*60}\n  🌿 Boomi Branch Manager  —  Account: {bc.BOOMI_ACCOUNT_ID}\n{'='*60}\n")
    state = read_branch_state()

    if args.list:
        branches = list_branches()
        if not branches:
            print("  No branches found. Account may be in single-branch mode (main only).")
            return
        current = state.get("branchName", "main")
        print(f"  {'Name':<40} {'ID'}")
        print(f"  {'-'*55}")
        for b in sorted(branches, key=lambda x: x.get("name", "")):
            marker = "* " if b.get("name") == current else "  "
            print(f"  {marker}{b.get('name','?'):<38} {b.get('id','?')}")
        print(f"\n  (* = active branch in this workspace)")

    elif args.current:
        print(f"  Active branch : {state.get('branchName', 'main')}")
        print(f"  Branch ID     : {state.get('branchId') or '(not resolved — run --set to refresh)'}")

    elif args.create:
        print(f"  Creating branch: '{args.create}' from '{args.from_branch}'")
        result = create_branch(args.create, args.from_branch)
        print(f"  ✅ Created: {args.create} (ID: {result.get('id')})")
        print(f"\n  To switch: python scripts/boomi_branch.py --set \"{args.create}\"")
        bc.log_activity("branch-create", args.create, result="success")

    elif args.set:
        branch = find_branch_by_name(args.set)
        if branch:
            write_branch_state(args.set, branch.get("id"))
            print(f"  ✅ Active branch set to: {args.set} (ID: {branch.get('id')})")
        elif args.set.lower() == "main":
            write_branch_state("main", None)
            print(f"  ✅ Active branch set to: main (default)")
        else:
            print(f"  ❌ Branch '{args.set}' not found. Run --list or --create.")
            sys.exit(1)
        bc.log_activity("branch-set", args.set, result="success")

    elif args.status:
        print(f"  Active branch : {state.get('branchName', 'main')}")
        print(f"  Branch ID     : {state.get('branchId') or '(main/default)'}")
        print(f"  State file    : {BRANCH_STATE_FILE}  (exists: {BRANCH_STATE_FILE.exists()})")

    print()


if __name__ == "__main__":
    main()
