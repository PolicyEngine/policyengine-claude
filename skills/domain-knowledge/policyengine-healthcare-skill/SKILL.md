---
name: policyengine-healthcare
description: |
  Healthcare program modeling in PolicyEngine-US — Medicaid, ACA marketplace, CHIP, and Medicare.
  Covers encoding rules, running analyses, and navigating the unique complexity of US healthcare programs.
  Triggers: "healthcare", "health insurance", "Medicaid", "ACA", "CHIP", "Medicare",
  "marketplace", "premium tax credit", "APTC", "PTC", "SLCSP", "benchmark plan",
  "rating area", "age curve", "family tier", "coverage gap", "Medicaid expansion",
  "MAGI", "medicaid_magi", "aca_magi", "medicaid_income_level", "medicaid_category",
  "enrollment", "takeup", "take-up", "per capita", "CSR", "cost sharing",
  "insurance premium", "second lowest silver", "required contribution percentage",
  "42 CFR", "IRC 36B", "categorical eligibility", "expansion adult",
  "healthcare reform", "healthcare analysis", "health policy".
---

# PolicyEngine healthcare programs

> **Scope:** This skill covers the healthcare domain — Medicaid, ACA marketplace, CHIP, and Medicare as modeled in PolicyEngine-US. For general PolicyEngine-US patterns, see the `policyengine-us` skill. For variable/parameter implementation patterns, see the `policyengine-variable-patterns` and `policyengine-parameter-patterns` skills.

## For users

### What healthcare programs does PolicyEngine model?

PolicyEngine-US models four interconnected healthcare programs:

| Program | What it does | Key variable |
|---------|-------------|--------------|
| **Medicaid** | Free/low-cost coverage for low-income individuals | `medicaid` |
| **ACA marketplace** | Subsidized private insurance via premium tax credits | `aca_ptc` |
| **CHIP** | Children's health coverage above Medicaid thresholds | `per_capita_chip` |
| **Medicare** | Coverage for seniors and disabled individuals | `medicare` |

These programs are **mutually exclusive by design** — Medicaid eligibility disqualifies you from ACA subsidies, and CHIP covers children who don't qualify for Medicaid. This interconnection is a key modeling challenge.

### Why healthcare is different from other benefits

Most benefit programs (SNAP, TANF, EITC) have a single income test and a single benefit amount. Healthcare programs are different:

- **9 eligibility categories** for Medicaid alone (infant, young child, older child, young adult, adult expansion, parent, pregnant, SSI recipient, senior/disabled)
- **51 different Medicaid programs** — every state sets its own income limits and rules
- **~500 ACA rating areas** — premiums vary by geographic zone, not just by state
- **Actuarial calculations** — ACA subsidies depend on the second-lowest silver plan premium in your area, adjusted by age
- **Program interactions** — losing Medicaid doesn't automatically mean gaining ACA access (the "coverage gap")

## For analysts

### Healthcare variables reference

#### Medicaid

| Variable | Entity | Description |
|----------|--------|-------------|
| `medicaid` | person | Annual Medicaid benefit amount |
| `is_medicaid_eligible` | person | Overall eligibility (combines all checks) |
| `medicaid_enrolled` | person | Actually enrolled (eligibility x take-up) |
| `medicaid_category` | person | Enum: SSI_RECIPIENT, INFANT, YOUNG_CHILD, OLDER_CHILD, PREGNANT, PARENT, YOUNG_ADULT, ADULT, SENIOR_OR_DISABLED, NONE |
| `medicaid_income_level` | person | Person's tax unit MAGI as fraction of FPL |
| `medicaid_magi` | tax_unit | Modified AGI for Medicaid (= AGI + state additions) |
| `takes_up_medicaid_if_eligible` | person | Pseudo-random take-up flag (default rate: 93%) |
| `medicaid_cost` | person | Per-capita cost by eligibility group and state |

#### ACA marketplace

| Variable | Entity | Description |
|----------|--------|-------------|
| `aca_ptc` | tax_unit | Annual premium tax credit amount |
| `is_aca_ptc_eligible` | person | PTC eligibility (income 100-400%+ FPL, no other coverage) |
| `aca_magi` | tax_unit | Delegates to `medicaid_magi` via `adds = ["medicaid_magi"]` |
| `aca_magi_fraction` | tax_unit | Income as percentage of FPL |
| `aca_required_contribution_percentage` | tax_unit | Household's required premium contribution rate |
| `slcsp` | tax_unit | Second-lowest silver plan premium (monthly, definition_period=MONTH) |
| `takes_up_aca_if_eligible` | tax_unit | Take-up flag (default rate varies) |

#### CHIP

| Variable | Entity | Description |
|----------|--------|-------------|
| `per_capita_chip` | person | CHIP benefit per capita |
| `is_chip_eligible` | person | CHIP eligibility |
| `chip_category` | person | Enum: CHILD, PREGNANT_STANDARD, PREGNANT_FCEP, NONE |

### Household setup for healthcare analysis

Healthcare calculations require the state to be specified (unlike some federal-only programs):

```python
from policyengine_us import Simulation

situation = {
    "people": {
        "person1": {
            "age": {"2026": 35},
            "employment_income": {"2026": 25_000},
            "is_tax_unit_head": {"2026": True},
        },
        "person2": {
            "age": {"2026": 8},
            "is_tax_unit_dependent": {"2026": True},
        },
    },
    "tax_units": {"tax_unit": {"members": ["person1", "person2"]}},
    "families": {"family": {"members": ["person1", "person2"]}},
    "spm_units": {"spm_unit": {"members": ["person1", "person2"]}},
    "marital_units": {"marital_unit": {"members": ["person1"]}},
    "households": {
        "household": {
            "members": ["person1", "person2"],
            "state_name": {"2026": "NY"},
        }
    },
}

sim = Simulation(situation=situation)

# Check Medicaid eligibility at person level
medicaid_eligible = sim.calculate("is_medicaid_eligible", 2026)
# Check ACA PTC at tax unit level
aca_ptc = sim.calculate("aca_ptc", 2026)
```

### Healthcare reform modeling

#### Medicaid expansion repeal (parameter modification)

```python
from policyengine_core.reforms import Reform
from policyengine_core.periods import instant

YEAR = 2026

def create_medicaid_expansion_repeal(state="UT"):
    """Remove adult Medicaid expansion by setting income limit to -inf."""
    def modify_parameters(parameters):
        parameters.gov.hhs.medicaid.eligibility.categories.adult.income_limit[state].update(
            start=instant(f"{YEAR}-01-01"),
            stop=instant("2100-12-31"),
            value=float("-inf"),
        )
        return parameters

    class reform(Reform):
        def apply(self):
            self.modify_parameters(modify_parameters)
    return reform
```

#### ACA subsidy changes

```python
def modify_aca_contribution_rates():
    """Modify ACA required contribution percentages."""
    def modify_parameters(parameters):
        # The contribution percentage has sub-keys: threshold, initial, final
        # Increase the initial contribution rate at a given FPL bracket
        parameters.gov.aca.required_contribution_percentage.initial.update(
            start=instant(f"{YEAR}-01-01"),
            stop=instant("2100-12-31"),
            value=0.06,  # 6% instead of current rate
        )
        return parameters

    class reform(Reform):
        def apply(self):
            self.modify_parameters(modify_parameters)
    return reform
```

### Population-level healthcare analysis

```python
from policyengine_us import Microsimulation
import numpy as np

YEAR = 2026

# Use state-calibrated dataset for state-level analysis (much more accurate)
sim = Microsimulation(
    dataset="hf://policyengine/policyengine-us-data/states/UT.h5"
)

# Calculate baseline
weights = sim.calculate("person_weight", YEAR).values
medicaid_enrolled = sim.calculate("medicaid_enrolled", YEAR).values
aca_ptc = sim.calculate("aca_ptc", YEAR, map_to="person").values

# Weighted population counts
total_medicaid = (weights * medicaid_enrolled.astype(float)).sum()
total_aca_spending = (weights * aca_ptc).sum()

print(f"Medicaid enrollment: {total_medicaid:,.0f}")
print(f"Total ACA PTC spending: ${total_aca_spending:,.0f}")
```

### Common healthcare analysis patterns

#### Tracking coverage transitions

When modeling reforms that change Medicaid eligibility, track where people go:

```python
baseline_medicaid = baseline.calculate("medicaid_enrolled", YEAR).values
reform_medicaid = reform_sim.calculate("medicaid_enrolled", YEAR).values
reform_ptc_eligible = reform_sim.calculate("is_aca_ptc_eligible", YEAR).values

loses_medicaid = baseline_medicaid & ~reform_medicaid
gains_aca = loses_medicaid & reform_ptc_eligible
coverage_gap = loses_medicaid & ~reform_ptc_eligible  # Below 100% FPL, no ACA access

print(f"Lose Medicaid: {(weights * loses_medicaid.astype(float)).sum():,.0f}")
print(f"Transition to ACA: {(weights * gains_aca.astype(float)).sum():,.0f}")
print(f"Fall into coverage gap: {(weights * coverage_gap.astype(float)).sum():,.0f}")
```

#### Distributional analysis by income

```python
income_level = sim.calculate("medicaid_income_level", YEAR).values

# Group by FPL brackets
brackets = [(0, 1.0), (1.0, 1.38), (1.38, 2.0), (2.0, 4.0)]
for low, high in brackets:
    mask = (income_level >= low) & (income_level < high)
    enrolled = (weights * mask * medicaid_enrolled.astype(float)).sum()
    total = (weights * mask.astype(float)).sum()
    print(f"{low*100:.0f}-{high*100:.0f}% FPL: {enrolled:,.0f} / {total:,.0f}")
```

### Known pitfalls

#### Use state datasets for state analysis

The national CPS dataset can give implausible state-level results. For example, national CPS showed 76% employer-sponsored insurance at 100-138% FPL in Utah — the state-calibrated dataset gives much more realistic estimates.

```python
# National (less accurate for state analysis)
sim = Microsimulation(dataset="hf://policyengine/policyengine-us-data/enhanced_cps_2024.h5")

# State-calibrated (preferred for state analysis)
sim = Microsimulation(dataset="hf://policyengine/policyengine-us-data/states/UT.h5")
```

#### California ACA rating area bug

LA county's rating area can cause errors in California simulations. Workaround:

```python
import numpy as np

try:
    aca_ptc = sim.calculate("aca_ptc", YEAR)
except Exception as e:
    if state == "CA":
        sim.set_input("in_la", YEAR, np.zeros(n_households, dtype=bool))
        aca_ptc = sim.calculate("aca_ptc", YEAR)
```

#### The coverage gap

People below 100% FPL who lose Medicaid may not qualify for ACA premium tax credits (which start at 100% FPL in non-expansion states). Always check for this when modeling Medicaid eligibility changes.

#### Medicaid category transitions

When removing one Medicaid eligibility pathway (e.g., adult expansion), some people may remain eligible through a different category (e.g., parent Medicaid). Track `medicaid_category` in both baseline and reform to identify true coverage loss vs. category reassignment.

## For contributors

### Healthcare review checklist

When reviewing healthcare PRs, check these domain-specific items in addition to the standard review checklist:

**Program interactions:**
- [ ] If Medicaid eligibility changed, verify downstream ACA effects (is_aca_ptc_eligible checks Medicaid status)
- [ ] If CHIP eligibility changed, verify it still excludes Medicaid-eligible children
- [ ] Check that mutual exclusion logic in is_aca_ptc_eligible includes all relevant coverage sources

**Eligibility structure:**
- [ ] New Medicaid categories use the `_fc` / `_nfc` split pattern
- [ ] Category precedence order in medicaid_category.py is preserved (mandatory before optional, per 42 CFR 435.119)
- [ ] Income variable uses correct MAGI definition (medicaid_magi for Medicaid/ACA, not raw AGI)

**Geographic variation:**
- [ ] State-specific Medicaid income limits use the correct parameter path (gov.hhs.medicaid.eligibility.categories.[category].income_limit.[STATE])
- [ ] ACA changes check whether affected states use default federal age curves or custom curves (AL, DC, MA, MN, MS, OR, UT) or family tiers (NY, VT)
- [ ] SLCSP updates cover all affected rating areas

**Temporal correctness:**
- [ ] ACA calculations use prior-year FPL where required
- [ ] SLCSP premiums handled as monthly values (not accidentally annualized)
- [ ] ARPA/IRA subsidy enhancement sunset dates are correct in parameter timeline

**Take-up and costs:**
- [ ] Take-up rates are parameterized (not hard-coded)
- [ ] Cost allocation uses calibrated per-capita values by eligibility group and state
- [ ] Enrollment calibration targets updated if eligibility rules changed

### Code organization

Healthcare variables live in three directories under `policyengine_us/variables/gov/`:

```
gov/hhs/medicaid/          # ~44 variable files
gov/aca/                    # ~24 variable files
gov/hhs/chip/              # 8 variable files
gov/hhs/medicare/          # Parts A, B, savings programs
```

### Variable naming patterns

| Pattern | Example | Purpose |
|---------|---------|---------|
| `is_[program]_eligible` | `is_medicaid_eligible` | Overall eligibility flag |
| `[program]_category` | `medicaid_category` | Enum categorization |
| `is_[category]_for_[program]` | `is_adult_for_medicaid` | Category-specific eligibility |
| `is_[category]_for_[program]_fc` | `is_adult_for_medicaid_fc` | Financial criteria only |
| `is_[category]_for_[program]_nfc` | `is_adult_for_medicaid_nfc` | Non-financial criteria only |
| `[program]_magi` | `medicaid_magi` | Income measure |
| `[program]_income_level` | `medicaid_income_level` | Income as fraction of FPL |
| `takes_up_[program]_if_eligible` | `takes_up_medicaid_if_eligible` | Take-up modeling |
| `[program]_cost` | `medicaid_cost` | Benefit cost/amount |
| `per_capita_[program]` | `per_capita_chip` | Per-person cost |

### The `_fc` / `_nfc` pattern

Healthcare eligibility splits financial and non-financial criteria into separate variables. This is important because:

1. **Testability** — you can test income thresholds independently from age/demographic requirements
2. **Reform modeling** — reforms often change only one dimension (e.g., raising income limits without changing age ranges)
3. **Clarity** — reviewers can verify each criterion against its regulatory source

```python
# is_adult_for_medicaid.py combines both using a class attribute (not a formula):
class is_adult_for_medicaid(Variable):
    # all_of_variables as class attribute — no formula method needed
    formula = all_of_variables([
        "is_adult_for_medicaid_fc",   # Income < state limit
        "is_adult_for_medicaid_nfc",  # Age 19-64, not pregnant
    ])
```

### Medicaid categorical hierarchy

Categories are evaluated in regulatory precedence order (42 CFR 435.119). Mandatory groups first, then optional:

```python
# From medicaid_category.py — ORDER MATTERS
variable_to_category = dict(
    is_ssi_recipient_for_medicaid=MedicaidCategory.SSI_RECIPIENT,          # 1st
    is_infant_for_medicaid=MedicaidCategory.INFANT,                         # 2nd
    is_young_child_for_medicaid=MedicaidCategory.YOUNG_CHILD,               # 3rd
    is_older_child_for_medicaid=MedicaidCategory.OLDER_CHILD,               # 4th
    is_pregnant_for_medicaid=MedicaidCategory.PREGNANT,                     # 5th
    is_parent_for_medicaid=MedicaidCategory.PARENT,                         # 6th
    is_young_adult_for_medicaid=MedicaidCategory.YOUNG_ADULT,               # 7th
    is_adult_for_medicaid=MedicaidCategory.ADULT,                           # 8th (expansion)
    is_senior_or_disabled_for_medicaid=MedicaidCategory.SENIOR_OR_DISABLED, # Last
)
```

A person matched to an earlier category is assigned that category even if they also qualify for a later one. This means adult expansion is always the residual category.

### Parameter structure

Healthcare parameters are deeply nested with state-level overrides:

```
parameters/gov/hhs/medicaid/
├── eligibility/
│   └── categories/
│       ├── adult/income_limit.yaml     # State-by-state limits
│       ├── infant/income_limit.yaml
│       ├── parent/income_limit.yaml
│       └── [5 more categories]
├── income/modification.yaml            # AGI adjustments
├── takeup_rate.yaml                    # 0.93 nationally
└── emergency_medicaid/enabled.yaml

parameters/gov/aca/
├── state_rating_area_cost.yaml         # 1,565 lines — SLCSP by state x rating area
├── age_curves/
│   ├── default.yaml                    # Federal 3:1 ratio
│   ├── al.yaml, dc.yaml, ...          # 7 states with custom curves
│   └── ny.yaml, vt.yaml               # Family tier states
├── required_contribution_percentage/
│   ├── threshold.yaml                  # FPL brackets
│   ├── initial.yaml                    # Initial contribution rates by bracket
│   └── final.yaml                      # Final contribution rates by bracket
└── ptc_income_eligibility.yaml         # 100-400%+ FPL range
```

### ACA geographic complexity

The ACA premium calculation involves three layers of geographic variation:

1. **Rating area** — ~500 state+rating-area zones across the US, each with its own SLCSP benchmark premium
2. **Age curves** — most states use the federal 3:1 age rating; 7 states (AL, DC, MA, MN, MS, OR, UT) use custom curves; NY and VT use family tiers instead of age rating entirely
3. **State-specific rules** — max child count for subsidies, child age definitions

When adding or updating ACA parameters, check whether the state uses the default federal rules or has its own.

### Program interaction rules

Healthcare programs check for mutual exclusion:

```python
# In is_aca_ptc_eligible.py
INELIGIBLE_COVERAGE = [
    "is_medicaid_eligible",
    "is_chip_eligible",
    # ... other coverage sources
]
is_coverage_eligible = add(person, period, INELIGIBLE_COVERAGE) == 0
```

When modifying one program's eligibility, always verify the downstream effects on other programs. Removing Medicaid expansion, for example, shifts people to ACA eligibility (if above 100% FPL) or into a coverage gap (if below).

### Healthcare test patterns

Healthcare tests require attention to program interactions and categorical complexity that other benefit programs don't have.

**Testing category precedence:**

Verify that a person eligible for multiple Medicaid categories gets assigned the highest-precedence one:

```yaml
- name: Case 1, pregnant adult assigned PREGNANT not ADULT.
  period: 2026-01
  absolute_error_margin: 0.1
  input:
    people:
      person1:
        age: 25
        is_pregnant: true
        employment_income: 15_000
    households:
      household1:
        state_code_str: NY
  output:
    medicaid_category: PREGNANT  # Not ADULT, even though income qualifies for expansion
```

**Testing program mutual exclusion:**

Verify that Medicaid-eligible people are excluded from ACA PTC:

```yaml
- name: Case 2, Medicaid eligible person gets no ACA PTC.
  period: 2026
  absolute_error_margin: 0.1
  input:
    people:
      person1:
        age: 30
        employment_income: 15_000
        is_tax_unit_head: true
    households:
      household1:
        state_code_str: NY
  output:
    is_medicaid_eligible: true
    aca_ptc: 0
```

**Testing the `_fc` / `_nfc` split independently:**

Test financial and non-financial criteria separately to isolate failures:

```yaml
# Financial criteria only
- name: Case 3, adult income below Medicaid limit.
  period: 2026-01
  absolute_error_margin: 0.1
  input:
    people:
      person1:
        age: 30
        employment_income: 15_000
    households:
      household1:
        state_code_str: NY
  output:
    is_adult_for_medicaid_fc: true

# Non-financial criteria only
- name: Case 4, person in adult age range.
  period: 2026-01
  absolute_error_margin: 0.1
  input:
    people:
      person1:
        age: 30
        is_pregnant: false
  output:
    is_adult_for_medicaid_nfc: true
```

**Testing coverage transitions in reforms:**

When testing reforms that change eligibility, verify where people land:

```yaml
# In integration tests, check all three outcomes:
# 1. Still has coverage (different program)
# 2. Transitions to ACA
# 3. Falls into coverage gap (below 100% FPL, no ACA access)
```

**Testing state-specific ACA rules:**

For states with custom age curves or family tiers, include state-specific test cases:

```yaml
# NY uses family tiers instead of age rating
- name: Case 5, NY family tier premium.
  period: 2026
  absolute_error_margin: 1
  input:
    people:
      person1:
        age: 35
        employment_income: 40_000
        is_tax_unit_head: true
      person2:
        age: 8
        is_tax_unit_dependent: true
    households:
      household1:
        state_code_str: NY
  output:
    slcsp: 0  # Verify against NY family tier rates, not age-based
```

### Take-up modeling

All healthcare programs use pseudo-random seeding for take-up:

```python
class takes_up_medicaid_if_eligible(Variable):
    def formula(person, period, parameters):
        seed = person("medicaid_take_up_seed", period)  # Random 0-1
        takeup_rate = parameters(period).gov.hhs.medicaid.takeup_rate
        return seed < takeup_rate
```

Default take-up rates: Medicaid ~93%, ACA PTC ~62-67%. These are parameterized and can be modified in reforms.

### Cost allocation

Healthcare costs use per-capita lookups calibrated from MACPAC and CMS data, broken down by eligibility group and state:

```python
class medicaid_cost_if_enrolled(Variable):
    def formula(person, period, parameters):
        group = person("medicaid_group", period)  # Enum
        state = person.household("state_code", period)
        per_capita = parameters(period).calibration.gov.hhs.medicaid.spending
        return per_capita.by_eligibility_group[group][state]
```

### Temporal considerations

- **ACA uses prior-year FPL**: Income eligibility is measured against the previous year's federal poverty guidelines
- **SLCSP premiums are monthly**: But benefits are typically calculated annually — watch for period mismatches
- **Contribution rates sunset**: ARPA/IRA enhanced subsidies have expiration dates encoded in the parameter timeline

## Resources

- **Medicaid variables**: `policyengine_us/variables/gov/hhs/medicaid/`
- **ACA variables**: `policyengine_us/variables/gov/aca/`
- **CHIP variables**: `policyengine_us/variables/gov/hhs/chip/`
- **Healthcare parameters**: `policyengine_us/parameters/gov/hhs/medicaid/`, `policyengine_us/parameters/gov/aca/`
- **Calibration data**: `policyengine_us/parameters/calibration/gov/hhs/`
- **Analysis examples**: `analysis-notebooks/us/healthcare/`, `analysis-notebooks/us/medicaid/`, `analysis-notebooks/us/states/ut/`
- **Legal references**: 42 CFR 435.119 (Medicaid categories), IRC 36B (premium tax credit)
