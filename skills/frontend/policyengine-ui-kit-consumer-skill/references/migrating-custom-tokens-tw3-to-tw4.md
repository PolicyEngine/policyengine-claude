# Migrating Custom Legacy Tokens from Tailwind v3 to v4

How to preserve custom theme tokens during a Tailwind v3 → v4 migration while adopting `@policyengine/ui-kit`.

## When This Applies

Use this guide when migrating a repo that has:
- Tailwind v3 config with custom color/theme extensions
- Existing components using custom utility classes (e.g., `bg-pe-teal`, `text-pe-dark`)
- Need to migrate to Tailwind v4 + `@policyengine/ui-kit` without breaking existing styles

## The Problem

Tailwind v4 removes `tailwind.config.ts`. Custom tokens that lived in `theme.extend.colors` need to move to CSS using `@theme` blocks. If you just delete the config file, all custom utility classes break.

## Migration Pattern

### Step 1: Identify custom tokens in the old config

Look for custom color extensions in `tailwind.config.ts`:

```ts
// OLD - Tailwind v3 config
export default {
  theme: {
    extend: {
      colors: {
        'pe-teal': '#319795',
        'pe-teal-light': '#38B2AC',
        'pe-teal-dark': '#2C7A7B',
        'pe-dark': '#1E293B',
      },
    },
  },
};
```

### Step 2: Convert to CSS `@theme inline` blocks

Add these to `globals.css` **after** the ui-kit import:

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";

/* Preserve legacy custom tokens */
@theme inline {
  --color-pe-teal: #319795;
  --color-pe-teal-light: #38b2ac;
  --color-pe-teal-dark: #2c7a7b;
  --color-pe-dark: #1e293b;
}
```

**Why `@theme inline`:**
- Makes variables available to Tailwind's utility generator
- Existing `bg-pe-teal`, `text-pe-dark` classes continue working
- Variables are also available via `var(--color-pe-teal)` in inline styles

### Step 3: Delete the old config

```bash
rm tailwind.config.ts
```

### Step 4: Verify utility classes still work

Check that existing components using custom utilities still render correctly:

```tsx
// This should still work after migration
<div className="bg-pe-teal text-pe-dark" />
```

## Real-World Example: marketing-materials

The marketing-materials repo had:
- Custom `pe-teal*` color tokens in Tailwind v3 config
- Components using `bg-pe-teal` throughout the codebase
- Migration to Next.js 16 + Tailwind v4 + ui-kit 0.9

Solution applied:
```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";

@theme inline {
  --color-pe-teal: #319795;
  --color-pe-teal-light: #38b2ac;
  --color-pe-teal-dark: #2c7a7b;
  --color-pe-dark: #1e293b;
}
```

This preserved all existing utility classes while gaining ui-kit's standard tokens.

## When to Use Standard ui-kit Tokens Instead

If the custom tokens match ui-kit's standard palette, prefer migrating components to use standard classes:

| Custom token | ui-kit equivalent | Notes |
|--------------|------------------|-------|
| `pe-teal` (#319795) | `teal-500` | Exact match - prefer `bg-teal-500` |
| `pe-teal-light` (#38B2AC) | `teal-400` | Exact match - prefer `bg-teal-400` |
| `pe-teal-dark` (#2C7A7B) | `teal-600` or `primary` | Exact match - prefer `bg-teal-600` |
| `pe-dark` (#1E293B) | `gray-800` | Close match - verify design intent |

For new code, always use standard ui-kit tokens. Only preserve custom tokens for existing code that you don't want to refactor immediately.

## Pitfalls

### Don't use `@theme` without `inline` for utility classes

```css
/* WRONG - won't generate utility classes */
@theme {
  --color-pe-teal: #319795;
}
```

```css
/* CORRECT - generates bg-pe-teal, text-pe-teal, etc. */
@theme inline {
  --color-pe-teal: #319795;
}
```

Non-inline `@theme` blocks are for Tailwind's internal theme namespace (font sizes, spacing, etc.), not for color utilities.

### Don't skip the `--color-` prefix

```css
/* WRONG - won't match Tailwind's color naming convention */
@theme inline {
  --pe-teal: #319795;
}
```

```css
/* CORRECT - follows Tailwind v4 color variable pattern */
@theme inline {
  --color-pe-teal: #319795;
}
```

Tailwind v4 expects color variables to use `--color-*` prefix to generate utilities.

## Related Skills

- `policyengine-ui-kit-consumer-skill` — Standard ui-kit setup
- `policyengine-design-skill` — Full token reference for standard palette
