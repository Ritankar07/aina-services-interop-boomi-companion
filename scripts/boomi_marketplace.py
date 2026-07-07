#!/usr/bin/env python3
"""
boomi_marketplace.py
----------------------
Search the public Boomi Marketplace GraphQL API and optionally install a
recipe bundle into AtomSphere via the Platform API.

Usage:
  python scripts/boomi_marketplace.py --search "Salesforce to database"
  python scripts/boomi_marketplace.py --list-folders
  python scripts/boomi_marketplace.py --install BC-12345 --folder-id <guid>

Requirements: pip install requests python-dotenv
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc

MARKETPLACE_GRAPHQL_URL = "https://marketplace.boomi.com/graphql"


def search_recipes(query: str, limit: int = 10) -> list[dict]:
    """Search the public Marketplace GraphQL API. No auth required."""
    graphql_query = """
    query SearchRecipes($search: String!, $first: Int!) {
      recipes(search: $search, first: $first) {
        nodes {
          bundleId
          name
          description
          connectors
          categories
          rating
          installs
        }
      }
    }
    """
    resp = requests.post(
        MARKETPLACE_GRAPHQL_URL,
        json={"query": graphql_query, "variables": {"search": query, "first": limit}},
    )
    if resp.status_code != 200:
        print(f"❌ Marketplace search failed: HTTP {resp.status_code}")
        return []
    data = resp.json()
    return data.get("data", {}).get("recipes", {}).get("nodes", [])


def list_folders() -> list[dict]:
    """List AtomSphere folders (requires bc-integration credentials)."""
    bc.validate_env()
    resp = requests.get(bc.api_url("Folder/"), headers=bc.headers(), **bc.requests_kwargs())
    if resp.status_code == 200:
        return resp.json().get("result", [])
    print(f"❌ Folder list failed: HTTP {resp.status_code}")
    return []


def install_recipe(bundle_id: str, folder_id: str) -> dict:
    """Install a marketplace recipe bundle into the specified folder."""
    bc.validate_env()
    payload = {"bundleId": bundle_id, "folderId": folder_id}
    resp = requests.post(bc.api_url("MarketplaceInstall/"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code in (200, 201):
        return resp.json()
    print(f"❌ Install failed: HTTP {resp.status_code}\n   {resp.text[:300]}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Search and install Boomi Marketplace recipes")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", help="Search term, e.g. 'Salesforce to database'")
    group.add_argument("--list-folders", action="store_true")
    group.add_argument("--install", metavar="BUNDLE_ID")
    parser.add_argument("--folder-id", help="Target folder for --install")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    print(f"\n{'='*60}\n  🛒 Boomi Marketplace\n{'='*60}\n")

    if args.search:
        print(f"  Searching: \"{args.search}\"\n")
        results = search_recipes(args.search, args.limit)
        if not results:
            print("  No recipes found.")
            return
        print(f"  {'#':<3}{'Bundle ID':<14}{'Name':<35}{'Rating':<8}{'Installs'}")
        print(f"  {'-'*70}")
        for i, r in enumerate(results, 1):
            print(f"  {i:<3}{r.get('bundleId','?'):<14}{r.get('name','?')[:34]:<35}{r.get('rating','—'):<8}{r.get('installs','—')}")
            if r.get("description"):
                print(f"      {r['description'][:90]}")
            if r.get("connectors"):
                print(f"      Connectors: {', '.join(r['connectors'])}")
        print(f"\n  To install: python scripts/boomi_marketplace.py --install <BUNDLE_ID> --folder-id <FOLDER_ID>")
        print(f"  To list your folders first: python scripts/boomi_marketplace.py --list-folders\n")

    elif args.list_folders:
        folders = list_folders()
        if not folders:
            print("  (no folders found)")
        else:
            for f in sorted(folders, key=lambda x: x.get("name", "")):
                print(f"    {f.get('name','?'):<40} {f.get('id','?')}")
        print()

    elif args.install:
        if not args.folder_id:
            print("❌ --folder-id is required for --install")
            sys.exit(1)
        print(f"  Installing {args.install} into folder {args.folder_id}...")
        result = install_recipe(args.install, args.folder_id)
        bc.log_activity("marketplace-install", args.install, result="success")
        print(f"  ✅ Installed. Response: {result}")
        print(f"\n  Pull installed components: python scripts/boomi_pull.py --folder-id {args.folder_id} --output migration-output/marketplace-recipes/\n")


if __name__ == "__main__":
    main()
