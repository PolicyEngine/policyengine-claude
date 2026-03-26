---
name: policyengine-testing-patterns
description: PolicyEngine testing patterns - YAML test structure, naming conventions, period handling, and quality standards
---

# PolicyEngine Testing Patterns

Comprehensive patterns and standards for creating PolicyEngine tests.

## Quick Reference

### File Structure
```
policyengine_us/tests/policy/baseline/gov/states/[state]/[agency]/[program]/
├── [variable_name].yaml       # Unit test for specific variable
├── [another_variable].yaml    # Another unit test
└── integration.yaml           # Integration test (NEVER prefixed)
```

### Period Restrictions
- ✅ `2024-01` - First month only
- ✅ `2024` - Whole year
- ❌ `2024-04` - Other months NOT supported
- ❌ `2024-01-01` - Full dates NOT supported

### Error Margin
Choose the margin based on the output type:
- **Boolean outputs** (`true`/`false`, eligibility, flags): **no error margin at all** — booleans are exact, no rounding. Omit `absolute_error_margin` entirely.
- **Currency outputs** (benefits, income, amounts): `absolute_error_margin: 0.01`
- **Rate/percentage outputs**: `absolute_error_margin: 0.001`
- **Never use 1** — a margin of 1 makes `true` (1) and `false` (0) indistinguishable, rendering the test meaningless

### Naming Convention
- Files: `variable_name.yaml` (matches variable exactly)
- Integration: Always `integration.yaml` (never prefixed)
- Cases: `Case 1, description.` (numbered, comma, period)
- People: `person1`, `person2` (never descriptive names)

---

## 1. Test File Organization

### File Naming Rules

**Unit tests** - Named after the variable they test:
```
✅ CORRECT:
az_liheap_eligible.yaml    # Tests az_liheap_eligible variable
az_liheap_benefit.yaml      # Tests az_liheap_benefit variable

❌ WRONG:
test_az_liheap.yaml         # Wrong prefix
liheap_tests.yaml           # Wrong pattern
```

**Integration tests** - Always named `integration.yaml`:
```
✅ CORRECT:
integration.yaml            # Standard name

❌ WRONG:
az_liheap_integration.yaml  # Never prefix integration
program_integration.yaml    # Never prefix integration
```

### Folder Structure

Follow state/agency/program hierarchy:
```
gov/
└── states/
    └── [state_code]/
        └── [agency]/
            └── [program]/
                ├── eligibility/
                │   └── income_eligible.yaml
                ├── income/
                │   └── countable_income.yaml
                └── integration.yaml
```

---

## 2. Period Format Restrictions

### Critical: Only Two Formats Supported

PolicyEngine test system ONLY supports:
- `2024-01` - First month of year
- `2024` - Whole year

**Never use:**
- `2024-04` - April (will fail)
- `2024-10` - October (will fail)
- `2024-01-01` - Full date (will fail)

### Handling Mid-Year Policy Changes

If policy changes April 1, 2024:
```yaml
# Option 1: Test with first month
period: 2024-01  # Tests January with new policy

# Option 2: Test next year
period: 2025-01  # When policy definitely active
```

---

## 3. Test Naming Conventions

### Case Names

Use numbered cases with descriptions:
```yaml
✅ CORRECT:
- name: Case 1, single parent with one child.
- name: Case 2, two parents with two children.
- name: Case 3, income at threshold.

❌ WRONG:
- name: Single parent test
- name: Test case for family
- name: Case 1 - single parent  # Wrong punctuation
```

### Adding Cases to Existing Test Files

**CRITICAL: Always append new test cases at the bottom of the file.** Never insert cases in the middle of existing tests.

```yaml
# Existing file has Cases 1-3
# ✅ CORRECT - Add Case 4 at the bottom:
- name: Case 3, income above threshold.
  ...

- name: Case 4, new edge case scenario.
  ...

# ❌ WRONG - Inserting between existing cases and renumbering:
- name: Case 1, ...
- name: Case 2, new case inserted here.    # Renumbered!
- name: Case 3, was previously Case 2.     # Renumbered!
```

**Why:** Inserting in the middle forces renumbering of existing cases, which creates noisy diffs and makes review harder. Appending at the bottom keeps existing cases untouched.

### Person Names

Use generic sequential names:
```yaml
✅ CORRECT:
people:
  person1:
    age: 30
  person2:
    age: 10
  person3:
    age: 8

❌ WRONG:
people:
  parent:
    age: 30
  child1:
    age: 10
```

### Output Format

Use simplified format without entity key:
```yaml
✅ CORRECT:
output:
  tx_tanf_eligible: true
  tx_tanf_benefit: 250

❌ WRONG:
output:
  tx_tanf_eligible:
    spm_unit: true  # Don't nest under entity
```

---

## 4. Which Variables Need Tests

### Variables That DON'T Need Tests

Skip tests for simple composition variables using only `adds` or `subtracts`:
```python
# NO TEST NEEDED - just summing
class tx_tanf_countable_income(Variable):
    adds = ["earned_income", "unearned_income"]

# NO TEST NEEDED - simple arithmetic
class net_income(Variable):
    adds = ["gross_income"]
    subtracts = ["deductions"]
```

### Variables That NEED Tests

Create tests for variables with:
- Conditional logic (`where`, `select`, `if`)
- Calculations/transformations
- Business logic
- Deductions/disregards
- Eligibility determinations

```python
# NEEDS TEST - has logic
class tx_tanf_income_eligible(Variable):
    def formula(spm_unit, period, parameters):
        return where(enrolled, passes_test, other_test)
```

---

## 5. Period Conversion in Tests

### Complete Input/Output Rules

**The key rule:** Input matches the **larger of (variable period, test period)**. Output matches the **test period**.

| Variable Def | Test Period | Input Value | Output Value |
|--------------|-------------|-------------|--------------|
| **YEAR** | YEAR | Yearly | Yearly |
| **YEAR** | MONTH | **Yearly** (always!) | Monthly (÷12) |
| **MONTH** | YEAR | Yearly (÷12 per month) | Yearly (sum of 12) |
| **MONTH** | MONTH | **Monthly** | Monthly |

### YEAR Variable Examples

```yaml
# YEAR variable + YEAR period
- name: Case 1, yearly test.
  period: 2024
  input:
    employment_income: 12_000  # Yearly input
  output:
    employment_income: 12_000  # Yearly output

# YEAR variable + MONTH period
- name: Case 2, monthly test with yearly variable.
  period: 2024-01
  input:
    employment_income: 12_000  # Still yearly input!
  output:
    employment_income: 1_000   # Monthly output (12_000/12)
```

### MONTH Variable Examples

```yaml
# MONTH variable + YEAR period
- name: Case 3, yearly test with monthly variable.
  period: 2024
  input:
    some_monthly_var: 1_200  # Yearly total (divided by 12 = 100/month)
  output:
    some_monthly_var: 1_200  # Yearly sum

# MONTH variable + MONTH period
- name: Case 4, monthly test with monthly variable.
  period: 2024-01
  input:
    some_monthly_var: 100  # Monthly input (just January)
  output:
    some_monthly_var: 100  # Monthly output
```

See **policyengine-period-patterns** skill for the full explanation of period auto-conversion.

---

## 6. Numeric Formatting

### Always Use Underscore Separators

```yaml
✅ CORRECT:
employment_income: 50_000
cash_assets: 1_500

❌ WRONG:
employment_income: 50000
cash_assets: 1500
```

---

## 7. Integration Test Quality Standards

### Inline Calculation Comments

Document every calculation step:
```yaml
- name: Case 2, earnings with deductions.
  period: 2025-01
  input:
    people:
      person1:
        employment_income: 3_000  # $250/month
  output:
    # Person-level arrays
    tx_tanf_gross_earned_income: [250, 0]
    # Person1: 3,000/12 = 250

    tx_tanf_earned_after_disregard: [87.1, 0]
    # Person1: 250 - 120 = 130
    # Disregard: 130/3 = 43.33
    # After: 130 - 43.33 = 86.67 ≈ 87.1
```

### Comprehensive Scenarios

Include 5-7 scenarios covering:
1. Basic eligible case
2. Earnings with deductions
3. Edge case at threshold
4. Mixed enrollment status
5. Special circumstances (SSI, immigration)
6. Ineligible case

### Verify Intermediate Values

Check 8-10 values per test:
```yaml
output:
  # Income calculation chain
  program_gross_income: 250
  program_earned_after_disregard: 87.1
  program_deductions: 200
  program_countable_income: 0

  # Eligibility chain
  program_income_eligible: true
  program_resources_eligible: true
  program_eligible: true

  # Final benefit
  program_benefit: 320
```

---

## 8. Common Variables to Use

### Always Available
```yaml
# Demographics
age: 30
is_disabled: false
is_pregnant: false

# Income
employment_income: 50_000
self_employment_income: 10_000
social_security: 12_000
ssi: 9_000

# Benefits
snap: 200
tanf: 150
medicaid: true

# Location
state_code: CA
county_code: "06037"  # String for FIPS
```

### Variables That DON'T Exist

Never use these (not in PolicyEngine):
- `heating_expense`
- `utility_expense`
- `utility_shut_off_notice`
- `past_due_balance`
- `bulk_fuel_amount`
- `weatherization_needed`

---

## 9. Enum Verification

### Always Check Actual Enum Values

Before using enums in tests:
```bash
# Find enum definition
grep -r "class ImmigrationStatus" --include="*.py"
```

```python
# Check actual values
class ImmigrationStatus(Enum):
    CITIZEN = "Citizen"
    LEGAL_PERMANENT_RESIDENT = "Legal Permanent Resident"  # NOT "PERMANENT_RESIDENT"
    REFUGEE = "Refugee"
```

```yaml
✅ CORRECT:
immigration_status: LEGAL_PERMANENT_RESIDENT

❌ WRONG:
immigration_status: PERMANENT_RESIDENT  # Doesn't exist
```

---

## 10. Test Quality Checklist

Before submitting tests:
- [ ] All variables exist in PolicyEngine
- [ ] Period format is `2024-01` or `2024` only
- [ ] Numbers use underscore separators
- [ ] Integration tests have calculation comments
- [ ] 5-7 comprehensive scenarios in integration.yaml
- [ ] Enum values verified against actual definitions
- [ ] Output values realistic, not placeholders
- [ ] File names match variable names exactly

---

## Common Test Patterns

### Income Eligibility
```yaml
- name: Case 1, income exactly at threshold.
  period: 2024-01
  input:
    people:
      person1:
        employment_income: 30_360  # Annual limit
  output:
    program_income_eligible: true  # At threshold = eligible
```

### Priority Groups
```yaml
- name: Case 2, elderly priority.
  period: 2024-01
  input:
    people:
      person1:
        age: 65
  output:
    program_priority_group: true
```

### Categorical Eligibility
```yaml
- name: Case 3, SNAP categorical.
  period: 2024-01
  input:
    spm_units:
      spm_unit:
        snap: 200  # Receives SNAP
  output:
    program_categorical_eligible: true
```

### Negative Income — Benefit Cap

Always include a test that verifies benefits are capped at the maximum payment amount when countable income is negative. This prevents the bug where `max_benefit - (-N) = max_benefit + N`, inflating benefits beyond the payment standard.

```yaml
# Tests that benefits are capped at the maximum payment amount,
# even when countable income is negative.
# Prevents: benefit = max - (-5M) = 5M+
- name: Case N, negative countable income does not inflate benefit.
  period: 2025-01
  input:
    people:
      person1:
        age: 30
        self_employment_income: -60_000_000  # -$5M/month
      person2:
        age: 8
    spm_units:
      spm_unit:
        members: [person1, person2]
    households:
      household:
        members: [person1, person2]
        state_code: XX
  output:
    xx_tanf: 300  # Capped at max payment standard, not 5M+
```

---

## 11. Required Test Scenarios

### Every Benefit Program Must Test

1. **At least one positive (non-zero) benefit case.** Zero-benefit-only tests hide formula errors that cancel out.
2. **At least one ineligible case** returning zero/false.
3. **Edge case at exactly the threshold** (income, age, or resource limits).
4. **Edge case for empty/zero-size units** to verify graceful handling of degenerate inputs.

### Dimension Coverage

When a variable depends on a multi-valued dimension (provider type, care setting, filing status), **every dimension value** needs at least one test case. Zero coverage of an entire dimension hides bugs.

### Household Composition

- **TANF/cash assistance**: Always include at least one child — single adults without children are demographically ineligible.
- **Couple/marital-unit programs**: Include a test with asymmetric eligibility (one member eligible, one not) to catch half-benefit or incorrect-amount bugs from `defined_for` filtering.

### Mid-Year Parameter Transitions

When values change mid-year (e.g., July 1), test **both sides** of the boundary (e.g., June vs July). January-only tests miss off-by-one errors in effective dates.

### Add-On Components

When a benefit has supplements or adjustments, test that each flows through to the **top-level benefit variable** — not just in isolation.

### Combined Federal + State Benefits

When a source provides combined amounts (e.g., Federal SSI + State SSP), test both components independently with comments showing the combined math matches the source.

---

## 12. Test Maintenance Rules

### Verify Input Variable Names
Check the formula's actual input variable names before writing tests. Use the variable the formula reads (e.g., `employment_income_before_lsr`), not a similar-sounding upstream variable.

### Test Names Must Match Values
A case named "$275 weekly" that expects $250 misleads reviewers. Keep names and expected values consistent.

### Bug Fixes Require a Test Sweep
When fixing a buggy parameter or formula, sweep **ALL** test files referencing the affected variable. Stale expected values silently mask regressions.

---

