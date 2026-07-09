# Boomi Migration Workspace
### GitHub Copilot + Boomi AtomSphere — Code Migration & Integration Development

> AI-assisted workflow for migrating Java, .NET, and Python code to Boomi integration processes, through GitHub Copilot custom prompt commands. Credential model and platform knowledge verified against the official [bc-integration](https://github.com/OfficialBoomi/bc-integration) plugin specification.
> Built for LTM (Arch Insurance) Interop Team / Center for Enablement.

---

## Quick Start

```bash
pip install requests python-dotenv

git clone https://github.com/YOUR-ORG/aina-services-interop-boomi-companion
cd aina-services-interop-boomi-companion
code .

cp .env.template .env
# Fill in BOOMI_API_URL, BOOMI_USERNAME, BOOMI_API_TOKEN, BOOMI_ACCOUNT_ID, etc.

python scripts/boomi_env_check.py --test-auth
```

Then in VS Code: **Settings → search `chat.promptFiles` → enable → restart VS Code**. Open Copilot Chat (`Ctrl+Shift+I`) and type `/` — all commands appear.

---

## Slash Commands

| Command | What It Does |
|---|---|
| `/repo-connect` | Connect to a GitHub/Azure DevOps repo |
| `/analyze` | Scan entire repo, discover APIs **and** score each one GREEN/AMBER/RED in one pass |
| `/select-apis` | Pick which scored APIs to migrate **and** confirm the migration decision (YES MIGRATE) |
| `/plan` | Full build blueprint before any XML is generated |
| `/migrate` | Generate Boomi XML for the locked, approved scope (prompts for folder) |
| `/mapping` | Build or fix a Boomi Map component — standalone or auto-invoked by `/migrate` |
| `/document` | TDD, Runbook, API Reference → Confluence or Markdown |
| `/unittest` | Test cases + Boomi Test mode checklist |
| `/debug` | Fetch execution logs, diagnose failures (BOOMI_THINKING framework) |
| `/pull-component` | Modify existing AtomSphere components |
| `/marketplace` | Search Boomi Marketplace before migrating |
| `/feasibility-detail` | Optional — deeper re-assessment of a specific API beyond the /analyze summary score |
| `/tidy` | Clean workspace artifacts |

---

## Credential Model (verified against official spec)

```bash
BOOMI_API_URL=https://api.boomi.com      # root URL only
BOOMI_USERNAME=your.email@company.com    # separate from token
BOOMI_API_TOKEN=raw_token_here           # raw, NOT base64 — encoded at runtime
BOOMI_ACCOUNT_ID=your_account_id
BOOMI_TARGET_FOLDER=folder_guid_here     # default folder for new components
BOOMI_ENVIRONMENT_ID_STG=...             # this workspace's STG/PROD safety split
BOOMI_ENVIRONMENT_ID_PROD=...
BOOMI_TEST_ATOM_ID=atom_guid
```
Full reference: [`.env.template`](.env.template). Verify with `python scripts/boomi_env_check.py --test-auth`.

---

## Migration Workflow

```
/repo-connect → /analyze (scores inline) → /select-apis (selects + YES MIGRATE)
       ↓
     /plan → APPROVE PLAN
       ↓
   /migrate  (asks for Boomi folder path, generates Map via /mapping logic)
       ↓
  /document + /unittest
       ↓
python scripts/boomi_deploy.py --env STG
       ↓ (test-fix-retest loop, see /debug)
python scripts/boomi_deploy.py --env PROD
```

---

## Scripts

| Script | Purpose |
|---|---|
| `boomi_common.py` | Shared credential loading, auth headers, activity logging |
| `boomi_env_check.py` | Verify credentials without revealing values |
| `boomi_push.py` | **Push component XML to Boomi account** (create/update — no deployment) |
| `boomi_deploy.py` | **Package + deploy** using `--component-id` from boomi_push.py |
| `boomi_undeploy.py` | Remove deployed component |
| `boomi_pull.py` | Pull existing component XML |
| `boomi_folder.py` | Resolve / create AtomSphere folder by path |
| `boomi_logs.py` | Fetch execution records and logs |
| `boomi_branch.py` | Manage AtomSphere Git branches |
| `boomi_marketplace.py` | Search and install Marketplace recipes |
| `confluence_push.py` | Push documentation to Confluence Cloud |
| `scaffold.py` | Create new isolated project from this template |

---

## Folder Structure

```
.github/
  copilot-instructions.md     ← Boomi knowledge base + Mapping Skill (auto-read by Copilot)
  copilot/prompts/            ← All slash commands
migration-output/             ← Generated artifacts
scripts/                      ← Python automation (all share boomi_common.py)
templates/                    ← Document reference templates
preferred_connections.md      ← Connection reuse registry
.env                          ← Credentials (gitignored — create from .env.template)
```

---

## Official Boomi Companion (Copilot-native install)

```bash
gh skill install OfficialBoomi/boomi-integration
gh skill install OfficialBoomi/boomi-marketplace
```
This workspace adds the migration-specific layer (code analysis, feasibility scoring, API selection, Plan Mode replication) on top.

---

## Documentation

- [`GUIDE.md`](GUIDE.md) — Full workflow guide
- [`SETUP-AND-EXECUTION.md`](SETUP-AND-EXECUTION.md) — Step-by-step setup
- [`BOOMI-COMPANION-AUDIT.md`](BOOMI-COMPANION-AUDIT.md) — Gap analysis vs official Boomi Companion

---

## License

Custom-built for LTM internal use. Boomi Companion skills referenced are licensed under [BSD-2-Clause](https://github.com/OfficialBoomi/bc-integration/blob/main/LICENSE).
