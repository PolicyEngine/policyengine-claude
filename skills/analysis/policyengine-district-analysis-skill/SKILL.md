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

## Documentation References

- **Microsimulation API**: https://policyengine.github.io/policyengine-us/usage/microsimulation.html
- **Parameter Discovery**: https://policyengine.github.io/policyengine-us/usage/parameter-discovery.html
- **Reform.from_dict()**: https://policyengine.github.io/policyengine-core/usage/reforms.html

## When to Use This Skill

Use this skill when the user asks:
- "What share of people in [rep]'s district would lose/gain from [policy]?"
- "Analyze [district code like NY-17 or CA-52]"
- "How would [policy] affect [representative]'s constituents?"
- "Compare [district] to national average for [policy]"

## Workflow

### 1. Load District Data

Congressional district microdata is on HuggingFace at `policyengine/policyengine-us-data/districts/`:

```python
from policyengine_us import Microsimulation

district_code = "NY-17"  # Format: {STATE}-{DISTRICT_NUMBER}
district_sim = Microsimulation(
    dataset=f'hf://policyengine/policyengine-us-data/districts/{district_code}.h5'
)
```

### 2. Find Parameter Paths

Search policyengine-us to find the relevant parameters:

```bash
grep -r "salt" policyengine_us/parameters/gov/irs/ --include="*.yaml"
cat policyengine_us/parameters/gov/irs/deductions/itemized/salt_and_real_estate/cap.yaml
```

### 3. Define Reform

```python
from policyengine_core.reforms import Reform

reform = Reform.from_dict({
    'gov.irs.deductions.itemized.salt_and_real_estate.cap.JOINT': {
        '2026-01-01.2100-12-31': 10000
    },
    # Include all filing statuses from the YAML
}, 'policyengine_us')
```

### 4. Run Comparison

```python
from policyengine_us import Microsimulation
import numpy as np

# District
district_baseline = Microsimulation(dataset=f'hf://policyengine/policyengine-us-data/districts/{district_code}.h5')
district_reformed = Microsimulation(dataset=f'hf://policyengine/policyengine-us-data/districts/{district_code}.h5', reform=reform)

# National
national_baseline = Microsimulation()
national_reformed = Microsimulation(reform=reform)

# Calculate at person level for population shares
def get_loser_share(baseline, reformed, period=2026):
    baseline_inc = baseline.calc('household_net_income', period=period, map_to='person')
    reformed_inc = reformed.calc('household_net_income', period=period, map_to='person')
    change = reformed_inc - baseline_inc
    return change.weights[change.values < 0].sum() / change.weights.sum()

district_loser_share = get_loser_share(district_baseline, district_reformed)
national_loser_share = get_loser_share(national_baseline, national_reformed)

print(f"District: {district_loser_share:.1%} lose")
print(f"National: {national_loser_share:.1%} lose")
print(f"Relative impact: {district_loser_share/national_loser_share:.1f}x")
```

### 5. Present Results

```markdown
## [Policy] Impact: [District] vs National

| Metric | [District] | National | Difference |
|--------|------------|----------|------------|
| Share losing | X.X% | Y.Y% | +Z.Z pp |
| Average loss | $X,XXX | $Y,YYY | +$Z,ZZZ |

**Key takeaway**: [District] residents are [X]x more affected because...
```

## Weight Sanity Checks

- National: ~130M households, ~330M people
- District: ~200-400k households typically
- State: varies (CA ~14M, WY ~250k)
