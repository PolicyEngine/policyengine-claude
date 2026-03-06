---
name: policyengine-frontend-builder-spec
description: Mandatory frontend technology requirements for PolicyEngine dashboards and interactive tools — Tailwind CSS v4, Next.js (App Router), @policyengine/ui-kit theme, Vercel deployment
---

# Frontend builder spec

Authoritative specification for all PolicyEngine frontend projects (dashboards and interactive tools). Any agent building or validating a frontend MUST load this skill and follow every requirement below. Where another agent's instructions conflict with this spec, **this spec wins**.

## Mandatory requirements

### 1. Tailwind CSS (v4+)

The application MUST use **Tailwind CSS v4** for all styling. Tailwind utility classes are the primary styling mechanism.

- MUST install `tailwindcss` (v4+)
- MUST have a `globals.css` containing:
  ```css
  @import "tailwindcss";
  @import "@policyengine/ui-kit/theme.css";
  ```
- MUST NOT have a `tailwind.config.ts` or `tailwind.config.js` — Tailwind v4 uses `@theme` in CSS instead
- MUST NOT have a `postcss.config.js` or `postcss.config.mjs` — Tailwind v4 does not require PostCSS
- MUST NOT use `@tailwind base; @tailwind components; @tailwind utilities;` — use `@import "tailwindcss"` instead
- MUST NOT use plain CSS files or CSS modules (`*.module.css`) for layout or styling
- MUST NOT use other CSS-in-JS libraries (styled-components, emotion, vanilla-extract)
- MUST NOT use other component frameworks for styling (Mantine, Chakra UI, Material UI)
- The only CSS files allowed are `globals.css` (which imports ui-kit theme)

### 2. @policyengine/ui-kit (component library + theme)

The application MUST install `@policyengine/ui-kit` and use it as the primary component library and design token source. **MUST use ui-kit components when an equivalent exists** — do NOT rebuild components that ui-kit already provides.

- MUST install: `bun add @policyengine/ui-kit`
- MUST import theme in `globals.css`: `@import "@policyengine/ui-kit/theme.css";`
- MUST use ui-kit components for all standard UI patterns (see availability table below)
- MAY build custom components only when no ui-kit equivalent exists

**Component availability table:**

| Dashboard need | ui-kit component |
|---|---|
| Page shell | `DashboardShell` |
| Header with logo | `Header` (light/dark variants) |
| Two-column layout | `SidebarLayout` + `InputPanel` + `ResultsPanel` |
| Single-column narrative | `SingleColumnLayout` |
| Buttons | `Button` (4 variants, 3 sizes) |
| Cards | `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardFooter` |
| Badges | `Badge` (6 variants) |
| Tab navigation | `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` |
| Currency input | `CurrencyInput` |
| Number input | `NumberInput` |
| Select dropdown | `SelectInput` |
| Checkbox | `CheckboxInput` |
| Slider | `SliderInput` |
| Input grouping | `InputGroup` |
| KPI display | `MetricCard` (currency/percent, trends) |
| Summary text | `SummaryText` |
| Data tables | `DataTable` |
| Charts | `ChartContainer`, `PEBarChart`, `PELineChart`, `PEAreaChart`, `PEWaterfallChart` |
| Branding | `PolicyEngineWatermark`, `logos.*` |
| Utilities | `formatCurrency`, `formatPercent`, `formatNumber` |

**Component precedence rule:** When building UI:
1. **First**: Use `@policyengine/ui-kit` if it has the component
2. **Second**: Use [shadcn/ui](https://ui.shadcn.com) primitives (Dialog, Popover, Tooltip, Select, DropdownMenu, etc.) styled with Tailwind semantic classes
3. **Third**: Build custom from scratch with Tailwind utility classes

### 3. Design tokens via ui-kit theme

The application MUST load design tokens from `@policyengine/ui-kit/theme.css`. This single CSS import provides all colors, spacing, typography, and chart tokens.

- MUST import theme in `globals.css`: `@import "@policyengine/ui-kit/theme.css";`
- MUST NOT load tokens via CDN `<link>` — the theme is bundled with ui-kit
- MUST NOT hardcode hex color values when a design token exists
- MUST NOT hardcode pixel spacing values when a Tailwind spacing class exists
- MUST NOT hardcode font-family values — use `var(--font-sans)`
- MAY use custom values when no token covers the need (e.g., chart-specific dimensions, animation durations)

**Token usage patterns:**

| Context | Approach | Example |
|---------|----------|---------|
| React components | Tailwind semantic classes | `className="bg-primary text-foreground"` |
| Brand palette | Tailwind direct classes | `className="bg-teal-500 text-gray-600"` |
| Recharts (SVG) | CSS vars directly in fill/stroke | `fill="var(--chart-1)"` |
| Inline styles | CSS vars | `style={{ color: "var(--primary)" }}` |

### 4. Framework: Next.js (App Router)

The application MUST use **Next.js with the App Router**.

- MUST use `create-next-app` or equivalent to scaffold with App Router
- MUST have `next.config.ts` at the project root
- MUST have an `app/` directory with `layout.tsx` and `page.tsx`
- MUST use TypeScript (`.ts`/`.tsx` files, `tsconfig.json`)
- MUST NOT use the Pages Router (`pages/` directory)
- MUST NOT use Vite as the application bundler (Vite is only used by Vitest for testing)
- MUST NOT use other bundlers (Webpack, Parcel, esbuild, etc.)
- MUST NOT use other meta-frameworks (Remix, Gatsby, Astro, etc.)

### 5. Package manager: bun

The application MUST use **bun** as the package manager.

- MUST use `bun install` instead of `npm install`
- MUST use `bun run dev`, `bun run build` instead of `npm run dev`, `npm run build`
- MUST use `bunx vitest run` instead of `npx vitest run`
- MUST have a `bun.lock` lockfile (not `package-lock.json`)
- MUST NOT use npm, yarn, or pnpm

### 6. Vercel deployment

The application MUST be deployed using **Vercel**.

- MUST have a `vercel.json` at the project root with appropriate configuration
- MUST use `output: 'export'` in `next.config.ts` for static export, unless the dashboard requires server-side rendering
- MUST configure the Vercel project to build from the repository root (not a subdirectory)
- MUST set any required environment variables in the Vercel project settings using the `NEXT_PUBLIC_*` prefix
- MUST deploy under the `policy-engine` Vercel scope
- MUST NOT deploy using other hosting platforms (Netlify, AWS Amplify, GitHub Pages, etc.) for the frontend

### 7. shadcn/ui for custom components

When building custom components not available in `@policyengine/ui-kit`, the application SHOULD use [shadcn/ui](https://ui.shadcn.com) primitives as the base layer.

- SHOULD initialize shadcn/ui: `bunx shadcn@latest init`
- SHOULD use shadcn/ui for: Dialog, Popover, Tooltip, Select, DropdownMenu, Accordion, Sheet, and other interaction primitives
- MUST style shadcn/ui components with Tailwind semantic classes (the ui-kit theme already defines shadcn/ui semantic tokens like `background`, `foreground`, `primary`, `muted`)
- MUST NOT use shadcn/ui when an equivalent `@policyengine/ui-kit` component exists

## Tailwind v4 + ui-kit theme integration pattern

### globals.css

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

The single `@import "@policyengine/ui-kit/theme.css"` provides:
1. **`:root` variables** — shadcn/ui semantic tokens (`--primary`, `--background`, `--chart-1`, etc.)
2. **`@theme inline`** — Bridges `:root` vars to Tailwind utilities (`bg-primary`, `text-foreground`)
3. **`@theme`** — Brand palette (`bg-teal-500`, `text-gray-600`), font sizes, spacing, breakpoints

### Next.js: app/layout.tsx

```tsx
import './globals.css'
import { Inter } from 'next/font/google'
import type { Metadata } from 'next'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DASHBOARD_TITLE - PolicyEngine',
  description: 'DASHBOARD_DESCRIPTION',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

### Usage in components

```tsx
// Prefer ui-kit components:
import { MetricCard, Button, Card, CardContent } from '@policyengine/ui-kit';
import { formatCurrency } from '@policyengine/ui-kit';

// Use Tailwind classes with semantic and brand tokens for custom layouts:
<div className="bg-background border border-border rounded-lg p-4 flex flex-col gap-1">
  <span className="text-sm text-muted-foreground font-medium">Metric title</span>
  <span className="text-2xl font-bold text-foreground">{formatCurrency(1234)}</span>
</div>

// Brand colors when needed:
<div className="bg-teal-500 text-white hover:bg-teal-600">Primary teal</div>

// Responsive design uses Tailwind breakpoint prefixes:
<main className="max-w-content mx-auto px-6 py-4 font-sans text-foreground">
  <div className="flex gap-6 md:flex-col">
    {/* sidebar collapses at md breakpoint */}
  </div>
</main>

// Recharts uses CSS vars directly:
<Line stroke="var(--chart-1)" />
<Bar fill="var(--chart-2)" />
<CartesianGrid stroke="var(--border)" />
```

## Project structure

```
DASHBOARD_NAME/
├── app/
│   ├── layout.tsx              # Root layout — Inter font + globals.css
│   ├── page.tsx                # Main dashboard page
│   ├── globals.css             # @import "tailwindcss" + @import ui-kit theme
│   └── providers.tsx           # React Query provider (client component)
├── components/
│   └── (from plan.yaml)        # Custom dashboard components (only if not in ui-kit)
├── lib/
│   ├── api/
│   │   ├── client.ts           # API client (stubs or real)
│   │   ├── types.ts            # Request/response TypeScript types
│   │   └── fixtures.ts         # Mock data for stubs
│   ├── embedding.ts            # Country detection, hash sync, share URLs
│   └── hooks/
│       └── useCalculation.ts   # React Query hooks
├── public/
├── next.config.ts
├── tsconfig.json
├── package.json
├── vitest.config.ts
├── plan.yaml
├── CLAUDE.md
├── README.md
├── vercel.json
└── .gitignore
```

## Package dependencies

**Production:**
- `next`
- `react`, `react-dom`
- `tailwindcss` (v4+)
- `@policyengine/ui-kit`
- `@tanstack/react-query`
- `recharts` (if custom charts beyond ui-kit)
- `react-plotly.js`, `plotly.js-dist-min` (if maps)
- `axios`

**Development:**
- `typescript`, `@types/react`, `@types/react-dom`, `@types/node`
- `vitest`, `@vitejs/plugin-react`, `jsdom`
- `@testing-library/react`, `@testing-library/jest-dom`

## Testing

Vitest is the test runner. Configure `vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
  },
})
```

Note: `@vitejs/plugin-react` is only used by Vitest for JSX transform during testing — Vite is NOT used as the application bundler.

## What NOT to do

- MUST NOT use Vite as the application bundler — only Next.js is allowed (Vite is used only by Vitest for testing)
- MUST NOT use other bundlers (Webpack, Parcel, esbuild)
- MUST NOT use other meta-frameworks (Remix, Gatsby, Astro)
- MUST NOT use the Next.js Pages Router — use App Router only
- MUST NOT have `tailwind.config.ts` or `postcss.config.js` — Tailwind v4 uses `@theme` in CSS
- MUST NOT use `@tailwind base; @tailwind components; @tailwind utilities;` — use `@import "tailwindcss"`
- MUST NOT use plain CSS files or CSS modules for layout/styling
- MUST NOT use styled-components, emotion, or vanilla-extract
- MUST NOT use Mantine, Chakra UI, Material UI, or other component frameworks for styling
- MUST NOT hardcode hex color values when a design token exists
- MUST NOT hardcode pixel spacing values when a Tailwind spacing class exists
- MUST NOT hardcode font-family values — use `var(--font-sans)` via Tailwind
- MUST NOT deploy to platforms other than Vercel
- MUST NOT use npm, yarn, or pnpm — use bun
- MUST NOT rebuild components that exist in `@policyengine/ui-kit`
- MUST NOT use `getCssVar()` — it no longer exists. SVG accepts `var()` directly.

## Related skills

- **policyengine-design-skill** — Complete design token reference (colors, typography, spacing, chart branding)
- **policyengine-interactive-tools-skill** — Embedding, hash sync, country detection patterns
- **policyengine-app-skill** — app-v2 component architecture reference
