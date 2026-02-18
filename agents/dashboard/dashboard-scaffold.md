---
name: dashboard-scaffold
description: Creates a new GitHub repository and project structure from an approved dashboard plan
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

Creates a new GitHub repository with complete project structure from an approved `plan.yaml`.

## Skills Used

- **policyengine-interactive-tools-skill** - Project scaffolding patterns, embedding boilerplate
- **policyengine-design-skill** - Design tokens, CSS setup
- **policyengine-vercel-deployment-skill** - Vercel configuration
- **policyengine-standards-skill** - CI/CD, Git workflow

## First: Load Required Skills

**Before starting ANY work, use the Skill tool to load each required skill:**

1. `Skill: policyengine-interactive-tools-skill`
2. `Skill: policyengine-design-skill`
3. `Skill: policyengine-vercel-deployment-skill`
4. `Skill: policyengine-standards-skill`

## Input

- An approved `plan.yaml` file in the working directory
- The plan has been reviewed and approved by the user

## Output

- A new GitHub repository under `PolicyEngine/` with the project scaffold
- All code on a feature branch (not main)
- Initial commit with scaffold, CI, and README

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

### Step 2: Create the Repository

```bash
# Create the project directory
mkdir -p /tmp/DASHBOARD_NAME
cd /tmp/DASHBOARD_NAME

# Initialize git
git init
git checkout -b main
```

### Step 3: Create Project Structure

#### For API v2 Alpha pattern:

```
DASHBOARD_NAME/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .claude/
│   └── settings.json
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── api/
│   │   │   ├── client.ts          # API v2 alpha stub client
│   │   │   ├── types.ts           # Request/response types from plan
│   │   │   └── fixtures.ts        # Mock data for stubs
│   │   ├── components/
│   │   │   └── (from plan.yaml components)
│   │   ├── hooks/
│   │   │   └── useCalculation.ts
│   │   └── __tests__/
│   │       └── App.test.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   ├── eslint.config.js
│   └── index.html
├── plan.yaml                       # The approved plan
├── CLAUDE.md
├── README.md
├── vercel.json
└── .gitignore
```

#### For Custom Backend pattern (adds):

```
DASHBOARD_NAME/
├── ... (same frontend as above)
├── api/
│   ├── modal_app.py
│   ├── requirements.txt
│   └── tests/
│       └── test_calculate.py
└── ...
```

### Step 4: Generate Core Files

#### CLAUDE.md

Generate a CLAUDE.md following the pattern from existing applets (givecalc, ctc-calculator):

```markdown
# DASHBOARD_NAME

[Description from plan]

## Architecture

- `frontend/` - Vite React-TS app with @policyengine/design-system
- [Backend description based on data pattern]

## Development

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd frontend
npx vitest run
```

## Build

```bash
cd frontend
npm run build
```

## Design standards
- Uses @policyengine/design-system tokens
- Primary teal: var(--pe-color-primary-500)
- Font: Inter (via design system)
- Sentence case for all headings
- Charts follow policyengine-app-v2 patterns
```

#### package.json

Generate from the fixed tech stack, including:
- `react`, `react-dom` (^19)
- `@policyengine/design-system`
- `recharts` (if charts in plan)
- `react-plotly.js` (if maps in plan)
- `@tanstack/react-query`
- `axios`
- Dev: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `typescript`, `vite`, `@vitejs/plugin-react`, `jsdom`

#### vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/",
});
```

#### index.html

Include Inter font and design system tokens:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>TITLE - PolicyEngine</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

#### API Client Stubs (for api-v2-alpha pattern)

Generate `frontend/src/api/types.ts` with TypeScript interfaces matching the plan's endpoint inputs/outputs.

Generate `frontend/src/api/fixtures.ts` with mock data from `plan.yaml`'s `stub_fixtures`.

Generate `frontend/src/api/client.ts` with:
- Functions matching each endpoint in the plan
- Currently returns fixture data
- Clearly marked with `// TODO: Replace with real API v2 alpha calls` comments
- Types that match the v2 alpha async pattern (job creation → polling → result)

```typescript
// client.ts - API v2 Alpha stub
// TODO: Replace stubs with real API v2 alpha calls when available

import { fixtures } from './fixtures';
import type { HouseholdRequest, HouseholdResponse } from './types';

const API_V2_BASE_URL = import.meta.env.VITE_API_V2_URL || '';

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

```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["app-development@policyengine-claude"]
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
      - run: cd frontend && npm ci
      - run: cd frontend && npx vitest run
      - run: cd frontend && npm run build
```

#### Embedding Boilerplate

Generate country detection, hash sync, and share URL helpers in `frontend/src/lib/embedding.ts`:

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

Generate `frontend/src/__tests__/App.test.tsx` with a basic render test.

### Step 5: Create Skeleton Components

For each component in `plan.yaml`, create a skeleton file:
- Input forms: Basic form with fields from plan, wired to state
- Charts: Component shell with correct Recharts imports and data shape
- Metric cards: Component shell with formatting

Each skeleton should:
- Import design system tokens
- Have the correct TypeScript props interface
- Include a `// TODO: Implement` comment where real logic goes
- Export the component

### Step 6: Initialize Git and Push

```bash
cd /tmp/DASHBOARD_NAME

# Initial commit on main
git add -A
git commit -m "Initial scaffold from dashboard plan"

# Create GitHub repo
gh repo create PolicyEngine/DASHBOARD_NAME --public --source=. --push

# Create feature branch for development
git checkout -b feature/initial-implementation
git push -u origin feature/initial-implementation
```

### Step 7: Verify

```bash
cd /tmp/DASHBOARD_NAME/frontend
npm install
npm run build  # Should succeed with skeleton components
npx vitest run  # Initial test should pass
```

If either fails, fix before proceeding.

## Quality Checklist

- [ ] `plan.yaml` is included in the repo
- [ ] `CLAUDE.md` follows existing applet patterns
- [ ] `package.json` has all required dependencies
- [ ] Design system tokens are imported (not hardcoded colors)
- [ ] Inter font is loaded
- [ ] Embedding boilerplate is in place
- [ ] API client stubs match the plan's endpoint signatures
- [ ] CI workflow is configured
- [ ] `.claude/settings.json` auto-installs the app-development plugin
- [ ] `vercel.json` is configured for frontend deployment
- [ ] Feature branch is created and pushed
- [ ] Build passes on the scaffold
- [ ] Initial test passes

## DO NOT

- Commit to main after the initial scaffold commit
- Deploy to Vercel or Modal (that's `/deploy-dashboard`)
- Implement real logic (that's Phase 3 agents)
- Skip the feature branch
