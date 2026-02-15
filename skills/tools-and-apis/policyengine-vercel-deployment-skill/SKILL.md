---
name: policyengine-vercel-deployment
description: Deploying PolicyEngine frontend apps to Vercel - naming, scope, team settings
---

# PolicyEngine Vercel Deployment

Standard patterns for deploying frontend apps (interactive tools, dashboards, static sites) to Vercel under the PolicyEngine team.

## Deployment

### Team and scope

All PE apps deploy under the `policy-engine` Vercel team:

```bash
vercel link --scope policy-engine
vercel --prod --yes --scope policy-engine
```

### Naming convention

Projects use the pattern `policyengine--{repo-name}`:

```
policyengine--marriage.vercel.app
policyengine--aca-calc.vercel.app
policyengine--state-legislative-tracker.vercel.app
```

Vercel auto-assigns a random production URL (e.g., `marriage-zeta-beryl.vercel.app`). Use that in apps.json as the source URL since custom aliases may have deployment protection issues.

### First deploy

```bash
cd my-project

# Link to team (creates .vercel/)
vercel link --scope policy-engine

# Deploy
vercel --prod --yes
```

### Subsequent deploys

```bash
vercel --prod --yes --scope policy-engine
```

### Environment variables

For apps with API backends (e.g., Modal):

```bash
# Set env var
vercel env add VITE_API_URL production

# Must force-redeploy after changing env vars
vercel --prod --force --yes --scope policy-engine
```

Vite apps access env vars via `import.meta.env.VITE_API_URL`.

### Verify deployment

```bash
curl -s -o /dev/null -w "%{http_code}" https://your-app.vercel.app/
# Should return 200
```

### Common issues

**Deployed to personal account:** If `vercel --prod` goes to your personal account, delete `.vercel/` and re-link:
```bash
rm -rf .vercel
vercel link --scope policy-engine
vercel --prod --yes
```

**Deployment protection (401):** Team deployment protection may block unauthenticated access to alias URLs. Use the auto-assigned production URL instead, or configure in Vercel dashboard > Settings > Deployment Protection.

**Generic project names:** Never use generic names like `app` or `site` — they can steal domains from other projects. Always use descriptive names.

### Vite base path

For Vercel, always use `base: "/"` in vite.config.js (unlike GitHub Pages which needs a subpath).

### vercel.json (optional)

Must be at repo root. For SPAs:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```
