# Select APIs for Migration

## Mode
API Selection + Migration Decision — Step 3 of 6 (runs after /analyze)

This command does TWO things in sequence: (1) lets the user pick which scored APIs to migrate, (2) captures the explicit migration approval decision for that selection. No separate /feasibility step is needed afterward — scoring already happened in /analyze.

## Pre-flight Check
Is the API DISCOVERY + FEASIBILITY ASSESSMENT COMPLETE block present (from /analyze)?
- YES → read the numbered, scored API list.
- NO  → ask: "Run /analyze first — it discovers APIs and scores them together."

---

## Step 1: Display the Selection Menu (with scores already visible)

```
╔══════════════════════════════════════════════════════════════════╗
║           🎯  SELECT APIs FOR BOOMI MIGRATION                    ║
╚══════════════════════════════════════════════════════════════════╝
[REPO NAME] — [TOTAL] APIs scored

  SERVICE 1: [ClassName]
    1  GET    /api/v1/orders/{id}           🟢 GREEN
    2  POST   /api/v1/orders                🟢 GREEN
    3  POST   /api/v1/orders/price          🟡 AMBER  (Groovy port needed)
    4  GET    /api/v1/orders/stream         🔴 RED    (WebSocket, not supported)

  NON-API:
   12  SCHEDULED  BatchExportService         🟢 GREEN
   13  EVENT      OrderEventConsumer         🟡 AMBER

──────────────────────────────────────────────────────────────────
HOW TO SELECT:
  Single        → "5"
  Multiple      → "1, 3, 5, 6"
  Range         → "1-4"
  Whole service → "Service 1" or "S1"
  By score      → "ALL GREEN" / "GREEN AND AMBER" / "ALL except RED"
  All           → "ALL"
──────────────────────────────────────────────────────────────────
```

## Step 2: Parse Selection
Resolve the input to a flat list of API numbers, including score-based shortcuts ("ALL GREEN" = every API scored 🟢). If ambiguous, ask for clarification.

If the user selects any RED-scored API, warn explicitly:
> "⚠️ API #[N] is scored RED — [reason]. Boomi is not a suitable platform for this. Do you want to include it anyway (not recommended), or exclude it?"

## Step 3: Confirm Selection

```
╔══════════════════════════════════════════════════════════════════╗
║           ✅  MIGRATION SCOPE CONFIRMATION                       ║
╚══════════════════════════════════════════════════════════════════╝
You selected [N] of [TOTAL] APIs:
  #   Method   Path                    Service            Score
  1   GET      /api/v1/orders/{id}    OrderService       🟢 GREEN
  3   POST     /api/v1/orders/price   OrderService       🟡 AMBER

  Excluded: APIs 2, 4, 12, 13
  Selection profile: GREEN [N]  AMBER [N]  RED [N]
──────────────────────────────────────────────────────────────────
Type CONFIRM SELECTION to proceed to the migration decision, or CHANGE SELECTION to pick again.
──────────────────────────────────────────────────────────────────
```

## Step 4: Migration Decision Gate (folded in here — no separate step needed)

After `CONFIRM SELECTION`, immediately ask:

```
⚠️  MIGRATION DECISION REQUIRED

You are about to approve migration of:
  🟢 GREEN : [N] APIs — direct mapping, low risk
  🟡 AMBER : [N] APIs — needs adaptation, review the risk notes above
  🔴 RED   : [N] APIs — NOT recommended (only if you explicitly included one above)

Type one of:
  YES MIGRATE              — approve all selected APIs (GREEN + AMBER + any RED you explicitly kept)
  YES MIGRATE GREEN ONLY   — approve GREEN only, drop AMBER/RED from this run
  NO STOP                  — halt, do not proceed
```

## Step 5: Lock In

Once a decision is given, output this block — the anchor that `/plan` and `/migrate` check for:

```
╔══════════════════════════════════════════════════════════════════╗
║           🔒  SELECTED APIs — MIGRATION SCOPE LOCKED             ║
╚══════════════════════════════════════════════════════════════════╝
Repository  : [org/repo-name]
Decision    : YES MIGRATE  (or YES MIGRATE GREEN ONLY)
Approved    : [N] APIs

APPROVED API LIST:
  1  GET  /api/v1/orders/{id}          OrderService.java       🟢 GREEN
  3  POST /api/v1/orders/price         OrderService.java       🟡 AMBER

SOURCE FILES IN SCOPE:
  - [full path]/OrderService.java

══════════════════════════════════════════════════════════════════
SCOPE LOCKED AND APPROVED. Run /plan next (recommended for >3 components
or any AMBER modules), or /migrate directly for simple builds.
══════════════════════════════════════════════════════════════════
```

This block must stay in conversation context — `/plan` and `/migrate` both check for the presence of `YES MIGRATE` / `YES MIGRATE GREEN ONLY` within it.

## Handling NO STOP
> "Migration halted. No components will be generated. Run /select-apis again when ready to pick a different scope, or /analyze to re-scan the repo."

## Edge Cases
- Zero selected → "No APIs selected. Please choose at least one."
- All RED → block: "All selected APIs are RED-scored — none are suitable for Boomi migration. Please revise your selection."
- Invalid number → "API #[N] was not found. Check the number and try again."
- Wants to change after lock → "Scope already locked. Type CHANGE SELECTION and re-run /select-apis."
