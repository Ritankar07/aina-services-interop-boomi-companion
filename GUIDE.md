# Boomi Migration Workflow Guide

## Architecture

```
Source Code (Java / .NET / Python)
        ↓
  /repo-connect    ← establish workspace
        ↓
  /analyze         ← @workspace scan + GREEN/AMBER/RED scoring, ONE combined pass
        ↓
  /select-apis     ← user picks from the SCORED list, then confirms YES MIGRATE
        ↓
  /plan ★          ← full build blueprint (recommended >3 components or any AMBER)
        ↓
   APPROVE PLAN
        ↓
  /migrate         ← prompts for Boomi folder path, generates XML
        │             (Map components built via /mapping logic)
        ↓
  /document + /unittest
        ↓
  boomi_push.py --file [xml]                  ← push to Boomi account, get component ID
        ↓
  boomi_deploy.py --component-id [ID] --env STG   ← package + deploy to STG
        ↓
  test-fix-retest loop (see /debug)
        ↓
  boomi_deploy.py --component-id [ID] --env PROD
```

★ Skip Plan Mode only for simple single-process builds with clear 1:1 mappings.

> Honest constraint: Copilot is conversational, not autonomous — each phase is a chat command you invoke. `YES MIGRATE` and `APPROVE PLAN` are literal human gates. The test-fix-retest retry loop within `/debug` is automated; moving between major phases is not.

---

## Why Analyze and Feasibility Are Now Combined

Earlier versions of this workflow ran discovery (`/analyze`) and feasibility scoring (`/feasibility`) as two separate steps, with scoring happening only AFTER API selection. That meant you picked APIs blind, then found out their feasibility afterward — backwards from how you'd actually want to decide.

Now `/analyze` does both in one pass: every discovered API gets a GREEN/AMBER/RED score immediately, in the same list. `/select-apis` then lets you pick from that scored list — including shortcuts like "ALL GREEN" or "GREEN AND AMBER" — and captures the `YES MIGRATE` decision as part of confirming your selection. No separate gate, no blind picking.

If you want a deeper write-up on one specific AMBER API beyond its one-line score, `/feasibility-detail` is still available as an optional standalone command — it does not change your locked scope.

---

## Phase-by-Phase

### 1. Repo Connect
`/repo-connect` — clone/open the source repo, confirm Copilot can see it via `@workspace`.

### 2. Analyze (discovery + feasibility combined)
`/analyze` — full repo scan. Outputs a numbered, GREEN/AMBER/RED-scored inventory of every REST endpoint, scheduled job, and event consumer, with a Boomi component mapping and risk note per item.

### 3. Select APIs + Decide
`/select-apis` — pick a subset by number, range, service name, "ALL", or by score ("ALL GREEN", "GREEN AND AMBER"). After confirming the selection, you're immediately asked the migration decision: `YES MIGRATE` / `YES MIGRATE GREEN ONLY` / `NO STOP`. This locks the scope for everything downstream.

### 4. Plan Mode
`/plan` — shows folder structure, connections (REUSE from `preferred_connections.md` vs CREATE), profiles, map components, process shapes in order, deployment target, and a risk summary. Iterate with `MODIFY PLAN: [changes]` until `APPROVE PLAN`.

### 5. Migrate
`/migrate` — checks the locked+approved scope, then asks for the Boomi folder path (or "default" to use `BOOMI_TARGET_FOLDER`). Generates process XML, connection stubs (CREATE only), Map components (using the verified Mapping Skill rules), and migration notes.

### 5b. Mapping (standalone or auto-invoked)
`/mapping` — dedicated skill for building or debugging a Map component: field mapping matrix, default-value rules, Standard/User-Defined/Custom-Script function selection, Cross Reference Tables, Map Extensions.

### 6. Document & Test
`/document` asks document type and format. `/unittest` generates happy-path, null-field, boundary, and malformed-input test cases plus a Boomi Test mode checklist.

### 7. Push + Deploy

**Step 1 — Push to your Boomi account** (component appears in AtomSphere, no environment yet):
```bash
python scripts/boomi_push.py --file migration-output/boomi-processes/[Name]/[Name].xml
```
Copy the **Component ID** printed in the output. Open AtomSphere → Component Explorer to review the component before deploying.

**Step 2 — Deploy to STG** (package + release to environment):
```bash
python scripts/boomi_deploy.py --component-id [ID from Step 1] --env STG
```

After STG sign-off:
```bash
python scripts/boomi_deploy.py --component-id [ID] --env PROD
```

### Post-Deploy: Test-Fix-Retest
```bash
python scripts/boomi_logs.py --process-name "[name]" --count 1 --download
```
If it fails, run `/debug` — checks the known-error table first, then diagnostic steps, platform docs, escalation.

---

## Quick Reference

| Command | Phase |
|---|---|
| `/repo-connect` | 1 |
| `/analyze` | 2 — discovery + scoring combined |
| `/select-apis` | 3 — selection + YES MIGRATE decision combined |
| `/plan` then `APPROVE PLAN` | 4 |
| `/migrate` | 5 |
| `/mapping` | 5b |
| `/document` / `/unittest` | 6 |
| `/push` | 6b — push generated XML to Boomi account, get component IDs, no deployment |
| `boomi_push.py --file [xml]` | 7a — push component to Boomi account, get component ID |
| `boomi_deploy.py --component-id [ID] --env STG` | 7b — package + deploy to STG |
| `boomi_deploy.py --component-id [ID] --env PROD` | 7c — promote to PROD |
| `/debug` | post-deploy |
| `/pull-component` | modify existing components |
| `/marketplace` | check before building from scratch |
| `/feasibility-detail` | optional — deep dive on one API, doesn't change scope |
| `/tidy` | workspace cleanup |
