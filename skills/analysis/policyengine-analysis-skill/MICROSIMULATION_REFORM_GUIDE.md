# Microsimulation reform implementation guide

> **Note**: Always use MicroSeries arithmetic (`.sum()`, `.mean()`, `*`, `>`) instead of extracting `.values` and using numpy. MicroSeries handles weighting automatically. Only use `household_weight` — it's the only calibrated weight.

Guide for implementing policy reforms and microsimulation analysis in PolicyEngine  UK ONLY projects.

## Overview

This guide covers the technical patterns for implementing policy reforms in PolicyEngine microsimulation projects, with focus on UK microsimulation work using policyengine-uk.

## Core concepts

### Reform types

PolicyEngine reforms fall into two main categories:

**Parameter-based reforms** - Simple changes to policy parameters (rates, thresholds, amounts):
- Direct parameter modifications via `parameter_changes` dictionary
- Easiest to implement and understand
- Limited to existing policy structure

**Structural reforms** - Complex changes requiring custom logic:
- Use `simulation_modifier` functions
- Can create new variables, modify formulas, change calculation logic
- Required when policy structure changes

### The Scenario object

All reforms use the `Scenario` class from `policyengine_uk.model_api`:

```python
from policyengine_uk.model_api import Scenario
```

Two main patterns:

```python
# Parameter-based
reform = Scenario(
    parameter_changes={
        "path.to.parameter": {
            "year:2026:10": new_value,
        }
    }
)

# Structural
def modifier(simulation):
    # Custom logic here
    pass

reform = Scenario(simulation_modifier=modifier)
```

## Finding parameters and variables

**Critical step:** Before implementing any reform, you must find the correct parameter or variable names in the policyengine-uk repository.

### Looking up parameters

Parameters are in `policyengine_uk/parameters/` directory:
- Navigate the YAML file structure
- Parameter paths use dot notation matching directory structure
- Example: `gov.hmrc.income_tax.rates.uk[0].rate`

Common parameter locations:
- Income tax: `gov.hmrc.income_tax.*`
- National insurance: `gov.hmrc.national_insurance.*`
- Benefits: `gov.dwp.*` or `gov.dfe.*`
- Economic assumptions: `gov.economic_assumptions.*`

### Looking up variables

Variables are in `policyengine_uk/variables/` directory:
- Check variable definition files to understand structure
- Variable names are snake_case
- Check `entity` (Person, Household, BenUnit, etc.)
- Check `definition_period` (YEAR, MONTH, ETERNITY)

Key variable attributes to check:
```python
class example_variable(Variable):
    value_type = float
    entity = Household  # Who this applies to
    label = "Description"
    definition_period = YEAR  # Time period granularity

    def formula(household, period, parameters):
        # How it's calculated
        pass
```

## Pattern 1: Simple parameter changes

For straightforward policy changes (rates, thresholds, amounts).

### Single parameter change

```python
from policyengine_uk.model_api import Scenario

# Example: changing a rate
rate_change = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.rates.uk[0].rate": {
            "year:2026:10": 0.21,  # 21% from 2026 onwards
        }
    }
)
```

### Multiple parameter changes

```python
threshold_change = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
            "year:2026:2": 13_000,
        },
        "gov.hmrc.income_tax.rates.uk[1].threshold": {
            "year:2026:2": 38_270,  # Adjusted for new PA
        },
    }
)
```

### Time period syntax

```python
"year:2026:10"    # From 2026, for 10 years
"year:2026:1"     # Just 2026
"2026-04-01"      # Specific date
"month:2026-01"   # Specific month
```

### Using numpy for special values

```python
import numpy as np

remove_cap = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.benefit_cap.couple": {
            "year:2026:10": np.inf,  # Remove cap entirely
        }
    }
)
```

## Pattern 2: Structural reforms with parameter updates

When you need to freeze, uprate, or modify parameters across multiple years.

### The parameter update pattern

```python
from policyengine_uk.model_api import Scenario
from policyengine_uk import Simulation

def freeze_threshold_modifier(sim: Simulation):
    # Critical: clone first to avoid side effects
    clone = sim.clone()
    clone.tax_benefit_system.reset_parameters()

    # Access parameter tree
    it = clone.tax_benefit_system.parameters.gov.hmrc.income_tax

    # Get current value
    current_threshold = it.rates.uk[1].threshold(2026)

    # Update for multiple years
    for year in range(2026, 2031):
        it.rates.uk[1].threshold.update(
            period=str(year),
            value=current_threshold,
            remove_after=True,  # Don't affect years after
        )

    # Process changes
    clone.tax_benefit_system.process_parameters()

    # Copy back to original simulation
    sim.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.uk[1].threshold.values_list = \
        it.rates.uk[1].threshold.values_list

    # Reset caches
    sim.tax_benefit_system.reset_parameter_caches()

freeze_threshold = Scenario(simulation_modifier=freeze_threshold_modifier)
```

### Key steps in parameter modification

1. **Clone the simulation** - `clone = sim.clone()`
2. **Reset parameters** - `clone.tax_benefit_system.reset_parameters()`
3. **Make changes on the clone** - Update parameters
4. **Process parameters** - `clone.tax_benefit_system.process_parameters()`
5. **Copy back to original** - Replace `.values_list`
6. **Reset caches** - `sim.tax_benefit_system.reset_parameter_caches()`

### Uprating with economic assumptions

```python
def create_uprating_modifier(base_amount: float):
    def modifier(simulation):
        p = simulation.tax_benefit_system.parameters

        # Get inflation index
        cpi = p.gov.economic_assumptions.yoy_growth.obr.consumer_price_index

        amount = base_amount
        for year in range(2026, 2031):
            if year > 2026:
                amount = amount * (1 + cpi(year - 1))

            # Use the uprated amount
            p.gov.dwp.universal_credit.elements.child.amount.update(
                start=f"{year}-01-01",
                value=amount,
            )

        simulation.tax_benefit_system.reset_parameter_caches()

    return Scenario(simulation_modifier=modifier)
```

## Pattern 3: Variable-based reforms

When you need to override calculated variables directly.

### Setting variable values

```python
def variable_override_modifier(sim: Simulation):
    for year in range(2026, 2030):
        # Calculate baseline value
        previous_value = sim.calculate("universal_credit", year)

        # Modify it
        new_value = previous_value * 1.1  # 10% increase

        # Set the new value
        sim.set_input("universal_credit", year, new_value)

reform = Scenario(simulation_modifier=variable_override_modifier)
```

### Conditional modifications

```python
def conditional_modifier(sim: Simulation):
    for year in range(2026, 2030):
        # Get eligibility criteria
        has_children = sim.calculate("benunit_count_children", year, map_to="benunit").values > 0  # Prefer MicroSeries arithmetic where possible; .values needed here for np.where below

        # Get baseline amount
        baseline_uc = sim.calculate("universal_credit", year, map_to="benunit").values  # .values used for np.where; prefer MicroSeries for aggregations

        # Create modified amount (only for those with children)
        modified_uc = np.where(
            has_children,
            baseline_uc + 500,  # £500 bonus
            baseline_uc
        )

        # Set the new values
        sim.set_input("universal_credit", year, modified_uc)
```

### Important notes on map_to

When working with variables at different entity levels:

```python
# Calculate at household level
household_income = sim.calculate("household_net_income", year)

# Calculate person-level, aggregate to household
employment_income = sim.calculate("employment_income", year, map_to="household")

# Calculate person-level, aggregate to benefit unit
benunit_earnings = sim.calculate("employment_income", year, map_to="benunit")
```

Entity levels in policyengine-uk:
- `person` - Individual people
- `benunit` - Benefit units (tax/benefit calculation units)
- `household` - Households (groups of people living together)

## Pattern 4: Creating new variables

For truly novel policy features.

### Adding a new variable to the system

```python
from policyengine_core.variables import Variable
from policyengine_core.periods import YEAR
from policyengine_uk.entities import BenUnit
import numpy as np

def add_new_variable_modifier(sim: Simulation):
    # Define the new variable
    class new_benefit_amount(Variable):
        value_type = float
        entity = BenUnit
        label = "New benefit amount"
        definition_period = YEAR

        def formula(benunit, period, parameters):
            # Access other variables
            income = benunit("benunit_net_income", period)
            children = benunit("benunit_count_children", period)

            # Implement logic
            base_amount = parameters(period).gov.new_benefit.base_amount

            return np.where(
                (income < 20_000) & (children > 0),
                base_amount,
                0
            )

    # Add to tax-benefit system
    sim.tax_benefit_system.update_variable(new_benefit_amount)

    # Now can use it in calculations
    for year in range(2026, 2030):
        benefit = sim.calculate("new_benefit_amount", year)
        # Use the values...

reform = Scenario(simulation_modifier=add_new_variable_modifier)
```

### Helper variables for complex logic

```python
def add_helper_variable(sim: Simulation):
    class working_adults_count(Variable):
        value_type = int
        entity = BenUnit
        label = "Number of working adults in benefit unit"
        definition_period = YEAR

        def formula(benunit, period, parameters):
            in_work = benunit.members("in_work", period)
            return benunit.sum(in_work)

    sim.tax_benefit_system.update_variable(working_adults_count)

    # Now use it in subsequent calculations
    for year in range(2026, 2030):
        working_count = sim.calculate("working_adults_count", year, map_to="benunit").values  # .values for element-wise logic; prefer MicroSeries for aggregations
        # Apply logic based on working_count...
```

## Pattern 5: Combining reforms

Use the `+` operator to combine multiple scenarios:

```python
# Individual reforms
personal_allowance_increase = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
            "year:2026:10": 13_000,
        }
    }
)

basic_rate_increase = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.rates.uk[0].rate": {
            "year:2026:10": 0.21,
        }
    }
)

# Combined reform
combined_reform = personal_allowance_increase + basic_rate_increase

# Can also combine structural reforms
full_package = combined_reform + structural_reform + another_reform
```

## Microsimulation analysis patterns

### Creating simulations

Standard pattern for creating baseline and reform simulations:

```python
from policyengine_uk import Microsimulation

# Baseline
baseline = Microsimulation()

# With reform
reform_sim = Microsimulation(
    scenario=my_reform
)
```

### Custom simulation setup

Many projects have helper functions:

```python
def create_base_simulation(scenario=None, dataset=None):
    """Create simulation with standard adjustments."""
    scenarios = []

    # Add standard modifications
    scenarios.append(adjust_data_quality())
    scenarios.append(calibrate_weights())

    # Add user scenario
    if scenario is not None:
        scenarios.append(scenario)

    # Combine all scenarios
    combined = None
    for s in scenarios:
        combined = s if combined is None else combined + s

    return Microsimulation(
        dataset=dataset,  # Omit or use HF URL like 'hf://policyengine/policyengine-uk-data/...' — never pass short dataset names
        scenario=combined
    )
```

### Calculating impacts

```python
# Single variable
baseline_income = baseline.calculate("household_net_income", 2026)
reform_income = reform_sim.calculate("household_net_income", 2026)

# Impact
impact = reform_income - baseline_income

# Summary statistics
mean_impact = impact.mean()
total_impact = impact.sum()

```

### Subgroup analysis with filters

```python
import numpy as np

# Define filter
def filter_pensioners(sim):
    """Filter for pensioner households."""
    age = sim.calculate("age", map_to="person")
    is_pensioner = sim.map_result(
        (age >= 65) & (age <= 100),
        "person",
        "household",
        how="any"  # Any pensioner in household
    )
    return is_pensioner

# Apply filter
pensioner_mask = filter_pensioners(baseline)

# Calculate for subgroup
pensioner_baseline = baseline.calculate("household_net_income", 2026)[pensioner_mask]
pensioner_reform = reform_sim.calculate("household_net_income", 2026)[pensioner_mask]
pensioner_impact = pensioner_reform - pensioner_baseline
```

### Common filters

```python
# Working age
age = sim.calculate("age", map_to="household")
working_age = age < 65

# Has children
children = sim.calculate("is_child", map_to="household")
has_children = children > 0

# In work
in_work = sim.map_result(
    sim.calculate("in_work"),
    "person",
    "household"
) > 0

# By income decile
equiv_income = sim.calculate("equiv_household_net_income")
decile = equiv_income.decile_rank().clip(1, 10)
bottom_half = decile <= 5
```

### Decomposition analysis

Breaking down what drives income changes:

```python
import pandas as pd

# Components that increase income
income_components = [
    'employment_income',
    'self_employment_income',
    'pension_income',
    'benefits',
]

# Components that decrease income (taxes, costs)
cost_components = [
    'income_tax',
    'national_insurance',
    'council_tax',
]

# Calculate each component for baseline and reform
df = pd.DataFrame()

for var in income_components:
    baseline_val = baseline.calculate(var, 2026, map_to="household").mean()
    reform_val = reform_sim.calculate(var, 2026, map_to="household").mean()
    df.loc[var, 'baseline'] = baseline_val
    df.loc[var, 'reform'] = reform_val
    df.loc[var, 'change'] = reform_val - baseline_val

for var in cost_components:
    baseline_val = -baseline.calculate(var, 2026, map_to="household").mean()
    reform_val = -reform_sim.calculate(var, 2026, map_to="household").mean()
    df.loc[var, 'baseline'] = baseline_val
    df.loc[var, 'reform'] = reform_val
    df.loc[var, 'change'] = reform_val - baseline_val
```

### Time series analysis

```python
years = range(2024, 2031)
results = []

for year in years:
    baseline_income = baseline.calculate("household_net_income", year)
    reform_income = reform_sim.calculate("household_net_income", year)

    results.append({
        'year': year,
        'baseline_mean': baseline_income.mean(),
        'reform_mean': reform_income.mean(),
        'mean_impact': (reform_income - baseline_income).mean(),
    })

df = pd.DataFrame(results)
```

### Real vs nominal analysis

```python
# Get inflation adjustment
inflation_2026 = baseline.calculate("inflation_adjustment", 2026)
inflation_2029 = baseline.calculate("inflation_adjustment", 2029)

# Calculate real values
nominal_2029 = baseline.calculate("household_net_income", 2029)
real_2029 = nominal_2029 * (inflation_2026 / inflation_2029)

# Compare real change over time
real_2026 = baseline.calculate("household_net_income", 2026)
real_change = real_2029 - real_2026
```

## Common pitfalls and solutions

### Pitfall 1: Not cloning when modifying parameters

**Wrong:**
```python
def modifier(sim):
    # Modifying directly - affects caches incorrectly
    sim.tax_benefit_system.reset_parameters()
    p = sim.tax_benefit_system.parameters
    p.some_param.update(...)
```

**Right:**
```python
def modifier(sim):
    clone = sim.clone()
    clone.tax_benefit_system.reset_parameters()
    p = clone.tax_benefit_system.parameters
    p.some_param.update(...)
    clone.tax_benefit_system.process_parameters()
    # Copy back
    sim.tax_benefit_system.parameters.some_param.values_list = \
        clone.tax_benefit_system.parameters.some_param.values_list
    sim.tax_benefit_system.reset_parameter_caches()
```

### Pitfall 2: Wrong entity level

**Wrong:**
```python
# Trying to calculate household variable at person level
income = sim.calculate("household_net_income", 2026)  # Returns household-level
children = sim.calculate("is_child", 2026)  # Returns person-level
# These have different shapes!
```

**Right:**
```python
# Map to same level
income = sim.calculate("household_net_income", 2026)  # Household level
children = sim.calculate("is_child", 2026, map_to="household")  # Now household level
```

### Pitfall 3: Modifying arrays in place

**Wrong:**
```python
baseline_amount = sim.calculate("universal_credit", 2026)
baseline_amount[eligible] += 500  # Modifies the cached value!
sim.set_input("universal_credit", 2026, baseline_amount)
```

**Right:**
```python
baseline_amount = sim.calculate("universal_credit", 2026).values  # .values needed here to .copy() and mutate; prefer MicroSeries for aggregations
new_amount = baseline_amount.copy()  # Explicit copy
new_amount[eligible] += 500
sim.set_input("universal_credit", 2026, new_amount)
```

### Pitfall 4: Not accounting for parameter indexing

Some parameters are arrays with indices:

**Wrong:**
```python
"gov.hmrc.income_tax.rates.uk.rate": {"year:2026:10": 0.21}  # Missing [0]
```

**Right:**
```python
"gov.hmrc.income_tax.rates.uk[0].rate": {"year:2026:10": 0.21}  # Correct
```

### Pitfall 5: Forgetting remove_after

**Wrong:**
```python
it.rates.uk[1].threshold.update(
    period="2026",
    value=50_000,
    # Missing remove_after - will affect all future years!
)
```

**Right:**
```python
it.rates.uk[1].threshold.update(
    period="2026",
    value=50_000,
    remove_after=True,  # Only affects specified period
)
```

## Workflow summary

### Implementing a new reform

1. **Understand the policy change**
   - What parameter/variable is affected?
   - Is it a simple parameter change or structural change?

2. **Find the right parameter/variable**
   - Search policyengine-uk repository
   - Check parameter path in YAML files
   - Verify variable names and entities

3. **Choose implementation pattern**
   - Simple parameter change? Use `parameter_changes`
   - Need multi-year logic? Use `simulation_modifier` with parameter updates
   - Need new calculation? Use `simulation_modifier` with variable creation

4. **Implement the reform**
   - Write the `Scenario` code
   - Test with a small simulation first

5. **Validate**
   - Check parameter values are applied correctly
   - Verify calculations make sense
   - Compare against expected outcomes

### Running an analysis

1. **Create simulations**
   - Baseline simulation
   - Reform simulation(s)

2. **Define analysis groups**
   - What populations matter? (pensioners, working families, etc.)
   - Create filter functions

3. **Calculate impacts**
   - Overall impacts
   - By subgroup
   - By year
   - Real vs nominal

4. **Create decompositions**
   - Which components drive changes?
   - Tax vs benefit effects

5. **Visualize and report**
   - Follow policyengine-writing-skill conventions
   - Create charts showing distributional impacts
   - Report key statistics

## Resources

**Essential repositories to reference:**
- `policyengine-uk` - Parameter paths, variable definitions
- `policyengine-core` - Core simulation engine, variable/parameter classes
- `policyengine-uk-data` - Dataset documentation

**Common imports:**
```python
# Core
from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario, parameters, variables
from policyengine_uk import Simulation

# Variables and parameters
from policyengine_core.variables import Variable
from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.periods import instant, period, YEAR, MONTH, ETERNITY
from policyengine_core.holders import set_input_divide_by_period

# Entities
from policyengine_uk.entities import Person, Household, BenUnit

# Data manipulation
import numpy as np
from numpy import where, maximum, minimum, select
import pandas as pd
```

## Advanced patterns

### Creating custom parameter nodes

```python
from policyengine_core.parameters import Parameter

def add_custom_parameter(sim):
    p = sim.tax_benefit_system.parameters

    # Create a new parameter
    new_param = Parameter(
        "gov.new_policy.phase_in_rate",
        data={
            "values": {
                "2026-01-01": 0.30,
                "2027-01-01": 0.35,
                "2028-01-01": 0.40,
            }
        }
    )

    # Add it to the parameter tree
    p.gov.add_child("new_policy_param", new_param)

    sim.tax_benefit_system.process_parameters()
```
### Conditional reform application

```python
def create_conditional_reform(threshold_reform, benefit_reform):
    """Apply different reforms based on household characteristics."""
    def modifier(sim):
        # Apply base threshold reform
        threshold_reform.modify_simulation(sim)

        # Then apply benefit reform only to eligible households
        for year in range(2026, 2030):
            # Identify eligible households
            income = sim.calculate("household_net_income", year)
            eligible = income < 30_000

            # Calculate benefit reform impact
            baseline_benefits = sim.calculate("benefits", year)

            # Apply conditionally
            new_benefits = baseline_benefits.copy()
            # Only modify for eligible households
            # ... complex logic here

            sim.set_input("benefits", year, new_benefits)

    return Scenario(simulation_modifier=modifier)
```

## Next steps

For analysis and reporting:
- See `policyengine-analysis-skill/SKILL.md` for analysis patterns
- See `policyengine-writing-skill` for writing conventions
- See `policyengine-design-skill` for visualization standards

For specific country models:
- Check the policyengine-uk repository for UK-specific documentation
- Check the policyengine-us repository for US-specific documentation
