---
name: microcalibrate
description: Survey weight calibration to match population targets - used in policyengine-us-data for enhanced microdata
---

# MicroCalibrate

MicroCalibrate calibrates survey weights to match population targets, with L0 regularization for sparsity and automatic hyperparameter tuning.

## For Users 👥

### What is MicroCalibrate?

When you see PolicyEngine population impacts, the underlying data has been "calibrated" using MicroCalibrate to match official population statistics.

**What calibration does:**
- Adjusts survey weights to match known totals (population, income, employment)
- Creates representative datasets
- Reduces dataset size while maintaining accuracy
- Ensures PolicyEngine estimates match administrative data

**Example:**
- Census says US has 331 million people
- Survey has 100,000 households representing the population
- MicroCalibrate adjusts weights so survey totals match census totals
- Result: More accurate PolicyEngine calculations

## For Analysts 📊

### Installation

```bash
pip install microcalibrate
```

### What MicroCalibrate Does

**Calibration problem:**
You have survey data with initial weights, and you know certain population totals (benchmarks). Calibration adjusts weights so weighted survey totals match benchmarks.

**Example:**
```python
from microcalibrate import Calibration
import numpy as np
import pandas as pd

# Survey data (1,000 households)
weights = np.ones(1000)  # Initial weights

# Estimates (how much each household contributes to targets)
estimate_matrix = pd.DataFrame({
    'total_income': household_incomes,      # Each household's income
    'total_employed': household_employment  # 1 if employed, 0 if not
})

# Known population targets (benchmarks)
targets = np.array([
    50_000_000,  # Total income in population
    600,         # Total employed people
])

# Calibrate
cal = Calibration(
    weights=weights,
    targets=targets,
    estimate_matrix=estimate_matrix,
    l0_lambda=0.01  # Sparsity penalty
)

# Optimize weights
new_weights = cal.calibrate(max_iter=1000)

# Check results
achieved = (estimate_matrix.values.T @ new_weights)
print(f"Target: {targets}")
print(f"Achieved: {achieved}")
print(f"Non-zero weights: {(new_weights > 0).sum()} / {len(weights)}")
```

### L0 Regularization for Sparsity

**Why sparsity matters:**
- Reduces dataset size (fewer households to simulate)
- Faster PolicyEngine calculations
- Easier to validate and understand

**L0 penalty:**
```python
# L0 encourages many weights to be exactly zero
cal = Calibration(
    weights=weights,
    targets=targets,
    estimate_matrix=estimate_matrix,
    l0_lambda=0.01  # Higher = more sparse
)
```

**To see impact:**
```python
# Without L0
cal_dense = Calibration(..., l0_lambda=0.0)
weights_dense = cal_dense.calibrate()

# With L0
cal_sparse = Calibration(..., l0_lambda=0.01)
weights_sparse = cal_sparse.calibrate()

print(f"Dense: {(weights_dense > 0).sum()} households")
print(f"Sparse: {(weights_sparse > 0).sum()} households")
# Sparse might use 60% fewer households while matching same targets
```

### Automatic Hyperparameter Tuning

**Find optimal l0_lambda:**
```python
from microcalibrate import tune_hyperparameters

# Find best l0_lambda using cross-validation
best_lambda, results = tune_hyperparameters(
    weights=weights,
    targets=targets,
    estimate_matrix=estimate_matrix,
    lambda_min=1e-4,
    lambda_max=1e-1,
    n_trials=50
)

print(f"Best lambda: {best_lambda}")
```

### Robustness Evaluation

**Test calibration stability:**
```python
from microcalibrate import evaluate_robustness

# Holdout validation
robustness = evaluate_robustness(
    weights=weights,
    targets=targets,
    estimate_matrix=estimate_matrix,
    l0_lambda=0.01,
    n_folds=5
)

print(f"Mean error: {robustness['mean_error']}")
print(f"Std error: {robustness['std_error']}")
```

### Interactive Dashboard

**Visualize calibration:**
https://microcalibrate.vercel.app/

Features:
- Upload survey data
- Set targets
- Tune hyperparameters
- View results
- Download calibrated weights

## For Contributors 💻

### Repository

**Location:** PolicyEngine/microcalibrate

**Clone:**
```bash
git clone https://github.com/PolicyEngine/microcalibrate
cd microcalibrate
```

### Current Implementation

**To see structure:**
```bash
tree microcalibrate/

# Key modules:
ls microcalibrate/
# - calibration.py - Main Calibration class
# - hyperparameter_tuning.py - Optuna integration
# - evaluation.py - Robustness testing
# - target_analysis.py - Target diagnostics
```

**To see specific implementations:**
```bash
# Main calibration algorithm
cat microcalibrate/calibration.py

# Hyperparameter tuning
cat microcalibrate/hyperparameter_tuning.py

# Robustness evaluation
cat microcalibrate/evaluation.py
```

### Dependencies

**Required:**
- torch (PyTorch for optimization)
- l0-python (L0 regularization)
- optuna (hyperparameter tuning)
- numpy, pandas, tqdm

**To see all dependencies:**
```bash
cat pyproject.toml
```

### How MicroCalibrate Uses L0

```python
# Internal to microcalibrate
from l0 import HardConcrete

# Create gates for sample selection
gates = HardConcrete(
    n_items=len(weights),
    temperature=temperature,
    init_mean=0.999
)

# Apply gates during optimization
effective_weights = weights * gates()

# L0 penalty encourages gates → 0 or 1
# Result: Many households get weight = 0 (sparse)
```

**To see L0 integration:**
```bash
grep -n "HardConcrete\|l0" microcalibrate/calibration.py
```

### Optimization Algorithm

**Iterative reweighting:**
1. Start with initial weights
2. Apply L0 gates (select samples)
3. Optimize to match targets
4. Apply penalty for sparsity
5. Iterate until convergence

**Loss function:**
```python
# Target matching loss
target_loss = sum((achieved_targets - desired_targets)^2)

# L0 penalty (number of non-zero weights)
l0_penalty = l0_lambda * count_nonzero(weights)

# Total loss
total_loss = target_loss + l0_penalty
```

### Testing

**Run tests:**
```bash
make test

# Or
pytest tests/ -v
```

**To see test patterns:**
```bash
cat tests/test_calibration.py
cat tests/test_hyperparameter_tuning.py
```

### Usage in policyengine-us-data

**To see how data pipeline uses microcalibrate:**
```bash
cd ../policyengine-us-data

# Find usage
grep -r "microcalibrate" policyengine_us_data/
grep -r "Calibration" policyengine_us_data/
```

## Common Patterns

### Pattern 1: Basic Calibration

```python
from microcalibrate import Calibration

cal = Calibration(
    weights=initial_weights,
    targets=benchmark_values,
    estimate_matrix=contributions,
    l0_lambda=0.01
)

calibrated_weights = cal.calibrate(max_iter=1000)
```

### Pattern 2: With Hyperparameter Tuning

```python
from microcalibrate import tune_hyperparameters, Calibration

# Find best lambda
best_lambda, results = tune_hyperparameters(
    weights=weights,
    targets=targets,
    estimate_matrix=estimate_matrix
)

# Use best lambda
cal = Calibration(..., l0_lambda=best_lambda)
calibrated_weights = cal.calibrate()
```

### Pattern 3: Multi-Target Calibration

```python
# Multiple population targets
estimate_matrix = pd.DataFrame({
    'total_population': population_counts,
    'total_income': incomes,
    'total_employed': employment_indicators,
    'total_children': child_counts
})

targets = np.array([
    331_000_000,   # US population
    15_000_000_000_000,  # Total income
    160_000_000,   # Employed people
    73_000_000     # Children
])

cal = Calibration(weights, targets, estimate_matrix, l0_lambda=0.01)
```

## Performance Considerations

**Calibration speed:**
- 1,000 households, 5 targets: ~1 second
- 100,000 households, 10 targets: ~30 seconds
- Depends on: dataset size, number of targets, l0_lambda

**Memory usage:**
- PyTorch tensors for optimization
- Scales linearly with dataset size

**To profile:**
```python
import time

start = time.time()
weights = cal.calibrate()
print(f"Calibration took {time.time() - start:.1f}s")
```

## Troubleshooting

**Common issues:**

**1. Calibration not converging:**
```python
# Try:
# - More iterations
# - Lower l0_lambda
# - Better initialization

cal = Calibration(..., l0_lambda=0.001)  # Lower sparsity penalty
weights = cal.calibrate(max_iter=5000)  # More iterations
```

**2. Targets not matching:**
```python
# Check achieved vs desired
achieved = (estimate_matrix.values.T @ weights)
error = np.abs(achieved - targets) / targets
print(f"Relative errors: {error}")

# If large errors, l0_lambda may be too high
```

**3. Too sparse (all weights zero):**
```python
# Lower l0_lambda
cal = Calibration(..., l0_lambda=0.0001)
```

## Related Skills

- **l0-skill** - Understanding L0 regularization
- **policyengine-us-data-skill** - How calibration fits in data pipeline
- **microdf-skill** - Working with calibrated survey data

## Resources

**Repository:** https://github.com/PolicyEngine/microcalibrate
**Dashboard:** https://microcalibrate.vercel.app/
**PyPI:** https://pypi.org/project/microcalibrate/
**Paper:** Louizos et al. (2017) on L0 regularization
