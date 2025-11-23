---
name: microdf
description: Weighted pandas DataFrames for survey microdata analysis - inequality, poverty, and distributional calculations
---

# MicroDF

MicroDF provides weighted pandas DataFrames and Series for analyzing survey microdata, with built-in support for inequality and poverty calculations.

## For Users 👥

### What is MicroDF?

When you see poverty rates, Gini coefficients, or distributional charts in PolicyEngine, those are calculated using MicroDF.

**MicroDF powers:**
- Poverty rate calculations (SPM)
- Inequality metrics (Gini coefficient)
- Income distribution analysis
- Weighted statistics from survey data

### Understanding the Metrics

**Gini coefficient:**
- Calculated using MicroDF from weighted income data
- Ranges from 0 (perfect equality) to 1 (perfect inequality)
- US typically around 0.48

**Poverty rates:**
- Calculated using MicroDF with weighted household data
- Compares income to poverty thresholds
- Accounts for household composition

**Percentiles:**
- MicroDF calculates weighted percentiles
- Shows income distribution (10th, 50th, 90th percentile)

## For Analysts 📊

### Installation

```bash
pip install microdf-python
```

### Quick Start

```python
import microdf as mdf
import pandas as pd

# Create sample data
df = pd.DataFrame({
    'income': [10000, 20000, 30000, 40000, 50000],
    'weights': [1, 2, 3, 2, 1]
})

# Create MicroDataFrame
mdf_df = mdf.MicroDataFrame(df, weights='weights')

# All operations are weight-aware
print(f"Weighted mean: ${mdf_df.income.mean():,.0f}")
print(f"Gini coefficient: {mdf_df.income.gini():.3f}")
```

### Common Operations

**Weighted statistics:**
```python
mdf_df.income.mean()     # Weighted mean
mdf_df.income.median()   # Weighted median
mdf_df.income.sum()      # Weighted sum
mdf_df.income.std()      # Weighted standard deviation
```

**Inequality metrics:**
```python
mdf_df.income.gini()     # Gini coefficient
mdf_df.income.top_x_pct_share(10)  # Top 10% share
mdf_df.income.top_x_pct_share(1)   # Top 1% share
```

**Poverty analysis:**
```python
# Poverty rate (income < threshold)
poverty_rate = mdf_df.poverty_rate(
    income_measure='income',
    threshold=poverty_line
)

# Poverty gap (how far below threshold)
poverty_gap = mdf_df.poverty_gap(
    income_measure='income',
    threshold=poverty_line
)

# Deep poverty (income < 50% of threshold)
deep_poverty_rate = mdf_df.deep_poverty_rate(
    income_measure='income',
    threshold=poverty_line,
    deep_poverty_line=0.5
)
```

**Quantiles:**
```python
# Deciles
mdf_df.income.decile_values()

# Quintiles
mdf_df.income.quintile_values()

# Custom quantiles
mdf_df.income.quantile(0.25)  # 25th percentile
```

### MicroSeries

```python
# Extract a Series with weights
income_series = mdf_df.income  # This is a MicroSeries

# MicroSeries operations
income_series.mean()
income_series.gini()
income_series.percentile(50)
```

### Working with PolicyEngine Results

```python
import microdf as mdf
from policyengine_us import Simulation

# Run simulation with axes (multiple households)
situation_with_axes = {...}  # See policyengine-us-skill
sim = Simulation(situation=situation_with_axes)

# Get results as arrays
incomes = sim.calculate("household_net_income", 2024)
weights = sim.calculate("household_weight", 2024)

# Create MicroDataFrame
df = pd.DataFrame({'income': incomes, 'weight': weights})
mdf_df = mdf.MicroDataFrame(df, weights='weight')

# Calculate metrics
gini = mdf_df.income.gini()
poverty_rate = mdf_df.poverty_rate('income', threshold=15000)

print(f"Gini: {gini:.3f}")
print(f"Poverty rate: {poverty_rate:.1%}")
```

## For Contributors 💻

### Repository

**Location:** PolicyEngine/microdf

**Clone:**
```bash
git clone https://github.com/PolicyEngine/microdf
cd microdf
```

### Current Implementation

**To see current API:**
```bash
# Main classes
cat microdf/microframe.py   # MicroDataFrame
cat microdf/microseries.py  # MicroSeries

# Key modules
cat microdf/generic.py      # Generic weighted operations
cat microdf/inequality.py   # Gini, top shares
cat microdf/poverty.py      # Poverty metrics
```

**To see all methods:**
```bash
# MicroDataFrame methods
grep "def " microdf/microframe.py

# MicroSeries methods
grep "def " microdf/microseries.py
```

### Testing

**To see test patterns:**
```bash
ls tests/
cat tests/test_microframe.py
```

**Run tests:**
```bash
make test

# Or
pytest tests/ -v
```

### Contributing

**Before contributing:**
1. Check if method already exists
2. Ensure it's weighted correctly
3. Add tests
4. Follow policyengine-standards-skill

**Common contributions:**
- New inequality metrics
- New poverty measures
- Performance optimizations
- Bug fixes

## Advanced Patterns

### Custom Aggregations

```python
# Define custom weighted aggregation
def weighted_operation(series, weights):
    return (series * weights).sum() / weights.sum()

# Apply to MicroSeries
result = weighted_operation(mdf_df.income, mdf_df.weights)
```

### Groupby Operations

```python
# Group by with weights
grouped = mdf_df.groupby('state')
state_means = grouped.income.mean()  # Weighted means by state
```

### Inequality Decomposition

**To see decomposition methods:**
```bash
grep -A 20 "def.*decomp" microdf/
```

## Integration Examples

### Example 1: PolicyEngine Blog Post Analysis

```python
# Pattern from PolicyEngine blog posts
import microdf as mdf

# Get simulation results
baseline_income = baseline_sim.calculate("household_net_income", 2024)
reform_income = reform_sim.calculate("household_net_income", 2024)
weights = baseline_sim.calculate("household_weight", 2024)

# Create MicroDataFrame
df = pd.DataFrame({
    'baseline_income': baseline_income,
    'reform_income': reform_income,
    'weight': weights
})
mdf_df = mdf.MicroDataFrame(df, weights='weight')

# Calculate impacts
baseline_gini = mdf_df.baseline_income.gini()
reform_gini = mdf_df.reform_income.gini()

print(f"Gini change: {reform_gini - baseline_gini:+.4f}")
```

### Example 2: Poverty Analysis

```python
# Calculate poverty under baseline and reform
from policyengine_us import Simulation

baseline_sim = Simulation(situation=situation)
reform_sim = Simulation(situation=situation, reform=reform)

# Get incomes
baseline_income = baseline_sim.calculate("spm_unit_net_income", 2024)
reform_income = reform_sim.calculate("spm_unit_net_income", 2024)
spm_threshold = baseline_sim.calculate("spm_unit_poverty_threshold", 2024)
weights = baseline_sim.calculate("spm_unit_weight", 2024)

# Calculate poverty rates
df_baseline = mdf.MicroDataFrame(
    pd.DataFrame({'income': baseline_income, 'threshold': spm_threshold, 'weight': weights}),
    weights='weight'
)

poverty_baseline = (df_baseline.income < df_baseline.threshold).mean()  # Weighted

# Similar for reform
print(f"Poverty reduction: {(poverty_baseline - poverty_reform):.1%}")
```

## Package Status

**Maturity:** Stable, production-ready
**API stability:** Stable (rarely breaking changes)
**Performance:** Optimized for large datasets

**To see version:**
```bash
pip show microdf-python
```

**To see changelog:**
```bash
cat CHANGELOG.md  # In microdf repo
```

## Related Skills

- **policyengine-us-skill** - Generating data for microdf analysis
- **policyengine-analysis-skill** - Using microdf in policy analysis
- **policyengine-us-data-skill** - Data sources for microdf

## Resources

**Repository:** https://github.com/PolicyEngine/microdf
**PyPI:** https://pypi.org/project/microdf-python/
**Issues:** https://github.com/PolicyEngine/microdf/issues
