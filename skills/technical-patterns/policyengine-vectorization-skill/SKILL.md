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

### Pattern 5: Flooring Subtraction Results (CRITICAL)

When subtracting values and wanting to floor at zero, you must wrap the **entire subtraction** in `max_()`:

```python
# Common scenario: income after deductions/losses
❌ WRONG - Creates phantom negative values:
income = max_(income, 0) - capital_loss  # If capital_loss > income, result is negative!

✅ CORRECT - Properly floors at zero:
income = max_(income - capital_loss, 0)  # Entire subtraction floored

# Real example from MT income tax bug:
❌ WRONG - Tax on phantom negative income:
def formula(tax_unit, period, parameters):
    income = tax_unit("adjusted_gross_income", period)
    capital_gains = tax_unit("capital_gains", period)

    # BUG: If capital_gains is negative (loss), this creates negative income
    # But max_() only floors income, not the result
    regular_income = max_(income, 0) - capital_gains
    return calculate_tax(regular_income)  # Tax on negative number!

✅ CORRECT - No phantom income:
def formula(tax_unit, period, parameters):
    income = tax_unit("adjusted_gross_income", period)
    capital_gains = tax_unit("capital_gains", period)

    # Properly floors the entire result
    regular_income = max_(income - capital_gains, 0)
    return calculate_tax(regular_income)  # Never negative
```

**Why this matters:**
- If `capital_gains = -3000` (loss), then `income - capital_gains = income + 3000`
- The wrong pattern `max_(income, 0) - capital_gains` allows the subtraction to make the result negative
- This creates "phantom income" where none exists, leading to incorrect tax calculations

**Rule:** When the formula is `A - B` and you want the result floored at zero, use `max_(A - B, 0)`, NOT `max_(A, 0) - B`.

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

## 5. Advanced Patterns

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

## 6. Performance Implications

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

## 7. Testing for Vectorization Issues

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
| Floor subtraction | `max_(x, 0) - y` ❌ | `max_(x - y, 0)` ✅ |
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