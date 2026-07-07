# Boomi Marketplace Recipe Search & Install

## Mode
Marketplace — run before migrating, to check if a validated starting point exists

Recipes are reference samples from the Boomi community — always inspect and adapt before using in production, never deploy as-is.

## Step 1: Ask What to Search For
> "What system or use case should I search for? e.g. 'Salesforce to PostgreSQL', 'REST API with JSON transformation', 'EDI 850 purchase order'."

## Step 2: Search
Public GraphQL API at `marketplace.boomi.com/graphql` — no auth required for search.
> "Run: `python scripts/boomi_marketplace.py --search \"[term]\"`"

```
🛒 BOOMI MARKETPLACE RESULTS: "[term]"
  #  Bundle ID    Name                     Connectors            Rating  Installs
  1  BC-12345     Salesforce to DB Sync    Salesforce, Database  4.2     1,234
```

## Step 3: Evaluate
- 🟢 USE RECIPE — close match, install and adapt
- 🟡 USE AS REFERENCE — install for pattern guidance, build fresh
- 🔴 BUILD FROM SCRATCH — no useful match, proceed with `/analyze` → `/select-apis` → `/plan` → `/migrate`

## Step 4: Install (if applicable)
Requires `bc-integration` for auth, folder creation, and component management — search itself does not.
```bash
python scripts/boomi_marketplace.py --list-folders
python scripts/boomi_marketplace.py --install [BUNDLE_ID] --folder-id [FOLDER_ID]
python scripts/boomi_pull.py --folder-id [installed-folder-id] --output migration-output/marketplace-recipes/
```

## Step 5: Next Step
- Recipe installed → "Review components in `migration-output/marketplace-recipes/`. If adapting, pull the main process XML and use `/migrate` noting the adaptation."
- No match → "Proceed with the standard workflow: `/analyze` (scores automatically) → `/select-apis` → `/plan` → `/migrate`."
