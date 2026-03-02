---
name: policyengine-uk
description: |
  ALWAYS LOAD THIS SKILL FIRST before writing any PolicyEngine-UK code.
  Contains the correct API patterns for household calculations and population simulations
  using the new policyengine package (not policyengine_uk directly).
  Triggers: "what would", "how much would a", "benefit be", "eligible for", "qualify for",
  "single parent", "married couple", "family of", "household of", "if they earn", "with income of",
  "earning £", "making £", "calculate benefits", "calculate taxes", "benefit for a", "tax for a",
  "what would I get", "what would they get", "what is the rate", "what is the threshold",
  "personal allowance", "maximum benefit", "income limit", "benefit amount", "how much is",
  "Universal Credit", "child benefit", "pension credit", "housing benefit", "council tax",
  "income tax", "national insurance", "JSA", "ESA", "PIP", "disability living allowance",
  "working tax credit", "child tax credit", "Scotland", "Wales", "UK",
  "microsimulation", "population", "reform", "policy impact", "budgetary", "decile".
---

# PolicyEngine-UK

> **IMPORTANT: Always use the current year (2026) in calculations, not 2024 or 2025.**

PolicyEngine-UK models the UK tax and benefit system, including devolved variations for Scotland and Wales.

## For Users

### What is PolicyEngine-UK?

PolicyEngine-UK is the "calculator" for UK taxes and benefits. When you use policyengine.org/uk, PolicyEngine-UK runs behind the scenes.

**What it models:**

**Direct taxes:**
- Income tax (UK-wide, Scottish, and Welsh variations)
- National Insurance (Classes 1, 2, 4)
- Capital gains tax, Dividend tax

**Property and transaction taxes:**
- Council Tax
- Stamp Duty Land Tax (England/NI)
- Land and Buildings Transaction Tax (Scotland)
- Land Transaction Tax (Wales)

**Universal Credit:**
- Standard allowance, Child elements, Housing cost element
- Childcare costs element, Carer element, Work capability elements

**Legacy benefits (being phased out):**
- Working Tax Credit, Child Tax Credit, Income Support
- Income-based JSA/ESA, Housing Benefit

**Other benefits:**
- Child Benefit, Pension Credit, PIP, DLA, Attendance Allowance, State Pension

**See full list:** https://policyengine.org/uk/parameters

### Understanding Variables

**Income variables:**
- `employment_income` - Gross employment earnings/salary
- `self_employment_income` - Self-employment profits
- `pension_income` - Private pension income
- `property_income` - Rental income
- `savings_interest_income` - Interest from savings
- `dividend_income` - Dividend income

**Tax variables:**
- `income_tax` - Total income tax liability
- `national_insurance` - Total NI contributions
- `council_tax` - Council tax liability

**Benefit variables:**
- `universal_credit` - Universal Credit amount
- `child_benefit` - Child Benefit amount
- `pension_credit` - Pension Credit amount

**Summary variables:**
- `household_net_income` - Income after taxes and benefits
- `hbai_household_net_income` - HBAI-definition net income

## For Analysts

### Installation

```bash
pip install policyengine
```

### Two Modes of Analysis

PolicyEngine provides two main ways to analyze the UK tax-benefit system:

1. **Household Calculations** - Single household, quick answers
2. **Population Simulations** - Microsimulation, policy analysis at scale

---

## 1. Household Calculations

Use `calculate_household_impact()` with `UKHouseholdInput` for quick single-household calculations.

### Basic Pattern

```python
from policyengine.tax_benefit_models.uk import (
    UKHouseholdInput,
    calculate_household_impact,
)

household = UKHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000},
    ],
    year=2026,
)
result = calculate_household_impact(household)

# Access results
print(f"Income tax: £{result.person[0]['income_tax']:,.0f}")
print(f"Net income: £{result.household['hbai_household_net_income']:,.0f}")
```

### Single Person

```python
household = UKHouseholdInput(
    people=[{"age": 30, "employment_income": 30_000}],
    household={"region": "LONDON"},
    year=2026,
)
result = calculate_household_impact(household)
```

### Couple with Children

```python
household = UKHouseholdInput(
    people=[
        {"age": 35, "employment_income": 50_000},
        {"age": 33, "employment_income": 25_000},
        {"age": 8},
        {"age": 5},
    ],
    benunit={"would_claim_uc": True},
    household={"region": "NORTH_WEST"},
    year=2026,
)
result = calculate_household_impact(household)

print(f"Child Benefit: £{result.benunit[0]['child_benefit']:,.0f}")
print(f"Universal Credit: £{result.benunit[0]['universal_credit']:,.0f}")
```

### With Housing Costs

```python
household = UKHouseholdInput(
    people=[{"age": 28, "employment_income": 25_000}],
    benunit={"would_claim_uc": True},
    household={"region": "LONDON", "rent": 15_000},
    year=2026,
)
result = calculate_household_impact(household)
```

### Accessing Results

Results are organized by entity level:
- `result.person[i]` - Person-level variables (indexed by person order)
- `result.benunit[i]` - Benefit unit variables
- `result.household` - Household-level variables

```python
# Person-level (returns dict for each person)
income_tax = result.person[0]['income_tax']
ni = result.person[0]['national_insurance']

# Benefit unit level
uc = result.benunit[0]['universal_credit']
child_benefit = result.benunit[0]['child_benefit']

# Household level
net_income = result.household['hbai_household_net_income']
```

---

## 2. Population Simulations

Use `Simulation` with datasets for population-level microsimulation analysis.

### Loading Data

```python
from policyengine.tax_benefit_models.uk import (
    uk_latest,
    ensure_datasets,
    PolicyEngineUKDataset,
)

# Load pre-prepared datasets
datasets = ensure_datasets(
    data_folder="./data",
    years=[2026, 2027, 2028, 2029, 2030],
)
dataset = datasets["enhanced_frs_2023_24_2026"]
```

### Running Simulations

```python
from policyengine.core import Simulation

simulation = Simulation(
    dataset=dataset,
    tax_benefit_model_version=uk_latest,
)
simulation.ensure()  # Runs if not cached, loads if cached

# Access output data (weighted MicroDataFrames)
output = simulation.output_dataset.data
income_tax_total = output.household['household_tax'].sum()
mean_net_income = output.household['household_net_income'].mean()
```

### Key Points for Population Simulations

- `simulation.ensure()` runs the simulation if not cached, or loads from cache
- Output data in `simulation.output_dataset.data` contains weighted MicroDataFrames
- **Never strip weights** - keep results as MicroSeries and use `.sum()`, `.mean()` directly
- Access by entity: `output.person`, `output.benunit`, `output.household`

---

## Policy Reforms

### Parametric Reforms (ParameterValue)

For simple parameter changes:

```python
from policyengine.core import Policy, ParameterValue
from datetime import datetime

# Get parameter from model
param = uk_latest.get_parameter("gov.hmrc.income_tax.rates.uk[0].rate")

policy = Policy(
    name="Basic rate 25%",
    parameter_values=[
        ParameterValue(
            parameter=param,
            value=0.25,
            start_date=datetime(2026, 1, 1),
        )
    ],
)

# Run reform simulation
reform_sim = Simulation(
    dataset=dataset,
    tax_benefit_model_version=uk_latest,
    policy=policy,
)
reform_sim.ensure()
```

### Simulation Modifier Reforms (Complex/Programmatic)

For complex reforms that need programmatic control:

```python
def my_reform_modifier(sim):
    """Modify the underlying policyengine_uk Microsimulation."""
    # Modify parameters
    sim.tax_benefit_system.parameters.get_child(
        "gov.dwp.universal_credit.elements.child.limit.child_count"
    ).update(period="year:2026:10", value=float('inf'))

    # Or modify inputs
    employment_income = sim.calculate("employment_income", 2026)
    sim.set_input("employment_income", 2026, employment_income * 1.05)

    sim.tax_benefit_system.reset_parameter_caches()

policy = Policy(
    name="Complex reform",
    simulation_modifier=my_reform_modifier,
)
```

### Combining Policies

```python
policy_combined = policy_a + policy_b  # Chains modifiers
```

---

## Analysis Patterns

### Decile Impacts

```python
from policyengine.outputs.decile_impact import calculate_decile_impacts

results = calculate_decile_impacts(
    dataset=dataset,
    tax_benefit_model_version=uk_latest,
    baseline_policy=None,  # Current law
    reform_policy=my_policy,
)
# Returns OutputCollection with .dataframe and .outputs
```

### Economic Impact Analysis

```python
from policyengine.tax_benefit_models.uk.analysis import economic_impact_analysis

analysis = economic_impact_analysis(
    baseline_simulation=baseline_sim,
    reform_simulation=reform_sim,
)
# Returns PolicyReformAnalysis with:
# - decile_impacts
# - programme_statistics
# - baseline_poverty / reform_poverty
# - baseline_inequality / reform_inequality
```

### Aggregate Statistics

```python
from policyengine.outputs.aggregate import Aggregate, AggregateType

agg = Aggregate(
    simulation=simulation,
    variable="universal_credit",
    aggregate_type=AggregateType.SUM,
    entity="benunit",
)
agg.run()
print(f"Total UC spending: £{agg.result / 1e9:.1f}bn")
```

---

## Parameter Lookup

For quick parameter lookups (rates, thresholds), use the old API directly:

```python
from policyengine_uk import CountryTaxBenefitSystem

params = CountryTaxBenefitSystem().parameters

# Personal allowance
pa = params.gov.hmrc.income_tax.allowances.personal_allowance.amount("2026-01-01")

# Basic rate (use .children["N"] for brackets)
basic_rate = params.gov.hmrc.income_tax.rates.uk.brackets.children["0"].rate("2026-01-01")

# UC standard allowance
uc_standard = params.gov.dwp.universal_credit.elements.standard_allowance.amount.single.over_25("2026-01-01")
```

**When to use parameter lookup vs simulation:**
- **Parameter lookup**: "What is the personal allowance?", "What is the basic rate?"
- **Simulation**: "What would my tax be if I earn £30k?", "Am I eligible for UC?"

---

## Regions

UK uses ITL 1 regions:
- `NORTH_EAST`, `NORTH_WEST`, `YORKSHIRE`, `EAST_MIDLANDS`, `WEST_MIDLANDS`
- `EAST_OF_ENGLAND`, `LONDON`, `SOUTH_EAST`, `SOUTH_WEST`
- `WALES`, `SCOTLAND`, `NORTHERN_IRELAND`

**Regional Tax Variations:**
- **Scotland:** 6 bands (starter 19%, basic 20%, intermediate 21%, higher 42%, advanced 45%, top 47%)
- **Wales:** Welsh Rate of Income Tax (WRIT), currently at parity with England
- **England/NI:** Standard UK rates (20%, 40%, 45%)

---

## Common Pitfalls

### 1. Don't Strip Weights from MicroSeries
```python
# WRONG - strips weights
values = output.household['income_tax'].values
mean = values.mean()  # Unweighted!

# CORRECT - keep as MicroSeries
mean = output.household['income_tax'].mean()  # Weighted
```

### 2. Use .ensure() for Cached Runs
```python
simulation.ensure()  # Loads from cache if available
# NOT simulation.run() unless you want to force re-run
```

### 3. Parameter Paths Use Bracket Notation
```python
# New API uses brackets: uk[0].rate
param = uk_latest.get_parameter("gov.hmrc.income_tax.rates.uk[0].rate")

# Old API uses .children["N"]
params.gov.hmrc.income_tax.rates.uk.brackets.children["0"].rate("2026-01-01")
```

### 4. Household Input Uses List of Dicts
```python
# New API - list of person dicts
UKHouseholdInput(people=[{"age": 35}, {"age": 8}], ...)

# Old API - nested situation dict (still works for old Simulation)
{"people": {"person1": {"age": {2026: 35}}, ...}}
```

---

## For Contributors

### Repository

**Location:** PolicyEngine/policyengine-uk

```bash
git clone https://github.com/PolicyEngine/policyengine-uk
cd policyengine-uk
```

**Key directories:**
- `policyengine_uk/variables/` - Tax and benefit calculations
- `policyengine_uk/parameters/` - Policy rules (YAML)
- `policyengine_uk/reforms/` - Pre-defined reforms
- `policyengine_uk/tests/` - Test cases

### UK Legislation References

All UK parameters MUST have legislation.gov.uk references with exact section links.

**Primary legislation:**
- Welfare Reform Act 2012 - Universal Credit
- Social Security Contributions and Benefits Act 1992
- Income Tax Act 2007

**Secondary legislation:**
- Universal Credit Regulations 2013 (SI 2013/376)
- Income Tax (Earnings and Pensions) Act 2003

**Reference format:**
```yaml
metadata:
  reference:
    - title: Universal Credit Regulations 2013, Schedule 4, Table 3
      href: https://www.legislation.gov.uk/uksi/2013/376/schedule/4
```

---

## Additional Resources

- **Documentation:** https://policyengine.org/uk/docs
- **Variable Explorer:** https://policyengine.org/uk/variables
- **Parameter Explorer:** https://policyengine.org/uk/parameters
- **API Reference:** https://github.com/PolicyEngine/policyengine-uk
