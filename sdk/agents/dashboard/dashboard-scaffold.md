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
- `data_pattern` - determines backend structure
- `tech_stack` - confirms fixed stack choices
- `components` - informs which dependencies to install

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
│   ├── layout.tsx                  # Root layout — CDN tokens + ui-kit styles + globals.css
│   ├── page.tsx                    # Main dashboard page
│   ├── globals.css                 # @import "tailwindcss" + @theme block
│   └── providers.tsx               # React Query provider (client component)
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
├── public/
├── __tests__/
│   └── page.test.tsx
├── next.config.ts
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── plan.yaml                       # The approved plan
├── CLAUDE.md
├── README.md
├── vercel.json
└── .gitignore
```

#### For Custom Backend pattern (adds):

```
DASHBOARD_NAME/
├── ... (same structure as above)
├── backend/
│   ├── modal_app.py
│   ├── requirements.txt
│   └── tests/
│       └── test_calculate.py
└── ...
```

### Step 3: Generate Core Files

#### CLAUDE.md

Generate a CLAUDE.md following the pattern from existing applets (givecalc, ctc-calculator):

```markdown
# DASHBOARD_NAME

[Description from plan]

## Architecture

- Next.js App Router with Tailwind CSS v4 and @policyengine/design-system tokens
- @policyengine/ui-kit for standard UI components
- [Backend description based on data pattern]

## Development

```bash
bun install
bun run dev
```

## Testing

```bash
bunx vitest run
```

## Build

```bash
bun run build
```

## Design standards
- Uses Tailwind CSS v4 with @policyengine/design-system tokens bridged via @theme block
- @policyengine/ui-kit for all standard UI components
- Primary teal: `bg-pe-primary-500` / `text-pe-primary-500`
- Font: Inter (via next/font/google)
- Sentence case for all headings
- Charts follow policyengine-app-v2 patterns
```

#### package.json

Generate from the fixed tech stack, including:
- `next`, `react`, `react-dom` (^19)
- `tailwindcss` (^4)
- `@policyengine/ui-kit`
- `recharts` (if custom charts beyond ui-kit)
- `react-plotly.js` (if maps in plan)
- `@tanstack/react-query`
- `axios`
- Dev: `vitest`, `@vitejs/plugin-react`, `@testing-library/react`, `@testing-library/jest-dom`, `typescript`, `@types/react`, `@types/react-dom`, `@types/node`, `jsdom`

#### next.config.ts

```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',  // Static export for Vercel
}

export default nextConfig
```

#### app/globals.css

Generate the Tailwind v4 configuration with `@theme` block bridging PE tokens:

```css
@import "tailwindcss";

@theme {
  /* Primary brand colors — teal */
  --color-pe-primary-50: var(--pe-color-primary-50);
  --color-pe-primary-500: var(--pe-color-primary-500);
  --color-pe-primary-600: var(--pe-color-primary-600);
  --color-pe-primary-700: var(--pe-color-primary-700);
  /* ... complete color bridges */

  /* Gray scale */
  --color-pe-gray-50: var(--pe-color-gray-50);
  --color-pe-gray-100: var(--pe-color-gray-100);
  --color-pe-gray-200: var(--pe-color-gray-200);
  --color-pe-gray-500: var(--pe-color-gray-500);
  --color-pe-gray-600: var(--pe-color-gray-600);
  --color-pe-gray-700: var(--pe-color-gray-700);
  /* ... */

  /* Semantic colors */
  --color-pe-text-primary: var(--pe-color-text-primary);
  --color-pe-text-secondary: var(--pe-color-text-secondary);
  --color-pe-bg-primary: var(--pe-color-bg-primary);
  --color-pe-bg-secondary: var(--pe-color-bg-secondary);
  --color-pe-border-light: var(--pe-color-border-light);
  --color-pe-success: var(--pe-color-success);
  --color-pe-error: var(--pe-color-error);
  --color-pe-warning: var(--pe-color-warning);
  --color-pe-info: var(--pe-color-info);

  /* Spacing */
  --spacing-pe-xs: var(--pe-space-xs);
  --spacing-pe-sm: var(--pe-space-sm);
  --spacing-pe-md: var(--pe-space-md);
  --spacing-pe-lg: var(--pe-space-lg);
  --spacing-pe-xl: var(--pe-space-xl);
  --spacing-pe-2xl: var(--pe-space-2xl);
  --spacing-pe-3xl: var(--pe-space-3xl);
  --spacing-pe-4xl: var(--pe-space-4xl);

  /* Typography — font families */
  --font-pe: var(--pe-font-family-primary), 'Inter', sans-serif;
  --font-pe-mono: var(--pe-font-family-mono), 'JetBrains Mono', monospace;

  /* Typography — font sizes: override Tailwind defaults with PE values.
   * Tailwind v4 uses --text-* namespace to generate text-* utilities.
   * Use standard classes (text-xs, text-sm, text-base, etc.) in components. */
  --text-*: initial;
  --text-xs: var(--pe-font-size-xs);
  --text-sm: var(--pe-font-size-sm);
  --text-base: var(--pe-font-size-base);
  --text-lg: var(--pe-font-size-lg);
  --text-xl: var(--pe-font-size-xl);
  --text-2xl: var(--pe-font-size-2xl);
  --text-3xl: var(--pe-font-size-3xl);
  --text-4xl: var(--pe-font-size-4xl);

  /* Border radius */
  --radius-pe-sm: var(--pe-radius-element);
  --radius-pe-md: 6px;
  --radius-pe-lg: var(--pe-radius-container);

  /* shadcn/ui semantic tokens — bridge to PE equivalents */
  --color-background: var(--pe-color-bg-primary);
  --color-foreground: var(--pe-color-gray-900);
  --color-primary: var(--pe-color-primary-600);
  --color-primary-foreground: var(--pe-color-text-inverse);
  --color-muted: var(--pe-color-gray-100);
  --color-muted-foreground: var(--pe-color-text-secondary);
  --color-border: var(--pe-color-border-light);
  --color-ring: var(--pe-color-primary-500);
}
```

Follow the complete `@theme` block from the `policyengine-frontend-builder-spec-skill` for the full set of bridges.

#### app/layout.tsx

The root layout loads design tokens via CDN, imports ui-kit styles, and sets up Inter font:

```tsx
import '@policyengine/ui-kit/styles.css'
import './globals.css'
import { Inter } from 'next/font/google'
import type { Metadata } from 'next'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TITLE - PolicyEngine',
  description: 'DESCRIPTION from plan',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/@policyengine/design-system/dist/tokens.css"
        />
      </head>
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

#### API Client Stubs (for api-v2-alpha pattern)

Generate `lib/api/types.ts` with TypeScript interfaces matching the plan's endpoint inputs/outputs.

Generate `lib/api/fixtures.ts` with mock data from `plan.yaml`'s `stub_fixtures`.

Generate `lib/api/client.ts` with:
- Functions matching each endpoint in the plan
- Currently returns fixture data
- Clearly marked with `// TODO: Replace with real API v2 alpha calls` comments
- Types that match the v2 alpha async pattern (job creation → polling → result)

```typescript
// client.ts - API v2 Alpha stub
// TODO: Replace stubs with real API v2 alpha calls when available

import { fixtures } from './fixtures';
import type { HouseholdRequest, HouseholdResponse } from './types';

const API_V2_BASE_URL = process.env.NEXT_PUBLIC_API_V2_URL || '';

/**
 * Stub: Calculate household impacts
 * Will call POST /simulate/household when v2 alpha is integrated
 */
export async function calculateHousehold(
  request: HouseholdRequest
): Promise<HouseholdResponse> {
  // TODO: Replace with real v2 alpha call:
  // const job = await fetch(`${API_V2_BASE_URL}/simulate/household`, { ... });
  // return pollForResult(job.job_id);
  return fixtures.defaultHouseholdResponse;
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
- Use `pe-*` Tailwind token classes for styling
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
- [ ] `CLAUDE.md` follows existing applet patterns
- [ ] `package.json` has all required dependencies (Next.js, Tailwind v4, ui-kit)
- [ ] `globals.css` has `@import "tailwindcss"` + `@theme` block bridging PE tokens
- [ ] No `tailwind.config.ts` or `postcss.config.js` (Tailwind v4)
- [ ] `@policyengine/ui-kit/styles.css` imported in layout.tsx
- [ ] Design-system tokens loaded via CDN `<link>` in layout.tsx
- [ ] Inter font is loaded
- [ ] Embedding boilerplate is in place
- [ ] API client stubs match the plan's endpoint signatures
- [ ] CI workflow is configured
- [ ] `.claude/settings.json` auto-installs the dashboard-builder plugin
- [ ] `vercel.json` is configured for frontend deployment
- [ ] Feature branch is created and pushed
- [ ] Build passes on the scaffold
- [ ] Initial test passes

## DO NOT

- Commit to main after the initial scaffold commit
- Deploy to Vercel or Modal (that's `/deploy-dashboard`)
- Implement real logic (that's Phase 3 agents)
- Skip the feature branch
- Create `tailwind.config.ts` or `postcss.config.js` (Tailwind v4 uses `@theme` in CSS)
- Rebuild components that exist in `@policyengine/ui-kit`
