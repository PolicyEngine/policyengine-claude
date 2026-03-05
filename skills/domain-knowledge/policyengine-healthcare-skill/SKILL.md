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
| `slcsp` | tax_unit | Second-lowest silver plan premium (monthly, definition_period=MONTH). **Returns $0 for ineligible people** — the model skips the calculation when someone doesn't qualify for ACA. To get the unsubsidized benchmark premium regardless of eligibility, look at the underlying rating area cost parameters directly. |
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

#### IRA subsidy extension (variable-override reform)

The most common ACA policy question: extending the IRA-enhanced subsidies beyond their 2025 sunset. **`Reform.from_dict()` does not work** for ACA contribution rate parameters because they are list-valued (threshold + initial + final arrays). Use a variable-override reform instead:

```python
from policyengine_us import Microsimulation
from policyengine_core.reforms import Reform

ANALYSIS_YEAR = 2026  # Don't use "YEAR" — it shadows model_api.YEAR

# Look up actual parameter values to build the reform
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters
contrib = p.gov.aca.required_contribution_percentage

# Check what values look like pre/post sunset
print("2025 initial rates:", contrib.initial("2025-01-01"))  # IRA-enhanced
print("2026 initial rates:", contrib.initial("2026-01-01"))  # Post-sunset (higher)

# Option A: Use Reform.from_dict for the scalar parameters that DO work
reform = Reform.from_dict({
    # The 400% FPL cap removal (IRA made subsidies available above 400%)
    'gov.aca.ptc_income_eligibility[2].amount': {
        f'{ANALYSIS_YEAR}-01-01.2100-12-31': True
    },
}, 'policyengine_us')

# Option B: For contribution rates (list-valued), use modify_parameters
from policyengine_core.periods import instant

def create_ira_extension():
    def modify_parameters(parameters):
        # Restore IRA-era contribution percentages
        # You need to set each bracket's initial and final rates
        for bracket_param in ['initial', 'final']:
            getattr(
                parameters.gov.aca.required_contribution_percentage,
                bracket_param,
            ).update(
                start=instant(f"{ANALYSIS_YEAR}-01-01"),
                stop=instant("2100-12-31"),
                value=getattr(contrib, bracket_param)("2025-01-01"),
            )
        return parameters

    class reform(Reform):
        def apply(self):
            self.modify_parameters(modify_parameters)
    return reform
```

Also see existing reforms in `policyengine_us/reforms/aca/` for production examples of variable-override ACA reforms.

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

#### PTC does not flow into `household_net_income` (biggest time sink)

The microsimulation skill says to use `household_net_income` change as the budgetary cost measure. **This does not work for ACA premium tax credit reforms.** The PTC is classified as an in-kind health benefit, not a refundable tax credit, so it flows through a separate chain:

```
aca_ptc → premium_tax_credit → household_health_benefits → household_benefits
```

There is a toggle parameter `gov.simulation.include_health_benefits_in_net_income` that defaults to **False**. With the default, PTC changes produce a **$0 change in `household_net_income`**.

**How to measure PTC impact instead:**

```python
# Option 1: Use household_net_income_including_health_benefits
baseline_hni = baseline.calc("household_net_income_including_health_benefits", period=YEAR)
reformed_hni = reformed.calc("household_net_income_including_health_benefits", period=YEAR)
cost = (reformed_hni - baseline_hni).sum()

# Option 2: Measure the PTC change directly
baseline_ptc = baseline.calc("aca_ptc", period=YEAR).sum()
reformed_ptc = reformed.calc("aca_ptc", period=YEAR).sum()
ptc_cost = reformed_ptc - baseline_ptc

# Option 3: Enable the toggle in the reform
# Add gov.simulation.include_health_benefits_in_net_income = True
# Then household_net_income will include PTC
```

#### "IRA reform" means extending IRA-era ACA subsidy brackets

In PolicyEngine context, "IRA reform" is shorthand for extending the Inflation Reduction Act's enhanced ACA premium tax credit brackets beyond their 2025 sunset. The IRA (2022) temporarily expanded ACA subsidies by lowering required contribution percentages and removing the 400% FPL subsidy cliff. These enhancements are scheduled to expire — "IRA reform" typically means making them permanent or extending them.

See the variable-override reform example below for how to implement this.

#### `YEAR` constant shadows `model_api.YEAR`

If you define `YEAR = 2026` in the same file where you also define a reform variable class, it shadows the `YEAR` period constant imported from `model_api`. This breaks `definition_period = YEAR` on variable classes:

```python
# ❌ This breaks — YEAR is now 2026 (int), not the period constant
from policyengine_us.model_api import *
YEAR = 2026  # Shadows model_api.YEAR

class my_reform_variable(Variable):
    definition_period = YEAR  # Gets 2026, not the YEAR period constant!

# ✅ Use a different name for the analysis year
from policyengine_us.model_api import *
ANALYSIS_YEAR = 2026

class my_reform_variable(Variable):
    definition_period = YEAR  # Gets the period constant from model_api
```

#### `slcsp` returns $0 for ineligible people

The `slcsp` variable (second-lowest silver plan premium) returns $0 when the person is not ACA-eligible — the model skips the premium lookup entirely. If you need the unsubsidized benchmark premium for comparison purposes (e.g., "what would this person pay without subsidies?"), you can't just read `slcsp`. Instead, look up the premium from the rating area cost parameters directly:

```python
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters
# state_rating_area_cost is indexed by state and rating area
p.gov.aca.state_rating_area_cost("2026-01-01")
```

#### `healthcare_benefit_value` entity mapping in population analysis

`healthcare_benefit_value` is a household-level variable that aggregates a tax-unit-level variable (`aca_ptc`). When you use `map_to='person'`, the benefit value gets spread across all household members, including those not in the affected tax unit. This can produce a "mystery group" that appears to gain healthcare benefit value but shows no change in `aca_ptc`. Measure PTC impact at the tax-unit level when possible.

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
├── required_contribution_percentage/   # LIST-VALUED — not scalar!
│   ├── threshold.yaml                  # FPL bracket boundaries (list)
│   ├── initial.yaml                    # Initial contribution rates by bracket (list)
│   └── final.yaml                      # Final contribution rates by bracket (list)
│   # These three files form parallel arrays. Reform.from_dict() cannot modify
│   # list-valued parameters — use modify_parameters() instead.
└── ptc_income_eligibility.yaml         # 100-400%+ FPL range (bracket-indexed)
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
