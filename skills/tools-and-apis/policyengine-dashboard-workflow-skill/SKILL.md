---
name: policyengine-dashboard-workflow
description: Reference for the /create-dashboard and /deploy-dashboard orchestrated AI workflow
---

# PolicyEngine Dashboard Workflow

How to use the orchestrated AI workflow for creating PolicyEngine dashboards from natural-language descriptions.

## Overview

The dashboard workflow is a multi-agent pipeline that takes a few paragraphs describing a desired dashboard and produces a working, deployable application in a new GitHub repository.

### Commands

| Command | Purpose |
|---------|---------|
| `/init-dashboard` | Create a new GitHub repo, clone locally, set up dashboard-builder plugin |
| `/create-dashboard` | Full pipeline: plan → scaffold → implement → validate → review |
| `/deploy-dashboard` | Deploy a completed dashboard to Vercel (and optionally Modal) |
| `/dashboard-overview` | List all dashboard builder ecosystem components |

### Agents

| Agent | Phase | Role |
|-------|-------|------|
| `dashboard-planner` | 1 | Produces structured plan YAML from description |
| `dashboard-scaffold` | 2 | Generates Next.js + Tailwind project structure into the current repo |
| `backend-builder` | 3 | Builds API stubs or custom Modal backend |
| `frontend-builder` | 3 | Builds React components with Tailwind + PE design tokens |
| `dashboard-integrator` | 4 | Wires frontend to backend, handles data flow |
| `dashboard-validator` | 5A | Validates against plan, runs tests, checks design |
| `dashboard-design-token-validator` | 5B | Validates frontend spec compliance (Tailwind, Next.js, tokens) |
| `dashboard-overview-updater` | Post | Updates dashboard-overview command if ecosystem changed |

## Workflow Phases

```
Pre-req: /init-dashboard (creates repo + clones locally)
Phase 1: Plan ──→ [HUMAN APPROVAL] ──→ Phase 2: Scaffold
  ──→ Phase 3: Implement (backend + frontend)
  ──→ Phase 4: Integrate
  ──→ Phase 5A: Validate ──→ Phase 5B: Spec validate ──→ [fix loop, max 3 cycles]
  ──→ Phase 6: [HUMAN REVIEW] ──→ DONE
  ──→ Phase 6.5: Update overview (silent)

Separately: /deploy-dashboard (after user merges to main)
```

## Data Patterns

### API v2 Alpha (default)

The dashboard is built against the PolicyEngine API v2 alpha interface. During development, the backend-builder creates **typed stubs** that return fixture data matching the v2 alpha response shapes.

**When v2 alpha alignment agent is built (future):** Stubs will be replaced with real API calls using the async job pattern:
1. `POST /endpoint` → returns `{ job_id, status }`
2. `GET /endpoint/{job_id}` → poll until `status: COMPLETED`
3. Extract `result` from completed response

**Available v2 alpha endpoints (from DESIGN.md):**

| Endpoint | Purpose |
|----------|---------|
| `POST /simulate/household` | Single household calculation |
| `POST /simulate/economy` | Population simulation |
| `POST /analysis/decile-impact/economy` | Income decile breakdown |
| `POST /analysis/budget-impact/economy` | Tax/benefit programme totals |
| `POST /analysis/winners-losers/economy` | Who gains and loses |
| `POST /analysis/compare/economy` | Multi-scenario comparison |
| `POST /analysis/compare/household` | Household scenario comparison |

**Switching from stubs to real API:** Set `NEXT_PUBLIC_API_V2_URL` environment variable. The client code checks this and switches from fixture returns to real HTTP calls.

### Custom Backend (escape hatch)

Use only when the dashboard needs something v2 alpha cannot provide:
- Custom reform parameters not exposed by the API
- Non-standard entity structures
- Combining PolicyEngine with external models
- Microsimulation with custom reform configurations

**Pattern:** FastAPI on Modal with `policyengine-us` or `policyengine-uk` packages.

**The plan MUST document why v2 alpha is insufficient** before selecting this pattern.

## Tech Stack (fixed)

| Layer | Technology | Source |
|-------|-----------|--------|
| Framework | Next.js (App Router) + React 19 + TypeScript | Fixed |
| UI tokens | `@policyengine/design-system` | From app-v2 |
| Styling | Tailwind CSS with design token integration | Fixed |
| Font | Inter (via `next/font/google`) | Fixed |
| Charts | Recharts | Following app-v2 patterns |
| Maps | react-plotly.js | Following app-v2 patterns |
| Data fetching | TanStack React Query | Fixed |
| Testing | Vitest + React Testing Library | Fixed |
| Deployment | Vercel (frontend) + Modal (backend) | Fixed |

See `policyengine-frontend-builder-spec-skill` for the full mandatory technology specification.

### Design Token Usage

All visual values must come from `@policyengine/design-system` tokens, accessed via Tailwind utility classes mapped in `tailwind.config.ts`:

```tsx
// Colors — use Tailwind classes mapped to PE tokens
<div className="bg-pe-primary-500 text-white">        {/* Primary teal */}
<div className="hover:bg-pe-primary-600">              {/* Hover state */}
<span className="text-pe-text-primary">               {/* Body text */}
<span className="text-pe-text-secondary">             {/* Muted text */}
<div className="bg-pe-bg-primary">                    {/* Backgrounds */}
<div className="border border-pe-gray-200">           {/* Borders */}

// Spacing
<div className="p-pe-lg gap-pe-md m-pe-xl">

// Typography
<span className="font-pe text-pe-sm font-medium">

// Border radius
<div className="rounded-pe-md">
```

**Never hardcode hex colors, pixel spacing, or font values.** Both the dashboard-validator and dashboard-design-token-validator check for violations.

### Chart Patterns

Charts must follow the patterns from `policyengine-app-v2`:

```tsx
// Standard Recharts pattern
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

<ResponsiveContainer width="100%" height={400}>
  <LineChart data={data}>
    <CartesianGrid strokeDasharray="3 3" stroke="var(--pe-color-gray-100)" />
    <XAxis dataKey="x" tickFormatter={formatCurrency} />
    <YAxis tickFormatter={formatCurrency} />
    <Tooltip contentStyle={{ background: 'white', border: '1px solid var(--pe-color-gray-200)' }} />
    <Line type="monotone" dataKey="income_tax" stroke="var(--pe-color-primary-500)" />
  </LineChart>
</ResponsiveContainer>
```

**Future:** When `@policyengine/chart-library` is built, charts will import from that package instead of directly using Recharts.

## Plan YAML Schema

The plan is the contract between the planner and all other agents:

```yaml
dashboard:
  name: string        # kebab-case, becomes repo name
  title: string       # Human-readable title
  description: string # One paragraph
  country: string     # us, uk, or both
  audience: string    # public, researchers, legislators, internal

data_pattern: string  # api-v2-alpha or custom-backend

api_v2_integration:   # Only if api-v2-alpha
  endpoints_needed: [{ endpoint, purpose, variables_requested }]
  stub_fixtures: [{ name, description, expected_outputs }]

custom_backend:       # Only if custom-backend
  reason: string      # WHY v2 alpha is insufficient
  framework: string
  policyengine_package: string
  endpoints: [{ name, method, inputs, outputs, policyengine_variables }]

tech_stack:           # Fixed values, included for documentation
  framework: react-nextjs
  ui: "@policyengine/design-system"
  styling: tailwind-with-design-tokens
  charts: recharts
  testing: vitest

components:           # What to build
  - type: input_form | chart | metric_card | data_table
    id: string
    # Type-specific fields...

embedding:
  register_in_apps_json: boolean
  display_with_research: boolean
  slug: string
  tags: string[]

tests:
  api_tests: [{ name, description, input, expected }]
  frontend_tests: [{ name, description }]
  design_compliance: [{ name, description }]
  embedding_tests: [{ name, description }]
```

## Embedding

All dashboards are built to embed in policyengine.org via iframe:

1. **Country detection:** Read `#country=` from URL hash
2. **Hash sync:** Update hash on input change, `postMessage` to parent
3. **Share URLs:** Point to `policyengine.org/{country}/{slug}`, not Vercel URL
4. **Country toggle:** Hidden when embedded (country comes from route)

See `policyengine-interactive-tools-skill` for full embedding documentation.

## Validation Checklist

The dashboard-validator checks 10 categories:

1. Build compiles without errors
2. All tests pass
3. No hardcoded colors or spacing (design tokens only)
4. Inter font loaded, sentence case headings
5. Responsive at 768px and 480px
6. Embedding features (country detection, hash sync, share URLs)
7. API contract matches plan
8. All plan components implemented
9. Loading and error states handled
10. Chart ResponsiveContainer wrappers

The dashboard-design-token-validator additionally validates:
- Tailwind CSS is used (no plain CSS modules)
- Next.js App Router is the framework (no Vite)
- `@policyengine/design-system` tokens are integrated via Tailwind config
- No hardcoded values where tokens exist

## Deployment

After the user merges the feature branch to `main`:

```bash
/deploy-dashboard
```

This handles:
- Vercel frontend deployment
- Modal backend deployment (if custom-backend)
- Registration in policyengine-app-v2's apps.json (via PR)
- Smoke testing

## Future: API v2 Alpha Alignment

When the API v2 alpha is production-ready, an alignment agent will:
1. Read the plan's `api_v2_integration` section
2. Replace stub functions in `client.ts` with real v2 alpha HTTP calls
3. Implement the async job polling pattern
4. Run the full validation suite against live API responses
5. Update fixture data with real response shapes

This is a planned future addition, not yet implemented.
