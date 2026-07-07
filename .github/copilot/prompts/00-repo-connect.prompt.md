# Connect to Repository

## Mode
Repository Setup — Step 1 of 7 (runs before /analyze)

---

## Step 1: Ask for the Repository

If not already provided, ask:
> "Which repository do you want to migrate to Boomi? Provide a GitHub URL, `org/repo` shorthand, or a local path if already cloned."

## Step 2: Determine Workspace State

**Already open in VS Code?** → skip to Step 4.

**Needs cloning:**
```bash
git clone https://github.com/[org]/[repo-name]
cd [repo-name]
code .

# Or with GitHub CLI (auto-authenticates)
gh repo clone [org]/[repo-name]
cd [repo-name]
code .
```

**Private repo:**
```bash
gh auth status
gh auth login
gh repo clone [org]/[repo-name]
cd [repo-name]
code .
```

Tell the user: "Run those commands, then start a new Copilot Chat session in that workspace and run `/repo-connect` again, or continue with `/analyze`."

## Step 3: Confirm Repository Details

```
✅ REPOSITORY CONNECTED

  Name        : [repo name]
  Language(s) : [Java / .NET / Python / mixed]
  Framework(s): [Spring Boot 3.x / ASP.NET Core / FastAPI / Flask / etc.]
  Source files: [N] detected via @workspace

  Root structure:
  [2-level folder tree]
```

⚠️ Flag any hardcoded credentials, API keys, or PII found during this scan — do not echo them in output.

## Step 4: Verify Copilot Workspace Access

Confirm `@workspace` can see source files. If not:
```
1. Close and reopen VS Code in the repo folder: code .
2. Trust the workspace when prompted
3. Ensure GitHub Copilot extension is active (status bar)
```

## Step 5: Confirm Ready

```
╔══════════════════════════════════════════════════════════════╗
║            🗂️  MIGRATION WORKSPACE ESTABLISHED               ║
╚══════════════════════════════════════════════════════════════╝
  Repository : [org/repo-name]
  Language   : [detected]
  Status     : ✅ Workspace open and readable by Copilot
══════════════════════════════════════════════════════════════
  Run /analyze next to scan the repository and discover APIs.
══════════════════════════════════════════════════════════════
```

Do NOT attempt to access the GitHub API directly or clone repos yourself — all access happens through `@workspace` once the repo is open in VS Code.
