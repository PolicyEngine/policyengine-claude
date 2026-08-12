---
name: policyengine-ui-kit-maintenance
description: |
  Guidance for maintaining and developing the @policyengine/ui-kit package itself.
  Covers theme.css structure, utility class definition patterns, and common gotchas
  when working on the ui-kit codebase (not consuming it).
  Triggers: "ui-kit maintenance", "theme.css", "utility classes missing", "text-5xl",
  "slide-deck build error", "unknown utility class", "@theme reset", "ui-kit development"
---

# Maintaining @policyengine/ui-kit

This skill covers patterns specific to developing and maintaining the `@policyengine/ui-kit` package itself. For consuming the ui-kit in applications, see `policyengine-ui-kit-consumer-skill`.

## Theme Architecture

The ui-kit's `theme.css` file serves as the single source of truth for all design tokens across PolicyEngine projects. It uses Tailwind v4's `@theme` directive to define utility classes that consumers will have access to.

### Critical Pattern: Reset and Redefine

The ui-kit uses a "reset and redefine" pattern for Tailwind utilities:

```css
@theme {
  /* Reset existing Tailwind defaults */
  --text-*: initial;

  /* Selectively redefine what we want available */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  --text-5xl: 3rem;      /* 48px */
  --text-6xl: 3.75rem;   /* 60px */
  --text-7xl: 4.5rem;    /* 72px */
  --text-8xl: 6rem;      /* 96px */
  --text-9xl: 8rem;      /* 128px */
}
```

**Critical gotcha:** If you reset a Tailwind utility namespace (like `--text-*: initial`) but don't redefine a specific value, that utility class will NOT be available to consumers. They'll get build errors like:

```
Cannot apply unknown utility class 'text-6xl'
```

### Common Resets

These resets are used in theme.css:

- `--text-*: initial` - Text size utilities (must redefine xs through 9xl)
- `--font-*: initial` - Font family utilities (must redefine sans, serif, mono if needed)
- `--spacing-*: initial` - Custom spacing utilities (redefine header, sidebar, etc.)

## Impact on Consumers

When a utility is missing from the ui-kit's `@theme` block:

1. **Web apps** using the ui-kit may not notice immediately if they don't use that utility
2. **Slide-deck repos** commonly use larger text sizes (`text-5xl` through `text-9xl`) and will fail to build
3. **Build errors** appear as "Cannot apply unknown utility class"

## Verification Checklist

When modifying `theme.css`:

1. **Check for complete ranges**: If you reset `--text-*`, ensure you've redefined ALL commonly-used text sizes (xs through 9xl)
2. **Test slide-deck repos**: These are most likely to use edge cases like `text-6xl`, `text-7xl`, etc.
3. **Review consumer usage**: Search across policyengine-app, policyengine-us, and slide repos for utility class usage
4. **Verify build**: Run `bun run build` in the ui-kit to ensure the theme compiles correctly

## Related Patterns

### Font Size Scale

The complete Tailwind text size scale should be defined if using the reset pattern:

```css
@theme {
  --text-*: initial;
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  --text-5xl: 3rem;      /* 48px */
  --text-6xl: 3.75rem;   /* 60px */
  --text-7xl: 4.5rem;    /* 72px */
  --text-8xl: 6rem;      /* 96px */
  --text-9xl: 8rem;      /* 128px */
}
```

### Why Reset?

The reset pattern (`--text-*: initial`) is used to:

1. Override Tailwind's default scale
2. Ensure consistency across all PolicyEngine projects
3. Prevent consumers from accidentally using non-standard sizes

However, this means the ui-kit **must** redefine every utility that consumers need.

## Common Mistakes

### 1. Partial Range Definition

```css
/* WRONG - only defines xs through 4xl, breaks slide-deck repos */
@theme {
  --text-*: initial;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;
  /* Missing 5xl through 9xl! */
}

/* CORRECT - defines complete range */
@theme {
  --text-*: initial;
  /* ... xs through 4xl ... */
  --text-5xl: 3rem;
  --text-6xl: 3.75rem;
  --text-7xl: 4.5rem;
  --text-8xl: 6rem;
  --text-9xl: 8rem;
}
```

### 2. Assuming Tailwind Defaults Apply

```css
/* WRONG - assumes Tailwind's default text-6xl will work */
@theme {
  --text-*: initial;  /* This resets ALL text utilities */
  --text-base: 1rem;  /* Only base is redefined */
}
/* Result: Only text-base works, everything else breaks */

/* CORRECT - explicitly redefine everything needed */
@theme {
  --text-*: initial;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  /* ... define complete range ... */
}
```

### 3. Not Testing Against All Consumer Types

- Web apps might only use `text-sm` through `text-2xl`
- Slide decks commonly use `text-5xl` through `text-7xl`
- Landing pages might use `text-8xl` or `text-9xl` for hero sections

Always test against multiple consumer types or search for utility usage across repos.

## Testing Strategy

Before publishing a ui-kit release:

1. **Local link testing**:
   ```bash
   cd policyengine-ui-kit
   bun link

   cd ../policyengine-app
   bun link @policyengine/ui-kit
   bun run build
   ```

2. **Search for utility usage**:
   ```bash
   # Find all text size usages across repos
   rg "text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)" --type tsx
   ```

3. **Check slide-deck repos**: These are most likely to catch missing utilities

## Related Skills

- `policyengine-ui-kit-consumer-skill` - How apps consume the ui-kit
- `policyengine-tailwind-shadcn-skill` - @theme namespace mechanics
- `policyengine-design-skill` - Design token values and guidelines
