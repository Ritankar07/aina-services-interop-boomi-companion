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

Each API gets its own subfolder named after its main process.
Files from different migration runs are never overwritten.

migration-output/boomi-processes/
├── [SourceClass]_API_[Verb]_[Resource]/   ← SourceClass + API name for quick identification
│     e.g. ClaimsController_API_GET_Policy/
│     API_[Verb]_[Resource].xml            e.g. API_GET_Policy.xml
│     SUB_[Purpose].xml                 e.g. SUB_InvokeGuidewire.xml  (if any)
│     CONN_[System].xml                 e.g. CONN_Guidewire.xml        (CREATE only)
│     [Entity]_Request_[Format].xml     e.g. Policy_Request_JSON.xml
│     [Entity]_Response_[Format].xml    e.g. Policy_Response_JSON.xml
│     MAP_[Source]_TO_[Target].xml      e.g. MAP_Request_TO_GWPolicy.xml
│     [Domain] [API Name] API.xml       e.g. Policy_Management_API.xml (if APIM)
│     [API Name] Proxy.xml              e.g. Policy_Proxy.xml          (if APIM)
│     API_[Verb]_[Resource]-MIGRATION-NOTES.md
│
├── API_[Verb]_[Resource2]/             ← second API — its own folder
│     ...
│
└── API_[Verb]_[Resource3]/             ← third API — its own folder
      ...

🔌 CONNECTIONS
  ✅ REUSE : [CONN_System] — matched from preferred_connections.md
  🆕 CREATE: [CONN_System] ([connector type] — [why])

📊 PROFILES
  🆕 [Entity_Direction_Format]  e.g. Policy_Request_JSON
     Direction: Request/Response/Inbound/Outbound
     Format: JSON/XML/CSV/Flat
     Source: [system]   Fields: ~[N]   Complexity: LOW/MEDIUM/HIGH

🗺️  MAP COMPONENTS
  🆕 MAP_[Source]_TO_[Target]   e.g. MAP_Request_TO_GWPolicy
     Source Profile : [Entity_Direction_Format]
     Target Profile : [Entity_Direction_Format]
     Direct mappings: [N]   Functions needed: [Lookup/Date/Concat/Script]
     Complexity: LOW/MEDIUM/HIGH

⚙️  PROCESS SHAPES — [API_Verb_Resource]
  1. Start          [trigger: API Service/Schedule/Listen/Manual]
  2. Try/Catch
    3.   Connector  [GET/SEND/QUERY/EXECUTE — CONN_System — OperationName]
    4.   Map        [MAP_Source_TO_Target]
  Catch:
    5.   Exception  [error format/HTTP code]

  [Sub-processes use SUB_ prefix, Process Routes use ROUTE_ prefix]
  [Process Properties named PP_Purpose, Document Caches named CACHE_Purpose]
  [Cross Reference Tables named XREF_Source_Target, Operations named Action_Object]

📡 BOOMI APIM DEFINITION (if APIs exposed)
  API Service : [Domain] [API Name] API  e.g. Policy Management API
  API Proxy   : [API Name] Proxy          e.g. Policy Proxy
  Path        : [METHOD /api/v{n}/...]
  Auth        : Entra ID JWT   Linked Process: [API_Verb_Resource]

🚀 DEPLOYMENT TARGET
  Folder         : [pending — confirmed in /migrate Step 5]
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

On `APPROVE PLAN`, do all three things:

1. Confirm to the user: "Plan approved. Run `/migrate` to generate components."

2. Create the **API-specific output folder** immediately using this naming convention:
   `migration-output/boomi-processes/[SourceClass]_API_[Verb]_[Resource]/`
   Example: `ClaimsController_API_GET_Policy/`

   - `[SourceClass]` = the Java class / .NET controller / Python router the API came from
   - `API_[Verb]_[Resource]` = the main process name following the naming convention
   - This groups related APIs from the same service together when sorted alphabetically

3. Save the **Migration Plan document** to that folder:
   `migration-output/boomi-processes/[SourceClass]_API_[Verb]_[Resource]/MIGRATION_PLAN.md`

   Use this structure:

   ```markdown
   # Migration Plan
   **API**: [Method] [Path]
   **Source**: [SourceClass] ([file path])
   **Approved**: [YYYY-MM-DD HH:MM]
   **Target Platform**: Boomi AtomSphere + APIM

   ---

   ## Folder
   migration-output/boomi-processes/[SourceClass]_API_[Verb]_[Resource]/

   ## Components to Create

   ### Connections
   | Name | Type | Action |
   |---|---|---|
   | [CONN_System] | connector-settings | CREATE / REUSE |

   ### Profiles
   | Name | Type | Direction |
   |---|---|---|
   | [Entity_Direction_Format] | profile.json / profile.xml | IN / OUT |

   ### Maps
   | Name | Source Profile | Target Profile |
   |---|---|---|
   | [MAP_Source_TO_Target] | [profile] | [profile] |

   ### Process Shapes
   | # | Step Name | Shape Type | Notes |
   |---|---|---|---|
   | 1 | Start | start | [trigger type + path] |
   | 2 | [name] | [type] | [connector + operation] |
   | 3 | [name] | map | [map component name] |
   | 4 | Return | return | — |

   ## Deployment Target
   | Property | Value |
   |---|---|
   | Boomi Folder | [path — to be confirmed in /migrate] |
   | Atom | [BOOMI_TEST_ATOM_ID from .env] |
   | First deploy | STG |
   | Promote to | PROD (after STG sign-off) |

   ## Build Summary
   | Item | Count |
   |---|---|
   | Total components | [N] |
   | New to create | [N] |
   | Reused from platform | [N] |
   | Groovy scripts | [N] |
   | Complexity | LOW / MEDIUM / HIGH |

   ## Risks
   [bullet list from plan output]
   ```

## Handling CANCEL PLAN
"Plan cancelled. No components generated. Run `/plan` again when ready."
