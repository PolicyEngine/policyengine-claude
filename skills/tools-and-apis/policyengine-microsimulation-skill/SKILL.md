---
name: policyengine-microsimulation
description: Run population-level policy simulations using PolicyEngine-US/UK Microsimulation with weighted microdata - national, state, and congressional district level analysis
---

# PolicyEngine Microsimulation

This skill covers running **population-level** simulations using the `Microsimulation` class with weighted survey data. This is different from household-level `Simulation` which analyzes specific families.

## When to Use Microsimulation vs Simulation

| Use Case | Class | Data Source |
|----------|-------|-------------|
| "What would a family earning $X pay in taxes?" | `Simulation` | User-defined situation |
| "What share of Americans would benefit from policy X?" | `Microsimulation` | Survey microdata |
| "How much would policy X cost nationwide?" | `Microsimulation` | Survey microdata |
| "Compare impacts in NY-17 vs national average" | `Microsimulation` | District/national microdata |

## Quick Start: National Analysis

```python
from policyengine_us import Microsimulation
from policyengine_core.reforms import Reform
import numpy as np

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
income_change = reformed_income - baseline_income

# Weighted statistics
print(f"Average impact: ${income_change.mean():,.0f}")
print(f"Total cost: ${-income_change.sum()/1e9:,.1f} billion")

# Winners/losers analysis
total_weight = income_change.weights.sum()
loser_share = income_change.weights[income_change.values < 0].sum() / total_weight
print(f"Share losing: {loser_share*100:.1f}%")
```

## Available Microdata Datasets

### Hugging Face Repository Structure

All datasets are in `policyengine/policyengine-us-data` on Hugging Face:

```
hf://policyengine/policyengine-us-data/
├── enhanced_cps_2024.h5          # National (DEFAULT)
├── states/
│   ├── NY.h5                     # New York state
│   ├── CA.h5                     # California
│   └── ...                       # All 50 states + DC
└── districts/
    ├── NY-17.h5                  # Congressional districts
    ├── CA-52.h5
    └── ...                       # All 435+ districts
```

### Loading Different Geographies

```python
# National (default - no dataset argument needed)
sim = Microsimulation()

# State-level
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/states/NY.h5')

# Congressional district level
sim = Microsimulation(dataset='hf://policyengine/policyengine-us-data/districts/NY-17.h5')
```

**Note:** District files use state abbreviation + district number (e.g., `NY-17`, `CA-52`, `TX-03`).

### HuggingFace Authentication

For private datasets, set the environment variable:
```bash
export HUGGING_FACE_TOKEN=$(cat ~/.huggingface/token)
```

Or download manually:
```python
from huggingface_hub import hf_hub_download

file_path = hf_hub_download(
    repo_id='policyengine/policyengine-us-data',
    filename='districts/NY-17.h5',
    repo_type='model',
    token=os.environ.get('HUGGING_FACE_TOKEN')
)
sim = Microsimulation(dataset=file_path)
```

## Core Calculation Methods

### calc() - Returns Weighted MicroSeries

```python
# calc() returns MicroSeries with embedded weights
income = sim.calc('household_net_income', period=2026)

# Automatic weighted operations
mean_income = income.mean()      # Weighted mean
total_income = income.sum()      # Weighted sum
median_income = income.median()  # Weighted median

# Access raw values and weights
values = income.values           # numpy array
weights = income.weights         # numpy array

# Manual weighted calculations
weighted_avg = np.average(values, weights=weights)
```

### calculate() - Returns Raw Values

```python
# calculate() returns raw numpy array (no weights)
income_values = sim.calculate('household_net_income', period=2026)
weights = sim.calculate('household_weight', period=2026)

# Manual weighted mean
weighted_mean = np.average(income_values, weights=weights)
```

### Entity Mapping with map_to

```python
# Calculate at person level, mapped from household
person_income = sim.calc('household_net_income', period=2026, map_to='person')

# Calculate at household level (default for household variables)
hh_income = sim.calc('household_net_income', period=2026, map_to='household')
```

## Common Analysis Patterns

### Pattern 1: Winners/Losers Analysis

```python
from policyengine_us import Microsimulation
from policyengine_core.reforms import Reform
import numpy as np

def analyze_winners_losers(baseline_sim, reform_sim, period=2026):
    """Calculate share of population that wins, loses, or is unchanged."""

    # Person-level analysis for population shares
    baseline = baseline_sim.calc('household_net_income', period=period, map_to='person')
    reformed = reform_sim.calc('household_net_income', period=period, map_to='person')
    change = reformed - baseline

    total_weight = change.weights.sum()

    results = {
        'total_population': total_weight,
        'loser_share': change.weights[change.values < 0].sum() / total_weight,
        'winner_share': change.weights[change.values > 0].sum() / total_weight,
        'unchanged_share': change.weights[change.values == 0].sum() / total_weight,
    }

    # Among losers
    if results['loser_share'] > 0:
        loser_vals = change.values[change.values < 0]
        loser_weights = change.weights[change.values < 0]
        results['avg_loss'] = -np.average(loser_vals, weights=loser_weights)

    return results
```

### Pattern 2: Geographic Comparison

```python
def compare_district_to_national(district_code, reform, period=2026):
    """Compare policy impact in a district vs national average."""

    # National baseline and reform
    national_baseline = Microsimulation()
    national_reformed = Microsimulation(reform=reform)

    # District baseline and reform
    district_path = f'hf://policyengine/policyengine-us-data/districts/{district_code}.h5'
    # Note: May need to download manually if HF URL parsing doesn't work
    district_baseline = Microsimulation(dataset=district_path)
    district_reformed = Microsimulation(dataset=district_path, reform=reform)

    national_results = analyze_winners_losers(national_baseline, national_reformed, period)
    district_results = analyze_winners_losers(district_baseline, district_reformed, period)

    return {
        'national': national_results,
        'district': district_results,
        'relative_impact': district_results['loser_share'] / national_results['loser_share']
    }
```

### Pattern 3: Finding Parameter Paths

To create a reform, first find the exact parameter paths:

```bash
# Search policyengine-us parameters for relevant policy
grep -r "salt" policyengine_us/parameters/gov/irs/ --include="*.yaml"
grep -r "child_tax_credit\|ctc" policyengine_us/parameters/gov/irs/credits/ --include="*.yaml"

# Read the YAML to understand structure
cat policyengine_us/parameters/gov/irs/deductions/itemized/salt_and_real_estate/cap.yaml
```

**Parameter tree structure:**
- Federal tax: `gov.irs.deductions`, `gov.irs.credits`, `gov.irs.income`
- State taxes: `gov.states.{state_code}.tax`
- Benefits: `gov.hhs` (Medicaid, TANF), `gov.usda` (SNAP), `gov.ed` (Pell)

**Key patterns:**
- Filing status variants: Many tax parameters have SINGLE, JOINT, SEPARATE, HEAD_OF_HOUSEHOLD, SURVIVING_SPOUSE
- Bracket parameters: Use `[index]` syntax, e.g., `gov.irs.credits.ctc.amount.base[0].amount`
- Date ranges: `'YYYY-MM-DD.YYYY-MM-DD'` format

```python
# After finding paths via grep, create reform
reform = Reform.from_dict({
    'gov.irs.deductions.itemized.salt_and_real_estate.cap.JOINT': {
        '2026-01-01.2100-12-31': 10000
    },
    # Include all filing statuses found in the YAML
}, 'policyengine_us')
```

## Key Variables for Policy Analysis

### Income & Taxes
- `household_net_income` - After-tax income
- `income_tax` - Federal income tax
- `payroll_tax` - Social Security and Medicare taxes
- `state_income_tax` - State income tax
- `adjusted_gross_income` - AGI for tax calculations

### Demographics
- `household_weight` - Survey weight
- `state_fips` - State FIPS code
- `congressional_district_geoid` - Congressional district code
- `age` - Person age
- `employment_income` - Wages and salaries

## Troubleshooting

### Weight Sanity Checks

```python
# National dataset should have ~150M households
weights = sim.calculate('household_weight', period=2026)
print(f"Total households: {weights.sum()/1e6:.1f}M")  # Should be ~145-150M

# District should have ~200-400k households
# State should have millions (varies by state)
```

### Memory Issues

For national simulations, memory usage can be high. Use subsampling for testing:

```python
sim = Microsimulation()
sim.subsample(10000)  # Use 10k households for testing
```
