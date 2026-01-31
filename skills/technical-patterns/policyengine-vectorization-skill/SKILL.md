---
name: policyengine-vectorization
description: PolicyEngine vectorization patterns - NumPy operations, where/select usage, avoiding scalar logic with arrays
---

# PolicyEngine Vectorization Patterns

Critical patterns for vectorized operations in PolicyEngine. Scalar logic with arrays will crash the microsimulation.

## The Golden Rule

**PolicyEngine processes multiple households simultaneously using NumPy arrays. NEVER use if-elif-else with entity data.**

---

## 1. Critical: What Will Crash

### ❌ NEVER: if-elif-else with Arrays

```python
# THIS WILL CRASH - household data is an array
def formula(household, period, parameters):
    income = household("income", period)
    if income > 1000:  # ❌ CRASH: "truth value of array is ambiguous"
        return 500
    else:
        return 100
```

### ✅ ALWAYS: Vectorized Operations

```python
# CORRECT - works with arrays
def formula(household, period, parameters):
    income = household("income", period)
    return where(income > 1000, 500, 100)  # ✅ Vectorized
```

---

## 2. Common Vectorization Patterns

### Pattern 1: Simple Conditions → `where()`

```python
# Instead of if-else
❌ if age >= 65:
    amount = senior_amount
else:
    amount = regular_amount

✅ amount = where(age >= 65, senior_amount, regular_amount)
```

### Pattern 2: Multiple Conditions → `select()`

```python
# Instead of if-elif-else
❌ if age < 18:
    benefit = child_amount
elif age >= 65:
    benefit = senior_amount
else:
    benefit = adult_amount

✅ benefit = select(
    [age < 18, age >= 65],
    [child_amount, senior_amount],
    default=adult_amount
)
```

### Pattern 3: Boolean Operations

```python
# Combining conditions
eligible = (age >= 18) & (income < threshold)  # Use & not 'and'
eligible = (is_disabled | is_elderly)          # Use | not 'or'
eligible = ~is_excluded                        # Use ~ not 'not'
```

### Pattern 4: Clipping Values

```python
# Instead of if for bounds checking
❌ if amount < 0:
    amount = 0
elif amount > maximum:
    amount = maximum

✅ amount = clip(amount, 0, maximum)
# Or: amount = max_(0, min_(amount, maximum))
```

---

## 3. When if-else IS Acceptable

### ✅ OK: Parameter-Only Conditions

```python
# OK - parameters are scalars, not arrays
def formula(entity, period, parameters):
    p = parameters(period).gov.program

    # This is fine - p.enabled is a scalar boolean
    if p.enabled:
        base = p.base_amount
    else:
        base = 0

    # But must vectorize when using entity data
    income = entity("income", period)
    return where(income < p.threshold, base, 0)
```

### ✅ OK: Control Flow (Not Data)

```python
# OK - controlling which calculation to use
def formula(entity, period, parameters):
    year = period.start.year

    if year >= 2024:
        # Use new formula (still vectorized)
        return entity("new_calculation", period)
    else:
        # Use old formula (still vectorized)
        return entity("old_calculation", period)
```

---

## 4. Common Vectorization Mistakes

### Mistake 1: Scalar Comparison with Array

```python
❌ WRONG:
if household("income", period) > 1000:
    # Error: truth value of array is ambiguous

✅ CORRECT:
income = household("income", period)
high_income = income > 1000  # Boolean array
benefit = where(high_income, low_benefit, high_benefit)
```

### Mistake 2: Using Python's and/or/not

```python
❌ WRONG:
eligible = is_elderly or is_disabled  # Python's 'or'

✅ CORRECT:
eligible = is_elderly | is_disabled   # NumPy's '|'
```

### Mistake 3: Nested if Statements

```python
❌ WRONG:
if eligible:
    if income < threshold:
        return full_benefit
    else:
        return partial_benefit
else:
    return 0

✅ CORRECT:
return where(
    eligible,
    where(income < threshold, full_benefit, partial_benefit),
    0
)
```

---

## 5. CRITICAL: Avoiding Divide-by-Zero Warnings

### The Problem with `where()` for Division

`where()` evaluates **BOTH branches** before selecting. This causes divide-by-zero warnings even when the zero case wouldn't be selected:

```python
# ❌ WRONG - causes divide-by-zero warning
proportion = where(
    total_income > 0,
    person_income / total_income,  # Still evaluated when total_income = 0!
    0,
)
```

### ✅ CORRECT: Use `np.divide` with `where` Parameter

```python
# ✅ CORRECT - only divides where mask is True
# The `out` parameter IS the default value - positions where mask=False keep this value
mask = total_income > 0
proportion = np.divide(
    person_income,
    total_income,
    out=np.zeros_like(person_income),  # Default to 0 where mask is False
    where=mask,
)
```

**How `out` works as the default:**
- `out=np.zeros_like(...)` → default is 0
- `out=np.ones_like(...)` → default is 1
- Positions where `where=False` keep their `out` value unchanged

### ✅ CORRECT: Alternative Mask Pattern

```python
# ✅ CORRECT - traditional mask assignment
proportion = np.zeros_like(total_income)
mask = total_income > 0
proportion[mask] = person_income[mask] / total_income[mask]
```

### Common Use Cases

**Proportional allocation (e.g., splitting deductions between spouses):**
```python
# Allocate proportionally by income
unit_income = tax_unit.sum(person_income)
mask = unit_income > 0
share = np.divide(
    person_income,
    unit_income,
    out=np.zeros_like(person_income),
    where=mask,
)
# Default share when unit has no income
share = where(mask, share, where(is_head, 1.0, 0.0))
```

**Calculating ratios:**
```python
# AGI ratio for credit calculations
mask = us_agi != 0
ratio = np.divide(
    state_agi,
    us_agi,
    out=np.zeros_like(us_agi),
    where=mask,
)
```

### Real Examples in Codebase

See these files for reference implementations:
- `taxable_social_security.py` - person share of unit benefits
- `mo_taxable_income.py` - AGI share allocation
- `md_two_income_subtraction.py` - head's share of couple income
- `ok_child_care_child_tax_credit.py` - AGI ratio

---

## 6. More Advanced Patterns

### Pattern: Vectorized Lookup Tables

```python
# Instead of if-elif for ranges
❌ if size == 1:
    amount = 100
elif size == 2:
    amount = 150
elif size == 3:
    amount = 190

✅ # Using parameter brackets
amount = p.benefit_schedule.calc(size)

✅ # Or using select
amounts = [100, 150, 190, 220, 250]
amount = select(
    [size == i for i in range(1, 6)],
    amounts[:5],
    default=amounts[-1]  # 5+ people
)
```

### Pattern: Accumulating Conditions

```python
# Building complex eligibility
income_eligible = income < p.income_threshold
resource_eligible = resources < p.resource_limit
demographic_eligible = (age < 18) | is_pregnant

# Combine with & (not 'and')
eligible = income_eligible & resource_eligible & demographic_eligible
```

### Pattern: Conditional Accumulation

```python
# Sum only for eligible members
person = household.members
is_eligible = person("is_eligible", period)
person_income = person("income", period)

# Only count income of eligible members
eligible_income = where(is_eligible, person_income, 0)
total = household.sum(eligible_income)
```

---

## 7. Performance Implications

### Why Vectorization Matters

- **Scalar logic**: Processes 1 household at a time → SLOW
- **Vectorized**: Processes 1000s of households simultaneously → FAST

```python
# Performance comparison
❌ SLOW (if it worked):
for household in households:
    if household.income > 1000:
        household.benefit = 500

✅ FAST:
benefits = where(incomes > 1000, 500, 100)  # All at once!
```

---

## 8. Testing for Vectorization Issues

### Signs Your Code Isn't Vectorized

**Error messages:**
- "The truth value of an array is ambiguous"
- "ValueError: The truth value of an array with more than one element"

**Performance:**
- Tests run slowly
- Microsimulation times out

### How to Test

```python
# Your formula should work with arrays
def test_vectorization():
    # Create array inputs
    incomes = np.array([500, 1500, 3000])

    # Should return array output
    benefits = formula_with_arrays(incomes)
    assert len(benefits) == 3
```

---

## Quick Reference Card

| Operation | Scalar (WRONG) | Vectorized (CORRECT) |
|-----------|---------------|---------------------|
| Simple condition | `if x > 5:` | `where(x > 5, ...)` |
| Multiple conditions | `if-elif-else` | `select([...], [...])` |
| Boolean AND | `and` | `&` |
| Boolean OR | `or` | `\|` |
| Boolean NOT | `not` | `~` |
| Bounds checking | `if x < 0: x = 0` | `max_(0, x)` |
| Complex logic | Nested if | Nested where/select |

---

## For Agents

When implementing formulas:
1. **Never use if-elif-else** with entity data
2. **Always use where()** for simple conditions
3. **Use select()** for multiple conditions
4. **Use NumPy operators** (&, |, ~) not Python (and, or, not)
5. **Test with arrays** to ensure vectorization
6. **Parameter conditions** can use if-else (scalars)
7. **Entity data** must use vectorized operations