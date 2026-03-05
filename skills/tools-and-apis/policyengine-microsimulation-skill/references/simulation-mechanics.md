# Simulation mechanics (policyengine.py)

Advanced patterns for working with `policyengine.py` simulations — caching, result access, and entity mapping.

**Note:** This covers the `policyengine.py` microsimulation package (`from policyengine.core import Simulation`), not country-specific packages (`policyengine_us.Microsimulation`). For country-specific usage, see the main skill.

## Simulation lifecycle

```python
from policyengine.core import Simulation
from policyengine.tax_benefit_models.uk import uk_latest

simulation = Simulation(
    dataset=dataset,
    tax_benefit_model_version=uk_latest,
)

simulation.run()      # Always run (no caching)
simulation.ensure()   # Run only if needed (recommended)
simulation.save()     # Persist results to disk
simulation.load()     # Resume from previous session
```

### How ensure() works

1. Check in-memory LRU cache (100 simulations)
2. Try loading from disk
3. Only run if both cache and disk fail
4. Add to cache for next call

**Performance:** First call = full runtime. Same session = instant. New session = fast disk load.

### Reusing baseline across reforms

```python
baseline = Simulation(dataset=dataset, tax_benefit_model_version=uk_latest)
baseline.ensure()
baseline.save()

for reform in [reform1, reform2, reform3]:
    baseline.ensure()  # Instant from cache!
    reform_sim = Simulation(dataset=dataset, tax_benefit_model_version=uk_latest, policy=reform)
    reform_sim.run()
```

## Accessing results: output_dataset.data

```python
simulation.run()
output = simulation.output_dataset.data

# Entity-level MicroDataFrames
output.person       # Person-level results
output.household    # Household-level results

# US entities
output.tax_unit     # Federal tax filing unit
output.spm_unit     # Supplemental Poverty Measure unit
output.family       # Census family definition

# UK entities
output.benunit      # Benefit unit results
```

All operations respect survey weights automatically:
```python
mean_income = output.household["household_net_income"].mean()  # Weighted
poverty_rate = output.household["in_absolute_poverty_bhc"].mean()  # Weighted
```

## Entity mapping with map_to_entity()

Convert data between entity levels.

```python
output.map_to_entity(
    source_entity="person",     # Map from
    target_entity="household",  # Map to
    columns=["employment_income"],
    how="sum"  # sum, first, mean, max, min (aggregation)
               # project, divide (expansion)
)
```

### Aggregation (person → group)
```python
household_income = output.map_to_entity(
    source_entity="person", target_entity="household",
    columns=["employment_income"], how="sum"
)
```

### Expansion (group → person)
```python
person_rent = output.map_to_entity(
    source_entity="household", target_entity="person",
    columns=["rent"], how="project"  # Broadcast to all members
)
```

### Custom values
```python
import numpy as np
custom_tax = np.where(output.person["employment_income"] > 50000,
    output.person["income_tax"] * 1.1, output.person["income_tax"])
household_custom_tax = output.map_to_entity(
    source_entity="person", target_entity="household",
    values=custom_tax, how="sum"
)
```

## Automatic mapping in Aggregate classes

```python
from policyengine.outputs.aggregate import Aggregate, AggregateType

total_tax = Aggregate(
    simulation=simulation,
    variable="income_tax",       # Person-level
    entity="household",          # Auto-maps to household
    aggregate_type=AggregateType.SUM,
)
total_tax.run()
```

## Debugging tips

```python
# Verify simulation ran
assert simulation.output_dataset is not None

# Check entity linkages
person_hh_ids = set(output.person["person_household_id"])
household_ids = set(output.household["household_id"])
assert person_hh_ids.issubset(household_ids)

# Verify weights
total_persons = output.person["person_weight"].sum()
assert not output.person["person_weight"].isna().any()
```
