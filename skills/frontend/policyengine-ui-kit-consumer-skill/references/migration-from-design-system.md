# Migrating from @policyengine/design-system to @policyengine/ui-kit

Guide for migrating repositories from the deprecated `@policyengine/design-system` package to `@policyengine/ui-kit/legacy`.

## Why Migrate

- `@policyengine/design-system` is deprecated and being phased out
- `@policyengine/ui-kit` is the canonical PolicyEngine design system going forward
- The `/legacy` subpath provides a drop-in replacement with identical API

## Migration Steps

### 1. Update package.json

Replace the design-system dependency with ui-kit:

```bash
# Remove old package
bun remove @policyengine/design-system

# Add new package
bun add @policyengine/ui-kit
```

### 2. Update imports

Replace all imports from `@policyengine/design-system` with `@policyengine/ui-kit/legacy`.

This is a pure import path change - no code changes needed:

```tsx
// Before
import { colors, spacing, typography } from '@policyengine/design-system';

// After
import { colors, spacing, typography } from '@policyengine/ui-kit/legacy';
```

### 3. Search and replace

Use find-and-replace across your codebase:

```bash
# Find all occurrences
grep -r "@policyengine/design-system" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx"

# Or use your editor's find-and-replace:
# Find: @policyengine/design-system
# Replace: @policyengine/ui-kit/legacy
```

### 4. Verify the build

```bash
bun run build
```

The migration should be transparent - no type errors, no runtime changes.

## Why `/legacy`?

The `/legacy` subpath in ui-kit mirrors the old design-system API exactly, allowing for a seamless migration without code changes.

Once migrated to `/legacy`, you can optionally migrate to the modern ui-kit patterns (Tailwind v4, CSS custom properties) when ready. See the main `policyengine-ui-kit-consumer-skill` for modern setup.

## What Stays the Same

After migration to `/legacy`:
- All exported values (colors, spacing, typography, etc.) remain identical
- TypeScript types remain compatible
- Runtime behavior is unchanged
- This is purely a dependency replacement

## Common Scenarios

### Monorepo with local design-system package

If your repo has `packages/design-system/` as a local package:

1. Keep the local package if needed for legacy code
2. Migrate new code to `@policyengine/ui-kit/legacy`
3. Eventually remove the local package when all code is migrated

### Re-export layers

If you have re-export convenience layers like:

```tsx
// app/src/designTokens/index.ts
export * from '@policyengine/design-system';
```

Update them to:

```tsx
// app/src/designTokens/index.ts
export * from '@policyengine/ui-kit/legacy';
```

This allows the rest of your codebase to keep using the convenience import (`@/designTokens`).

## Next Steps

After migrating to `/legacy`, consider:

1. **Stay on `/legacy`** - Perfectly fine for stable codebases. No urgency to migrate.
2. **Migrate to modern ui-kit** - Use Tailwind v4 classes and CSS custom properties. See `policyengine-ui-kit-consumer-skill` for setup.

## Related Skills

- `policyengine-ui-kit-consumer-skill` — Modern ui-kit setup with Tailwind v4
- `policyengine-design-skill` — Token reference and usage guidelines
