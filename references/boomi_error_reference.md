# Boomi Error Reference
## Error Patterns, Silent Failures, and Troubleshooting

**Source:** Adapted from OfficialBoomi/boomi-integration `references/guides/boomi_error_reference.md`
**Rule:** Read this early in any troubleshooting effort. Most debugging dead-ends trace back to a known pattern here.

---

## Issue #1 — Message Step Quote Escaping with JSON Body

**Symptom:** Variables appear literally as `{1}`, `{2}` etc. in the output. The JSON is returned as-is without substitution.

**Root cause:** Curly braces `{}` in a Message step body are variable substitution markers. Inside JSON, these characters conflict with the JSON syntax and Boomi's substitution parser.

**Fix:** Wrap the entire JSON body in single quotes. Use `'"` and `"'` around each variable inside JSON string values.

```xml
<!-- BROKEN -->
<content><![CDATA[{"orderId":"{1}","status":"active"}]]></content>

<!-- FIXED -->
<content><![CDATA['{"orderId":"'{1}'","status":"active"}']]></content>
```

**Rule:** If the message body is JSON, every `{N}` variable that appears inside a JSON string must be written as `"'{N}'"` (closing the JSON double-quote, opening a single-quote, the variable, closing single-quote, reopening double-quote).

---

## Issue #2 — Environment Variable References in Component XML

**Symptom:** API calls fail with authentication errors, or connection fields contain literal `${ENV_VAR}` text.

**Root cause:** Boomi component XML does not support shell-style `${ENV_VAR}` references. They are stored as-is, not substituted.

**Fix:** Either:
1. Leave credential fields as empty strings and configure via Environment Extensions in AtomSphere UI
2. Use actual values (for non-sensitive config)
3. Use Dynamic Process Properties that are set by a process step, not by XML

**Never** put `${ENV_VAR}` or `PLACEHOLDER_*` in XML that will be pushed to the platform.

---

## Issue #3 — Subprocess Changes Not Reflected

**Symptom:** You updated a subprocess and redeployed it, but the parent process still behaves as before.

**Root cause:** Deploying a subprocess does not automatically trigger a redeploy of its parent. The parent continues running the version it was last deployed with.

**Fix:** After updating a subprocess:
1. Push the subprocess
2. Push the parent process
3. Deploy the **parent** (this bundles the updated subprocess)

If testing the subprocess in isolation, deploy it independently as well.

---

## Issue #4 — Set Properties Step Using Wrong shapetype

**Symptom:** Component pushes but the step doesn't appear to set any properties.

**Root cause:** Using `shapetype="setproperties"` instead of the correct value.

**Fix:**
```xml
<!-- WRONG -->
<step shapetype="setproperties">

<!-- CORRECT -->
<step shapetype="documentproperties">
```

---

## Issue #5 — DPP/DDP valueType Confusion

**Symptom:** A property read gives null or the wrong value.

**Root cause:**
- `valueType="track"` reads **Dynamic Document Properties (DDPs)** — per-document, not persistent across steps
- `valueType="process"` reads/writes **Dynamic Process Properties (DPPs)** — process-wide, accessible at any step

**Fix:**
```xml
<!-- Reading a DPP (process-wide variable) -->
<propertyName valueType="process" name="myPropertyName"/>

<!-- Reading a DDP (document-level variable) -->
<propertyName valueType="track" name="myPropertyName"/>
```

---

## Issue #6 — Map Step with Child Elements

**Symptom:** Map step causes a validation error or doesn't transform data.

**Root cause:** Adding child configuration elements to the map step. The Map step only needs the `mapId` reference.

**Fix:**
```xml
<!-- WRONG — has child elements -->
<step shapetype="map">
  <configuration>
    <mapRef mapId="guid"/>
  </configuration>
</step>

<!-- CORRECT — just the mapId reference -->
<step shapetype="map">
  <map mapId="actual-component-guid"/>
</step>
```

---

## Issue #7 — Component Pushed to Account Root (No Folder)

**Symptom:** Component appears to push successfully but is hard to find. May cause folder quota or organization issues.

**Root cause:** `folderId` attribute missing or empty in the component XML.

**Fix:** Always include a valid `folderId` in every component XML:
```xml
<bns:Component ... folderId="actual-folder-guid-here">
```

Get the folder ID by running:
```bash
python scripts/boomi_folder.py --path "YOUR/FOLDER/PATH" --create-if-missing
```

---

## Issue #8 — Wrong XML Structure (Validation Error on Push)

**Symptom:** Push fails with a platform validation error.

**Common causes:**

| Problem | Wrong | Correct |
|---|---|---|
| Set Properties shapetype | `shapetype="setproperties"` | `shapetype="documentproperties"` |
| Missing `name` attribute | `<step shapetype="map">` | `<step name="My Map Step" shapetype="map">` |
| Process Component closing | `</bns:ProcessDefinition>` without dragpoints | Every `<step>` needs `<dragpoints>` child |
| Map step has body | `<step shapetype="map"><map>...</map></step>` | `<step shapetype="map"><map mapId="guid"/></step>` |

**General approach:** Read the exact error from the platform response, identify the problematic element, compare against reference documentation.

---

## Issue #9 — REST Connector Selected Over HTTP Client (or Vice Versa)

**Symptom:** Connection or step works differently than expected.

**Rule:** Always use the REST connector (`connectorType="officialboomi-X3979C-rest-prod"`) unless the user explicitly requests HTTP Client or you are modifying an existing HTTP Client component.

The connectorType values are different:
- REST: `connectorType="officialboomi-X3979C-rest-prod"`
- HTTP Client: `connectorType="http"`

---

## Issue #10 — Missing dragpoints

**Symptom:** Step appears in Component Explorer (push succeeded) but does nothing during execution. No error thrown.

**Root cause:** Missing `<dragpoints>` element on the step.

**Fix:** Every step in a valid process XML must include `<dragpoints>`:
```xml
<step name="My Step" shapetype="connector" ...>
  <dragpoints>
    <dragpoint fromStepId="previous-step-id" toStepId="this-step-id"/>
  </dragpoints>
  <!-- rest of step config -->
</step>
```

---

## Issue #11 — Component Created With Placeholder GUIDs

**Symptom:** Process pushes successfully but fails at runtime with "component not found" or similar.

**Root cause:** A step in the process references a component GUID that doesn't exist on the platform (e.g., a placeholder value or a GUID from a different account/environment).

**Fix:** Always push components in dependency order. Each component pushed to the platform returns a real GUID. Use that GUID in the next component before pushing it.

**Dependency order:**
```
Profile components → Connection components → Operation components → Process (referencing all above GUIDs)
```

---

## Issue #12 — Zero Documents Flowing Through

**Symptom:** Process executes without error but produces no output or downstream steps don't run.

**Root cause:** A step produced zero output documents. This silently stops the pipeline for that path.

**Diagnostic steps:**
1. Add Notify steps immediately after each connector/map to log the document count and payload
2. Check if the connector is returning data (look at execution logs for the connector step)
3. Verify the profile matches the actual data structure being received
4. Check if a Decision step is routing all documents away from the expected path

---

## Issue #13 — Execution Log Returns 204

**Symptom:** `boomi_logs.py --download` returns empty or the log file is not available.

**Root cause:** HTTP 204 means the log is still being generated, not that it's empty.

**Fix:** `boomi_logs.py` already retries automatically on 202/204. If still not available after 5 retries, wait 30 seconds and run again. Logs expire after 30 days.

---

## Issue #14 — Trading Partner Process Blocks Other Executions

**Symptom:** Trading partner process runs, but while it's running no other executions of the same process can start.

**Root cause:** `allowSimultaneous="false"` (the default) prevents concurrent executions.

**Fix for Trading Partner processes:** Set `allowSimultaneous="true"` in the process definition:
```xml
<bns:ProcessDefinition allowSimultaneous="true" ...>
```

---

## Issue #15 — Groovy Script Network Call Blocked

**Symptom:** Groovy script in a Data Process step silently fails or throws `SecurityException`.

**Root cause:** Boomi's Groovy sandbox blocks all external network calls. You cannot use `URL`, `HttpURLConnection`, or any HTTP library in Groovy scripts.

**Fix:** Move any external API call to a REST Connector step before or after the Data Process step. Pass data via Dynamic Process Properties.

---

## Quick Diagnostic Reference

| What you see | First thing to check |
|---|---|
| Variable appears as `{1}` literally | Issue #1: JSON quote escaping in Message step |
| Credentials not working in XML | Issue #2: No `${ENV_VAR}` in XML — use Environment Extensions |
| Subprocess change ignored | Issue #3: Redeploy parent process |
| Set Properties does nothing | Issue #4: Wrong shapetype |
| Property value is null | Issue #5: DPP vs DDP — check valueType |
| Map step validation error | Issue #6: Remove all child elements from map step |
| Component hard to find | Issue #7: Missing folderId |
| Push validation error | Issue #8: Compare XML against step reference docs |
| Step does nothing, no error | Issue #10: Missing dragpoints |
| Runtime "component not found" | Issue #11: PLACEHOLDER GUIDs — push dependencies first |
| No output, no error | Issue #12: Zero documents — add Notify steps to trace |
| 204 on log download | Issue #13: Retry — log still generating |
