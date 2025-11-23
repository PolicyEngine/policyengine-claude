---
name: policyengine-implementation-patterns
description: PolicyEngine implementation patterns - variable creation, no hard-coding principle, federal/state separation, metadata standards
---

# PolicyEngine Implementation Patterns

Essential patterns for implementing government benefit program rules in PolicyEngine.

## Critical Principles

### 1. ZERO Hard-Coded Values
**Every numeric value MUST be parameterized**

```python
❌ FORBIDDEN:
return where(eligible, 1000, 0)     # Hard-coded 1000
age < 15                             # Hard-coded 15
benefit = income * 0.33              # Hard-coded 0.33
month >= 10 and month <= 3           # Hard-coded months

✅ REQUIRED:
return where(eligible, p.maximum_benefit, 0)
age < p.age_threshold.minor_child
benefit = income * p.benefit_rate
month >= p.season.start_month
```

**Acceptable literals:**
- `0`, `1`, `-1` for basic math
- `12` for month conversion (`/ 12`, `* 12`)
- Array indices when structure is known

### 2. No Placeholder Implementations
**Delete the file rather than leave placeholders**

```python
❌ NEVER:
def formula(entity, period, parameters):
    # TODO: Implement
    return 75  # Placeholder

✅ ALWAYS:
# Complete implementation or no file at all
```

---

## Variable Implementation Standards

### Variable Metadata Format

Follow established patterns:
```python
class il_tanf_countable_earned_income(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    label = "Illinois TANF countable earned income"
    unit = USD
    reference = "https://www.law.cornell.edu/regulations/illinois/..."
    defined_for = StateCode.IL

    # Use adds for simple sums
    adds = ["il_tanf_earned_income_after_disregard"]
```

**Key rules:**
- ✅ Use full URL in `reference` (clickable)
- ❌ Don't use `documentation` field
- ❌ Don't use statute citations without URLs

### When to Use `adds` vs `formula`

**Use `adds` when:**
- Just summing variables
- Passing through a single variable
- No transformations needed

```python
✅ BEST - Simple sum:
class tanf_gross_income(Variable):
    adds = ["employment_income", "self_employment_income"]
```

**Use `formula` when:**
- Applying transformations
- Conditional logic
- Calculations needed

```python
✅ CORRECT - Need logic:
def formula(entity, period, parameters):
    income = add(entity, period, ["income1", "income2"])
    return max_(0, income)  # Need max_
```

---

## Federal/State Separation

### Federal Parameters
Location: `/parameters/gov/{agency}/`
- Base formulas and methodologies
- National standards
- Required elements

### State Parameters
Location: `/parameters/gov/states/{state}/`
- State-specific thresholds
- Implementation choices
- Scale factors

```yaml
# Federal: parameters/gov/hhs/fpg/base.yaml
first_person: 14_580

# State: parameters/gov/states/ca/scale_factor.yaml
fpg_multiplier: 2.0  # 200% of FPG
```

---

## Code Reuse Patterns

### Avoid Duplication - Create Intermediate Variables

**❌ ANTI-PATTERN: Copy-pasting calculations**
```python
# File 1: calculates income after deduction
def formula(household, period, parameters):
    gross = add(household, period, ["income"])
    deduction = p.deduction * household.nb_persons()
    return max_(gross - deduction, 0)

# File 2: DUPLICATES same calculation
def formula(household, period, parameters):
    gross = add(household, period, ["income"])  # Copy-pasted
    deduction = p.deduction * household.nb_persons()  # Copy-pasted
    after_deduction = max_(gross - deduction, 0)  # Copy-pasted
    return after_deduction < p.threshold
```

**✅ CORRECT: Reuse existing variables**
```python
# File 2: reuses calculation
def formula(household, period, parameters):
    countable_income = household("program_countable_income", period)
    return countable_income < p.threshold
```

**When to create intermediate variables:**
- Same calculation in 2+ places
- Logic exceeds 5 lines
- Reference implementations have similar variable

---

## TANF-Specific Patterns

### Study Reference Implementations First

**MANDATORY before implementing any TANF:**
- DC TANF: `/variables/gov/states/dc/dhs/tanf/`
- IL TANF: `/variables/gov/states/il/dhs/tanf/`
- TX TANF: `/variables/gov/states/tx/hhs/tanf/`

**Learn from them:**
1. Variable organization
2. Naming conventions
3. Code reuse patterns
4. When to use `adds` vs `formula`

### Standard TANF Structure
```
tanf/
├── eligibility/
│   ├── demographic_eligible.py
│   ├── income_eligible.py
│   └── eligible.py
├── income/
│   ├── earned/
│   ├── unearned/
│   └── countable_income.py
└── [state]_tanf.py
```

### Simplified TANF Rules

For simplified implementations:

**DON'T create state-specific versions of:**
- Demographic eligibility (use federal)
- Immigration eligibility (use federal)
- Income sources (use federal baseline)

```python
❌ DON'T CREATE:
ca_tanf_demographic_eligible_person.py
ca_tanf_gross_earned_income.py
parameters/.../income/sources/earned.yaml

✅ DO USE:
# Federal demographic eligibility
is_demographic_tanf_eligible
# Federal income aggregation
tanf_gross_earned_income
```

### Demographic Eligibility Pattern

**Option 1: Use Federal (Simplified)**
```python
class ca_tanf_eligible(Variable):
    def formula(spm_unit, period, parameters):
        # Use federal variable
        has_eligible = spm_unit.any(
            spm_unit.members("is_demographic_tanf_eligible", period)
        )
        return has_eligible & income_eligible
```

**Option 2: State-Specific (Different thresholds)**
```python
class ca_tanf_demographic_eligible_person(Variable):
    def formula(person, period, parameters):
        p = parameters(period).gov.states.ca.tanf
        age = person("age", period.this_year)  # NOT monthly_age

        age_limit = where(
            person("is_full_time_student", period),
            p.age_threshold.student,
            p.age_threshold.minor_child
        )
        return age < age_limit
```

---

## Common Implementation Patterns

### Income Eligibility
```python
class program_income_eligible(Variable):
    value_type = bool
    entity = SPMUnit
    definition_period = MONTH

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.xx.program
        income = spm_unit("program_countable_income", period)
        size = spm_unit("spm_unit_size", period.this_year)

        # Get threshold from parameters
        threshold = p.income_limit[min_(size, p.max_household_size)]
        return income <= threshold
```

### Benefit Calculation
```python
class program_benefit(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    unit = USD

    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.xx.program
        eligible = spm_unit("program_eligible", period)

        # Calculate benefit amount
        base = p.benefit_schedule.base_amount
        adjustment = p.benefit_schedule.adjustment_rate
        size = spm_unit("spm_unit_size", period.this_year)

        amount = base + (size - 1) * adjustment
        return where(eligible, amount, 0)
```

### Using Scale Parameters
```python
def formula(entity, period, parameters):
    p = parameters(period).gov.states.az.program
    federal_p = parameters(period).gov.hhs.fpg

    # Federal base with state scale
    size = entity("household_size", period.this_year)
    fpg = federal_p.first_person + federal_p.additional * (size - 1)
    state_scale = p.income_limit_scale  # Often exists
    income_limit = fpg * state_scale
```

---

## Variable Creation Checklist

Before creating any variable:
- [ ] Check if it already exists
- [ ] Use standard demographic variables (age, is_disabled)
- [ ] Reuse federal calculations where applicable
- [ ] Check for household_income before creating new
- [ ] Look for existing intermediate variables
- [ ] Study reference implementations

---

## Quality Standards

### Complete Implementation Requirements
- All values from parameters (no hard-coding)
- Complete formula logic
- Proper entity aggregation
- Correct period handling
- Meaningful variable names
- Proper metadata

### Anti-Patterns to Avoid
- Copy-pasting logic between files
- Hard-coding any numeric values
- Creating duplicate income variables
- State-specific versions of federal rules
- Placeholder TODOs in production code

---

## For Agents

When implementing variables:
1. **Study reference implementations** (DC, IL, TX TANF)
2. **Never hard-code values** - use parameters
3. **Reuse existing variables** - avoid duplication
4. **Use `adds` when possible** - cleaner than formula
5. **Create intermediate variables** for complex logic
6. **Follow metadata standards** exactly
7. **Complete implementation** or delete the file