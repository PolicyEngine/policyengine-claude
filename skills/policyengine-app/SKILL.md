---
name: policyengine-app
description: |
  Load when developing policyengine-app-v2 — the site served at policyengine.org.
  Covers the bun/turbo monorepo, the Next.js 15 App Router host in website/, the legacy
  Vite SPA in app/ being migrated, ui-kit + designTokens theming, multizone rewrites, and
  how the frontend calls the PolicyEngine API.
  Triggers: policyengine-app-v2, policyengine.org, app-v2, website host, App Router page,
  server component split, appZoneRoutes, multizone rewrite, designTokens, BASE_URL,
  household calc from the app, economy over baseline, calculator app, bun run build.
  NOT for: building a standalone embedded tool (use policyengine-tools), design tokens in
  isolation (policyengine-design), or the API server itself (policyengine-api).
metadata:
  category: apps
---

# PolicyEngine app v2

`PolicyEngine/policyengine-app-v2` is the frontend served at **policyengine.org**. It is
mid-migration: a **Next.js 15 App Router host lives in `website/`** and is the live apex,
while a **legacy Vite SPA in `app/`** still owns the calculator surface and is being ported
page by page. Verify the current stack from `package.json` files before trusting any summary
— this repo moves fast.

## Monorepo layout

Bun workspaces + Turbo (`packageManager: bun@1.2.21`, root `turbo.json`). Workspaces:
`packages/*`, `app`, `website`, `calculator-app`.

| Path | What | Bundler |
|---|---|---|
| `website/` | `@policyengine/website` — Next.js 15 App Router **host** (live apex, marketing/research/tools) | Next 15 + Turbopack |
| `app/` | `policyengine-app-v2` — legacy Vite SPA (calculator: policies, households, reports, simulations) | Vite 6 |
| `calculator-app/` | standalone calculator workspace | Vite |
| `packages/` | shared workspace packages | — |

Root scripts run through Turbo: `bun run build` → `turbo run build`; `bun run dev` runs the
Next host (`scripts/dev-server-next.mjs`); `bun run dev:legacy` runs the Vite app.

## Tech stack (verified from package.json)

There is **no third-party component framework** — UI is built from radix-ui primitives plus
local components. Do not add one.

- `website/`: `next` ^15.3.3, `radix-ui` ^1.4.3, `@tabler/icons-react`, `tailwindcss` v4
  (`@tailwindcss/postcss`), `class-variance-authority`, `react` 19, `react-plotly.js` (maps),
  `framer-motion`, `fuse.js`, `react-markdown`.
- `app/`: `vite` 6, `react-router-dom` 7, `@tanstack/react-query`, `@reduxjs/toolkit` +
  `react-redux`, `recharts` ^3.7.0, `@tabler/icons-react`, `tailwindcss` v4
  (`@tailwindcss/vite`), Storybook.
- Both pin **`@policyengine/ui-kit` ^0.4.0**. See the policyengine-design skill for its API.

`useDisclosure` / `useMediaQuery` / `useViewportSize` in `app/src/hooks/` are local
reimplementations — not a dependency.

## App Router page pattern (website/)

Pages live under `website/src/app/[countryId]/<slug>/`. The convention is a **server
`page.tsx`** (exports `metadata`, awaits `params`) that renders a **`*Client.tsx`** client
component:

```tsx
// website/src/app/[countryId]/claude-plugin/page.tsx  (server)
import type { Metadata } from "next";
import ClaudePluginClient from "./ClaudePluginClient";
export const metadata: Metadata = { title: "Claude plugin", description: "..." };
export default async function Page({ params }: { params: Promise<{ countryId: string }> }) {
  const { countryId } = await params;               // params is a Promise in Next 15
  return <ClaudePluginClient countryId={countryId} />;
}
```

Styling is a **hybrid**: Tailwind v4 utilities use a `tw:` prefix
(`className="tw:block tw:no-underline"`) and inline styles pull from JS design tokens
(`import { colors, spacing, typography } from "@/designTokens"`). `@/components/ui` exports
local `Text` / `Title` / etc. The JS tokens are a **local shim**: `app/src/designTokens/`
(`colors.ts`, `spacing.ts`, `typography.ts`) is a runtime object kept in sync with ui-kit's
`theme.css` during migration, and `website/src/designTokens` re-exports it. Never hardcode
hex — use the token.

## Multizone routing

New cross-app rewrites go in **`website/next.config.ts`**, not the root `vercel.json` (which
is legacy: favicons, SPA catch-all, pre-multizone proxies). External Next tools are
registered in **`website/src/data/appZoneRoutes.ts`** (`appZoneRewrites`, spread into
`rewrites().beforeFiles` so zones beat the dynamic `[slug]` route). `afterFiles` proxies
Modal/Vercel/GitHub-Pages apps (tracker, slides, taxsim, model docs). A CI guard fails PRs
that add country-prefixed `*.vercel.app` rewrites to `vercel.json`. Full zone mechanics
(basePath, assetPrefix, self-rewrites) are in the policyengine-tools skill.

## Calling the API

The legacy calculator calls the **v1 API** (`app/src/constants.ts`:
`BASE_URL = 'https://api.policyengine.org'`). Verified shapes:

- `GET  {BASE_URL}/{country}/household/{id}` and `.../household/{id}/policy/{policyId}` — household calc
- `POST {BASE_URL}/{country}/household` — create household
- `GET  {BASE_URL}/{country}/economy/{reformPolicyId}/over/{baselinePolicyId}?region=&time_period=&dataset=`
  — society-wide; **async/polling** (`status: "computing" | "ok" | "error"`, `queue_position`,
  `average_time`, `result`)

An **api-v2 alpha adapter** lives in `app/src/api/v2/` (`API_V2_BASE_URL =
process.env.NEXT_PUBLIC_API_V2_URL || 'https://v2.api.policyengine.org'`, endpoints per
policyengine-api-v2-alpha PR #77). It is async job + poll, and CRUD for households/policies/
simulations. Variation/axes calls are **not** in v2 and remain on v1. See the
policyengine-api skill for both APIs.

## Verification discipline

- **`curl` is NOT verification.** An SPA (and a streamed Next page) returns a 200 HTML shell
  whether or not React renders. The reliable compile check is **`bun run build`** (catches
  import/type/missing-dep errors).
- **You cannot visually verify a frontend.** After a green build and a running dev server,
  tell the user it is ready to check in the browser — never claim it "looks good."
- Before claiming the dev server is up, check the port: `lsof -i :3000` (Next host) or
  `lsof -i :5173` (Vite app). Do not assume.
- When `bun install` fails, try at most 2 fixes, then ask. Never `rm -rf node_modules`,
  hand-extract tarballs, or edit the lockfile.
- **Sentence case** on all UI text ("Your saved policies", not "Your Saved Policies").
  Exceptions: proper nouns (PolicyEngine), acronyms (IRS), official names (Child Tax Credit).

## Key files

| File | Purpose |
|---|---|
| `website/next.config.ts` | Multizone rewrites, redirects, icon rewrites |
| `website/src/data/appZoneRoutes.ts` | Registry of external Next zones |
| `website/src/app/[countryId]/<slug>/page.tsx` | Server page + client split |
| `app/src/constants.ts` | `BASE_URL` (v1 API) |
| `app/src/api/` and `app/src/api/v2/` | v1 fetchers and v2 alpha adapter |
| `app/src/designTokens/` | Local JS token shim (re-exported by website) |
| `vercel.json` (root) | Legacy config — do not add new zone rewrites here |

## Related skills

- policyengine-tools — standalone embedded tools + full multizone zone config
- policyengine-design — ui-kit 0.4.0 components and design tokens
- policyengine-api — v1 and v2 API surfaces
- policyengine-writing — content and copy style
