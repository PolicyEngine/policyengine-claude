# Aggregation patterns

Detailed patterns for summing variables across entities in PolicyEngine.

## Quick decision

```
Is the variable ONLY a sum of other variables?
├─ YES → Use `adds` attribute (NO formula needed!)
└─ NO  → Use `add()` function in formula
```

## 1. `adds` class attribute (preferred)

Use when a variable is ONLY the sum of other variables with NO additional logic.

```python
class tanf_gross_earned_income(Variable):
    value_type = float
    entity = SPMUnit
    definition_period = MONTH
    adds = ["employment_income", "self_employment_income"]
    # NO formula needed! Automatically sums across SPM unit members
```

### From parameter list
```python
class income_tax_refundable_credits(Variable):
    adds = "gov.irs.credits.refundable"
    # Parameter file lists: earned_income_tax_credit, child_tax_credit, etc.
```

### Counting booleans
```python
class count_eligible_people(Variable):
    adds = ["is_eligible_person"]  # Sums True(1)/False(0)
```

## 2. `add()` function (when logic needed)

Use inside `formula()` when you need `max_()`, `where()`, conditions, or modifications.

```python
def formula(spm_unit, period, parameters):
    gross = add(spm_unit, period, ["employment_income", "self_employment_income"])
    return max_(0, gross)  # Prevent negative income
```

## 3. Entity aggregation

PolicyEngine automatically handles cross-entity aggregation:

```python
class household_total_income(Variable):
    entity = Household  # Higher-level entity
    adds = ["employment_income"]  # Person-level variable
    # Auto: gets each person's employment_income, sums to household
```

Works across all hierarchies: Person → Tax Unit/SPM Unit/Household.

## 4. Anti-patterns

```python
# ❌ NEVER manual summing
person = spm_unit.members
return spm_unit.sum(person("income1", period) + person("income2", period))

# ❌ NEVER add() when adds suffices
def formula(spm_unit, period, parameters):
    return add(spm_unit, period, ["income1", "income2"])  # Overkill

# ✅ Use adds
adds = ["income1", "income2"]
```

## 5. Decision matrix

| Scenario | Solution |
|----------|----------|
| Sum 2-3 variables | `adds = ["var1", "var2"]` |
| Sum many variables | `adds = "gov.path.list"` |
| Sum + prevent negatives | `max_(0, add(...))` |
| Sum + conditional | `where(eligible, add(...), 0)` |
| Count booleans | `adds = ["is_child"]` |
