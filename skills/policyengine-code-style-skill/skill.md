---
name: policyengine-code-style
description: PolicyEngine code writing style guide - formula optimization, direct returns, eliminating unnecessary variables
---

# PolicyEngine Code Writing Style Guide

Essential patterns for writing clean, efficient PolicyEngine formulas.

## Core Principles

1. **Eliminate unnecessary intermediate variables**
2. **Use direct parameter/variable access**
3. **Return directly when possible**
4. **Combine boolean logic**
5. **Use correct period access** (period vs period.this_year)
6. **NO hardcoded values** - use parameters or constants

---

## Pattern 1: Direct Parameter Access

### ❌ Bad - Unnecessary intermediate variable

```python
def formula(spm_unit, period, parameters):
    countable = spm_unit("tn_tanf_countable_resources", period)
    p = parameters(period).gov.states.tn.dhs.tanf.resource_limit
    resource_limit = p.amount  # ❌ Unnecessary
    return countable <= resource_limit
```

### ✅ Good - Direct access

```python
def formula(spm_unit, period, parameters):
    countable = spm_unit("tn_tanf_countable_resources", period)
    p = parameters(period).gov.states.tn.dhs.tanf.resource_limit
    return countable <= p.amount
```

---

## Pattern 2: Direct Return

### ❌ Bad - Unnecessary result variable

```python
def formula(spm_unit, period, parameters):
    assets = spm_unit("spm_unit_assets", period.this_year)
    p = parameters(period).gov.states.tn.dhs.tanf.resource_limit
    vehicle_exemption = p.vehicle_exemption  # ❌ Unnecessary
    countable = max_(assets - vehicle_exemption, 0)  # ❌ Unnecessary
    return countable
```

### ✅ Good - Direct return

```python
def formula(spm_unit, period, parameters):
    assets = spm_unit("spm_unit_assets", period.this_year)
    p = parameters(period).gov.states.tn.dhs.tanf.resource_limit
    return max_(assets - p.vehicle_exemption, 0)
```

---

## Pattern 3: Combined Boolean Logic

### ❌ Bad - Too many intermediate booleans

```python
def formula(spm_unit, period, parameters):
    person = spm_unit.members
    age = person("age", period.this_year)
    is_disabled = person("is_disabled", period.this_year)

    caretaker_is_60_or_older = spm_unit.any(age >= 60)  # ❌ Unnecessary
    caretaker_is_disabled = spm_unit.any(is_disabled)   # ❌ Unnecessary
    eligible = caretaker_is_60_or_older | caretaker_is_disabled  # ❌ Unnecessary

    return eligible
```

### ✅ Good - Combined logic

```python
def formula(spm_unit, period, parameters):
    person = spm_unit.members
    age = person("age", period.this_year)
    is_disabled = person("is_disabled", period.this_year)

    return spm_unit.any((age >= 60) | is_disabled)
```

---

## Pattern 4: Period Access - period vs period.this_year

### ❌ Bad - Wrong period access

```python
def formula(person, period, parameters):
    # MONTH formula accessing YEAR variables
    age = person("age", period)  # ❌ Gives age/12 = 2.5 "monthly age"
    assets = person("assets", period)  # ❌ Gives assets/12
    monthly_income = person("employment_income", period.this_year) / MONTHS_IN_YEAR  # ❌ Redundant

    return (age >= 18) & (assets < 10000) & (monthly_income < 2000)
```

### ✅ Good - Correct period access

```python
def formula(person, period, parameters):
    # MONTH formula accessing YEAR variables
    age = person("age", period.this_year)  # ✅ Gets actual age (30)
    assets = person("assets", period.this_year)  # ✅ Gets actual assets ($10,000)
    monthly_income = person("employment_income", period)  # ✅ Auto-converts to monthly

    p = parameters(period).gov.program.eligibility
    return (age >= p.age_min) & (age <= p.age_max) &
           (assets < p.asset_limit) & (monthly_income < p.income_threshold)
```

**Rule:**
- Income/flows → Use `period` (want monthly from annual)
- Age/assets/counts/booleans → Use `period.this_year` (don't divide by 12)

---

## Pattern 5: No Hardcoded Values

### ❌ Bad - Hardcoded numbers

```python
def formula(spm_unit, period, parameters):
    size = spm_unit.nb_persons()
    capped_size = min_(size, 10)  # ❌ Hardcoded

    age = person("age", period.this_year)
    income = person("income", period) / 12  # ❌ Use MONTHS_IN_YEAR

    # ❌ Hardcoded thresholds
    if age >= 18 and age <= 65 and income < 2000:
        return True
```

### ✅ Good - Parameterized

```python
def formula(spm_unit, period, parameters):
    p = parameters(period).gov.program
    capped_size = min_(spm_unit.nb_persons(), p.max_unit_size)  # ✅

    age = person("age", period.this_year)
    monthly_income = person("income", period)  # ✅ Auto-converts (no manual /12)

    age_eligible = (age >= p.age_min) & (age <= p.age_max)  # ✅
    income_eligible = monthly_income < p.income_threshold  # ✅

    return age_eligible & income_eligible
```

---

## Pattern 6: Streamline Variable Access

### ❌ Bad - Redundant steps

```python
def formula(spm_unit, period, parameters):
    unit_size = spm_unit.nb_persons()  # ❌ Unnecessary
    max_size = 10  # ❌ Hardcoded
    capped_size = min_(unit_size, max_size)

    p = parameters(period).gov.states.tn.dhs.tanf.benefit
    spa = p.standard_payment_amount[capped_size]  # ❌ Unnecessary
    dgpa = p.differential_grant_payment_amount[capped_size]  # ❌ Unnecessary

    eligible = spm_unit("eligible_for_dgpa", period)
    return where(eligible, dgpa, spa)
```

### ✅ Good - Streamlined

```python
def formula(spm_unit, period, parameters):
    p = parameters(period).gov.states.tn.dhs.tanf.benefit
    capped_size = min_(spm_unit.nb_persons(), p.max_unit_size)
    eligible = spm_unit("eligible_for_dgpa", period)

    return where(
        eligible,
        p.differential_grant_payment_amount[capped_size],
        p.standard_payment_amount[capped_size]
    )
```

---

## When to Keep Intermediate Variables

### ✅ Keep when value is used multiple times

```python
def formula(tax_unit, period, parameters):
    p = parameters(period).gov.irs.credits
    filing_status = tax_unit("filing_status", period)

    # ✅ Used multiple times - keep as variable
    threshold = p.phase_out.start[filing_status]

    income = tax_unit("adjusted_gross_income", period)
    excess = max_(0, income - threshold)
    reduction = (excess / p.phase_out.width) * threshold

    return max_(0, threshold - reduction)
```

### ✅ Keep when calculation is complex

```python
def formula(spm_unit, period, parameters):
    p = parameters(period).gov.program
    gross_earned = spm_unit("gross_earned_income", period)

    # ✅ Complex multi-step calculation - break it down
    work_expense_deduction = min_(gross_earned * p.work_expense_rate, p.work_expense_max)
    after_work_expense = gross_earned - work_expense_deduction

    earned_disregard = after_work_expense * p.earned_disregard_rate
    countable_earned = after_work_expense - earned_disregard

    dependent_care = spm_unit("dependent_care_expenses", period)

    return max_(0, countable_earned - dependent_care)
```

---

## Complete Example: Before vs After

### ❌ Before - Multiple Issues

```python
def formula(person, period, parameters):
    # Wrong period access
    age = person("age", period)  # ❌ age/12
    assets = person("assets", period)  # ❌ assets/12
    annual_income = person("employment_income", period.this_year)
    monthly_income = annual_income / 12  # ❌ Use MONTHS_IN_YEAR

    # Hardcoded values
    min_age = 18  # ❌
    max_age = 64  # ❌
    asset_limit = 10000  # ❌
    income_limit = 2000  # ❌

    # Unnecessary intermediate variables
    age_check = (age >= min_age) & (age <= max_age)
    asset_check = assets <= asset_limit
    income_check = monthly_income <= income_limit
    eligible = age_check & asset_check & income_check

    return eligible
```

### ✅ After - Clean and Correct

```python
def formula(person, period, parameters):
    p = parameters(period).gov.program.eligibility

    # Correct period access
    age = person("age", period.this_year)
    assets = person("assets", period.this_year)
    monthly_income = person("employment_income", period)

    # Direct return with combined logic
    return (
        (age >= p.age_min) & (age <= p.age_max) &
        (assets <= p.asset_limit) &
        (monthly_income <= p.income_threshold)
    )
```

---

## Quick Checklist

Before finalizing code:
- [ ] No hardcoded numbers (use parameters or constants like MONTHS_IN_YEAR)
- [ ] Correct period access:
  - Income/flows use `period`
  - Age/assets/counts/booleans use `period.this_year`
- [ ] No single-use intermediate variables
- [ ] Direct parameter access (`p.amount` not `amount = p.amount`)
- [ ] Direct returns when possible
- [ ] Combined boolean logic when possible

---

## Key Takeaways

1. **Less is more** - Eliminate unnecessary variables
2. **Direct is better** - Access parameters and return directly
3. **Combine when logical** - Group related boolean conditions
4. **Keep when needed** - Complex calculations and reused values deserve variables
5. **Period matters** - Use correct period access to avoid auto-conversion bugs

---

## Related Skills

- **policyengine-period-patterns-skill** - Deep dive on period handling
- **policyengine-implementation-patterns-skill** - Variable structure and patterns
- **policyengine-vectorization-skill** - NumPy operations and vectorization

---

## For Agents

When writing or reviewing formulas:
1. **Scan for single-use variables** - eliminate them
2. **Check period access** - ensure correct for variable type
3. **Look for hardcoded values** - parameterize them
4. **Identify redundant steps** - streamline them
5. **Consider readability** - keep complex calculations clear