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

## Congressional District Reference

### Key Districts by State

**New York (high-SALT impact):**
- NY-17: Mike Lawler (R) - Westchester/Rockland suburbs
- NY-03: Tom Suozzi (D) - Long Island
- NY-04: Anthony D'Esposito (R) - Long Island
- NY-16: Jamaal Bowman (D) - Westchester/Bronx

**California:**
- CA-45: Michelle Steel (R) - Orange County
- CA-47: Katie Porter (D) - Orange County
- CA-27: Mike Garcia (R) - LA suburbs

**New Jersey:**
- NJ-07: Tom Kean Jr. (R) - Central NJ suburbs
- NJ-03: Andy Kim (D) - Burlington/Ocean

### District GEOID Codes

Congressional district GEOIDs follow the pattern: `{state_fips}{district_number}`
- NY-17 = 3617 (state FIPS 36, district 17)
- CA-52 = 0652 (state FIPS 06, district 52)

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

### Pattern 3: SALT Cap Analysis

```python
def analyze_salt_cap_change(new_cap=10000, period=2026):
    """Analyze impact of changing SALT deduction cap."""

    salt_reform = Reform.from_dict({
        'gov.irs.deductions.itemized.salt_and_real_estate.cap.SINGLE': {
            f'{period}-01-01.2100-12-31': new_cap
        },
        'gov.irs.deductions.itemized.salt_and_real_estate.cap.JOINT': {
            f'{period}-01-01.2100-12-31': new_cap
        },
        'gov.irs.deductions.itemized.salt_and_real_estate.cap.SEPARATE': {
            f'{period}-01-01.2100-12-31': new_cap // 2
        },
        'gov.irs.deductions.itemized.salt_and_real_estate.cap.HEAD_OF_HOUSEHOLD': {
            f'{period}-01-01.2100-12-31': new_cap
        },
        'gov.irs.deductions.itemized.salt_and_real_estate.cap.SURVIVING_SPOUSE': {
            f'{period}-01-01.2100-12-31': new_cap
        },
    }, 'policyengine_us')

    baseline = Microsimulation()
    reformed = Microsimulation(reform=salt_reform)

    return analyze_winners_losers(baseline, reformed, period)
```

## Key Variables for Policy Analysis

### Income & Taxes
- `household_net_income` - After-tax income
- `income_tax` - Federal income tax
- `payroll_tax` - Social Security and Medicare taxes
- `state_income_tax` - State income tax
- `adjusted_gross_income` - AGI for tax calculations

### SALT-Related
- `salt_deduction` - Actual SALT deduction taken
- `salt_cap` - SALT cap amount
- `reported_salt` - Total SALT before cap
- `real_estate_taxes` - Property taxes paid
- `state_and_local_sales_or_income_tax` - State/local taxes

### Demographics
- `household_weight` - Survey weight
- `state_fips` - State FIPS code
- `congressional_district_geoid` - Congressional district code
- `age` - Person age
- `employment_income` - Wages and salaries

## Current Law Context (2026)

Under OBBBA (One Big Beautiful Bill Act, signed July 2025):

**SALT Cap:**
- 2025: $40,000 ($20k MFS)
- 2026: $40,400 ($20.2k MFS)
- 2027-2029: Annual 1% increases
- 2030+: Reverts to $10,000

**Phaseout:**
- Begins at $500k AGI ($250k MFS)
- 30% reduction rate
- Floors at $10,000

## Troubleshooting

### HuggingFace URL Parsing Issue

The `hf://` URL format expects exactly 3 path components after the protocol. For nested paths like `districts/NY-17.h5`, download manually:

```python
from huggingface_hub import hf_hub_download
import os

file_path = hf_hub_download(
    repo_id='policyengine/policyengine-us-data',
    filename='districts/NY-17.h5',
    repo_type='model',
    token=os.environ.get('HUGGING_FACE_TOKEN')
)

sim = Microsimulation(dataset=file_path)
```

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
