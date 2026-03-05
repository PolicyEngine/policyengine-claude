# Period patterns

Detailed patterns for handling YEAR, MONTH, and ETERNITY periods in PolicyEngine.

## Quick reference

| From | To | Method |
|------|-----|--------|
| MONTH formula | YEAR variable | `period.this_year` |
| YEAR formula | MONTH variable | `period.first_month` |
| Any | Year integer | `period.start.year` |
| Any | Month integer | `period.start.month` |

## The golden rule

When accessing a variable with a different definition period, specify the target period explicitly.

```python
# ✅ CORRECT - MONTH formula accessing YEAR variable
age = person("age", period.this_year)  # Gets actual age

# ❌ WRONG - Would get age/12
age = person("age", period)  # BAD: gives age divided by 12!
```

## Auto-conversion: period vs period.this_year

**Key question:** When accessing a YEAR variable from a MONTH formula, should the value be divided by 12?

| Variable Type | Use `period` | Use `period.this_year` | Why |
|--------------|-------------|----------------------|-----|
| Income (flow) | ✅ | ❌ | Want monthly portion |
| Age | ❌ | ✅ | Age/12 is meaningless |
| Assets/Resources | ❌ | ✅ | Point-in-time value |
| Household size/counts | ❌ | ✅ | Can't divide people |
| Boolean/status flags | ❌ | ✅ | True/12 is nonsense |

## Complete example

```python
class monthly_tanf_eligible(Variable):
    definition_period = MONTH

    def formula(person, period, parameters):
        age = person("age", period.this_year)          # ✅ Stock
        assets = person("assets", period.this_year)    # ✅ Stock
        monthly_income = person("employment_income", period)  # ✅ Flow

        p = parameters(period).gov.tanf.eligibility
        return (
            (age >= 18) & (age <= 64) &
            (assets <= p.asset_limit) &
            (monthly_income <= p.monthly_income_limit)
        )
```

## Redundant conversion mistake

```python
# ❌ WRONG - Double-converting
fpg = spm_unit("spm_unit_fpg", period.this_year) / MONTHS_IN_YEAR

# ✅ CORRECT - Core auto-converts when you use period
fpg = spm_unit("spm_unit_fpg", period)
```

## Parameter access

```python
# Standard: parameters use formula's period
p = parameters(period).gov.program.benefit

# Specific date
p = parameters("2024-10-01").gov.hhs.fpg

# NEVER use parameters(period.this_year)
```

## Testing with periods

**For MONTH period tests** (`period: 2025-01`):
- **Input** YEAR variables as **annual amounts**
- **Output** YEAR variables show **monthly values** (÷12)

```yaml
- name: Case 1, monthly test.
  period: 2025-01
  input:
    employment_income: 12_000  # Annual input
  output:
    employment_income: 1_000   # Monthly output (12_000/12)
```

### Input/output rules

| Variable Def | Test Period | Input | Output |
|--------------|-------------|-------|--------|
| YEAR | YEAR | Yearly | Yearly |
| YEAR | MONTH | Yearly | Monthly (÷12) |
| MONTH | YEAR | Yearly (÷12/month) | Yearly (sum) |
| MONTH | MONTH | Monthly | Monthly |

### Formula design: never multiply by 12

Let PolicyEngine handle conversion automatically. Never use `* MONTHS_IN_YEAR` in formulas.

## Common variables needing period.this_year

`age`, `household_size`, `spm_unit_size`, `cash_assets`, `vehicles_value`, `state_name`, `state_code`, and any demographic variable.
