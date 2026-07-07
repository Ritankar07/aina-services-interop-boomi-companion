"""
boomi_common.py
-----------------
Shared credential loading, auth header construction, and activity logging
for all boomi_*.py scripts in this workspace.

Matches the verified official bc-integration .env variable names exactly:
  BOOMI_API_URL, BOOMI_USERNAME, BOOMI_API_TOKEN, BOOMI_ACCOUNT_ID,
  BOOMI_VERIFY_SSL, BOOMI_TARGET_FOLDER, BOOMI_ENVIRONMENT_ID,
  BOOMI_TEST_ATOM_ID, BOOMI_COMPANION_LOG_ACTIVITY

Extends with this workspace's STG/PROD safety convention:
  BOOMI_ENVIRONMENT_ID_STG, BOOMI_ENVIRONMENT_ID_PROD
"""

import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# ─── Credentials (matches official bc-integration naming) ──────────────────
BOOMI_API_URL    = os.getenv("BOOMI_API_URL", "https://api.boomi.com").rstrip("/")
BOOMI_USERNAME   = os.getenv("BOOMI_USERNAME", "")
BOOMI_API_TOKEN  = os.getenv("BOOMI_API_TOKEN", "")  # raw token, NOT base64
BOOMI_ACCOUNT_ID = os.getenv("BOOMI_ACCOUNT_ID", "")
BOOMI_VERIFY_SSL = os.getenv("BOOMI_VERIFY_SSL", "true").lower() != "false"

BOOMI_TARGET_FOLDER  = os.getenv("BOOMI_TARGET_FOLDER", "")
BOOMI_ENVIRONMENT_ID = os.getenv("BOOMI_ENVIRONMENT_ID", "")
BOOMI_TEST_ATOM_ID   = os.getenv("BOOMI_TEST_ATOM_ID", "")

# This workspace's STG/PROD extension on top of the official single-env var
BOOMI_ENVIRONMENT_ID_STG  = os.getenv("BOOMI_ENVIRONMENT_ID_STG", BOOMI_ENVIRONMENT_ID)
BOOMI_ENVIRONMENT_ID_PROD = os.getenv("BOOMI_ENVIRONMENT_ID_PROD", "")

LOG_ACTIVITY = os.getenv("BOOMI_COMPANION_LOG_ACTIVITY", "0") == "1"
ACTIVITY_LOG_FILE = PROJECT_ROOT / ".activity-log" / "activity.jsonl"

REQUIRED_VARS = ["BOOMI_API_URL", "BOOMI_USERNAME", "BOOMI_API_TOKEN", "BOOMI_ACCOUNT_ID"]


def validate_env():
    """Exit with a clear error if required credentials are missing."""
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        print(f"❌ Missing required .env variables: {', '.join(missing)}")
        print(f"   Copy .env.template to .env and fill in the values.")
        print(f"   Run: python scripts/boomi_env_check.py")
        sys.exit(1)


def _basic_auth_header() -> str:
    """
    Build the Basic auth header value at runtime from BOOMI_USERNAME and
    BOOMI_API_TOKEN. The official spec stores these as two SEPARATE plain
    values — base64(username:token) is computed here, not stored in .env.
    """
    raw = f"{BOOMI_USERNAME}:{BOOMI_API_TOKEN}"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def headers(accept: str = "application/json", content_type: str = "application/json") -> dict:
    h = {
        "Authorization": f"Basic {_basic_auth_header()}",
        "Accept": accept,
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def api_url(path: str) -> str:
    """Build a full Boomi Platform REST API v1 URL for the configured account."""
    return f"{BOOMI_API_URL}/api/rest/v1/{BOOMI_ACCOUNT_ID}/{path}"


def requests_kwargs() -> dict:
    """Common kwargs to pass to requests calls (handles SSL verify toggle)."""
    return {"verify": BOOMI_VERIFY_SSL}


def resolve_environment_id(env: str) -> str:
    """Resolve 'STG' or 'PROD' (or a raw GUID) to an environment ID."""
    env_upper = env.upper()
    if env_upper == "STG":
        if not BOOMI_ENVIRONMENT_ID_STG:
            print("❌ BOOMI_ENVIRONMENT_ID_STG (or BOOMI_ENVIRONMENT_ID) not set in .env")
            sys.exit(1)
        return BOOMI_ENVIRONMENT_ID_STG
    if env_upper == "PROD":
        if not BOOMI_ENVIRONMENT_ID_PROD:
            print("❌ BOOMI_ENVIRONMENT_ID_PROD not set in .env")
            sys.exit(1)
        return BOOMI_ENVIRONMENT_ID_PROD
    # Treat as a raw environment GUID passed directly
    return env


def log_activity(operation: str, component: str = "", env: str = "", result: str = "", details: str = ""):
    """
    Append a JSONL entry to .activity-log/activity.jsonl.
    Opt-in only — controlled by BOOMI_COMPANION_LOG_ACTIVITY=1 in .env.
    Matches the official bc-integration activity logging convention.
    """
    if not LOG_ACTIVITY:
        return
    ACTIVITY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "operation": operation,
        "component": component,
        "env": env,
        "result": result,
        "details": details,
    }
    with open(ACTIVITY_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
