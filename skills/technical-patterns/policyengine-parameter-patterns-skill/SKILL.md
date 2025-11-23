---
name: policyengine-parameter-patterns
description: PolicyEngine parameter patterns - YAML structure, naming conventions, metadata requirements, federal/state separation
---

# PolicyEngine Parameter Patterns

Comprehensive patterns for creating PolicyEngine parameter files.

## Critical: Required Structure

Every parameter MUST have this exact structure:
```yaml
description: [One sentence description].
values:
  YYYY-MM-DD: value

metadata:
  unit: [type]       # REQUIRED
  period: [period]   # REQUIRED
  label: [name]      # REQUIRED
  reference:         # REQUIRED
    - title: [source]
      href: [url]
```

**Missing ANY metadata field = validation error**

---

## 1. File Naming Conventions

### Study Reference Implementations First
Before naming, examine:
- DC TANF: `/parameters/gov/states/dc/dhs/tanf/`
- IL TANF: `/parameters/gov/states/il/dhs/tanf/`
- TX TANF: `/parameters/gov/states/tx/hhs/tanf/`

### Naming Patterns

**Dollar amounts → `/amount.yaml`**
```
income/deductions/work_expense/amount.yaml     # $120
resources/limit/amount.yaml                    # $6,000
payment_standard/amount.yaml                   # $320
```

**Percentages/rates → `/rate.yaml` or `/percentage.yaml`**
```
income_limit/rate.yaml                         # 1.85 (185% FPL)
benefit_reduction/rate.yaml                    # 0.2 (20%)
income/disregard/percentage.yaml               # 0.67 (67%)
```

**Thresholds → `/threshold.yaml`**
```
age_threshold/minor_child.yaml                 # 18
age_threshold/elderly.yaml                     # 60
income/threshold.yaml                          # 30_000
```

---

## 2. Description Field

**Pattern:** `[State] [verb] [this X] [context].`

**Use generic placeholders:**
- `this amount`
- `this share`
- `this percentage`
- `this threshold`
- `these sources`

**Common verbs:**
- `excludes`
- `deducts`
- `provides`
- `limits`
- `uses`

```yaml
✅ GOOD:
description: Illinois excludes this share of earnings from TANF countable income.
description: Montana provides this amount as the minimum TANF benefit.
description: Texas limits resources to this amount for TANF eligibility.

❌ BAD:
description: Crisis benefit maximum  # Too short
description: Illinois allows eligibility when income is below...  # Too complex
```

---

## 3. Values Section

### Format Rules
```yaml
values:
  2024-01-01: 3_000    # Use underscores
  # NOT: 3000

  2024-01-01: 0.2      # Remove trailing zeros
  # NOT: 0.20 or 0.200

  2024-01-01: 2        # No decimals for integers
  # NOT: 2.0 or 2.00
```

### Effective Dates

**Use exact dates from sources:**
```yaml
# If source says "effective July 1, 2023"
2023-07-01: value

# If source says "as of October 1"
2024-10-01: value

# NOT arbitrary dates:
2000-01-01: value  # Shows no research
```

**Date format:** `YYYY-MM-01` (always use 01 for day)

---

## 4. Metadata Fields (ALL REQUIRED)

### unit
Common units:
- `currency-USD` - Dollar amounts
- `/1` - Rates, percentages (as decimals)
- `month` - Number of months
- `year` - Age in years
- `bool` - True/false
- `person` - Count of people

### period
- `year` - Annual values
- `month` - Monthly values
- `day` - Daily values
- `eternity` - Never changes

### label
Pattern: `[State] [PROGRAM] [description]`
```yaml
label: Montana TANF minor child age threshold
label: Illinois TANF earned income disregard rate
label: California SNAP resource limit
```
**Rules:**
- Spell out state name
- Abbreviate program (TANF, SNAP)
- No period at end

### reference
**Requirements:**
1. At least one source (prefer two)
2. Must contain the actual value
3. Legal codes need subsections
4. PDFs need page anchors

```yaml
✅ GOOD:
reference:
  - title: Idaho Admin Code 16.05.03.205(3)
    href: https://adminrules.idaho.gov/rules/current/16/160503.pdf#page=14
  - title: Idaho LIHEAP Guidelines, Section 3, page 8
    href: https://healthandwelfare.idaho.gov/guidelines.pdf#page=8

❌ BAD:
reference:
  - title: Federal LIHEAP regulations  # Too generic
    href: https://www.acf.hhs.gov/ocs  # No specific section
```

---

## 5. Federal/State Separation

### Federal Parameters
Location: `/parameters/gov/{agency}/{program}/`
```yaml
# parameters/gov/hhs/fpg/first_person.yaml
description: HHS sets this amount as the federal poverty guideline for one person.
```

### State Parameters
Location: `/parameters/gov/states/{state}/{agency}/{program}/`
```yaml
# parameters/gov/states/ca/dss/tanf/income_limit/rate.yaml
description: California uses this multiplier of the federal poverty guideline for TANF income eligibility.
```

---

## 6. Common Parameter Patterns

### Income Limits (as FPL multiplier)
```yaml
# income_limit/rate.yaml
description: State uses this multiplier of the federal poverty guideline for program income limits.
values:
  2024-01-01: 1.85  # 185% FPL

metadata:
  unit: /1
  period: year
  label: State PROGRAM income limit multiplier
```

### Benefit Amounts
```yaml
# payment_standard/amount.yaml
description: State provides this amount as the monthly program benefit.
values:
  2024-01-01: 500

metadata:
  unit: currency-USD
  period: month
  label: State PROGRAM payment standard amount
```

### Age Thresholds
```yaml
# age_threshold/minor_child.yaml
description: State defines minor children as under this age for program eligibility.
values:
  2024-01-01: 18

metadata:
  unit: year
  period: eternity
  label: State PROGRAM minor child age threshold
```

### Disregard Percentages
```yaml
# income/disregard/percentage.yaml
description: State excludes this share of earned income from program calculations.
values:
  2024-01-01: 0.67  # 67%

metadata:
  unit: /1
  period: eternity
  label: State PROGRAM earned income disregard percentage
```

---

## 7. Validation Checklist

Before creating parameters:
- [ ] Studied reference implementations (DC, IL, TX)
- [ ] All four metadata fields present
- [ ] Description is one complete sentence
- [ ] Values use underscore separators
- [ ] Trailing zeros removed from decimals
- [ ] References include subsections and page numbers
- [ ] Label follows naming pattern
- [ ] Effective date matches source document

---

## 8. Common Mistakes to Avoid

### Missing Metadata
```yaml
❌ WRONG - Missing required fields:
metadata:
  unit: currency-USD
  label: Benefit amount
  # Missing: period, reference
```

### Generic References
```yaml
❌ WRONG:
reference:
  - title: State TANF Manual
    href: https://state.gov/tanf

✅ CORRECT:
reference:
  - title: State TANF Manual Section 5.2, page 15
    href: https://state.gov/tanf-manual.pdf#page=15
```

### Arbitrary Dates
```yaml
❌ WRONG:
values:
  2000-01-01: 500  # Lazy default

✅ CORRECT:
values:
  2023-07-01: 500  # From source: "effective July 1, 2023"
```

---

## For Agents

When creating parameters:
1. **Study existing implementations** for patterns
2. **Include ALL metadata fields** - missing any causes errors
3. **Use exact effective dates** from sources
4. **Follow naming conventions** (amount/rate/threshold)
5. **Write simple descriptions** with "this" placeholders
6. **Include specific references** with subsections and pages
7. **Format values properly** (underscores, no trailing zeros)