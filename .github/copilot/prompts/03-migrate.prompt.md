# Generate Boomi Process Components

## Mode
Migration — Steps 5-6 of 6

## Pre-flight Checks (run ALL in order)

**Check 1 — Scope locked AND approved?** Is `SELECTED APIs — MIGRATION SCOPE LOCKED` present, containing `YES MIGRATE` or `YES MIGRATE GREEN ONLY`?
- NO → "Run /select-apis first — it scores APIs, lets you select, and captures the migration decision in one flow." STOP.

**Check 2 — Plan Mode?** `APPROVE PLAN` present?
- YES → use the approved plan as the authoritative component list/names/shapes.
- NO → if build is complex (>3 components or any AMBER): "⚠️ Complex build — run /plan first, or type SKIP PLAN to proceed without it."
- NO + simple build → proceed, note "No approved plan — generating from analysis context."

**Check 3 — Connection reuse**: cross-reference `preferred_connections.md`. Apply REUSE decisions from the plan — only generate stubs for CREATE connections.

**Check 4 — Scope confirmation**: state "I will generate components for: [list]." before proceeding.

---

## ★ Check 5 — Boomi Folder Path (always runs, even for simple builds)

```
📁 BOOMI FOLDER PATH — REQUIRED

Where in AtomSphere should the generated components be placed?
Examples: CLAIMS/INBOUND  ·  Interop Layer/Migration/June2026

If you leave this blank, I will use BOOMI_TARGET_FOLDER from .env as the default.
Type the folder path, or "default" to use BOOMI_TARGET_FOLDER: _
```

Wait for response. If "default" → tell user this resolves to whatever `BOOMI_TARGET_FOLDER` is set to in `.env` (the deploy script handles this automatically — no path resolution needed).

If a custom path is given:
```bash
python scripts/boomi_folder.py --path "[user input]" --create-if-missing
```
Ask the user to paste the returned folder ID back into chat, then confirm:
```
✅ Folder confirmed: [user path]   Folder ID: [resolved ID]
   All components will be created in this folder.
```

Only proceed to XML generation after folder is confirmed (or default explicitly chosen).

---

## What to Generate Per Module

### 1. Process Component XML
- Valid `type="process"` XML, named `[DOMAIN]-[DIRECTION]-[SYSTEM]-[TYPE]`
- `folderId` attribute present — use the ID from Check 5 (or leave as `PLACEHOLDER_FOLDER_ID` if default/BOOMI_TARGET_FOLDER was chosen, since the deploy script injects it automatically)
- All credentials = `PLACEHOLDER_[TYPE]`
- **Every shape has `<dragpoints>`** — this is mandatory, not optional
- XML comments on non-obvious shapes

### 2. Connection Component Stub
Only for connections marked CREATE. For REUSE connections, add a note instead:
> `CONN-[NAME]: REUSE existing — pulled via boomi_pull.py before importing the process.`

```xml
<!-- CONNECTION STUB: Complete credentials in AtomSphere before use -->
<!-- Not found in preferred_connections.md -->
<bns:Component name="CONN-[SYSTEM]-[PROTOCOL]" type="connection">
  <!-- Credentials: PLACEHOLDER_[TYPE] -->
</bns:Component>
```

### 3. Map Component Definition
Apply the Mapping Skill from copilot-instructions.md:
- Source profile, destination profile, field mapping table
- Mark each destination field's source as ONE of: direct source mapping, default value (used only if source null/blank), or always-default (no source mapped)
- List any functions needed (Standard vs User-Defined vs Custom Script) — flag Custom Script as last resort
- If Date/Number fields map directly without a function, confirm both profile steps are typed correctly so Boomi auto-formats

### 4. APIM Definition (if source exposed REST endpoints)
API Component name, path/methods, Entra ID JWT auth policy, linked process name.

### 5. Migration Notes File
```markdown
# Migration Notes: [ProcessName]
**Source**: [file/class]   **API Endpoint(s)**: [method + path]
**Migration Date**: [date]   **Approved Plan**: [present/absent]
**Boomi Folder**: [path or "BOOMI_TARGET_FOLDER default"]   **Folder ID**: [resolved or PLACEHOLDER]

## What Changed / What Was Excluded
## Connections: Reuse vs Created
## Manual Steps Required
- [ ] For REUSE connections: pull via boomi_pull.py before importing
- [ ] For CREATE connections: fill PLACEHOLDER_* credentials in AtomSphere Extensions
- [ ] Import connections → profiles → maps → process, in that order
- [ ] Run test in Test mode before promoting to STG

## Groovy Scripts (if any)
[script name, purpose, Groovy 2.4 constraint notes — confirm no external network calls]

## Known Gaps vs Original Code
## Validation Checklist
- [ ] All shapes match approved plan shape list and have <dragpoints>
- [ ] No PLACEHOLDER_ tokens remain before deploying
```

---

## Component Naming Convention
| Type | Pattern | Example |
|---|---|---|
| Process | `[DOM]-[DIR]-[SYS]-[TYPE]` | `CLAIMS-INBOUND-IMRIGHT-REST` |
| Connection | `CONN-[SYS]-[PROTOCOL]` | `CONN-SALESFORCE-REST` |
| Map | `MAP-[FROM]-TO-[TO]` | `MAP-JSON-TO-XML-CLAIMPROFILE` |
| API | `API-[VERSION]-[RESOURCE]` | `API-V1-CLAIMS` |
| Profile | `PROF-[SYS]-[FORMAT]-[DIR]` | `PROF-IMRIGHT-JSON-IN` |

## Output Instructions
Save to `migration-output/boomi-processes/[ProcessName]/`: main process XML, connection stubs (NEW only), maps XML, APIM XML (if applicable), migration notes.

After generating:
> "Generation complete. Components match the approved plan. Run `/unittest` next, then deploy with `python scripts/boomi_deploy.py --file [...] --env STG`."

---

## Post-Generation: Test-Fix-Retest

After the user deploys to STG, offer to run the test loop:
1. `python scripts/boomi_logs.py --process-name "[name]" --count 1 --download` to fetch the latest execution
2. Review the log — confirm success, or diagnose failure using the known error patterns in copilot-instructions.md
3. If a known fix applies, propose it and regenerate the XML; otherwise ask the user before guessing at structural changes
4. Repeat until passing, or escalate to `/debug` for the full tiered framework
