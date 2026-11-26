# Migrating from @policyengine/design-system to @policyengine/ui-kit/legacy

Guide for migrating repositories that use the deprecated `@policyengine/design-system` package to the modern `@policyengine/ui-kit/legacy` compatibility layer.

## Context

`@policyengine/design-system` was a standalone NPM package containing design tokens and components. It has been deprecated in favor of `@policyengine/ui-kit`, which is the canonical design system per `PolicyEngine/CLAUDE.md`.

For repositories not yet ready to adopt Tailwind v4 and the full ui-kit setup, ui-kit 0.8.0+ provides a `/legacy` subpath that mirrors the old design-system API exactly.

## When to Use `/legacy` vs Full ui-kit

| Use `/legacy` if... | Use full ui-kit if... |
|---------------------|----------------------|
| Using Mantine, Ant Design, or other non-Tailwind UI framework | Building with Tailwind v4 |
| Need minimal changes (pure import-path swap) | Starting a new project or doing a major refactor |
| Build config uses Webpack, Rollup, or other bundlers | Using Next.js or Vite with PostCSS |
| Not ready to adopt Tailwind v4 yet | Want access to shadcn/ui components and utilities |

## Migration Steps

### 1. Update package.json

Replace the design-system dependency:

```diff
{
  "dependencies": {
-   "@policyengine/design-system": "^X.Y.Z",
+   "@policyengine/ui-kit": "^0.8.0"
  }
}
```

Run:
```bash
bun install
```

### 2. Update JavaScript/TypeScript imports

Find and replace all imports. The `/legacy` subpath provides the exact same API:

```diff
- import { colors } from "@policyengine/design-system";
+ import { colors } from "@policyengine/ui-kit/legacy";

- import * as tokens from "@policyengine/design-system";
+ import * as tokens from "@policyengine/ui-kit/legacy";
```

For large codebases, use a bulk find-replace:

```bash
# Preview changes
grep -r "@policyengine/design-system" src/

# Replace in all files (macOS/BSD sed)
find src/ -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  -exec sed -i '' 's/@policyengine\/design-system/@policyengine\/ui-kit\/legacy/g' {} +

# Replace in all files (GNU sed / Linux)
find src/ -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  -exec sed -i 's/@policyengine\/design-system/@policyengine\/ui-kit\/legacy/g' {} +
```

### 3. Update CSS imports (if applicable)

If importing CSS tokens directly:

```diff
- @import "@policyengine/design-system/tokens.css";
+ @import "@policyengine/ui-kit/legacy/tokens.css";
```

### 4. Update CDN links (if applicable)

If using CDN for browser-only projects:

```diff
- <link rel="stylesheet" href="https://unpkg.com/@policyengine/design-system/tokens.css">
+ <link rel="stylesheet" href="https://unpkg.com/@policyengine/ui-kit@0.8.0/legacy/tokens.css">
```

### 5. Verify and test

After migration:

```bash
# Clean build
rm -rf node_modules/.cache dist build .next
bun install

# Run build
bun run build

# Run tests
bun test
```

Check that:
- All imports resolve correctly
- Design tokens (colors, spacing, typography) render as before
- No runtime errors related to missing exports
- Build output size is similar (ui-kit legacy bundle is comparable to old design-system)

## What `/legacy` Exports

The `/legacy` subpath provides:

- `colors` object (all brand colors, semantic colors, chart colors)
- `spacing` tokens
- `typography` tokens (font family, sizes, weights)
- `breakpoints`
- `style` object (any Mantine theme extensions from the old package)

It does NOT include:
- Tailwind utility classes
- shadcn/ui components
- `@theme` blocks
- PostCSS dependencies

If you need those, migrate to the full ui-kit setup (see `policyengine-ui-kit-consumer-skill`).

## Comparison

| Aspect | Old (`design-system`) | New (`ui-kit/legacy`) |
|--------|----------------------|----------------------|
| Package name | `@policyengine/design-system` | `@policyengine/ui-kit` |
| Import path | `@policyengine/design-system` | `@policyengine/ui-kit/legacy` |
| API surface | Colors, spacing, typography | **Identical** |
| Bundle size | ~15KB | ~15KB (same) |
| Maintenance | Deprecated (no updates) | Maintained (synced with ui-kit tokens) |
| Tailwind required | No | No (legacy is standalone) |
| TypeScript types | Yes | Yes (identical) |

## Migration Checklist

- [ ] Update `package.json` dependencies
- [ ] Run `bun install`
- [ ] Replace all `@policyengine/design-system` imports with `@policyengine/ui-kit/legacy`
- [ ] Update any CSS imports or CDN links
- [ ] Clear build caches
- [ ] Run build successfully
- [ ] Run tests successfully
- [ ] Visual regression check (if applicable)
- [ ] Commit with message: "Migrate from @policyengine/design-system to @policyengine/ui-kit/legacy"

## Future Path: Full ui-kit Migration

Once ready to adopt Tailwind v4, migrate from `/legacy` to the full ui-kit:

1. Replace Mantine/Ant Design with Tailwind utilities
2. Set up PostCSS with `@tailwindcss/postcss`
3. Create `globals.css` with `@import "tailwindcss"` and `@import "@policyengine/ui-kit/theme.css"`
4. Replace `/legacy` imports with Tailwind classes or shadcn/ui components
5. Remove `/legacy` subpath from all imports

See `policyengine-ui-kit-consumer-skill` for the full setup guide.

## Troubleshooting

### Import errors after migration

**Error:** `Module not found: Can't resolve '@policyengine/ui-kit/legacy'`

**Fix:** Ensure you're using ui-kit 0.8.0 or later:
```bash
bun add @policyengine/ui-kit@latest
```

### TypeScript types not found

**Error:** `Could not find a declaration file for module '@policyengine/ui-kit/legacy'`

**Fix:** The `/legacy` subpath has types. Check:
1. `node_modules/@policyengine/ui-kit/legacy/index.d.ts` exists
2. Your TypeScript `moduleResolution` is set to `"bundler"` or `"node16"` (not `"node"`)

### Colors render differently

**Cause:** Unlikely, but if tokens differ, the ui-kit version may have updated values.

**Fix:** Check the changelog. The `/legacy` API matches the last design-system version, but token values themselves may evolve. If you need frozen values, pin the ui-kit version:
```json
{
  "dependencies": {
    "@policyengine/ui-kit": "0.8.0"
  }
}
```

### Build size increased significantly

**Cause:** Accidentally importing the full ui-kit instead of `/legacy`.

**Fix:** Verify all imports end with `/legacy`:
```bash
grep -r "from ['\"]@policyengine/ui-kit['\"]" src/
```

Should return no results. All imports should be:
```typescript
import { colors } from "@policyengine/ui-kit/legacy";
```

Not:
```typescript
import { colors } from "@policyengine/ui-kit"; // WRONG - imports full Tailwind setup
```

## Related Documentation

- `policyengine-ui-kit-consumer-skill` — Full ui-kit setup with Tailwind v4
- `policyengine-design-skill` — Token reference and usage guidelines
- `migration-from-broken-setup.md` — Fixing incorrect Tailwind + ui-kit setups
