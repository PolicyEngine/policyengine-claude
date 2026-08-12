---
name: policyengine-vite-to-nextjs-migration
description: Migrating legacy Vite-based PolicyEngine apps (using Mantine, Plotly, or other UI frameworks) to Next.js App Router while preserving existing UI code
---

# Vite to Next.js migration for legacy PolicyEngine apps

How to migrate existing Vite-based PolicyEngine apps to Next.js App Router when they use UI frameworks other than the current standard (@policyengine/ui-kit + Tailwind).

## When to use this skill

**Use this skill when:**
- Migrating an existing Vite app to Next.js for consistency with PolicyEngine's deployment stack
- The app uses Mantine, Chakra UI, Material UI, or other component libraries
- The goal is framework migration only (not a full UI rewrite)
- You want to preserve the existing UI code while modernizing the build/deployment layer

**Do NOT use this skill when:**
- Building a new dashboard or tool from scratch (use `policyengine-frontend-builder-spec` instead — all new apps must use Next.js + Tailwind + ui-kit)
- The app is already on Next.js
- You're doing a full rewrite (in that case, follow the standard stack requirements)

## Migration strategy

The migration is **framework-only**: move from Vite bundler + SPA routing to Next.js App Router while keeping all existing UI components and styling unchanged.

### Core principle: Preserve the UI layer

Unlike new apps (which must use @policyengine/ui-kit + Tailwind), legacy migrations can retain their existing component library (Mantine, Chakra, etc.) to minimize diff size and risk.

**What changes:**
- Build system: `vite` → `next build`
- Routing: React Router → App Router file-based routing
- Entry point: `index.html` + `main.tsx` → `app/layout.tsx` + `app/page.tsx`
- Dev server: `vite dev` → `next dev`
- Deployment: Static export via `output: 'export'` in `next.config.ts`

**What stays the same:**
- All existing components (Mantine, Plotly, etc.)
- All existing styles (CSS modules, component library themes, etc.)
- All existing business logic and state management
- Package manager (keep using `bun`)

## Migration steps

### 1. Install Next.js dependencies

```bash
bun add next react react-dom
bun add -D @types/react @types/react-dom @types/node
```

**Remove Vite dependencies:**
```bash
bun remove vite @vitejs/plugin-react
```

### 2. Create Next.js configuration

**next.config.ts:**
```ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'export',  // Static export for Vercel deployment
  trailingSlash: true,
  reactStrictMode: true,
};

export default nextConfig;
```

**tsconfig.json updates:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowJs": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 3. Move from index.html to App Router

**Old structure (Vite):**
```
index.html                 # Entry point with <script src="main.tsx">
src/
  main.tsx                 # ReactDOM.createRoot
  App.tsx                  # Root component
  components/              # UI components
```

**New structure (Next.js):**
```
src/
  app/
    layout.tsx             # Root layout (replaces index.html metadata)
    page.tsx               # Main page (replaces App.tsx)
  components/              # UI components (unchanged)
```

**Migrating index.html metadata:**

Extract `<head>` content from `index.html` into `app/layout.tsx` using Next.js Metadata API:

```tsx
// src/app/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Your App Title',
  description: 'Your app description',
  icons: {
    icon: '/favicon.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

**Migrating main.tsx + App.tsx:**

Move the root component from `src/App.tsx` to `src/app/page.tsx`:

```tsx
// src/app/page.tsx
import YourMainComponent from '@/components/YourMainComponent';

export default function HomePage() {
  return <YourMainComponent />;
}
```

If `App.tsx` included providers (React Query, theme providers, etc.), move them to `layout.tsx` or a separate `providers.tsx` client component:

```tsx
// src/app/providers.tsx (if needed)
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MantineProvider } from '@mantine/core';  // or your UI framework
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider>{children}</MantineProvider>
    </QueryClientProvider>
  );
}
```

Then import in `layout.tsx`:
```tsx
import { Providers } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

### 4. Handle CSS imports

**If using CSS Modules:** No changes needed — Next.js supports CSS Modules natively.

**If using global CSS:** Import in `layout.tsx`:
```tsx
import './globals.css';
import '@mantine/core/styles.css';  // or your UI framework's CSS
```

**If using component library themes (Mantine, Chakra, etc.):** Keep them as-is in `providers.tsx` or `layout.tsx`.

### 5. Update scripts in package.json

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

Remove old Vite scripts (`vite`, `vite build`, `vite preview`).

### 6. Handle public assets

**Vite:** Assets in `public/` are served at `/public/asset.png`
**Next.js:** Assets in `public/` are served at `/asset.png` (no `/public` prefix)

Update all asset references:
```tsx
// Old (Vite)
<img src="/public/logo.png" />

// New (Next.js)
<img src="/logo.png" />
```

### 7. Remove Vite-specific files

Delete:
- `vite.config.ts` or `vite.config.js`
- `index.html` (replaced by `app/layout.tsx`)
- `src/main.tsx` (replaced by `app/page.tsx`)

### 8. Test the migration

```bash
# Development server
bun run dev

# Production build (static export)
bun run build
```

Verify:
- [ ] Dev server runs without errors
- [ ] Production build completes successfully
- [ ] All pages render correctly
- [ ] All existing functionality works (forms, charts, API calls, etc.)
- [ ] Assets (images, fonts, etc.) load correctly

## Client Components

Next.js App Router uses Server Components by default. Components that use hooks, browser APIs, or event handlers must be marked as Client Components:

```tsx
'use client';

import { useState } from 'react';

export function InteractiveComponent() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

**Mark as Client Components:**
- Any component using React hooks (`useState`, `useEffect`, `useQuery`, etc.)
- Any component using browser APIs (`window`, `document`, `localStorage`, etc.)
- Any component using event handlers (`onClick`, `onChange`, etc.)
- Provider components (React Query, theme providers, etc.)

**Leave as Server Components (default):**
- Pure presentational components with no interactivity
- Layout components that only render children

## Example: Mantine + Plotly migration

**Before (Vite structure):**
```
index.html
src/
  main.tsx              # ReactDOM.createRoot
  App.tsx               # MantineProvider + main UI
  components/
    Chart.tsx           # Plotly chart
  styles/
    global.css
```

**After (Next.js structure):**
```
next.config.ts
src/
  app/
    layout.tsx          # Metadata + Providers (MantineProvider)
    page.tsx            # Main UI
    globals.css
  components/
    Chart.tsx           # Plotly chart (marked 'use client')
```

**Key changes:**
1. `index.html` metadata → `app/layout.tsx` Metadata API
2. `main.tsx` + `App.tsx` → `app/layout.tsx` (providers) + `app/page.tsx` (UI)
3. MantineProvider moved to `layout.tsx` or `providers.tsx`
4. All Plotly charts marked `'use client'` (they use browser APIs)
5. Global CSS imported in `layout.tsx`
6. Scripts updated in `package.json`

## Gotchas

### 1. Default exports in Server Components

Next.js requires default exports for `layout.tsx` and `page.tsx`:
```tsx
// CORRECT
export default function RootLayout({ children }) { ... }

// WRONG
export function RootLayout({ children }) { ... }
```

### 2. Client-only libraries (Plotly, Recharts, charting libraries)

Most charting libraries use browser APIs and must be Client Components:
```tsx
'use client';

import Plot from 'react-plotly.js';

export function PlotlyChart({ data }) {
  return <Plot data={data} />;
}
```

### 3. Environment variables

**Vite:** `import.meta.env.VITE_API_URL`
**Next.js:** `process.env.NEXT_PUBLIC_API_URL`

Update all env var references:
```tsx
// Old (Vite)
const apiUrl = import.meta.env.VITE_API_URL;

// New (Next.js)
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

Update `.env` file:
```env
# Old
VITE_API_URL=https://api.example.com

# New
NEXT_PUBLIC_API_URL=https://api.example.com
```

### 4. Dynamic imports with SSR

If a component breaks during build with "window is not defined" or similar errors, use dynamic import with `ssr: false`:

```tsx
import dynamic from 'next/dynamic';

const PlotlyChart = dynamic(() => import('@/components/PlotlyChart'), {
  ssr: false,
});
```

### 5. JSON-LD structured data

If the original `index.html` included JSON-LD for SEO, move it to `layout.tsx` using `next/script`:

```tsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Script id="json-ld" type="application/ld+json">
          {JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebApplication',
            name: 'Your App',
            // ...
          })}
        </Script>
      </body>
    </html>
  );
}
```

### 6. Google Analytics

Move GA4 script from `index.html` to `layout.tsx` using `next/script` with `strategy="afterInteractive"`:

```tsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-XXXXXXXXXX');
          `}
        </Script>
      </body>
    </html>
  );
}
```

## Deployment

Follow standard PolicyEngine Vercel deployment:

1. Ensure `next.config.ts` has `output: 'export'`
2. Deploy to Vercel under `policy-engine` scope
3. Verify static export works (`bun run build` produces `out/` directory)

See `policyengine-vercel-deployment-skill` for full deployment instructions.

## Testing strategy

**Minimal test changes:** If the app already has tests, they should continue working with minimal changes:

- If using Vitest: Keep `vitest.config.ts`, update any imports that changed
- If using Jest: May need to update config for Next.js compatibility
- Component tests: Should work unchanged if using Testing Library

**Focus testing on:**
- [ ] Pages render correctly in both dev and production builds
- [ ] All interactive features work (forms, buttons, charts)
- [ ] API calls succeed
- [ ] Routing works (if multi-page app)

## When to consider a full rewrite instead

This migration strategy preserves the existing UI framework. Consider a **full rewrite to the standard PolicyEngine stack** (Next.js + Tailwind + ui-kit) if:

- The app is small (< 1000 lines of component code)
- The UI framework is outdated or has security issues
- You're making significant UX changes anyway
- The app will receive ongoing development (not a static analysis tool)

For small tools and active projects, the standard stack provides better long-term maintainability.

## Related skills

- **policyengine-frontend-builder-spec** — Required stack for all new PolicyEngine apps
- **policyengine-vercel-deployment-skill** — Deployment patterns
- **policyengine-interactive-tools-skill** — Building new standalone tools (use standard stack)
