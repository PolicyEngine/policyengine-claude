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

### Production URLs

Vercel auto-assigns the production URL on first deploy — the exact domain depends on team/name availability (suffixes like `-one`, `-phi`, or `-policy-engine` are common when the base name is taken). Examples of live PolicyEngine zones:

```
working-americans-tax-cut-act-one.vercel.app
keep-your-pay-act.vercel.app
oregon-kicker-refund.vercel.app
household-api-docs-policy-engine.vercel.app
policyengine-model-phi.vercel.app
```

Capture whatever Vercel assigns on the first deploy and hardcode that exact URL anywhere it's needed (host rewrites, apps.json source). Do not assume a deterministic naming scheme, and do not use custom aliases — they may have deployment protection issues.

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
# Set env var (Next.js uses NEXT_PUBLIC_* prefix)
vercel env add NEXT_PUBLIC_API_URL production

# Must force-redeploy after changing env vars
vercel --prod --force --yes --scope policy-engine
```

Next.js apps access env vars via `process.env.NEXT_PUBLIC_API_URL`.

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

### vercel.json

Must be at repo root. For Next.js static exports, configure rewrites as needed:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

## Multi-zone deployments

PolicyEngine tools deploy as **Next.js multi-zones** mounted behind `policyengine.org`. The host (`policyengine-app-v2/website/`) proxies specific paths to each zone's Vercel deployment via `rewrites` in `beforeFiles`.

Before deploying a new tool, make sure you've read `policyengine-interactive-tools-skill` → "Multi-zone integration (preferred)". The Vercel-facing implications:

- **Vercel project URLs are not deterministic.** Vercel auto-assigns the production domain on first deploy (often appending suffixes like `-one`, `-phi`, or `-policy-engine` when the base name is taken). Capture whatever Vercel assigns and hardcode that exact URL in the host rewrite destination. Do not assume a naming convention.
- **Static-export zones need a `vercel.json` self-rewrite** so the zone's own preview can serve prefixed assets:
  ```json
  {
    "framework": "nextjs",
    "rewrites": [
      { "source": "/_zones/<repo-name>/_next/:path*", "destination": "/_next/:path*" }
    ]
  }
  ```
- **Host rewrites must land before the zone is reachable at `policyengine.org`** — add to `policyengine-app-v2/website/next.config.ts` in `rewrites().beforeFiles`, hardcoded to the zone's production Vercel URL. `/deploy-dashboard` handles this after the first deploy captures the production URL.
- **Run `/audit-multizone` before announcing a zone as live** — validates `basePath`, phase-gated `assetPrefix`, `vercel.json` self-rewrite, and host rewrites in one pass.
