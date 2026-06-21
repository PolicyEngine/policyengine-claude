---
name: policyengine-ui-kit-consumer
description: |
  This skill should be used when setting up a new project that uses @policyengine/ui-kit,
  debugging CSS or styling issues in a consumer app, or when Tailwind utility classes are not
  being generated. Also use when creating globals.css, configuring PostCSS, or troubleshooting
  "no styles", "no spacing", or "no layout" problems.
  Triggers: "ui-kit import", "globals.css setup", "Tailwind not working", "styles not applying",
  "utility classes missing", "setup ui-kit", "PostCSS config", "no styling", "CSS broken",
  "import ui-kit", "theme.css", "no layout", "no spacing", "@tailwindcss/postcss",
  "PolicyEngineShell", "multizone shell", "PolicyEngine header", "PolicyEngine footer"
---

# Consuming @policyengine/ui-kit

How to correctly import and use the PolicyEngine UI kit's design system in any consumer application. This skill covers the required setup, the correct import order, and common mistakes that cause styling to break.

## Required Consumer Setup

Every app using `@policyengine/ui-kit` needs exactly three things:

### 1. Install dependencies

```bash
bun add @policyengine/ui-kit
bun add -D @tailwindcss/postcss postcss
```

### 2. Create `postcss.config.mjs`

```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

No other PostCSS plugins needed — `@tailwindcss/postcss` handles imports, vendor prefixes, and nesting internally.

### 3. Create `app/globals.css` with two imports

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

**Both lines are required. The order matters.** Tailwind must come first because the ui-kit's `@theme` blocks extend it.

This provides:
- All Tailwind v4 utility classes (`flex`, `grid`, `p-4`, `text-sm`, etc.)
- All PolicyEngine design tokens (colors, fonts, spacing, breakpoints)
- shadcn/ui semantic tokens (`bg-primary`, `text-foreground`, `border-border`)
- Brand palette (`bg-teal-500`, `text-gray-600`, `bg-blue-500`)
- Base element styles (body font, border defaults, slider styling)

## Canonical PolicyEngine Shell

Multizone apps must render the PolicyEngine shell themselves. The parent app-v2
rewrite cannot inject a header or footer into a child app response, and iframes
should not be used to fake a shared shell.

For Next App Router apps, prefer the runtime shell exports from ui-kit instead
of copying header constants into each repo:

```tsx
import { PolicyEngineShell } from "@policyengine/ui-kit";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <PolicyEngineShell country="us">{children}</PolicyEngineShell>
      </body>
    </html>
  );
}
```

Use `country="uk"` for UK-only apps. If the app needs a custom main wrapper or
sticky local toolbar, render the header and footer separately:

```tsx
import { PolicyEngineFooter, PolicyEngineHeader } from "@policyengine/ui-kit";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <PolicyEngineHeader country="uk" />
        {children}
        <PolicyEngineFooter country="uk" />
      </body>
    </html>
  );
}
```

When adding a PE header above an app-local sticky bar, offset the local sticky
bar by the shared header height:

```css
.local-toolbar {
  position: sticky;
  top: var(--spacing-header, 58px);
}
```

Static HTML routes still need visible PE branding and nav. Prefer migrating the
route to the canonical Next stack; if that is not feasible, include a small
static shell in the generated HTML. Do not rely on app-v2 rewrites, iframes, or
the parent route to add the shell after the fact.

For multizone apps, verify both the destination URL and the policyengine.org
source URL. The source URL is the one users and ads see.

## How It Works

Understanding the flow prevents debugging confusion:

1. The consumer's build tool (Next.js/Vite) processes `globals.css` through `@tailwindcss/postcss`
2. `@import "tailwindcss"` establishes the cascade layers and enables utility class generation
3. Tailwind's automatic source detection scans from `process.cwd()` (the consumer's project root) — this is why the consumer's utility classes get generated
4. `@import "@policyengine/ui-kit/theme.css"` is inlined by Tailwind's import bundler
5. The ui-kit's `@theme` and `@theme inline` blocks merge into the consumer's Tailwind build
6. The ui-kit's `@source` directive tells Tailwind to also scan the ui-kit's own component files
7. The ui-kit's `@layer base` styles apply within the existing cascade

## What NOT to Do

### Do NOT skip the Tailwind import

```css
/* WRONG — utility classes will not be generated */
@import "@policyengine/ui-kit/theme.css";
```

```css
/* CORRECT */
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

Without `@import "tailwindcss"`, there is no Tailwind build. The ui-kit's `@theme` blocks have nothing to extend. No utility classes (`flex`, `p-4`, `grid`) will exist.

### Do NOT add a duplicate Tailwind import

```css
/* WRONG — double Tailwind causes conflicting resets and broken styles */
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
@import "tailwindcss";
```

The ui-kit does NOT contain `@import "tailwindcss"` inside it. One import at the top of `globals.css` is all that's needed.

### Do NOT create tailwind.config.ts

```
/* WRONG — Tailwind v4 does not use JavaScript config */
tailwind.config.ts  ← DELETE THIS
```

Tailwind v4 is CSS-first. All configuration comes from `@theme` blocks in the ui-kit's theme CSS. There is no `content` array, no `theme.extend`, no JavaScript config.

### Do NOT add postcss-import or autoprefixer

```js
/* WRONG — these conflict with @tailwindcss/postcss */
export default {
  plugins: {
    "postcss-import": {},
    "@tailwindcss/postcss": {},
    "autoprefixer": {},
  },
};
```

```js
/* CORRECT — @tailwindcss/postcss handles both internally */
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

### Do NOT put `@import "tailwindcss"` inside the ui-kit package

If working on the ui-kit itself, never add `@import "tailwindcss"` to `tokens.css`. The consumer owns that import. See `tailwind-design-system-authoring` skill for details.

### Do NOT hardcode hex colors or font names

```tsx
/* WRONG */
<div style={{ color: '#319795', fontFamily: 'Inter' }}>

/* CORRECT — use Tailwind classes */
<div className="text-teal-500 font-sans">

/* CORRECT — use CSS variables for inline styles */
<div style={{ color: 'var(--primary)', fontFamily: 'var(--font-sans)' }}>
```

## Troubleshooting

### "No styles at all" — page is unstyled

1. Verify `globals.css` has `@import "tailwindcss"` as the first line
2. Verify `postcss.config.mjs` exists with `@tailwindcss/postcss`
3. Verify `@tailwindcss/postcss` and `postcss` are installed as devDependencies
4. Verify `globals.css` is imported in `app/layout.tsx` (or `pages/_app.tsx`)

### "Tokens load but no utility classes" — colors work but no flex/grid/padding

This means `@theme` tokens are being processed but Tailwind's utility generation isn't scanning files correctly.

**If missing classes are from the consumer's own components** (`app/`, `components/`):
1. Verify `@import "tailwindcss"` comes BEFORE the ui-kit import (order matters)
2. Check that `process.cwd()` is the project root when the build runs
3. If in a monorepo, add `source()` to the import: `@import "tailwindcss" source("./src")`

**If missing classes are from ui-kit components** (`DashboardShell`, `Header`, `InputPanel`, etc.):
The ui-kit's `@source` directive in `tokens.css` may not match the actual directory structure. This is a ui-kit-side fix — the `@source` glob must cover all directories containing `.tsx` files with `className=` attributes. See the `tailwind-design-system-authoring` skill for the verification procedure.

### "Double styling / Tailwind defaults override tokens"

This means Tailwind is being imported twice.

1. Check that the ui-kit's `tokens.css` does NOT contain `@import "tailwindcss"`
2. Check that `globals.css` has only ONE `@import "tailwindcss"` line
3. Check for other CSS files that might import Tailwind

### "Utility classes from ui-kit components missing"

The ui-kit ships `@source` directives to tell Tailwind to scan its components. If this fails:

1. Add a manual `@source` in `globals.css`:
   ```css
   @import "tailwindcss";
   @import "@policyengine/ui-kit/theme.css";
   @source "../node_modules/@policyengine/ui-kit/src";
   ```
2. If using `bun link` (symlinked package), the path resolves differently — check the actual resolved path

## Framework-Specific Notes

### Next.js 14 (App Router)

Standard setup. Requires `@tailwindcss/postcss` in PostCSS config.

```
app/
  globals.css    ← @import "tailwindcss"; @import ui-kit theme
  layout.tsx     ← import "./globals.css";
postcss.config.mjs
```

### Next.js 15+ / Next.js 16

Same setup. Turbopack processes PostCSS normally. No changes needed.

### Vite (non-Next.js)

Use `@tailwindcss/vite` instead of `@tailwindcss/postcss`:

```ts
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({ plugins: [tailwindcss()] })
```

No `postcss.config.mjs` needed — the Vite plugin handles everything.

`globals.css` is the same two imports.

### Migrating from Vite to Next.js

When converting a Vite project to Next.js (e.g., adding routing, SSR, or API routes):

1. **Remove Vite files**:
   ```bash
   rm vite.config.js index.html
   ```

2. **Switch Tailwind plugin**:
   ```bash
   bun remove @tailwindcss/vite
   bun add -D @tailwindcss/postcss postcss
   ```

3. **Create `postcss.config.mjs`**:
   ```js
   export default {
     plugins: {
       "@tailwindcss/postcss": {},
     },
   };
   ```

4. **Move app entry point**:
   - Delete `src/main.jsx` (Vite entry)
   - Create `app/layout.tsx` (Next.js root layout with `<html>` and `<body>`)
   - Move component tree to `app/page.jsx`
   - Import `globals.css` in `layout.tsx` instead of `main.jsx`

5. **Create `next.config.ts`**:
   ```ts
   export default {
     // Add any Next.js config here
   };
   ```

6. **Fix environment variable references**:
   - Replace `import.meta.env.BASE_URL` with absolute paths (e.g., `/data.json`)
   - Replace `import.meta.env.VITE_*` with `process.env.NEXT_PUBLIC_*`

7. **Update package.json scripts**:
   ```json
   {
     "scripts": {
       "dev": "next dev",
       "build": "next build",
       "start": "next start"
     }
   }
   ```

The `globals.css` stays the same — two imports, Tailwind first.

## Quick Reference

| What | Where | Content |
|------|-------|---------|
| PostCSS config | `postcss.config.mjs` | `{ plugins: { "@tailwindcss/postcss": {} } }` |
| Entry CSS | `app/globals.css` | `@import "tailwindcss"; @import "@policyengine/ui-kit/theme.css";` |
| Dependencies | `package.json` devDeps | `@tailwindcss/postcss`, `postcss` |
| Dependencies | `package.json` deps | `@policyengine/ui-kit` |

## What the Theme Provides

After the two-line import, these are available:

| Category | Examples | Source |
|----------|---------|--------|
| Semantic colors | `bg-primary`, `text-foreground`, `border-border` | `:root` + `@theme inline` |
| Brand palette | `bg-teal-500`, `text-gray-600`, `bg-blue-500` | `@theme` |
| Status colors | `text-success`, `bg-warning`, `text-error` | `@theme` |
| Chart colors | `fill-chart-1` through `fill-chart-5` | `:root` + `@theme inline` |
| Typography | `text-sm` (14px), `text-base` (16px), `font-sans` | `@theme` |
| Spacing | `h-header` (58px), `w-sidebar` (280px), `max-w-content` (976px) | `@theme` |
| Breakpoints | `xs:`, `sm:`, `md:`, `lg:`, `xl:`, `2xl:` | `@theme` |
| Radius | `rounded-sm` (4px), `rounded-md` (6px), `rounded-lg` (8px) | `@theme inline` |
| All Tailwind utilities | `flex`, `grid`, `p-4`, `gap-2`, `hidden`, etc. | `@import "tailwindcss"` |

## Migrating from `@policyengine/design-system`

`@policyengine/design-system` is **deprecated** — every new tool must use `@policyengine/ui-kit`. For repos still importing from design-system, ui-kit ships a backwards-compat shim under `@policyengine/ui-kit/legacy/*` that mirrors the design-system API exactly. Migrating is a pure import-path rename — no source rewrite needed.

| Before | After |
|---|---|
| `from "@policyengine/design-system"` | `from "@policyengine/ui-kit/legacy"` |
| `from "@policyengine/design-system/tokens"` | `from "@policyengine/ui-kit/legacy/tokens"` |
| `from "@policyengine/design-system/tokens/colors"` | `from "@policyengine/ui-kit/legacy/tokens/colors"` |
| `from "@policyengine/design-system/tokens/typography"` | `from "@policyengine/ui-kit/legacy/tokens/typography"` |
| `from "@policyengine/design-system/tokens/spacing"` | `from "@policyengine/ui-kit/legacy/tokens/spacing"` |
| `from "@policyengine/design-system/charts"` | `from "@policyengine/ui-kit/legacy/charts"` |
| `next.config.*` `transpilePackages: ['@policyengine/design-system']` | `transpilePackages: ['@policyengine/ui-kit']` |
| `vitest.config.*` `inline: ['@policyengine/design-system']` | `inline: ['@policyengine/ui-kit']` |
| HTML CDN `unpkg.com/@policyengine/design-system/dist/tokens.css` | `unpkg.com/@policyengine/ui-kit/dist/styles.css` |
| `package.json` deps `"@policyengine/design-system": "^0.3.x"` | `"@policyengine/ui-kit": "^0.9.0"` |

After the rename, prefer the canonical exports for **new** code (this gets you accessibility wins from 0.6.0+):

| Legacy | Canonical | Notes |
|---|---|---|
| `colors.primary[N]` | `palette.teal[N]` | same hex |
| `colors.gray[N]` | `palette.gray[N]` | **DIFFERENT hex** — legacy is Tailwind-3 gray, canonical is Slate |
| `colors.blue[N]` | `palette.blue[N]` | same hex |
| `colors.warning` | `semanticFills.warning` | same `#FEC601` |
| `colors.error` | `semanticFills.error` | same `#EF4444` |
| `colors.text.warning` | `var(--text-warning)` | **DIFFERENT hex** — legacy `#d9480f` fails AA at small text; canonical `#c2410c` clears 5.18:1 |
| `typography.fontFamily.primary` | `typography.fontFamily.sans` | same Inter stack |
| `chartColors` (Plotly) | `chartPalette.light` / `chartPalette.dark` | by-theme resolved hex |

Both `colors.gray[N]` and `colors.text.warning` change visible color on migration — don't bulk `sed`-replace, walk per usage.

## Common gotchas

- **Bun, not npm.** `@policyengine/ui-kit` ships ESM + CJS, but the lockfile pattern across PolicyEngine is `bun.lock` committed (NOT in `.gitignore`). If your CI runs `bun install --frozen-lockfile`, make sure `bun.lock` is committed — otherwise the install always fails.
- **CI order: build before test.** ui-kit's `tests/consumer-types/` harness type-checks the *built* `dist/` surface against a bundler-resolution consumer. If your repo embeds a similar pattern (or just runs `tsc --noEmit` against `node_modules/@policyengine/ui-kit`), put `bun run build` *before* `bun run test` in the workflow.
- **Don't fight Vercel's Root Directory.** If your `package.json` lives in a subdirectory (`app/`, `frontend/`, etc.), set the Vercel project's Root Directory to that subdir in the dashboard — don't add a root-level `vercel.json` with `cd subdir && bun install` commands. The two configs fight and the framework detector fails ("No Next.js version detected").
- **`Header` API changed in 0.4.0.** Old props (`variant`, `logo`, `navLinks`, `children`) no longer exist. New API uses `navItems`, `logoSrc`, `linkComponent`. If you bump from `^0.3.x` and hit `Type '{ children: Element; variant: string; logo: Element; navLinks: …; }' is not assignable to type 'IntrinsicAttributes & HeaderProps'`, that's the migration. Read `@policyengine/ui-kit/dist/layout/header/Header.d.ts` for the current shape.

## Next 16 Multizone Migration Checklist

For child apps served under `policyengine.org`, the target state is:

1. Next.js App Router on Next 16.
2. Tailwind v4 with `@import "tailwindcss";` before `@import "@policyengine/ui-kit/theme.css";`.
3. `@policyengine/ui-kit` installed and used for the PE shell.
4. No Vite-era Vercel overrides (`framework: vite`, stale `outputDirectory`, or root-level `cd subdir &&` build commands).
5. The deployed policyengine.org source route renders PE branding plus the main nav labels (`Research`, `Model`, `API`, `Donate`).

Use `PolicyEngineShell` for straightforward tools, and use
`PolicyEngineHeader`/`PolicyEngineFooter` separately when the page structure
needs a custom main container. Keep the shell runtime-owned by ui-kit; do not
copy nav arrays into new apps.

## Related Skills

- `policyengine-design-skill` — Full token reference (hex values, usage guidelines)
- `policyengine-tailwind-shadcn-skill` — `@theme` namespace mechanics, SVG var() usage
- `policyengine-interactive-tools-skill` — Full tool scaffolding checklist
- `policyengine-vercel-deployment-skill` — Deploying consumer apps
