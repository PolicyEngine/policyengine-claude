# Canonical Stack Migration

Guide for upgrading PolicyEngine frontend repositories to the canonical Next.js 16 + Tailwind 4 + ui-kit 0.9 stack.

## What is the Canonical Stack?

As of 2026, PolicyEngine's standard frontend stack for new and upgraded projects is:

- **Next.js**: `^16.2.6` (App Router)
- **React/React-DOM**: `^19.2.0`
- **Tailwind CSS**: v4 (via `@tailwindcss/postcss`)
- **UI Kit**: `@policyengine/ui-kit` `^0.9.0`

This replaces older stacks that used:
- Next.js 14.x or 15.x
- React 18.x
- Tailwind CSS v3 (with `tailwind.config.ts`)
- `@policyengine/design-system` 0.3.x

## When You'll Encounter This

You may see PRs labeled "Phase 2F batch sweep" or similar that upgrade multiple repositories simultaneously. These are coordinated migrations across the PolicyEngine ecosystem to standardize the frontend stack.

## Migration Checklist

When upgrading a repo to the canonical stack, follow this order:

### 1. Update package.json dependencies

```json
{
  "dependencies": {
    "next": "^16.2.6",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "@policyengine/ui-kit": "^0.9.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "latest",
    "postcss": "latest"
  }
}
```

**Remove** if present:
- `@policyengine/design-system`
- `tailwindcss` (the package itself - v4 uses `@tailwindcss/postcss`)
- `tailwindcss-animate` (bundled in ui-kit)
- `postcss-import`
- `autoprefixer`

### 2. Delete deprecated config files

```bash
rm -f tailwind.config.ts tailwind.config.js tailwind.config.mjs
```

Tailwind v4 uses CSS-first configuration via `@theme` blocks, not JavaScript config.

### 3. Update postcss.config.mjs

Replace entire file with:

```js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

### 4. Update globals.css

Replace with exactly:

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

Remove:
- `@tailwind base; @tailwind components; @tailwind utilities;` (v3 syntax)
- Manual `@theme` blocks
- Manual `:root` color definitions
- Additional `@import "tailwindcss"` lines (only one needed)

### 5. Update imports from design-system to ui-kit

**Option A: Quick migration (backwards-compat)**

Use the legacy shim for a drop-in replacement:

```ts
// Before
import { Button } from "@policyengine/design-system";

// After
import { Button } from "@policyengine/ui-kit/legacy";
```

**Option B: Full migration (recommended for new code)**

Migrate to the canonical ui-kit exports:

```ts
// Before
import { colors } from "@policyengine/design-system/tokens";
const tealColor = colors.primary[500];

// After
import { palette } from "@policyengine/ui-kit";
const tealColor = palette.teal[500];
```

See the main ui-kit consumer skill for the full migration table.

### 6. Update Next.js config if present

**Remove** `transpilePackages` entries for design-system:

```js
// Before
const nextConfig = {
  transpilePackages: ['@policyengine/design-system']
};

// After
const nextConfig = {
  transpilePackages: ['@policyengine/ui-kit']
};
```

Note: With Next.js 16, many packages no longer need transpilation. Check if you can remove the array entirely.

### 7. Update test configs

If using Vitest:

```ts
// Before
export default defineConfig({
  optimizeDeps: {
    include: ['@policyengine/design-system']
  }
});

// After
export default defineConfig({
  optimizeDeps: {
    include: ['@policyengine/ui-kit']
  }
});
```

### 8. Install and verify

```bash
bun install
rm -rf .next node_modules/.cache
bun run build
```

Expected build output:
- No Tailwind-related errors
- No "utility class not found" warnings
- Clean build with no deprecation warnings

## React 19 Breaking Changes

The migration to React 19 may require code changes:

### 1. ref is now a regular prop

```tsx
// Before (React 18)
const Component = React.forwardRef<HTMLDivElement, Props>((props, ref) => (
  <div ref={ref} {...props} />
));

// After (React 19)
const Component = ({ ref, ...props }: Props & { ref?: React.Ref<HTMLDivElement> }) => (
  <div ref={ref} {...props} />
);
```

### 2. Context Provider value is required

```tsx
// Before (React 18) - value was optional if defined in createContext
<MyContext.Provider>
  {children}
</MyContext.Provider>

// After (React 19) - must be explicit
<MyContext.Provider value={defaultValue}>
  {children}
</MyContext.Provider>
```

### 3. Stricter PropTypes

React 19 removes the `propTypes` runtime check. Use TypeScript instead.

## Common Issues

### "Module not found: @policyengine/design-system"

You upgraded `package.json` but didn't update imports. Search the codebase:

```bash
grep -r "@policyengine/design-system" src/
```

Replace with `@policyengine/ui-kit/legacy` for quick fixes.

### "className 'flex' not found"

Missing `@import "tailwindcss"` in `globals.css`. Add it as the first line.

### Build works but styles are wrong

Likely multiple `@import "tailwindcss"` statements or stale cache. Clear `.next/` and rebuild.

### Type errors after React 19 upgrade

Check for `forwardRef` usage and Context Providers without explicit values.

## Testing the Migration

After migrating, verify:

1. **Visual regression**: Compare staging deployment to production
   - Brand colors (teal, gray, blue) match
   - Typography (Inter font) loads correctly
   - Spacing and layout match previous version

2. **Build verification**:
   ```bash
   bun run build
   bun run lint
   ```

3. **Runtime verification**:
   - No console warnings about missing utilities
   - DevTools shows Tailwind classes applied correctly
   - Responsive breakpoints work (xs/sm/md/lg/xl/2xl)

## Related Skills

- **policyengine-ui-kit-consumer-skill**: Full setup guide and troubleshooting
- **policyengine-design-skill**: Token reference and design system guidelines
- **policyengine-tailwind-shadcn-skill**: Advanced Tailwind v4 patterns
