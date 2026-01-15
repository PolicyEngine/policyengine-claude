---
name: policyengine-district-analysis
description: |
  Analyzes policy impacts at the congressional district level using PolicyEngine microsimulation.
  Use when analyzing a specific congressional district, asking about policy impacts in a representative's district,
  questions like "analyze NY-17", "what share of people in Mike Lawler's district would lose from...",
  "how would [policy] affect [representative]'s constituents", "compare [district] to national average",
  or any district-level policy simulation questions.
---

# Congressional District Policy Analysis

This skill enables district-level policy impact analysis using PolicyEngine microsimulation with weighted survey data.

## When to Use This Skill

Use this skill when the user asks:
- "What share of people in [rep]'s district would lose/gain from [policy]?"
- "Analyze [district code like NY-17 or CA-52]"
- "How would [policy] affect [representative]'s constituents?"
- "Compare [district] to national average for [policy]"
- "District-level impact of [policy change]"

## Step-by-Step Workflow

### Download District Data

Congressional district microdata is on HuggingFace. The URL parser in policyengine-core doesn't handle nested paths, so download manually:

```python
from huggingface_hub import hf_hub_download
import os

# Set token if needed
os.environ['HUGGING_FACE_TOKEN'] = open(os.path.expanduser('~/.huggingface/token')).read().strip()

# Download district file (e.g., NY-17)
district_code = "NY-17"  # Format: {STATE}-{DISTRICT_NUMBER}
file_path = hf_hub_download(
    repo_id='policyengine/policyengine-us-data',
    filename=f'districts/{district_code}.h5',
    repo_type='model',
    token=os.environ.get('HUGGING_FACE_TOKEN')
)
```

### Define the Policy Reform

Use `Reform.from_dict()` to define parameter changes. Common examples:

**SALT Cap Change:**
```python
from policyengine_core.reforms import Reform

salt_reform = Reform.from_dict({
    'gov.irs.deductions.itemized.salt_and_real_estate.cap.SINGLE': {
        '2026-01-01.2100-12-31': 10000  # New cap amount
    },
    'gov.irs.deductions.itemized.salt_and_real_estate.cap.JOINT': {
        '2026-01-01.2100-12-31': 10000
    },
    'gov.irs.deductions.itemized.salt_and_real_estate.cap.SEPARATE': {
        '2026-01-01.2100-12-31': 5000
    },
    'gov.irs.deductions.itemized.salt_and_real_estate.cap.HEAD_OF_HOUSEHOLD': {
        '2026-01-01.2100-12-31': 10000
    },
    'gov.irs.deductions.itemized.salt_and_real_estate.cap.SURVIVING_SPOUSE': {
        '2026-01-01.2100-12-31': 10000
    },
}, 'policyengine_us')
```

**Child Tax Credit Change:**
```python
ctc_reform = Reform.from_dict({
    'gov.irs.credits.ctc.amount.base[0].amount': {
        '2026-01-01.2100-12-31': 3000  # New CTC amount per child
    }
}, 'policyengine_us')
```

### Run District and National Simulations

```python
from policyengine_us import Microsimulation
import numpy as np

# District simulation
district_baseline = Microsimulation(dataset=file_path)
district_reformed = Microsimulation(dataset=file_path, reform=reform)

# National simulation for comparison
national_baseline = Microsimulation()  # Uses default enhanced_cps_2024.h5
national_reformed = Microsimulation(reform=reform)

period = 2026  # Or relevant year
```

### Calculate Winners/Losers

```python
def analyze_impact(baseline_sim, reform_sim, period=2026):
    """Calculate share who win, lose, and amounts."""

    # Person-level for population shares
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

    # Average loss among losers
    if results['loser_share'] > 0:
        loser_vals = change.values[change.values < 0]
        loser_weights = change.weights[change.values < 0]
        results['avg_loss'] = -np.average(loser_vals, weights=loser_weights)

    # Average gain among winners
    if results['winner_share'] > 0:
        winner_vals = change.values[change.values > 0]
        winner_weights = change.weights[change.values > 0]
        results['avg_gain'] = np.average(winner_vals, weights=winner_weights)

    # Overall impact
    results['avg_impact'] = np.average(change.values, weights=change.weights)
    results['total_impact'] = (change.values * change.weights).sum()

    return results

# Run analysis
district_results = analyze_impact(district_baseline, district_reformed, period)
national_results = analyze_impact(national_baseline, national_reformed, period)
```

### Present Results

Format results as a comparison table:

```
## [Policy] Impact: [District] vs National

| Metric | [District] | National | Difference |
|--------|------------|----------|------------|
| Share of people losing | X.X% | Y.Y% | +Z.Z pp |
| Average loss among losers | $X,XXX | $Y,YYY | +$Z,ZZZ |
| Average impact per household | -$XXX | -$YYY | -$ZZZ |

### Key Takeaway
[District] residents are [X]x more/less affected than the national average because...
```

## Current Law Context (2026)

**SALT Cap under OBBBA (signed July 2025):**
- 2025: $40,000 ($20k MFS)
- 2026: $40,400 ($20.2k MFS)
- 2027-2029: Annual 1% increases
- 2030+: Reverts to $10,000
- Phaseout: Begins at $500k AGI, 30% rate, floors at $10k

**Child Tax Credit:**
- 2025: $2,000/child (TCJA rates extended)
- Refundable portion varies by year

## Common Analysis Requests

1. **"What share would lose from cutting SALT to $10k?"**
   - Compare current law ($40k cap) to $10k cap
   - Report loser_share and avg_loss

2. **"How does [district] compare to national?"**
   - Run both district and national simulations
   - Report relative impact (district / national ratios)

3. **"Impact of [CTC/EITC/etc.] expansion in [district]"**
   - Define reform for the relevant credit
   - Report winner_share and avg_gain

## Troubleshooting

**HuggingFace authentication:**
```bash
# If prompted for token, set environment variable
export HUGGING_FACE_TOKEN=$(cat ~/.huggingface/token)
```

**Memory issues with national simulation:**
```python
sim = Microsimulation()
sim.subsample(10000)  # Use 10k households for testing
```

**Verify weights make sense:**
- National: ~145-150M households
- State: Varies (CA ~14M, WY ~250k)
- District: ~175-400k households typically
