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

### The ONLY Acceptable Formula

```yaml
description: [State] [verb] [category] to [this X] under the [Full Program Name] program.
```

**Components:**
1. **[State]**: Full state name (Indiana, Texas, California)
2. **[verb]**: ONLY use: limits, provides, sets, excludes, deducts, uses
3. **[category]**: What's being limited/provided (gross income, resources, payment standard)
4. **[this X]**: ALWAYS use generic placeholder
   - `this amount` (for currency-USD)
   - `this share` or `this percentage` (for rates/percentages)
   - `this threshold` (for age/counts)
5. **[Full Program Name]**: ALWAYS spell out (Temporary Assistance for Needy Families, NOT TANF)

### Copy These Exact Templates

**For income limits:**
```yaml
description: [State] limits gross income to this amount under the Temporary Assistance for Needy Families program.
```

**For resource limits:**
```yaml
description: [State] limits resources to this amount under the Temporary Assistance for Needy Families program.
```

**For payment standards:**
```yaml
description: [State] provides this amount as the payment standard under the Temporary Assistance for Needy Families program.
```

**For disregards:**
```yaml
description: [State] excludes this share of earnings from countable income under the Temporary Assistance for Needy Families program.
```

### Description Validation Checklist

Run this check on EVERY description:
```python
# Pseudo-code validation
def validate_description(desc):
    checks = [
        desc.count('.') == 1,  # Exactly one sentence
        'TANF' not in desc,     # No acronyms
        'SNAP' not in desc,     # No acronyms
        'this amount' in desc or 'this share' in desc or 'this percentage' in desc,
        'under the' in desc and 'program' in desc,
        'by household size' not in desc,  # No explanatory text
        'based on' not in desc,           # No explanatory text
        'for eligibility' not in desc,    # Redundant
    ]
    return all(checks)
```

**CRITICAL: Always spell out full program names in descriptions!**

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
3. **Title: Include FULL section path** (all subsections and sub-subsections)
4. **PDF links: Add `#page=XX` at end of href ONLY** (never in title)

**Title Format - Include ALL subsection levels (NO page numbers):**
```yaml
# ❌ BAD - Too generic:
title: OAR 461-155  # Missing subsections!
title: Section 5    # Which subsection?
title: TEA Manual, page 13  # Page number belongs in href, not title!

# ✅ GOOD - Full section path, no page number:
title: OAR 461-155-0030(2)(a)(B)     # All levels included
title: 7 CFR § 273.9(d)(6)(ii)(A)    # Federal regulation with all subsections
title: Indiana Admin Code 12-14-2-3.5(b)(1)  # State admin code
title: Arkansas TEA Manual Section 5.2.3    # Manual with section (page in href)
```

**PDF Link Format - Always include page in href:**

**CRITICAL: Use the PDF file page number, NOT the printed page number inside the document.**
- The `#page=XX` value is the page position in the PDF file (1st page = 1, 2nd page = 2, etc.)
- This may differ from the page number printed on the document itself
- **Why?** When users click the link, they must land directly on the page showing the referenced values

```yaml
# ❌ BAD - No page number:
href: https://state.gov/manual.pdf

# ✅ GOOD - Page anchor in href (file page number):
href: https://humanservices.arkansas.gov/wp-content/uploads/TEA_MANUAL.pdf#page=13
href: https://adminrules.idaho.gov/rules/current/16/160503.pdf#page=8
```

**Complete Examples:**
```yaml
✅ GOOD (page number in href only):
reference:
  - title: OAR 461-155-0030(2)(a)(B)
    href: https://oregon.public.law/rules/oar_461-155-0030
  - title: Oregon DHS TANF Policy Manual Section 4.3.2
    href: https://oregon.gov/dhs/tanf-manual.pdf#page=23

✅ GOOD:
reference:
  - title: 7 CFR § 273.9(d)(6)(ii)(A)
    href: https://www.ecfr.gov/current/title-7/section-273.9#p-273.9(d)(6)(ii)(A)
  - title: Arkansas TEA Manual Section 2100
    href: https://humanservices.arkansas.gov/wp-content/uploads/TEA_MANUAL.pdf#page=45

❌ BAD (page number in title):
reference:
  - title: Arkansas TEA Manual, page 13  # Page belongs in href!
    href: https://humanservices.arkansas.gov/wp-content/uploads/TEA_MANUAL.pdf

❌ BAD (missing info):
reference:
  - title: Federal LIHEAP regulations  # Too generic - no section!
    href: https://www.acf.hhs.gov/ocs  # No specific page
  - title: OAR 461-155  # Missing subsections (2)(a)(B)!
    href: https://oregon.gov/manual.pdf  # Missing #page=XX
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

## 5.5 Parameter Folder Organization

### Core Principles

1. **Group logically** - Parameters that relate to the same aspect should be together
2. **Don't create subfolder for 1 file** - If only 1 parameter for an aspect, keep it at parent level
3. **Payment standard at root** - Main benefit amounts can stay at program root

### Common Aspects (adapt to your program)

- `income/` - Income limits, deductions, disregards
- `eligibility/` - Age thresholds, citizenship requirements
- `resources/` - Asset/resource limits

### Study Existing Implementations

Each program is different. Before organizing, look at similar programs:
```bash
ls policyengine_us/parameters/gov/states/{state}/{agency}/
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

### Age Thresholds (Simple)
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

### Age-Based Eligibility (Bracket Style) - PREFERRED

**When eligibility depends on age ranges, use a single bracket-style parameter instead of separate min/max files.**

```yaml
# eligibility/by_age.yaml
description: Massachusetts determines eligibility for the Bay Transportation reduced fare program based on age.

metadata:
  threshold_unit: year
  amount_unit: bool
  period: year
  type: single_amount
  label: Massachusetts Bay Transportation reduced fare age eligibility
  reference:
    - title: MBTA Reduced Fare Program
      href: https://www.mbta.com/fares/reduced

brackets:
  - threshold:
      2024-01-01: 0
    amount:
      2024-01-01: false    # Under 18: not eligible
  - threshold:
      2024-01-01: 18
    amount:
      2024-01-01: true     # Ages 18-64: eligible
  - threshold:
      2024-01-01: 65
    amount:
      2024-01-01: false    # 65+: not eligible (different program)
```

**Federal example (SNAP student eligibility):**
```yaml
# parameters/gov/usda/snap/student_age_eligibility_threshold.yaml
description: The United States includes students in this age range for SNAP eligibility.

brackets:
  - threshold:
      2018-01-01: 0
    amount:
      2018-01-01: true     # Under 18: eligible
  - threshold:
      2018-01-01: 18
    amount:
      2018-01-01: false    # Ages 18-49: not eligible (student restrictions)
  - threshold:
      2018-01-01: 50
    amount:
      2018-01-01: true     # 50+: eligible

metadata:
  type: single_amount
  threshold_unit: year
  amount_unit: bool
  label: SNAP student age eligibility threshold
  reference:
    - title: 7 U.S. Code § 2015 - Eligibility disqualifications
      href: https://www.law.cornell.edu/uscode/text/7/2015
```

**When to use bracket-style:**
- ✅ Eligibility varies by age range (eligible for ages X-Y only)
- ✅ Multiple age cutoffs affect the same benefit
- ✅ Boolean eligibility that changes at different thresholds
- ✅ Non-contiguous eligibility (e.g., eligible under 18 AND over 50, but not 18-49)

**When NOT to use bracket-style:**
- ❌ Single threshold (just use simple `threshold.yaml`)
- ❌ Non-boolean values that scale with age (use `single_amount` brackets with currency amounts)

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

### Bracket-Based Parameters

**CRITICAL: Handling Negative Values**

When creating bracket-based parameters (e.g., tax credits based on AGI), the first bracket threshold MUST be `-.inf` if negative values are possible, NOT `0`.

**❌ WRONG - Excludes negative AGI:**
```yaml
# threshold.yaml (for single filers)
brackets:
  - threshold:
      2023-01-01: 0      # ❌ Bug: negative AGI excluded!
    amount:
      2023-01-01: 300
  - threshold:
      2023-01-01: 30_000
    amount:
      2023-01-01: 110
```

**✅ CORRECT - Includes all possible values:**
```yaml
# threshold.yaml (for single filers)
brackets:
  - threshold:
      2023-01-01: -.inf  # ✅ Covers negative AGI
    amount:
      2023-01-01: 300
  - threshold:
      2023-01-01: 30_000
    amount:
      2023-01-01: 110
```

**When to use `-.inf`:**
- Income-based calculations (AGI can be negative)
- Any parameter where negative input values are valid
- Tax credits, deductions, or benefits based on earnings

**When `0` is appropriate:**
- Age thresholds (always non-negative)
- Count-based parameters (household size, number of dependents)
- Resource limits (assets can't be negative)

**Real-world example:** Hawaii Food/Excise Tax Credit uses AGI brackets. The first threshold must be `-.inf` to correctly handle taxpayers with negative AGI (e.g., business losses).

### Parameter Structure Transitions (Flat → Bracket)

**When a parameter changes structure over time** (e.g., a flat rate becomes a tiered/marginal rate in a later year), you CANNOT put both structures in a single YAML file. Instead, split into separate files with a boolean toggle.

**Problem:** A single `rate.yaml` with marginal brackets would retroactively apply the tiered structure to years that had a flat rate.

**Solution:** Create a `rate/` folder with three files:

```
rate/
├── flat.yaml           # The original flat-rate value
├── incremental.yaml    # The new bracket/marginal structure
└── flat_applies.yaml   # Boolean toggle: true = use flat, false = use brackets
```

**`rate/flat.yaml`** — The original single-value parameter:
```yaml
description: Washington taxes long-term capital gains at this rate.
values:
  2022-01-01: 0.07

metadata:
  unit: /1
  period: year
  label: Washington flat capital gains tax rate
  reference:
    - title: RCW 82.87.040(1) Tax imposed—Long-term capital assets
      href: https://app.leg.wa.gov/RCW/default.aspx?cite=82.87.040
```

**`rate/incremental.yaml`** — The new bracket structure:
```yaml
description: Washington taxes long-term capital gains at these marginal rates.
brackets:
  - threshold:
      2022-01-01: 0
    rate:
      2022-01-01: 0.07
  - threshold:
      2025-01-01: 1_000_000
    rate:
      2025-01-01: 0.099

metadata:
  threshold_unit: currency-USD
  rate_unit: /1
  threshold_period: year
  type: marginal_rate
  label: Washington marginal capital gains tax rate
  reference:
    - title: RCW 82.87.040(1)-(2) Tax imposed—Long-term capital assets
      href: https://app.leg.wa.gov/RCW/default.aspx?cite=82.87.040
    - title: ESSB 5813, Chapter 421, Laws of 2025, Sec. 101
      href: https://lawfilesext.leg.wa.gov/biennium/2025-26/Htm/Bills/Session%20Laws/Senate/5813-S.SL.htm
```

**`rate/flat_applies.yaml`** — The boolean toggle:
```yaml
description: Washington uses this indicator to determine whether the flat capital gains tax rate applies.
values:
  2022-01-01: true
  2025-01-01: false

metadata:
  unit: bool
  period: year
  label: Washington flat capital gains tax rate applies
  reference:
    - title: RCW 82.87.040(1) Tax imposed—Long-term capital assets
      href: https://app.leg.wa.gov/RCW/default.aspx?cite=82.87.040
    - title: ESSB 5813, Chapter 421, Laws of 2025, Sec. 101
      href: https://lawfilesext.leg.wa.gov/biennium/2025-26/Htm/Bills/Session%20Laws/Senate/5813-S.SL.htm
```

**When to use this pattern:**
- ✅ A flat rate becomes a marginal bracket schedule
- ✅ A single value becomes a lookup table by household size
- ✅ Any parameter whose YAML structure type changes at a specific date

**When NOT to use this pattern:**
- ❌ Values change but the structure stays the same (just add a new date entry)
- ❌ A new bracket is added to an existing bracket structure (see below)

**See variable patterns skill for the corresponding variable-side logic (`if p.rate.flat_applies`).**

### Adding New Brackets to Existing Scales

**When a new bracket is added to an existing scale in a later year**, you CANNOT simply add the bracket with only the new year's date — the bracket would have no defined threshold/amount for prior years, breaking the scale.

**Solution:** Add the new bracket with its threshold set to `.inf` (or `-.inf` for rate brackets starting from the bottom) for the base year. This makes the bracket structurally present for all years but **functionally unreachable** before the year it takes effect.

**Example: Ohio personal exemption phase-out (HB 96)**

Ohio's personal exemption had 3 brackets (by AGI). Starting 2025, a 4th bracket phases the exemption to $0 at high incomes ($750k in 2025, $500k in 2026+):

```yaml
brackets:
  - threshold:
      2021-01-01: 0
    amount:
      2021-01-01: 2_400
  - threshold:
      2021-01-01: 40_001
    amount:
      2021-01-01: 2_150
  - threshold:
      2021-01-01: 80_001
    amount:
      2021-01-01: 1_900
  # New bracket: use .inf for base year so pre-2025 is unaffected
  - threshold:
      2021-01-01: .inf         # Pre-2025: unreachable → bracket is inert
      2025-01-01: 750_000      # 2025: phase-out at $750k
      2026-01-01: 500_000      # 2026+: phase-out drops to $500k
    amount:
      2021-01-01: 0            # $0 exemption above threshold
```

**Why `.inf` works:**
- For pre-2025 periods, no income can reach `.inf`, so the bracket never activates
- Starting 2025, the threshold becomes a real value ($750k) and the bracket takes effect
- The scale remains structurally valid across all time periods

**Another example: Ohio joint filing credit MAGI cap**

```yaml
brackets:
  - threshold:
      2021-01-01: 0
    amount:
      2021-01-01: 0.2
  - threshold:
      2021-01-01: 25_000
    amount:
      2021-01-01: 0.15
  - threshold:
      2021-01-01: 50_000
    amount:
      2021-01-01: 0.1
  - threshold:
      2021-01-01: 75_000
    amount:
      2021-01-01: 0.05
  # New bracket: MAGI cap added by HB 96
  - threshold:
      2021-01-01: .inf
      2025-01-01: 750_000
      2026-01-01: 500_000
    amount:
      2021-01-01: 0
```

**When to use `.inf` for new brackets:**
- ✅ A new upper bracket is added in a later year (cap, phase-out, new rate tier)
- ✅ The bracket should not affect calculations for prior years
- ✅ The new bracket sets a value to zero (phase-out) or introduces a new rate

**When NOT to use this pattern:**
- ❌ The bracket existed in all prior years too (just add it normally with the base date)
- ❌ The parameter structure type itself changes (use the flat→bracket transition pattern above)

**Real-world reference:** [policyengine-us PR #7107](https://github.com/PolicyEngine/policyengine-us/pull/7107) — Ohio 2025 income tax update (HB 96 personal exemption and joint filing credit MAGI caps).

### Choosing Between the Three Boolean Toggle Approaches

The **flat→bracket transition**, **`.inf` new bracket**, and **`in_effect` provision gating** patterns all handle parameters that change over time, but they solve different problems:

| | Flat→Bracket Transition | `.inf` New Bracket | `in_effect` Provision Gating |
|---|---|---|---|
| **Problem** | Structure type changes (flat → brackets) | New bracket added to existing scale | A provision starts or ends at a specific date |
| **Parameter side** | Split into folder + boolean toggle | Add bracket with `.inf` threshold | Single `in_effect.yaml` boolean |
| **Variable side** | `if p.toggle:` to choose access method | No changes — `.calc()` works | `if p.in_effect:` gates entire logic block |
| **Example** | WA capital gains: flat 7% → tiered 7%/9.9% | OH exemptions: 3→4 brackets | CT TFA high earnings reduction (new in 2024) |

### Provision Gating with `in_effect` Boolean

**When a provision starts (or ends) at a specific date**, create a boolean parameter that gates the entire logic block in the variable formula. This is different from `flat_applies` — it doesn't switch between two parameter access methods, it controls whether a block of logic runs at all.

**Use case:** A new program feature is added by legislation (e.g., a high-earnings reduction that didn't exist before 2024), or an existing feature is repealed.

**`in_effect.yaml`** — Boolean that tracks when the provision is active:
```yaml
# e.g., payment/high_earnings/in_effect.yaml
description: Connecticut uses this indicator to determine whether the high-earnings benefit reduction applies under the Temporary Family Assistance program.

values:
  1997-01-01: false
  2024-01-01: true

metadata:
  unit: bool
  period: month
  label: Connecticut TFA high earnings reduction in effect
  reference:
    - title: State of Connecticut TANF State Plan 2024-2026, High Earnings Provision
      href: https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/state-plans-and-federal-reports/tanf-state-plan/ct-tanf-state-plan-2024---2026---41524-amendment.pdf#page=10
    - title: Connecticut General Statutes § 17b-112(d)
      href: https://cga.ct.gov/current/pub/chap_319s.htm#sec_17b-112
```

**Sibling parameters** — The provision's actual values live alongside `in_effect.yaml`:
```
payment/high_earnings/
├── in_effect.yaml      # false before 2024, true from 2024
├── rate.yaml            # FPL multiplier threshold (e.g., 0.75)
└── reduction_rate.yaml  # Benefit reduction rate (e.g., 0.25)
```

**See variable patterns skill for the corresponding variable-side logic (`if p.high_earnings.in_effect:`).**

**When to use this pattern:**
- ✅ A new provision is added by legislation at a specific date
- ✅ An existing provision is repealed at a specific date
- ✅ The provision gates an entire block of logic (not just a parameter access method)
- ✅ The provision has its own sub-parameters (rates, thresholds) that only make sense when active

**When NOT to use this pattern:**
- ❌ The parameter structure itself changes (use flat→bracket transition)
- ❌ A new bracket is added to an existing scale (use `.inf` pattern)
- ❌ A simple value changes over time (just add a new date entry)

### Regional Variation with `regional_in_effect` Boolean

**When a program has regional payment variations that start or end at a specific date**, create a boolean that switches between regional lookup and a flat statewide amount.

**Use case:** A state originally had different payment standards by region, then consolidated to a single statewide amount (or vice versa).

**`regional_in_effect.yaml`** — Boolean that tracks when regional variation applies:
```yaml
# e.g., payment/regional_in_effect.yaml
description: Connecticut uses this indicator to determine whether regional payment standards apply under the Temporary Family Assistance program.

values:
  1997-01-01: true
  2022-07-01: false

metadata:
  unit: bool
  period: month
  label: Connecticut TFA regional payment standards in effect
  reference:
    - title: Connecticut General Statutes § 17b-104(c)
      href: https://cga.ct.gov/current/pub/chap_319s.htm#sec_17b-104
    - title: State of Connecticut TANF State Plan 2021-2023
      href: https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/state-plans-and-federal-reports/tanf-state-plan/ct-tanf-plan-2021-2023--draft.pdf#page=57
```

**Folder structure** — Regional amounts AND the flat statewide amount coexist:
```
payment/
├── regional_in_effect.yaml          # true before 2022-07, false after
├── regional/
│   ├── region_a/amount.yaml         # Regional amounts (by household size)
│   ├── region_b/amount.yaml
│   └── region_c/amount.yaml
├── amount.yaml                      # Flat statewide amount (used when regional_in_effect is false)
└── max_unit_size.yaml
```

**See variable patterns skill for the corresponding variable-side logic (`if p.regional_in_effect:`).**

**When to use this pattern:**
- ✅ A program transitions from regional to statewide payment standards (or vice versa)
- ✅ Regional variation is controlled by legislation at a specific date
- ✅ The regional and flat structures are fundamentally different (enum lookup vs simple index)

**When NOT to use this pattern:**
- ❌ Regional variation always applies (just use the regional parameters directly)
- ❌ The variation is by household characteristic, not geographic region (use `where()` in variable)

**Real-world reference:** Connecticut TFA payment standards — regional (Region A/B/C) before July 2022, flat statewide amount after.

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

## Real-World Examples from Production Code

**CRITICAL: Study actual parameter files, not just examples!**

Before writing ANY parameter:
1. Open and READ 3+ similar parameter files from TX/IL/DC
2. COPY their exact description pattern
3. Replace state name and specific details only

### Payment Standards
```yaml
# Texas (actual production)
description: Texas provides this amount as the payment standard under the Temporary Assistance for Needy Families program.

# Pennsylvania (actual production)
description: Pennsylvania limits TANF benefits to households with resources at or below this amount.
```

### Income Limits
```yaml
# Indiana (should be)
description: Indiana limits gross income to this amount under the Temporary Assistance for Needy Families program.

# Texas (actual production)
description: Texas limits countable resources to this amount under the Temporary Assistance for Needy Families program.
```

### Disregards
```yaml
# Indiana (should be)
description: Indiana excludes this share of earnings from countable income under the Temporary Assistance for Needy Families program.

# Texas (actual production)
description: Texas deducts this standard work expense amount from gross earned income for Temporary Assistance for Needy Families program calculations.
```

### Pattern Analysis
- **ALWAYS** spell out full program name
- Use "under the [Program] program" or "for [Program] program calculations"
- One simple verb (limits, provides, excludes, deducts)
- One "this X" placeholder
- NO extra explanation ("based on X", "This is Y")

### Common Description Mistakes to AVOID

**❌ WRONG - Using acronyms:**
```yaml
description: Indiana sets this gross income limit for TANF eligibility by household size.
# Problems: "TANF" not spelled out, unnecessary "by household size"
```

**✅ CORRECT:**
```yaml
description: Indiana limits gross income to this amount under the Temporary Assistance for Needy Families program.
```

**❌ WRONG - Adding explanatory text:**
```yaml
description: Indiana provides this payment standard amount based on household size.
# Problem: "based on household size" is unnecessary (evident from breakdown)
```

**✅ CORRECT:**
```yaml
description: Indiana provides this amount as the payment standard under the Temporary Assistance for Needy Families program.
```

**❌ WRONG - Missing program context:**
```yaml
description: Indiana sets the gross income limit.
# Problem: No program name, no "this amount"
```

**✅ CORRECT:**
```yaml
description: Indiana limits gross income to this amount under the Temporary Assistance for Needy Families program.
```

### Authoritative Source Requirements

**ONLY use official government sources:**
- ✅ State codes and administrative regulations
- ✅ Official state agency websites (.gov domains)
- ✅ Federal regulations (CFR, USC)
- ✅ State plans and official manuals (.gov PDFs)

**NEVER use:**
- ❌ Third-party guides (singlemotherguide.com, benefits.gov descriptions)
- ❌ Wikipedia
- ❌ Nonprofit summaries (unless no official source exists)
- ❌ News articles

---

## For Agents

When creating parameters:
1. **READ ACTUAL FILES** - Study TX/IL/DC parameter files, not just skill examples
2. **Include ALL metadata fields** - missing any causes errors
3. **Use exact effective dates** from sources
4. **Follow naming conventions** (amount/rate/threshold)
5. **Write simple descriptions** with "this" placeholders and full program names
6. **Include ONLY official government references** with subsections and pages
7. **Format values properly** (underscores, no trailing zeros)