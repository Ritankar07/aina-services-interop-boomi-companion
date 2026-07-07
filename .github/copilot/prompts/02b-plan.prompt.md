# Plan Mode — Boomi Migration Build Plan

## Mode
Plan Mode — Step 4 of 6 (after /select-apis locks scope, before /migrate)

Recommended for any build with >3 components or any AMBER modules. Skip for simple single-process builds.

## Pre-flight Checks
1. Is `SELECTED APIs — MIGRATION SCOPE LOCKED` present with `YES MIGRATE` or `YES MIGRATE GREEN ONLY`?
   - NO → "Run /select-apis first — it scores, selects, and approves scope in one flow."
2. Read `preferred_connections.md` if present — cross-reference every needed connection type. Mark matches REUSE. If file absent: "No preferred_connections.md found — all connections will be created fresh."

---

## Plan Output Format

```
╔══════════════════════════════════════════════════════════════╗
║              📋  BOOMI MIGRATION BUILD PLAN                  ║
╚══════════════════════════════════════════════════════════════╝
Source   : [source filename/module]   Language : [Java/.NET/Python]
Scope    : [GREEN only / GREEN+AMBER / specific modules]

📁 FOLDER STRUCTURE
migration-output/boomi-processes/
└── [MAIN-PROCESS-NAME]/
    ├── [PROCESS-NAME].xml
    ├── [CONNECTION-NAME].xml
    ├── [PROFILE-NAME-IN].xml
    ├── [PROFILE-NAME-OUT].xml
    ├── [MAP-NAME].xml
    ├── [APIM-DEFINITION].xml      (if applicable)
    └── [PROCESS-NAME]-MIGRATION-NOTES.md

🔌 CONNECTIONS
  ✅ REUSE : [ConnectionName] — matched from preferred_connections.md
  🆕 CREATE: [ConnectionName] ([connector type] — [why])

📊 PROFILES
  🆕 [ProfileName] ([JSON/XML/CSV/Flat File/DB])
     Direction: IN/OUT   Source: [system]   Fields: ~[N]   Complexity: LOW/MEDIUM/HIGH

🗺️  MAP COMPONENTS
  🆕 [MapName]
     Source: [Profile]  Target: [Profile]
     Direct mappings: [N]   Functions needed: [Lookup/Date/Concat/Script]
     Complexity: LOW/MEDIUM/HIGH

⚙️  PROCESS SHAPES — [PROCESS-NAME]
  1. Start          [trigger: API Service/Schedule/Listen/Manual]
  2. Try/Catch
    3.   Connector  [GET/SEND/QUERY/EXECUTE — name — operation]
    4.   Map        [map component name]
  Catch:
    5.   Exception  [error format/HTTP code]

📡 BOOMI APIM DEFINITION (if APIs exposed)
  API Component: [name]   Path: [METHOD /api/v{n}/...]
  Auth: Entra ID JWT   Linked Process: [name]

🚀 DEPLOYMENT TARGET
  Folder         : [pending — confirmed in /migrate Step 6]
  Atom           : [BOOMI_TEST_ATOM_ID from .env]
  First deploy to: STG (BOOMI_ENVIRONMENT_ID_STG)
  Promote to     : PROD (manual, after sign-off)

📈 BUILD SUMMARY
  Total components: [N]  New: [N]  Reused: [N]
  Profiles: [N]  Maps: [N]  Connections new/reused: [N]/[N]  Groovy scripts: [N] (flag if >2)
  Complexity: LOW/MEDIUM/HIGH/VERY HIGH

  ⚠️ RISKS:
  - [specific risk, e.g. AMBER module requires Groovy port — test carefully]

══════════════════════════════════════════════════════════════
  Type: APPROVE PLAN  /  MODIFY PLAN: [changes]  /  CANCEL PLAN
══════════════════════════════════════════════════════════════
```

## Handling MODIFY PLAN
Apply requested changes, re-display the full updated plan, ask again.

## Handling APPROVE PLAN
"Plan approved. Run `/migrate` to generate components as planned." Save to `migration-output/boomi-processes/[PROCESS-NAME]-APPROVED-PLAN.md`.

## Handling CANCEL PLAN
"Plan cancelled. No components generated. Run `/plan` again when ready."
