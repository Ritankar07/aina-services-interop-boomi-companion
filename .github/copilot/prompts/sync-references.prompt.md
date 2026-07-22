# Sync Boomi Reference Files

## Mode
Reference Sync — check the official OfficialBoomi/bc-integration repository for
updates and pull any changes into the local references/ folder.

Run this periodically to keep your Boomi knowledge base current as Boomi evolves
its connectors, adds new step types, or fixes documented patterns.

---

## When to Run This

- Before starting a major migration (ensure you have the latest patterns)
- When you hit an unexpected error that isn't in the known error reference
- After Boomi releases a new platform version
- Periodically (monthly is a reasonable cadence for most teams)

---

## Step 1: Check What Has Changed

Tell the user to run the check first — no files are downloaded yet:

```bash
python scripts/sync_boomi_references.py --check
```

This makes **one GitHub API call** to get the file tree from the official repo,
compares SHA hashes against the local sync state, and prints a report like:

```
  Last synced : 2026-06-15T08:30:00Z
  Unchanged   : 91 file(s)

  ADDED (2 new file(s) in official repo):
     + steps/mcp_connector_step.md
     + components/mcp_connector_operation_component.md

  MODIFIED (3 file(s) changed upstream):
     ~ components/rest_connection_component.md
     ~ steps/message_step.md
     ~ guides/boomi_error_reference.md

  Run with --apply to download these 5 change(s).
```

---

## Step 2: Review What Changed

Before downloading, ask the user if they want to know what the upstream changes
actually contain. If they want to check manually:

> "You can view any changed file at:
> `https://github.com/OfficialBoomi/bc-integration/blob/main/skills/boomi-integration/references/[filename]`"

---

## Step 3: Apply the Updates

Once the user is ready to download:

```bash
python scripts/sync_boomi_references.py --apply
```

This downloads ONLY the changed files — not the unchanged ones. Each downloaded
file is written to the local `references/` folder, overwriting the old version.
The local sync state file (`references/.sync-state.json`) is updated.

**For a complete refresh** (re-download everything even if unchanged):
```bash
python scripts/sync_boomi_references.py --apply --force
```

---

## Step 4: Commit the Updates

After applying, tell the user to commit the updated files to Git so the whole
team gets the latest reference docs:

```bash
git add references/
git commit -m "chore: sync Boomi reference files from OfficialBoomi/bc-integration [date]"
git push
```

---

## Rate Limits

The GitHub API allows 60 requests/hour without authentication. This sync uses
**only 1 API call** (for the tree), then downloads via `raw.githubusercontent.com`
(which has no enforced rate limit). So rate limits should never be a problem.

If you see a 403 rate limit error on the tree call:
- Add a GitHub Personal Access Token to your `.env`: `GITHUB_TOKEN=ghp_yourtoken`
- Or pass it directly: `python scripts/sync_boomi_references.py --check --token ghp_yourtoken`
- An authenticated call allows 5,000 requests/hour

---

## About DELETED Files

If the official repo removes a file, `--check` will show it as DELETED.
When you run `--apply`, the script removes it from the sync state but
**keeps your local copy** — it will not delete files from your disk.

If you want to remove a deleted file:
```bash
git rm references/[path/to/file.md]
git commit -m "chore: remove reference file deleted upstream"
```

---

## After Sync — Restart VS Code

After applying updates, restart VS Code so Copilot re-indexes the workspace
and picks up the new/updated reference files.

The next time you run `/migrate` or `/debug`, Copilot will automatically read
the updated reference files for any component types or steps involved.
