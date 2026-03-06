---
name: policyengine-tailwind-shadcn
description: |
  Tailwind CSS v4 + shadcn/ui integration patterns for PolicyEngine frontend projects.
  Covers @theme namespaces, CSS variable conventions, SVG var() usage, and common mistakes.
  Triggers: "Tailwind v4", "@theme", "shadcn", "CSS variables", "design tokens CSS", "theme.css", "@theme inline"
---

# Tailwind CSS v4 + shadcn/ui integration

Technical reference for how PolicyEngine's CSS-first design token architecture works. This skill explains the **mechanism** — how Tailwind v4 and shadcn/ui consume CSS variables. For the actual **token values** (colors, fonts, spacing), see `policyengine-design-skill`.

## Architecture overview

PolicyEngine uses a single CSS file (`@policyengine/ui-kit/theme.css`) as the source of truth for all design tokens. This file has three layers:

```
Layer 1: :root { --primary: #2C7A7B; }          ← Raw values (shadcn/ui convention)
Layer 2: @theme inline { --color-primary: var(--primary); }  ← Bridge to Tailwind
Layer 3: @theme { --color-teal-500: #319795; }   ← Brand palette + fonts + sizes
```

Consumers import it in their `globals.css`:
```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

## Tailwind v4 `@theme` namespaces

Tailwind v4 uses CSS custom properties in `@theme` blocks to generate utility classes. The **namespace prefix** determines which utilities are created:

| CSS variable prefix | Tailwind utility | Example variable | Example class |
|---|---|---|---|
| `--color-*` | `bg-*`, `text-*`, `border-*`, `fill-*` | `--color-primary: #2C7A7B` | `bg-primary`, `text-primary` |
| `--color-teal-*` | `bg-teal-*`, `text-teal-*` | `--color-teal-500: #319795` | `bg-teal-500` |
| `--text-*` | `text-*` (font size) | `--text-sm: 14px` | `text-sm` |
| `--font-*` | `font-*` | `--font-sans: Inter, ...` | `font-sans` |
| `--radius-*` | `rounded-*` | `--radius-lg: 8px` | `rounded-lg` |
| `--spacing-*` | `p-*`, `m-*`, `gap-*`, `w-*`, `h-*` | `--spacing-header: 58px` | `h-header` |
| `--breakpoint-*` | `sm:`, `md:`, `lg:` | `--breakpoint-md: 62rem` | `md:flex-col` |

**Source:** [Tailwind v4 Theme docs](https://tailwindcss.com/docs/theme)

## `@theme` vs `@theme inline`

```css
/* @theme — bakes values directly into generated CSS */
@theme {
  --color-teal-500: #319795;  /* Resolved at build time */
}

/* @theme inline — preserves var() for runtime resolution */
@theme inline {
  --color-primary: var(--primary);  /* Resolved at runtime via :root */
}
```

**When to use `@theme inline`:**
- When the value references a `:root` CSS variable (`var(--something)`)
- Required for dark mode (`:root` values change, Tailwind must re-resolve)
- Used for all shadcn/ui semantic tokens (primary, background, foreground, etc.)

**When to use `@theme`:**
- When the value is a static literal (`#319795`, `14px`, `Inter`)
- Used for brand palette colors, font sizes, spacing, breakpoints

**Source:** [Tailwind v4 Functions and Directives](https://tailwindcss.com/docs/functions-and-directives)

## shadcn/ui CSS variable convention

shadcn/ui defines semantic tokens as **unprefixed** CSS variables in `:root`:

```css
:root {
  --primary: #2C7A7B;
  --background: #FFFFFF;
  --foreground: #000000;
  --muted: #F2F4F7;
  --muted-foreground: #6B7280;
  --border: #E2E8F0;
  --chart-1: #319795;
  --chart-2: #0EA5E9;
  /* ... */
}
```

These are then bridged to Tailwind via `@theme inline`:

```css
@theme inline {
  --color-primary: var(--primary);       /* → bg-primary, text-primary */
  --color-background: var(--background); /* → bg-background */
  --color-foreground: var(--foreground); /* → text-foreground */
  --color-chart-1: var(--chart-1);       /* → fill-chart-1 */
}
```

**Source:** [shadcn/ui Theming](https://ui.shadcn.com/docs/theming), [shadcn/ui Tailwind v4 guide](https://ui.shadcn.com/docs/tailwind-v4)

## SVG `var()` in Recharts

Modern browsers resolve CSS custom properties in SVG presentation attributes. Recharts `fill` and `stroke` props accept `var()` directly:

```tsx
<Bar fill="var(--chart-1)" />
<Line stroke="var(--chart-2)" />
<CartesianGrid stroke="var(--border)" />
```

No helper function needed. The old `getCssVar()` / `getComputedStyle()` pattern is unnecessary.

**Source:** [shadcn/ui Charts](https://ui.shadcn.com/docs/components/chart)

## Complete namespace reference

### Layer 1: `:root` (shadcn/ui semantic)

| Variable | Hex | Usage |
|----------|-----|-------|
| `--primary` | `#2C7A7B` | Primary actions, buttons |
| `--primary-foreground` | `#FFFFFF` | Text on primary |
| `--background` | `#FFFFFF` | Page background |
| `--foreground` | `#000000` | Body text |
| `--muted` | `#F2F4F7` | Muted backgrounds |
| `--muted-foreground` | `#6B7280` | Secondary text |
| `--border` | `#E2E8F0` | Borders, dividers |
| `--card` | `#FFFFFF` | Card backgrounds |
| `--destructive` | `#EF4444` | Error states |
| `--ring` | `#319795` | Focus rings |
| `--chart-1` through `--chart-5` | Teal→Gray | Chart series |

### Layer 2: `@theme inline` (bridges)

Maps each `:root` var to Tailwind's `--color-*` namespace. Example:
- `--color-primary: var(--primary)` → enables `bg-primary`, `text-primary`
- `--color-chart-1: var(--chart-1)` → enables `fill-chart-1`

### Layer 3: `@theme` (brand palette)

| Namespace | Example | Tailwind class |
|-----------|---------|---------------|
| `--color-teal-*` | `--color-teal-500: #319795` | `bg-teal-500` |
| `--color-gray-*` | `--color-gray-600: #4B5563` | `text-gray-600` |
| `--color-blue-*` | `--color-blue-500: #0EA5E9` | `bg-blue-500` |
| `--text-*` | `--text-sm: 14px` | `text-sm` |
| `--font-*` | `--font-sans: Inter, ...` | `font-sans` |
| `--spacing-*` | `--spacing-header: 58px` | `h-header` |

## Common mistakes

### 1. Using `@theme` instead of `@theme inline` for var() references

```css
/* WRONG — var() won't resolve, Tailwind bakes the literal string */
@theme {
  --color-primary: var(--primary);
}

/* CORRECT — var() resolves at runtime */
@theme inline {
  --color-primary: var(--primary);
}
```

### 2. Wrong namespace prefix

```css
/* WRONG — creates a utility called "primary", not a color */
@theme {
  --primary: #2C7A7B;
}

/* CORRECT — --color-* prefix creates bg-primary, text-primary */
@theme inline {
  --color-primary: var(--primary);
}
```

### 3. Using getCssVar() for Recharts

```tsx
// WRONG — unnecessary helper
const color = getCssVar('--chart-1');
<Bar fill={color} />

// CORRECT — SVG accepts var() directly
<Bar fill="var(--chart-1)" />
```

### 4. Hardcoding hex in components

```tsx
// WRONG
<div style={{ color: '#319795' }}>

// CORRECT — use Tailwind class
<div className="text-teal-500">

// CORRECT — use CSS var for inline styles
<div style={{ color: 'var(--primary)' }}>
```

### 5. Creating tailwind.config.ts

Tailwind v4 does NOT use `tailwind.config.ts`. All configuration is in CSS via `@theme` blocks. The ui-kit theme CSS file handles this.

### 6. Using old pe-* prefixed classes

```tsx
// WRONG — old convention
<div className="bg-pe-primary-500 text-pe-text-secondary p-pe-lg">

// CORRECT — standard Tailwind/shadcn classes
<div className="bg-teal-500 text-muted-foreground p-4">
```

## Related skills

- `policyengine-design-skill` — Token values, color tables, chart branding
- `policyengine-frontend-builder-spec-skill` — Mandatory technology requirements
- `policyengine-recharts-skill` — Chart-specific patterns
- `policyengine-interactive-tools-skill` — Standalone tool scaffolding
