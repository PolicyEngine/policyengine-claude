# Migrating from @policyengine/design-system to @policyengine/ui-kit/legacy

Quick reference for migrating legacy repositories from the deprecated `@policyengine/design-system` package to `@policyengine/ui-kit/legacy`.

## Background

- `@policyengine/design-system` is deprecated and being phased out
- `@policyengine/ui-kit/legacy` provides the same API (source files copied verbatim from design-system)
- This is a pure import-path rename with no symbol changes or value changes
- For modern ui-kit setup (non-legacy), see the main `SKILL.md` file

## Migration Steps

### 1. Update package.json

Replace the design-system dependency:

```diff
  "dependencies": {
-   "@policyengine/design-system": "^1.0.0",
+   "@policyengine/ui-kit": "^0.8.0"
  }
```

### 2. Update all import statements

Find and replace all imports:

```diff
- import { ... } from "@policyengine/design-system"
+ import { ... } from "@policyengine/ui-kit/legacy"

- import { ... } from "@policyengine/design-system/tokens"
+ import { ... } from "@policyengine/ui-kit/legacy/tokens"

- import { ... } from "@policyengine/design-system/dist/..."
+ import { ... } from "@policyengine/ui-kit/legacy/dist/..."
```

Search patterns to find all occurrences:
```bash
grep -r "@policyengine/design-system" src/
```

### 3. Switch to bun.lock (PolicyEngine standard)

If the project is using `package-lock.json`, migrate to `bun.lock`:

```bash
rm package-lock.json
bun install
```

Per `PolicyEngine/CLAUDE.md`, bun is the standard package manager for PolicyEngine projects.

### 4. Verify the build

```bash
bun run build
```

The build should succeed with no changes to functionality or styling.

## What Changes

- Import paths: `@policyengine/design-system` → `@policyengine/ui-kit/legacy`
- Package dependency in `package.json`
- Lockfile (if switching to bun)

## What Does NOT Change

- Component APIs (same props, same methods)
- CSS/styling output (identical tokens)
- Symbol names (same exports)
- Functionality (source files are identical)

## Common Files to Update

Typical files that import from design-system:

- Theme configuration files (e.g., `src/policyengineTheme.js`)
- Component files that import design tokens
- Layout files using design-system components
- Any file with `import ... from "@policyengine/design-system"`

## Testing

After migration:

1. ✅ Build succeeds (`bun run build`)
2. ✅ Dev server runs (`bun dev`)
3. ✅ No console errors about missing modules
4. ✅ Visual appearance unchanged in deployed preview
5. ✅ No runtime errors when interacting with the app

## Future Migration to Modern ui-kit

The `/legacy` subpath is for backward compatibility. To eventually migrate to the modern ui-kit setup:

1. See the main `SKILL.md` for full modern setup instructions
2. Modern setup uses `@import "@policyengine/ui-kit/theme.css"` in CSS
3. Modern setup provides shadcn/ui components and Tailwind v4 integration
4. This is a larger migration that changes component structure and styling approach
5. Not all repos need to migrate to modern setup — `/legacy` is fully supported

## Example PR

See PolicyEngine/senior-state-tax-breaks#1 for a complete migration example.
