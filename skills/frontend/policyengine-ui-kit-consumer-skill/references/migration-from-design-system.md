# Migrating from @policyengine/design-system to @policyengine/ui-kit/legacy

Guide for migrating existing projects from the deprecated `@policyengine/design-system` package to `@policyengine/ui-kit/legacy`.

## Overview

`@policyengine/design-system` is deprecated. The canonical design system is now `@policyengine/ui-kit`.

For projects that need a drop-in replacement with minimal changes, ui-kit 0.8.0+ provides a `/legacy` subpath that mirrors the design-system API exactly.

## Quick Migration (Legacy Compatibility Mode)

This is a pure import-path rename with no behavioral changes.

### 1. Update package.json

```diff
  "dependencies": {
-   "@policyengine/design-system": "^x.x.x",
+   "@policyengine/ui-kit": "^0.8.0"
  }
```

### 2. Update source imports

Replace all design-system imports with ui-kit/legacy:

```diff
- import { Button } from '@policyengine/design-system/components';
+ import { Button } from '@policyengine/ui-kit/legacy/components';

- import { colors } from '@policyengine/design-system/tokens';
+ import { colors } from '@policyengine/ui-kit/legacy/tokens';
```

### 3. Handle TypeScript typedef quirk (if using tokens)

Due to a published 0.8.0 typedef quirk where `dist/legacy/tokens.js` shadows `dist/legacy/tokens/index.d.ts`, you must import tokens from the full path:

```diff
- import { colors, spacing, typography } from '@policyengine/ui-kit/legacy';
+ import { colors, spacing, typography } from '@policyengine/ui-kit/legacy/tokens';
```

This applies to:
- `colors`
- `spacing`
- `typography`

Component imports work normally from `/legacy`.

### 4. Update CSS imports (if importing tokens.css directly)

If your `globals.css` or other CSS files imported design-system's tokens.css:

```diff
- @import "../node_modules/@policyengine/design-system/dist/tokens.css";
+ /* Inline the --pe-* variables or migrate to ui-kit's theme.css */
```

**Important**: ui-kit's `theme.css` uses different variable names (shadcn-style: `--primary`, `--foreground`, etc.) instead of the old `--pe-color-*` / `--pe-font-*` aliases.

If you need the old variable names, inline them directly in your CSS:

```css
:root {
  /* Colors — primary (teal) */
  --pe-color-primary-50: #E6FFFA;
  --pe-color-primary-100: #B2F5EA;
  /* ... rest of tokens ... */
}
```

See the aspen-eitc-ctc migration (PolicyEngine/aspen-eitc-ctc#6) for a complete example of inlining the token set.

## When to Use /legacy vs Modern ui-kit

| Use `/legacy` if... | Migrate to modern ui-kit if... |
|---------------------|----------------------------------|
| Minimal changes required | Starting a new project |
| Tight deadline | Refactoring existing UI |
| App uses old token names (`--pe-*`) | App can adopt shadcn conventions |
| Importing design-system components directly | Want to use new ui-kit components |

## Full Migration Path (Recommended for New Work)

For new projects or major refactors, migrate to the modern ui-kit setup instead of using `/legacy`:

### 1. Install ui-kit

```bash
bun add @policyengine/ui-kit
bun add -D @tailwindcss/postcss postcss
```

### 2. Setup PostCSS

Create `postcss.config.mjs`:

```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

### 3. Setup globals.css

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

### 4. Update component imports

```diff
- import { Button } from '@policyengine/design-system/components';
+ import { Button } from '@policyengine/ui-kit';
```

### 5. Adopt shadcn-style CSS variables

Replace old `--pe-*` variables with shadcn conventions:

| Old (design-system) | New (ui-kit) |
|---------------------|--------------|
| `--pe-color-primary-500` | `--primary` |
| `--pe-color-text-primary` | `--foreground` |
| `--pe-color-bg-primary` | `--background` |
| `--pe-color-gray-200` | `--border` |

See `policyengine-ui-kit-consumer-skill` for full setup details.

## Troubleshooting

### "Module not found: @policyengine/ui-kit/legacy"

Ensure you're using ui-kit 0.8.0 or higher. The `/legacy` subpath was added in 0.8.0.

```bash
bun add @policyengine/ui-kit@^0.8.0
```

### "Cannot find module '@policyengine/ui-kit/legacy/tokens'"

This is the correct import path due to the typedef quirk. Use the full path:

```ts
import { colors } from '@policyengine/ui-kit/legacy/tokens';
```

### "Colors work but layout/spacing broken"

If you migrated token imports but components still reference old design-system paths, update all component imports to use `/legacy`:

```bash
# Find all design-system imports
grep -r "@policyengine/design-system" --include="*.tsx" --include="*.ts"
```

## Examples

### Before (design-system)

```tsx
import { Button } from '@policyengine/design-system/components';
import { colors } from '@policyengine/design-system/tokens';

export function MyComponent() {
  return <Button style={{ color: colors.primary[500] }}>Click</Button>;
}
```

### After (ui-kit/legacy)

```tsx
import { Button } from '@policyengine/ui-kit/legacy/components';
import { colors } from '@policyengine/ui-kit/legacy/tokens';

export function MyComponent() {
  return <Button style={{ color: colors.primary[500] }}>Click</Button>;
}
```

## Related Skills

- `policyengine-ui-kit-consumer-skill` — Full ui-kit setup guide
- `policyengine-design-skill` — Complete design token reference
- `policyengine-tailwind-shadcn-skill` — Understanding @theme mechanics

## References

- aspen-eitc-ctc migration: PolicyEngine/aspen-eitc-ctc#6
- ui-kit package: https://github.com/PolicyEngine/policyengine-ui-kit
