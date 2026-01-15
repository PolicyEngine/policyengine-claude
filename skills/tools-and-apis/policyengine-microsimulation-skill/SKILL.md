---
name: policyengine-microsimulation
description: Run population-level policy simulations using PolicyEngine-US/UK Microsimulation with weighted microdata - national, state, and congressional district level analysis
---

# PolicyEngine Microsimulation

This skill covers running **population-level** simulations using the `Microsimulation` class with weighted survey data. This is different from household-level `Simulation` which analyzes specific families.

## Documentation References

For comprehensive documentation, see:
- **Microsimulation API**: https://policyengine.github.io/policyengine-us/usage/microsimulation.html
- **Parameter Discovery**: https://policyengine.github.io/policyengine-us/usage/parameter-discovery.html
- **Reform.from_dict()**: https://policyengine.github.io/policyengine-core/usage/reforms.html

## When to Use Microsimulation vs Simulation

| Use Case | Class | Data Source |
|----------|-------|-------------|
| "What would a family earning $X pay in taxes?" | `Simulation` | User-defined situation |
| "What share of Americans would benefit from policy X?" | `Microsimulation` | Survey microdata |
| "How much would policy X cost nationwide?" | `Microsimulation` | Survey microdata |
| "Compare impacts in NY-17 vs national average" | `Microsimulation` | District/national microdata |

## Quick Start

```python
from policyengine_us import Microsimulation
from policyengine_core.reforms import Reform

# Load national enhanced CPS (default dataset)
baseline = Microsimulation()

# Define a reform
reform = Reform.from_dict({
    'gov.irs.credits.ctc.amount.base[0].amount': {
        '2026-01-01.2100-12-31': 3000
    }
}, 'policyengine_us')

reformed = Microsimulation(reform=reform)

# Calculate impacts (calc() returns weighted MicroSeries)
baseline_income = baseline.calc('household_net_income', period=2026)
reformed_income = reformed.calc('household_net_income', period=2026)
change = reformed_income - baseline_income

# Weighted statistics
print(f"Average impact: ${change.mean():,.0f}")
print(f"Total cost: ${-change.sum()/1e9:,.1f} billion")

# Winners/losers
loser_share = change.weights[change.values < 0].sum() / change.weights.sum()
print(f"Share losing: {loser_share*100:.1f}%")
```

## Available Datasets (HuggingFace)

All datasets are in `policyengine/policyengine-us-data`:

```
hf://policyengine/policyengine-us-data/
├── enhanced_cps_2024.h5          # National (DEFAULT)
├── states/
│   ├── NY.h5, CA.h5, ...         # All 50 states + DC
└── districts/
    ├── NY-17.h5, CA-52.h5, ...   # All 435+ congressional districts
```

```python
# National (default)
sim = Microsimulation()

# State-level
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/states/NY.h5')

# Congressional district
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/districts/NY-17.h5')
```

## Key Methods

### calc() - Returns Weighted MicroSeries

```python
income = sim.calc('household_net_income', period=2026)
income.mean()      # Weighted mean
income.sum()       # Weighted sum
income.median()    # Weighted median
income.values      # Raw numpy array
income.weights     # Weight array
```

### map_to - Entity Mapping

```python
# Map household variable to person level (for person-weighted stats)
person_income = sim.calc('household_net_income', period=2026, map_to='person')
```

## Finding Parameter Paths

To create a reform, find the parameter paths in policyengine-us:

```bash
# Search parameters directory
grep -r "salt" policyengine_us/parameters/gov/irs/ --include="*.yaml"

# Read YAML to understand structure
cat policyengine_us/parameters/gov/irs/deductions/itemized/salt_and_real_estate/cap.yaml
```

**Parameter tree structure:**
- Federal tax: `gov.irs.deductions`, `gov.irs.credits`, `gov.irs.income`
- State taxes: `gov.states.{state_code}.tax`
- Benefits: `gov.hhs`, `gov.usda`, `gov.ed`

**Key patterns:**
- Filing status variants: SINGLE, JOINT, SEPARATE, HEAD_OF_HOUSEHOLD, SURVIVING_SPOUSE
- Bracket parameters: `[index]` syntax, e.g., `gov.irs.credits.ctc.amount.base[0].amount`
- Date ranges: `'YYYY-MM-DD.YYYY-MM-DD'` format

## Weight Sanity Checks

```python
# National: ~130M households, ~330M people
weights = sim.calc('household_weight')
print(f"Total households: {weights.sum()/1e6:.0f}M")

# District: ~200-400k households
# State: varies (CA ~14M, WY ~250k)
```

## Performance Tips

```python
# Subsample for faster development
sim = Microsimulation()
sim.subsample(10_000)  # Use 10k households
```
