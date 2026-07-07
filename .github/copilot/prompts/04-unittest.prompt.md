# Generate Unit Tests for Migrated Boomi Processes

## Mode
Unit Testing — Step 7b (parallel to /document, or standalone)

For each Boomi process generated in `/migrate`, produce a complete test pack designed to run in **Boomi's built-in Test mode** on a Test Atom.

## For Each Process, Generate

### 1. `test-happy-path.json` (or `.xml`)
Complete, valid input matching the process's input profile. Synthetic data only — no PII, no real system identifiers.

### 2. `test-error-null-fields.json`
Required fields missing/null. Expected: routes to error handling shape.

### 3. `test-error-boundary.json`
Strings: empty, max-length+1, special characters. Numbers: 0, negative, max value. Dates: past, future, invalid format.

### 4. `test-error-wrong-format.json`
Malformed JSON/XML, wrong content type, truncated payload.

### 5. `test-checklist.md`

```markdown
# Test Checklist: [ProcessName]

## Pre-Test Setup
- [ ] Process imported into AtomSphere (STG)
- [ ] Connection components configured with STG credentials (or pulled via boomi_pull.py if REUSE)
- [ ] Test Atom running and connected (BOOMI_TEST_ATOM_ID in .env)

## Running Tests
1. Open process in AtomSphere Process Builder
2. Click Test → select Test Atom → paste test input → Run Test
3. Review shape-by-shape execution

## Test Cases
### TC-001: Happy Path
Input: test-happy-path.json | Expected: completes, output matches schema
Verify: all shapes green, no errors in logs, connector received correct payload

### TC-002: Null Required Fields
Input: test-error-null-fields.json | Expected: Exception shape triggered
Verify: Try/Catch caught it, did NOT reach final connector, error in Process Reporting

### TC-003: Boundary Values
Input: test-error-boundary.json | Expected: [per process design]
Verify: Decision routed correctly, Map handled edge cases, no null pointer in Groovy

### TC-004: Wrong Format
Input: test-error-wrong-format.json | Expected: early failure with descriptive message

## Map Component Testing (separate)
1. Open Map component → Test in Map editor → paste source → verify mapped output

## After All Tests Pass
- [ ] Promote package from Test to STG
- [ ] Smoke test on STG with non-PII sample
- [ ] Review Process Reporting for errors
- [ ] Team lead sign-off before PROD promotion
```

## Groovy Script Test Notes (if applicable)
```markdown
## Groovy Script Test: [ScriptName]
Tested in: Data Process shape → Test mode
### Input / Expected Output
### Common Groovy 2.4 Pitfalls to Check
- [ ] No Java 8+ streams (.stream(), .forEach(), Optional)
- [ ] No `var` keyword
- [ ] No external network calls (sandbox blocks these)
- [ ] dataContext.getStream(i) returned InputStream read fully before storing
- [ ] InputStream not manually closed
```

## Output
Save to `migration-output/test-cases/[ProcessName]/`. After generating:
> "Test pack complete. Follow the test checklist in Boomi Test mode. When tests pass, run `python scripts/boomi_deploy.py --file [...] --env STG`."
