#!/usr/bin/env python3
"""
boomi_push.py
--------------
Push a Boomi component XML file to AtomSphere (create or update the component).
This is Step 1 only — it does NOT package or deploy.
Run boomi_deploy.py afterward with the returned component ID to package and deploy.

Why two steps?
  boomi_push.py   → gets the component into AtomSphere (you can review it in the UI)
  boomi_deploy.py → packages it and releases it to an environment (STG or PROD)

Usage:
  # Push a single component
  python scripts/boomi_push.py --file migration-output/boomi-processes/MyProcess/MyProcess.xml

  # Push all XML files in a folder
  python scripts/boomi_push.py --folder migration-output/boomi-processes/MyProcess/

  # Push with a specific folder placement in AtomSphere
  python scripts/boomi_push.py --file MyProcess.xml --folder-id <guid>

  # Dry run — validate without touching AtomSphere
  python scripts/boomi_push.py --file MyProcess.xml --dry-run

Output:
  Prints the component ID(s) — paste these into boomi_deploy.py with --component-id

Requirements: pip install requests python-dotenv
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc


# ─── XML helpers ────────────────────────────────────────────────────────────

def validate_no_placeholders(xml_path: Path) -> list[str]:
    """Block push if any PLACEHOLDER_ tokens remain unfilled."""
    content = xml_path.read_text(encoding="utf-8")
    return [line.strip() for line in content.splitlines() if "PLACEHOLDER_" in line]


def inject_folder_id(xml_content: str, folder_id: str) -> str:
    """Inject or replace folderId on the root Component element."""
    already = re.search(r'folderId="([^"]+)"', xml_content)
    if already:
        existing = already.group(1)
        if existing == folder_id:
            return xml_content
        print(f"   ↳ Replacing existing folderId '{existing}' with '{folder_id}'")
        return xml_content.replace(f'folderId="{existing}"', f'folderId="{folder_id}"')

    injected = re.sub(
        r'(<bns:Component\b[^>]*?)(>|\s*/>)',
        lambda m: m.group(1) + f' folderId="{folder_id}"' + m.group(2),
        xml_content, count=1
    )
    if injected == xml_content:  # fallback: no namespace prefix
        injected = re.sub(
            r'(<Component\b[^>]*?)(>|\s*/>)',
            lambda m: m.group(1) + f' folderId="{folder_id}"' + m.group(2),
            xml_content, count=1
        )
    return injected


def get_component_name(xml_path: Path) -> str:
    """Extract the component name from the XML file."""
    try:
        root = ET.parse(xml_path).getroot()
        return root.attrib.get("name", xml_path.stem)
    except ET.ParseError:
        return xml_path.stem


# ─── Platform API helpers ────────────────────────────────────────────────────

def find_existing_component(component_name: str) -> dict | None:
    """Check if a component with this name already exists on the platform."""
    payload = {
        "QueryFilter": {
            "expression": {
                "operator": "and",
                "nestedExpression": [
                    {"argument": [component_name], "operator": "EQUALS", "property": "name"},
                    {"argument": ["process"],       "operator": "EQUALS", "property": "type"},
                ]
            }
        }
    }
    resp = requests.post(
        bc.api_url("Component/query"),
        headers=bc.headers(),
        json=payload,
        **bc.requests_kwargs()
    )
    if resp.status_code == 200:
        results = resp.json().get("result", [])
        return results[0] if results else None
    return None


def _apply_known_fix(xml_content: str, error_msg: str) -> tuple[bool, str, str]:
    """Apply a known auto-fix for common platform validation errors before retrying."""
    if "${" in xml_content and ("invalid" in error_msg.lower() or "syntax" in error_msg.lower()):
        fixed = re.sub(r'\$\{[^}]+\}', '', xml_content)
        if fixed != xml_content:
            return True, fixed, "Removed unsupported ${ENV_VAR} syntax"

    if "durableId" in error_msg or "0x7FFFFFFF" in error_msg:
        import random
        fixed = re.sub(
            r'durableId="\d+"',
            lambda _: f'durableId="{random.randint(1, 0x7FFFFFFE)}"',
            xml_content
        )
        if fixed != xml_content:
            return True, fixed, "Regenerated out-of-range durableId values"

    if "xml:space" in error_msg or "whitespace" in error_msg.lower():
        fixed = re.sub(r'<w:t>(\s+)', r'<w:t xml:space="preserve">\1', xml_content)
        if fixed != xml_content:
            return True, fixed, "Added xml:space='preserve' to whitespace text elements"

    return False, xml_content, ""


def push_component_xml(
    xml_content: str,
    component_name: str,
    component_id: str | None = None,
    max_retries: int = 2
) -> str:
    """
    POST component XML to AtomSphere. Create if component_id is None, update otherwise.
    Returns the component ID on success.
    Auto-retries with known fixes on validation errors.
    """
    path = f"Component/{component_id}" if component_id else "Component/"
    action = "UPDATE" if component_id else "CREATE"

    last_error = None
    for attempt in range(1, max_retries + 2):
        resp = requests.post(
            bc.api_url(path),
            headers=bc.headers(content_type="application/xml"),
            data=xml_content.encode("utf-8"),
            **bc.requests_kwargs()
        )

        if resp.status_code in (200, 201):
            returned_id = resp.json().get("componentId") or component_id
            return returned_id

        try:
            error_msg = resp.json().get("message", resp.text[:400])
        except Exception:
            error_msg = resp.text[:400]

        last_error = error_msg
        print(f"   ⚠️  Attempt {attempt} failed: HTTP {resp.status_code}")
        print(f"      Error: {error_msg[:180]}")

        if attempt > max_retries:
            break

        fixed, xml_content, description = _apply_known_fix(xml_content, error_msg)
        if fixed:
            print(f"   🔧 Auto-fix applied: {description} — retrying...")
        else:
            print(f"   ❌ No auto-fix available for this error.")
            break

    print(f"\n❌ {action} failed after {max_retries + 1} attempt(s).")
    print(f"   Last error: {last_error}")
    print(f"\n   Manual options:")
    print(f"   - Open AtomSphere → Component Explorer → Import XML manually")
    print(f"   - Paste error into Copilot Chat with /debug for diagnosis")
    return ""


# ─── Push single file ────────────────────────────────────────────────────────

def push_file(
    xml_path: Path,
    folder_id: str | None,
    dry_run: bool
) -> str | None:
    """Push a single XML component file to AtomSphere. Returns component ID or None."""

    print(f"\n  📄 {xml_path.name}")

    # Validate — no placeholders allowed
    placeholders = validate_no_placeholders(xml_path)
    if placeholders:
        print(f"   ❌ Blocked — {len(placeholders)} unfilled PLACEHOLDER_ token(s):")
        for p in placeholders[:5]:
            print(f"      {p}")
        print(f"   Fill all PLACEHOLDER_ values before pushing.")
        return None

    xml_content = xml_path.read_text(encoding="utf-8")

    # Inject folder if provided
    effective_folder = folder_id or bc.BOOMI_TARGET_FOLDER
    if effective_folder:
        xml_content = inject_folder_id(xml_content, effective_folder)
        print(f"   📁 folderId: {effective_folder}")

    component_name = get_component_name(xml_path)
    print(f"   📦 Component name: {component_name}")

    if dry_run:
        print(f"   [DRY RUN] Would push to AtomSphere — no changes made")
        return "DRY-RUN-COMPONENT-ID"

    # Check if component already exists
    existing = find_existing_component(component_name)
    if existing:
        component_id = existing["componentId"]
        print(f"   🔄 Updating existing component (ID: {component_id})")
    else:
        component_id = None
        print(f"   ✨ Creating new component")

    returned_id = push_component_xml(xml_content, component_name, component_id)

    if returned_id:
        print(f"   ✅ Pushed successfully")
        print(f"      Component ID: {returned_id}")
        bc.log_activity(
            "push", component_name,
            result="success",
            details=f"componentId={returned_id} folder={effective_folder or 'none'}"
        )
    return returned_id or None


# ─── Push folder ─────────────────────────────────────────────────────────────

def push_folder(folder: Path, folder_id: str | None, dry_run: bool) -> dict[str, str]:
    """Push all XML files in a folder. Returns {filename: component_id}."""
    xml_files = sorted([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() == ".xml"])
    if not xml_files:
        print(f"❌ No .xml files found in {folder}")
        sys.exit(1)

    print(f"\n  📂 Pushing {len(xml_files)} XML file(s) from {folder.name}/")
    results = {}
    for f in xml_files:
        cid = push_file(f, folder_id, dry_run)
        if cid:
            results[f.name] = cid
    return results


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Push Boomi component XML to AtomSphere (create/update only — no packaging or deployment)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file",   help="Path to a single Boomi component XML file")
    group.add_argument("--folder", help="Path to a folder — pushes all .xml files inside it")

    parser.add_argument(
        "--folder-id",
        help="AtomSphere folder GUID. Overrides BOOMI_TARGET_FOLDER in .env. "
             "Get this from: python scripts/boomi_folder.py --path 'YOUR/PATH' --create-if-missing"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate inputs and print what would happen, without touching AtomSphere"
    )

    args = parser.parse_args()
    bc.validate_env()

    print("\n" + "=" * 60)
    print("📤 Boomi Component Push")
    print(f"   Account  : {bc.BOOMI_ACCOUNT_ID}")
    print(f"   Folder ID: {args.folder_id or bc.BOOMI_TARGET_FOLDER or '(none — using XML value)'}")
    print(f"   Dry Run  : {args.dry_run}")
    print("=" * 60)

    if args.file:
        xml_path = Path(args.file).resolve()
        if not xml_path.exists():
            print(f"❌ File not found: {xml_path}")
            sys.exit(1)
        component_id = push_file(xml_path, args.folder_id, args.dry_run)
        if component_id and not args.dry_run:
            print("\n" + "=" * 60)
            print("✅ PUSH COMPLETE")
            print(f"   Component is now in AtomSphere.")
            print(f"   Review it in Component Explorer before deploying.")
            print(f"\n   To deploy to STG, run:")
            print(f"   python scripts/boomi_deploy.py --component-id {component_id} --env STG")
            print("=" * 60)

    elif args.folder:
        folder = Path(args.folder).resolve()
        if not folder.is_dir():
            print(f"❌ Folder not found: {folder}")
            sys.exit(1)
        results = push_folder(folder, args.folder_id, args.dry_run)
        if results and not args.dry_run:
            print("\n" + "=" * 60)
            print(f"✅ PUSH COMPLETE — {len(results)} component(s) pushed")
            print(f"\n   Component IDs (use with boomi_deploy.py --component-id):")
            for filename, cid in results.items():
                print(f"   {cid}   ← {filename}")
            print(f"\n   To deploy all to STG:")
            for cid in results.values():
                print(f"   python scripts/boomi_deploy.py --component-id {cid} --env STG")
            print("=" * 60)


if __name__ == "__main__":
    main()
