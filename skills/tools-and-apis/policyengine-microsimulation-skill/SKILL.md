---
name: policyengine-microsimulation
description: |
  ALWAYS USE THIS SKILL for PolicyEngine microsimulation, population-level analysis, winners/losers calculations.
  Triggers: "microsimulation", "share who would lose/gain", "policy impact", "national average", "weighted analysis",
  "cost", "revenue impact", "budgetary", "estimate the cost", "federal revenues", "tax revenue", "budget score",
  "how much would it cost", "how much would the policy cost", "total cost of", "aggregate impact",
  "cost to the government", "revenue loss", "fiscal impact",
  "poverty impact", "child poverty", "deep poverty", "poverty rate", "poverty reduction",
  "how many people lifted out of poverty", "SPM poverty", "distributional impact".
  NOT for single-household calculations like "what would my benefit be" — use policyengine-us or policyengine-uk for those.
  Use this skill's code pattern, but explore the codebase to find specific parameter paths if needed.
---

# PolicyEngine Microsimulation

## Documentation References

- **Microsimulation API**: https://policyengine.github.io/policyengine-us/usage/microsimulation.html
- **Parameter Discovery**: https://policyengine.github.io/policyengine-us/usage/parameter-discovery.html
- **Reform.from_dict()**: https://policyengine.github.io/policyengine-core/usage/reforms.html

## CRITICAL: Use calc() with MicroSeries - No Manual Weights Ever

**MicroSeries handles all weighting automatically. Never access .weights or do manual weight math.**

### NEVER strip weights with .values

`calc()` and `calculate()` return MicroSeries with embedded weights. Calling `.values` strips them and returns a plain numpy array where `.mean()` is **unweighted**.

```python
# ❌ WRONG - .values strips weights, .mean() is UNWEIGHTED
result = sim.calc("household_net_income", period=2026).values
wrong_mean = result.mean()  # Unweighted!

# ❌ WRONG - same problem with .to_numpy()
result = sim.calc("household_net_income", period=2026).to_numpy()

# ✅ CORRECT - keep as MicroSeries, all operations are weighted
result = sim.calc("household_net_income", period=2026)
correct_mean = result.mean()  # Weighted automatically!
```

### Correct patterns

```python
# ✅ CORRECT - MicroSeries handles everything
change = reformed.calc('household_net_income', period=2026, map_to='person') - \
         baseline.calc('household_net_income', period=2026, map_to='person')
loser_share = (change < 0).mean()  # Weighted automatically!

# ❌ WRONG - never access .weights or do manual math
loser_share = change.weights[change.values < 0].sum() / change.weights.sum()
```

## Quick Start

```python
from policyengine_us import Microsimulation
from policyengine_core.reforms import Reform

baseline = Microsimulation()
reform = Reform.from_dict({
    'gov.irs.credits.ctc.amount.base[0].amount': {'2026-01-01.2100-12-31': 3000}
}, 'policyengine_us')
reformed = Microsimulation(reform=reform)

# calc() returns MicroSeries - all operations are weighted automatically
baseline_income = baseline.calc('household_net_income', period=2026, map_to='person')
reformed_income = reformed.calc('household_net_income', period=2026, map_to='person')
change = reformed_income - baseline_income

# Weighted stats - no manual weight handling needed!
print(f"Average impact: ${change.mean():,.0f}")
print(f"Total cost: ${-change.sum()/1e9:,.1f}B")
print(f"Share losing: {(change < 0).mean():.1%}")
```

## Available Datasets (HuggingFace)

```python
# National (default)
sim = Microsimulation()

# State-level
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/states/NY.h5')

# Congressional district - SEE policyengine-district-analysis skill for full examples
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/districts/NY-17.h5')
```

**For congressional district analysis** (representative's constituents, district-level impacts), use the `policyengine-district-analysis` skill which has complete examples.

## Key MicroSeries Methods

MicroSeries (from [microdf](https://github.com/PolicyEngine/microdf)) handles all weighting automatically — see the `microdf` skill for full documentation.

```python
income = sim.calc('household_net_income', period=2026, map_to='person')

# Basic weighted statistics
income.mean()           # Weighted mean
income.sum()            # Weighted sum
income.median()         # Weighted median
(income > 50000).mean() # Weighted share meeting condition

# Inequality metrics (see microdf skill for more)
income.gini()           # Weighted Gini coefficient
```

### Inequality & Distributional Analysis

Use built-in MicroSeries methods — never reimplement Gini or other inequality metrics manually:

```python
baseline_income = baseline.calc('household_net_income', period=2026, map_to='person')
reformed_income = reformed.calc('household_net_income', period=2026, map_to='person')

# Gini coefficient change
print(f"Baseline Gini: {baseline_income.gini():.4f}")
print(f"Reform Gini:   {reformed_income.gini():.4f}")

# Poverty rate (boolean MicroSeries)
in_poverty = baseline.calc('spm_unit_is_in_spm_poverty', map_to='person', period=2026)
print(f"SPM poverty rate: {in_poverty.mean():.1%}")

# Decile-level analysis
income.decile_rank()    # Assign decile ranks (1-10)
```

## Poverty analysis

### Overall and child poverty (person-level)

For poverty rates, you need to filter by subgroup. This requires extracting `.values` for masking — this is the one case where `.values` is appropriate.

```python
from policyengine_us import Microsimulation
import numpy as np

baseline = Microsimulation()
reformed = Microsimulation(reform=reform)

YEAR = 2026

# Extract person weights and poverty indicators
pw = baseline.calc("person_weight", period=YEAR).values
is_child = baseline.calc("is_child", period=YEAR).values.astype(bool)

baseline_pov = baseline.calc("person_in_poverty", period=YEAR).values
reform_pov = reformed.calc("person_in_poverty", period=YEAR).values

def poverty_rate(indicator, weights, mask=None):
    if mask is not None:
        return np.sum(indicator[mask] * weights[mask]) / weights[mask].sum()
    return np.sum(indicator * weights) / weights.sum()

# Overall poverty
overall_bl = poverty_rate(baseline_pov, pw)
overall_rf = poverty_rate(reform_pov, pw)

# Child poverty
child_bl = poverty_rate(baseline_pov, pw, is_child)
child_rf = poverty_rate(reform_pov, pw, is_child)

# People lifted out of poverty
lifted = np.sum((baseline_pov - reform_pov) * pw)
children_lifted = np.sum((baseline_pov[is_child] - reform_pov[is_child]) * pw[is_child])
```

### Deep poverty (SPM unit level)

`in_deep_poverty` is at the SPM unit level, not person level. Weight by unit size/children count:

```python
baseline_deep = baseline.calc("in_deep_poverty", period=YEAR).values
reform_deep = reformed.calc("in_deep_poverty", period=YEAR).values
spm_w = baseline.calc("spm_unit_weight", period=YEAR).values
spm_size = baseline.calc("spm_unit_size", period=YEAR).values
spm_children = baseline.calc("spm_unit_count_children", period=YEAR).values

# Overall deep poverty rate (person-weighted)
total_persons = np.sum(spm_size * spm_w)
deep_bl = np.sum(baseline_deep * spm_size * spm_w) / total_persons
deep_rf = np.sum(reform_deep * spm_size * spm_w) / total_persons

# Deep child poverty rate
total_children = np.sum(spm_children * spm_w)
deep_child_bl = np.sum(baseline_deep * spm_children * spm_w) / total_children
deep_child_rf = np.sum(reform_deep * spm_children * spm_w) / total_children
```

### When .values IS appropriate

The "never use .values" rule has one exception: **filtered/subgroup analysis** where you need boolean masking across arrays. When computing poverty rates by age, race, or other subgroups, extract `.values` and apply weights manually:

```python
# ✅ OK to use .values for filtered analysis
pw = sim.calc("person_weight", period=YEAR).values
mask = sim.calc("is_child", period=YEAR).values.astype(bool)
pov = sim.calc("person_in_poverty", period=YEAR).values
child_poverty_rate = np.sum(pov[mask] * pw[mask]) / pw[mask].sum()

# ✅ ALSO OK - MicroSeries for unfiltered totals
total_cost = reformed.calc("household_net_income", period=YEAR).sum() - \
             baseline.calc("household_net_income", period=YEAR).sum()
```

## Budgetary cost decomposition

```python
programs = ["income_tax", "ctc", "eitc", "snap", "ssi"]
for prog in programs:
    b = baseline.calc(prog, period=YEAR).sum()
    r = reformed.calc(prog, period=YEAR).sum()
    print(f"{prog}: ${(r - b) / 1e9:+.1f}B")
```

## Current law context

**Always check baseline parameter values before interpreting reform impacts.** Tax law changes frequently (TCJA, OBBBA, etc.). Use `CountryTaxBenefitSystem().parameters` to look up current-law values:

```python
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters
print(p.gov.irs.credits.ctc.amount.base("2026-01-01"))
print(p.gov.irs.credits.ctc.refundable.fully_refundable("2026-01-01"))
```

## Finding parameter paths

```bash
grep -r "salt" policyengine_us/parameters/gov/irs/ --include="*.yaml"
```

**Parameter tree:** `gov.irs.deductions`, `gov.irs.credits`, `gov.states.{state}.tax`

**Patterns:** Filing status variants (SINGLE, JOINT, etc.), bracket syntax `[index]`, date format `'YYYY-MM-DD.YYYY-MM-DD'`

## Common variables for microsimulation

### Person-level
- `person_weight` — survey weight
- `person_in_poverty` — SPM poverty indicator (boolean)
- `is_child` — under 18
- `age`, `employment_income`

### Household-level
- `household_net_income` — net income after taxes/transfers
- `household_weight` — survey weight

### SPM unit-level
- `spm_unit_weight`, `spm_unit_size`, `spm_unit_count_children`
- `in_poverty`, `in_deep_poverty`

### Tax/benefit variables
- `income_tax`, `ctc`, `eitc`, `snap`, `ssi`
