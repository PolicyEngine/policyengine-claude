---
name: policyengine-vercel-deployment
description: Deploying PolicyEngine frontend apps to Vercel - naming, scope, team settings
---

# PolicyEngine Vercel deployment

Standard patterns for deploying frontend apps (interactive tools, dashboards, static sites) to Vercel under the PolicyEngine team.

## CRITICAL: scope enforcement

**EVERY Vercel command MUST include `--scope policy-engine`.** No exceptions.

```bash
# CORRECT — always include --scope
vercel link --scope policy-engine
vercel --prod --yes --scope policy-engine
vercel env add VAR production --scope policy-engine

# WRONG — NEVER omit --scope (defaults to personal account)
vercel --prod --yes          # ← WILL DEPLOY TO WRONG ACCOUNT
vercel link                  # ← WILL LINK TO WRONG ACCOUNT
```

**After EVERY deployment, verify the scope:**
```bash
# Check .vercel/project.json to confirm orgId matches policy-engine team
cat .vercel/project.json | grep orgId
# Must show the policy-engine team orgId, NOT a personal account
```

**If `.vercel/` directory already exists**, ALWAYS check it first:
```bash
cat .vercel/project.json
# If orgId doesn't match policy-engine team, delete and re-link:
rm -rf .vercel
vercel link --scope policy-engine
```

## GitHub integration

When connecting a repo to Vercel via GitHub integration:
- The integration MUST be installed under the `policy-engine` Vercel team, NOT a personal account
- Verify in Vercel dashboard: Settings > Git > check that the connected account is `policy-engine`
- If preview deployments show a personal account URL (e.g., `max-ghenis-projects`), the GitHub integration is wrong — it needs to be reconnected under the team

**Root directory setting:** If the app is in a subdirectory (e.g., `frontend/`), set the root directory in Vercel dashboard > Settings > General > Root Directory. The `vercel.json` must be inside that root directory.

## Naming convention

Projects use the pattern `policyengine--{repo-name}`:

```
policyengine--marriage.vercel.app
policyengine--aca-calc.vercel.app
policyengine--state-legislative-tracker.vercel.app
```

Vercel auto-assigns a random production URL (e.g., `marriage-zeta-beryl.vercel.app`). Use that in apps.json as the source URL since custom aliases may have deployment protection issues.

**Never use generic names** like `app` or `site` — they can steal domains from other projects.

## First deploy

```bash
cd my-project

# ALWAYS link to team first
vercel link --scope policy-engine

# Verify link
cat .vercel/project.json  # Confirm orgId is policy-engine team

# Deploy
vercel --prod --yes --scope policy-engine
```

## Subsequent deploys

```bash
vercel --prod --yes --scope policy-engine
```

## Environment variables

For apps with API backends (e.g., Modal):

```bash
vercel env add VITE_API_URL production --scope policy-engine

# Must force-redeploy after changing env vars
vercel --prod --force --yes --scope policy-engine
```

Vite apps access env vars via `import.meta.env.VITE_API_URL`.

## Post-deployment verification checklist

After every deployment, verify ALL of these:

1. **Scope**: `cat .vercel/project.json` — orgId matches policy-engine team
2. **HTTP status**: `curl -s -o /dev/null -w "%{http_code}" https://your-app.vercel.app/` — returns 200
3. **CDN cache**: `curl -sI https://your-app.vercel.app/ | grep -i age` — if age is high, old version is cached; use `--force` to bust cache
4. **Content**: Actually visit the URL or fetch it to confirm the right content is served

## Common issues

**Deployed to personal account:** Delete `.vercel/` and re-link with explicit scope:
```bash
rm -rf .vercel
vercel link --scope policy-engine
vercel --prod --yes --scope policy-engine
```

**GitHub integration on wrong account:** Preview deployments build under a personal account instead of policy-engine. Fix: disconnect the repo in Vercel dashboard, then reconnect it under the policy-engine team's GitHub integration.

**Deployment protection (401):** Team deployment protection may block unauthenticated access to alias URLs. Use the auto-assigned production URL instead, or configure in Vercel dashboard > Settings > Deployment Protection.

## Vite base path

For Vercel, always use `base: "/"` in vite.config.js (unlike GitHub Pages which needs a subpath).

## vercel.json (optional)

Must be inside the root directory configured in Vercel. For SPAs:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```
