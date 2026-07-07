#!/usr/bin/env python3
"""
boomi_deploy.py
----------------
Deploy a Boomi component XML file to AtomSphere: create/update component,
package it, and deploy to STG or PROD. Uses corrected, verified credential
model from boomi_common.py.

Usage:
  python scripts/boomi_deploy.py --file path/to/Process.xml --env STG
  python scripts/boomi_deploy.py --file path/to/Process.xml --env PROD
  python scripts/boomi_deploy.py --file path/to/Process.xml --env STG --folder-id <guid>
  python scripts/boomi_deploy.py --file path/to/Process.xml --env STG --dry-run

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


# ─── XML helpers ────────────────────────────────────────────────────────────

def inject_folder_id(xml_content: str, folder_id: str) -> str:
    """Inject or replace folderId on the root <bns:Component> element."""
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


def validate_xml_has_no_placeholders(xml_path: Path) -> list[str]:
    content = xml_path.read_text(encoding="utf-8")
    return [line.strip() for line in content.splitlines() if "PLACEHOLDER_" in line]


def get_component_name_from_xml(xml_path: Path) -> str:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return root.attrib.get("name", xml_path.stem)


# ─── Auto-fix patterns (validation-error retry) ────────────────────────────

def _apply_validation_fix(xml_content: str, error_msg: str) -> tuple[bool, str, str]:
    if "xml:space" in error_msg or "whitespace" in error_msg.lower():
        fixed = re.sub(r'<w:t>(\s+)', r'<w:t xml:space="preserve">\1', xml_content)
        if fixed != xml_content:
            return True, fixed, "Added xml:space='preserve' to text elements with leading whitespace"

    if "${" in xml_content and ("invalid" in error_msg.lower() or "syntax" in error_msg.lower()):
        fixed = re.sub(r'\$\{[^}]+\}', '', xml_content)
        if fixed != xml_content:
            return True, fixed, "Removed unsupported ${ENV_VAR} syntax — use Boomi process properties instead"

    if "durableId" in error_msg or "0x7FFFFFFF" in error_msg:
        import random
        fixed = re.sub(r'durableId="\d+"', lambda m: f'durableId="{random.randint(1, 0x7FFFFFFE)}"', xml_content)
        if fixed != xml_content:
            return True, fixed, "Regenerated durableId values (were out of valid range)"

    if "dragpoint" in error_msg.lower():
        return False, xml_content, ""  # needs manual shape correction, can't auto-fix structurally

    return False, xml_content, ""


def _post_with_retry(path: str, xml_content: str, component_name: str, max_retries: int = 2) -> dict:
    last_error = None
    for attempt in range(1, max_retries + 2):
        response = requests.post(
            bc.api_url(path), headers=bc.headers(content_type="application/xml"),
            data=xml_content.encode("utf-8"), **bc.requests_kwargs()
        )
        if response.status_code in (200, 201):
            return response.json()

        try:
            err = response.json()
            error_msg = err.get("message", response.text[:500])
        except Exception:
            error_msg = response.text[:500]

        last_error = error_msg
        print(f"  ⚠️  Attempt {attempt} failed: HTTP {response.status_code}")
        print(f"     Error: {error_msg[:200]}")

        if attempt > max_retries:
            break

        fixed, xml_content, fix_description = _apply_validation_fix(xml_content, error_msg)
        if fixed:
            print(f"  🔧 Auto-fix applied: {fix_description}")
            print(f"  → Retrying (attempt {attempt + 1})...")
        else:
            print(f"  ❌ No auto-fix available for this error. Manual correction required.")
            break

    bc.log_activity("deploy", component_name, result="failed", details=str(last_error)[:300])
    print(f"\n❌ Component push failed after {max_retries + 1} attempt(s).")
    print(f"   Last error: {last_error}")
    print(f"\n   Try:")
    print(f"   - Validate the XML is well-formed and has <dragpoints> on every shape")
    print(f"   - Import manually via AtomSphere → Component Explorer → Import")
    print(f"   - Run /debug in Copilot Chat with the error above for diagnosis")
    sys.exit(1)


def create_component(xml_content: str, component_name: str) -> dict:
    print(f"  → Creating new component: {component_name}")
    return _post_with_retry("Component/", xml_content, component_name)


def update_component(component_id: str, xml_content: str, component_name: str) -> dict:
    print(f"  → Updating existing component: {component_name} (ID: {component_id})")
    return _post_with_retry(f"Component/{component_id}", xml_content, component_name)


def get_component_by_name(component_name: str) -> dict | None:
    payload = {
        "QueryFilter": {"expression": {"operator": "and", "nestedExpression": [
            {"argument": [component_name], "operator": "EQUALS", "property": "name"},
            {"argument": ["process"], "operator": "EQUALS", "property": "type"},
        ]}}
    }
    resp = requests.post(bc.api_url("Component/query"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code == 200:
        results = resp.json().get("result", [])
        return results[0] if results else None
    return None


def create_packaged_component(component_id: str, version_notes: str) -> dict:
    print(f"  → Creating packaged component...")
    payload = {
        "componentId": component_id,
        "packageVersion": datetime.now().strftime("%Y%m%d.%H%M"),
        "notes": version_notes,
        "componentType": "process",
    }
    resp = requests.post(bc.api_url("PackagedComponent/"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    resp.raise_for_status()
    return resp.json()


def deploy_packaged_component(packaged_component_id: str, environment_id: str) -> dict:
    print(f"  → Deploying packaged component to environment {environment_id}...")
    payload = {"environmentId": environment_id, "packagedComponentId": packaged_component_id}
    resp = requests.post(bc.api_url("DeployedPackage/"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    resp.raise_for_status()
    return resp.json()


# ─── Main flow ──────────────────────────────────────────────────────────────

def deploy(xml_path: Path, environment: str, folder_id: str | None, dry_run: bool):
    print("\n" + "=" * 60)
    print(f"🚀 Boomi Deploy Script")
    print(f"   File      : {xml_path}")
    print(f"   Target Env: {environment}")
    print(f"   Dry Run   : {dry_run}")
    print("=" * 60)

    bc.validate_env()
    env_id = bc.resolve_environment_id(environment)

    if environment.upper() == "PROD":
        print("\n⚠️  WARNING: Deploying to PRODUCTION. Are you sure? (yes/no): ", end="")
        if input().strip().lower() != "yes":
            print("❌ PROD deployment cancelled.")
            sys.exit(0)

    if not xml_path.exists():
        print(f"❌ File not found: {xml_path}")
        sys.exit(1)

    placeholders = validate_xml_has_no_placeholders(xml_path)
    if placeholders:
        print(f"\n❌ XML contains {len(placeholders)} unfilled PLACEHOLDER_ token(s):")
        for p in placeholders[:10]:
            print(f"   {p}")
        print("\n  Fill all PLACEHOLDER_ values before deploying.")
        sys.exit(1)
    print(f"\n✅ Credential check passed (no PLACEHOLDERs found)")

    xml_content = xml_path.read_text(encoding="utf-8")

    # Resolve folder: explicit --folder-id > BOOMI_TARGET_FOLDER default > none
    effective_folder = folder_id or bc.BOOMI_TARGET_FOLDER
    if effective_folder:
        print(f"\n📁 Injecting folderId: {effective_folder}")
        xml_content = inject_folder_id(xml_content, effective_folder)
        print(f"   ✅ folderId injected")
    else:
        print(f"\n⚠️  No folder ID provided and BOOMI_TARGET_FOLDER not set in .env")
        print(f"   Component will use whatever folderId (if any) is already in the XML.")

    component_name = get_component_name_from_xml(xml_path)
    print(f"\n📦 Component name: {component_name}")

    if dry_run:
        print("\n[DRY RUN] No changes made to AtomSphere.")
        return

    print(f"\n🔍 Checking if component exists in AtomSphere...")
    existing = get_component_by_name(component_name)

    if existing:
        component_id = existing["componentId"]
        component_result = update_component(component_id, xml_content, component_name)
    else:
        component_result = create_component(xml_content, component_name)
        component_id = component_result.get("componentId")

    if not component_id:
        print(f"❌ Failed to get component ID from AtomSphere response: {component_result}")
        sys.exit(1)
    print(f"  ✅ Component ID: {component_id}")

    version_notes = f"Auto-deployed via boomi_deploy.py on {datetime.now().isoformat()} — {environment}"
    packaged = create_packaged_component(component_id, version_notes)
    packaged_id = packaged.get("packagedComponentId")
    if not packaged_id:
        print(f"❌ Packaging failed. Response: {packaged}")
        sys.exit(1)
    print(f"  ✅ Packaged Component ID: {packaged_id}")

    deployment = deploy_packaged_component(packaged_id, env_id)
    deployment_id = deployment.get("deployedPackageId") or deployment.get("id")
    print(f"  ✅ Deployed. Deployment ID: {deployment_id}")

    bc.log_activity("deploy", component_name, env=environment, result="success",
                     details=f"componentId={component_id} deploymentId={deployment_id}")

    print(f"\n🎉 SUCCESS: {component_name} deployed to {environment}")
    print(f"   View in AtomSphere: Deploy → Deployments → {environment}")
    print(f"   Check logs in: Manage → Process Reporting\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy a Boomi component XML to AtomSphere")
    parser.add_argument("--file", required=True, help="Path to the Boomi component XML file")
    parser.add_argument("--env", choices=["STG", "PROD"], default="STG", help="Target environment")
    parser.add_argument("--folder-id", help="AtomSphere folder GUID (overrides BOOMI_TARGET_FOLDER)")
    parser.add_argument("--dry-run", action="store_true", help="Validate without making changes")
    args = parser.parse_args()

    deploy(Path(args.file).resolve(), args.env, args.folder_id, args.dry_run)
