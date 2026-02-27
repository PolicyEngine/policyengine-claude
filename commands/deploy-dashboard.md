---
description: Deploys a PolicyEngine dashboard to Vercel (and optionally Modal) and registers it in the app
---

# Deploying dashboard: $ARGUMENTS

Deploy a completed PolicyEngine dashboard to production. Run this AFTER merging your feature branch into `main`.

**Precondition:** The user should be on the `main` branch with a clean working tree and the dashboard code merged.

## Skills Used

- **policyengine-vercel-deployment-skill** — Frontend deployment (all dashboards)
- **policyengine-modal-deployment-skill** — Backend deployment (only if `custom-backend` pattern)

## Step 1: Verify Prerequisites

```bash
# Check we're on main
git branch --show-current

# Check for clean working tree
git status

# Verify build passes
npm ci && npm run build && npx vitest run
```

**If not on main:** Tell the user to merge their feature branch first:
> You're currently on branch `{branch}`. Please merge into `main` first:
> ```bash
> git checkout main
> git merge {branch}
> git push
> ```
> Then run `/deploy-dashboard` again.

**If build fails:** Report the error and STOP. Do not deploy broken code.

## Step 2: Read the Plan

```bash
cat plan.yaml
```

Extract:
- `dashboard.name` — for Vercel project and Modal app names
- `data_pattern` — determines if Modal deploy is needed (`custom-backend` vs `api-v2-alpha`)
- `tech_stack.framework` — should be `react-nextjs` (env var prefix: `NEXT_PUBLIC_*`)
- `embedding.register_in_apps_json` — determines if apps.json update is needed
- `embedding.slug` — the URL slug for policyengine.org

## Step 3: Deploy Backend (if custom-backend)

**Only if `data_pattern: custom-backend`.** If `api-v2-alpha`, skip to Step 4.

See `policyengine-modal-deployment-skill` for the full Modal deployment reference.

### 3a. Authentication check (human gate)

```bash
modal token info
modal profile list
```

Present the output to the user. Verify:
- Active profile is `policyengine`
- Workspace is `policyengine`

**If authentication fails or shows wrong workspace:**

> **Modal authentication required.** Your CLI is not configured for the `policyengine` workspace.
>
> Please run:
> ```bash
> modal token new --profile policyengine
> modal profile activate policyengine
> ```
>
> If you don't have access, ask a PolicyEngine workspace owner for an invite.

**Do NOT proceed until `modal token info` shows `Workspace: policyengine`.**

### 3b. Environment selection (human gate)

Ask the user which Modal environment to deploy to:

> Which Modal environment should this deploy to?
>
> - **main** — Production (default)
> - **staging** — Pre-production testing
> - **testing** — Development/CI

Default to `main` for production deployments.

### 3c. Deploy

```bash
# Guard against env var override
unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET

# Deploy to the selected environment
modal deploy modal_app.py --env SELECTED_ENV
```

### 3d. Verify endpoint

Construct the URL from the app name and function name in `modal_app.py`:

- Pattern: `https://policyengine--APP_NAME-FUNCTION_NAME.modal.run`
- With non-main environment: `https://policyengine-ENV--APP_NAME-FUNCTION_NAME.modal.run`

```bash
# Health check (if endpoint exists)
curl -s -w "\n%{http_code}" https://policyengine--DASHBOARD_NAME-health.modal.run

# Test the calculation endpoint
curl -s -X POST https://policyengine--DASHBOARD_NAME-calculate.modal.run \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

**If deploy fails:** Report error and STOP. See the `policyengine-modal-deployment-skill` troubleshooting table.

### 3e. Set API URL in Vercel

After successful Modal deploy, set the API URL as a Vercel environment variable.

```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://policyengine--DASHBOARD_NAME-calculate.modal.run
```

## Step 4: Deploy Frontend to Vercel

See `policyengine-vercel-deployment-skill` for the full Vercel deployment reference.

```bash
# Link to Vercel under PolicyEngine team (if not already linked)
vercel link --scope policy-engine

# Deploy to production
vercel --prod --yes --scope policy-engine
```

If a Modal backend was deployed in Step 3, force-rebuild to pick up the new env var:
```bash
vercel --prod --force --yes --scope policy-engine
```

Capture the production URL from the output.

Verify the deployment:
```bash
curl -s -o /dev/null -w "%{http_code}" https://VERCEL_PRODUCTION_URL/
```

**IMPORTANT:** Use the auto-assigned Vercel production URL, not a custom alias. Custom aliases may have deployment protection issues.

## Step 5: Register in apps.json (if applicable)

**Only if `embedding.register_in_apps_json: true`:**

This requires a PR to `PolicyEngine/policyengine-app-v2`.

```bash
# Clone app-v2 if not already available
gh repo clone PolicyEngine/policyengine-app-v2 /tmp/policyengine-app-v2

cd /tmp/policyengine-app-v2
git checkout move-to-api-v2
git checkout -b add-DASHBOARD_NAME-tool
```

Add entry to `app/src/data/apps/apps.json`:

```json
{
  "type": "iframe",
  "slug": "SLUG",
  "title": "TITLE",
  "description": "DESCRIPTION",
  "source": "VERCEL_PRODUCTION_URL",
  "tags": ["COUNTRY", "policy", "interactives"],
  "countryId": "COUNTRY",
  "displayWithResearch": true,
  "image": "SLUG-cover.png",
  "date": "CURRENT_DATE 12:00:00",
  "authors": ["AUTHOR_SLUG"]
}
```

Ask the user for:
- Author slug (check existing entries for format)
- Cover image (if `displayWithResearch: true`)

```bash
git add app/src/data/apps/apps.json
git commit -m "Register DASHBOARD_NAME interactive tool"
git push -u origin add-DASHBOARD_NAME-tool

gh pr create --repo PolicyEngine/policyengine-app-v2 \
  --title "Register DASHBOARD_NAME tool" \
  --body "Adds DASHBOARD_NAME to the interactive tools listing.

Source: VERCEL_PRODUCTION_URL
Slug: /COUNTRY/SLUG"
```

## Step 6: Smoke Test

After deployment:

1. **Direct URL:** Visit the Vercel production URL, verify the dashboard loads
2. **Embedded (if registered):** After apps.json PR merges, verify at `policyengine.org/COUNTRY/SLUG`
3. **Hash sync:** Test that URL parameters work (add `#income=50000` etc.)
4. **Country detection:** Test with `#country=uk` if the dashboard supports multiple countries

## Step 7: Report

Present deployment summary to the user:

> ## Dashboard deployed
>
> - **Live URL:** VERCEL_PRODUCTION_URL
> - **Vercel project:** DASHBOARD_NAME
> [If custom backend:]
> - **API endpoint:** https://policyengine--DASHBOARD_NAME-calculate.modal.run
> - **Modal environment:** SELECTED_ENV
> [If registered:]
> - **apps.json PR:** PR_URL (will be available at policyengine.org/COUNTRY/SLUG after merge)
>
> ### Verify
> - [ ] Dashboard loads at the Vercel URL
> - [ ] Calculations work (or stubs respond correctly)
> - [ ] Hash parameters are preserved on refresh
> [If registered:]
> - [ ] After apps.json PR merges, dashboard embeds correctly in policyengine.org

## Error Recovery

| Issue | Fix | Reference |
|-------|-----|-----------|
| Vercel deploy fails | Check `vercel.json` config, ensure project builds | `policyengine-vercel-deployment-skill` |
| Modal deploy fails | Check Python deps, Modal auth, function timeouts | `policyengine-modal-deployment-skill` |
| Wrong Modal workspace | `modal profile activate policyengine` | `policyengine-modal-deployment-skill` |
| 404 on Vercel URL | Wait 30s for propagation, check Vercel dashboard | `policyengine-vercel-deployment-skill` |
| API returns errors | Check Modal logs: `modal app logs DASHBOARD_NAME` | `policyengine-modal-deployment-skill` |
| Hash sync broken | Check postMessage calls in embedding.ts | `policyengine-interactive-tools-skill` |
