#!/usr/bin/env python3
"""
confluence_push.py
-------------------
Pushes Copilot-generated Boomi documentation to Confluence Cloud via REST API.

Usage:
  python scripts/confluence_push.py --file migration-output/confluence-docs/MyProcess-TDD.html \\
      --space INTEROP --title "TDD — CLAIMS-INBOUND-IMRIGHT-REST v1.0"
  python scripts/confluence_push.py --folder migration-output/confluence-docs/ --space INTEROP
  python scripts/confluence_push.py --folder migration-output/confluence-docs/ --space INTEROP --dry-run

Requirements: pip install requests python-dotenv
"""

import argparse
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

BASE_URL      = os.getenv("CONFLUENCE_BASE_URL", "").rstrip("/")
CONF_USER     = os.getenv("CONFLUENCE_USER", "")
API_TOKEN     = os.getenv("CONFLUENCE_API_TOKEN", "")
DEFAULT_SPACE = os.getenv("CONFLUENCE_SPACE_KEY", "")
DEFAULT_PARENT= os.getenv("CONFLUENCE_PARENT_PAGE_ID", "")


def validate_env():
    missing = [v for v in ["CONFLUENCE_BASE_URL", "CONFLUENCE_USER", "CONFLUENCE_API_TOKEN"] if not os.getenv(v)]
    if missing:
        print(f"❌ Missing required .env variables: {', '.join(missing)}")
        sys.exit(1)


def auth():
    return (CONF_USER, API_TOKEN)


def api(path: str) -> str:
    return f"{BASE_URL}/rest/api{path}"


def filename_to_title(filename: str) -> str:
    stem = Path(filename).stem
    return stem.replace("_", " ").replace("-", " — ", 1)


def read_file_content(filepath: Path) -> str:
    content = filepath.read_text(encoding="utf-8")
    if filepath.suffix.lower() == ".md":
        content = md_to_confluence(content)
    return content


def md_to_confluence(md: str) -> str:
    lines = md.split("\n")
    output = []
    in_code_block = False
    code_lang = "text"
    code_lines = []
    in_table = False

    for line in lines:
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip() or "text"
                code_lines = []
            else:
                in_code_block = False
                code_content = "\n".join(code_lines)
                output.append(
                    f'<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{code_lang}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body>'
                    f'</ac:structured-macro>'
                )
            continue
        if in_code_block:
            code_lines.append(line)
            continue

        if line.startswith("# "):
            output.append(f"<h1>{line[2:].strip()}</h1>")
        elif line.startswith("## "):
            output.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("### "):
            output.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("#### "):
            output.append(f"<h4>{line[5:].strip()}</h4>")
        elif line.startswith("|") and "|" in line[1:]:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue
            if not in_table:
                in_table = True
                output.append("<table><tbody>")
                row_type = "th"
            else:
                row_type = "td"
            output.append(f"<tr>{''.join(f'<{row_type}>{c}</{row_type}>' for c in cells)}</tr>")
        else:
            if in_table:
                output.append("</tbody></table>")
                in_table = False
            if line.startswith("- ") or line.startswith("* "):
                output.append(f"<ul><li>{inline_md(line[2:])}</li></ul>")
            elif re.match(r"^\d+\. ", line):
                output.append(f"<ol><li>{inline_md(re.sub(r'^\d+\. ', '', line))}</li></ol>")
            elif line.strip() in ("---", "***", "___"):
                output.append("<hr/>")
            elif line.startswith("> "):
                output.append(f'<ac:structured-macro ac:name="info"><ac:rich-text-body><p>{inline_md(line[2:])}</p></ac:rich-text-body></ac:structured-macro>')
            elif line.strip() == "":
                output.append("")
            else:
                output.append(f"<p>{inline_md(line)}</p>")

    if in_table:
        output.append("</tbody></table>")
    return "\n".join(output)


def inline_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def get_page_by_title(space_key: str, title: str) -> dict | None:
    resp = requests.get(api("/content"), params={"spaceKey": space_key, "title": title, "expand": "version"}, auth=auth())
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        return results[0] if results else None
    return None


def get_space_homepage(space_key: str) -> str | None:
    resp = requests.get(api(f"/space/{space_key}"), params={"expand": "homepage"}, auth=auth())
    if resp.status_code == 200:
        return resp.json().get("homepage", {}).get("id")
    return None


def create_page(space_key, title, body, parent_id=None) -> dict:
    payload = {"type": "page", "title": title, "space": {"key": space_key},
               "body": {"storage": {"value": body, "representation": "storage"}}}
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    resp = requests.post(api("/content"), json=payload, auth=auth(), headers={"Content-Type": "application/json"})
    resp.raise_for_status()
    return resp.json()


def update_page(page_id, title, body, current_version) -> dict:
    payload = {"type": "page", "title": title, "version": {"number": current_version + 1},
               "body": {"storage": {"value": body, "representation": "storage"}}}
    resp = requests.put(api(f"/content/{page_id}"), json=payload, auth=auth(), headers={"Content-Type": "application/json"})
    resp.raise_for_status()
    return resp.json()


def add_label(page_id: str, labels: list[str]):
    requests.post(api(f"/content/{page_id}/label"),
                  json=[{"prefix": "global", "name": lbl} for lbl in labels],
                  auth=auth(), headers={"Content-Type": "application/json"})


def push_file(filepath, space_key, title, parent_id, labels, dry_run) -> dict | None:
    page_title = title or filename_to_title(filepath.name)
    body = read_file_content(filepath)

    print(f"\n  📄 {filepath.name}\n     Title : {page_title}\n     Space : {space_key}\n     Parent: {parent_id or 'space homepage'}")

    if dry_run:
        print(f"     [DRY RUN] Would create/update page — no changes made")
        return None

    existing = get_page_by_title(space_key, page_title)
    if existing:
        page_id = existing["id"]
        version = existing["version"]["number"]
        print(f"     Action: UPDATE (existing ID {page_id}, v{version} → v{version+1})")
        result = update_page(page_id, page_title, body, version)
    else:
        print(f"     Action: CREATE (new page)")
        result = create_page(space_key, page_title, body, parent_id)
        page_id = result.get("id")

    if labels and page_id:
        add_label(page_id, labels)
        print(f"     Labels: {', '.join(labels)}")

    print(f"     ✅ URL : {BASE_URL}/pages/{result.get('id')}")
    return result


def push_folder(folder, space_key, parent_id, labels, dry_run):
    files = sorted([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in (".html", ".md")])
    if not files:
        print(f"❌ No .html or .md files found in {folder}")
        sys.exit(1)

    print(f"\n📂 Pushing {len(files)} file(s) from {folder}")
    resolved_parent = parent_id
    if not resolved_parent and not dry_run:
        resolved_parent = get_space_homepage(space_key)
        print(f"   Using space homepage as parent (ID: {resolved_parent})" if resolved_parent
              else f"   ⚠️  Could not find space homepage — pages created at space root")

    for f in files:
        push_file(f, space_key, None, resolved_parent, labels, dry_run)


def main():
    parser = argparse.ArgumentParser(description="Push Boomi migration documentation to Confluence")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file")
    group.add_argument("--folder")
    parser.add_argument("--space")
    parser.add_argument("--title")
    parser.add_argument("--parent-id")
    parser.add_argument("--labels", nargs="+", default=["boomi", "migration", "interop"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    validate_env()
    space_key = args.space or DEFAULT_SPACE
    if not space_key:
        print("❌ No Confluence space key. Use --space or set CONFLUENCE_SPACE_KEY in .env")
        sys.exit(1)
    parent_id = args.parent_id or DEFAULT_PARENT or None

    print(f"\n{'='*60}\n📘 Confluence Push Script\n   Target  : {BASE_URL}\n   Space   : {space_key}")
    print(f"   Parent  : {parent_id or 'space homepage (auto)'}\n   Labels  : {', '.join(args.labels)}\n   Dry Run : {args.dry_run}\n{'='*60}")

    if args.file:
        filepath = Path(args.file).resolve()
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            sys.exit(1)
        push_file(filepath, space_key, args.title, parent_id, args.labels, args.dry_run)
    elif args.folder:
        folder = Path(args.folder).resolve()
        if not folder.is_dir():
            print(f"❌ Folder not found: {folder}")
            sys.exit(1)
        push_folder(folder, space_key, parent_id, args.labels, args.dry_run)

    print("\n🎉 Done.\n")


if __name__ == "__main__":
    main()
