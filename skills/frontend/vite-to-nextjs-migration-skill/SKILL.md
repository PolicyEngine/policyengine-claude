---
name: vite-to-nextjs-migration
description: |
  Migrating legacy PolicyEngine tools from Vite + react-router-dom to Next.js 16 App Router.
  Use when updating older repos to match current PolicyEngine frontend standards.
  Triggers: "migrate from Vite", "convert to Next.js", "update to App Router",
  "remove react-router-dom", "Vite to Next.js"
---

# Migrating from Vite to Next.js App Router

How to migrate legacy PolicyEngine React apps from Vite + react-router-dom to Next.js 16 App Router with Tailwind 4.

## Background

Older PolicyEngine tools (pre-2024) may use Vite as their bundler with react-router-dom for routing. Current PolicyEngine standards require Next.js 14+ App Router for all frontend applications. This guide covers the migration pattern.

## Migration Checklist

### 1. Update dependencies

**Remove:**
```json
{
  "vite": "*",
  "@vitejs/plugin-react": "*",
  "react-router-dom": "*"
}
```

**Add:**
```bash
bun add next@16.2.6 react@19.2.0 react-dom@19.2.0
bun add -D @tailwindcss/postcss postcss
bun add @policyengine/ui-kit
```

### 2. Replace Vite config with Next.js config

**Delete:**
- `vite.config.ts` or `vite.config.js`
- `index.html` (Vite's HTML entry point)

**Create `next.config.ts`:**
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export", // for static export if needed
  images: {
    unoptimized: true, // required for static export
  },
};

export default nextConfig;
```

### 3. Restructure to App Router filesystem

**Before (Vite):**
```
src/
  App.tsx          ← router setup with react-router-dom
  pages/
    Home.tsx
    Country.tsx
  main.tsx         ← ReactDOM.render()
index.html
```

**After (Next.js App Router):**
```
app/
  layout.tsx       ← root layout with <html> wrapper
  page.tsx         ← homepage (redirects if needed)
  [countryId]/
    page.tsx       ← dynamic route for country pages
  globals.css      ← Tailwind imports
```

### 4. Convert routing patterns

#### React Router → Next.js App Router

**Before (react-router-dom):**
```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/:countryId" element={<CountryPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**After (Next.js filesystem):**
```tsx
// app/page.tsx - homepage
import { redirect } from "next/navigation";

export default function RootPage() {
  // Redirect based on locale or default
  redirect("/us");
}

// app/[countryId]/page.tsx - country page
export default function CountryPage({
  params,
}: {
  params: { countryId: string };
}) {
  const { countryId } = params;
  return <YourCountryComponent countryId={countryId} />;
}
```

#### Dynamic imports and navigation

**Before:**
```tsx
import { useNavigate, useParams } from "react-router-dom";

function Component() {
  const navigate = useNavigate();
  const { countryId } = useParams();

  return <button onClick={() => navigate("/uk")}>Go to UK</button>;
}
```

**After:**
```tsx
import { useRouter } from "next/navigation";
import Link from "next/link";

function Component({ params }: { params: { countryId: string } }) {
  const router = useRouter();
  const { countryId } = params;

  // Prefer Link for navigation
  return <Link href="/uk">Go to UK</Link>;

  // Or router.push for programmatic navigation
  // router.push("/uk");
}
```

### 5. Set up Tailwind 4 + ui-kit

**Create `postcss.config.mjs`:**
```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

**Create `app/globals.css`:**
```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

**Import in `app/layout.tsx`:**
```tsx
import "./globals.css";

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

**Delete:**
- `tailwind.config.js` or `tailwind.config.ts` (Tailwind v4 uses CSS config)
- Old CSS import from `main.tsx` or `index.html`

See `policyengine-ui-kit-consumer-skill` for full Tailwind 4 setup details.

### 6. Convert data imports

Vite's special import features (e.g., `?raw`, `?url`) don't exist in Next.js.

**Before (Vite raw import for YAML):**
```tsx
import dataYaml from "./data.yaml?raw";
import yaml from "js-yaml";

const data = yaml.load(dataYaml);
```

**After (Next.js - use JSON instead):**
```tsx
import data from "./data.json";
// Just use the data directly
```

**Migration:** Convert YAML files to JSON:
```bash
# Manual conversion or use a script
python -c "import yaml, json, sys; json.dump(yaml.safe_load(sys.stdin), sys.stdout, indent=2)" < data.yaml > data.json
```

Or for multiple files:
```python
# scripts/convert_yaml_to_json.py
import yaml
import json
from pathlib import Path

for yaml_file in Path("src/data").glob("*.yaml"):
    with open(yaml_file) as f:
        data = yaml.safe_load(f)

    json_file = yaml_file.with_suffix(".json")
    with open(json_file, "w") as f:
        json.dump(data, f, indent=2)
```

### 7. Update package.json scripts

**Before:**
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

**After:**
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

### 8. Handle environment variables

**Before (Vite):**
- Variables prefixed with `VITE_` are exposed to client
- Access via `import.meta.env.VITE_API_URL`

**After (Next.js):**
- Variables prefixed with `NEXT_PUBLIC_` are exposed to client
- Access via `process.env.NEXT_PUBLIC_API_URL`

**Migration:**
1. Rename env vars in `.env`:
   ```diff
   - VITE_API_URL=https://api.example.com
   + NEXT_PUBLIC_API_URL=https://api.example.com
   ```

2. Update references in code:
   ```diff
   - const apiUrl = import.meta.env.VITE_API_URL;
   + const apiUrl = process.env.NEXT_PUBLIC_API_URL;
   ```

### 9. Root layout requirements

Next.js App Router requires a root `app/layout.tsx` with `<html>` and `<body>` tags:

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PolicyEngine Tool Name",
  description: "Tool description for SEO",
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

Do NOT include `<html>` or `<body>` in individual page components.

### 10. Client vs Server Components

Next.js App Router uses React Server Components by default. Components that use:
- `useState`, `useEffect`, `useContext`
- Event handlers (`onClick`, `onChange`, etc.)
- Browser APIs (`window`, `localStorage`, etc.)

Must be marked as client components:

```tsx
"use client";

import { useState } from "react";

export default function InteractiveComponent() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

**When in doubt:** Add `"use client"` at the top of the file. Server Components are an optimization, not a requirement for migration.

## Common Migration Gotchas

### 1. Missing `"use client"` directive

**Error:**
```
You're importing a component that needs useState. It only works in a Client Component
but none of its parents are marked with "use client"
```

**Fix:** Add `"use client"` to the top of the component file.

### 2. Hydration mismatches

**Error:**
```
Hydration failed because the initial UI does not match what was rendered on the server
```

**Common causes:**
- Using `Date.now()` or `Math.random()` directly in render
- Accessing `window` or `localStorage` without checking if it exists
- Different content between server and client

**Fix:** Move client-only logic into `useEffect`:
```tsx
"use client";
import { useEffect, useState } from "react";

export default function Component() {
  const [clientData, setClientData] = useState(null);

  useEffect(() => {
    setClientData(window.localStorage.getItem("key"));
  }, []);

  return <div>{clientData}</div>;
}
```

### 3. Import.meta.url not available

**Error:**
```
Cannot use 'import.meta' outside a module
```

**Fix:** Next.js doesn't support `import.meta` in the same way Vite does. For file paths, use `path` module in Node.js context or public directory for static assets.

### 4. Index.html removal

Vite uses `index.html` as the entry point. Next.js generates HTML from `app/layout.tsx`.

**Migration:**
- Move any `<head>` tags to `metadata` export in layout.tsx or use `next/head`
- Move `<script>` tags to layout.tsx body or use `next/script`
- Move global styles import to layout.tsx

## Vercel Deployment

After migration, update Vercel project settings:
- Framework Preset: **Next.js**
- Build Command: `bun run build`
- Output Directory: `.next` (auto-detected)
- Install Command: `bun install`

See `policyengine-vercel-deployment-skill` for full deployment guide.

## Testing After Migration

1. **Dev server:** `bun run dev` - should start on port 3000
2. **Build:** `bun run build` - should complete without errors
3. **Routes:** Test all navigation paths work
4. **Data:** Verify JSON imports load correctly
5. **Styles:** Confirm Tailwind classes and ui-kit theme apply
6. **Interactivity:** Check useState/onClick work (with "use client")

## Example Migration: 2025-year-in-review

See `PolicyEngine/2025-year-in-review` PR #3 for a complete migration example:
- Converted from Vite + react-router-dom to Next.js 16 App Router
- Added locale-based redirect from `/` to `/us` or `/uk`
- Converted YAML data files to JSON
- Set up Tailwind 4 with `@policyengine/ui-kit ^0.9.0`
- Used filesystem routing: `/[countryId]` dynamic route

## Related Skills

- `policyengine-ui-kit-consumer-skill` — Tailwind 4 + ui-kit setup
- `policyengine-interactive-tools-skill` — Building new Next.js tools from scratch
- `policyengine-vercel-deployment-skill` — Deployment configuration
