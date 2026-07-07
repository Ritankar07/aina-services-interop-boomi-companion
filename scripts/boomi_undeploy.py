#!/usr/bin/env python3
"""
boomi_undeploy.py
-------------------
Remove a deployed component from an AtomSphere environment.

Usage:
  python scripts/boomi_undeploy.py --name "CLAIMS-INBOUND-IMRIGHT-REST" --env STG
  python scripts/boomi_undeploy.py --deployment-id "abc123" --env STG
  python scripts/boomi_undeploy.py --name "PROCESS-NAME" --env STG --dry-run
  python scripts/boomi_undeploy.py --list --env STG
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc


def list_deployments(env_id: str) -> list[dict]:
    payload = {"QueryFilter": {"expression": {"argument": [env_id], "operator": "EQUALS", "property": "environmentId"}}}
    resp = requests.post(bc.api_url("DeployedPackage/query"), headers=bc.headers(), json=payload, **bc.requests_kwargs())
    if resp.status_code == 200:
        return resp.json().get("result", [])
    print(f"❌ Failed to list deployments: HTTP {resp.status_code}")
    return []


def find_deployment_by_name(component_name: str, env_id: str) -> dict | None:
    for dep in list_deployments(env_id):
        if dep.get("componentName", "").lower() == component_name.lower():
            return dep
    return None


def undeploy(deployment_id: str, dry_run: bool) -> bool:
    if dry_run:
        print(f"  [DRY RUN] Would DELETE DeployedPackage/{deployment_id}")
        return True
    resp = requests.delete(bc.api_url(f"DeployedPackage/{deployment_id}"), headers=bc.headers(), **bc.requests_kwargs())
    if resp.status_code in (200, 204):
        return True
    print(f"  ❌ Undeploy failed: HTTP {resp.status_code}\n     {resp.text[:300]}")
    return False


def print_deployments(deployments: list[dict], env_label: str):
    print(f"\n  Current deployments in {env_label}:\n")
    if not deployments:
        print("  (no deployments found)")
        return
    print(f"  {'Deployment ID':<38} {'Component Name':<45} {'Version'}")
    print(f"  {'-'*38} {'-'*45} {'-'*10}")
    for dep in sorted(deployments, key=lambda d: d.get("componentName", "")):
        dep_id = dep.get("deployedPackageId") or dep.get("id") or "?"
        print(f"  {dep_id:<38} {dep.get('componentName','?')[:44]:<45} {dep.get('packageVersion','?')}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Undeploy a Boomi component from an environment")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name")
    group.add_argument("--deployment-id")
    group.add_argument("--list", action="store_true")
    parser.add_argument("--env", choices=["STG", "PROD"], default="STG")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    bc.validate_env()
    env_id = bc.resolve_environment_id(args.env)
    env_label = args.env.upper()

    print(f"\n{'='*60}\n  🗑️  Boomi Undeploy Script\n     Environment : {env_label}\n     Dry Run     : {args.dry_run}\n{'='*60}\n")

    if args.list:
        print_deployments(list_deployments(env_id), env_label)
        return

    if env_label == "PROD":
        print("⚠️  WARNING: Undeploying from PRODUCTION. Are you sure? (yes/no): ", end="")
        if input().strip().lower() != "yes":
            print("❌ PROD undeploy cancelled.")
            sys.exit(0)

    if args.deployment_id:
        deployment_id = args.deployment_id
        print(f"  Using provided Deployment ID: {deployment_id}")
    else:
        print(f"  Looking up '{args.name}' in {env_label}...")
        dep = find_deployment_by_name(args.name, env_id)
        if not dep:
            print(f"  ❌ No deployment found for '{args.name}' in {env_label}\n     Run --list to see current deployments.")
            sys.exit(1)
        deployment_id = dep.get("deployedPackageId") or dep.get("id")
        print(f"  ✅ Found: {dep.get('componentName')} (Deployment ID: {deployment_id})")

    print(f"\n  Undeploying from {env_label}...")
    success = undeploy(deployment_id, args.dry_run)
    bc.log_activity("undeploy", args.name or args.deployment_id, env=env_label,
                     result="success" if success else "failed")

    if success:
        action = "would be undeployed" if args.dry_run else "successfully undeployed"
        print(f"\n{'='*60}\n  ✅ {action} from {env_label}")
        print(f"     Redeploy with: python scripts/boomi_deploy.py --file [...] --env {env_label}")
        print(f"{'='*60}\n")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
