# Migrating Vite + React Apps to Next.js 16 with @policyengine/ui-kit

Guide for converting existing Vite-based PolicyEngine tools to Next.js 16 App Router while preserving functionality and adopting ui-kit.

## Migration Checklist

### 1. Package Dependencies

**Remove Vite dependencies:**
```bash
bun remove vite @vitejs/plugin-react vite-tsconfig-paths
```

**Add Next.js + ui-kit:**
```bash
bun add next@^16.0.0 react@^19 react-dom@^19
bun add @policyengine/ui-kit
bun add -D @tailwindcss/postcss postcss
```

**Update package.json scripts:**
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }
}
```

### 2. Build Configuration

**Delete Vite config:**
- Remove `vite.config.ts`
- Remove `postcss.config.js` (if using Tailwind v3 syntax)

**Create `next.config.ts`:**
```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Transpile ui-kit for RSC compatibility
  transpilePackages: ["@policyengine/ui-kit"],

  // If your Vite app proxied /api to a backend:
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
```

**Create `postcss.config.mjs`:**
```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

**Delete `tailwind.config.js` / `tailwind.config.ts`** (Tailwind v4 is CSS-first)

### 3. Directory Structure Changes

**Rename `src/pages/` to `src/views/`** to avoid collision with Next.js Pages Router conventions:
```bash
mv src/pages src/views
```

Update all imports:
```ts
// Before
import CalculatorView from "./pages/CalculatorView";

// After
import CalculatorView from "./views/CalculatorView";
```

**Create App Router structure:**
```
src/
  app/
    layout.tsx       # Root layout (replaces index.html + App wrapper)
    page.tsx         # Home route (was / in Vite router)
    not-found.tsx    # 404 page
    globals.css      # Global styles (replaces index.css)
    law/
      page.tsx       # /law route
    forms/
      page.tsx       # /forms route
  views/             # Renamed from pages/
    CalculatorView.tsx
    LawView.tsx
    TaxFormView.tsx
  components/
    ...
```

### 4. Routing Migration

**Before (Vite with react-router-dom or manual routing in App.tsx):**
```tsx
// App.tsx
function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handleLocationChange = () => setCurrentPath(window.location.pathname);
    window.addEventListener("popstate", handleLocationChange);
    return () => window.removeEventListener("popstate", handleLocationChange);
  }, []);

  return (
    <div className="app">
      <Header />
      <main>
        {currentPath === "/" && <CalculatorView />}
        {currentPath === "/law" && <LawView />}
        {currentPath === "/forms" && <TaxFormView />}
        {!["/" , "/law", "/forms"].includes(currentPath) && <NotFound />}
      </main>
    </div>
  );
}
```

**After (Next.js App Router):**

`src/app/layout.tsx`:
```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QBI Visualizer",
  description: "Qualified Business Income deduction calculator",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
```

`src/app/page.tsx`:
```tsx
import CalculatorView from "@/views/CalculatorView";

export default function HomePage() {
  return <CalculatorView />;
}
```

`src/app/law/page.tsx`:
```tsx
import LawView from "@/views/LawView";

export default function LawPage() {
  return <LawView />;
}
```

`src/app/not-found.tsx`:
```tsx
export default function NotFound() {
  return (
    <div className="text-center py-16">
      <h1 className="text-4xl font-bold mb-4">404</h1>
      <p className="text-muted-foreground">Page not found</p>
    </div>
  );
}
```

### 5. Styling Migration

**Delete old CSS entry point:**
- Remove `src/index.css` (or `App.css`)

**Create `src/app/globals.css`:**
```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";

/* Add any app-specific global styles here */
```

**If migrating from Tailwind v3 custom config**, translate theme extensions into CSS variables or accept ui-kit defaults:

Before (tailwind.config.js with custom PE colors):
```js
module.exports = {
  theme: {
    extend: {
      colors: {
        "pe-teal": { 500: "#319795" },
        "pe-blue": { 500: "#3B82F6" },
      },
    },
  },
};
```

After: The ui-kit already provides these as `bg-teal-500`, `text-blue-500`, etc. No config needed.

If you had custom colors NOT in the ui-kit, add them in `globals.css`:
```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";

@theme {
  --color-custom-purple: #9333ea;
}
```

Then use `bg-[--color-custom-purple]` or register a full palette.

### 6. Entry Point Migration

**Delete:**
- `index.html`
- `src/main.tsx` (Vite entry point)

Next.js generates HTML automatically from `app/layout.tsx`.

If your `index.html` had critical `<meta>` tags or `<link>` tags, move them to `layout.tsx`:

```tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Your App",
  description: "Description",
  icons: {
    icon: "/favicon.ico",
  },
  // Open Graph, Twitter cards, etc.
};
```

For runtime `<head>` manipulation, use Next.js `<head>` or the `metadata` API.

### 7. Client Component Boundaries

Next.js 16 App Router defaults to **Server Components**. Any component using browser APIs, hooks, or event handlers must be marked `"use client"`.

**Identify components that need client directive:**
- Uses `useState`, `useEffect`, `useReducer`, etc.
- Has event handlers (`onClick`, `onChange`, etc.)
- Uses browser APIs (`window`, `document`, `localStorage`)
- Uses third-party libraries that depend on browser globals

**Mark interactive views as client components:**

`src/views/CalculatorView.tsx`:
```tsx
"use client";

import { useState } from "react";

export default function CalculatorView() {
  const [value, setValue] = useState(0);
  // ...
}
```

**Mark interactive UI components:**

`src/components/InfoTooltip.tsx`:
```tsx
"use client";

import { Tooltip, TooltipTrigger, TooltipContent } from "@policyengine/ui-kit";
```

**Keep presentational components as Server Components** when possible (no directive needed).

### 8. TypeScript Configuration

**Replace `tsconfig.json` with Next.js defaults:**

```json
{
  "compilerOptions": {
    "target": "ES2020",
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
    "paths": {
      "@/*": ["./src/*"]
    },
    "plugins": [
      {
        "name": "next"
      }
    ]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

**Delete `tsconfig.node.json`** (Vite-specific)

### 9. Environment Variables

Next.js has different conventions:

**Vite:**
- `VITE_API_BASE_URL` accessed via `import.meta.env.VITE_API_BASE_URL`

**Next.js:**
- Public vars: `NEXT_PUBLIC_API_BASE_URL` accessed via `process.env.NEXT_PUBLIC_API_BASE_URL`
- Server-only vars: `API_SECRET` accessed via `process.env.API_SECRET` (only in Server Components)

Rename `.env` variables and update references:

```bash
# Before
VITE_API_BASE_URL=http://localhost:8000

# After
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

```ts
// Before
const apiUrl = import.meta.env.VITE_API_BASE_URL;

// After
const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
```

### 10. API Proxy Configuration

**Vite proxy (vite.config.ts):**
```ts
export default defineConfig({
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

**Next.js proxy (next.config.ts):**
```ts
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};
```

Both achieve the same effect: requests to `/api/*` are forwarded to the backend during development.

### 11. Static Assets

Vite serves `public/` at the root. Next.js does the same.

**No changes needed** for:
```
public/
  favicon.ico
  logo.png
```

Reference in code the same way:
```tsx
<img src="/logo.png" alt="Logo" />
```

### 12. Deployment

**For Vercel:**

Add `vercel.json` to specify framework (optional, usually auto-detected):
```json
{
  "framework": "nextjs"
}
```

**Update CI workflows:**

Replace Vite build commands:
```yaml
# Before
- run: npm run build  # Vite
- run: npm run preview

# After
- run: bun install --frozen-lockfile
- run: bun run build  # Next.js
```

If using GitHub Actions, check that `bun.lock` is committed (not in `.gitignore`).

### 13. ESLint Migration

**Vite apps often use `eslint.config.js` (flat config) or `.eslintrc.json` (legacy).**

Next.js 16 expects `eslint.config.mjs` (flat config) with `next` plugin:

```js
import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({
  baseDirectory: import.meta.dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // Demote legacy warnings if needed during migration
      "@typescript-eslint/no-explicit-any": "warn",
      "react/no-unescaped-entities": "warn",
    },
  },
];

export default eslintConfig;
```

**Run `bun run lint` to verify** — tighten rules incrementally.

### 14. Testing Setup

If your Vite app used Vitest:

**Option 1: Keep Vitest** (Next.js supports it)
```ts
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
  },
});
```

**Option 2: Switch to Jest** (Next.js provides `next/jest`)

## Common Gotchas

### `window` is not defined

**Symptom:** Build fails with `ReferenceError: window is not defined`

**Cause:** Server Components cannot access browser APIs.

**Fix:** Add `"use client"` to the component or wrap browser code in `useEffect`.

### CSS not loading

**Symptom:** Styles missing or Tailwind utilities not generated.

**Fix:** Verify `globals.css` is imported in `layout.tsx`:
```tsx
import "./globals.css";
```

### Dynamic imports breaking

**Symptom:** `import()` calls fail or components don't render.

**Cause:** Next.js handles code splitting differently.

**Fix:** Use `next/dynamic`:
```tsx
import dynamic from "next/dynamic";

const HeavyComponent = dynamic(() => import("@/components/HeavyComponent"), {
  ssr: false, // if it relies on browser APIs
});
```

### Routing doesn't match Vite paths

**Symptom:** `/law` works in Vite but returns 404 in Next.js.

**Cause:** Missing `src/app/law/page.tsx` file.

**Fix:** Ensure filesystem routes match old paths exactly. Check capitalization.

### Bun lockfile not committed

**Symptom:** CI fails with `lockfile out of date`

**Cause:** `bun.lock` is in `.gitignore` but CI runs `bun install --frozen-lockfile`.

**Fix:** Remove `bun.lock` from `.gitignore` and commit it.

## Verification Checklist

After migration:

- [ ] `bun install` succeeds
- [ ] `bun run dev` starts development server
- [ ] All routes from Vite app are accessible (`, `/law`, `/forms`, 404)
- [ ] Styles load correctly (ui-kit colors, Tailwind utilities)
- [ ] Interactive components work (forms, tooltips, dropdowns)
- [ ] `bun run build` completes without errors
- [ ] `bun run lint` passes (or has only expected warnings)
- [ ] API proxy works (if applicable)
- [ ] Environment variables are read correctly
- [ ] Static assets load from `/public`

## Example Migration: QBI Visualizer

See [PolicyEngine/qbi-visualizer#23](https://github.com/PolicyEngine/qbi-visualizer/pull/23) for a complete real-world migration following this guide.

Key changes:
- Replaced Vite + React 18 with Next.js 16 + React 19
- Converted `App.tsx` routing to filesystem routes under `src/app/`
- Renamed `src/pages` → `src/views` to avoid collision
- Added `@policyengine/ui-kit` with Tailwind v4 `@theme` tokens
- Migrated Vite proxy to Next.js `rewrites()`
- Marked interactive views (`CalculatorView`, `LawView`, `TaxFormView`, `InfoTooltip`) as `"use client"`
- Switched from npm to Bun with committed `bun.lock`
- Updated CI to run `bun install --frozen-lockfile` + `bun run build`

Result: 4 routes generated, lint passes with 0 errors, all functionality preserved.

## Related Skills

- `policyengine-ui-kit-consumer-skill` — Core ui-kit setup reference
- `policyengine-design-skill` — Design token usage
- `policyengine-interactive-tools-skill` — Full tool scaffolding for new Next.js apps
