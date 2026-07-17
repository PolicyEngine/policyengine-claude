---
name: policyengine-healthcare
description: |
  US healthcare domain knowledge (Medicaid, ACA premium tax credit, CHIP, Medicare) for analysts
  using the policyengine package. Load for: why ACA PTC and Medicaid changes show $0 in
  household_net_income (the include_health_benefits_in_net_income gotcha) and how to measure health
  impact instead; the aca_ptc / medicaid / medicaid_category / slcsp / is_aca_ptc_eligible /
  per_capita_chip variables; Medicaid category precedence (42 CFR 435.119); the _fc/_nfc split; why
  a flat reform dict fails on required_contribution_percentage; slcsp returning $0 for the
  ineligible; and what "IRA reform" means.
  Triggers: Medicaid, ACA, premium tax credit, PTC, aca_ptc, SLCSP, CHIP, Medicare, MAGI, coverage
  gap, Medicaid expansion, IRA subsidy extension, required contribution percentage, age curve,
  family tier, medicaid_category.
  NOT for: non-health US programs (use policyengine-us); new health variables (use
  policyengine-model-development); core calculate_household / Simulation mechanics (use the
  policyengine skill).
metadata:
  category: domain
---

# PolicyEngine US healthcare domain knowledge

Medicaid, the ACA marketplace (premium tax credit), CHIP, and Medicare are the hardest US programs
to analyze correctly, because they are modeled as **in-kind health benefits** rather than cash.
This skill is the domain layer for analysts using the `policyengine` package; for non-health US
programs use **policyengine-us**, for the shared calculation/reform mechanics use the
**policyengine** skill, and for building new health variables use **policyengine-model-development**.

Verified against policyengine 4.21.0 / policyengine-us 1.764.6 (2026-07). Re-verify variable names
and parameter values before reporting.

## The one gotcha that dominates everything: health benefits are excluded from net income

`gov.simulation.include_health_benefits_in_net_income` defaults to **False**. ACA PTC, Medicaid,
CHIP, and Medicare cost flow through `household_health_benefits`, which the default
`household_net_income` **does not include**. So a reform that changes `aca_ptc` or `medicaid`
produces a **$0 change in `household_net_income`** — the single biggest time-sink in health
analysis. If you score a PTC or Medicaid reform by net-income change and get zero, this is why.

Measure health impact one of these ways instead:

- **`household_net_income_including_health_benefits`** — the same net income *with* health benefits
  folded in. Its difference from `household_net_income` is exactly the household's health-benefit
  value.
- **The program variable directly** — `aca_ptc` (tax_unit), `medicaid` (person), summed or
  differenced across baseline and reform.
- **Population cost: `pe.us.calculate_budgetary_impact`.** Its `total` already adds the
  shared-funding health-program cost (Medicaid / CHIP / Medicare Savings Programs) on top of
  Δtax − Δbenefits, so it captures the health split automatically — do not hand-roll it from
  `household_net_income`. See the policyengine skill for the population flow.

Verified end to end (single adult, $35k, Texas — ACA-eligible, not Medicaid-eligible):

<!-- verify -->
```python
import policyengine as pe

r = pe.us.calculate_household(
    people=[{"age": 45, "employment_income": 35_000}],
    tax_unit={"filing_status": "SINGLE"},
    household={"state_code": "TX"},
    year=2026,
    extra_variables=["aca_ptc", "household_net_income_including_health_benefits"],
)
assert round(r.tax_unit.aca_ptc, 2) == 6_250.38          # a real PTC...
# ...but it is NOT in default net income; the gap is exactly the PTC:
gap = (r.household.household_net_income_including_health_benefits
       - r.household.household_net_income)
assert round(gap, 2) == round(r.tax_unit.aca_ptc, 2)
```

And the toggle itself:

<!-- verify -->
```python
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters
assert p.gov.simulation.include_health_benefits_in_net_income("2026-01-01") == False
```

## Healthcare variables

Entity and period are load-bearing (verified). Note `aca_ptc` and `slcsp` are **tax-unit**;
Medicaid/CHIP eligibility is **person**; `slcsp` is **monthly**.

| Variable | Entity | Period | Meaning |
|---|---|---|---|
| `aca_ptc` | tax_unit | year | ACA premium tax credit (annual) |
| `is_aca_ptc_eligible` | person | year | PTC eligibility (income band, no disqualifying coverage) |
| `aca_magi` | tax_unit | year | MAGI for ACA — `adds` `medicaid_magi` |
| `aca_required_contribution_percentage` | tax_unit | year | required premium contribution rate |
| `slcsp` | tax_unit | **month** | second-lowest silver plan (benchmark) premium |
| `medicaid` | person | year | modeled Medicaid benefit value (per-capita cost when enrolled) |
| `is_medicaid_eligible` | person | year | overall Medicaid eligibility |
| `medicaid_enrolled` | person | year | eligibility × take-up |
| `medicaid_category` | person | year | enum (see precedence below) |
| `medicaid_magi` | tax_unit | year | MAGI for Medicaid |
| `medicaid_income_level` | person | year | MAGI as a fraction of FPL |
| `per_capita_chip` | person | year | CHIP benefit per capita |
| `is_chip_eligible` | person | year | CHIP eligibility |

Medicaid and ACA income tests use **`medicaid_magi`**, not raw AGI (`aca_magi` delegates to it).
The programs are mutually exclusive by construction — `is_aca_ptc_eligible` excludes people who are
Medicaid- or CHIP-eligible — so a Medicaid eligibility change cascades into ACA eligibility and can
open a **coverage gap** (below 100% FPL, no Medicaid and no PTC in non-expansion states).

## Medicaid category precedence (42 CFR 435.119)

`medicaid_category` assigns each person the **highest-precedence** category they qualify for.
Federal law requires mandatory groups before optional ones, and the ACA "not otherwise eligible"
rule (42 CFR 435.119) makes **adult expansion the residual** among mandatory groups. The model's
current evaluation order (verified in 1.764.6 — it has grown beyond the classic nine categories
older notes cite):

1. `SSI_RECIPIENT` — non-MAGI, automatic in most states
2. `INFANT` → 3. `YOUNG_CHILD` → 4. `OLDER_CHILD` — mandatory MAGI children
5. `PREGNANT`
6. `PARENT` / caretaker relative
7. `YOUNG_ADULT` (optional, 19–20)
8. `ADULT` — expansion, evaluated last among mandatory per 435.119
9. `SENIOR_OR_DISABLED` — optional aged/blind/disabled (non-SSI)
10. `MEDICALLY_NEEDY` → 11. `WORKING_DISABLED_BUY_IN` → 12. `SECTION_1115_MEC_ADULT`
    plus `HEALTHIER_MISSISSIPPI_WAIVER` (MS-specific)

Because order is precedence, a pregnant adult who also meets the expansion income test is
`PREGNANT`, not `ADULT`. When a reform removes one pathway, always compare `medicaid_category`
across baseline and reform — some people reassign to another category (true coverage retained)
rather than losing coverage.

## The `_fc` / `_nfc` split

Each Medicaid category's eligibility is split into **financial criteria** (`_fc`, income vs the
state limit) and **non-financial criteria** (`_nfc`, age / pregnancy / immigration): e.g.
`is_adult_for_medicaid` = `is_adult_for_medicaid_fc` & `is_adult_for_medicaid_nfc`. This lets you
test an income threshold independently of demographic rules, and lets a reform move only one
dimension (raise an income limit without touching age ranges). When a reform or test targets
eligibility, target the right half.

## Reforms: the parameters that flat dicts cannot express

Most ACA/Medicaid parameters take a flat reform dict `{path: value}` (see the policyengine skill).
Two structures do not:

- **`gov.aca.required_contribution_percentage`** is **list-valued** — three parallel arrays
  (`threshold`, `initial`, `final`) that together define the FPL-bracketed contribution schedule.
  A single `{path: scalar}` cannot represent a schedule change, so extending or steepening the
  contribution curve needs a parameter-array edit (a `modify_parameters` / variable-override reform
  on the country package), not a flat dict. See policyengine-model-development for writing one.
- State-specific **Medicaid income limits** live per-state under
  `gov.hhs.medicaid.eligibility.categories.<category>.income_limit.<STATE>`; reform the specific
  state key, not a national scalar.

**"IRA reform"** in PolicyEngine shorthand means extending the Inflation Reduction Act's enhanced
ACA subsidies — the lowered required-contribution percentages and the removal of the 400%-FPL
subsidy cliff — beyond their scheduled sunset. It is a change to `required_contribution_percentage`
and the income-eligibility cap, i.e. the list-valued case above.

## `slcsp` returns $0 for the ineligible

`slcsp` (the benchmark second-lowest silver premium) returns **$0 when the person is not
ACA-eligible** — the model skips the premium lookup. It is not a $0 premium. If you need the
unsubsidized benchmark for someone regardless of eligibility (e.g. "what would they pay without
subsidies?"), read the rating-area cost parameters directly rather than `slcsp`:

```python
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters
p.gov.aca.state_rating_area_cost  # indexed by state and rating area
```

## Geographic variation: age curves and family tiers

ACA premiums vary by rating area, and the age-rating rule is not uniform. Most states use the
federal age curve, but the model carries **custom age curves for AL, DC, MA, MN, MS, OR, UT** and
**family-tier rating (not age-based) for NY and VT** (verified from
`policyengine_us/parameters/gov/aca/age_curves/`: `al, dc, ma, mn, ms, or, ut` plus `ny, vt`). When
a change touches ACA premiums, check whether the affected state is one of these — a fix that
assumes the federal curve will be wrong for them.

## Data for state-level health analysis

State-level Medicaid/ACA results need a state-representative sample. There are **no per-state data
files** — do it by filtering the certified national dataset (or the `populace_us_2024_acs_local`
build) by its `state_fips` / `state_code` column. The dataset names, `ensure_datasets`, and scoping
strategies are all in the **policyengine** skill; how the data is built and calibrated is in
**policyengine-data**. National samples can give implausible single-state health mixes, so scope to
the state and read the build's release notes before reporting state numbers.
