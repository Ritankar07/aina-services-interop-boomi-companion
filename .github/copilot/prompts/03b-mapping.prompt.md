# Build or Fix a Boomi Map Component

## Mode
Mapping Skill — callable standalone (`/mapping`) or invoked automatically during `/migrate`

This is the dedicated skill for designing, generating, and debugging Boomi Map components and Map Functions — the most frequently needed and most error-prone part of any migration. Source: verified official help.boomi.com Map component and Map Function documentation, folded into `copilot-instructions.md`.

---

## When to Use This

- Standalone: user asks "build me a map from X to Y" or "fix this broken mapping"
- Automatically invoked: Step 5.3 of `/migrate` generation (Map Component Definition)
- Debugging: user reports a field isn't mapping correctly, or a function is returning unexpected results

---

## Step 1: Gather Inputs

If not already provided, ask:
> "What's the source format and destination format for this map? (e.g. JSON → XML, source code object → ImageRight API request). If you have sample payloads for either side, share them — they make the field mapping far more accurate than guessing from a schema alone."

---

## Step 2: Build the Field Mapping Matrix

For every field, decide ONE of these mapping types — never more than one per destination field (Boomi only allows a single connection into a destination step):

| Mapping Type | When to Use |
|---|---|
| **Direct** | Source and destination types match exactly, no transformation needed |
| **Direct + Default** | Source mapped, but falls back to a default if source is null/blank |
| **Always-Default** | No source field exists; destination always gets a static default value |
| **Standard Function** | Single-step transform: uppercase, date reformat, math, string ops, lookup |
| **User-Defined Function** | Multi-step chained transform — build once, reuse across maps |
| **Custom Script** | Only when no standard/user-defined function covers the logic — LAST RESORT |
| **Cross Reference Table** | Lookup against a reference dataset (exact/wildcard/regex match) |

Produce the matrix:

```
🗺️  FIELD MAPPING MATRIX — [MapName]

| # | Source Field | Source Type | Dest Field | Dest Type | Mapping Type | Function/Notes |
|---|---|---|---|---|---|---|
| 1 | firstName | String | FirstName | String | Direct | — |
| 2 | statusCode | Integer | Status | String | Standard Function | Lookup: 1→OPEN, 2→CLOSED |
| 3 | — | — | RetrievedAt | DateTime | Always-Default | Current date/time function |
| 4 | discountPct | Decimal | FinalPrice | Decimal | Custom Script | Multi-tier calc — see script below |
```

---

## Step 3: Apply the Verified Mapping Rules

Before finalizing, check each row against these rules:

1. **Default value behavior**: if a row has both a source AND a default, confirm the user understands the default only fires on null/blank — it does NOT override a present value.
2. **Date/Number auto-formatting**: if source and destination are both Date/Time or Number types with masks defined, map directly — no function needed. Only add a function for non-standard reformatting.
3. **One connection per destination**: verify no destination field appears twice in the matrix from two different sources.
4. **Boomi Suggest**: offer it as a starting point — "I can use Boomi Suggest as a first pass, but I'll verify every suggested mapping against your actual schemas rather than trusting it blindly."

---

## Step 4: Design Functions

### For Standard Functions
List the exact function type needed (e.g. "Date Format: ISO8601 → MM/dd/yyyy", "String: Uppercase", "Math: Multiply by 100").

### For User-Defined Functions (multi-step)
If the same multi-step transform will be reused across multiple maps in this migration, design it as a User-Defined function:
```
USER-DEFINED FUNCTION: [Name]
  Step 1: [standard function] — input: [field] → output: [intermediate]
  Step 2: [standard function] — input: [intermediate from step 1] → output: [final]
  Function output → mapped to: [destination field]
```
Note: "Get Functions Require Input" is ON by default — any Get-type function step needs input data to execute.

### For Custom Scripts (last resort only)
Before writing a script, confirm: "No standard or user-defined function combination covers this logic — this requires a custom Groovy script."

```groovy
// Groovy 2.4 — Boomi sandbox blocks external network calls.
// JsonSlurper IS available natively.
import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    // Read fully before storing — do not close InputStream manually
    String content = is.text
    def json = new JsonSlurper().parseText(content)

    // [transformation logic here — no network calls]

    Properties props = dataContext.getProperties(i)
    dataContext.storeStream(new ByteArrayInputStream(outputContent.bytes), props)
}
```

---

## Step 5: Cross Reference Table (if any lookups needed)

```
CROSS REFERENCE TABLE: [Name]
  Match type: EXACT / WILDCARD / REGEX
  Columns: [source column] → [target column]
  skipLookupIfNoInputs: [true/false]
  Behavior: case-insensitive, first-row-wins, empty string on no-match
```

---

## Step 6: Generate the Map Component XML

Produce the Map component XML following the structure in `copilot-instructions.md`'s XML reference, with the field mapping matrix from Step 2 fully wired, functions from Step 4 embedded, and any Cross Reference Table referenced as a parameter source.

Save as: `migration-output/boomi-processes/[ProcessName]/MAP-[FROM]-TO-[TO].xml`

---

## Step 7: Map Extensions (if STG/PROD need different defaults)

If the user mentions environment-specific default values (e.g. different fallback values in STG vs PROD), don't create separate map components — note this as a Map Extension:
```
MAP EXTENSION NEEDED: [MapName]
  Field: [field name]
  STG default : [value]
  PROD default: [value]
  Configure via: AtomSphere → Environment → Extensions → Map Extensions
```

---

## Debugging an Existing Map

If the user reports a mapping problem:
1. Ask for the actual input payload and the actual (wrong) output
2. Check in order: (a) is the destination field receiving two connections? (b) is a default value firing when it shouldn't, or not firing when it should? (c) is a Date/Number field that should auto-format instead routed through an unnecessary function? (d) is a function's cache setting (`None`/`By Document`/`By Map`) causing stale data?
3. Recommend: "Unmap fields one at a time, starting from the problem field, to isolate exactly where the data diverges from expected — this is the fastest way to debug a complex map."
4. If a Groovy script is involved, check for sandbox network-call violations and Groovy 2.4 syntax compliance (no `var`, no Java 8+ streams, no `Optional`).

---

## Output Summary

After completing a mapping task, always end with:
```
Map component ready: MAP-[FROM]-TO-[TO]
  Direct mappings    : [N]
  Functions used     : [N] ([Standard]/[User-Defined]/[Custom Script breakdown])
  Cross Reference    : [N] tables referenced
  Map Extensions flagged: [N] (if any)

Run /unittest to generate test payloads for this map, or continue with /migrate to wire it into the full process.
```
