---
description: Build new UI components for @policyengine/ui-kit — with design token validation, tests, visual preview, and PR creation
---

# Create new component

Builds one or more new components for the `@policyengine/ui-kit` library. Handles the full lifecycle: research existing patterns, build with design tokens, validate token usage, write tests, preview visually, and open a PR.

## Prerequisites

The `policyengine-ui-kit` repo must be cloned locally. If not found, clone it:
```bash
gh repo clone PolicyEngine/policyengine-ui-kit
```

All work happens in the `policyengine-ui-kit` repo directory.

## Step 1: Gather requirements

Use `AskUserQuestion` to ask the user:

1. **Component description** — What component(s) do you need? Describe their purpose, behavior, and any variants.

Parse the description to identify:
- Component names (PascalCase, e.g., `Tooltip`, `ProgressBar`, `Accordion`)
- Which category they belong to: `primitives`, `layout`, `inputs`, `display`, or `charts`
- Expected props, variants, and states

## Step 2: Research app-v2 for similar components

Before building from scratch, search `PolicyEngine/policyengine-app-v2` for similar implementations:

```bash
# Search app-v2 for components with similar names or purposes
find /path/to/policyengine-app-v2/app/src -name "*.tsx" | xargs grep -li "COMPONENT_NAME_PATTERN"

# Also check the design-system package
find /path/to/policyengine-app-v2/packages/design-system -name "*.tsx" | xargs grep -li "COMPONENT_NAME_PATTERN"

# Check Mantine usage patterns for the same component type
grep -r "Mantine.*COMPONENT_TYPE" /path/to/policyengine-app-v2/app/src --include="*.tsx" -l
```

If similar components exist in app-v2:
- Study their props interface, variant patterns, and behavior
- Adapt the design and UX, but rebuild using the ui-kit's Tailwind v4 + CVA stack
- Do NOT copy Mantine-dependent code — translate it to Tailwind utility classes

If nothing similar exists in app-v2:
- Research common patterns for that component type
- Design props and variants that are consistent with existing ui-kit components

## Step 3: Build the component(s)

**Tech stack (mandatory):**
- React 19 with `forwardRef`
- TypeScript with strict types
- Tailwind CSS v4 with `tw:` prefix on all utility classes
- CVA (`class-variance-authority`) for variant management
- `cn()` utility from `@/utils/cn` for class merging
- Design tokens from the ui-kit's Tailwind theme (colors, spacing, typography, radius)

**File structure for each component:**
```
src/<category>/ComponentName.tsx
```

**Component template:**
```tsx
import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '../utils/cn';

const componentVariants = cva(
  'tw:base-classes-here',
  {
    variants: {
      variant: {
        default: 'tw:variant-classes',
        // ... more variants
      },
      size: {
        sm: 'tw:size-classes',
        md: 'tw:size-classes',
        lg: 'tw:size-classes',
      },
    },
    defaultVariants: { variant: 'default', size: 'md' },
  },
);

export interface ComponentNameProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof componentVariants> {
  // Additional props here
}

export const ComponentName = forwardRef<HTMLDivElement, ComponentNameProps>(
  ({ variant, size, className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(componentVariants({ variant, size }), className)}
      {...props}
    >
      {children}
    </div>
  ),
);
ComponentName.displayName = 'ComponentName';
```

**Rules:**
- ALL Tailwind classes must use the `tw:` prefix
- ALL colors, spacing, font sizes, and radii must reference design tokens — no hardcoded hex values, no arbitrary pixel values
- Export the component and its props interface from the category barrel (`src/<category>/index.ts`)
- Export from the main barrel (`src/index.ts`)
- Build ALL components the user requested — do not skip any

## Step 4: Design token validation agent

Launch the **Design Token Validator Agent** (`agents/app/design-token-validator.md`) to audit every component file created in Step 3.

The agent will:
1. Scan all new component files for hardcoded values
2. Replace hardcoded colors, spacing, font sizes, and radii with token-based Tailwind classes
3. Report what was replaced and what was kept

Review the agent's output. If it made changes, verify they look correct.

## Step 5: Add components to a preview page

Create or update `demo/Demo.tsx` to include a new section showcasing ALL new components with realistic example data.

```tsx
// Add a new section for each component
<section>
  <h2 className="tw:text-2xl tw:font-bold tw:mb-lg">ComponentName</h2>
  <div className="tw:flex tw:flex-wrap tw:gap-md">
    {/* Render every variant, size, and state */}
    <ComponentName variant="default">Example</ComponentName>
    <ComponentName variant="primary" size="lg">Large primary</ComponentName>
    {/* ... all combinations */}
  </div>
</section>
```

**Important:** Include ALL new components on the preview page, not just some.

## Step 6: Launch preview and iterate with user

Start the demo dev server:
```bash
cd /path/to/policyengine-ui-kit
bun run dev:demo
```

Tell the user:
> The demo server is running at http://localhost:5173/demo/index.html — scroll to the new component section to preview your components.

Then use `AskUserQuestion` to ask:
> Do the components look correct? Please review and either approve or describe changes you'd like.

**This is iterative.** If the user requests changes:
1. Apply the requested modifications
2. The dev server will hot-reload automatically
3. Ask the user to review again
4. Repeat until the user approves

Do NOT proceed to Step 7 until the user explicitly approves the components.

## Step 7: Component test writer agent

After user approval, launch the **Component Test Writer Agent** (`agents/app/component-test-writer.md`) to write unit tests for ALL new components.

The agent will:
1. Read each new component file
2. Write comprehensive test files (rendering, props, variants, interaction, ref forwarding)
3. Place tests next to components (`src/<category>/ComponentName.test.tsx`)
4. Run `bun run test` and fix any failures

Verify all tests pass:
```bash
cd /path/to/policyengine-ui-kit
bun run test
```

If tests fail, fix them before proceeding.

## Step 8: Create changelog fragment

Add a towncrier changelog fragment:
```bash
echo "Add <ComponentName>, <ComponentName2>, ... components." > changelog.d/add-COMPONENT_NAME.added.md
```

## Step 9: Commit, push, and open PR

```bash
# Create feature branch
git checkout -b add-COMPONENT_NAME-component

# Stage all new and modified files
git add src/<category>/ComponentName.tsx
git add src/<category>/ComponentName.test.tsx
git add src/<category>/index.ts
git add src/index.ts
git add demo/Demo.tsx
git add changelog.d/add-COMPONENT_NAME.added.md

# Commit
git commit -m "Add ComponentName component with tests"

# Push
git push -u origin add-COMPONENT_NAME-component
```

Create a PR with details about the new components and their test coverage:
```bash
gh pr create --repo PolicyEngine/policyengine-ui-kit \
  --title "Add ComponentName component" \
  --body "$(cat <<'EOF'
## Summary
- Add `ComponentName` component to `@policyengine/ui-kit`
- <Describe each component, its variants, and purpose>

## Components added
- `ComponentName` — <brief description>
  - Variants: <list variants>
  - Props: <list key props>

## Testing
- Unit tests written with Vitest + React Testing Library
- Tests cover: rendering, all variants, props, interaction, ref forwarding
- All tests passing

## Design token compliance
- All colors reference design tokens (no hardcoded hex)
- All spacing uses token-based Tailwind classes
- All typography uses token scale
- Validated by design-token-validator agent

## Test plan
- [ ] Run `bun run dev:demo` and verify components render correctly
- [ ] Run `bun run test` and verify all tests pass
- [ ] Review component API matches existing ui-kit conventions

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Report the PR URL to the user.

## Reference

See these skills and agents for detailed guidance:
- `policyengine-design-skill` — Design token values and usage
- `policyengine-app-skill` — app-v2 component patterns to reference
- `agents/app/design-token-validator.md` — Automated design token compliance
- `agents/app/component-test-writer.md` — Automated test writing
