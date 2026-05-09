# Migrating from @policyengine/design-system to @policyengine/ui-kit

Guide for migrating projects that use the deprecated `@policyengine/design-system` package to the canonical `@policyengine/ui-kit`.

## Background

`@policyengine/design-system` is deprecated. All PolicyEngine projects should use `@policyengine/ui-kit` as the canonical design system (per `PolicyEngine/CLAUDE.md`).

For projects that need a gradual migration, ui-kit 0.8.0+ provides a `/legacy` subpath that mirrors the design-system API exactly.

## Migration Paths

There are two migration strategies:

### Path A: Legacy Subpath (Quick Migration)

Use this for projects that need immediate migration with minimal changes.

**What changes:**
- Import paths only (source imports and CSS imports)
- Package dependency in `package.json`
- No code changes needed

**Migration steps:**

1. **Update package.json**
   ```diff
   - "@policyengine/design-system": "^X.Y.Z"
   + "@policyengine/ui-kit": "^0.8.0"
   ```

2. **Update source imports**
   ```diff
   - import { colors } from '@policyengine/design-system/tokens/colors'
   + import { colors } from '@policyengine/ui-kit/legacy/tokens/colors'
   ```

3. **Update CSS imports**

   The legacy subpath does NOT re-export the CSS variables file. You need to inline the CSS custom properties that your app uses.

   **Before:**
   ```css
   @import "@policyengine/design-system/tokens.css";
   ```

   **After:**
   ```css
   /* Inline the relevant CSS custom properties */
   :root {
     --pe-color-teal-50: #e6fffa;
     --pe-color-teal-100: #b2f5ea;
     --pe-color-teal-500: #319795;
     /* ... other variables your app uses ... */
   }
   ```

   Check what variables your app actually uses (grep for `var(--pe-`) and only inline those.

4. **Update lockfile** (if switching to bun)
   ```bash
   rm package-lock.json
   bun install
   ```

5. **Test**
   ```bash
   bun install
   bun run build
   ```

**Why inline CSS?**

`@policyengine/ui-kit/legacy` provides the JavaScript exports (color objects, spacing, etc.) but not the CSS file. This is because:
- ui-kit uses the new `theme.css` with shadcn-style variable names (`--primary`, `--background`)
- The old `--pe-color-*` naming is legacy and shouldn't be in the main theme
- Inlining forces you to be explicit about which tokens you depend on

### Path B: Full Modern Migration (Recommended for New Work)

Use this for new projects or when doing significant refactoring.

**What changes:**
- Import paths become `@policyengine/ui-kit/theme.css`
- Variable names change to shadcn-style (`--primary` instead of `--pe-color-teal-500`)
- Setup requires Tailwind v4 + PostCSS config

**Migration steps:**

See the main `policyengine-ui-kit-consumer-skill` SKILL.md for full setup instructions.

**Quick summary:**
1. Install: `bun add @policyengine/ui-kit` + `bun add -D @tailwindcss/postcss postcss`
2. Create `postcss.config.mjs` with `@tailwindcss/postcss`
3. Create `globals.css`:
   ```css
   @import "tailwindcss";
   @import "@policyengine/ui-kit/theme.css";
   ```
4. Use Tailwind classes (`bg-primary`, `text-teal-500`) instead of CSS vars

## When to Use Which Path

| Scenario | Recommended Path | Reason |
|----------|-----------------|--------|
| Standalone tool with minimal CSS | Legacy subpath | Quick migration, minimal changes |
| Tool in active development | Modern migration | Future-proof, Tailwind utilities |
| Quick fix needed | Legacy subpath | Unblocks immediately |
| New greenfield project | Modern migration | Start with best practices |
| Large refactor planned | Modern migration | Do it right once |

## Common Issues

### Issue: CSS variables not working after migration

**Symptom:** `var(--pe-color-teal-500)` returns nothing

**Fix:** The legacy subpath doesn't export the CSS file. You must inline the variables you use:

```css
:root {
  --pe-color-teal-500: #319795;
  /* ... other vars ... */
}
```

### Issue: Module not found '@policyengine/ui-kit/legacy'

**Fix:** Ensure you're using ui-kit 0.8.0 or later:

```bash
bun add @policyengine/ui-kit@^0.8.0
```

### Issue: Import works but types are wrong

**Fix:** The legacy subpath preserves the exact types from design-system. If types are wrong, check:
1. TypeScript is using the right version (`bun install`)
2. Editor is using workspace TypeScript (Cmd+Shift+P > "Select TypeScript Version")

## Examples

### Example 1: uk-land-value-tax (Standalone Dashboard)

**Before:**
```tsx
// src/components/BaselineTab.jsx
import { colors } from '@policyengine/design-system/tokens/colors';
```

```css
/* app/globals.css */
@import "@policyengine/design-system/tokens.css";
```

```json
// package.json
{
  "dependencies": {
    "@policyengine/design-system": "^1.0.0"
  }
}
```

**After (legacy path):**
```tsx
// src/components/BaselineTab.jsx
import { colors } from '@policyengine/ui-kit/legacy/tokens/colors';
```

```css
/* app/globals.css */
:root {
  --pe-color-teal-50: #e6fffa;
  --pe-color-teal-100: #b2f5ea;
  --pe-color-teal-200: #81e6d9;
  --pe-color-teal-300: #4fd1c5;
  --pe-color-teal-400: #38b2ac;
  --pe-color-teal-500: #319795;
  --pe-color-teal-600: #2c7a7b;
  --pe-color-teal-700: #285e61;
  --pe-color-teal-800: #234e52;
  --pe-color-teal-900: #1d4044;

  --pe-color-gray-50: #f7fafc;
  --pe-color-gray-100: #edf2f7;
  --pe-color-gray-200: #e2e8f0;
  --pe-color-gray-300: #cbd5e0;
  --pe-color-gray-400: #a0aec0;
  --pe-color-gray-500: #718096;
  --pe-color-gray-600: #4a5568;
  --pe-color-gray-700: #2d3748;
  --pe-color-gray-800: #1a202c;
  --pe-color-gray-900: #171923;

  --pe-color-blue-50: #ebf8ff;
  --pe-color-blue-100: #bee3f8;
  --pe-color-blue-200: #90cdf4;
  --pe-color-blue-300: #63b3ed;
  --pe-color-blue-400: #4299e1;
  --pe-color-blue-500: #3182ce;
  --pe-color-blue-600: #2b6cb0;
  --pe-color-blue-700: #2c5282;
  --pe-color-blue-800: #2a4365;
  --pe-color-blue-900: #1a365d;

  --pe-font-family-sans: Inter, system-ui, -apple-system, sans-serif;
  --pe-font-size-xs: 0.75rem;
  --pe-font-size-sm: 0.875rem;
  --pe-font-size-base: 1rem;
  --pe-font-size-lg: 1.125rem;
  --pe-font-size-xl: 1.25rem;
  --pe-font-size-2xl: 1.5rem;
  --pe-font-size-3xl: 1.875rem;
  --pe-font-size-4xl: 2.25rem;
}
```

```json
// package.json
{
  "dependencies": {
    "@policyengine/ui-kit": "^0.8.0"
  }
}
```

## Related Skills

- `policyengine-ui-kit-consumer-skill` — Full modern ui-kit setup
- `policyengine-design-skill` — Design token reference
- `policyengine-tailwind-shadcn-skill` — Tailwind v4 mechanics
