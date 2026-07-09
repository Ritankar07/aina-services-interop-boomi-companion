#!/usr/bin/env python3
"""
boomi_deploy.py
----------------
Package and deploy a Boomi component to an environment (STG or PROD).

RECOMMENDED two-step flow:
  Step 1  python scripts/boomi_push.py --file MyProcess.xml     ← push to platform, get component ID
  Step 2  python scripts/boomi_deploy.py --component-id <ID> --env STG  ← package + deploy

All-in-one flow (push + package + deploy in one command):
  python scripts/boomi_deploy.py --file MyProcess.xml --env STG

Usage:
  # Recommended: deploy a component already pushed via boomi_push.py
  python scripts/boomi_deploy.py --component-id abc-123 --env STG
  python scripts/boomi_deploy.py --component-id abc-123 --env PROD

  # All-in-one: push + package + deploy from an XML file
  python scripts/boomi_deploy.py --file migration-output/boomi-processes/MyProcess/MyProcess.xml --env STG

  # Dry run
  python scripts/boomi_deploy.py --component-id abc-123 --env STG --dry-run

Requirements: pip install requests python-dotenv
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc


# ─── XML helpers (only used in all-in-one --file mode) ──────────────────────

def inject_folder_id(xml_content: str, folder_id: str) -> str:
    already = re.search(r'folderId="([^"]+)"', xml_content)
    if already:
        existing = already.group(1)
        if existing == folder_id:
            return xml_content
        return xml_content.replace(f'folderId="{existing}"', f'folderId="{folder_id}"')
    injected = re.sub(
        r'(<bns:Component\b[^>]*?)(>|\s*/>)',
        lambda m: m.group(1) + f' folderId="{folder_id}"' + m.group(2),
        xml_content, count=1
    )
    if injected == xml_content:
        injected = re.sub(
            r'(<Component\b[^>]*?)(>|\s*/>)',
            lambda m: m.group(1) + f' folderId="{folder_id}"' + m.group(2),
            xml_content, count=1
        )
    return injected


def validate_no_placeholders(xml_path: Path) -> list[str]:
    content = xml_path.read_text(encoding="utf-8")
    return [line.strip() for line in content.splitlines() if "PLACEHOLDER_" in line]


def get_component_name_from_xml(xml_path: Path) -> str:
    try:
        root = ET.parse(xml_path).getroot()
        return root.attrib.get("name", xml_path.stem)
    except ET.ParseError:
        return xml_path.stem


def _apply_fix(xml_content: str, error_msg: str) -> tuple[bool, str, str]:
    if "${" in xml_content and ("invalid" in error_msg.lower() or "syntax" in error_msg.lower()):
        fixed = re.sub(r'\$\{[^}]+\}', '', xml_content)
        if fixed != xml_content:
            return True, fixed, "Removed unsupported ${ENV_VAR} syntax"
    if "durableId" in error_msg or "0x7FFFFFFF" in error_msg:
        import random
        fixed = re.sub(r'durableId="\d+"', lambda _: f'durableId="{random.randint(1, 0x7FFFFFFE)}"', xml_content)
        if fixed != xml_content:
            return True, fixed, "Regenerated out-of-range durableId values"
    if "xml:space" in error_msg or "whitespace" in error_msg.lower():
        fixed = re.sub(r'<w:t>(\s+)', r'<w:t xml:space="preserve">\1', xml_content)
        if fixed != xml_content:
            return True, fixed, "Added xml:space='preserve' to whitespace text elements"
    return False, xml_content, ""


def _push_xml(path: str, xml_content: str, component_name: str, max_retries: int = 2) -> dict:
    """POST XML to AtomSphere with auto-retry on known validation errors."""
    last_error = None
    for attempt in range(1, max_retries + 2):
        resp = requests.post(
            bc.api_url(path),
            headers=bc.headers(content_type="application/xml"),
            data=xml_content.encode("utf-8"),
            **bc.requests_kwargs()
        )
        if resp.status_code in (200, 201):
            return resp.json()
        try:
            error_msg = resp.json().get("message", resp.text[:400])
        except Exception:
            error_msg = resp.text[:400]
        last_error = error_msg
        print(f"  ⚠️  Attempt {attempt} failed: HTTP {resp.status_code} — {error_msg[:160]}")
        if attempt > max_retries:
            break
        fixed, xml_content, desc = _apply_fix(xml_content, error_msg)
        if fixed:
            print(f"  🔧 Auto-fix applied: {desc} — retrying...")
        else:
            print(f"  ❌ No auto-fix available.")
            break
    bc.log_activity("push", component_name, result="failed", details=str(last_error)[:300])
    print(f"\n❌ Component push failed: {last_error}")
    print(f"   Try running boomi_push.py first — it has better error reporting.")
    print(f"   Or import manually via AtomSphere → Component Explorer → Import")
    sys.exit(1)


def push_from_file(xml_path: Path, folder_id: str | None) -> str:
    """
    Push XML to AtomSphere (create or update). Returns component ID.
    This is the --file fallback path — the recommended path is boomi_push.py first.
    """
    placeholders = validate_no_placeholders(xml_path)
    if placeholders:
        print(f"\n❌ XML contains {len(placeholders)} unfilled PLACEHOLDER_ token(s):")
        for p in placeholders[:10]:
            print(f"   {p}")
        print("\n  Fill all PLACEHOLDER_ values before deploying.")
        sys.exit(1)
    print(f"\n✅ No PLACEHOLDER_ tokens found")

    xml_content = xml_path.read_text(encoding="utf-8")
    effective_folder = folder_id or bc.BOOMI_TARGET_FOLDER
    if effective_folder:
        print(f"\n📁 Injecting folderId: {effective_folder}")
        xml_content = inject_folder_id(xml_content, effective_folder)

    component_name = get_component_name_from_xml(xml_path)
    print(f"\n📦 Component: {component_name}")
    print(f"   Checking if it already exists in AtomSphere...")

    payload = {
        "QueryFilter": {"expression": {"operator": "and", "nestedExpression": [
            {"argument": [component_name], "operator": "EQUALS", "property": "name"},
            {"argument": ["process"],       "operator": "EQUALS", "property": "type"},
        ]}}
    }
    resp = requests.post(bc.api_url("Component/query"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    existing = resp.json().get("result", []) if resp.status_code == 200 else []

    if existing:
        cid = existing[0]["componentId"]
        print(f"   → Updating existing component (ID: {cid})")
        result = _push_xml(f"Component/{cid}", xml_content, component_name)
    else:
        print(f"   → Creating new component")
        result = _push_xml("Component/", xml_content, component_name)
        cid = result.get("componentId")

    if not cid:
        print(f"❌ No component ID returned from AtomSphere: {result}")
        sys.exit(1)

    print(f"  ✅ Component in AtomSphere. ID: {cid}")
    return cid


# ─── Package + Deploy (the main job of this script) ─────────────────────────

def create_packaged_component(component_id: str, env_label: str) -> str:
    """Package the component and return the packaged component ID."""
    print(f"\n📦 Packaging component {component_id}...")
    payload = {
        "componentId": component_id,
        "packageVersion": datetime.now().strftime("%Y%m%d.%H%M"),
        "notes": f"Packaged via boomi_deploy.py on {datetime.now().isoformat()} — {env_label}",
        "componentType": "process",
    }
    resp = requests.post(bc.api_url("PackagedComponent/"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    resp.raise_for_status()
    packaged_id = resp.json().get("packagedComponentId")
    if not packaged_id:
        print(f"❌ Packaging failed. Response: {resp.json()}")
        sys.exit(1)
    print(f"  ✅ Packaged Component ID: {packaged_id}")
    return packaged_id


def deploy_to_environment(packaged_id: str, env_id: str) -> str:
    """Deploy the packaged component to an environment. Returns deployment ID."""
    print(f"\n🚀 Deploying to environment {env_id}...")
    payload = {"environmentId": env_id, "packagedComponentId": packaged_id}
    resp = requests.post(bc.api_url("DeployedPackage/"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    resp.raise_for_status()
    deployment_id = resp.json().get("deployedPackageId") or resp.json().get("id")
    print(f"  ✅ Deployment ID: {deployment_id}")
    return deployment_id


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Package and deploy a Boomi component to STG or PROD.\n"
                    "Recommended: run boomi_push.py first to get the component ID, then use --component-id here."
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--component-id",
        help="Component ID from boomi_push.py. Skips the push step — packages and deploys only. RECOMMENDED."
    )
    source.add_argument(
        "--file",
        help="Path to Boomi component XML. Pushes + packages + deploys in one step (all-in-one fallback)."
    )

    parser.add_argument("--env", choices=["STG", "PROD"], default="STG", help="Target environment (default: STG)")
    parser.add_argument("--folder-id", help="AtomSphere folder GUID (only used with --file)")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print plan without making changes")

    args = parser.parse_args()
    bc.validate_env()
    env_id = bc.resolve_environment_id(args.env)

    print("\n" + "=" * 60)
    print(f"🚀 Boomi Deploy Script")
    print(f"   Mode      : {'component-id (push already done)' if args.component_id else 'all-in-one (push + package + deploy)'}")
    print(f"   Target Env: {args.env}")
    print(f"   Dry Run   : {args.dry_run}")
    print("=" * 60)

    # PROD safety gate
    if args.env.upper() == "PROD" and not args.dry_run:
        print("\n⚠️  WARNING: Deploying to PRODUCTION.")
        print("   Have you validated this on STG first? (yes/no): ", end="")
        if input().strip().lower() != "yes":
            print("❌ PROD deployment cancelled.")
            sys.exit(0)

    # Resolve the component ID
    if args.component_id:
        # Recommended path: component already pushed via boomi_push.py
        component_id = args.component_id
        print(f"\n📦 Using component ID: {component_id}")
        print(f"   (Component was already pushed to AtomSphere via boomi_push.py)")
    else:
        # All-in-one fallback: push from file first
        xml_path = Path(args.file).resolve()
        if not xml_path.exists():
            print(f"❌ File not found: {xml_path}")
            sys.exit(1)
        print(f"\n⚠️  Running in all-in-one mode (push + package + deploy).")
        print(f"   Recommended: use boomi_push.py first to review the component,")
        print(f"   then run: boomi_deploy.py --component-id <ID> --env {args.env}")
        component_id = push_from_file(xml_path, args.folder_id)

    if args.dry_run:
        print(f"\n[DRY RUN] Would package component {component_id} and deploy to {args.env}.")
        print(f"[DRY RUN] No changes made.")
        return

    # Package the component
    packaged_id = create_packaged_component(component_id, args.env)

    # Deploy to environment
    deployment_id = deploy_to_environment(packaged_id, env_id)

    bc.log_activity(
        "deploy", component_id,
        env=args.env, result="success",
        details=f"packagedComponentId={packaged_id} deploymentId={deployment_id}"
    )

    print(f"\n{'=' * 60}")
    print(f"✅ DEPLOY COMPLETE")
    print(f"   Component    : {component_id}")
    print(f"   Environment  : {args.env}")
    print(f"   Deployment ID: {deployment_id}")
    print(f"\n   Review in AtomSphere:")
    print(f"   Deploy → Deployments → {args.env}")
    print(f"\n   Check execution logs:")
    print(f"   python scripts/boomi_logs.py --status ERROR --hours 1")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
