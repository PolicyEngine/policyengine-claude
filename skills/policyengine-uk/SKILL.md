---
name: policyengine-uk
description: |
  Load before writing PolicyEngine-UK code — UK household calculations, income tax (incl.
  Scottish and Welsh variations), National Insurance, Universal Credit and other benefits,
  poverty and reform analysis. Covers the person/benunit/household entity model (UK has NO
  tax_unit), pe.uk.calculate_household, BHC vs AHC poverty, ITL1 regions, populace_uk_2023
  data, and the policyengine_uk Scenario surface for country-model development.
  Triggers: policyengine uk, pe.uk, Universal Credit, child benefit, pension credit, housing
  benefit, council tax, income tax, national insurance, personal allowance, Scottish income
  tax, Welsh rate, benunit, hbai, in_poverty_bhc, in_poverty_ahc, ITL1 region, populace_uk,
  HUGGING_FACE_TOKEN, UK reform, Scenario.
  NOT for: US or Canada models (see policyengine-us / policyengine-canada), general
  microsimulation mechanics (see policyengine), or implementing new UK variables/parameters
  inside the model (see policyengine-model-development).
metadata:
  category: domain
---

# PolicyEngine UK

UK-specific facts for the PolicyEngine Python stack. Read the `policyengine` skill first for
the canonical `import policyengine as pe` interface, the population flow
(`ensure_datasets` / `Simulation` / `economic_impact_analysis`), the MicroSeries discipline,
and dataset handling — this skill only carries what is *different* about the UK.

Verified against policyengine 4.21.0 + policyengine-uk 2.89.2 + policyengine-core 3.30.0
(2026-07). UK examples are not in the `[us]`-only CI verify set, so they carry no
`<!-- verify -->` marker; each was run manually in a `policyengine[uk]` environment.

## Setup

The UK model is an extra — bare `policyengine` installs no country model:

```bash
uv pip install "policyengine[uk]"   # UK model + certified UK data bundle metadata
```

Household calculations need no data download. Population runs need the UK dataset, which is a
**private** Hugging Face repo — see "Population data" below.

## Entity model — and the benunit trap

UK entities are **`person` → `benunit` → `household`**. There is **no `tax_unit`** and no
`spm_unit` / `marital_unit` / `family` — those are US entities. The single most common UK
mistake is reaching for `result.tax_unit` out of US habit; on a UK result it raises
`AttributeError` (verified: a UK result has `person`, `benunit`, `household` and no `tax_unit`).

| Concept | US entity | UK entity |
|---|---|---|
| Means-tested assessment unit | `tax_unit` (+ `spm_unit`) | **`benunit`** (benefit unit) |
| Statistical unit for poverty | `spm_unit` / `household` | `household` |
| Individual | `person` | `person` |

A **benefit unit** is a single adult or a couple plus their dependent children — the DWP
assessment unit for means-tested benefits (Universal Credit, Pension Credit, etc.). One
household can contain several benunits (e.g. adult children living with parents). Read
means-tested benefits at the **benunit** level, income tax and NI at the **person** level, and
net income and poverty at the **household** level.

## Household calculations

`pe.uk.calculate_household` mirrors the US call (keyword-only, `year` defaults to 2026), but
results are read on UK entities. Access is dot-attribute on singular entities; only
`result.person` is a list.

```python
import policyengine as pe

r = pe.uk.calculate_household(
    people=[{"age": 35, "employment_income": 50_000}],
    year=2026,
)
assert round(r.person[0].income_tax) == 7_486
assert round(r.person[0].national_insurance) == 2_994
assert round(r.household.hbai_household_net_income) == 39_520
```

Net income comes in two conventions: **`hbai_household_net_income`** follows the DWP
Households Below Average Income definition (the one PolicyEngine reports, and what the poverty
measures below use); `household_net_income` is the plain accounting definition. Prefer the
HBAI variable for anything compared against official UK statistics.

Benefit-unit variables read off `benunit` (a family with two children on £30k gross):

```python
r = pe.uk.calculate_household(
    people=[
        {"age": 35, "employment_income": 30_000},
        {"age": 33},
        {"age": 8},
        {"age": 5},
    ],
    household={"region": "NORTH_WEST"},
    year=2026,
)
r.benunit.universal_credit   # 6029.82
r.benunit.child_benefit      # 2337.40
```

Reforms are the same **flat `{parameter_path: value}` dict** as the US package surface:

```python
reformed = pe.uk.calculate_household(
    people=[{"age": 35, "employment_income": 50_000}],
    year=2026,
    reform={"gov.hmrc.income_tax.allowances.personal_allowance.amount": 15_000},
)
assert round(reformed.person[0].income_tax) == 7_000   # 2,430 more allowance x 20%
```

## Poverty — always state the measure

UK poverty is reported at the **household** level under two measures, and they can disagree
for the same household:

- **`in_poverty_bhc`** — Before Housing Costs.
- **`in_poverty_ahc`** — After Housing Costs.

```python
fam = pe.uk.calculate_household(
    people=[{"age": 35, "employment_income": 16_000}, {"age": 33}, {"age": 4}, {"age": 2}],
    household={"region": "WALES"},
    year=2026,
)
fam.household.in_poverty_bhc   # 1.0  (in poverty before housing costs)
fam.household.in_poverty_ahc   # 0.0  (NOT in poverty after housing costs)
```

That verified split — same household, BHC in poverty, AHC not — is why a UK poverty figure is
meaningless without its measure. Name BHC or AHC in every result, and match whichever the
source you compare against used (DWP HBAI headline child-poverty figures are AHC). Deep-poverty
variants (`in_deep_poverty_bhc` / `in_deep_poverty_ahc`) follow the same convention. At
population scale these are the poverty variables behind `compute_uk_*` breakdowns and the
`Poverty` outputs described in the `policyengine` skill.

## Parameter lookup

For "what is the rate/threshold?" questions, read the parameter tree directly (no simulation).
Print the live value in your working year rather than trusting a hardcoded rate — UK rates and
thresholds move at every fiscal event.

```python
from policyengine_uk import CountryTaxBenefitSystem

p = CountryTaxBenefitSystem().parameters
p.gov.hmrc.income_tax.allowances.personal_allowance.amount("2026-01-01")   # 12570
```

Bracket/scale parameters index the scale node with `[i]` (no `.brackets` in the reform-dict
path, same convention as US):

```python
"gov.hmrc.income_tax.rates.uk[0].rate"   # basic-rate node in a reform dict
```

When browsing the tree object (not a reform path), a `ParameterScale` exposes `.brackets` as a
Python list of `ParameterScaleBracket`, each with `.rate(date)` / `.threshold(date)`.

## Devolved income tax — Scotland and Wales

Income tax rates live under `gov.hmrc.income_tax.rates`, whose children are
`dividends, property, savings, savings_starter_rate, scotland, uk`. Verify band counts and
values live (below is the verified 2026 structure, but treat the parameter tree as the source
of truth — do not hardcode rates into analysis):

- **Rest of UK (England & Northern Ireland):** `gov.hmrc.income_tax.rates.uk` is a
  `ParameterScale`. Verified 4 brackets / **3 distinct statutory rates** — basic 20%, higher
  40%, additional 45% (the 4th bracket is a technical top node repeating the additional rate).
- **Scotland:** `gov.hmrc.income_tax.rates.scotland.rates` is a *separate* `ParameterScale`
  with **6 bands** (verified 2026: starter, basic, intermediate, higher, advanced, top).
  Scotland's extra bands are why a UK income-tax analysis must branch on nation rather than
  assume the rest-of-UK schedule.
- **Wales:** there is **no separate Welsh income-tax rate parameter** (the only `WALES`
  parameter anywhere under `gov.hmrc` is in `business_rates`). The Welsh Rate of Income Tax is
  set at parity, so Wales is computed on the rest-of-UK `rates.uk` schedule. Model Wales via
  the `WALES` region, not a separate rate table.

```python
p.gov.hmrc.income_tax.rates.uk.brackets              # verified len 4 (3 distinct rates)
p.gov.hmrc.income_tax.rates.scotland.rates.brackets  # verified len 6
```

## Regions (ITL1)

`region` is a household-level enum. The `Region` enum
(`policyengine_uk/variables/household/demographic/geography.py`) is the 12 ITL1 regions plus
`UNKNOWN`:

```
NORTH_EAST, NORTH_WEST, YORKSHIRE, EAST_MIDLANDS, WEST_MIDLANDS, EAST_OF_ENGLAND,
LONDON, SOUTH_EAST, SOUTH_WEST, WALES, SCOTLAND, NORTHERN_IRELAND   (+ UNKNOWN)
```

Pass the enum member name as a string: `household={"region": "SCOTLAND"}`. `YORKSHIRE` is the
key for "Yorkshire and the Humber". UK constituency-level distributional analysis uses the
dataset's `constituency_code_oa` column via `compute_uk_constituency_impacts` /
`compute_uk_local_authority_impacts` — see the `policyengine` skill.

## Population data

The UK default dataset is **`populace_uk_2023`** (a Populace build), pinned by the certified
bundle in policyengine 4.21.0. It lives in a **private** Hugging Face repo, so population runs
require a `HUGGING_FACE_TOKEN` with access:

```bash
export HUGGING_FACE_TOKEN=hf_...   # required for UK population data; household calcs do NOT need it
```

Do not hardcode a raw `hf://` dataset URI — the certified default resolves by name through the
bundle. The pre-Populace UK datasets are superseded. See the `policyengine-data` skill for how
Populace UK is built (FRS + WAS imputation) and calibrated, and the `policyengine` skill for the
`ensure_datasets` / `Simulation` population flow, which is identical across countries.

## Country-model development notes (policyengine_uk directly)

Everything above uses the managed `pe.uk` surface. When you work *inside* the UK country model
(new variables, structural reforms, debugging formulas), you use `policyengine_uk` directly, and
the reform surface there is the **`Scenario`** object, verified importable:

```python
from policyengine_uk.model_api import Scenario   # -> policyengine_uk.utils.scenario.Scenario
```

`Scenario` is a Pydantic model with two fields — `parameter_changes` (`{path: {period: value}}`)
and `simulation_modifier` (a `Callable[[Simulation], None]`) — and scenarios compose with `+`
(parameter dicts merge, modifiers chain). The country-package `Microsimulation(reform=...)`
accepts **either a plain dict or a `Reform` class** (its verified signature is
`reform: Union[Dict, Type[Reform]]`) and internally calls `Scenario.from_reform(reform)`.
`Reform.from_dict(dict, country_id="uk")` also works and applies correctly for both flat and
date-ranged dicts — there is no UK-specific `from_dict` failure. (Note: the UK baseline bakes in
the July-2025 Universal Credit reform, so a bare `Microsimulation()` is already post-July-2025
UC law.)

Reform patterns for country-model work (from the analysis skill's
`MICROSIMULATION_REFORM_GUIDE.md`):

Parameter-change scenario, with period syntax `"year:START:COUNT"` or an ISO date:

```python
reform = Scenario(parameter_changes={
    "gov.hmrc.income_tax.rates.uk[0].rate": {"year:2026:10": 0.21},   # 21% for 2026..2035
})
```

Structural or multi-year edits go through a `simulation_modifier`. The safe
**parameter-freeze recipe** avoids corrupting shared parameter caches — clone, edit the clone,
process, copy the `values_list` back, then reset caches:

```python
def freeze_higher_threshold(sim):
    clone = sim.clone()
    clone.tax_benefit_system.reset_parameters()
    node = clone.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.uk[1].threshold
    current = node("2026-01-01")
    for year in range(2026, 2031):
        node.update(period=str(year), value=current, remove_after=True)
    clone.tax_benefit_system.process_parameters()
    sim.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.uk[1].threshold.values_list = (
        node.values_list
    )
    sim.tax_benefit_system.reset_parameter_caches()

reform = Scenario(simulation_modifier=freeze_higher_threshold)
```

Two gotchas from that recipe:

- **`remove_after=True`** on `.update(...)` is mandatory when you mean to change only one
  period — without it the edit propagates to every later year.
- **Parameter paths are indexed** in reform/scenario dicts: `...rates.uk[0].rate`, never
  `...rates.uk.rate`.

## UK legislation citation convention

Every UK parameter YAML carries `legislation.gov.uk` references with exact section links.
Distinguish primary legislation (Acts) from secondary legislation (Statutory Instruments, cited
by SI year/number):

- **Acts (primary):** Welfare Reform Act 2012 (Universal Credit), Social Security Contributions
  and Benefits Act 1992, Income Tax Act 2007, Income Tax (Earnings and Pensions) Act 2003.
- **Statutory Instruments (secondary):** cited as `SI YYYY/NNNN`, e.g. the Universal Credit
  Regulations 2013 (SI 2013/376). SI URLs use the `/uksi/` path; Acts use `/ukpga/`.

```yaml
metadata:
  reference:
    - title: Universal Credit Regulations 2013, Schedule 4
      href: https://www.legislation.gov.uk/uksi/2013/376/schedule/4
    - title: Income Tax Act 2007, Section 10
      href: https://www.legislation.gov.uk/ukpga/2007/3/section/10
```

Uprating usually tracks a statutory index (CPI/RPI or a benefit-specific order) rather than a
fixed value — cite the uprating order, not just the base Act, when a value changes annually.

## Related skills

- `policyengine` — the canonical `pe.*` interface, population flow, MicroSeries rules, and
  regional impacts. Read it first.
- `policyengine-data` — how Populace UK (FRS + WAS) is built and calibrated.
- `policyengine-model-development` — implementing new UK variables and parameters.
- `policyengine-us` — the US counterpart (and the source of the `tax_unit` habit to unlearn).
