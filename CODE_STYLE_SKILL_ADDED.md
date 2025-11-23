# Code Style Skill Added

## Summary

Created a new skill `policyengine-code-style-skill` to capture PolicyEngine's preferred code writing style for formulas.

## Why This Is a Separate Skill

While there's some overlap with existing skills, this focuses specifically on **formula optimization and code efficiency**, which is distinct from:
- **implementation-patterns-skill**: Focuses on structural decisions (federal/state, adds vs formula)
- **vectorization-skill**: Focuses on avoiding crashes from scalar logic
- **period-patterns-skill**: Focuses on period conversion

This skill focuses on **writing cleaner, more efficient formulas**.

## Key Patterns Documented

### 1. Direct Parameter Access
- Don't create intermediate variables for single-use parameter values
- Access directly: `p.amount` not `amount = p.amount`

### 2. Direct Returns
- Return expressions directly when possible
- Avoid unnecessary result variables

### 3. Combined Boolean Logic
- Combine related boolean conditions
- Avoid excessive intermediate boolean variables

### 4. Streamlined Variable Access
- Eliminate redundant steps
- Access nested parameters directly

### 5. When to Keep Variables
- Keep when used multiple times
- Keep when calculation is complex and needs clarity

## Example Impact

**Before (15 lines):**
```python
def formula(person, period, parameters):
    age = person("age", period)  # Wrong - gets age/12
    min_age = 18  # Hardcoded
    max_age = 64  # Hardcoded
    age_check = (age >= min_age) & (age <= max_age)

    assets = person("assets", period)  # Wrong - gets assets/12
    asset_limit = 10000  # Hardcoded
    asset_check = assets <= asset_limit

    annual_income = person("employment_income", period.this_year)
    monthly_income = annual_income / 12
    income_limit = 2000  # Hardcoded
    income_check = monthly_income <= income_limit

    eligible = age_check & asset_check & income_check
    return eligible
```

**After (7 lines):**
```python
def formula(person, period, parameters):
    p = parameters(period).gov.program.eligibility

    return (
        (person("age", period.this_year) >= p.age_min) &
        (person("age", period.this_year) <= p.age_max) &
        (person("assets", period.this_year) <= p.asset_limit) &
        (person("employment_income", period) <= p.income_threshold)
    )
```

## Files Modified

1. **Created:** `/skills/policyengine-code-style-skill/skill.md`
2. **Updated:** `/.claude-plugin/marketplace.json` (added to country-models and complete plugins)
3. **Updated:** `/skills/README.md` (added to Technical Pattern Skills section)

## Who Benefits

- **rules-engineer agent**: Writing cleaner formulas
- **ci-fixer agent**: Refactoring code to be cleaner
- **rules-reviewer agent**: Checking for code style issues
- **Human developers**: Learning PolicyEngine's preferred style

## Integration with Other Skills

The code style skill references and complements:
- **policyengine-period-patterns-skill**: For period access details
- **policyengine-implementation-patterns-skill**: For structural patterns
- **policyengine-vectorization-skill**: For NumPy operations

## Result

This skill helps ensure PolicyEngine formulas are:
- **More readable** (less clutter)
- **More maintainable** (direct parameter access)
- **More efficient** (fewer unnecessary variables)
- **Less error-prone** (correct period access)