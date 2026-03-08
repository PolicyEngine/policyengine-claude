---
name: policyengine-ui-kit-consumer
description: |
  This skill should be used when setting up a new project that uses @policyengine/ui-kit,
  debugging CSS or styling issues in a consumer app, or when Tailwind utility classes are not
  being generated. Also use when creating globals.css, configuring PostCSS, or troubleshooting
  "no styles", "no spacing", or "no layout" problems.
  Triggers: "ui-kit import", "globals.css setup", "Tailwind not working", "styles not applying",
  "utility classes missing", "setup ui-kit", "PostCSS config", "no styling", "CSS broken",
  "import ui-kit", "theme.css", "no layout", "no spacing", "@tailwindcss/postcss"
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

## Related Skills

- `policyengine-design-skill` — Full token reference (hex values, usage guidelines)
- `policyengine-tailwind-shadcn-skill` — `@theme` namespace mechanics, SVG var() usage
- `policyengine-interactive-tools-skill` — Full tool scaffolding checklist
- `policyengine-vercel-deployment-skill` — Deploying consumer apps
