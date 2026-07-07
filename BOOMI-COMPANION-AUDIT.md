# Boomi Companion — Feature Audit & Correction Log

## What Was Corrected in This Pass (verified against actual source)

Earlier passes inferred behavior from README/CLAUDE.md/CHANGELOG descriptions without reading the actual `.env.example` or skill reference files. This pass fetched real files directly and corrected the following:

### 1. Credential Model — CORRECTED
| Was (incorrect) | Now (verified from `bc-integration/template/.env.example`) |
|---|---|
| `BOOMI_API_TOKEN` = base64(user:token), pre-encoded | `BOOMI_API_TOKEN` = raw token; `BOOMI_USERNAME` separate; base64 built at runtime |
| `BOOMI_BASE_URL` = full `/api/rest/v1` path | `BOOMI_API_URL` = root only, e.g. `https://api.boomi.com` |
| `BOOMI_ENV_ID_STG` / `BOOMI_ENV_ID_PROD` | `BOOMI_ENVIRONMENT_ID` (official, single) + this workspace's `BOOMI_ENVIRONMENT_ID_STG`/`_PROD` extension |
| `BOOMI_ATOM_ID` | `BOOMI_TEST_ATOM_ID` |
| Activity logging assumed always-on | `BOOMI_COMPANION_LOG_ACTIVITY=1` — **opt-in only** |
| No SSL toggle | `BOOMI_VERIFY_SSL` (default true) |
| No target folder default | `BOOMI_TARGET_FOLDER` — default folder for new components |
| No WSS test config | `SERVER_AUTH_TYPE`/`SERVER_BASE_URL`/`SERVER_USERNAME`/`SERVER_TOKEN`/`SERVER_BEARER_TOKEN`/`SERVER_VERIFY_SSL` added |

All `scripts/boomi_*.py` now import a shared `boomi_common.py` that implements this exact model.

### 2. Mapping Skill — ADDED (was previously thin)
Built a dedicated `/mapping` command plus a full Mapping Skill section in `copilot-instructions.md`, sourced from verified help.boomi.com Map and Map Function documentation:
- Map connection rules (one connection per destination field — previously unstated)
- Default value firing behavior (null/blank fallback vs always-default — previously unstated)
- Date/Number auto-formatting without functions
- Boomi Suggest feature
- Map Extensions for environment-specific overrides
- Standard vs User-Defined vs Custom Script function hierarchy
- Map Function caching (None/By Document/By Map)
- Cross Reference Table behavior
- Groovy sandbox network-call block (critical, previously stated but not enforced in generation rules)

### 3. Data Hub — REMOVED per user instruction
The `boomi-datahub` skill is out of scope for this workspace. `09-datahub.prompt.md` has been dropped entirely. If you need it later, the verified official workflow is: prompt → Draft model → review checkpoint (locks field types/repeatability) → Publish (version 1) → create repository on a Hub Cloud → deploy as "universe" → manually wire `DATAHUB_REPO_URI`/`DATAHUB_REPO_USERNAME`/`DATAHUB_REPO_AUTH_TOKEN` (separate credential from the platform token) → load test data.

### 4. Test-Fix-Retest Loop — Documented Accurately
The official workflow auto-tests after every deploy: execute → download log → review → if failed, diagnose from log → apply fix → redeploy → retest, without requiring manual intervention for the retry itself. This is now explicit in `copilot-instructions.md` and wired through `/debug` and `boomi_logs.py`'s log-retry handling.

---

## Full Plugin Inventory (verified)

| Plugin | Skill | Scope |
|---|---|---|
| `bc-integration` | `boomi-integration` | Build, deploy, test integration processes, EDI, Event Streams |
| `bc-marketplace` | `boomi-marketplace` | Search/install Marketplace recipes |
| `bc-datahub` | `boomi-datahub` | **Out of scope for this workspace** |

Install the official skills directly in Copilot:
```bash
gh skill install OfficialBoomi/boomi-integration
gh skill install OfficialBoomi/boomi-marketplace
```

---

## What's Still Inferred, Not Verified

GitHub blocks crawler access to the actual `SKILL.md` and individual reference docs inside `skills/boomi-integration/references/` (tree views and most raw content are `robots.txt`-disallowed unless directly linked). What's verified:
- `README.md`, `CLAUDE.md`, `CHANGELOG.md` (full 321 lines) — confirms what exists and what was fixed across versions
- `.env.example` (direct commit-hash link) — fully verified, now matched exactly
- `developer.boomi.com` documentation pages — fully verified for workflow, commands, credentials, and Data Hub lifecycle
- help.boomi.com Map/Map Function pages — fully verified, used as the basis for the Mapping Skill

Not verified (synthesized from changelog descriptions, treated as best-effort, not guaranteed byte-exact to the real skill): exact Trading Partner XML attribute names, exact Document Cache XML schema, exact Cross Reference Table component XML structure. These are documented in `copilot-instructions.md` at a behavioral level (what to do) rather than exact XML schema level — always validate generated XML against AtomSphere's actual import validation before deploying to PROD.

---

## Not Replicable in GitHub Copilot (Claude Code-native, no equivalent built)

| Feature | Why Not Replicable |
|---|---|
| Canvas Arranger Agent | Requires direct AtomSphere layout API + autonomous file execution |
| Shift+Tab Plan Mode trigger | Claude Code keyboard shortcut — replaced by `/plan` command |
| Fully autonomous build→test→fix→redeploy with zero gates | Copilot requires human confirmation at each command invocation; the retry loop within a single `/debug` or deploy call is automated, but moving between major phases (`/migrate` → test → `/document`) is not chained automatically |
