# Migrating from a Broken Tailwind + ui-kit Setup

Step-by-step guide for fixing projects where the ui-kit was imported incorrectly and styles are broken.

## Symptoms of a Broken Setup

| Symptom | Likely Cause |
|---------|-------------|
| No styles at all (unstyled HTML) | Missing `@import "tailwindcss"` or missing PostCSS config |
| Colors load but no layout (no flex/grid/padding) | `@import "tailwindcss"` is inside the ui-kit, not in consumer's CSS |
| Tailwind defaults override PE tokens | Double `@import "tailwindcss"` (once in consumer, once in ui-kit) |
| Correct on first load, wrong after hot reload | PostCSS processing order issue — check import order |
| Works with Tailwind CLI but not with Next.js | Missing `@tailwindcss/postcss` in PostCSS config |

## Fix Procedure

### Step 1: Verify the ui-kit's tokens.css

Read `node_modules/@policyengine/ui-kit/src/theme/tokens.css`. It must NOT contain `@import "tailwindcss"`.

If it does, the ui-kit itself needs to be fixed (remove that line). If using a local/linked version, fix it there.

### Step 2: Clean globals.css

Replace the entire contents of `app/globals.css` with exactly:

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

Remove any:
- Additional `@import "tailwindcss"` lines
- Manual `@theme` blocks that duplicate ui-kit tokens
- Manual `:root` blocks with PE colors
- `@tailwind base; @tailwind components; @tailwind utilities;` (v3 syntax)
- `@config` directives
- `postcss-import` related imports

### Step 3: Verify postcss.config.mjs

Replace with exactly:

```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

Remove any:
- `postcss-import` (Tailwind handles imports)
- `autoprefixer` (Tailwind handles prefixing)
- `tailwindcss` (v3 plugin name — v4 uses `@tailwindcss/postcss`)
- `postcss-nested` (Tailwind uses Lightning CSS for nesting)

### Step 4: Delete stale config files

Remove if present:
- `tailwind.config.ts` / `tailwind.config.js` (v4 is CSS-first)
- `tailwind.config.cjs` / `tailwind.config.mjs`

### Step 5: Verify dependencies

```bash
# Required
bun add @policyengine/ui-kit
bun add -D @tailwindcss/postcss postcss

# Remove stale deps if present
bun remove tailwindcss-animate  # replaced by tw-animate-css (bundled in ui-kit)
bun remove postcss-import       # handled by @tailwindcss/postcss
bun remove autoprefixer         # handled by @tailwindcss/postcss
```

Note: `tailwindcss` itself should still be installed (it's a peer dep of `@tailwindcss/postcss`).

### Step 6: Clear caches and restart

```bash
rm -rf .next node_modules/.cache
bun dev
```

### Step 7: Verify

Open the app in a browser. Check that:
1. Page has the correct background color (white, `--background`)
2. Text is in Inter font
3. Teal brand colors are present
4. Layout utilities work (`flex`, `grid`, `p-4`, `gap-2`)
5. No Tailwind default blue/indigo colors leaking through

## If `@source` Scanning Fails

If ui-kit component styles are missing (components render but with wrong styling), the `@source` directive inside the ui-kit's CSS may not be reaching the consumer's build.

Add a manual fallback in `globals.css`:

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
@source "../node_modules/@policyengine/ui-kit/src";
```

For `bun link`'d packages, find the real path:

```bash
readlink -f node_modules/@policyengine/ui-kit
```

And use that absolute path or adjust the relative path accordingly.

## History of This Issue

The original problem: `tokens.css` in the ui-kit contained `@import "tailwindcss"`. This caused Tailwind's source detection to scan from the ui-kit's directory inside `node_modules` instead of the consumer's project. Design tokens loaded (because `@theme` blocks are processed regardless of scan directory), but utility classes for the consumer's components were not generated (because the scanner only found files inside the ui-kit package).

Multiple fix attempts failed:
- Adding `@source` directives in the consumer — path resolution was fragile
- Inlining all tokens in the consumer's CSS — user rejected (ui-kit should own styling)
- Removing `@import "tailwindcss"` from tokens.css but not adding it to the consumer — no Tailwind at all

The correct fix (confirmed by Tailwind maintainers and every major Tailwind-based library):
1. Remove `@import "tailwindcss"` from the library
2. Consumer writes `@import "tailwindcss"` first, then imports the library's theme
3. Library includes `@source` for its own components
