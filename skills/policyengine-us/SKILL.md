---
name: policyengine-us
description: |
  US tax-benefit domain knowledge for analysts computing household or population impacts
  with the policyengine package (pe.us). Load for: which entity a US program attaches to
  (tax_unit vs spm_unit vs person), tax-unit role flags and filing status, post-OBBBA
  current-law values (2026 CTC, standard deduction, SALT cap), the parameter tree
  (gov.irs / gov.states.{xx} / gov.usda.snap / gov.ssa), state income-tax and credit
  coverage, and SNAP monthly/FPL semantics.
  Triggers: EITC, CTC, SNAP, TANF, SSI, income tax, state income tax, standard deduction,
  SALT cap, federal poverty level, spm_unit, tax_unit, filing status, is_tax_unit_dependent,
  household_net_income, in_poverty, state credit, CalEITC, ca_eitc, ny_eitc, OBBBA.
  NOT for: implementing new US variables/parameters (use policyengine-model-development);
  Medicaid/ACA/CHIP/Medicare (use policyengine-healthcare); the core calculate_household /
  Simulation / reform mechanics shared across countries (use the policyengine skill).
metadata:
  category: domain
---

# PolicyEngine US domain knowledge

This skill is the US-specific layer for analysts using the `policyengine` package. It assumes
you already know the shared mechanics — `pe.us.calculate_household`, population `Simulation`,
reform dicts, datasets — from the **policyengine** skill; read that first for anything not
US-specific. For building new US variables or parameters, use **policyengine-model-development**.
For Medicaid / ACA / CHIP / Medicare, use **policyengine-healthcare**.

Verified against policyengine 4.21.0 / policyengine-us 1.764.6 (2026-07). Re-verify law-year
values before reporting — the model updates continuously.

## The six entities, and which program lives on which

US taxes and benefits are administered by different units, so the model has six entities. A
program's variable is defined on exactly one of them, and reading it from the wrong entity is the
most common US mistake.

| Entity | Plural key | What it groups |
|---|---|---|
| `person` | `people` | individuals |
| `marital_unit` | `marital_units` | a married couple (or a single person) |
| `family` | `families` | a nuclear family (Census-style) |
| `tax_unit` | `tax_units` | a tax-filing unit (a 1040) |
| `spm_unit` | `spm_units` | a Supplemental Poverty Measure resource-sharing unit |
| `household` | `households` | everyone at a physical address |

Which entity a program attaches to (verified — entity *and* definition period both matter):

| Program / measure | Variable | Entity | Period |
|---|---|---|---|
| Federal income tax | `income_tax` | tax_unit | year |
| EITC | `eitc` | tax_unit | year |
| Child Tax Credit | `ctc` | tax_unit | year |
| State income tax (aggregate) | `state_income_tax` | tax_unit | year |
| SNAP | `snap` | spm_unit | **month** |
| TANF | `tanf` | spm_unit | year |
| SSI | `ssi` | **person** | **month** |
| Net income | `household_net_income` | household | year |
| Total benefits | `household_benefits` | household | year |
| Total taxes | `household_tax` | household | year |
| In poverty (SPM) | `in_poverty` | spm_unit | year |
| Person in poverty | `person_in_poverty` | person | year |
| Is a child | `is_child` | person | year |

Rules of thumb: **income tax and its credits (EITC, CTC, CDCC, education, and the aggregate
`state_income_tax`) are tax-unit variables**; **means-tested transfers keyed to a resource-sharing
unit (SNAP, TANF, school meals, housing) are spm_unit variables**; **SSI is a person-level
benefit** (each individual's own SSI), rolled up into `household_benefits`. Poverty is measured on
the `spm_unit`. On a `calculate_household` result you read these as dot-attributes on the singular
entity — `result.tax_unit.eitc`, `result.spm_unit.snap`, `result.person[0].ssi`,
`result.household.household_net_income`.

## Tax-unit roles and filing status

`tax_unit={"filing_status": ...}` accepts `SINGLE`, `JOINT`, `SEPARATE`, `HEAD_OF_HOUSEHOLD`,
`SURVIVING_SPOUSE`.

Three person-level role flags exist: `is_tax_unit_head`, `is_tax_unit_spouse`,
`is_tax_unit_dependent`. **You usually do not set them for a simple family** — minor children in
the `people` list are inferred as dependents automatically, the first adult is the head, and
`JOINT` designates the second adult as the spouse. Setting them wrong is worse than omitting them.

**When you do need them: adult dependents.** An adult in the `people` list is *not* auto-inferred
as a dependent. A 20-year-old student, a supported parent, or any qualifying relative must be
flagged `is_tax_unit_dependent: True`, or the model treats them as an independent unit member and
their credit vanishes. Verified — a HOH filer with a 20-year-old earning $4,000:

<!-- verify -->
```python
import policyengine as pe

def odc(dependent):
    kid = {"age": 20, "employment_income": 4_000}
    if dependent:
        kid["is_tax_unit_dependent"] = True
    return pe.us.calculate_household(
        people=[{"age": 45, "employment_income": 40_000}, kid],
        tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
        household={"state_code": "CA"},
        year=2026,
    ).tax_unit.ctc

assert odc(False) == 0      # adult not treated as a dependent -> no credit
assert odc(True) == 500     # $500 credit for other dependents (ODC)
```

## Household calculation

`state_code` (not `state_code_str`) goes in the `household` dict. A low-income married couple with
two children, showing where each program lands:

<!-- verify -->
```python
import policyengine as pe

r = pe.us.calculate_household(
    people=[
        {"age": 35, "employment_income": 25_000},
        {"age": 33, "employment_income": 0},
        {"age": 8},
        {"age": 5},
    ],
    tax_unit={"filing_status": "JOINT"},
    household={"state_code": "NY"},
    year=2026,
)
assert round(r.tax_unit.ctc) == 4_400          # 2 children x $2,200 (OBBBA, 2026)
assert round(r.tax_unit.eitc) == 7_316         # federal EITC (tax_unit)
assert round(r.spm_unit.snap) == 7_364         # annual = sum of 12 monthly allotments
assert round(r.household.household_net_income) == 62_681
```

Here `income_tax` is about −$10,691 (refundable EITC + CTC exceed liability), so
`household_net_income` exceeds gross earnings. `state_income_tax` can likewise be negative when
refundable state credits exceed state liability.

Variables outside the default output columns (poverty flags, `is_child`, state credits, most
intermediate variables) must be requested with `extra_variables=[...]`, or attribute access raises
`AttributeError` listing what *is* available:

<!-- verify -->
```python
import policyengine as pe

r = pe.us.calculate_household(
    people=[{"age": 35, "employment_income": 25_000}, {"age": 8}],
    tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
    household={"state_code": "NY"},
    year=2026,
    extra_variables=["in_poverty", "person_in_poverty", "is_child"],
)
assert r.person[1].is_child == 1
r.spm_unit.in_poverty          # SPM-unit poverty flag
r.person[0].person_in_poverty  # person-level projection
```

## Current law is post-OBBBA — check the year

The One Big Beautiful Bill Act reshaped 2026 federal law; pre-2026 summaries are wrong. Verified
2026 headline values (each is a live parameter read, not a memorized number):

<!-- verify -->
```python
from policyengine_us import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters

# Child Tax Credit: $2,200 per child in 2026 (not $2,000, not the $3,600 ARPA figure)
assert p.gov.irs.credits.ctc.amount.base[0].amount("2026-01-01") == 2_200

# Standard deduction, 2026
std = p.gov.irs.deductions.standard.amount
assert std.children["SINGLE"]("2026-01-01") == 16_100
assert std.children["JOINT"]("2026-01-01") == 32_200
assert std.children["HEAD_OF_HOUSEHOLD"]("2026-01-01") == 24_150

# SALT cap, by filing status: $40,400 in 2026, scheduled to revert to $10,000 in 2030
salt = p.gov.irs.deductions.itemized.salt_and_real_estate.cap
assert salt.children["JOINT"]("2026-01-01") == 40_400
assert salt.children["SEPARATE"]("2026-01-01") == 20_200
assert salt.children["JOINT"]("2030-01-01") == 10_000
```

The SALT cap is scheduled: $40,000 (2025) → $40,400 (2026), rising ~1%/yr through 2029, then a hard
revert to $10,000 in 2030. Always read the value at *your* simulation year before interpreting a
SALT reform.

## The parameter tree

Federal and state law live under `gov.*`. The top-level agencies (verified children of `gov`)
include `irs`, `ssa`, `hhs`, `usda`, `hud`, `dol`, `ed`, `doe`, `states`, `local`, `aca`,
`simulation`. The ones you reach for most:

| Path | Contains |
|---|---|
| `gov.irs.*` | federal income tax: `credits.ctc`, `credits.eitc`, `deductions.standard`, `deductions.itemized.salt_and_real_estate`, `payroll`, `capital_gains` |
| `gov.usda.snap.*` | SNAP: allotments, deductions, income limits, `expected_contribution` |
| `gov.ssa.*` | Social Security (`social_security`), SSI (`ssi`), `sga`, wage indices |
| `gov.hhs.*` | TANF (federal frame), Medicaid, CHIP |
| `gov.hud.*` | housing assistance |
| `gov.states.{xx}.*` | one node per state, `{xx}` = lowercase two-letter code (`ca`, `ny`, `dc`, …); state income tax lives at `gov.states.{xx}.tax`, state benefits under the agency (e.g. `gov.states.ca.cdss`) |

Bracket/scale parameters index the scale node directly — there is no `.brackets` segment
(`gov.irs.credits.ctc.amount.base[0].amount`). Discover paths by browsing `.children.keys()` on a
node or grepping the YAML tree in `policyengine-us/policyengine_us/parameters/gov/`; a guessed name
raises a `ValueError` listing the real children. See the policyengine skill for the three
reform-dict formats — they all share these paths.

## State coverage

PolicyEngine-US models income tax for **all 50 states and DC** (`gov.states` has one node per state
plus `dc`); `state_income_tax` is computed everywhere and returns 0 in no-income-tax states (TX,
FL, WA, …). Many states also model refundable credits — state EITCs, CTCs, and rent/property
credits — as `{state}_{program}` variables. Request them with `extra_variables`:

<!-- verify -->
```python
import policyengine as pe

r = pe.us.calculate_household(
    people=[{"age": 30, "employment_income": 20_000}, {"age": 4}],
    tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
    household={"state_code": "CA"},
    year=2026,
    extra_variables=["ca_eitc"],
)
assert round(r.tax_unit.eitc) == 4_427          # federal EITC
assert round(r.tax_unit.ca_eitc, 2) == 410.16   # CalEITC (state)
assert r.tax_unit.state_income_tax < 0          # refundable CA credits exceed liability
```

State-EITC variable names follow the pattern `{xx}_eitc` (`ny_eitc`, `md_eitc`, …); browse a
state's variables with `[v for v in CountryTaxBenefitSystem().variables if v.startswith("ca_")]`.

## SNAP: monthly, FPL-October, and the allotment hierarchy

SNAP is the US benefit whose timing most often surprises analysts. Everything below is verified
against the model source.

**SNAP is monthly.** `snap` and its inputs have `definition_period = MONTH`. When
`calculate_household` reports an annual figure (like the $7,364 above), it is the **sum of twelve
monthly allotments** — not one annual calculation. That is why SNAP produces partial-year cliffs
that annual-only reasoning misses.

**The FPL updates in October, on the federal fiscal year.** `snap_fpg` (the poverty guideline used
for the income tests) reads the guideline dated October 1: for a month in Oct–Dec it uses that
calendar year's October figure; for Jan–Sep it uses the *prior* year's October figure. So a
household near the limit can fail the gross-income test for nine months and pass for the last
three, landing its annual SNAP at roughly a quarter of the full-year amount rather than at zero.
This is a real feature of the law, not a rounding artifact.

**The allotment hierarchy** (each name verified to exist as a monthly spm_unit variable):

```
snap  =  snap_normal_allotment + snap_emergency_allotment + dc_snap_temporary_local_benefit
         |__ snap_normal_allotment = max( snap_min_allotment,
                                           snap_max_allotment - snap_expected_contribution )
             |__ snap_max_allotment          (by household size and region)
             |__ snap_expected_contribution  = floor(snap_net_income) x 0.30
             |    |__ snap_net_income = snap_gross_income - deductions
             |         (snap_standard_deduction, snap_earned_income_deduction,
             |          snap_dependent_care_deduction, shelter, medical, child support)
             |         snap_gross_income = snap_earned_income + snap_unearned_income
             |__ snap_min_allotment          (small 1-2 person households)

is_snap_eligible  =  meets_snap_gross_income_test   (<= 130% FPL, or categorical)
                   & meets_snap_net_income_test     (<= 100% FPL)
                   & meets_snap_asset_test
                   & (meets_snap_categorical_eligibility can override the gross test)
```

The 30% expected-contribution rate is itself a parameter — `gov.usda.snap.expected_contribution` =
0.30 in 2026 — so it is reformable.

To debug one month, drop to the country package and calculate at a monthly period:
`from policyengine_us import Simulation; Simulation(situation=...).calculate("snap_normal_allotment", "2026-11")`, with `.trace = True` for the dependency tree. That direct-import surface is for tracing,
not for analysis results you report (see the policyengine skill).

## Datasets and population analysis

US population runs use the certified `populace_us_2024` bundle (and `populace_us_2024_acs_local`
for state/district grain). The mechanics — `ensure_datasets`, `Simulation`,
`economic_impact_analysis`, `calculate_budgetary_impact`, MicroSeries — are shared across countries
and documented in the **policyengine** skill; how Populace is built and calibrated is in the
**policyengine-data** skill. State and congressional-district breakdowns filter one national
dataset by its `state_fips` / `congressional_district_geoid` columns — there are no per-state or
per-district data files.
