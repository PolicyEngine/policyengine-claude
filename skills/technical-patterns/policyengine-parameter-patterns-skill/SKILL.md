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
4. **PDF links: Add `#page=XX` at end**

**Title Format - Include ALL subsection levels:**
```yaml
# ❌ BAD - Too generic:
title: OAR 461-155  # Missing subsections!
title: Section 5    # Which subsection?

# ✅ GOOD - Full section path:
title: OAR 461-155-0030(2)(a)(B)     # All levels included
title: 7 CFR § 273.9(d)(6)(ii)(A)    # Federal regulation with all subsections
title: Indiana Admin Code 12-14-2-3.5(b)(1)  # State admin code
title: Oregon TANF Policy Manual Section 5.2.3.1, page 15  # Manual with subsection
```

**PDF Link Format - Always include page:**
```yaml
# ❌ BAD - No page number:
href: https://state.gov/manual.pdf

# ✅ GOOD - Page anchor included:
href: https://state.gov/manual.pdf#page=14
href: https://adminrules.idaho.gov/rules/current/16/160503.pdf#page=8
```

**Complete Examples:**
```yaml
✅ GOOD:
reference:
  - title: OAR 461-155-0030(2)(a)(B)
    href: https://oregon.public.law/rules/oar_461-155-0030
  - title: Oregon DHS TANF Policy Manual Section 4.3.2.1, page 23
    href: https://oregon.gov/dhs/tanf-manual.pdf#page=23

✅ GOOD:
reference:
  - title: 7 CFR § 273.9(d)(6)(ii)(A)
    href: https://www.ecfr.gov/current/title-7/section-273.9#p-273.9(d)(6)(ii)(A)
  - title: Indiana Admin Code 12-14-2-3.5(b)(1)
    href: https://www.in.gov/dcs/files/tanf-manual.pdf#page=45

❌ BAD:
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