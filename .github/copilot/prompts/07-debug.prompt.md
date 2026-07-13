# Debug Boomi Process — Execution Log Analysis

## Mode
Debugging — post-deployment, or whenever a process fails

## Step 1: Identify the Process
Ask for process name or execution ID if not provided.

## Step 2: Fetch Execution Records
```bash
python scripts/boomi_logs.py --process-name "PROCESS-NAME" --count 5
python scripts/boomi_logs.py --execution-id "executionId-abc123" --download
python scripts/boomi_logs.py --process-name "PROCESS-NAME" --status ERROR --hours 24
```

## Step 3: Known Error Pattern Reference

**Read `references/boomi_error_reference.md` first** — it contains the complete, sourced error pattern table. Quick reference of the most common ones:

| Error Pattern | Root Cause | Fix |
|---|---|---|
| Variable appears as `{1}` literally in output | JSON quote escaping in Message step | Wrap JSON body in single quotes, use `'"'{1}'"'` pattern |
| Connection auth fails, credentials look right | `${ENV_VAR}` in XML — not substituted | Use empty strings in XML, configure via Environment Extensions |
| Subprocess change ignored | Parent not redeployed | Push subprocess → push parent → deploy parent |
| Set Properties does nothing | `shapetype="setproperties"` wrong | Use `shapetype="documentproperties"` |
| Property value is null | Wrong valueType | DPP = `valueType="process"`, DDP = `valueType="track"` |
| Map step validation error | Child elements on map step | Only `<map mapId="guid"/>`, no children |
| Component pushed, step does nothing | Missing `<dragpoints>` | Add dragpoints to every step |
| Runtime "component not found" | PLACEHOLDER GUIDs in process XML | Push all dependencies first, use real GUIDs |
| No output, no error | Zero documents from a step | Add Notify steps to trace the pipeline |
| 204 on log download | Log still generating | boomi_logs.py retries automatically — wait or retry |
| Groovy network call fails | Sandbox blocks network | Move to REST Connector step |
| Trading Partner blocks concurrent runs | `allowSimultaneous="false"` | Set to `true` for TP start processes |
| XML profile fails PUT/POST | Missing XMLFlavor element | Add `<XMLFlavor><CustomStandardFlavor/></XMLFlavor>` |

See `references/boomi_error_reference.md` for full details on all 15 patterns.

## Step 4: Produce Diagnosis

```
🔍 EXECUTION LOG ANALYSIS
Process: [name]   Execution: [ID]   Status: ERROR/WARNING/SUCCESS
Shape: [where error occurred]   Error: [exact message]   Pattern: [matched/UNKNOWN]

Root Cause: [plain language]
Recommended Fix: [steps]

Type FIX IT to generate the corrected component, or MANUAL to fix in the UI.
```

## Step 5: Apply Fix (if requested)
1. Show exact XML change
2. Confirm: "Apply this fix? YES/NO"
3. If YES → update XML in `migration-output/boomi-processes/[ProcessName]/`
4. "Run `python scripts/boomi_deploy.py --file [...] --env STG` to redeploy."

---

## BOOMI_THINKING — Tiered Problem-Solving Framework

### Tier 1: Known Error Reference (table above) — check first, always

### Tier 2: Diagnostic Approach
1. Add a Notify shape before the failing shape with `valueType="current"` to log document state
2. Check Process Reporting — full log shows which shape failed and what document it received
3. Use Test mode with the Test Atom — step through interactively
4. Check batch vs single-document behavior — some shapes differ on empty/multiple documents

### Tier 3: Platform Documentation Fallback
1. Fetch `https://developer.boomi.com/docs` for the specific component/shape
2. Fetch `https://help.boomi.com` for platform behavior
3. Run a minimal reproduction in Test mode
4. Document the finding — may be an undocumented platform quirk

### Tier 4: Escalation
- Boomi support (paid accounts)
- `community.boomi.com`
- `developer-offerings@boomi.com` for Boomi Companion-specific issues
