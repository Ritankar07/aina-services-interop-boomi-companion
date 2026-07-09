# Setup & Execution Guide

## Part A: One-Time Setup

### A1. Clone / Open
```bash
git clone https://github.com/YOUR-ORG/aina-services-interop-boomi-companion
cd aina-services-interop-boomi-companion
code .
```

### A2. Credentials
```bash
cp .env.template .env
```
Fill in (all variable names match the verified official `bc-integration` spec):

| Variable | Where to find it |
|---|---|
| `BOOMI_API_URL` | Always `https://api.boomi.com` unless on a dedicated cell |
| `BOOMI_USERNAME` | Your Boomi platform login email |
| `BOOMI_API_TOKEN` | AtomSphere → Settings → API Tokens → generate (copy the raw token, do not encode it) |
| `BOOMI_ACCOUNT_ID` | AtomSphere → Manage → Account Information |
| `BOOMI_TARGET_FOLDER` | Optional — Component Explorer → right-click target folder → Properties → copy ID |
| `BOOMI_ENVIRONMENT_ID_STG` / `_PROD` | Manage → Atom Management → select environment → copy ID from URL |
| `BOOMI_TEST_ATOM_ID` | Manage → Atom Management → select your Atom → copy ID from URL |
| `CONFLUENCE_*` | Atlassian email, API token from id.atlassian.com, space key, parent page ID |

### A3. Verify
```bash
pip install requests python-dotenv
python scripts/boomi_env_check.py --test-auth
```
Confirms required vars are set AND makes a live API call to validate the credentials work.

### A4. Enable Copilot Prompt Files
VS Code → Settings (Ctrl+,) → search `chat.promptFiles` → enable → restart VS Code completely.

Verify: open Copilot Chat (Ctrl+Shift+I), type `/` — you should see `repo-connect`, `analyze`, `select-apis`, `feasibility`, `plan`, `migrate`, `mapping`, `document`, `unittest`, `debug`, `pull-component`, `marketplace`, `tidy`.

### A5. Populate preferred_connections.md
Add your existing AtomSphere connections (name, type, system, auth, environments) so Plan Mode can mark them REUSE instead of recreating them.

---

## Part B: Running a Migration

```
/repo-connect
/analyze               → discovers APIs AND scores them GREEN/AMBER/RED in one pass
/select-apis            → pick from the scored list, then type YES MIGRATE
/plan                  → type APPROVE PLAN  (or skip for simple builds)
/migrate               → answer the folder path prompt
/document              → pick type + format
/unittest
```

Then in terminal:
```bash
# Step 1 — push the generated XML to your Boomi account (no deployment yet)
python scripts/boomi_push.py --file migration-output/boomi-processes/[Name]/[Name].xml

# Copy the Component ID from the output, then:

# Step 2 — package + deploy to STG
python scripts/boomi_deploy.py --component-id [ID from Step 1] --env STG

# After STG validation:
python scripts/boomi_deploy.py --component-id [ID] --env PROD
```
If the test fails, run `/debug` in Copilot Chat with the log output pasted in.

After STG sign-off:
```bash
python scripts/boomi_deploy.py --file [...] --env PROD
```

---

## Folder Reference

```
.github/copilot-instructions.md          ← Boomi knowledge base + Mapping Skill
.github/copilot/prompts/
  00-repo-connect.prompt.md
  00-tidy.prompt.md
  01-analyze.prompt.md              ← discovery + feasibility scoring combined
  01b-api-selector.prompt.md        ← selection + YES MIGRATE decision combined
  02b-plan.prompt.md
  02c-feasibility-detail.prompt.md  ← optional deep-dive, not part of main flow
  03-migrate.prompt.md
  03b-mapping.prompt.md
  04-unittest.prompt.md
  05-document.prompt.md
  06-marketplace.prompt.md
  07-debug.prompt.md
  08-pull-component.prompt.md
scripts/
  boomi_common.py        ← shared credential/auth helper, imported by all others
  boomi_env_check.py
  boomi_deploy.py
  boomi_undeploy.py
  boomi_pull.py
  boomi_folder.py
  boomi_logs.py
  boomi_branch.py
  boomi_marketplace.py
  confluence_push.py
  scaffold.py
templates/
  feasibility-report-template.md
  confluence/sample-TDD.html
preferred_connections.md
CLAUDE.local.md     (gitignored)
.env                (gitignored — from .env.template)
```

---

## Common Errors

| Error | Fix |
|---|---|
| `/` commands don't appear in Copilot Chat | `chat.promptFiles` not enabled, or VS Code not restarted |
| `boomi_env_check.py --test-auth` returns 401 | Check `BOOMI_USERNAME` and `BOOMI_API_TOKEN` are both raw plain values — never pre-base64-encode |
| Deploy fails with validation error | Auto-retry attempts known fixes (whitespace, ${VAR} syntax, durableId range); if it still fails, check every shape has `<dragpoints>` |
| Confluence push 403 | Your Atlassian user needs Edit permission on the target space |
| Log download returns empty | `boomi_logs.py` retries automatically on 202/204 (log still generating) |
