# Tidy Up Workspace

## Mode
Workspace Maintenance — equivalent to Boomi Companion's `/tidy-up` command

---

```
🧹 TIDY-UP OPTIONS

  1. Light clean    — remove temp files, duplicate drafts, empty folders
  2. Output clean   — clear migration-output/ subfolders (keep approved plans)
  3. Full clean     — reset workspace to template state (WARNING: removes all output)
  4. Show me first  — list what would be deleted before doing anything

Type a number, or describe what you want cleaned.
```

Wait for user response before touching anything.

### Level 1 — Light Clean
Remove `*.tmp`, `*.bak`, `*.draft.*`, empty directories under `migration-output/`, duplicate `-copy`/`-v1`/`-v2` XML files, `__pycache__/` and `.pyc` in `scripts/`.

### Level 2 — Output Clean
Remove: `migration-output/feasibility-reports/*.md`, `migration-output/confluence-docs/*.html`, `migration-output/markdown-docs/*.md`, `migration-output/test-cases/` contents (all re-generatable).
**Keep**: `migration-output/boomi-processes/` (deployed XML, `*-APPROVED-PLAN.md`, `*-MIGRATION-NOTES.md` — audit trail).

### Level 3 — Full Clean
Warn first: "⚠️ FULL CLEAN removes ALL migration-output contents including Boomi XML. Deployed components in AtomSphere are unaffected, but local copies are lost. Type CONFIRM FULL CLEAN to proceed."
Only proceed after explicit confirmation.

### After Cleanup
```
🧹 Tidy-up complete.
Removed: [N] temp/draft files, [N] empty dirs, [size] MB freed
Preserved: migration-output/boomi-processes/ ([N] XML files), preferred_connections.md, [N] APPROVED-PLAN files
Run /analyze to start a new migration.
```
