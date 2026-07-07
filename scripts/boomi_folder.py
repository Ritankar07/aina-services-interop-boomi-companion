#!/usr/bin/env python3
"""
boomi_folder.py
----------------
Resolve an AtomSphere folder path (e.g. "CLAIMS/INBOUND") to a folder ID,
creating intermediate folders if they don't exist.

Usage:
  python scripts/boomi_folder.py --path "CLAIMS/INBOUND" --create-if-missing
  python scripts/boomi_folder.py --list
  python scripts/boomi_folder.py --list --parent-id <guid>
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc


def list_folders(parent_id: str | None = None) -> list[dict]:
    prop_val = parent_id if parent_id else "0"
    payload = {"QueryFilter": {"expression": {
        "argument": [prop_val], "operator": "EQUALS", "property": "parentFolderId"
    }}}
    resp = requests.post(bc.api_url("Folder/query"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code == 200:
        return resp.json().get("result", [])
    resp2 = requests.get(bc.api_url("Folder/"), headers=bc.headers(), **bc.requests_kwargs())
    if resp2.status_code == 200:
        all_folders = resp2.json().get("result", [])
        if parent_id:
            return [f for f in all_folders if f.get("parentFolderId") == parent_id]
        return [f for f in all_folders if not f.get("parentFolderId") or f.get("parentFolderId") == "0"]
    return []


def find_folder_by_name(name: str, parent_id: str | None = None) -> dict | None:
    for folder in list_folders(parent_id):
        if folder.get("name", "").lower() == name.lower():
            return folder
    return None


def create_folder(name: str, parent_id: str | None = None) -> dict:
    payload: dict = {"name": name}
    if parent_id:
        payload["parentFolderId"] = parent_id
    resp = requests.post(bc.api_url("Folder/"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code in (200, 201):
        return resp.json()
    print(f"❌ Failed to create folder '{name}': HTTP {resp.status_code}\n   {resp.text[:300]}")
    sys.exit(1)


def resolve_path(path_str: str, create_missing: bool) -> tuple[str, list[str]]:
    segments = [s.strip() for s in path_str.replace("\\", "/").split("/") if s.strip()]
    if not segments:
        print("❌ Empty folder path.")
        sys.exit(1)

    current_parent_id = None
    created = []
    for i, segment in enumerate(segments):
        folder = find_folder_by_name(segment, current_parent_id)
        if folder:
            current_parent_id = folder["id"]
            status = "found"
        elif create_missing:
            folder = create_folder(segment, current_parent_id)
            current_parent_id = folder["id"]
            created.append(segment)
            status = "created"
        else:
            print(f"\n❌ Folder not found: '{' > '.join(segments[:i+1])}'")
            print(f"   Run with --create-if-missing to create it automatically.")
            sys.exit(1)
        print(f"  {'  '*i}{'📁' if status=='found' else '✨'} {segment} ({status})  →  ID: {current_parent_id}")

    return current_parent_id, created


def main():
    parser = argparse.ArgumentParser(description="Resolve or create Boomi AtomSphere folder paths")
    parser.add_argument("--path", help="Folder path, e.g. 'CLAIMS/INBOUND'")
    parser.add_argument("--create-if-missing", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--parent-id")
    args = parser.parse_args()

    bc.validate_env()
    print(f"\n{'='*60}\n  📁 Boomi Folder Manager\n     Account: {bc.BOOMI_ACCOUNT_ID}\n{'='*60}\n")

    if args.list:
        folders = list_folders(args.parent_id)
        if not folders:
            print("  (no folders found)")
        else:
            for f in sorted(folders, key=lambda x: x.get("name", "").lower()):
                print(f"    {f.get('name','?')}  →  {f.get('id','?')}")
        print()
        return

    if not args.path:
        parser.print_help()
        sys.exit(1)

    print(f"  Resolving path: {args.path}  (create_if_missing={args.create_if_missing})\n")
    folder_id, created = resolve_path(args.path, args.create_if_missing)
    bc.log_activity("folder-resolve", args.path, result="success", details=f"folderId={folder_id}")

    print(f"\n{'='*60}\n  ✅ FOLDER RESOLVED\n     Path      : {args.path}\n     Folder ID : {folder_id}")
    if created:
        print(f"     Created   : {', '.join(created)}")
    print(f"{'='*60}\n")
    print(f"  Use this with deploy:")
    print(f"      python scripts/boomi_deploy.py --file [file.xml] --folder-id {folder_id} --env STG\n")
    print(f"  Or set as default in .env:  BOOMI_TARGET_FOLDER={folder_id}\n")


if __name__ == "__main__":
    main()
