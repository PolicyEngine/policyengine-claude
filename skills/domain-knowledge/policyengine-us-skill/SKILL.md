---
name: policyengine-us
description: |
  ALWAYS LOAD THIS SKILL FIRST before writing any PolicyEngine-US code.
  Contains the correct API patterns for household calculations and population simulations
  using the new policyengine package. Covers US federal and state taxes/benefits.
  Triggers: "what would", "how much would a", "benefit be", "eligible for", "qualify for",
  "single parent", "married couple", "family of", "household of", "if they earn",
  "earning $", "making $", "calculate benefits", "calculate taxes", "benefit for a",
  "what would I get", "what is the maximum", "what is the rate", "poverty line",
  "income limit", "benefit amount", "maximum benefit", "compare states",
  "TANF", "SNAP", "EITC", "CTC", "SSI", "WIC", "Section 8", "Medicaid", "ACA",
  "child tax credit", "earned income", "supplemental security", "housing voucher",
  "microsimulation", "population", "reform", "policy impact", "budgetary", "decile".
---

# PolicyEngine-US

> **IMPORTANT: Always use the current year (2026) in calculations, not 2024 or 2025.**

PolicyEngine-US models the US federal and state tax and benefit system.

## For Users

### What is PolicyEngine-US?

PolicyEngine-US is the "calculator" for US taxes and benefits. When you use policyengine.org/us, PolicyEngine-US runs behind the scenes.

**What it models:**

**Federal taxes:**
- Income tax (with standard/itemized deductions)
- Payroll tax (Social Security, Medicare)
- Capital gains tax

**Federal benefits:**
- Earned Income Tax Credit (EITC)
- Child Tax Credit (CTC)
- SNAP (food stamps)
- WIC, ACA premium tax credits
- Social Security, SSI, TANF

**State programs (varies by state):**
- State income tax (all 50 states + DC)
- State EITC, CTC
- State-specific benefits

**See full list:** https://policyengine.org/us/parameters

### Understanding Variables

**Income variables:**
- `employment_income` - W-2 wages
- `self_employment_income` - 1099 income
- `qualified_dividend_income` - Dividends
- `capital_gains` - Capital gains

**Tax variables:**
- `income_tax` - Federal income tax
- `state_income_tax` - State income tax
- `payroll_tax` - FICA taxes

**Benefit variables:**
- `eitc` - Earned Income Tax Credit
- `ctc` - Child Tax Credit
- `snap` - SNAP benefits

**Summary variables:**
- `household_net_income` - Income after taxes and benefits
- `household_tax` - Total taxes
- `household_benefits` - Total benefits

## For Analysts

### Installation

```bash
pip install policyengine
```

### Two Modes of Analysis

1. **Household Calculations** - Single household, quick answers
2. **Population Simulations** - Microsimulation, policy analysis at scale

---

## 1. Household Calculations

Use `calculate_household_impact()` with `USHouseholdInput` for quick calculations.

### Basic Pattern

```python
from policyengine.tax_benefit_models.us import (
    USHouseholdInput,
    calculate_household_impact,
)

household = USHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000, "is_tax_unit_head": True},
    ],
    household={"state_code_str": "CA"},
    year=2026,
)
result = calculate_household_impact(household)

print(f"Income tax: ${result.tax_unit[0]['income_tax']:,.0f}")
print(f"Net income: ${result.household['household_net_income']:,.0f}")
```

### US Entity Structure (6 entities)

The US has more entities than the UK due to different program structures:
- `person` - Individual people
- `marital_unit` - Married couples
- `family` - Family unit
- `spm_unit` - SPM unit (for SNAP, TANF, poverty measures)
- `tax_unit` - Tax filing unit (for income tax, EITC, CTC)
- `household` - Physical household

### Single Filer

```python
household = USHouseholdInput(
    people=[
        {"age": 30, "employment_income": 60_000, "is_tax_unit_head": True},
    ],
    household={"state_code_str": "CA"},
    year=2026,
)
result = calculate_household_impact(household)
```

### Married Couple with Children

```python
household = USHouseholdInput(
    people=[
        {"age": 35, "employment_income": 80_000, "is_tax_unit_head": True},
        {"age": 33, "employment_income": 40_000, "is_tax_unit_spouse": True},
        {"age": 8, "is_tax_unit_dependent": True},
        {"age": 5, "is_tax_unit_dependent": True},
    ],
    tax_unit={"filing_status": "JOINT"},
    household={"state_code_str": "NY"},
    year=2026,
)
result = calculate_household_impact(household)

print(f"EITC: ${result.tax_unit[0]['eitc']:,.0f}")
print(f"CTC: ${result.tax_unit[0]['ctc']:,.0f}")
print(f"SNAP: ${result.spm_unit[0]['snap']:,.0f}")
```

### Accessing Results

```python
# Person-level
employment_income = result.person[0]['employment_income']

# Tax unit level (income tax, credits)
income_tax = result.tax_unit[0]['income_tax']
eitc = result.tax_unit[0]['eitc']
ctc = result.tax_unit[0]['ctc']

# SPM unit level (means-tested benefits)
snap = result.spm_unit[0]['snap']
tanf = result.spm_unit[0]['tanf']

# Household level
net_income = result.household['household_net_income']
```

---

## 2. Population Simulations

Use `Simulation` with datasets for population-level analysis.

### Loading Data

```python
from policyengine.tax_benefit_models.us import (
    us_latest,
    ensure_datasets,
)

datasets = ensure_datasets(
    data_folder="./data",
    years=[2026],
)
dataset = datasets["enhanced_cps_2024_2026"]
```

### Running Simulations

```python
from policyengine.core import Simulation

simulation = Simulation(
    dataset=dataset,
    tax_benefit_model_version=us_latest,
)
simulation.ensure()

output = simulation.output_dataset.data
total_eitc = output.tax_unit['eitc'].sum()
total_snap = output.spm_unit['snap'].sum()
```

---

## Policy Reforms

### Parametric Reforms

```python
from policyengine.core import Policy, ParameterValue
from datetime import datetime

param = us_latest.get_parameter("gov.irs.credits.ctc.amount.base_amount")

policy = Policy(
    name="CTC $5000",
    parameter_values=[
        ParameterValue(
            parameter=param,
            value=5000,
            start_date=datetime(2026, 1, 1),
        )
    ],
)

reform_sim = Simulation(
    dataset=dataset,
    tax_benefit_model_version=us_latest,
    policy=policy,
)
reform_sim.ensure()
```

### Simulation Modifier Reforms

```python
def expand_eitc(sim):
    """Expand EITC phase-out threshold."""
    sim.tax_benefit_system.parameters.get_child(
        "gov.irs.credits.eitc.phase_out.start"
    ).update(period="year:2026:10", value=25000)
    sim.tax_benefit_system.reset_parameter_caches()

policy = Policy(
    name="Expand EITC",
    simulation_modifier=expand_eitc,
)
```

---

## Parameter Lookup

For quick parameter lookups:

```python
from policyengine_us import CountryTaxBenefitSystem

params = CountryTaxBenefitSystem().parameters

# CTC amount
ctc = params.gov.irs.credits.ctc.amount.base_amount("2026-01-01")

# SNAP max (use .children["N"] for indexed params)
snap_max = params.gov.usda.snap.income.max_allotment.children["4"]("2026-01-01")

# State TANF
dc_tanf = params.gov.states.dc.dhs.tanf.standard_payment.amount.children["3"]("2026-01-01")
```

---

## Common Pitfalls

### 1. Don't Strip Weights
```python
# WRONG
mean = output.tax_unit['eitc'].values.mean()

# CORRECT
mean = output.tax_unit['eitc'].mean()
```

### 2. Tax Unit Roles Required
```python
# People need tax unit roles
{"age": 35, "is_tax_unit_head": True}
{"age": 33, "is_tax_unit_spouse": True}
{"age": 8, "is_tax_unit_dependent": True}
```

### 3. Filing Status for Couples
```python
tax_unit={"filing_status": "JOINT"}  # or "SEPARATE", "HEAD_OF_HOUSEHOLD"
```

---

## State-Specific Variables

State variables use `{state_code}_{program}` naming:
- `ca_tanf`, `ny_tanf`, `dc_tanf` - State TANF
- `ca_eitc`, `ny_eitc` - State EITC
- `state_income_tax` - Aggregate state tax

```python
from policyengine_us import CountryTaxBenefitSystem
system = CountryTaxBenefitSystem()

# Find state variables
ca_vars = [v for v in system.variables if v.startswith("ca_")]
```

---

## Additional Resources

- **Documentation:** https://policyengine.org/us/docs
- **Variable Explorer:** https://policyengine.org/us/variables
- **Parameter Explorer:** https://policyengine.org/us/parameters
