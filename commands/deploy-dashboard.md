---
description: Deploys a PolicyEngine dashboard to Vercel (and optionally Modal) and registers it in the app
---

# Deploying dashboard: $ARGUMENTS

Deploy a completed PolicyEngine dashboard to production. Run this AFTER merging your feature branch into `main`.

**Precondition:** The user should be on the `main` branch with a clean working tree and the dashboard code merged.

## Step 1: Verify Prerequisites

```bash
# Check we're on main
git branch --show-current

# Check for clean working tree
git status

# Verify build passes
cd frontend && npm ci && npm run build && npx vitest run
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
- `dashboard.name` - for Vercel project and Modal app names
- `data_pattern` - determines if Modal deploy is needed
- `embedding.register_in_apps_json` - determines if apps.json update is needed
- `embedding.slug` - the URL slug for policyengine.org

## Step 3: Deploy Backend (if custom-backend)

**Only if `data_pattern: custom-backend`:**

```bash
cd api

# Deploy to Modal under policyengine workspace
unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET
modal deploy modal_app.py
```

Verify the Modal endpoint is live:
```bash
curl -s -o /dev/null -w "%{http_code}" https://policyengine--DASHBOARD_NAME-calculate.modal.run/health
```

**If deploy fails:** Report error and STOP. Common issues:
- Missing Modal authentication (need `modal token set`)
- Python dependency version conflicts
- Memory/timeout limits

After successful deploy, set the API URL in Vercel:
```bash
vercel env add VITE_API_URL production
# Enter: https://policyengine--DASHBOARD_NAME-calculate.modal.run
```

## Step 4: Deploy Frontend to Vercel

```bash
# Link to Vercel (if not already linked)
vercel link --scope policy-engine

# Deploy to production
vercel --prod --yes
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

| Issue | Fix |
|-------|-----|
| Vercel deploy fails | Check `vercel.json` config, ensure frontend/ builds |
| Modal deploy fails | Check Python deps, Modal auth, function timeouts |
| 404 on Vercel URL | Wait 30s for propagation, check Vercel dashboard |
| API returns errors | Check Modal logs: `modal app logs DASHBOARD_NAME` |
| Hash sync broken | Check postMessage calls in embedding.ts |
