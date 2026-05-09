# Consumer-Types Testing Pattern

Pattern for catching bundler resolution issues in design system packages before they reach consumers.

## The Problem

When a package ships both `.js` and `.d.ts` files with matching names at different directory levels, bundler-mode TypeScript resolution can fail silently:

```
dist/
  tokens.js           ← shadows the directory below in some resolvers
  tokens/
    index.d.ts        ← unreachable from consumers using moduleResolution: "bundler"
```

This works fine in the package's own tests (using local source) but breaks for all consumers. The failure mode is silent — no build errors in the package itself.

## The Solution: Consumer-Types Harness

Create a test that mimics how external consumers see the package:

### 1. Fixture that imports as a consumer would

**`tests/consumer-types/fixture.ts`**

```typescript
// Import from the built artifacts exactly as a consumer would
import {
  palette,
  rootColorsLight,
  rootColorsDark,
  // ... representative slice of all exports
} from '@policyengine/ui-kit'

import {
  colors,
  spacing,
  // ... legacy shim exports
} from '@policyengine/ui-kit/legacy'

import { DashboardShell } from '@policyengine/ui-kit/dashboard'
import { InputPanel } from '@policyengine/ui-kit/panels'
// ... per-feature subpath exports

// Type-only check — no runtime needed
export type Exports = {
  palette: typeof palette
  colors: typeof colors
  DashboardShell: typeof DashboardShell
  // ...
}
```

### 2. Consumer-like tsconfig

**`tests/consumer-types/tsconfig.json`**

```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "paths": {
      "@policyengine/ui-kit": ["../../dist/index.d.ts"],
      "@policyengine/ui-kit/*": ["../../dist/*/index.d.ts"]
    },
    "skipLibCheck": false,
    "noEmit": true
  },
  "include": ["fixture.ts"]
}
```

Key points:
- `moduleResolution: "bundler"` matches most consumer setups (Next.js, Vite)
- `paths` points to `dist/` (the built artifacts), NOT `src/`
- `skipLibCheck: false` ensures the package's own types are checked
- `noEmit: true` — only type-checking, no output

### 3. Test that spawns tsc

**`tests/consumer-types/typecheck.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import { spawnSync } from 'child_process'
import { existsSync } from 'fs'
import path from 'path'

describe('consumer-types harness', () => {
  it('type-checks successfully as an external consumer', () => {
    const distIndex = path.resolve(__dirname, '../../dist/index.d.ts')

    if (!existsSync(distIndex)) {
      console.warn('dist/ not found — skipping consumer-types check')
      console.warn('Run `bun run build` before `bun run test` to enable this check')
      return // skip without failing
    }

    const result = spawnSync(
      'tsc',
      ['--noEmit', '--project', 'tests/consumer-types/tsconfig.json'],
      { encoding: 'utf-8', cwd: path.resolve(__dirname, '../..') }
    )

    if (result.status !== 0) {
      console.error('Consumer-types check failed:')
      console.error(result.stdout)
      console.error(result.stderr)
    }

    expect(result.status).toBe(0)
  })
})
```

Key points:
- Spawns `tsc --noEmit` against the consumer tsconfig
- Gracefully skips if `dist/` doesn't exist (with actionable message)
- Fails loudly with full tsc output on error

### 4. Update CI workflow

Ensure the build happens before tests:

```yaml
- name: Install dependencies
  run: bun install

- name: Build package
  run: bun run build

- name: Run tests
  run: bun run test
```

Without this order, the harness skips in CI (no `dist/`). The skip message makes the fix obvious.

## What This Catches

1. **Shadowing bugs** — `dist/tokens.js` masking `dist/tokens/index.d.ts`
2. **Missing subpath exports** — `package.json` exports map incomplete
3. **Broken type re-exports** — `export type { Foo } from './internal'` where internal types aren't emitted
4. **Path mapping issues** — tsconfig `paths` that work locally but break for consumers

## When to Use This Pattern

Use for any package that:
- Ships `.d.ts` files generated from source
- Has subpath exports (`/legacy`, `/dashboard`, etc.)
- Is consumed by bundler-mode TypeScript projects (Next.js, Vite, etc.)
- Has had bundler resolution issues in the past

Do NOT use for:
- Pure runtime packages (no TypeScript)
- Packages consumed only via direct source imports
- Packages with a single flat export (no subdirectories)

## Maintenance

As you add exports:
1. Add representative imports to `fixture.ts`
2. No need to import everything — one symbol per subpath is sufficient
3. Update the type-only `Exports` type to ensure the imports are actually used

As you add subpath exports:
1. Add the path mapping to `consumer-types/tsconfig.json`
2. Add an import to `fixture.ts`

## Example From policyengine-ui-kit

From PR #31 (0.8.1):

- **36 main-entry symbols** imported (`palette`, `spacing`, `DashboardShell`, etc.)
- **4 legacy subpath symbols** imported (`colors`, `breakpoints`, etc.)
- **3 per-feature subpath symbols** imported (one from each of `dashboard`, `panels`, `charts`)
- **Caught** the `dist/tokens.js`-shadows-`dist/tokens/index.d.ts` issue that broke 36 consumer PRs

Runs in ~400ms, fails fast with actionable error messages.
