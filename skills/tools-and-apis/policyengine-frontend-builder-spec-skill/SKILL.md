---
name: policyengine-frontend-builder-spec
description: Mandatory frontend technology requirements for PolicyEngine dashboards and interactive tools — Tailwind CSS, Next.js (App Router), @policyengine/design-system token integration, Vercel deployment
---

# Frontend builder spec

Authoritative specification for all PolicyEngine frontend projects (dashboards and interactive tools). Any agent building or validating a frontend MUST load this skill and follow every requirement below. Where another agent's instructions conflict with this spec, **this spec wins**.

## Mandatory requirements

### 1. Tailwind CSS

The application MUST use **Tailwind CSS** for all styling. Tailwind utility classes are the primary styling mechanism.

- MUST install `tailwindcss`, `postcss`, and `autoprefixer`
- MUST have a `tailwind.config.ts` at the project root
- MUST have `postcss.config.js` (or `.mjs`) at the project root
- MUST have a `globals.css` containing the Tailwind directives:
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  ```
- MUST NOT use plain CSS files or CSS modules (`*.module.css`) for layout or styling
- MUST NOT use other CSS-in-JS libraries (styled-components, emotion, vanilla-extract)
- MUST NOT use other component frameworks for styling (Mantine, Chakra UI, Material UI)
- The only CSS file allowed (besides `globals.css`) is the design-system token import

### 2. @policyengine/design-system tokens

The application MUST install and import the `@policyengine/design-system` package. Design tokens MUST be used **wherever a matching token exists** for the value needed. Custom values are acceptable ONLY when no matching token exists.

- MUST install: `bun add @policyengine/design-system`
- MUST import the CSS tokens **before** any other stylesheets — in `app/layout.tsx` before `globals.css`
- MUST map PE tokens into the Tailwind config via `theme.extend` (see integration pattern below)
- MUST NOT hardcode hex color values when a PE color token exists
- MUST NOT hardcode pixel spacing values when a PE spacing token exists
- MUST NOT hardcode font-family values — use the PE font token
- MAY use custom values when no PE token covers the need (e.g., chart-specific dimensions, animation durations)

### 3. Framework: Next.js (App Router)

The application MUST use **Next.js with the App Router**.

- MUST use `create-next-app` or equivalent to scaffold with App Router
- MUST have `next.config.ts` at the project root
- MUST have an `app/` directory with `layout.tsx` and `page.tsx`
- MUST use TypeScript (`.ts`/`.tsx` files, `tsconfig.json`)
- MUST NOT use the Pages Router (`pages/` directory)
- MUST NOT use Vite as the application bundler (Vite is only used by Vitest for testing)
- MUST NOT use other bundlers (Webpack, Parcel, esbuild, etc.)
- MUST NOT use other meta-frameworks (Remix, Gatsby, Astro, etc.)

### 4. Package manager: bun (preferred)

The application SHOULD use **bun** as the package manager. Bun is strongly preferred over npm for its speed and compatibility.

- SHOULD use `bun install` instead of `npm install`
- SHOULD use `bun run dev`, `bun run build` instead of `npm run dev`, `npm run build`
- SHOULD use `bunx vitest run` instead of `npx vitest run`
- SHOULD have a `bun.lock` lockfile (not `package-lock.json`)
- MAY fall back to npm if bun is not available on the system, but bun is the default
- MUST NOT use yarn or pnpm

### 5. Vercel deployment

The application MUST be deployed using **Vercel**.

- MUST have a `vercel.json` at the project root with appropriate configuration
- MUST use `output: 'export'` in `next.config.ts` for static export, unless the dashboard requires server-side rendering
- MUST configure the Vercel project to build from the repository root (not a subdirectory)
- MUST set any required environment variables in the Vercel project settings using the `NEXT_PUBLIC_*` prefix
- MUST deploy under the `policy-engine` Vercel scope
- MUST NOT deploy using other hosting platforms (Netlify, AWS Amplify, GitHub Pages, etc.) for the frontend

## Tailwind + design token integration pattern

### tailwind.config.ts

```ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        pe: {
          primary: {
            50: 'var(--pe-color-primary-50)',
            400: 'var(--pe-color-primary-400)',
            500: 'var(--pe-color-primary-500)',
            600: 'var(--pe-color-primary-600)',
            700: 'var(--pe-color-primary-700)',
            800: 'var(--pe-color-primary-800)',
          },
          gray: {
            50: 'var(--pe-color-gray-50)',
            100: 'var(--pe-color-gray-100)',
            200: 'var(--pe-color-gray-200)',
            500: 'var(--pe-color-gray-500)',
            600: 'var(--pe-color-gray-600)',
            700: 'var(--pe-color-gray-700)',
          },
          blue: {
            500: 'var(--pe-color-blue-500)',
            700: 'var(--pe-color-blue-700)',
          },
          text: {
            primary: 'var(--pe-color-text-primary)',
            secondary: 'var(--pe-color-text-secondary)',
            tertiary: 'var(--pe-color-text-tertiary)',
          },
          bg: {
            primary: 'var(--pe-color-bg-primary)',
            secondary: 'var(--pe-color-bg-secondary)',
            tertiary: 'var(--pe-color-bg-tertiary)',
          },
          success: 'var(--pe-color-success)',
          error: 'var(--pe-color-error)',
          warning: 'var(--pe-color-warning)',
          info: 'var(--pe-color-info)',
        },
      },
      spacing: {
        'pe-xs': 'var(--pe-space-xs)',
        'pe-sm': 'var(--pe-space-sm)',
        'pe-md': 'var(--pe-space-md)',
        'pe-lg': 'var(--pe-space-lg)',
        'pe-xl': 'var(--pe-space-xl)',
        'pe-2xl': 'var(--pe-space-2xl)',
        'pe-3xl': 'var(--pe-space-3xl)',
        'pe-4xl': 'var(--pe-space-4xl)',
      },
      fontFamily: {
        pe: ['var(--pe-font-family-primary)', 'Inter', 'sans-serif'],
        'pe-mono': ['var(--pe-font-family-mono)', 'JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'pe-xs': 'var(--pe-font-size-xs)',
        'pe-sm': 'var(--pe-font-size-sm)',
        'pe-base': 'var(--pe-font-size-base)',
        'pe-lg': 'var(--pe-font-size-lg)',
        'pe-xl': 'var(--pe-font-size-xl)',
        'pe-2xl': 'var(--pe-font-size-2xl)',
        'pe-3xl': 'var(--pe-font-size-3xl)',
      },
      borderRadius: {
        'pe-sm': 'var(--pe-radius-sm)',
        'pe-md': 'var(--pe-radius-md)',
        'pe-lg': 'var(--pe-radius-lg)',
      },
    },
  },
} satisfies Config
```

### Next.js: app/layout.tsx

```tsx
import '@policyengine/design-system/tokens.css'
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
// Use Tailwind classes mapped to PE tokens:
<div className="bg-pe-bg-primary border border-pe-gray-200 rounded-pe-md p-pe-lg flex flex-col gap-pe-xs">
  <span className="text-pe-sm text-pe-text-secondary font-medium">Metric title</span>
  <span className="text-pe-2xl font-bold text-pe-text-primary">$1,234</span>
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
│   ├── layout.tsx              # Root layout — imports tokens.css + globals.css
│   ├── page.tsx                # Main dashboard page
│   ├── globals.css             # @tailwind directives only
│   └── providers.tsx           # React Query provider (client component)
├── components/
│   └── (from plan.yaml)        # Dashboard components
├── lib/
│   ├── api/
│   │   ├── client.ts           # API client (stubs or real)
│   │   ├── types.ts            # Request/response TypeScript types
│   │   └── fixtures.ts         # Mock data for stubs
│   ├── embedding.ts            # Country detection, hash sync, share URLs
│   └── hooks/
│       └── useCalculation.ts   # React Query hooks
├── public/
├── tailwind.config.ts
├── postcss.config.js
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
- `tailwindcss`, `postcss`, `autoprefixer`
- `@policyengine/design-system`
- `@tanstack/react-query`
- `recharts` (if charts)
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
- MUST NOT use plain CSS files or CSS modules for layout/styling
- MUST NOT use styled-components, emotion, or vanilla-extract
- MUST NOT use Mantine, Chakra UI, Material UI, or other component frameworks for styling
- MUST NOT hardcode hex color values when a PE color token exists
- MUST NOT hardcode pixel spacing values when a PE spacing token exists
- MUST NOT hardcode font-family values — use the PE font token via Tailwind
- MUST NOT deploy to platforms other than Vercel

## Related skills

- **policyengine-design-skill** — Complete design token reference (colors, typography, spacing, chart branding)
- **policyengine-interactive-tools-skill** — Embedding, hash sync, country detection patterns
- **policyengine-app-skill** — app-v2 component architecture reference
