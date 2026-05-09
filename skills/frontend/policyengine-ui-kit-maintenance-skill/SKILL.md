---
name: policyengine-ui-kit-maintenance
description: |
  Use this skill when working on the @policyengine/ui-kit package itself (not consumers).
  Covers legacy compatibility shims, multi-entry TypeScript builds, package.json exports,
  and deprecation strategies for API migrations.
  Triggers: "ui-kit package", "legacy shim", "package exports", "deprecate ui-kit",
  "multi-entry build", "vite library", "backward compatibility ui-kit"
---

# Maintaining @policyengine/ui-kit

Patterns for maintaining the ui-kit package, creating compatibility layers, and managing migrations.

## Legacy Compatibility Shim Pattern

When deprecating an old API surface in favor of a new one, create a `/legacy` compatibility layer to enable zero-code migration for consumers.

### Structure

```
src/
  legacy/
    index.ts              ← Main exports (deprecated, re-exports old API)
    tokens/
      index.ts
      colors.ts
      typography.ts
      spacing.ts
    charts/
      index.ts
tests/
  legacy/                 ← Port original tests to verify behavioral parity
    colors.test.ts
    typography.test.ts
    spacing.test.ts
    charts.test.ts
```

### Implementation Checklist

1. **Copy source verbatim**
   - Copy deprecated files from the old package/location
   - Do NOT refactor or "improve" the code
   - Goal is byte-for-byte API compatibility

2. **Add deprecation JSDoc**
   ```typescript
   /**
    * @deprecated Use `palette` from '@policyengine/ui-kit' instead.
    * This export mirrors the old @policyengine/design-system/tokens/colors API.
    * Migration: import { BLUE_PRIMARY } from '@policyengine/ui-kit/legacy/tokens/colors'
    *         →  import { palette } from '@policyengine/ui-kit'
    *            const BLUE_PRIMARY = palette.teal[500]
    */
   export const BLUE_PRIMARY = "#319795";
   ```

3. **Port all tests**
   - Copy test files from the deprecated package
   - Update imports to use `/legacy` paths
   - Ensure all tests pass to verify behavioral parity
   - Any test failures indicate breaking changes

4. **Update package.json exports**
   ```json
   {
     "exports": {
       "./legacy": {
         "types": "./dist/legacy/index.d.ts",
         "import": "./dist/legacy/index.js",
         "require": "./dist/legacy/index.cjs"
       },
       "./legacy/tokens": {
         "types": "./dist/legacy/tokens/index.d.ts",
         "import": "./dist/legacy/tokens/index.js",
         "require": "./dist/legacy/tokens/index.cjs"
       },
       "./legacy/tokens/colors": {
         "types": "./dist/legacy/tokens/colors.d.ts",
         "import": "./dist/legacy/tokens/colors.js",
         "require": "./dist/legacy/tokens/colors.cjs"
       }
     }
   }
   ```

5. **Configure multi-entry build**
   - See "Multi-Entry TypeScript Build" section below

6. **Document migration path**
   - Add migration table to changelog
   - Include sed-replace examples for bulk migration

### Migration Documentation Template

```markdown
## Migration from @old-package to @new-package/legacy

Pure import-path rename. No source code changes required.

| Before | After |
|--------|-------|
| `@old-package` | `@new-package/legacy` |
| `@old-package/tokens` | `@new-package/legacy/tokens` |
| `@old-package/tokens/colors` | `@new-package/legacy/tokens/colors` |

### Bulk migration

sed -i '' 's|@old-package|@new-package/legacy|g' **/*.{ts,tsx,js,jsx}
```

## Multi-Entry TypeScript Build

Building a TypeScript package with multiple entry points (subpath exports) using Vite.

### vite.config.ts Pattern

```typescript
import { defineConfig } from 'vite'
import { resolve } from 'path'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [
    dts({
      tsconfigPath: './tsconfig.json',
      rollupTypes: true,
    }),
  ],
  build: {
    lib: {
      entry: {
        // Main entry
        index: resolve(__dirname, 'src/index.ts'),

        // Legacy entries
        'legacy/index': resolve(__dirname, 'src/legacy/index.ts'),
        'legacy/tokens/index': resolve(__dirname, 'src/legacy/tokens/index.ts'),
        'legacy/tokens/colors': resolve(__dirname, 'src/legacy/tokens/colors.ts'),
        'legacy/charts/index': resolve(__dirname, 'src/legacy/charts/index.ts'),
      },
      formats: ['es', 'cjs'],
      fileName: (format, entryName) => {
        const ext = format === 'es' ? 'js' : 'cjs'
        return `${entryName}.${ext}`
      },
    },
    rollupOptions: {
      external: ['react', 'react-dom'],
    },
  },
})
```

### Key Points

1. **Entry object**: Maps output paths to source files
   - Keys become directory structure in `dist/`
   - `'legacy/tokens/colors'` → `dist/legacy/tokens/colors.{js,cjs,d.ts}`

2. **fileName function**: Controls extension based on format
   - ESM: `.js`
   - CommonJS: `.cjs`
   - Types: `.d.ts` (handled by vite-plugin-dts)

3. **External dependencies**: List peer dependencies to avoid bundling
   - React, React DOM should always be external
   - Any other packages consumers will install

4. **Type generation**: `vite-plugin-dts` with `rollupTypes: true`
   - Generates `.d.ts` for each entry
   - Rolls up type dependencies

### Verification Steps

After build, verify structure:

```bash
bun run build
ls -R dist/

# Expected:
# dist/
#   index.js
#   index.cjs
#   index.d.ts
#   legacy/
#     index.js
#     index.cjs
#     index.d.ts
#     tokens/
#       index.js
#       index.cjs
#       index.d.ts
#       colors.js
#       colors.cjs
#       colors.d.ts
```

Test imports in consuming project:

```typescript
import { Button } from '@policyengine/ui-kit'                    // ✓
import { palette } from '@policyengine/ui-kit/legacy'            // ✓
import { BLUE_PRIMARY } from '@policyengine/ui-kit/legacy/tokens/colors' // ✓
```

## Deprecation Strategy

### When to Use Legacy Shims

Use legacy compatibility shims when:
- 5+ repositories depend on the old API
- Migration requires import path changes across many files
- Old API is stable and well-tested
- New API is semantically different (not just renamed)

### When to Use Direct Breaking Changes

Use direct breaking changes (major version bump) when:
- Fewer than 5 consumers
- Old API has known bugs or security issues
- Migration is simple find-replace
- Maintaining two APIs creates confusion

### Deprecation Timeline

1. **Release N (current)**
   - Ship `/legacy` shim alongside new API
   - Mark all legacy exports with `@deprecated` JSDoc
   - Document migration path
   - Version: 0.8.0 (minor bump, backward compatible)

2. **Release N+1 (migration period)**
   - Keep legacy shim
   - Update all first-party consumers to new API
   - Log deprecation warnings if possible
   - Version: 0.9.0

3. **Release N+2 (removal)**
   - Remove `/legacy` exports
   - Major version bump
   - Version: 1.0.0

## Testing Compatibility Layers

### Port Original Tests

When creating a `/legacy` shim, port ALL tests from the original package:

```typescript
// tests/legacy/colors.test.ts
import { describe, test, expect } from 'vitest'
import {
  BLUE_PRIMARY,
  BLUE_LIGHT,
  // ... all 50+ color exports
} from '../src/legacy/tokens/colors'

describe('Legacy color tokens', () => {
  test('BLUE_PRIMARY matches design-system value', () => {
    expect(BLUE_PRIMARY).toBe('#319795')
  })

  // ... port all 143 original tests
})
```

### Why Port Tests?

1. **Behavioral parity**: Ensures shim truly mirrors old API
2. **Regression detection**: Any test failure means breaking change
3. **Refactor confidence**: Safe to refactor internals if tests pass
4. **Documentation**: Tests document expected behavior

### Test Organization

```
tests/
  legacy/          ← Tests for /legacy exports
    colors.test.ts
    typography.test.ts
    spacing.test.ts
    charts.test.ts

  tokens.test.ts   ← Tests for new API
  palette.test.ts
  theme.test.ts
```

Keep legacy tests separate so they can be deleted together when shim is removed.

## Package.json Best Practices

### Exports Field

Always use conditional exports for TypeScript packages:

```json
{
  "exports": {
    "./legacy/tokens/colors": {
      "types": "./dist/legacy/tokens/colors.d.ts",
      "import": "./dist/legacy/tokens/colors.js",
      "require": "./dist/legacy/tokens/colors.cjs"
    }
  }
}
```

Order matters: `types` first, then `import`, then `require`.

### Files Field

Limit published files:

```json
{
  "files": [
    "dist",
    "README.md",
    "LICENSE"
  ]
}
```

Do NOT publish `src/`, `tests/`, or config files.

## Related Skills

- `policyengine-ui-kit-consumer-skill` — How consumers import and use ui-kit
- `policyengine-design-skill` — Design token values and usage guidelines
- `policyengine-tailwind-shadcn-skill` — Theme authoring for ui-kit itself
