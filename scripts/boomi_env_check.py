#!/usr/bin/env python3
"""
boomi_env_check.py
--------------------
Check which .env variables are set, without printing their actual values.
Matches the verified official bc-integration credential model:
BOOMI_API_URL + BOOMI_USERNAME + BOOMI_API_TOKEN (raw, not base64) + BOOMI_ACCOUNT_ID.

Usage:
  python scripts/boomi_env_check.py
  python scripts/boomi_env_check.py --verbose
  python scripts/boomi_env_check.py --test-auth
"""

import argparse
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc

REQUIRED = {
    "BOOMI_API_URL":    "Boomi platform API root (e.g. https://api.boomi.com)",
    "BOOMI_USERNAME":   "Your platform email address",
    "BOOMI_API_TOKEN":  "Platform API Token (raw, generated in Settings — NOT base64)",
    "BOOMI_ACCOUNT_ID": "Your platform account ID",
}

OPTIONAL = {
    "BOOMI_VERIFY_SSL":            "SSL certificate verification (default: true)",
    "BOOMI_TARGET_FOLDER":         "Default folder GUID for new components",
    "BOOMI_ENVIRONMENT_ID":        "Single runtime environment ID",
    "BOOMI_ENVIRONMENT_ID_STG":    "Staging environment ID (this workspace's extension)",
    "BOOMI_ENVIRONMENT_ID_PROD":   "Production environment ID (this workspace's extension)",
    "BOOMI_TEST_ATOM_ID":          "Atom/runtime ID for test execution",
    "SERVER_AUTH_TYPE":            "WSS testing — basic | bearer | none",
    "SERVER_BASE_URL":             "WSS testing — your atom's shared web server URL",
    "SERVER_USERNAME":             "WSS testing — basic auth username",
    "SERVER_TOKEN":                "WSS testing — basic auth token",
    "SERVER_BEARER_TOKEN":         "WSS testing — bearer token",
    "SERVER_VERIFY_SSL":           "WSS testing — SSL verification (default: false)",
    "BOOMI_COMPANION_LOG_ACTIVITY":"Opt-in activity logging (set to 1 to enable)",
    "CONFLUENCE_BASE_URL":         "Confluence Cloud base URL",
    "CONFLUENCE_USER":             "Confluence account email",
    "CONFLUENCE_API_TOKEN":        "Atlassian API token",
}


def mask(value: str, verbose: bool) -> str:
    if not value:
        return "❌ NOT SET"
    if verbose:
        return f"✅ SET  (length: {len(value)}, starts with: '{value[:2]}...')"
    return "✅ SET"


def test_auth() -> bool:
    """Make a lightweight API call to verify credentials work end-to-end."""
    if not all([bc.BOOMI_API_URL, bc.BOOMI_USERNAME, bc.BOOMI_API_TOKEN, bc.BOOMI_ACCOUNT_ID]):
        print("  ❌ Cannot test auth — one or more required variables not set")
        return False

    url = bc.api_url("Atom/query")
    payload = {"QueryFilter": {"expression": {"argument": ["CLOUD"], "operator": "EQUALS", "property": "type"}}}
    try:
        resp = requests.post(url, headers=bc.headers(), json=payload, timeout=10, **bc.requests_kwargs())
        if resp.status_code == 200:
            count = len(resp.json().get("result", []))
            print(f"  ✅ AUTH VALID — API responded with {count} atom(s)")
            return True
        elif resp.status_code == 401:
            print(f"  ❌ AUTH FAILED — HTTP 401 Unauthorized")
            print(f"     Check BOOMI_USERNAME and BOOMI_API_TOKEN — both must be the raw")
            print(f"     plain values from Boomi Settings, NOT pre-base64-encoded.")
            return False
        elif resp.status_code == 403:
            print(f"  ❌ AUTH FAILED — HTTP 403 Forbidden (token valid, account access denied)")
            return False
        else:
            print(f"  ⚠️  Unexpected response: HTTP {resp.status_code}")
            print(f"     {resp.text[:200]}")
            return False
    except requests.exceptions.SSLError:
        print("  ❌ SSL error — if using a self-signed cert, set BOOMI_VERIFY_SSL=false")
        return False
    except requests.exceptions.ConnectionError:
        print("  ❌ Connection error — check network access to api.boomi.com")
        return False
    except requests.exceptions.Timeout:
        print("  ⚠️  Request timed out — Boomi API may be slow")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check .env variables (without revealing values)")
    parser.add_argument("--verbose", action="store_true", help="Show value length and prefix")
    parser.add_argument("--test-auth", action="store_true", help="Make a live API call to verify credentials")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  🔐 Boomi Environment Variable Check")
    print(f"     .env file: {bc.PROJECT_ROOT / '.env'}")
    print(f"{'='*60}\n")

    all_ok = True

    print("  REQUIRED VARIABLES:")
    for var, desc in REQUIRED.items():
        value = os.getenv(var, "")
        if not value:
            all_ok = False
        print(f"  {'✅' if value else '❌'} {var:<22} {desc}")
        print(f"     → {mask(value, args.verbose)}")
    print()

    print("  OPTIONAL VARIABLES:")
    for var, desc in OPTIONAL.items():
        value = os.getenv(var, "")
        print(f"  {'✅' if value else '⚠️ '} {var:<28} {desc}")
        print(f"     → {mask(value, args.verbose)}")
    print()

    print(f"{'='*60}")
    if all_ok:
        print(f"  ✅ All required variables are set")
    else:
        print(f"  ❌ Some required variables are MISSING")
        print(f"     Copy .env.template to .env and fill in the values")

    activity_status = "ENABLED" if bc.LOG_ACTIVITY else "disabled (opt-in — set BOOMI_COMPANION_LOG_ACTIVITY=1 to enable)"
    print(f"\n  📝 Activity logging: {activity_status}")

    if args.test_auth:
        print(f"\n  🧪 Testing live API authentication...")
        if not test_auth():
            all_ok = False

    print(f"{'='*60}\n")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
