#!/usr/bin/env python3
"""
boomi_pull.py
--------------
Pull component XML and dependencies from AtomSphere.

Usage:
  python scripts/boomi_pull.py --component-id "uuid-here"
  python scripts/boomi_pull.py --component-id "uuid-here" --with-dependencies
  python scripts/boomi_pull.py --name "CLAIMS-INBOUND-IMRIGHT-REST"
  python scripts/boomi_pull.py --folder-id "folder-uuid-here"
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc


def find_component_by_name(name: str) -> str:
    payload = {"QueryFilter": {"expression": {"argument": [name], "operator": "EQUALS", "property": "name"}}}
    resp = requests.post(bc.api_url("Component/query"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code == 200:
        results = resp.json().get("result", [])
        if not results:
            print(f"❌ No component found with name: {name}")
            sys.exit(1)
        if len(results) > 1:
            print(f"⚠️  Multiple components found with name '{name}':")
            for r in results:
                print(f"   {r.get('componentId')} — {r.get('name')} ({r.get('type')})")
            sys.exit(1)
        return results[0]["componentId"]
    print(f"❌ Name search failed: HTTP {resp.status_code}")
    sys.exit(1)


def get_component_xml(component_id: str) -> str:
    resp = requests.get(bc.api_url(f"Component/{component_id}"), headers=bc.headers(accept="application/xml"), **bc.requests_kwargs())
    if resp.status_code == 200:
        return resp.text
    print(f"❌ Failed to fetch component {component_id}: HTTP {resp.status_code}\n   {resp.text[:300]}")
    sys.exit(1)


def get_component_metadata(component_id: str) -> dict:
    resp = requests.get(bc.api_url(f"Component/{component_id}"), headers=bc.headers(), **bc.requests_kwargs())
    return resp.json() if resp.status_code == 200 else {}


def get_component_references(component_id: str) -> list[dict]:
    payload = {"QueryFilter": {"expression": {"argument": [component_id], "operator": "EQUALS", "property": "usedByComponentId"}}}
    resp = requests.post(bc.api_url("Component/query"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    return resp.json().get("result", []) if resp.status_code == 200 else []


def get_folder_components(folder_id: str) -> list[dict]:
    payload = {"QueryFilter": {"expression": {"argument": [folder_id], "operator": "EQUALS", "property": "folderId"}}}
    resp = requests.post(bc.api_url("Component/query"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code == 200:
        return resp.json().get("result", [])
    print(f"❌ Folder query failed: HTTP {resp.status_code}")
    sys.exit(1)


def save_component(component_id: str, output_dir: str, meta: dict | None = None) -> tuple[str, str, str]:
    if not meta:
        meta = get_component_metadata(component_id)
    name = meta.get("name", component_id)
    comp_type = meta.get("type", "unknown")
    safe_name = name.replace("/", "_").replace("\\", "_").replace(":", "_")
    out_path = Path(output_dir) / f"{safe_name}.xml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(get_component_xml(component_id), encoding="utf-8")
    return name, comp_type, str(out_path)


def pull(component_id, name, folder_id, with_dependencies, output_dir):
    bc.validate_env()
    print(f"\n{'='*60}\n  📥 Boomi Component Pull  —  Account: {bc.BOOMI_ACCOUNT_ID}\n{'='*60}\n")
    pulled = []

    if name and not component_id:
        print(f"  🔍 Searching for component: {name}")
        component_id = find_component_by_name(name)
        print(f"     Found: {component_id}")

    if folder_id:
        print(f"  📂 Fetching all components in folder: {folder_id}")
        folder_components = get_folder_components(folder_id)
        print(f"     Found {len(folder_components)} components")
        for comp in folder_components:
            n, t, p = save_component(comp["componentId"], output_dir, meta=comp)
            pulled.append((n, t, p))
            print(f"     ✅ {t:12} {n}")
    elif component_id:
        meta = get_component_metadata(component_id)
        n, t, p = save_component(component_id, output_dir, meta=meta)
        pulled.append((n, t, p))
        print(f"  ✅ Pulled: {t} — {n}")

        if with_dependencies:
            print(f"\n  🔗 Fetching dependencies...")
            deps = get_component_references(component_id)
            if deps:
                for dep in deps:
                    dep_id = dep.get("componentId")
                    if dep_id and dep_id != component_id:
                        dn, dt, dp = save_component(dep_id, output_dir, meta=get_component_metadata(dep_id))
                        pulled.append((dn, dt, dp))
                        print(f"     ✅ {dt:12} {dn} (dependency)")
            else:
                print("     No dependencies found (connection credentials never included, by design)")

    bc.log_activity("pull", name or component_id or folder_id, result="success", details=f"{len(pulled)} components")

    print(f"\n{'='*60}\n  SUMMARY: {len(pulled)} component(s) pulled")
    for n, t, p in pulled:
        print(f"    {t:12} → {p}")
    print(f"\n  To redeploy: python scripts/boomi_deploy.py --file [path] --env STG")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull Boomi components from AtomSphere")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--component-id")
    group.add_argument("--name")
    group.add_argument("--folder-id")
    parser.add_argument("--with-dependencies", action="store_true")
    parser.add_argument("--output", default="migration-output/pulled-components")
    args = parser.parse_args()

    pull(args.component_id, args.name, args.folder_id, args.with_dependencies, args.output)
