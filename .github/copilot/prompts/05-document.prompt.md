# Generate Documentation for Migrated Boomi Processes

## Mode
Documentation Generation — Step 7a (parallel to /unittest, or standalone)

## Step 1: Ask the User (required — do not skip)

```
What type of document do you want?
  1. Technical Design Document (TDD)
  2. Integration Specification
  3. Operations Runbook
  4. Migration Record
  5. API Reference
  6. Test Plan & Results
  7. Full Pack (all of the above)

What output format?
  Confluence (recommended)  |  Markdown  |  Both
```
Wait for both answers before generating.

## Templates

### TDD
Sections: Document Control, Executive Summary, Architecture Overview (pattern, runtime, trigger, auth, Interop Layer placement), Component Inventory, **Data Flow Diagram (text + arrows — see spec below)**, Numbered Steps, Data Mapping (reference the Mapping Skill matrix from `/mapping`), Error Handling, Security Considerations, Non-Functional Requirements, Deployment Notes, Open Items/Risks.

**Data Flow Diagram spec (required in every TDD and Integration Spec):**

Generate a text-based data flow inside a Confluence `noformat` macro. Use plain ASCII characters (`|`, `v`, `-->`) so it renders correctly in any Confluence theme.

Confluence Storage Format:
```xml
<ac:structured-macro ac:name="noformat">
<ac:plain-text-body><![CDATA[
[Source / Caller]
    |
    | HTTPS + JWT Bearer Token
    v
Boomi APIM Gateway
    |-- JWT Validation (Entra ID)
    |-- Rate Limiting
    |
    | Internal routing
    v
[Main Process Name]  (Boomi AtomSphere)
    |
    | [protocol] [method] [path]
    v
[CONN_SystemName]  -->  [Target System / External API]
    |
    | [Response format, e.g. JSON]
    v
[MAP_Source_TO_Target]  (Data Transformation)
    |
    v
Response returned to [Source / Caller]
]]></ac:plain-text-body>
</ac:structured-macro>
```

Fill in the actual values from the migration. Examples:
- Source: `Client Application`, `Scheduled Trigger`, `Event Stream`
- Protocol line: `REST GET /api/v1/policies/{policyId}`, `SFTP file write`, `JMS message publish`
- Target: `Guidewire Core`, `ImageRight REST API`, `PostgreSQL Claims DB`

For multi-step processes, show each intermediate step:
```
[Source]
    |
    v
APIM Gateway --> JWT validation
    |
    v
API_GET_Policy
    |
    |--> CONN_Guidewire --> Guidewire API (GET /policies/{id})
    |         |
    |         v
    |    Response (Policy JSON)
    |
    v
MAP_GWPolicy_TO_Canonical (transform)
    |
    v
Response to Client (Canonical JSON)
```

For error paths, add a branch:
```
    |--> [On Error] Try/Catch --> Exception Step --> HTTP 502 to Client
```

### Integration Specification
Integration Identity, Interface Contract (direction/protocol/frequency/SLA), Source System Details, Target System Details, **Data Flow Diagram (same text+arrow format as TDD — required)**, Payload Spec (request/response examples), Field Mapping Matrix, Error Codes, Test Endpoints.

### Operations Runbook
Service Overview, Health Checks, Common Errors & Resolutions (include: empty document body, 401 token expiry, Atom offline, dragpoints missing, subprocess not redeployed), Restart Procedure, Reprocessing Failed Documents, Deployment Runbook, Rollback Procedure, Contacts.

### Migration Record
Migration Summary, Scope (from feasibility report), Module Migration Map (source function → feasibility score → Boomi component → status), Adaptations Made, Excluded Items, Validation Evidence, Known Gaps.

### API Reference
API Overview, Authentication (Entra ID token flow), Endpoints (method/path/headers/params/body examples/response codes), Error Reference, Changelog.

### Test Plan & Results
Test Scope, Test Environment, Test Cases table (reference `/unittest` output), Defects Found, Sign-off.

### Full Pack
Generate all 6 as separate Confluence pages under one parent, in order: TDD → Integration Spec → Migration Record → API Reference (if APIM endpoints exist) → Test Plan → Operations Runbook.

## Confluence Storage Format Rules
```xml
<h1>Title</h1>
<table><tbody><tr><th>H</th></tr><tr><td>C</td></tr></tbody></table>
<ac:structured-macro ac:name="info"><ac:rich-text-body><p>Info</p></ac:rich-text-body></ac:structured-macro>
<ac:structured-macro ac:name="warning"><ac:rich-text-body><p>Warning</p></ac:rich-text-body></ac:structured-macro>
<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">xml</ac:parameter><ac:plain-text-body><![CDATA[code]]></ac:plain-text-body></ac:structured-macro>
<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Green</ac:parameter><ac:parameter ac:name="title">APPROVED</ac:parameter></ac:structured-macro>
```

## Output
- Confluence: `migration-output/confluence-docs/[ProcessName]-[DocType].html`
- Markdown: `migration-output/markdown-docs/[ProcessName]-[DocType].md`

After generating:
> "Documentation generated. Push to Confluence: `python scripts/confluence_push.py --folder migration-output/confluence-docs/ --space YOUR_SPACE_KEY`"
