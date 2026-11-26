---
description: React 19 best practices and migration patterns for PolicyEngine repositories
---

# React 19 Patterns

Critical patterns for React 19 compatibility in PolicyEngine React codebases.

## Component Definition Location

**React 19 enforces stricter rules about where components can be defined.**

### ❌ BAD - Component defined inside render

```tsx
export default function Page() {
  // ❌ Component defined during render - violates React 19 rules
  const StepHeader = ({ onClick }: { onClick: () => void }) => (
    <div onClick={onClick}>
      <h2>Step Header</h2>
    </div>
  );

  return (
    <div>
      <StepHeader onClick={() => console.log('clicked')} />
    </div>
  );
}
```

**Why this fails:**
- In React 19, components must be statically defined at module scope
- Defining components during render causes them to be recreated on every render
- This breaks React's reconciliation and causes unnecessary remounts
- ESLint rule `react-hooks/static-components` will error on this pattern

### ✅ GOOD - Component at module scope

```tsx
// ✅ Component defined at module scope
const StepHeader = ({ onClick }: { onClick: () => void }) => (
  <div onClick={onClick}>
    <h2>Step Header</h2>
  </div>
);

export default function Page() {
  return (
    <div>
      <StepHeader onClick={() => console.log('clicked')} />
    </div>
  );
}
```

### ✅ ALSO GOOD - Inline JSX when not reused

If the component is only used once and doesn't need to be extracted, inline the JSX directly:

```tsx
export default function Page() {
  return (
    <div>
      {/* ✅ Inline JSX - no component extraction needed */}
      <div onClick={() => console.log('clicked')}>
        <h2>Step Header</h2>
      </div>
    </div>
  );
}
```

## When to Extract Components

Extract to module scope when:
- Component is reused multiple times
- Component has complex logic worth isolating
- Component needs a descriptive name for readability

Keep inline when:
- JSX is simple and used only once
- Logic is tightly coupled to parent component
- Extraction would reduce readability

## ESLint Configuration

Ensure `react-hooks/static-components` is enabled in ESLint flat config:

```js
// eslint.config.mjs
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';

export default [
  {
    plugins: {
      react,
      'react-hooks': reactHooks,
    },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'react-hooks/static-components': 'error', // Enforces module-scope components
    },
  },
];
```

## Migration Checklist

When upgrading to React 19:

- [ ] Search codebase for components defined inside function bodies
- [ ] Move component definitions to module scope
- [ ] Pass dynamic data as props instead of closure variables
- [ ] Enable `react-hooks/static-components` ESLint rule
- [ ] Run `eslint --fix` to catch any remaining violations
- [ ] Test that components still render and behave correctly

## Related Changes

React 19 also includes:

- `forwardRef` is now built into component signatures (but still supported for compatibility)
- Stricter rules around hooks usage
- Improved TypeScript types for component props

See [React 19 upgrade guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide) for full migration details.
