---
name: policyengine-app
description: Developing policyengine-app-v2 — the main React frontend for policyengine.org
---

# PolicyEngine app (v2)

Architecture and patterns for developing the main PolicyEngine web application at `policyengine.org`.

**Repository:** `PolicyEngine/policyengine-app-v2`

## Architecture

### Monorepo

```
policyengine-app-v2/
├── packages/
│   └── design-system/          # @policyengine/design-system (npm)
├── app/                        # Main Vite application
│   ├── src/
│   │   ├── pages/              # Page components (*.page.tsx)
│   │   ├── components/         # Shared UI (charts, layouts, modals)
│   │   ├── routing/            # Guards, router config
│   │   ├── hooks/              # Custom React hooks
│   │   ├── designTokens/       # Re-exports from design-system
│   │   ├── styles/             # Mantine theme, global PostCSS
│   │   ├── data/               # Static data (apps.json, posts/)
│   │   ├── adapters/           # API fetch wrappers
│   │   ├── api/                # React Query hooks
│   │   ├── contexts/           # React Context providers
│   │   ├── types/              # TypeScript interfaces
│   │   └── utils/              # Formatters, helpers
│   ├── public/                 # Static assets (logos, post images)
│   └── vite.config.mjs
├── turbo.json
└── package.json                # Bun workspaces root
```

### Tech stack

| Layer | Technology |
|-------|-----------|
| Package manager | **Bun** (primary), npm fallback |
| Build | Vite + Turbo |
| UI framework | **Mantine v8** |
| Routing | React Router v7 (`createBrowserRouter`) |
| Charts | **Recharts** (standard), Plotly (maps only) |
| Server state | React Query |
| Design tokens | `@policyengine/design-system` |
| Language | TypeScript |
| Formatting | Prettier + ESLint |
| Testing | Vitest |

### Dual SPA mode

`VITE_APP_MODE` controls which entry point builds:
- `website` — Full policyengine.org (pages, blog, research, embedded tools)
- `calculator` — Standalone calculator at app.policyengine.org

## Development

```bash
bun install                          # Install dependencies
bun run dev                          # Dev server (builds design-system first)
cd app && bun run prettier -- --write .  # Format before committing
bun run lint                         # Lint (CI uses --max-warnings 0)
bun run build                        # Production build
bun run test                         # Tests
```

## CRITICAL: Frontend verification and troubleshooting

### How to verify the frontend works

The ONLY reliable way to verify the frontend compiles correctly is `bun run build`. This catches import errors, TypeScript errors, and missing dependencies.

**`curl` is NOT verification.** Vite serves an HTML shell regardless of whether React components actually render. A 200 from curl means nothing for an SPA. Never use curl output as evidence that the frontend works.

**You cannot visually verify a frontend.** After the build passes and dev server starts, tell the user it's ready for them to check in the browser. Do not claim it "looks good."

Before making any claim about dev server status, check with `lsof -i :5173`. Do not assume it is running.

### Correct verification sequence

```bash
bun run build                        # Catches all compile-time errors
# If build passes and dev server needed:
cd app && VITE_APP_MODE=website ./node_modules/.bin/vite --port 5173 &
open http://localhost:5173/us         # User checks visually
```

### Dependency troubleshooting

When `bun install` fails:

1. Read the error. Fix the specific issue.
2. Try at most **2 approaches** before asking the user for help.
3. **Hard stops — never do these:**
   - `rm -rf node_modules` without user approval
   - Manually `npm pack` + `tar -xzf` packages into node_modules
   - Editing lockfile internals
   - Looping through increasingly obscure npm/bun flags

## Design tokens

Import from `@/designTokens` (convenience layer that re-exports from the design-system package):

```tsx
import { colors, spacing, typography } from '@/designTokens';
```

**Never hardcode values:**
```tsx
// Wrong
style={{ color: '#319795', marginBottom: '16px' }}

// Correct
style={{ color: colors.primary[500], marginBottom: spacing.lg }}
```

See `policyengine-design-skill` for the full token reference.

## Mantine components

All UI uses Mantine v8. Key components:

```tsx
import { Stack, Group, Text, Button, Paper } from '@mantine/core';
import { colors, spacing } from '@/designTokens';

function PolicyCard({ title, description, onEdit }) {
  return (
    <Paper p={spacing.lg} withBorder>
      <Stack gap={spacing.sm}>
        <Text fw={600}>{title}</Text>
        <Text c={colors.text.secondary} fz="sm">{description}</Text>
        <Button variant="outline" onClick={onEdit}>Edit</Button>
      </Stack>
    </Paper>
  );
}
```

| Component | Usage |
|-----------|-------|
| `Stack`, `Group`, `Box` | Layout |
| `Text`, `Title` | Typography |
| `Button`, `ActionIcon` | Controls |
| `Paper`, `Card` | Containers |
| `Table`, `Modal`, `Tooltip` | Complex UI |
| `TextInput`, `Select`, `NumberInput` | Forms |

## Charts

### Recharts (standard for all new charts)

```tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartContainer, ChartWatermark, ImpactTooltip } from '@/components/charts';
import { colors } from '@/designTokens';

function RevenueChart({ data }) {
  return (
    <ChartContainer title="Revenue impact" csvData={data}>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <XAxis dataKey="name" />
          <YAxis tickFormatter={(v) => v.toLocaleString('en-US', {
            style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1,
          })} />
          <Tooltip content={<ImpactTooltip />} />
          <Bar dataKey="value" fill={colors.primary[500]} />
        </BarChart>
      </ResponsiveContainer>
      <ChartWatermark />
    </ChartContainer>
  );
}
```

### Semantic chart colors

| Meaning | Token |
|---------|-------|
| Primary data | `colors.primary[500]` |
| Secondary | `colors.gray[400]` |
| Positive/gains | `colors.success` |
| Negative/losses | `colors.gray[600]` |
| Error | `colors.error` |

### Plotly (maps only)

Plotly is only used for geographic visualizations (choropleths, hex maps). All other charts use Recharts.

### Chart components

| Component | Purpose |
|-----------|---------|
| `ChartContainer` | Card wrapper with title, CSV download |
| `ChartWatermark` | PolicyEngine logo below chart |
| `ImpactTooltip` | Formatted hover tooltip |
| `ImpactBarLabel` | Values above/below bars |

## Routing

Routes in `app/src/WebsiteRouter.tsx`:

```
/:countryId/
  ├── (StaticLayout)
  │   ├── home (index)
  │   ├── research/:slug (blog posts)
  │   ├── brand/*, team, donate
  │   └── model
  ├── (AppLayout)
  │   └── :slug → AppPage.tsx (apps.json)
  └── (full-page embeds)
```

### Country guards

- `CountryGuardSimple` — Validates countryId, redirects to default
- `CountryAppGuard` — Validates slug+countryId for apps

### Adding a new page

1. Create `app/src/pages/MyPage.page.tsx`
2. Add route in `WebsiteRouter.tsx` under appropriate layout
3. Use `useParams()` for `countryId`

## Embedded apps (apps.json)

Interactive tools register in `app/src/data/apps/apps.json` and render via `AppPage.tsx`:

```json
{
  "type": "iframe",
  "slug": "marriage",
  "title": "Marriage calculator",
  "source": "https://marriage-zeta-beryl.vercel.app/",
  "countryId": "us",
  "displayWithResearch": true
}
```

See `policyengine-interactive-tools-skill` for the full embedding pattern.

## Ingredient CRUD pages

Policies, Reports, Simulations, and Populations follow a shared pattern using `IngredientReadView` and `RenameIngredientModal`. See `app/.claude/skills/ingredient-patterns.md` for details.

## Blog posts

Markdown files in `app/src/data/posts/articles/`. Metadata in `posts.json`.

## Sentence case

Strictly enforced everywhere:

```tsx
// Correct
<Title order={2}>Your saved policies</Title>

// Wrong
<Title order={2}>Your Saved Policies</Title>
```

Exceptions: proper nouns (PolicyEngine), acronyms (IRS), official names (Child Tax Credit).

## Deployment

- Automatic on push to `main` via Vercel
- Domain: `policyengine.org` (website), `app.policyengine.org` (calculator)
- Team: `policy-engine` scope

## Key files

| File | Purpose |
|------|---------|
| `app/src/WebsiteRouter.tsx` | Main routes |
| `app/src/pages/AppPage.tsx` | Renders embedded apps |
| `app/src/data/apps/apps.json` | Tool registry |
| `app/src/designTokens/` | Token imports |
| `app/src/components/charts/` | Chart components |
| `packages/design-system/` | Token source of truth |
| `app/.claude/skills/` | Local skills (design-tokens, chart-standards, ingredient-patterns) |

## URL patterns

### Production domains

| Domain | Purpose |
|--------|---------|
| `policyengine.org` | Marketing website, research, blog |
| `app.policyengine.org` | Calculator app (policies, households, reports) |

### Calculator URLs (app.policyengine.org)

```
app.policyengine.org/:countryId/                             # Dashboard
app.policyengine.org/:countryId/policies                     # Saved policies
app.policyengine.org/:countryId/policies/create               # Policy builder
app.policyengine.org/:countryId/households                    # Saved households
app.policyengine.org/:countryId/households/create             # Household builder
app.policyengine.org/:countryId/reports                       # Saved reports
app.policyengine.org/:countryId/reports/create                # Report builder
app.policyengine.org/:countryId/simulations                   # Saved simulations
app.policyengine.org/:countryId/simulations/create            # Simulation builder
app.policyengine.org/:countryId/report-output/:reportId       # Report output (overview)
app.policyengine.org/:countryId/report-output/:reportId/:subpage/:view  # Specific chart
```

**Report output subpages and views:**
```
/report-output/:reportId/budget                               # Budget overview
/report-output/:reportId/distributional/incomeDecile          # Distributional by income
/report-output/:reportId/distributional/wealthDecile          # Distributional by wealth
/report-output/:reportId/winners-losers/incomeDecile          # Winners/losers by income
/report-output/:reportId/winners-losers/wealthDecile          # Winners/losers by wealth
/report-output/:reportId/poverty/age                          # Poverty by age
/report-output/:reportId/poverty/gender                       # Poverty by gender
/report-output/:reportId/poverty/race                         # Poverty by race (US only)
/report-output/:reportId/deep-poverty/age                     # Deep poverty by age
/report-output/:reportId/deep-poverty/gender                  # Deep poverty by gender
/report-output/:reportId/inequality                           # Inequality measures
```

**Country IDs:** `us`, `uk`, `ca`, `ng`, `il`

### Website URLs (policyengine.org)

```
policyengine.org/:countryId/                     # Country home
policyengine.org/:countryId/research             # Research index
policyengine.org/:countryId/research/:slug       # Research article
policyengine.org/:countryId/blog                 # Blog index
policyengine.org/:countryId/blog/:postName       # Blog post
policyengine.org/:countryId/model                # Policy model explorer
policyengine.org/:countryId/:slug                # Embedded app (from apps.json)
```

### Legacy v1 URLs (DO NOT USE)

The old `policyengine-app` (v1) used a different URL pattern that no longer works:
```
# WRONG — v1 format, returns "App not found"
policyengine.org/us/policy?reform=73278&baseline=2&region=enhanced_us&timePeriod=2025
policyengine.org/us/reform/2/280039/over/2/us?focus=policyOutput.winnersAndLosers.incomeDecile
```

Always use `app.policyengine.org` for calculator functionality.

## Related skills

- `policyengine-design-skill` — Full token reference
- `policyengine-interactive-tools-skill` — Building standalone tools
- `policyengine-vercel-deployment-skill` — Deployment patterns
- `policyengine-writing-skill` — Content style
- `policyengine-api-skill` — Backend API
