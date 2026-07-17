# Analyze Repository — Discover APIs AND Assess Feasibility

## Mode
Combined Discovery + Feasibility — Step 2 of 6 (replaces separate analyze/feasibility split)

This command does BOTH in one pass: finds every API/integration point in the repo, AND scores each one for Boomi migration feasibility, in a single combined output. The user selects from the SCORED list, not a blind list.

## Pre-flight Check
Is the MIGRATION WORKSPACE ESTABLISHED block present (from /repo-connect)?
- YES → use confirmed repo name, language, path.
- NO  → ask: "Please run /repo-connect first."

## Instructions
Use `@workspace` to scan the ENTIRE repository — not just one file.

## Security: Sanitize First
Flag (don't echo) hardcoded credentials, API keys, PII, internal hostnames/IPs found during scanning.

---

## Phase A: Repository Profiling
```
📦 REPOSITORY PROFILE
  Primary language  : [Java / C# .NET / Python / Mixed]
  Frameworks found  : [Spring Boot 3.x / ASP.NET Core 8 / FastAPI / Flask / etc.]
  Source file count : [N]
  Build system       : [Maven / Gradle / dotnet / pip / poetry]
```

## Phase B: API Discovery
Scan for ALL of:
- **Java/Spring**: `@RestController`, `@RequestMapping`/`@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`/`@PatchMapping`
- **.NET**: `[ApiController]`, `[Route]`, `[HttpGet]`/`[HttpPost]`/`[HttpPut]`/`[HttpDelete]`/`[HttpPatch]`
- **FastAPI**: `@app.get/post/put/delete/patch()`, `@router.*()`
- **Flask**: `@app.route()` with `methods=[...]`
- **Non-API**: `@Scheduled`/`IHostedService`/`APScheduler` (batch jobs), `@KafkaListener`/ServiceBus consumers, file watchers/FTP pollers

## Phase C: Feasibility Scoring — apply to EVERY discovered API, not just selected ones

For each API found, assign a score using these rules:
- 🟢 GREEN: stateless, clear input/output, direct connector mapping (REST call, DB CRUD, file transfer, simple routing, format conversion, scheduled batch with clear data flow)
- 🟡 AMBER: possible but needs Groovy scripting, complex config, or workarounds (stateful workflow, complex business rules, distributed transactions, high-frequency >100 TPS, complex regex, OAuth PKCE/device code)
- 🔴 RED: wrong tool for the job (real-time ML inference, complex algorithms, WebSocket/SSE, UI rendering, persistent session state, native OS calls, streaming media, Kafka-scale stream processing)

Do NOT promote AMBER to GREEN to be optimistic. Do NOT mark RED as AMBER unless you have a concrete Boomi workaround.

## Phase D: Combined Output — Numbered, Scored API Inventory

Produce in this EXACT format. Numbers are stable — used by /select-apis next.

```
╔══════════════════════════════════════════════════════════════════╗
║       📋  API DISCOVERY + FEASIBILITY ASSESSMENT COMPLETE        ║
╚══════════════════════════════════════════════════════════════════╝

Repository : [org/repo-name]      Language : [language]
Scanned    : [N] source files     Discovered : [TOTAL] APIs across [M] services

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVICE 1 : [ClassName]   [src/path/to/File.java]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  #  Method  Path                       Handler          Score   Boomi Equivalent           Risk Note
  1  GET     /api/v1/orders/{id}        getOrderById     🟢      HTTP Client Connector       —
  2  POST    /api/v1/orders             createOrder      🟢      HTTP Client + DB Connector  —
  3  POST    /api/v1/orders/price       calculatePrice   🟡      Data Process + Groovy       12-branch pricing logic, needs Groovy port
  4  GET     /api/v1/orders/stream      streamUpdates    🔴      Not supported               WebSocket — use Azure SignalR instead

[repeat per service]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-API INTEGRATION POINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  12  SCHEDULED  @Scheduled cron="0 * * * *"   BatchExportService.java  🟢   Schedule trigger + Connectors
  13  EVENT      @KafkaListener topic=orders   OrderEventConsumer.java  🟡   Event Streams Listen — verify throughput

══════════════════════════════════════════════════════════════════
SUMMARY
  Total APIs/integration points : [N]
  🟢 GREEN : [N]   🟡 AMBER : [N]   🔴 RED : [N]

  Migration scope estimate (if all GREEN+AMBER selected):
  Boomi Processes: ~[N]  Map components: ~[N]  Connections (new): ~[N]  Groovy scripts: ~[N]
══════════════════════════════════════════════════════════════════
Run /select-apis next to choose which APIs to migrate from this scored list.
══════════════════════════════════════════════════════════════════
```

## Rules
- Number all APIs sequentially from 1 across the whole repo (not per-service)
- Include EVERY endpoint found, even RED ones — the score informs the user's choice, it doesn't pre-filter the list
- Skip files with no API endpoints silently (DTOs, utility classes)
- Scheduled jobs and event consumers get numbers and scores too
- Be honest in scoring — this list is what the user picks from, so an inflated GREEN score leads to a bad selection downstream

---

## Save Analysis Report to Disk

After generating the scored API inventory, immediately save it as a markdown file:

**File:** `migration-output/analysis-reports/[RepoName]_ANALYSIS_[YYYYMMDD].md`

Use this structure:

```markdown
# API Analysis Report
**Repository**: [org/repo-name]
**Language**: [Java / .NET / Python / Mixed]
**Date**: [YYYY-MM-DD]
**Scanned**: [N] source files

---

## Repository Profile
| Property | Value |
|---|---|
| Framework | [Spring Boot 3.x / ASP.NET Core / FastAPI / etc.] |
| Build system | [Maven / Gradle / dotnet / pip] |
| Source files | [N] |
| Test files | [N] (excluded) |

---

## API Inventory

| # | Method | Path | Source Class / File | Score | Boomi Equivalent | Risk |
|---|---|---|---|---|---|---|
| 1 | GET | /api/v1/orders/{id} | OrderService.java | GREEN | HTTP Client Connector | — |
| 2 | POST | /api/v1/orders/price | OrderService.java | AMBER | Data Process + Groovy | 12-branch pricing logic |

---

## Non-API Integration Points

| # | Type | Trigger | Source File | Score | Boomi Equivalent |
|---|---|---|---|---|---|
| 12 | SCHEDULED | cron="0 * * * *" | BatchExportService.java | GREEN | Schedule trigger |

---

## Summary

| Score | Count | Description |
|---|---|---|
| GREEN | [N] | Direct Boomi mapping, low risk |
| AMBER | [N] | Possible with adaptation |
| RED | [N] | Not suitable for Boomi |

**Estimated effort (all GREEN + AMBER):**
Boomi Processes: ~[N] · Map components: ~[N] · New connections: ~[N] · Groovy scripts: ~[N]
```

Tell the user:
> "Analysis report saved to `migration-output/analysis-reports/[RepoName]_ANALYSIS_[YYYYMMDD].md`
> Run /select-apis to choose which APIs to migrate."
