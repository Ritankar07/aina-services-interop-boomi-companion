#!/usr/bin/env python3
"""
scaffold.py — /freshies equivalent
-------------------------------------
Creates a new isolated Boomi migration project folder from this template.

Usage:
  python scripts/scaffold.py --name "claims-migration-june2026"
  python scripts/scaffold.py --name "policyhub-migration" --dest ~/projects/
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

COPY_DIRS = [".github", "scripts", "templates"]
COPY_FILES = [
    "preferred_connections.md", ".env.template", ".gitignore",
    "GUIDE.md", "SETUP-AND-EXECUTION.md", "BOOMI-COMPANION-AUDIT.md", "CLAUDE.local.md",
]
CREATE_EMPTY = [
    "migration-output/feasibility-reports", "migration-output/boomi-processes",
    "migration-output/test-cases", "migration-output/confluence-docs",
    "migration-output/markdown-docs", "migration-output/pulled-components",
    "migration-output/marketplace-recipes", "migration-output/logs", ".activity-log",
]


def scaffold(name: str, dest: Path, template_dir: Path):
    safe_name = name.strip().lower().replace(" ", "-")
    project_dir = dest / safe_name

    if project_dir.exists():
        print(f"❌ Directory already exists: {project_dir}")
        sys.exit(1)

    print(f"\n{'='*60}\n  🚀 Boomi Migration Project Scaffolder\n     Template: {template_dir}\n     Project : {project_dir}\n{'='*60}\n")
    project_dir.mkdir(parents=True)
    print(f"  📁 Created: {project_dir}")

    for d in COPY_DIRS:
        src = template_dir / d
        if src.exists():
            shutil.copytree(src, project_dir / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            print(f"  ✅ Copied dir : {d}/")
        else:
            print(f"  ⚠️  Skipped (not found): {d}/")

    for f in COPY_FILES:
        src = template_dir / f
        if src.exists():
            dst = project_dir / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ✅ Copied file: {f}")
        else:
            print(f"  ⚠️  Skipped (not found): {f}")

    for d in CREATE_EMPTY:
        empty_dir = project_dir / d
        empty_dir.mkdir(parents=True, exist_ok=True)
        (empty_dir / ".gitkeep").touch()
    print(f"  ✅ Created empty migration-output/ structure")

    readme = project_dir / "README.md"
    readme.write_text(f"""# {name}
Boomi Migration Project — scaffolded {datetime.now().strftime('%Y-%m-%d')}

## Setup
1. `cp .env.template .env` and fill in credentials
2. `code .`
3. Enable `chat.promptFiles` in VS Code settings, restart
4. `python scripts/boomi_env_check.py --test-auth`

## Workflow
See `GUIDE.md`. Key commands: `/repo-connect` `/analyze` `/select-apis` `/plan` `/migrate` `/mapping` `/document` `/unittest` `/debug` `/pull-component` `/marketplace`
""", encoding="utf-8")
    print(f"  ✅ Created README.md")

    print(f"\n{'='*60}\n  ✅ Project ready: {project_dir}")
    print(f"\n  NEXT STEPS:\n  1. cd {project_dir}\n  2. cp .env.template .env  →  fill in credentials")
    print(f"  3. code .\n  4. Run /repo-connect in Copilot Chat\n{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold a new Boomi migration project from this template")
    parser.add_argument("--name", required=True)
    parser.add_argument("--dest", default="..")
    args = parser.parse_args()

    scaffold(args.name, Path(args.dest).expanduser().resolve(), Path(__file__).parent.parent.resolve())
