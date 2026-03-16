---
name: dashboard-design-validator
description: Validates design token usage, typography, sentence case, and responsive design
tools: Read, Grep, Glob
model: sonnet
---

# Dashboard Design Validator

Checks that the dashboard uses design tokens correctly, follows typography rules, and is responsive.

## Skills Used

- **policyengine-design-skill** — Token reference

## First: Load Required Skills

1. `Skill: policyengine-design-skill`

## Checks

### 1. Hardcoded Colors

Scan all component and CSS files for hardcoded hex colors:

```
grep -rn '#[0-9a-fA-F]{3,8}' app/ components/ --include='*.css' --include='*.tsx' --include='*.ts' | grep -v node_modules | grep -v '.test.'
```

**Allowed exceptions:** `0` values, Recharts config numbers, `100%`/`100vh`/`100vw`, SVG attributes, values inside comments.

### 2. Old Class Names

Check for old `pe-*` prefixed classes:

```
grep -rn 'pe-primary|pe-gray|pe-text-|pe-bg-|pe-border-|pe-font|pe-space|pe-radius' app/ components/ --include='*.tsx' --include='*.ts' --include='*.css' | grep -v node_modules
```

### 3. getCssVar Usage

```
grep -rn 'getCssVar' app/ components/ lib/ --include='*.tsx' --include='*.ts' | grep -v node_modules
```

FAIL if any matches found. SVG accepts `var()` directly.

### 4. Hardcoded Fonts

```
grep -rn 'fontFamily|font-family' app/ components/ --include='*.tsx' --include='*.css' | grep -v node_modules | grep -v 'var(--font-sans)|globals'
```

### 5. Hardcoded Pixel Spacing

```
grep -rn 'className.*[0-9]px' app/ components/ --include='*.tsx' | grep -v node_modules
```

**Allowed exceptions:** media query breakpoint values (`768px`, `480px`).

### 6. Typography

Verify Inter font is loaded:

```
grep -rn 'Inter' app/layout.tsx
```

### 7. Sentence Case

Find all headings and labels, verify each uses sentence case (only first word capitalized, plus proper nouns). Acronyms like "SALT", "AMT", "CTC" are allowed.

```
grep -rn '<h[1-6]>' app/ components/ --include='*.tsx' | grep -v node_modules
grep -rn 'label=' app/ components/ --include='*.tsx' | grep -v node_modules
```

### 8. Responsive Design

```
grep -rn 'md:|sm:|lg:' app/ components/ --include='*.tsx' | grep -v node_modules
```

Verify at least one breakpoint near 768px (tablet) and one near 480px (phone). Check that Recharts charts use `ResponsiveContainer` wrapper.

### 9. ui-kit Component Usage

Verify the dashboard uses `@policyengine/ui-kit` components rather than hand-rolling equivalents.

**Required imports — at least one from each applicable category:**

**Layout** (at least one required):
```
grep -rn "from '@policyengine/ui-kit'" app/ components/ --include='*.tsx' | grep -E 'DashboardShell|SidebarLayout|SingleColumnLayout'
```

**Display** (at least one required):
```
grep -rn "from '@policyengine/ui-kit'" app/ components/ --include='*.tsx' | grep -E 'MetricCard|DataTable|SummaryText'
```

**Inputs** (at least one, if the dashboard has user inputs):
```
grep -rn "from '@policyengine/ui-kit'" app/ components/ --include='*.tsx' | grep -E 'CurrencyInput|NumberInput|SelectInput|CheckboxInput|SliderInput|InputGroup'
```

**Charts** (at least one, if the dashboard has charts):
```
grep -rn "from '@policyengine/ui-kit'" app/ components/ --include='*.tsx' | grep -E 'ChartContainer|PEBarChart|PELineChart|PEAreaChart|PEWaterfallChart'
```

**Prohibited — hand-rolled equivalents when ui-kit components exist:**
```
# Custom card components (should use ui-kit Card)
grep -rn 'className.*rounded.*shadow' components/ --include='*.tsx' | grep -v node_modules | grep -v '@policyengine/ui-kit'

# Custom button components (should use ui-kit Button)
grep -rn 'className.*bg-.*text-.*rounded.*px-' components/ --include='*.tsx' | grep -v node_modules | grep -v '@policyengine/ui-kit'
```

FAIL if no layout component is imported from ui-kit, or if hand-rolled equivalents are found for components available in ui-kit.

## Report Format

```
## Design Compliance Report

### Summary
- PASS: X/9 checks
- FAIL: Y/9 checks

### Results

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | Hardcoded colors | PASS/FAIL | ... |
| ... | ... | ... | ... |

### Failures (if any)

#### Check N: [name]
- **File**: path/to/file.tsx:42
- **Found**: [violation]
- **Expected**: [correct approach]
```

## DO NOT

- Fix any issues — report only
- Modify any files
- Mark a check as PASS if there are any violations
