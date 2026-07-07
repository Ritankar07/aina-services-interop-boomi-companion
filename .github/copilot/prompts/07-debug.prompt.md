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

| Error Pattern | Root Cause | Fix |
|---|---|---|
| `NullPointerException` in Map | Source field null, no null-check | Add Decision before Map, or null-check function |
| `Connection refused` | Wrong URL/firewall/credentials | Check connection component; verify STG endpoint; check NSG rules |
| `401 Unauthorized` (outbound) | API key expired/wrong | Re-check connection extension credentials |
| `Could not find document` | Empty input | Add empty-document check at Start |
| Shape did not execute | Missing `<dragpoints>` on the shape | Regenerate XML with dragpoints on every shape |
| DPP value is null | `valueType="track"` used for a DPP | Use `valueType="process"` + `<processparameter>` — `track` only reads DDPs |
| Empty-check always fails in Decision | `isempty`/`isnotempty`/`contains` used | These don't exist — use `equals` with empty static value |
| Groovy makes no external call | Sandbox blocks network calls | Move logic to a connector step |
| XML profile fails PUT/POST | Missing `<XMLFlavor>` | Add `<XMLFlavor><CustomStandardFlavor/></XMLFlavor>` |
| Subprocess change has no effect | Parent not redeployed | Redeploy the **parent** process too |
| Log download returns 204/202 | Log still generating | Retry — `boomi_logs.py` already retries 5x automatically |
| Listener crashes on startup | `allowSimultaneous` misconfigured | Check process options for the listener type |
| Map field shows wrong value | Two sources wired to same destination | Only one connection allowed per destination field — find and remove the duplicate |
| Default value always overriding source | Misunderstanding of default behavior | Default only fires when source is null/blank, unless no source is mapped at all |
| `MOVED` error | Redis clustering issue (Azure Cache) | Check atom/molecule Redis config; escalate to infra |
| `Invalid XML/JSON profile` | Input doesn't match declared schema | Re-generate profile from live data sample |

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
