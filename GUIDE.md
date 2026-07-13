# Boomi Migration Workflow Guide

## Architecture

```
Source Code (Java / .NET / Python)
        |
  /repo-connect    <- establish workspace
        |
  /analyze         <- scan repo + score every API GREEN/AMBER/RED
        |
  /select-apis     <- pick from scored list, confirm YES MIGRATE
        |
  /plan            <- full build blueprint -> APPROVE PLAN
        |
  /migrate         <- generates XML files locally
        |              then shows: "What next? /push /document /unittest"
        |
  /push            <- uploads components to Boomi account
        |              then shows: "What next? /deploy /document /unittest /debug"
        |
  /deploy          <- packages + deploys to STG (then PROD after validation)
        |              then shows: "What next? /debug /document /unittest"
        |
  /debug           <- fetch logs, diagnose, fix -> /push -> /deploy again
```

Optional at any point in any order:
  /document  Generate TDD, Runbook, Confluence page
  /unittest  Generate test cases and Boomi Test mode checklist
  /mapping   Build or fix a Map component standalone

---

## Why the Flow Is Split This Way

| Step | What it does | Why separate |
|---|---|---|
| /migrate | Creates XML files on your disk | Review before touching the platform |
| /push | Uploads components to Boomi account | Review in AtomSphere UI before deploying |
| /deploy | Packages + deploys to an environment | Explicit environment selection (STG/PROD) |

Each step shows a menu of what to do next so you always know the path forward.

---

## Phase-by-Phase

### 1. /repo-connect
Connect to the source code repo. Provides `git clone` instructions or confirms
@workspace can see an already-open folder.

### 2. /analyze
Scans the ENTIRE repo. Every API endpoint gets scored GREEN/AMBER/RED inline.
No separate feasibility step needed.

### 3. /select-apis
Pick from the scored list (by number, range, "ALL GREEN", etc.).
Confirms migration scope with YES MIGRATE. Gates everything downstream.

### 4. /plan
Previews every component to be created: folder structure, connections (REUSE vs CREATE),
profiles, maps, process shapes. Type APPROVE PLAN when satisfied.

### 5. /migrate
Reads the official reference files for each component and step type, then generates
the XML files locally — one subfolder per API under migration-output/boomi-processes/.
After generation shows: /push /document /unittest

### 6. /push
Uploads the generated XML to your Boomi account. Returns component IDs.
After push shows: /deploy /document /unittest /debug

### 7. /deploy
Takes a component ID from /push and deploys it to STG or PROD.
After deploy shows: /debug /document /unittest

### Optional: /document
Generates TDD, Integration Spec, Runbook, Migration Record, API Reference, or Full Pack.
Pushes to Confluence or outputs Markdown.

### Optional: /unittest
Generates test data files and a Boomi Test mode step-by-step checklist.

### /debug (when things go wrong)
Fetches execution logs, matches errors against the official Boomi error reference,
suggests fixes. Fix the XML on disk, re-run /push, re-run /deploy.

---

## Quick Reference

| Command | What It Does |
|---|---|
| /repo-connect | Connect to the source code repo |
| /analyze | Scan repo and score every API GREEN/AMBER/RED |
| /select-apis | Pick APIs to migrate and confirm YES MIGRATE |
| /plan | Build blueprint -> APPROVE PLAN |
| /migrate | Generate XML files locally -> shows what-next menu |
| /push | Upload components to Boomi account -> shows what-next menu |
| /deploy | Package + deploy to STG or PROD -> shows what-next menu |
| /document | Generate documentation (any type, any format) |
| /unittest | Generate test cases and checklist |
| /debug | Diagnose failures from execution logs |
| /mapping | Build or fix a Map component standalone |
| /pull-component | Pull and modify existing AtomSphere components |
| /marketplace | Search Boomi Marketplace before building from scratch |
| /feasibility-detail | Optional deep-dive on one API (does not change scope) |
| /tidy | Clean workspace artifacts |
