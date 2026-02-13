# PolicyEngine design system

Use this skill when creating or modifying frontend components for PolicyEngine applications. This ensures consistent styling using the shared `@policyengine/design-system` package.

## Package

```bash
npm install @policyengine/design-system
```

## Imports

```typescript
import { colors, typography, spacing } from '@policyengine/design-system/tokens';
```

## Mantine theme setup

PolicyEngine apps use Mantine 8 with a theme built from design tokens:

```typescript
import { createTheme } from '@mantine/core';
import type { MantineColorsTuple } from '@mantine/core';
import { colors, typography } from '@policyengine/design-system/tokens';

const primary: MantineColorsTuple = [
  colors.primary[50], colors.primary[100], colors.primary[200],
  colors.primary[300], colors.primary[400], colors.primary[500],
  colors.primary[600], colors.primary[700], colors.primary[800],
  colors.primary[900],
];

export const theme = createTheme({
  primaryColor: 'primary',
  colors: { primary },
  fontFamily: typography.fontFamily.primary,
  fontFamilyMonospace: typography.fontFamily.mono,
  headings: { fontFamily: typography.fontFamily.primary, fontWeight: '600' },
  defaultRadius: 'md',
  focusRing: 'auto',
});
```

## Colors

```typescript
// Primary brand - teal
colors.primary[500]  // #319795 - main brand color
colors.primary[50]   // #E6FFFA - lightest
colors.primary[900]  // #1D4044 - darkest

// Gray scale
colors.gray[50]  // #F9FAFB
colors.gray[500] // #6B7280
colors.gray[900] // #101828

// Blue accent
colors.blue[500] // #0EA5E9

// Semantic
colors.success  // #22C55E
colors.warning  // #FEC601
colors.error    // #EF4444
colors.info     // #1890FF

// Text
colors.text.primary    // #000000
colors.text.secondary  // #5A5A5A
colors.text.tertiary   // #9CA3AF
colors.text.inverse    // #FFFFFF

// Background
colors.background.primary    // #FFFFFF
colors.background.secondary  // #F5F9FF
colors.background.tertiary   // #F1F5F9

// Border
colors.border.light   // #E2E8F0
colors.border.medium  // #CBD5E1
colors.border.dark    // #94A3B8
```

## Typography

```typescript
// Fonts
typography.fontFamily.primary   // 'Inter, -apple-system, ..., sans-serif'
typography.fontFamily.secondary // 'Public Sans, ..., sans-serif'
typography.fontFamily.body      // 'Roboto, ..., sans-serif'
typography.fontFamily.mono      // 'JetBrains Mono, "Fira Code", ...'
typography.fontFamily.chart     // 'Roboto Serif, Georgia, ...' (for chart axes/labels)

// Font sizes
typography.fontSize.xs   // 12px
typography.fontSize.sm   // 14px
typography.fontSize.base // 16px
typography.fontSize.lg   // 18px
typography.fontSize.xl   // 20px
typography.fontSize['2xl'] // 24px

// Font weights
typography.fontWeight.normal   // 400
typography.fontWeight.medium   // 500
typography.fontWeight.semibold // 600
typography.fontWeight.bold     // 700
```

## Plotly chart styling

All Plotly charts should use a consistent layout base:

```typescript
import { colors, typography } from '@policyengine/design-system/tokens';

const chartLayout = {
  font: {
    family: typography.fontFamily.primary, // Inter (sans-serif)
    size: 14,
    color: colors.text.primary,
  },
  paper_bgcolor: colors.background.primary,
  plot_bgcolor: colors.background.primary,
  margin: { l: 60, r: 40, t: 40, b: 60 },
};

// Semantic chart colors
const chartColors = {
  primary: colors.primary[500],    // teal - main series
  secondary: colors.blue[500],     // blue - secondary series
  positive: colors.success,        // green - positive changes
  negative: colors.error,          // red - negative changes
  oldBaseline: colors.gray[400],   // gray dashed - old/prior values
  newBaseline: colors.primary[500], // teal solid - new/current values
};
```

## Vitest configuration

If tests fail with ESM module resolution errors for the design system package, add:

```typescript
// vitest.config.ts
test: {
  server: {
    deps: {
      inline: ['@policyengine/design-system'],
    },
  },
},
```

## Key rules

1. **Never hardcode colors** - always use `colors.*` tokens
2. **Charts use Inter** - set `typography.fontFamily.primary` as chart font (not serif)
3. **Teal is the brand color** - `colors.primary[500]` (#319795)
4. **Sentence case for all UI text** - only capitalize first word and proper nouns
