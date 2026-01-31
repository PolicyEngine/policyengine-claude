---
name: policyengine-us-data
description: US survey data enhancement - CPS with PUF imputation patterns and cross-repo variable workflows
---

# PolicyEngine US Data

PolicyEngine US Data provides enhanced Current Population Survey (CPS) datasets with imputed variables from the IRS Public Use File (PUF).

## For Users

### What is policyengine-us-data?

PolicyEngine US uses the CPS ASEC as its primary microdata source. The CPS contains household demographics, income, and benefits but lacks detailed tax information. The IRS PUF provides comprehensive tax data but is restricted access. This package imputes tax-related variables from PUF to CPS.

**Key datasets:**
- **CPS ASEC (Current Population Survey Annual Social and Economic Supplement):** Main US household survey with ~200,000 people
- **IRS PUF (Public Use File):** Tax return data with detailed income components
- **Enhanced CPS:** CPS with imputed tax variables from PUF

## For Analysts

### Repository

**Location:** PolicyEngine/policyengine-us-data

**Clone:**
```bash
git clone https://github.com/PolicyEngine/policyengine-us-data
cd policyengine-us-data
```

### Structure

```
policyengine_us_data/
├── datasets/
│   ├── cps/               # CPS ASEC processing
│   │   ├── census_cps.py  # Raw CPS loader
│   │   └── cps.py         # CPS enhancement
│   └── puf/               # PUF imputation
│       ├── irs_puf.py     # Raw PUF loader
│       └── puf.py         # PUF-to-CPS imputation
└── storage/               # Data storage utilities
```

### Installation

**From PyPI:**
```bash
pip install policyengine-us-data
```

**Development:**
```bash
pip install -e .
```

## CRITICAL: Cross-Repo Variable Workflow

### When Adding a New Variable That Spans Both Repos

**This is the #1 source of CI failures when adding new data-backed variables.**

When you add a new variable that:
1. Has a definition in **policyengine-us** (the variable class)
2. Gets its data from **policyengine-us-data** (extracted from PUF/CPS)

You MUST follow this workflow:

### The Problem

The `puf.py` file filters `FINANCIAL_SUBSET` to only include variables that exist in policyengine-us:

```python
# In puf.py
self.available_financial_vars = [
    v for v in FINANCIAL_SUBSET if v in self.variable_to_entity
]
```

If policyengine-us doesn't have the variable yet, it gets **silently skipped** during data generation.

### The Solution: Correct PR Ordering

**Step 1: Create and merge the policyengine-us PR first**
```
# In policyengine-us
1. Add variable definition (e.g., partnership_se_income.py)
2. Add to relevant formulas
3. Merge PR
4. Wait for PyPI release (automatic, check pypi.org/project/policyengine-us)
```

**Step 2: Note the released version number**
```bash
# Check latest version
curl -s https://pypi.org/pypi/policyengine-us/json | jq '.info.version'
```

**Step 3: Create the policyengine-us-data PR with version bump**
```
# In policyengine-us-data
1. Add data extraction in puf.py (e.g., puf["partnership_se_income"] = ...)
2. Add to FINANCIAL_SUBSET list in puf.py
3. CRITICAL: Add to IMPUTED_VARIABLES in extended_cps.py
   - This is a SEPARATE list that controls what gets imputed into Enhanced CPS!
4. CRITICAL: Bump minimum version in pyproject.toml:
   - "policyengine-us>=1.516.0"  # Version with new variable
5. Run `uv lock` to update lockfile
6. Merge PR
```

**IMPORTANT: There are TWO variable lists!**
- `FINANCIAL_SUBSET` in `puf.py` - controls what data is extracted from PUF
- `IMPUTED_VARIABLES` in `extended_cps.py` - controls what gets imputed into Enhanced CPS

If you only add to one, the variable will be extracted but not imputed!

### Why Version Bumping Matters

The CI uses whatever policyengine-us version satisfies the pyproject.toml constraint:

```toml
# If pyproject.toml says:
"policyengine-us>=1.353.0"

# CI might install 1.499.0 (satisfies constraint but lacks new variable)
# Your variable gets silently skipped!

# Fix: bump to version with your variable
"policyengine-us>=1.516.0"  # Now CI installs 1.516.0+ with your variable
```

### Example: partnership_se_income

**Correct workflow that was followed:**

1. **policyengine-us PR #7239** - Added `partnership_se_income` variable
   - Merged → Released as version 1.516.0

2. **policyengine-us-data PR #481** - Added data extraction
   - Added `puf["partnership_se_income"] = k1bx14p + k1bx14s`
   - Added to `FINANCIAL_SUBSET`
   - But initially forgot to bump version!

3. **Fix commit** - Bumped minimum version
   - Changed `"policyengine-us>=1.353.0"` to `"policyengine-us>=1.516.0"`
   - Ran `uv lock`
   - Triggered rebuild → Data now includes the variable

### Common Mistakes

**Mistake 1: Merging us-data before us releases**
```
❌ Merge us-data PR while us PR still pending
   → Variable doesn't exist → Gets skipped → Data missing variable
```

**Mistake 2: Not bumping the minimum version**
```
❌ Add variable to FINANCIAL_SUBSET but keep old version constraint
   → CI installs old policyengine-us → Variable doesn't exist → Gets skipped
```

**Mistake 3: Checking data before rebuild completes**
```
❌ Run microsim right after merging
   → Still using old cached data → Variable shows $0
   → Need to wait for CI or `pip install --upgrade policyengine-us-data`
```

### Checklist for New Data-Backed Variables

- [ ] Create policyengine-us PR with variable definition
- [ ] Merge policyengine-us PR
- [ ] Note the PyPI version number that includes the variable
- [ ] Create policyengine-us-data PR with:
  - [ ] Data extraction code in puf.py
  - [ ] Variable name in FINANCIAL_SUBSET (puf.py)
  - [ ] Variable name in IMPUTED_VARIABLES (extended_cps.py) ⚠️ **Don't forget this!**
  - [ ] Bumped minimum policyengine-us version in pyproject.toml
  - [ ] Updated uv.lock via `uv lock`
- [ ] Merge policyengine-us-data PR
- [ ] Wait for CI to complete (~1 hour)
- [ ] Verify with microsim that variable has non-zero values

## For Contributors

### Adding a New PUF Variable

**1. Identify PUF columns:**
```python
# Check PUF documentation for column names
# e.g., k1bx14p = taxpayer's K-1 Box 14 partnership SE income
```

**2. Add extraction in puf.py:**
```python
# In _create_financial_variables method or similar
puf["my_new_variable"] = puf["puf_column"]

# Or derive from multiple columns:
puf["my_new_variable"] = puf["col1"] + puf["col2"]
```

**3. Add to FINANCIAL_SUBSET:**
```python
FINANCIAL_SUBSET = [
    # ... existing variables ...
    "my_new_variable",  # Add at end
]
```

**4. Bump policyengine-us version (if new variable):**
```toml
# pyproject.toml
dependencies = [
    "policyengine-us>=X.Y.Z",  # Version with my_new_variable
]
```

### Testing

**Local test (requires PUF access):**
```bash
make test
```

**CI test:**
The GitHub Actions CI has PUF access via secrets. Push to a branch and check the workflow.

### Common PUF Columns

| PUF Column | Description | Target Variable |
|------------|-------------|-----------------|
| e00200 | Wages and salaries | employment_income |
| e00300 | Taxable interest | taxable_interest_income |
| e00600 | Ordinary dividends | dividend_income |
| e00900 | Business income (Schedule C) | self_employment_income |
| e02100 | Farm income (Schedule F) | farm_income |
| k1bx14p | K-1 Box 14 (taxpayer) | partnership_se_income |
| k1bx14s | K-1 Box 14 (spouse) | partnership_se_income |

## Integration with PolicyEngine US

**Usage flow:**
```
1. Load raw CPS ASEC
   ↓
2. Load raw PUF
   ↓
3. Impute PUF variables to CPS using QRF
   ↓
4. Calibrate weights to administrative benchmarks
   ↓
5. Package as enhanced_cps_YYYY.h5
   ↓
6. Upload to HuggingFace
   ↓
7. Use in policyengine-us simulations
```

**In policyengine-us:**
```python
from policyengine_us import Microsimulation
from policyengine_us_data import EnhancedCPS_2024

# Uses enhanced CPS with PUF imputations
sim = Microsimulation(dataset=EnhancedCPS_2024)
sim.calculate('self_employment_tax', period=2024)
# Uses imputed self_employment_income, farm_income, etc.
```

## Related Skills

- **microimpute-skill** - ML imputation methods (underlying technique)
- **policyengine-us-skill** - US policy model (uses this data)
- **microcalibrate-skill** - Weight calibration (next step after imputation)
- **microdf-skill** - Working with survey microdata
- **policyengine-variable-patterns-skill** - Variable implementation patterns

## Resources

**Repository:** https://github.com/PolicyEngine/policyengine-us-data
**Dependencies:** policyengine-us, policyengine-core, microdf, microimpute
**Data sources:**
- CPS ASEC: https://www.census.gov/data/datasets/time-series/demo/cps/cps-asec.html
- IRS PUF: https://www.irs.gov/statistics/soi-tax-stats-individual-public-use-microdata-files
