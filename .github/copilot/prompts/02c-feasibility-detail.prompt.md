# Deep-Dive Feasibility Re-Assessment (Optional)

## Mode
Optional standalone command — NOT part of the main workflow gate anymore.

> **Note**: As of this workflow version, feasibility scoring happens automatically inside `/analyze`, and the migration decision (`YES MIGRATE`) is captured inside `/select-apis`. You do NOT need to run this command as part of the normal flow.

## When to Use This Command
Use `/feasibility-detail` standalone only when you want a deeper, more detailed re-assessment of one or more specific APIs beyond the summary score given in `/analyze` — for example, an AMBER-scored API where you want the full risk breakdown, effort estimate, and a written recommendation before committing.

## Pre-flight
Ask: "Which API number(s) from the /analyze output do you want a deep-dive feasibility report on?" If the user hasn't run /analyze yet, tell them to run it first — it already includes scoring for every API.

## Deep-Dive Report Format

```markdown
# Deep-Dive Feasibility Report
**API**: [# and path]   **Score from /analyze**: [GREEN/AMBER/RED]

## What It Does
[detailed description]

## Boomi Approach
[specific shapes/connectors/Groovy needed]

## What's Lost or Changed
[honest assessment of gaps vs original code]

## Effort Estimate
[Small/Medium/Large, with reasoning]

## Recommendation
[Proceed as-is / Proceed with caveats / Reconsider — with reasoning]
```

This report is informational only — it does NOT change the locked scope from `/select-apis`. If you want to change which APIs are in scope after reading this, run `/select-apis` again with `CHANGE SELECTION`.
