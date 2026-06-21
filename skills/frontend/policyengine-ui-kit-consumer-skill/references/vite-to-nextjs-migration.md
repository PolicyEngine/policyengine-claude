# Migrating Vite → Next.js 16 for PolicyEngine Tools

Step-by-step guide for migrating a Vite/React app to Next.js 16 (App Router, Turbopack) to align with the PolicyEngine portfolio standard stack (Vercel + bun + Tailwind v4 + `@policyengine/ui-kit`).

## When to Use This Guide

- Migrating existing Vite-based PolicyEngine tools to Next.js 16
- Converting standalone React apps to the standard PolicyEngine tooling stack
- Repos that need to align with `cost-dashboard`, `council-tax-ctr-map`, `policyengine-model` patterns

## Reference Implementation

See [missouri-transitional-benefits PR #5](https://github.com/PolicyEngine/missouri-transitional-benefits/pull/5) for a complete migration example.

## Directory Structure Decision

For repos with both Python research code and a frontend:

### Option A: Frontend at root (NOT RECOMMENDED)
```
app/              ← Next.js App Router
components/
package.json
benefits_cliffs/  ← Python code
pyproject.toml
```
**Rejected:** Collides with existing Python files, creates confusion about what lives at root.

### Option B: Keep `app/` as project root (NOT RECOMMENDED)
```
app/
  app/            ← Next.js App Router (awkward nesting)
  components/
  package.json
```
**Rejected:** Awkward `app/app/` nesting, breaks intuition, inverts Next.js convention.

### Option C: Rename to `web/` (RECOMMENDED)
```
web/
  app/            ← Next.js App Router
  components/
  package.json
  bun.lock
benefits_cliffs/  ← Python code unchanged
pyproject.toml
```
**Chosen:** Short, conventional, minimal diff to Python side. Update `vercel.json` and `Makefile` to point at `web/`.

For frontend-only repos, keep the frontend at root with `app/` as the Next.js App Router.

## Migration Checklist

### 1. Create new Next.js structure

```bash
mkdir -p web/app web/components web/data web/__tests__
```

### 2. Migrate entry points

**From:** `app/src/main.tsx` + `app/index.html`
**To:** `web/app/layout.tsx` + `web/app/page.tsx`

Move metadata, GA4, JSON-LD, scroll/time/outbound tracking to `layout.tsx`:

```tsx
// web/app/layout.tsx
import "./globals.css";
import { Metadata } from "next";
import { GoogleAnalytics } from "@next/third-parties/google";
import Script from "next/script";

export const metadata: Metadata = {
  title: "Tool Title | PolicyEngine",
  description: "Tool description",
  icons: { icon: "/favicon.svg" },
  // ... other metadata from index.html <meta> tags
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        {/* Move JSON-LD structured data here */}
        <Script id="jsonld" type="application/ld+json">
          {JSON.stringify({ /* ... */ })}
        </Script>
      </head>
      <body>
        {children}
        <GoogleAnalytics gaId="G-XXXXXXXXXX" />
        {/* Port scroll/time/outbound tracking scripts */}
      </body>
    </html>
  );
}
```

```tsx
// web/app/page.tsx
import App from "@/components/App";

export default function Home() {
  return <App />;
}
```

### 3. Migrate components

**From:** `app/src/App.tsx` and `app/src/components/`
**To:** `web/components/`

Add `"use client"` directive to components that use:
- `useState`, `useEffect`, `useContext`
- Event handlers (`onClick`, `onChange`)
- Browser APIs

```tsx
// web/components/App.tsx
"use client";

import { MantineProvider } from "@mantine/core";
// ... rest of component
```

**IMPORTANT:** Hoist providers like `MantineProvider` into `layout.tsx` if they don't need client state.

### 4. Handle client-only libraries (e.g., Plotly)

Libraries that depend on `window` or browser-only APIs must use `next/dynamic`:

```tsx
// web/components/PlotlyChart.tsx
"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function PlotlyChart({ data, layout, config }) {
  return <Plot data={data} layout={layout} config={config} />;
}
```

Then import `PlotlyChart` instead of importing `react-plotly.js` directly.

### 5. Migrate data and types

```bash
# Move data files
mv app/src/data/*.json web/data/

# Move types
mv app/src/types.d.ts web/types.d.ts

# Move theme config if present
mv app/src/theme.ts web/theme.ts
```

**Preserve TypeScript module augmentations** in `web/types.d.ts`:
- Keep declarations for `@policyengine/ui-kit/legacy/*`
- Keep any ambient module declarations for third-party packages

### 6. Update CSS imports

Create `web/app/globals.css`:

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";

/* Import third-party styles if needed */
@import "@mantine/core/styles.css";
@import "katex/dist/katex.min.css";
```

**Import order matters:** `tailwindcss` must come first, then ui-kit theme.

### 7. Create PostCSS config

```js
// web/postcss.config.mjs
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

### 8. Create Next.js config

```ts
// web/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@policyengine/ui-kit"],
  // Add other config as needed
};

export default nextConfig;
```

### 9. Update package.json

```json
{
  "name": "tool-name",
  "private": true,
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest"
  },
  "dependencies": {
    "next": "^16.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@policyengine/ui-kit": "^0.9.0",
    // ... other deps
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.0.0",
    "postcss": "^8.4.47",
    "typescript": "^5.6.3",
    "eslint": "^9.17.0",
    "eslint-config-next": "^16.0.0",
    "vitest": "latest",
    // ... other dev deps
  }
}
```

### 10. Update tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 11. Update environment variables

**From:** `import.meta.env.VITE_*`
**To:** `process.env.NEXT_PUBLIC_*`

Replace all instances:
```tsx
// Before (Vite)
const apiKey = import.meta.env.VITE_API_KEY;

// After (Next.js)
const apiKey = process.env.NEXT_PUBLIC_API_KEY;
```

Update `.env` file variable names accordingly.

### 12. Update Vercel config

For subdirectory deployments (Python + frontend monorepo):

```json
{
  "framework": "nextjs",
  "buildCommand": "cd web && bun run build",
  "outputDirectory": "web/.next",
  "installCommand": "cd web && bun install",
  "devCommand": "cd web && bun run dev"
}
```

For frontend-only repos (frontend at root):

```json
{
  "framework": "nextjs"
}
```

**IMPORTANT:** Do NOT set Vercel's "Root Directory" in the dashboard if you're using `vercel.json` commands. The two configs conflict and break framework detection.

### 13. Update Makefile (if present)

```makefile
install:
	cd web && bun install

dev:
	cd web && bun run dev

build:
	cd web && bun run build
```

### 14. Update .gitignore

```
# Dependencies
node_modules/

# Next.js
web/.next/
web/out/
web/.turbo

# Build artifacts
*.tsbuildinfo

# Keep lockfile
!web/bun.lock
```

**IMPORTANT:** Commit `bun.lock`. PolicyEngine CI runs `bun install --frozen-lockfile`, which fails without a committed lockfile.

### 15. Update CI workflows

```yaml
# .github/workflows/pr.yaml
jobs:
  lint-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
      - run: cd web && bun install --frozen-lockfile
      - run: cd web && bun run lint

  build-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
      - run: cd web && bun install --frozen-lockfile
      - run: cd web && bun run build

  test-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
      - run: cd web && bun install --frozen-lockfile
      - run: cd web && bun run test
```

### 16. Add smoke tests

```tsx
// web/__tests__/smoke.test.tsx
import { describe, it, expect } from "vitest";
import snapResults from "@/data/snap_results.json";

describe("Data integrity", () => {
  it("snap_results has expected structure", () => {
    expect(Array.isArray(snapResults)).toBe(true);
    expect(snapResults.length).toBeGreaterThan(0);
    expect(snapResults[0]).toHaveProperty("income");
  });
});
```

```ts
// web/vitest.config.ts
import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
```

### 17. Clean up old Vite files

```bash
rm -rf app/dist
rm app/vite.config.ts
rm app/index.html
rm app/bun.lock
```

## Common Gotchas

### 1. Client-only dependencies fail at build time

**Symptom:** `ReferenceError: window is not defined` during `bun run build`

**Fix:** Use `next/dynamic` with `{ ssr: false }` for browser-only libraries:
```tsx
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });
```

### 2. Legacy ui-kit imports break

**Symptom:** Type errors on `@policyengine/ui-kit/legacy/charts`

**Fix:** Keep type augmentations in `web/types.d.ts`:
```ts
declare module "@policyengine/ui-kit/legacy/charts" {
  export const chartColors: string[];
}
```

### 3. CI fails with "lockfile out of sync"

**Symptom:** `bun install --frozen-lockfile` fails in CI

**Fix:** Commit `web/bun.lock` and remove it from `.gitignore`.

### 4. Vercel build fails with "No framework detected"

**Symptom:** Vercel can't find Next.js even though `next.config.ts` exists

**Fix:** Either:
- Use `vercel.json` with explicit commands (shown above)
- OR set Vercel dashboard "Root Directory" to `web/` (don't mix both approaches)

### 5. Styles don't load

**Symptom:** Unstyled page or missing Tailwind utilities

**Fix:** Verify `web/app/globals.css` has:
```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

And that `globals.css` is imported in `layout.tsx`:
```tsx
import "./globals.css";
```

## Testing Checklist

Before submitting PR:

- [ ] `bun install --frozen-lockfile` succeeds
- [ ] `bun run build` compiles cleanly with Turbopack
- [ ] `bun run lint` reports 0 problems
- [ ] `bun run test` passes
- [ ] CI green (all jobs pass)
- [ ] Vercel preview deploys and renders correctly
- [ ] Client-only components (charts, etc.) load properly
- [ ] Metadata (title, description, favicon) correct
- [ ] Analytics tracking works (GA4, custom events)
- [ ] Structured data (JSON-LD) present in page source

## Related Skills

- `policyengine-ui-kit-consumer-skill` — CSS setup and Tailwind v4 configuration
- `policyengine-interactive-tools-skill` — Embedding, hash sync, country detection patterns
- `policyengine-vercel-deployment-skill` — Deployment and environment configuration
