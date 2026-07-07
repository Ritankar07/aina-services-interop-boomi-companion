# Pull Existing Component from AtomSphere

## Mode
Component Pull — modify or extend a component already on the platform

## Step 1: Get the Component ID
> "Please provide the component ID (UUID format) or name. Find it in Component Explorer → right-click → Properties, or from the AtomSphere URL."

## Step 2: Pull
```bash
python scripts/boomi_pull.py --component-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
python scripts/boomi_pull.py --component-id "..." --with-dependencies
python scripts/boomi_pull.py --folder-id "..."
python scripts/boomi_pull.py --name "CLAIMS-INBOUND-IMRIGHT-REST"
```
Output saved to `migration-output/pulled-components/[ComponentName]/`.

## Step 3: Review

```
📥 COMPONENT PULLED
Component: [name]   Type: process/map/connection/profile   ID: [UUID]

PULLED:
  ✅ [ComponentName].xml
  ✅ [DependencyName].xml (dependency)
  ⚠️  Credentials NOT included (by design — encrypted on platform)

WHAT IT DOES: [2-3 sentence summary]
SHAPES (if process): [numbered list, Plan Mode format]
CONNECTIONS USED: [list, cross-referenced against preferred_connections.md]
```

## Step 4: Decide
```
A) Modify it    → describe changes, I'll update the XML
B) Extend it    → add shapes/connectors/logic to the existing process
C) Reference    → keep in pulled-components/ for reference only
D) Replace it   → generate new version via /migrate, deploy over this one
```

## Step 5: Apply (if A or B)
1. User describes changes
2. Show what will change (plan-style) before generating
3. User confirms
4. Update XML
5. `python scripts/boomi_deploy.py --file [...] --env STG`

**Rules when modifying pulled components:**
- Never change the component's UUID — must match for the update to replace it on the platform
- Preserve component name/type unless intentionally renaming
- Only modify contents of `<bns:object>`, not outer `<bns:Component>` attributes
- New connection references must exist on the platform or be added to `preferred_connections.md`
- Every shape still needs `<dragpoints>` — don't strip these during edits
