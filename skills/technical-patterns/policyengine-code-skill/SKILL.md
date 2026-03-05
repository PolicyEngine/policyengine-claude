---
name: policyengine-code
description: PolicyEngine code patterns - variable naming, folder structure, formula style, period access, and optimization. Use when writing or reviewing PolicyEngine variable formulas, organizing code files, or following naming conventions.
---

# PolicyEngine code patterns

Patterns for writing clean, well-organized PolicyEngine code — naming conventions, folder structure, and formula style.

## Variable naming

### State programs

```python
# Pattern: {state}_{program}
az_liheap      # Arizona LIHEAP
ca_calfresh    # California CalFresh (SNAP)
ny_heap        # New York HEAP (LIHEAP)

# Sub-variables: {state}_{program}_{component}
az_liheap_eligible
az_liheap_income_eligible
az_liheap_benefit_amount
```

### Federal programs

```python
# Pattern: just {program}
snap
liheap

# Sub-variables: {program}_{component}
snap_eligible
snap_gross_income
```

**Use state's official name** — e.g., `ca_calworks` not `ca_tanf` (California calls it CalWORKs).

### Standard suffixes

| Type | Suffixes |
|------|----------|
| Eligibility | `_eligible`, `_income_eligible`, `_resource_eligible`, `_categorical_eligible` |
| Calculation | (no suffix for final benefit), `_maximum_benefit`, `_countable_income`, `_gross_income` |
| Deductions | `_earned_income_disregard`, `_work_expense_deduction`, `_standard_deduction` |
| Thresholds | `_income_limit`, `_resource_limit`, `_payment_standard` |

---

## Folder structure

### Core principles
1. **Group logically** — related files together
2. **Don't create subfolder for 1 file** — keep at parent level
3. **Final output at root** — main benefit variable stays at program folder root

### Small program (~5 files) — keep flat
```
{program}/
├── {prefix}.py                    # Final benefit
├── {prefix}_eligible.py
├── {prefix}_income_eligible.py
├── {prefix}_maximum_benefit.py
└── {prefix}_countable_income.py
```

### Medium program (6-15 files)
```
{program}/
├── {prefix}.py                    # Final benefit (at root)
├── eligibility/
│   ├── {prefix}_eligible.py
│   └── {prefix}_income_eligible.py
└── income/
    └── {prefix}_countable_income.py
```

### Tests
```
tests/policy/baseline/gov/states/{state}/{agency}/{program}/
├── {prefix}.yaml
├── {prefix}_eligible.yaml
└── integration.yaml          # Always named integration.yaml
```

---

## Formula style

### Direct parameter access — no single-use intermediates

```python
# ❌ Unnecessary intermediate
resource_limit = p.amount
return countable <= resource_limit

# ✅ Direct access
return countable <= p.amount
```

### Direct return

```python
# ❌ Unnecessary result variable
countable = max_(assets - p.vehicle_exemption, 0)
return countable

# ✅ Direct return
return max_(assets - p.vehicle_exemption, 0)
```

### Combined boolean logic

```python
# ❌ Too many intermediate booleans
caretaker_is_60_or_older = spm_unit.any(age >= 60)
caretaker_is_disabled = spm_unit.any(is_disabled)
eligible = caretaker_is_60_or_older | caretaker_is_disabled
return eligible

# ✅ Combined
return spm_unit.any((age >= 60) | is_disabled)
```

### When to KEEP intermediate variables

- **Used multiple times** — threshold used in excess calculation and final result
- **Complex multi-step calculations** — work expense deduction chains
- **Complex expressions inside where()/max_()** — give them descriptive names

```python
# ✅ Break out complex expressions inside where()
standard_payment = max_(maximum_benefit - countable_income, 0)
return where(above_trigger, reduced_payment, standard_payment)
```

---

## Period access — period vs period.this_year

**When accessing a YEAR variable from a MONTH formula:**
- **Income/flows** → Use `period` (want monthly from annual: auto ÷12)
- **Age/assets/counts/booleans** → Use `period.this_year` (don't divide by 12)

```python
def formula(person, period, parameters):
    age = person("age", period.this_year)          # ✅ Gets 30, not 2.5
    assets = person("assets", period.this_year)    # ✅ Gets $10,000
    monthly_income = person("employment_income", period)  # ✅ Auto-converts
```

**Rule of thumb:** If dividing by 12 makes the value meaningless → use `period.this_year`

---

## No hardcoded values

Every numeric value MUST be parameterized:

```python
# ❌ Hardcoded
return where(eligible, 1000, 0)
age < 15
benefit = income * 0.33

# ✅ Parameterized
return where(eligible, p.maximum_benefit, 0)
age < p.age_threshold.minor_child
benefit = income * p.benefit_rate
```

**Acceptable literals:** `0`, `1`, `-1` for basic math; `12` for month conversion.

---

## Use add() > 0 instead of spm_unit.any()

```python
# ❌ Verbose
person = spm_unit.members
has_citizen = spm_unit.any(person("is_citizen_or_legal_immigrant", period))

# ✅ Cleaner
immigration_eligible = add(spm_unit, period, ["is_citizen_or_legal_immigrant"]) > 0
```

## Use existing spm_unit variables directly

```python
# ❌ Unnecessary person-level access
person = spm_unit.members
demographic = person("is_person_demographic_tanf_eligible", period)

# ✅ Use spm_unit variable directly
demographic_eligible = spm_unit("is_demographic_tanf_eligible", period)
```

---

## Minimal comments

Variable names and structure should explain the code — not comments.

1. **NO comments explaining what code does** — variable names should be clear
2. **OK: Brief NOTE about implementation decisions** (one line)
3. **NO multi-line explanations** of calculations

---

## Quick checklist

Before finalizing code:
- [ ] No hardcoded numbers (use parameters)
- [ ] Correct period access (income→`period`, age/assets→`period.this_year`)
- [ ] No single-use intermediate variables for simple values
- [ ] Break out complex expressions inside `where()`/`max_()` into named variables
- [ ] Direct parameter access and direct returns
- [ ] Combined boolean logic where possible
- [ ] Minimal comments

## Related skills

- **policyengine-variable-patterns** — Variable creation, federal/state separation, TANF patterns
- **policyengine-parameter-patterns** — YAML parameter structure
- **policyengine-vectorization** — NumPy operations
