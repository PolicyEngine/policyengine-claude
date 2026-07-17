---
name: policyengine-canada
description: |
  How to compute Canadian household tax/benefit outcomes with PolicyEngine, and the hard limits.
  Load when a task involves Canadian taxes or benefits (CCB, GST/HST credit, CWB, OAS, provincial
  tax) at the household level. Key facts: pe.ca does NOT exist — Canada is not in the policyengine
  wrapper; use the policyengine_canada package directly via Simulation(situation=...); there is no
  representative microdata (only a synthetic template), so population microsimulation, national
  costs, and poverty rates are NOT possible — household-level only.
  Triggers: Canada, Canadian, CCB, Canada Child Benefit, GST credit, HST, GST/HST credit, CWB,
  Canada Workers Benefit, OAS, GIS, Ontario, Quebec, province, provincial tax, AFNI, full custody,
  policyengine canada, policyengine_canada.
  NOT for: US or UK analysis (use policyengine-us / policyengine-uk); anything population-scale
  for Canada (not supported).
metadata:
  category: domain
---

# PolicyEngine Canada domain knowledge

Canada is the exception to the standard PolicyEngine stack. Read this before writing any Canadian
analysis — the entry points and the limits are different from the US/UK.

Verified against `policyengine-canada` 0.99.0 (2026-07), installed standalone. Do not hardcode
benefit amounts; look them up live (below), because provincial and federal parameters re-index
every year.

## Two hard constraints

**1. `pe.ca` does not exist.** The `policyengine` wrapper ships US and UK only; there is no `pe.ca`.
Use the `policyengine_canada` package directly.

<!-- verify -->
```python
import policyengine as pe
assert not hasattr(pe, "ca")   # Canada is not in the policyengine wrapper
```

**2. Canada is household-only — there is no representative microdata.** The package ships a small
synthetic template, not a survey-weighted population sample. So you **cannot** run population
microsimulation, and you **cannot** produce national program costs, revenue estimates, caseloads,
or poverty rates for Canada. If asked "what would this cost nationally" or "how many families
benefit," say that population estimates are not available for Canada and offer a household example.
What you *can* do: compute taxes/benefits for a specific family, compare baseline vs. reform for
that family, sweep it across an income range, and compare provinces.

## One household calculation

Install the package on its own (it is not in the shared analysis venv), then build a `situation`
and use `policyengine_canada.Simulation`. Values below verified against 0.99.0.

```bash
uv pip install policyengine-canada
```

```python
from policyengine_canada import Simulation

sim = Simulation(situation={
    "people": {
        "parent1": {"age": {"2026": 35}, "employment_income": {"2026": 45_000}},
        "parent2": {"age": {"2026": 33}, "employment_income": {"2026": 20_000}},
        # full_custody defaults to False, which HALVES the CCB (see gotcha below):
        "child1": {"age": {"2026": 4}, "full_custody": {"2026": True}},
        "child2": {"age": {"2026": 9}, "full_custody": {"2026": True}},
    },
    "households": {"household": {
        "members": ["parent1", "parent2", "child1", "child2"],
        "province_code": {"2026": "ONT"},   # note: "ONT" for Ontario, "QC" for Quebec
    }},
})
assert round(float(sim.calculate("child_benefit", 2026)[0]), 2) == 11_030.75   # federal CCB
assert float(sim.calculate("adjusted_family_net_income", 2026)[0]) == 65_000    # AFNI
```

Entities are just **`household`** and **`person`** (far simpler than the US six). `province_code`
is an enum on the household: `AB, BC, MB, NB, NL, NS, NT, NU, ONT, PE, QC, SK, YT` — Ontario is
`"ONT"`, not `"ON"`.

Key variable names (they are not the acronyms): federal Canada Child Benefit = **`child_benefit`**,
GST/HST credit = **`gst_credit`**, Canada Workers Benefit = **`canada_workers_benefit`**, Old Age
Security = **`oas_net`**. Browse the full list with
`from policyengine_canada import CountryTaxBenefitSystem; CountryTaxBenefitSystem().variables`.

### Gotcha: `full_custody` defaults to False and halves the CCB

Each child's `full_custody` defaults to **False**, which the model treats as 50/50 shared custody
and **halves** that child's benefit base. A sole-custody two-parent family gets the full amount only
if you set `full_custody: {"YEAR": True}` on each child — otherwise every CCB (and child-benefit-
derived) figure comes out at half. Verified: the family above yields **$3,658.25** with the default
and **$11,030.75** with `full_custody=True`.

### Gotcha: prefer the specific benefit variable over `household_net_income`

In 0.99.0, computing `household_net_income` (or `gst_credit`, which depends on it) can raise a
`ClimateActionIncentiveCategory` enum error via the climate-incentive chain. Calculate the specific
variable you need (`child_benefit`, `adjusted_family_net_income`, `income_tax`) rather than the full
net-income roll-up.

## Look parameters up live — never hardcode

Resolve the parameter tree at an instant (as a formula does) and read the value. The CCB maximum is
an age-scaled parameter under `gov.cra.benefits.ccb`:

```python
from policyengine_canada import CountryTaxBenefitSystem
p = CountryTaxBenefitSystem().parameters("2026-01-01")
p.gov.cra.benefits.ccb.base.calc(4)   # -> 7997  : CCB max for a child under 6
p.gov.cra.benefits.ccb.base.calc(9)   # -> 6748  : CCB max for a child 6-17
p.gov.cra.benefits.ccb.base.calc(20)  # -> 0     : none over 17
```

The `reduction` sub-tree (`ccb.reduction.one_child`, `.two_children`, …) holds the AFNI phase-out
schedule. Provincial parameters live under `gov.provinces.<code>`. Read the value at your
simulation year rather than quoting a remembered figure — thresholds and maximums re-index yearly.

## Two facts that change the answer

- **AFNI is combined, and the benefit year lags the tax year.** `adjusted_family_net_income` is
  *both* partners' net income summed, not one person's. In the real program the July–June benefit
  year is based on the *prior* tax year's AFNI (e.g. July 2025–June 2026 payments use 2024 income);
  the model computes benefits from the same-year situation, so pick the income year to match the
  AFNI year you intend to represent.
- **Quebec is a different system.** Quebec runs its own pension plan (QPP, not CPP), parental
  insurance (QPIP), sales tax (QST), and a distinct set of provincial credits and a family
  allowance. Set `province_code` to `"QC"` and do not assume rest-of-Canada provincial rules carry
  over; the federal `child_benefit` still applies, but Quebec layers its own programs on top.
