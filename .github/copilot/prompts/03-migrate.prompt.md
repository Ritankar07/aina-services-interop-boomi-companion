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
> `CONN_[System]: REUSE existing — pulled via boomi_pull.py before importing the process.`

```xml
<!-- CONNECTION STUB: Complete credentials in AtomSphere before use -->
<!-- Not found in preferred_connections.md -->
<bns:Component name="CONN_[System]" type="connection">
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
API Service name: `<Domain> <API Name> API`
API Proxy name: `<API Name> Proxy`
Linked process: follows main process naming `API_<Verb>_<Resource>`
Auth policy: Entra ID JWT (standard Interop Layer)

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
- [ ] All component names comply with the naming convention table
- [ ] All shapes match approved plan shape list and have <dragpoints>
- [ ] No PLACEHOLDER_ tokens remain before pushing/deploying
```

---

## Component Naming Convention

Apply these to EVERY component name generated. Flag and correct any name that doesn't conform before writing the XML.

| Component | Pattern | Example |
|---|---|---|
| **API Service** | `<Domain> <API Name> API` | `Policy Management API` |
| **API Proxy** | `<API Name> Proxy` | `Policy Proxy` |
| **Main Process** | `API_<Verb>_<Resource>` | `API_GET_Policy` |
| **Subprocess** | `SUB_<Purpose>` | `SUB_InvokeGuidewire` |
| **Process Route** | `ROUTE_<Purpose>` | `ROUTE_PolicyOperations` |
| **Map** | `MAP_<Source>_TO_<Target>` | `MAP_Request_TO_GWPolicy` |
| **XML/JSON Profile** | `<Entity>_<Direction>_<Format>` | `Policy_Request_JSON` |
| **Connection** | `CONN_<System>` | `CONN_Guidewire` |
| **Operation** | `<Action>_<Object>` | `GET_Policy`, `UPSERT_Claim` |
| **Process Property** | `PP_<Purpose>` | `PP_API_Config` |
| **Environment Extension** | `EXT_<Property>` | `EXT_BaseURL` |
| **Cross Reference Table** | `XREF_<Source>_<Target>` | `XREF_ProductCode` |
| **Document Cache** | `CACHE_<Purpose>` | `CACHE_AccessToken` |

Direction values for profiles: `Request`, `Response`, `Inbound`, `Outbound`
Format values for profiles: `JSON`, `XML`, `CSV`, `Flat`
Verb values for processes: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `UPSERT`, `PROCESS`

## Output Instructions

### Folder Structure Rule — One Folder Per API

Every API selected for migration gets its own dedicated subfolder named after its main process (following the `API_<Verb>_<Resource>` naming convention). This ensures files from different migration runs never overwrite each other.

```
migration-output/
└── boomi-processes/
    ├── API_GET_Policy/                  ← one folder per migrated API
    │     API_GET_Policy.xml             ← main process
    │     CONN_Guidewire.xml             ← connection stub (CREATE only)
    │     Policy_Request_JSON.xml        ← input profile
    │     Policy_Response_JSON.xml       ← output profile
    │     MAP_Request_TO_GWPolicy.xml    ← map component
    │     Policy_Management_API.xml      ← APIM service (if applicable)
    │     Policy_Proxy.xml               ← APIM proxy (if applicable)
    │     API_GET_Policy-MIGRATION-NOTES.md
    │
    ├── API_POST_Policy/                 ← second API — its own folder
    │     API_POST_Policy.xml
    │     MAP_CreateRequest_TO_GWPolicy.xml
    │     Policy_Create_Request_JSON.xml
    │     API_POST_Policy-MIGRATION-NOTES.md
    │
    └── API_GET_Claim/                   ← third API — its own folder
          API_GET_Claim.xml
          ...
```

**Rules:**
- The subfolder name = the main process name (e.g. `API_GET_Policy/`)
- One subfolder per API, always — even if two APIs share a connection
- Connection stubs marked **REUSE**: do NOT generate an XML file — add a note in migration notes only
- Connection stubs marked **CREATE**: generate once in the first API that needs them; subsequent APIs reference the same component — note this in their migration notes
- Running `/migrate` again for new APIs adds new subfolders — it does NOT overwrite or delete existing ones

Save all files for each API directly into its named subfolder before moving to the next API.

After generating all APIs, tell the user:

> "Generation complete. Each API has its own folder in `migration-output/boomi-processes/`:
>
> ```
> migration-output/boomi-processes/
>   API_GET_Policy/
>   API_POST_Policy/
>   API_GET_Claim/
> ```
>
> **Run `/push` to push all generated components to your Boomi account** (requires `YES MIGRATE` and `APPROVE PLAN` to be active in this conversation).
>
> Or push individually from the terminal:
> ```
> python scripts/boomi_push.py --folder migration-output/boomi-processes/API_GET_Policy/
> python scripts/boomi_push.py --folder migration-output/boomi-processes/API_POST_Policy/
> ```
>
> Then deploy each pushed component:
> ```
> python scripts/boomi_deploy.py --component-id [ID] --env STG
> ```"

---

## Post-Generation: Test-Fix-Retest

After the user deploys to STG, offer to run the test loop:
1. `python scripts/boomi_logs.py --process-name "[name]" --count 1 --download` to fetch the latest execution
2. Review the log — confirm success, or diagnose failure using the known error patterns in copilot-instructions.md
3. If a known fix applies, propose it, regenerate the XML, re-push with `boomi_push.py`, then redeploy with `boomi_deploy.py --component-id`
4. Repeat until passing, or escalate to `/debug` for the full tiered framework
