---
name: policyengine-implementation-patterns
description: PolicyEngine implementation patterns - variable creation, no hard-coding principle, federal/state separation, metadata standards
---

# PolicyEngine Implementation Patterns

Essential patterns for implementing government benefit program rules in PolicyEngine.

## PolicyEngine Architecture Constraints

### What CANNOT Be Simulated (Single-Period Limitation)

**CRITICAL: PolicyEngine uses single-period simulation architecture**

The following CANNOT be implemented and should be SKIPPED when found in documentation:

#### 1. Time Limits and Lifetime Counters
**Cannot simulate:**
- ANY lifetime benefit limits (X months total)
- ANY time windows (X months within Y period)
- Benefit clocks and countable months
- Cumulative time tracking

**Why:** Requires tracking benefit history across multiple periods. PolicyEngine simulates one period at a time with no state persistence.

**What to do:** Document in comments but DON'T parameterize or implement:
```python
# NOTE: [State] has [X]-month lifetime limit on [Program] benefits
# This cannot be simulated in PolicyEngine's single-period architecture
```

#### 2. Work History Requirements
**Cannot simulate:**
- "Must have worked 6 of last 12 months"
- "Averaged 30 hours/week over past quarter"
- Prior employment verification
- Work participation rate tracking

**Why:** Requires historical data from previous periods.

#### 3. Waiting Periods and Benefit Delays
**Cannot simulate:**
- "3-month waiting period for new residents"
- "Benefits start month after application"
- Retroactive eligibility
- Benefit recertification cycles

**Why:** Requires tracking application dates and eligibility history.

#### 4. Progressive Sanctions and Penalties
**Cannot simulate:**
- "First violation: 1-month sanction, Second: 3-month, Third: permanent"
- Graduated penalties
- Strike systems

**Why:** Requires tracking violation history.

#### 5. Asset Spend-Down Over Time
**Cannot simulate:**
- Medical spend-down across months
- Resource depletion tracking
- Accumulated medical expenses

**Why:** Requires tracking expenses and resources across periods.

### What CAN Be Simulated (With Caveats)

PolicyEngine CAN simulate point-in-time eligibility and benefits:
- ✅ Current month income limits
- ✅ Current month resource limits
- ✅ Current benefit calculations
- ✅ Current household composition
- ✅ Current deductions and disregards

### Time-Limited Benefits That Affect Current Calculations

**Special Case: Time-limited deductions/disregards**

When a deduction or disregard is only available for X months:
- **DO implement the deduction** (assume it applies)
- **DO add a comment** explaining the time limitation
- **DON'T try to track or enforce the time limit**

Example:
```python
class state_tanf_countable_earned_income(Variable):
    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.xx.tanf.income
        earned = spm_unit("tanf_gross_earned_income", period)

        # NOTE: In reality, this 75% disregard only applies for first 4 months
        # of employment. PolicyEngine cannot track employment duration, so we
        # apply the disregard assuming the household qualifies.
        # Actual rule: [State Code Citation]
        disregard_rate = p.earned_income_disregard_rate  # 0.75

        return earned * (1 - disregard_rate)
```

**Rule: If it requires history or future tracking, it CANNOT be fully simulated - but implement what we can and document limitations**

---

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

### Avoiding Unnecessary Wrapper Variables (CRITICAL)

**Golden Rule: Only create a state variable if you're adding state-specific logic to it!**

#### Understand WHY Variables Exist, Not Just WHAT

When studying reference implementations:
1. **Note which variables they have**
2. **READ THE CODE inside each variable**
3. **Ask: "Does this variable have state-specific logic?"**
4. **If it just returns federal baseline → DON'T copy it**

#### Variable Creation Decision Tree

Before creating ANY state-specific variable, ask:
1. Does federal baseline already calculate this?
2. Does my state do it DIFFERENTLY than federal?
3. Can I write the difference in 1+ lines of state-specific logic?

- If YES/NO/NO → **DON'T create the variable**, use federal directly
- If YES/YES/YES → **CREATE the variable** with state logic

#### Red Flags for Unnecessary Wrapper Variables

```python
❌ INVALID - Pure wrapper, no state logic:
class in_tanf_assistance_unit_size(Variable):
    def formula(spm_unit, period):
        return spm_unit("spm_unit_size", period)  # Just returns federal

❌ INVALID - Aggregation without transformation:
class in_tanf_countable_unearned_income(Variable):
    def formula(tax_unit, period):
        return tax_unit.sum(person("tanf_gross_unearned_income", period))

❌ INVALID - Pass-through with no modification:
class in_tanf_gross_income(Variable):
    def formula(entity, period):
        return entity("tanf_gross_income", period)
```

#### Examples of VALID State Variables

```python
✅ VALID - Has state-specific disregard:
class in_tanf_countable_earned_income(Variable):
    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.in.tanf.income
        earned = spm_unit("tanf_gross_earned_income", period)
        return earned * (1 - p.earned_income_disregard_rate)  # STATE LOGIC

✅ VALID - Uses state-specific limits:
class in_tanf_income_eligible(Variable):
    def formula(spm_unit, period, parameters):
        p = parameters(period).gov.states.in.tanf
        income = spm_unit("tanf_countable_income", period)
        size = spm_unit("spm_unit_size", period.this_year)
        limit = p.income_limit[min_(size, p.max_household_size)]  # STATE PARAMS
        return income <= limit

✅ VALID - IL has different counting rules:
class il_tanf_assistance_unit_size(Variable):
    adds = [
        "il_tanf_payment_eligible_child",  # STATE-SPECIFIC
        "il_tanf_payment_eligible_parent",  # STATE-SPECIFIC
    ]
```

#### State Variables to AVOID Creating

For TANF implementations:

**❌ DON'T create these (use federal directly):**
- `state_tanf_assistance_unit_size` (unless different counting rules like IL)
- `state_tanf_countable_unearned_income` (unless state has disregards)
- `state_tanf_gross_income` (just use federal baseline)
- Any variable that's just `return entity("federal_variable", period)`

**✅ DO create these (when state has unique rules):**
- `state_tanf_countable_earned_income` (if unique disregard %)
- `state_tanf_income_eligible` (state income limits)
- `state_tanf_maximum_benefit` (state payment standards)
- `state_tanf` (final benefit calculation)

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

## Parameter-to-Variable Mapping Requirements

### Every Parameter Must Have a Variable

**CRITICAL: Complete implementation means every parameter is used!**

When you create parameters, you MUST create corresponding variables:

| Parameter Type | Required Variable(s) |
|---------------|---------------------|
| resources/limit | `state_program_resource_eligible` |
| income/limit | `state_program_income_eligible` |
| payment_standard | `state_program_maximum_benefit` |
| income/disregard | `state_program_countable_earned_income` |
| categorical/requirements | `state_program_categorically_eligible` |

### Complete Eligibility Formula

The main eligibility variable MUST combine ALL checks:

```python
class state_program_eligible(Variable):
    def formula(spm_unit, period, parameters):
        income_eligible = spm_unit("state_program_income_eligible", period)
        resource_eligible = spm_unit("state_program_resource_eligible", period)  # DON'T FORGET!
        categorical = spm_unit("state_program_categorically_eligible", period)

        return income_eligible & resource_eligible & categorical
```

**Common Implementation Failures:**
- ❌ Created resource limit parameter but no resource_eligible variable
- ❌ Main eligible variable only checks income, ignores resources
- ❌ Parameters created but never referenced in any formula

---

## For Agents

When implementing variables:
1. **Study reference implementations** (DC, IL, TX TANF)
2. **Never hard-code values** - use parameters
3. **Map every parameter to a variable** - no orphaned parameters
4. **Complete ALL eligibility checks** - income AND resources AND categorical
5. **Reuse existing variables** - avoid duplication
6. **Use `adds` when possible** - cleaner than formula
7. **Create intermediate variables** for complex logic
8. **Follow metadata standards** exactly
9. **Complete implementation** or delete the file