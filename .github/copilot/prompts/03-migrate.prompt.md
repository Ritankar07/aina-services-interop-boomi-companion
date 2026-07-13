# Generate Boomi Components — Push-As-You-Go Workflow

## Mode
Migration — Steps 5–7 of 7

## CRITICAL: Read These Before Generating Any XML

Before generating ANY component XML, read the files listed below for each component type
you are about to create. If a file doesn't exist yet, run `python scripts/clone_boomi_references.py` first.

**Always read first (every time):**
- `references/BOOMI_THINKING.md`
- `references/boomi_error_reference.md`

**Then read the specific file for each component you're creating:**

| Component to create | File to read |
|---|---|
| Process | `references/components/process_component.md` |
| JSON Profile | `references/components/json_profile_component.md` |
| XML Profile | `references/components/xml_profile_component.md` |
| REST Connection | `references/components/rest_connection_component.md` |
| REST Operation | `references/components/rest_connector_operation_component.md` |
| Map | `references/components/map_component.md` + `references/components/map_component_functions.md` |
| Document Cache | `references/components/document_cache_component.md` |
| Cross Reference | `references/components/cross_reference_table_component.md` |
| Process Property | `references/components/process_property_component.md` |

**And the specific step file for each step in your process:**

| Step type | File to read |
|---|---|
| Start | `references/steps/start_step.md` |
| REST Connector | `references/steps/rest_connector_step.md` |
| Map | `references/steps/map_step.md` |
| Message | `references/steps/message_step.md` |
| Set Properties | `references/steps/set_properties_step.md` |
| Decision | `references/steps/decision_step.md` |
| Try/Catch | `references/steps/try_catch_step.md` |
| Notify | `references/steps/notify_step.md` |
| Return Documents | `references/steps/return_documents_step.md` |
| Process Call | `references/steps/process_call_step.md` |
| Data Process/Groovy | `references/steps/data_process_step.md` + `references/steps/data_process_groovy_step.md` |
| Branch | `references/steps/branch_step.md` |
| Route | `references/steps/route_step.md` |
| Exception | `references/steps/exception_step.md` |

**Rule:** READ BEFORE WRITING. Validation errors almost always mean the XML doesn't match the documented structure. The reference file for that component or step type has the working example.

---

## Pre-flight Checks

**Check 1 — Scope locked and approved?**
`SELECTED APIs — MIGRATION SCOPE LOCKED` with `YES MIGRATE` present?
- NO → "Run /select-apis first." STOP.

**Check 2 — Plan approved?**
`APPROVE PLAN` present?
- YES → use it as the authoritative component list.
- NO + complex build (>3 components or any AMBER) → "Run /plan first, or type SKIP PLAN."

**Check 3 — Folder confirmed?**
Ask:
```
📁 BOOMI FOLDER PATH — REQUIRED

Where in AtomSphere should these components be placed?
Example: Policy Management/REST APIs

Or type "default" to use BOOMI_TARGET_FOLDER from .env.

Folder path: _
```
If custom path given:
```bash
python scripts/boomi_folder.py --path "[path]" --create-if-missing
```
Paste the Folder ID back. Confirm before proceeding.

**Check 4 — Connection reuse**
Check `preferred_connections.md`. REUSE connections are NOT generated — just note their GUID.

---

## The Only Correct Build Order

**Follow this order without exception. Never skip a level.**

```
Level 1: PROFILES        — push first, capture GUIDs
Level 2: CONNECTIONS     — push second, use profile GUIDs if needed
Level 3: OPERATIONS      — push third, reference connection + profile GUIDs
Level 4: MAPS            — push fourth, reference source + target profile GUIDs
Level 5: PROCESS         — push last, reference connection + operation + map GUIDs
Level 6: DEPLOY          — after all components exist on platform
```

---

## What to Generate Per API

For each selected API, work through the levels in order.

### Level 1: Profiles

Create ONE profile per data structure involved. Name: `<Entity>_<Direction>_<Format>`.

For each profile:
1. Generate the profile XML (see `references/boomi_component_guide.md`)
2. Tell the user:
```bash
python scripts/boomi_push.py \
  --file migration-output/boomi-processes/API_GET_Policy/Policy_Request_JSON.xml \
  --folder-id [FOLDER_ID]
```
3. Ask user to paste the **Component ID** returned
4. Record: `Policy_Request_JSON → componentId: [pasted-id]`
5. Repeat for every profile

**Do not proceed to Level 2 until all profile IDs are confirmed.**

### Level 2: Connections

For REUSE connections (from `preferred_connections.md`):
- Ask user to pull the existing connection: `python scripts/boomi_pull.py --name "CONN_SystemName"`
- Capture the componentId from the pulled XML
- Do NOT generate new XML for REUSE connections

For CREATE connections:
1. Generate connection XML with empty credential fields (never fill credentials into XML)
2. Push and capture component ID
3. Tell user: "After all components are pushed, configure credentials in AtomSphere → Environment Extensions"

### Level 3: Operations

Generate operation XML using:
- Real connection GUID from Level 2
- Real profile GUIDs from Level 1 (for request/response profiles)

Push and capture component ID.

### Level 4: Maps

Generate map XML using:
- Real source profile GUID from Level 1
- Real target profile GUID from Level 1

Apply mapping rules from `references/boomi_component_guide.md`:
- `<map mapId="ACTUAL_GUID"/>` — no child elements
- One destination field = one source connection only

Push and capture component ID.

### Level 5: Process

Generate process XML using ONLY real GUIDs captured from levels 1-4.
**No PLACEHOLDER values. No made-up GUIDs. Only real IDs from pushed components.**

Apply structural rules from `references/boomi_component_guide.md`:
- Every step has `<dragpoints>`
- Message step with JSON: single-quote escaping (`'{"key":"'{1}'"}'`)
- Set Properties: `shapetype="documentproperties"` NOT `"setproperties"`
- Map step: `<map mapId="guid"/>` with no child elements
- Decision: `equals`/`notequals` operators only — no isempty/isnotempty/contains

Push and capture component ID.

### Level 6: Deploy

After all components for ALL selected APIs are pushed:
```bash
python scripts/boomi_deploy.py --component-id [PROCESS_ID] --env STG
```

---

## Component Naming Convention

Apply to EVERY component generated:

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
| **Operation** | `<Action>_<Object>` | `GET_Policy` |
| **Process Property** | `PP_<Purpose>` | `PP_API_Config` |
| **Environment Extension** | `EXT_<Property>` | `EXT_BaseURL` |
| **Cross Reference Table** | `XREF_<Source>_<Target>` | `XREF_ProductCode` |
| **Document Cache** | `CACHE_<Purpose>` | `CACHE_AccessToken` |

---

## Output Folder Structure — One Folder Per API

```
migration-output/boomi-processes/
└── API_GET_Policy/
      API_GET_Policy.xml            ← Level 5 (process)
      Policy_Request_JSON.xml       ← Level 1 (profile)
      Policy_Response_JSON.xml      ← Level 1 (profile)
      CONN_Guidewire.xml            ← Level 2 (connection — CREATE only)
      GET_Policy.xml                ← Level 3 (operation)
      MAP_Request_TO_GWPolicy.xml   ← Level 4 (map)
      API_GET_Policy-MIGRATION-NOTES.md
```

---

## Migration Notes File

```markdown
# Migration Notes: [API_Verb_Resource]
**Source**: [file/class + endpoint]   **Migration Date**: [date]
**Boomi Folder**: [path]              **Folder ID**: [real GUID]

## Component IDs (record after each push)
| Component | Type | ID |
|---|---|---|
| Policy_Request_JSON | profile.json | [real GUID] |
| Policy_Response_JSON | profile.json | [real GUID] |
| CONN_Guidewire | connector-settings | [real GUID or REUSE] |
| GET_Policy | connector-action | [real GUID] |
| MAP_Request_TO_GWPolicy | transform.map | [real GUID] |
| API_GET_Policy | process | [real GUID] |

## Connections
- REUSE: [list from preferred_connections.md with GUIDs]
- CREATED: [list new with push order]

## Environment Extensions Required
- CONN_Guidewire → baseUrl: EXT_GuidewireBaseURL
- CONN_Guidewire → apiKey: EXT_GuidewireAPIKey
(Configure these in AtomSphere → Environment → Extensions after push)

## Known Gaps vs Original Code
[Honest list of anything not fully replicated]
```

---

## Post-Generation — Show What Next

After ALL XML files are written to disk, output this menu exactly:

```
╔══════════════════════════════════════════════════════════════╗
║           ✅  COMPONENTS READY                               ║
╚══════════════════════════════════════════════════════════════╝

Generated files:
  migration-output/boomi-processes/[API_Verb_Resource]/
  [one line per API folder created]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT WOULD YOU LIKE TO DO NEXT?

  /push       Upload components to your Boomi account
              (required before /deploy)

  /document   Generate TDD, Runbook, API Reference, Confluence page

  /unittest   Generate test cases and Boomi Test mode checklist

Type a command to continue. Run /push first if you want to deploy.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Do NOT include push commands, deploy commands, or component IDs in this output.
Those steps are handled by /push and /deploy respectively.

---

## Post-Deploy: Test-Fix-Retest (if /deploy was run and a step fails)

If the user reports a failure after deploying:
1. Fetch logs: `python scripts/boomi_logs.py --process-name "[name]" --count 1 --download`
2. Match error to `references/guides/boomi_error_reference.md`
3. Fix the specific component XML file on disk
4. Re-run `/push` to sync the fix to the platform
5. Re-run `/deploy` to redeploy
