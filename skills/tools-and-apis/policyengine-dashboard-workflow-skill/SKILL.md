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
| `/create-dashboard` | Full pipeline: plan → scaffold → implement → validate → review |
| `/deploy-dashboard` | Deploy a completed dashboard to Vercel (and optionally Modal) |

### Agents

| Agent | Phase | Role |
|-------|-------|------|
| `dashboard-planner` | 1 | Produces structured plan YAML from description |
| `dashboard-scaffold` | 2 | Creates new repo with project structure |
| `backend-builder` | 3 | Builds API stubs or custom Modal backend |
| `frontend-builder` | 3 | Builds React components with design system |
| `dashboard-integrator` | 4 | Wires frontend to backend, handles data flow |
| `dashboard-validator` | 5 | Validates against plan, runs tests, checks design |

## Workflow Phases

```
Phase 1: Plan ──→ [HUMAN APPROVAL] ──→ Phase 2: Scaffold
  ──→ Phase 3: Implement (backend + frontend)
  ──→ Phase 4: Integrate
  ──→ Phase 5: Validate ──→ [fix loop, max 3 cycles]
  ──→ Phase 6: [HUMAN REVIEW] ──→ DONE

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

**Switching from stubs to real API:** Set `VITE_API_V2_URL` environment variable. The client code checks this and switches from fixture returns to real HTTP calls.

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
| Framework | React 19 + Vite + TypeScript | Fixed |
| UI tokens | `@policyengine/design-system` | From app-v2 |
| Styling | CSS with design token variables | Fixed |
| Font | Inter (via Google Fonts) | Fixed |
| Charts | Recharts | Following app-v2 patterns |
| Maps | react-plotly.js | Following app-v2 patterns |
| Data fetching | TanStack React Query | Fixed |
| Testing | Vitest + React Testing Library | Fixed |
| Deployment | Vercel (frontend) + Modal (backend) | Fixed |

### Design Token Usage

All visual values must come from the `@policyengine/design-system` CSS custom properties:

```css
/* Colors */
var(--pe-color-primary-500)     /* Primary teal */
var(--pe-color-primary-600)     /* Hover state */
var(--pe-color-text-primary)    /* Body text */
var(--pe-color-text-secondary)  /* Muted text */
var(--pe-color-bg-primary)      /* Backgrounds */
var(--pe-color-gray-200)        /* Borders */

/* Spacing */
var(--pe-space-xs)  var(--pe-space-sm)  var(--pe-space-md)
var(--pe-space-lg)  var(--pe-space-xl)  var(--pe-space-2xl)

/* Typography */
var(--pe-font-family-primary)   /* Inter */
var(--pe-font-size-sm)  var(--pe-font-size-md)  var(--pe-font-size-lg)
var(--pe-font-weight-medium)  var(--pe-font-weight-bold)

/* Borders */
var(--pe-radius-sm)  var(--pe-radius-md)  var(--pe-radius-lg)
```

**Never hardcode hex colors, pixel spacing, or font values.** The validator checks for violations.

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
  framework: react-vite
  ui: "@policyengine/design-system"
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

The validator checks 10 categories:

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
