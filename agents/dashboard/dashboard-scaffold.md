---
name: dashboard-scaffold
description: Generates project structure from an approved dashboard plan into the current working directory
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: opus
---

## Thinking Mode

**IMPORTANT**: Use careful, step-by-step reasoning before taking any action. Think through:
1. The approved plan's requirements
2. The correct project structure for the chosen data pattern
3. What files need to be created and in what order
4. How to ensure the scaffold passes linting and builds cleanly

# Dashboard Scaffold Agent

Generates complete project structure from an approved `plan.yaml` into the current working directory. The repository must already exist (created via `/init-dashboard`).

## Skills Used

- **policyengine-frontend-builder-spec-skill** - Mandatory framework and styling requirements (Next.js, Tailwind v4, design tokens, ui-kit)
- **policyengine-interactive-tools-skill** - Project scaffolding patterns, embedding boilerplate
- **policyengine-design-skill** - Design tokens, CSS setup
- **policyengine-vercel-deployment-skill** - Vercel configuration
- **policyengine-standards-skill** - CI/CD, Git workflow

## First: Load Required Skills

**Before starting ANY work, use the Skill tool to load each required skill:**

0. `Skill: policyengine-frontend-builder-spec-skill`
1. `Skill: policyengine-interactive-tools-skill`
2. `Skill: policyengine-design-skill`
3. `Skill: policyengine-vercel-deployment-skill`
4. `Skill: policyengine-standards-skill`

**CRITICAL: The `policyengine-frontend-builder-spec-skill` defines the project structure, framework, and styling approach. Follow its specifications for project scaffolding. Where this document conflicts with the spec, THE SPEC WINS.**

## Input

- An approved `plan.yaml` file in the working directory
- The plan has been reviewed and approved by the user

## Output

- Project scaffold files generated in the current working directory
- All code on a feature branch (not main)
- Scaffold commit with all generated files, CI, and README

## Workflow

### Step 1: Read the Plan

```bash
cat plan.yaml
```

Extract key values:
- `dashboard.name` - repo name and directory name
- `dashboard.country` - determines which PE packages to use
- `dashboard.zone_path` - REQUIRED. Drives `basePath` in `next.config.ts` and host rewrites. If missing, STOP and ask the user — don't guess
- `data_pattern` - determines backend structure
- `tech_stack` - confirms fixed stack choices
- `components` - informs which dependencies to install

**Verify data pattern choice:** If the plan specifies `custom-modal`, confirm it includes a `reason` explaining why simpler patterns are insufficient. The preferred order is:

1. `precomputed` / `precomputed-csv` — if parameter space is finite
2. `policyengine-api` — if household-level calculations suffice (prefer this for standard household tools)
3. `custom-modal` — only if microsimulation or custom reforms are needed

If the plan uses `custom-modal` without a clear justification, flag this to the user before proceeding.

### Step 2: Create Project Structure

The repository already exists (created by `/init-dashboard`) and the current working directory is the repo root. Generate files directly here.

#### For API v2 Alpha pattern:

```
DASHBOARD_NAME/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .claude/
│   └── settings.json
├── app/
│   ├── layout.tsx                  # Root layout — Inter font + globals.css
│   ├── page.tsx                    # Main dashboard page
│   ├── globals.css                 # @import "tailwindcss" + @import ui-kit theme
│   ├── providers.tsx               # React Query provider (client component)
│   └── icon.svg                    # PE logo favicon (basePath-safe via App Router)
├── components/
│   └── (from plan.yaml components — only custom ones not in ui-kit)
├── lib/
│   ├── api/
│   │   ├── client.ts              # API v2 alpha stub client
│   │   ├── types.ts               # Request/response types from plan
│   │   └── fixtures.ts            # Mock data for stubs
│   ├── embedding.ts
│   └── hooks/
│       └── useCalculation.ts
├── __tests__/
│   └── page.test.tsx
├── next.config.ts
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── plan.yaml                       # The approved plan
├── CLAUDE.md
├── README.md
├── Makefile
├── vercel.json
└── .gitignore
```

#### For Custom Backend pattern (adds):

```
DASHBOARD_NAME/
├── ... (same structure as above, including Makefile and app/icon.svg)
├── backend/
│   ├── _image_setup.py         # Standalone snapshot function (no package imports)
│   ├── app.py                  # Modal worker app + function decorators (only `modal` at module level)
│   ├── modal_app.py            # Lightweight gateway (FastAPI, no PE deps)
│   ├── simulation.py           # Pure business logic (policyengine imports at module level, snapshotted)
│   └── tests/
│       └── test_simulation.py
└── ...
```

### Step 3: Generate Core Files

#### CLAUDE.md

Generate a CLAUDE.md following the pattern from existing applets (givecalc, ctc-calculator):

```markdown
# DASHBOARD_NAME

[Description from plan]

## Architecture

- Next.js App Router with Tailwind CSS v4 and @policyengine/ui-kit theme
- @policyengine/ui-kit for standard UI components
- [Backend description based on data pattern]

## Development

```bash
bun install
make dev            # Full dev stack (Modal + frontend, port 4000-4100)
make dev-frontend   # Frontend only
```

## Testing

```bash
make test
```

## Build

```bash
make build
```

## Design standards
- Uses Tailwind CSS v4 with @policyengine/ui-kit/theme.css (single import for all tokens)
- @policyengine/ui-kit for all standard UI components
- Primary teal: `bg-teal-500` / `text-teal-500`
- Semantic colors: `bg-primary`, `text-foreground`, `text-muted-foreground`
- Font: Inter (via next/font/google)
- Sentence case for all headings
- Charts use `fill="var(--chart-1)"` for series colors
```

#### package.json

Generate from the fixed tech stack, including:
- `next`, `react`, `react-dom` (^19)
- `tailwindcss` (^4)
- `@tailwindcss/postcss` (dev)
- `postcss` (dev)
- `@policyengine/ui-kit`
- `recharts` (if custom charts beyond ui-kit)
- `react-plotly.js` (if maps in plan)
- `@tanstack/react-query`
- `axios`
- Dev: `vitest`, `@vitejs/plugin-react`, `@testing-library/react`, `@testing-library/jest-dom`, `typescript`, `@types/react`, `@types/react-dom`, `@types/node`, `jsdom`

#### next.config.mjs (static export with multi-zone)

Dashboards use `output: 'export'` AND mount as multi-zones behind policyengine.org. This requires the three-piece static-export pattern (phase-gated `assetPrefix` + `vercel.json` self-rewrite + host asset rewrite) — see `policyengine-interactive-tools-skill` → "Canonical zone config — static export" for full rationale.

The scaffolded `next.config.mjs` MUST:
1. Export a **function** that takes `phase` (so we can detect `next dev`)
2. Set `basePath` to `dashboard.zone_path` from the plan
3. Set `assetPrefix` conditionally: `undefined` in dev, `/_zones/<dashboard.name>` in builds

Replace `DASHBOARD_NAME` with `dashboard.name` and `ZONE_PATH` with `dashboard.zone_path`:

```js
import { PHASE_DEVELOPMENT_SERVER } from 'next/constants.js';

/** @type {import('next').NextConfig} */
export default function nextConfig(phase) {
  const isDev = phase === PHASE_DEVELOPMENT_SERVER;

  return {
    output: 'export',
    basePath: 'ZONE_PATH',
    // Phase-gated: undefined in `next dev` (local paths work),
    // /_zones/DASHBOARD_NAME in builds (assets don't collide with host).
    assetPrefix: isDev ? undefined : '/_zones/DASHBOARD_NAME',
    trailingSlash: true,
    images: { unoptimized: true },
  };
}
```

Do NOT scaffold a plain object-form `next.config.ts` — the phase gate requires the function form.

#### vercel.json (static deploy + multi-zone self-rewrites)

Static-export dashboards deploy as **plain static sites** (`"framework": null`): Vercel silently IGNORES `vercel.json` rewrites under the Next.js framework preset, and `next.config` rewrites can't be used with `output: 'export'` — with the preset, the deployed zone 404s on every basePath route and asset. The rewrites map the basePath routes and prefixed assets onto the export root (static export writes pages at the `out/` root; internal links carry the basePath). The catch-all must be a regex param `:path(.*)` — `:path*` doesn't match the trailing-slash URLs the app generates.

Replace `DASHBOARD_NAME` with `dashboard.name` and `ZONE_PATH` with `dashboard.zone_path`:

```json
{
  "framework": null,
  "buildCommand": "bun run build",
  "outputDirectory": "out",
  "trailingSlash": true,
  "rewrites": [
    { "source": "/_zones/DASHBOARD_NAME/_next/:path*", "destination": "/_next/:path*" },
    { "source": "ZONE_PATH", "destination": "/" },
    { "source": "ZONE_PATH/:path(.*)", "destination": "/:path" }
  ]
}
```

The host-side asset rewrite (`policyengine-app-v2/website/next.config.ts`) is added separately during deploy — see `/deploy-dashboard`.

#### postcss.config.mjs

**Required for Tailwind v4.** Without this file, `@import "tailwindcss"` in globals.css is never processed and no utility classes are generated.

```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

#### app/globals.css

Generate the Tailwind v4 configuration with the ui-kit theme import:

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";

body {
  font-family: var(--font-sans);
  color: var(--foreground);
  background: var(--background);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

The single `@import "@policyengine/ui-kit/theme.css"` replaces the entire manual `@theme` block. It provides all color, spacing, typography, and chart tokens as CSS variables that Tailwind 4 picks up automatically.

#### app/layout.tsx

The root layout imports globals.css and sets up Inter font:

```tsx
import './globals.css'
import { Inter } from 'next/font/google'
import type { Metadata } from 'next'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TITLE - PolicyEngine',
  description: 'DESCRIPTION from plan',
  // Favicon is picked up automatically from app/icon.svg (basePath-safe).
  // Do NOT set icons: { icon: '/favicon.svg' } — that path is not basePath-prefixed
  // and resolves to the host's favicon when the zone is served behind policyengine.org.
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

#### app/providers.tsx

Client component wrapping React Query:

```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

#### API Client Stubs

Generate `lib/api/types.ts` with TypeScript interfaces matching the plan's endpoint inputs/outputs.

Generate `lib/api/fixtures.ts` with mock data from `plan.yaml`'s `stub_fixtures`.

**For `policyengine-api` or API v2 alpha patterns**, generate `lib/api/client.ts` with synchronous fetch stubs that return fixture data.

**For `custom-modal` pattern**, generate `lib/api/client.ts` with the gateway polling pattern:

```typescript
// client.ts - Gateway + Polling client
const API_URL = process.env.NEXT_PUBLIC_API_URL
  || 'https://policyengine--DASHBOARD_NAME-fastapi-app.modal.run';

interface JobResponse { job_id: string }

export interface StatusResponse {
  status: 'computing' | 'ok' | 'error';
  result?: unknown;
  message?: string;
}

export async function submitJob(endpoint: string, params: unknown): Promise<string> {
  const res = await fetch(`${API_URL}/submit/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Submit failed: ${res.status}`);
  const data: JobResponse = await res.json();
  return data.job_id;
}

export async function pollStatus(jobId: string): Promise<StatusResponse> {
  const res = await fetch(`${API_URL}/status/${jobId}`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}
```

Generate `lib/hooks/useCalculation.ts` with the async polling hook:

```typescript
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { submitJob, pollStatus } from '../api/client';
import type { StatusResponse } from '../api/client';

export function useAsyncCalculation<T>(
  queryKey: unknown[],
  endpoint: string,
  params: unknown,
  options?: { enabled?: boolean },
) {
  const [jobId, setJobId] = useState<string | null>(null);
  useEffect(() => { setJobId(null); }, [JSON.stringify(params)]);

  const submit = useQuery({
    queryKey: [...queryKey, 'submit'],
    queryFn: async () => {
      const id = await submitJob(endpoint, params);
      setJobId(id);
      return id;
    },
    enabled: options?.enabled ?? true,
  });

  const poll = useQuery<StatusResponse>({
    queryKey: [...queryKey, 'poll', jobId],
    queryFn: () => pollStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) =>
      query.state.data?.status === 'computing' ? 2000 : false,
  });

  return {
    isLoading: submit.isLoading || (!!jobId && poll.isLoading),
    isComputing: poll.data?.status === 'computing',
    isError: submit.isError || poll.data?.status === 'error',
    data: poll.data?.status === 'ok' ? (poll.data.result as T) : undefined,
    error: poll.data?.message || submit.error?.message,
  };
}
```

#### .claude/settings.json

**Skip this file if it already exists** — `/init-dashboard` creates it with the correct plugin configuration.

If it does not exist, create it:

```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["dashboard-builder@policyengine-claude"]
  }
}
```

#### CI Workflow

Generate `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: oven-sh/setup-bun@v2
      - run: bun install --frozen-lockfile
      - run: bunx vitest run
      - run: bun run build
```

#### Makefile

Generate a `Makefile` that provides standard development targets. The Makefile content depends on the `data_pattern` from `plan.yaml`.

**IMPORTANT:** Makefile recipes must use literal tab characters for indentation, not spaces.

**For all patterns:** The `dev` and `dev-frontend` targets must try port 4000 first, then increment by 1 up to 4100, erroring out if no port in that range is available. Use this helper script embedded in the Makefile — copy it exactly:

```makefile
# Port selection helper — finds the first available port in 4000-4100
define find_port
$$(python3 -c '\
import socket, sys;\
for p in range(4000, 4101):\
    try:\
        s = socket.socket(); s.bind(("", p)); s.close(); print(p); sys.exit(0)\
    except OSError:\
        continue\
print("ERROR: no free port in 4000-4100", file=sys.stderr); sys.exit(1)\
')
endef
```

**For `precomputed`, `policyengine-api`, or `precomputed-csv` patterns:**

```makefile
.PHONY: dev dev-frontend
.PHONY: build test lint clean

# Port selection helper — finds the first available port in 4000-4100
define find_port
$$(python3 -c '\
import socket, sys;\
for p in range(4000, 4101):\
    try:\
        s = socket.socket(); s.bind(("", p)); s.close(); print(p); sys.exit(0)\
    except OSError:\
        continue\
print("ERROR: no free port in 4000-4100", file=sys.stderr); sys.exit(1)\
')
endef

# Start development server
dev: dev-frontend

# Frontend only (no backend for this data pattern)
dev-frontend:
	@PORT=$(find_port); \
	echo "Frontend: http://localhost:$$PORT"; \
	PORT=$$PORT bun run dev

build:
	bun run build

test:
	bunx vitest run

lint:
	bun run lint

clean:
	rm -rf .next node_modules
```

**For `custom-modal` pattern:**

Replace `DASHBOARD_NAME` below with the actual `dashboard.name` value from `plan.yaml`.

The custom-modal pattern uses a **gateway + worker architecture** with frontend polling. The worker must be deployed first (it contains the heavy policyengine code), then the gateway is started in dev mode.

```makefile
.PHONY: dev dev-frontend dev-backend deploy-worker
.PHONY: build test test-backend lint clean

# Port selection helper — finds the first available port in 4000-4100
define find_port
$$(python3 -c '\
import socket, sys;\
for p in range(4000, 4101):\
    try:\
        s = socket.socket(); s.bind(("", p)); s.close(); print(p); sys.exit(0)\
    except OSError:\
        continue\
print("ERROR: no free port in 4000-4100", file=sys.stderr); sys.exit(1)\
')
endef

# Deploy worker functions, then start gateway + frontend
dev:
	@echo "Deploying worker functions..."
	@unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET && modal deploy backend/app.py
	@echo "Starting gateway (ephemeral)..."
	@modal serve backend/modal_app.py & MODAL_PID=$$!; \
	sleep 5; \
	MODAL_URL="https://policyengine--DASHBOARD_NAME-fastapi-app-dev.modal.run"; \
	PORT=$(find_port); \
	echo "Gateway: $$MODAL_URL"; \
	echo "Frontend: http://localhost:$$PORT"; \
	NEXT_PUBLIC_API_URL=$$MODAL_URL PORT=$$PORT bun run dev; \
	kill $$MODAL_PID 2>/dev/null

# Frontend only (uses production API or NEXT_PUBLIC_API_URL if set)
dev-frontend:
	@PORT=$(find_port); \
	echo "Frontend: http://localhost:$$PORT"; \
	PORT=$$PORT bun run dev

# Backend only (gateway in dev mode — worker must already be deployed)
dev-backend:
	modal serve backend/modal_app.py

# Deploy worker functions to Modal (required before gateway can spawn jobs)
deploy-worker:
	unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET && modal deploy backend/app.py

build:
	bun run build

test:
	bunx vitest run

test-backend:
	cd backend && uv run pytest

lint:
	bun run lint

clean:
	rm -rf .next node_modules
```

#### Favicon

Copy the PolicyEngine logo into `app/icon.svg` — the App Router convention. Next.js emits it at `<basePath>/icon.svg`, so it resolves correctly whether the zone is hit directly or served behind the host.

```bash
cp node_modules/@policyengine/ui-kit/src/assets/logos/policyengine/teal-square.svg app/icon.svg
```

Do NOT use `public/favicon.svg` + `icons: { icon: '/favicon.svg' }` in metadata — that path is written verbatim into the HTML and is not basePath-prefixed. Behind the host, the browser will request it from `policyengine.org/favicon.svg` and get the host's favicon instead of the zone's.

#### Embedding Boilerplate

Generate country detection, hash sync, and share URL helpers in `lib/embedding.ts`:

```typescript
export function getCountryFromHash(): string {
  const params = new URLSearchParams(window.location.hash.slice(1));
  return params.get("country") || "us";
}

export function isEmbedded(): boolean {
  return window.self !== window.top;
}

export function updateHash(params: Record<string, string>, countryId: string) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => p.set(k, v));
  if (countryId !== "us" && !isEmbedded()) p.set("country", countryId);
  const hash = `#${p.toString()}`;
  window.history.replaceState(null, "", hash);
  if (isEmbedded()) {
    window.parent.postMessage({ type: "hashchange", hash }, "*");
  }
}

export function getShareUrl(countryId: string, slug: string): string {
  const hash = window.location.hash;
  if (isEmbedded()) {
    return `https://policyengine.org/${countryId}/${slug}${hash}`;
  }
  return window.location.href;
}
```

#### Initial Test File

Generate `__tests__/page.test.tsx` with a basic render test.

### Step 4: Create Skeleton Components

For each component in `plan.yaml`, first check if `@policyengine/ui-kit` already provides it. Only create skeleton files for components NOT available in ui-kit.

Each custom skeleton should:
- Use Tailwind utility classes with semantic and brand tokens for styling
- Have the correct TypeScript props interface
- Include a `// TODO: Implement` comment where real logic goes
- Export the component

### Step 5: Commit and Create Feature Branch

The repository and remote already exist (created by `/init-dashboard`). Commit the scaffold and create a feature branch:

```bash
git add -A
git commit -m "Initial scaffold from dashboard plan"
git checkout -b feature/initial-implementation
git push -u origin feature/initial-implementation
```

### Step 6: Verify

```bash
bun install
bun run build  # Should succeed with skeleton components
bunx vitest run  # Initial test should pass
```

If either fails, fix before proceeding.

## Quality Checklist

- [ ] `plan.yaml` is included in the repo
- [ ] `dashboard.zone_path` from plan is written as `basePath` in `next.config.mjs`
- [ ] `next.config.mjs` exports a FUNCTION taking `phase` (not a plain object)
- [ ] `assetPrefix` is phase-gated: `undefined` in dev, `/_zones/<dashboard.name>` in builds
- [ ] `vercel.json` has `framework: null`, `outputDirectory: out`, `trailingSlash: true`, the asset self-rewrite (`/_zones/<dashboard.name>/_next/:path*` → `/_next/:path*`), and the basePath route rewrites (`<zone_path>` → `/`, `<zone_path>/:path(.*)` → `/:path`)
- [ ] `CLAUDE.md` follows existing applet patterns
- [ ] `package.json` has all required dependencies (Next.js, Tailwind v4, ui-kit)
- [ ] `globals.css` has `@import "tailwindcss"` + `@import "@policyengine/ui-kit/theme.css"`
- [ ] `postcss.config.mjs` exists with `@tailwindcss/postcss` plugin
- [ ] No `tailwind.config.ts` (Tailwind v4)
- [ ] No CDN `<link>` for design-system tokens (ui-kit theme provides everything)
- [ ] Inter font is loaded via `next/font/google`
- [ ] Embedding boilerplate is in place
- [ ] API client stubs match the plan's endpoint signatures
- [ ] CI workflow is configured
- [ ] `.claude/settings.json` auto-installs the dashboard-builder plugin
- [ ] `vercel.json` is configured for frontend deployment
- [ ] Feature branch is created and pushed
- [ ] `app/icon.svg` exists (PE logo, basePath-safe via App Router)
- [ ] `layout.tsx` metadata does NOT set `icons: { icon: '/favicon.svg' }` (that path isn't basePath-prefixed and would collide with the host behind policyengine.org)
- [ ] Header uses `logos.whiteWordmark` or `logos.tealWordmark` (not text-only)
- [ ] `Makefile` has correct targets for the data pattern
- [ ] `make dev` uses port range 4000-4100 (not random, not hardcoded 3000)
- [ ] If custom-modal: `make dev` deploys worker, then starts gateway + frontend
- [ ] If custom-modal: backend has 3-file structure (`_image_setup.py`, `app.py`, `simulation.py`)
- [ ] If custom-modal: `_image_setup.py` has no package imports at module level
- [ ] If custom-modal: `app.py` only imports `modal` at module level
- [ ] If custom-modal: `simulation.py` has policyengine imports at module level (snapshotted)
- [ ] If custom-modal: image uses `.run_function(snapshot_models)` for fast cold starts
- [ ] If custom-modal: worker image `pip_install` includes `"pydantic"` (simulation.py uses it at module level)
- [ ] If custom-modal: worker image uses `.add_local_file()` for `simulation.py` (not auto-mounted since it's imported inside function bodies)
- [ ] If custom-modal: gateway is lightweight (no policyengine in its Modal image)
- [ ] If custom-modal: gateway image explicitly includes `pydantic`
- [ ] If custom-modal: workers have `cpu=8.0`, `memory=32768`, `timeout >= 3600`
- [ ] If custom-modal: frontend uses polling (`refetchInterval`), not synchronous await
- [ ] If custom-modal: `/status` endpoint returns `{status, result, message}`
- [ ] Build passes on the scaffold
- [ ] Initial test passes

## DO NOT

- Commit to main after the initial scaffold commit
- Deploy to Vercel or Modal (that's `/deploy-dashboard`)
- Implement real logic (that's Phase 3 agents)
- Skip the feature branch
- Create `tailwind.config.ts` (Tailwind v4 uses `@theme` in CSS)
- Omit `postcss.config.mjs` — it IS required for Tailwind v4 (the `@tailwindcss/postcss` plugin processes `@import "tailwindcss"`)
- Rebuild components that exist in `@policyengine/ui-kit`
- Load tokens via CDN `<link>` (use `@import "@policyengine/ui-kit/theme.css"` instead)
- Use `getCssVar()` — it no longer exists. SVG accepts `var()` directly.
