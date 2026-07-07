#!/usr/bin/env python3
"""
boomi_logs.py
--------------
Fetch and display execution records and logs from AtomSphere.

Usage:
  python scripts/boomi_logs.py --process-name "CLAIMS-INBOUND-IMRIGHT-REST" --count 5
  python scripts/boomi_logs.py --execution-id "executionId-abc123" --download
  python scripts/boomi_logs.py --process-name "PROCESS" --status ERROR --hours 24
  python scripts/boomi_logs.py --all-processes --status ERROR --hours 1
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import boomi_common as bc

STATUS_ICONS = {"COMPLETE": "✅", "ERROR": "❌", "INPROCESS": "🔄", "DISCARDED": "⚠️ "}
STATUS_MAP = {"ERROR": "e", "COMPLETE": "c", "INPROCESS": "i"}


def query_executions(process_name=None, status=None, hours=None, count=10):
    cutoff = None
    if hours:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    expressions = []
    if process_name:
        expressions.append({"argument": [process_name], "operator": "EQUALS", "property": "processName"})
    if status:
        expressions.append({"argument": [STATUS_MAP.get(status.upper(), status.lower())], "operator": "EQUALS", "property": "status"})
    if cutoff:
        expressions.append({"argument": [cutoff], "operator": "GREATER_THAN_OR_EQUAL", "property": "executionTime"})

    if len(expressions) == 1:
        query_filter = {"expression": expressions[0]}
    elif len(expressions) > 1:
        query_filter = {"expression": {"operator": "and", "nestedExpression": expressions}}
    else:
        query_filter = {}

    resp = requests.post(bc.api_url("ExecutionRecord/query"), headers=bc.headers(),
                          json={"QueryFilter": query_filter} if query_filter else {}, **bc.requests_kwargs())
    if resp.status_code != 200:
        print(f"❌ Failed to query executions: HTTP {resp.status_code}\n   {resp.text[:500]}")
        sys.exit(1)
    return resp.json().get("result", [])[:count]


def get_execution_by_id(execution_id):
    resp = requests.get(bc.api_url(f"ExecutionRecord/{execution_id}"), headers=bc.headers(), **bc.requests_kwargs())
    if resp.status_code == 200:
        return [resp.json()]
    print(f"❌ Execution {execution_id} not found: HTTP {resp.status_code}")
    sys.exit(1)


def download_execution_log(execution_id, output_dir=None):
    # 204 means log still generating — retry a few times (verified Boomi quirk)
    import time
    for attempt in range(5):
        resp = requests.get(bc.api_url(f"ExecutionRecord/{execution_id}/log"),
                             headers=bc.headers(accept="text/plain"), **bc.requests_kwargs())
        if resp.status_code == 200:
            log_text = resp.text
            if output_dir:
                out_path = Path(output_dir) / f"{execution_id}.log"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(log_text, encoding="utf-8")
                print(f"  📄 Log saved: {out_path}")
            return log_text
        elif resp.status_code in (202, 204):
            print(f"  ⏳ Log still generating (HTTP {resp.status_code}), retrying...")
            time.sleep(2)
            continue
        elif resp.status_code == 404:
            return "[Log not available — execution too old (logs expire after 30 days) or never ran]"
        else:
            return f"[Log fetch failed: HTTP {resp.status_code}]"
    return "[Log generation timed out after 5 retries]"


def format_duration(ms):
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{ms}ms"
    if ms < 60000:
        return f"{ms/1000:.1f}s"
    return f"{ms/60000:.1f}min"


def display_executions(records, download_log, output_dir):
    if not records:
        print("  No executions found matching your criteria.")
        return

    print(f"\n{'='*70}\n  EXECUTION RECORDS  ({len(records)} results)\n{'='*70}")
    for rec in records:
        status = rec.get("status", "UNKNOWN").upper()
        icon = STATUS_ICONS.get(status, "❓")
        exec_id = rec.get("executionId", "?")
        print(f"\n  {icon} {status}")
        print(f"     Process   : {rec.get('processName', '?')}")
        print(f"     Exec ID   : {exec_id}")
        print(f"     Started   : {rec.get('executionTime', '?')}")
        print(f"     Duration  : {format_duration(rec.get('duration'))}")
        if rec.get("message"):
            print(f"     Message   : {rec['message'][:200]}")

        if download_log:
            print(f"     Fetching log...")
            log = download_execution_log(exec_id, output_dir)
            print("     ── LOG EXCERPT (last 30 lines) ──────────────────────")
            for line in log.strip().split("\n")[-30:]:
                print(f"     {line}")
            print("     ──────────────────────────────────────────────────")

    print(f"\n{'='*70}\n  Copy this output and run /debug in Copilot Chat to analyze.\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Fetch Boomi AtomSphere execution records and logs")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--process-name")
    group.add_argument("--execution-id")
    group.add_argument("--all-processes", action="store_true")
    parser.add_argument("--status", choices=["ERROR", "COMPLETE", "INPROCESS"])
    parser.add_argument("--hours", type=int)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--output-dir", default="migration-output/logs")
    args = parser.parse_args()

    bc.validate_env()
    print(f"\n{'='*70}\n  🔍 Boomi Execution Log Fetcher  —  Account: {bc.BOOMI_ACCOUNT_ID}\n{'='*70}")

    if args.execution_id:
        records = get_execution_by_id(args.execution_id)
    else:
        records = query_executions(
            process_name=args.process_name if not args.all_processes else None,
            status=args.status, hours=args.hours, count=args.count
        )

    display_executions(records, args.download, args.output_dir if args.download else None)
    bc.log_activity("fetch-logs", args.process_name or "all", result="success", details=f"{len(records)} records")


if __name__ == "__main__":
    main()
