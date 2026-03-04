---
name: policyengine-frontend-builder-spec
description: Mandatory frontend technology requirements for PolicyEngine dashboards and interactive tools — Tailwind CSS v4, Next.js (App Router), @policyengine/ui-kit, @policyengine/design-system token integration, Vercel deployment
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

  @theme {
    /* Bridge PE design tokens into Tailwind */
    --color-pe-primary-50: var(--pe-color-primary-50);
    --color-pe-primary-400: var(--pe-color-primary-400);
    --color-pe-primary-500: var(--pe-color-primary-500);
    --color-pe-primary-600: var(--pe-color-primary-600);
    --color-pe-primary-700: var(--pe-color-primary-700);
    --color-pe-primary-800: var(--pe-color-primary-800);
    /* ... all color, spacing, font-size, radius bridges */
  }
  ```
- MUST NOT have a `tailwind.config.ts` or `tailwind.config.js` — Tailwind v4 uses `@theme` in CSS instead
- MUST NOT have a `postcss.config.js` or `postcss.config.mjs` — Tailwind v4 does not require PostCSS
- MUST NOT use `@tailwind base; @tailwind components; @tailwind utilities;` — use `@import "tailwindcss"` instead
- MUST NOT use plain CSS files or CSS modules (`*.module.css`) for layout or styling
- MUST NOT use other CSS-in-JS libraries (styled-components, emotion, vanilla-extract)
- MUST NOT use other component frameworks for styling (Mantine, Chakra UI, Material UI)
- The only CSS files allowed are `globals.css` and `@policyengine/ui-kit/styles.css`

### 2. @policyengine/ui-kit (component library)

The application MUST install `@policyengine/ui-kit` and use it as the primary component library. **MUST use ui-kit components when an equivalent exists** — do NOT rebuild components that ui-kit already provides.

- MUST install: `bun add @policyengine/ui-kit`
- MUST import styles in `app/layout.tsx`: `import '@policyengine/ui-kit/styles.css'`
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
| Utilities | `formatCurrency`, `formatPercent`, `formatNumber`, `getCssVar` |

**Component precedence rule:** When building UI:
1. **First**: Use `@policyengine/ui-kit` if it has the component
2. **Second**: Use [shadcn/ui](https://ui.shadcn.com) primitives (Dialog, Popover, Tooltip, Select, DropdownMenu, etc.) styled with Tailwind + `pe-*` tokens
3. **Third**: Build custom from scratch with Tailwind + `pe-*` tokens

### 3. @policyengine/design-system tokens

The application MUST load `@policyengine/design-system` tokens. Design tokens MUST be used **wherever a matching token exists**.

- MUST load tokens via CDN `<link>` in `app/layout.tsx`'s `<head>`:
  ```html
  <link rel="stylesheet" href="https://unpkg.com/@policyengine/design-system/dist/tokens.css" />
  ```
- MUST bridge PE tokens into Tailwind via the `@theme` block in `globals.css` (see integration pattern below)
- MUST NOT hardcode hex color values when a PE color token exists
- MUST NOT hardcode pixel spacing values when a PE spacing token exists
- MUST NOT hardcode font-family values — use the PE font token
- MAY use custom values when no PE token covers the need (e.g., chart-specific dimensions, animation durations)

**`getCssVar()` helper:** For Recharts and other SVG libraries that need resolved color strings (not CSS `var()` references), use the `getCssVar` utility from ui-kit:
```tsx
import { getCssVar } from '@policyengine/ui-kit';
const primaryColor = getCssVar('--pe-color-primary-500'); // '#319795'
```

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
- MUST style shadcn/ui components with Tailwind + `pe-*` tokens (the ui-kit already defines shadcn/ui semantic tokens like `background`, `foreground`, `primary`, `muted` in its `@theme` block)
- MUST NOT use shadcn/ui when an equivalent `@policyengine/ui-kit` component exists

## Tailwind v4 + design token integration pattern

### globals.css

```css
@import "tailwindcss";

@theme {
  /* Primary brand colors — teal */
  --color-pe-primary-50: var(--pe-color-primary-50);
  --color-pe-primary-100: var(--pe-color-primary-100);
  --color-pe-primary-200: var(--pe-color-primary-200);
  --color-pe-primary-300: var(--pe-color-primary-300);
  --color-pe-primary-400: var(--pe-color-primary-400);
  --color-pe-primary-500: var(--pe-color-primary-500);
  --color-pe-primary-600: var(--pe-color-primary-600);
  --color-pe-primary-700: var(--pe-color-primary-700);
  --color-pe-primary-800: var(--pe-color-primary-800);
  --color-pe-primary-900: var(--pe-color-primary-900);

  /* Gray scale */
  --color-pe-gray-50: var(--pe-color-gray-50);
  --color-pe-gray-100: var(--pe-color-gray-100);
  --color-pe-gray-200: var(--pe-color-gray-200);
  --color-pe-gray-300: var(--pe-color-gray-300);
  --color-pe-gray-400: var(--pe-color-gray-400);
  --color-pe-gray-500: var(--pe-color-gray-500);
  --color-pe-gray-600: var(--pe-color-gray-600);
  --color-pe-gray-700: var(--pe-color-gray-700);
  --color-pe-gray-800: var(--pe-color-gray-800);
  --color-pe-gray-900: var(--pe-color-gray-900);

  /* Blue accent */
  --color-pe-blue-500: var(--pe-color-blue-500);
  --color-pe-blue-700: var(--pe-color-blue-700);

  /* Semantic text colors */
  --color-pe-text-primary: var(--pe-color-text-primary);
  --color-pe-text-secondary: var(--pe-color-text-secondary);
  --color-pe-text-tertiary: var(--pe-color-text-tertiary);
  --color-pe-text-inverse: var(--pe-color-text-inverse);

  /* Semantic background colors */
  --color-pe-bg-primary: var(--pe-color-bg-primary);
  --color-pe-bg-secondary: var(--pe-color-bg-secondary);
  --color-pe-bg-tertiary: var(--pe-color-bg-tertiary);

  /* Semantic border colors */
  --color-pe-border-light: var(--pe-color-border-light);
  --color-pe-border-medium: var(--pe-color-border-medium);
  --color-pe-border-dark: var(--pe-color-border-dark);

  /* Status colors */
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

### Next.js: app/layout.tsx

```tsx
import '@policyengine/ui-kit/styles.css'
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

### Usage in components

```tsx
// Prefer ui-kit components:
import { MetricCard, Button, Card, CardContent } from '@policyengine/ui-kit';
import { formatCurrency } from '@policyengine/ui-kit';

// Use Tailwind classes with pe-* tokens for custom layouts:
<div className="bg-pe-bg-primary border border-pe-border-light rounded-pe-md p-pe-lg flex flex-col gap-pe-xs">
  <span className="text-sm text-pe-text-secondary font-medium">Metric title</span>
  <span className="text-2xl font-bold text-pe-text-primary">{formatCurrency(1234)}</span>
</div>

// Responsive design uses Tailwind breakpoint prefixes:
<main className="max-w-[1200px] mx-auto px-pe-xl py-pe-lg font-pe text-pe-text-primary">
  <div className="flex gap-pe-xl md:flex-col">
    {/* sidebar collapses at md breakpoint */}
  </div>
</main>
```

## Project structure

```
DASHBOARD_NAME/
├── app/
│   ├── layout.tsx              # Root layout — CDN tokens + ui-kit styles + globals.css
│   ├── page.tsx                # Main dashboard page
│   ├── globals.css             # @import "tailwindcss" + @theme block
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
- MUST NOT hardcode hex color values when a PE color token exists
- MUST NOT hardcode pixel spacing values when a PE spacing token exists
- MUST NOT hardcode font-family values — use the PE font token via Tailwind
- MUST NOT deploy to platforms other than Vercel
- MUST NOT use npm, yarn, or pnpm — use bun
- MUST NOT rebuild components that exist in `@policyengine/ui-kit`

## Related skills

- **policyengine-design-skill** — Complete design token reference (colors, typography, spacing, chart branding)
- **policyengine-interactive-tools-skill** — Embedding, hash sync, country detection patterns
- **policyengine-app-skill** — app-v2 component architecture reference
