# Deploy Boomi Components to Environment

## Mode
Deployment — runs after /push has confirmed component IDs

This command packages a pushed component and deploys it to a Boomi runtime
environment (STG or PROD). It does NOT push the component — that was done by
/push. It takes a Component ID and releases it to an environment.

---

## Pre-flight Checks

**Check 1 — Components pushed?**
Has /push completed successfully in this conversation, with component IDs confirmed?
- NO → respond: "Run /push first to get the component uploaded to your Boomi account.
  /deploy needs the Component ID that /push returns." STOP.

**Check 2 — APPROVE PLAN and YES MIGRATE present?**
Are both gates present in this conversation?
- NO → respond: "Run /select-apis and /plan first to establish the migration context." STOP.

---

## Step 1: Confirm What to Deploy

Ask the user:

```
Which process do you want to deploy?
Paste the Component ID from the /push output:  _

Which environment?
  1. STG (staging — always deploy here first)
  2. PROD (production — only after STG validation)
```

Wait for both answers.

If the user says PROD, ask:
> "Has this process been validated on STG? (yes/no)"
If no: "Deploy to STG first. Run /deploy again and choose STG."

---

## Step 2: Run the Deploy Command

Tell the user to run:

```bash
# Deploy to STG
python scripts/boomi_deploy.py --component-id [COMPONENT_ID] --env STG

# Deploy to PROD (only after STG sign-off)
python scripts/boomi_deploy.py --component-id [COMPONENT_ID] --env PROD
```

---

## Step 3: Confirm Result and Show What Next

Ask the user to share the terminal output. Then:

**If successful:**

```
DEPLOY COMPLETE

Process    : [process name]
Environment: [STG / PROD]
Deployment : [deployment ID]

The process is now running in [environment].

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT WOULD YOU LIKE TO DO NEXT?

  /debug      Check execution logs — did the process run correctly?
              (fetch logs, diagnose errors if any)

  /document   Generate TDD, Runbook, API Reference, Confluence page

  /unittest   Review test cases (if not already done)

  /deploy     Deploy another process or promote this one to PROD

Type a command to continue.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**If it fails:**

```
DEPLOY FAILED

Error: [paste the error from terminal]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:

  /debug      Diagnose the error — I'll check the known error patterns
              and suggest a fix

  /push       If you fix the XML on disk, re-push before retrying deploy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Environment Extensions Reminder

If this is the first deployment for a process with new connections, remind the user:

> "Before running the process, configure its credentials in AtomSphere:
> Manage → Atom Management → select your [STG / PROD] environment → Extensions tab
> Set real values for all EXT_* properties the process uses."

---

## Promoting from STG to PROD

The same component ID is used for both environments. After STG validation:

```bash
python scripts/boomi_deploy.py --component-id [SAME_ID] --env PROD
```

No re-push required. The component is already on the platform — /deploy just
packages it again and releases it to the PROD environment.

---

## Undeploying (Rollback)

To remove a deployment from an environment:

```bash
python scripts/boomi_undeploy.py --name "API_GET_Policy" --env STG
```

This removes the deployment without deleting the component.
