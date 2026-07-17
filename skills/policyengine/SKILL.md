---
name: policyengine
description: |
  ALWAYS load this skill before writing any Python that computes taxes, benefits, or policy
  impacts with PolicyEngine — household calculations, microsimulation, reform scoring, poverty
  or distributional analysis, state/district/constituency breakdowns.
  Triggers: policyengine, microsimulation, calculate_household, reform impact, budgetary impact,
  cost of a policy, revenue estimate, poverty rate, child poverty, winners and losers, decile,
  Gini, inequality, CTC, EITC, SNAP, income tax, universal credit, state-level analysis,
  congressional district, constituency, Populace dataset, MicroSeries, ensure_datasets,
  economic_impact_analysis, managed_microsimulation.
  NOT for: implementing new variables/parameters inside country models (use
  policyengine-model-development) or calling the REST API from JS (use policyengine-api).
metadata:
  category: analysis
---

# PolicyEngine Python analysis

The `policyengine` package (repo: PolicyEngine/policyengine.py) is the canonical Python
interface for both single-household calculations and population microsimulation. It pins a
certified model + data bundle, so results are reproducible and the data provenance is known.

Verified against policyengine 4.21.0 (2026-07). Re-verify the bundle when precision matters
(see "Checking what you're running" below).

## Setup

Country models are extras — bare `policyengine` installs neither:

```bash
uv pip install "policyengine[us]"   # US model + certified US data bundle
uv pip install "policyengine[uk]"   # UK model (population data needs HUGGING_FACE_TOKEN)
uv pip install "policyengine"       # both countries
```

## Household calculations (fast, ~2 GB RAM)

`calculate_household` answers "what does this specific household get/pay?" — no dataset
download, runs in seconds.

<!-- verify -->
```python
import policyengine as pe

result = pe.us.calculate_household(
    people=[{"age": 40, "employment_income": 50_000}, {"age": 8}],
    tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
    household={"state_code": "CA"},
    year=2026,
    extra_variables=["income_tax"],
)
assert result.tax_unit.ctc == 2_200          # OBBBA CTC, 2026
assert round(result.household.household_net_income) == 46_358
print(result.spm_unit.snap, result.tax_unit.eitc, result.tax_unit.income_tax)
```

Result access is **dot-attribute on singular entities** — `result.tax_unit.ctc`, never
`result.tax_unit[0]["ctc"]`. Only `result.person` is a list (`result.person[0].age`). Entities:
`person[i]`, `marital_unit`, `family`, `spm_unit`, `tax_unit`, `household` (US);
`person[i]`, `benunit`, `household` (UK).

**Each entity exposes a limited default column set** — accessing anything else raises
`AttributeError` listing what's available and telling you the fix: pass
`extra_variables=["variable_name"]` to materialize it (as with `income_tax` above; the
default person columns don't include it).

Reforms are a **flat dict** of `{parameter_path: value}`:

<!-- verify -->
```python
import policyengine as pe

baseline = pe.us.calculate_household(
    people=[{"age": 40, "employment_income": 50_000}, {"age": 8}],
    tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
    household={"state_code": "CA"},
    year=2026,
)
reformed = pe.us.calculate_household(
    people=[{"age": 40, "employment_income": 50_000}, {"age": 8}],
    tax_unit={"filing_status": "HEAD_OF_HOUSEHOLD"},
    household={"state_code": "CA"},
    year=2026,
    reform={"gov.irs.credits.ctc.amount.base[0].amount": 3_000},
)
assert reformed.tax_unit.ctc == 3_000
assert reformed.household.household_net_income - baseline.household.household_net_income == 800
```

UK works the same way:

```python
uk = pe.uk.calculate_household(
    people=[{"age": 35, "employment_income": 50_000}],
    year=2026,
)
uk.person[0].income_tax
uk.household.hbai_household_net_income
```

To sweep an input (e.g. earnings 0→200k for an MTR curve), pass `axes`. Every variable on the
result then comes back as a **list of values across the sweep** instead of a scalar:

<!-- verify -->
```python
import policyengine as pe

result = pe.us.calculate_household(
    people=[{"age": 40}],
    tax_unit={"filing_status": "SINGLE"},
    household={"state_code": "TX"},
    year=2026,
    axes=[[{"name": "employment_income", "min": 0, "max": 200_000, "count": 401}]],
)
earnings = result.person[0].employment_income      # [0.0, 500.0, ..., 200000.0]
net = result.household.household_net_income        # list of 401 values
assert len(earnings) == len(net) == 401
assert earnings[1] == 500.0
```

## Population analysis (heavy: tens of GB RAM, minutes per simulation)

The canonical population flow builds year-specific datasets from the certified bundle, then
runs baseline and reform `Simulation`s:

<!-- verify: slow -->
```python
import policyengine as pe
from policyengine.core import Simulation

datasets = pe.us.ensure_datasets(years=[2026], data_folder="./data")
dataset = next(iter(datasets.values()))

baseline = Simulation(dataset=dataset, tax_benefit_model_version=pe.us.model)
reform = Simulation(
    dataset=dataset,
    tax_benefit_model_version=pe.us.model,
    policy={"gov.irs.credits.ctc.amount.base[0].amount": 3_000},
)

analysis = pe.us.economic_impact_analysis(baseline, reform)
budget = pe.us.calculate_budgetary_impact(baseline, reform)
print(f"Total budgetary impact: ${budget.total / 1e9:,.1f}B "
      f"(federal ${budget.federal / 1e9:,.1f}B, state ${budget.state / 1e9:,.1f}B)")
for d in analysis.decile_impacts.outputs:
    print(d.decile, d.absolute_change, d.relative_change)
```

Key facts:

- **Call `economic_impact_analysis` before (or instead of) manual `ensure()`.** It configures
  conditionally-materialized output variables (e.g. `federal_benefit_cost`) and ensures both
  simulations. If you call `Simulation.ensure()` yourself and then
  `calculate_budgetary_impact`, it fails with "variable ... is not present in simulation
  output data" — the fix is `pe.us.economic_impact_analysis(baseline, reform)` first, or
  `configure_budgetary_impact_variables` on each simulation before `ensure()`.
- `economic_impact_analysis` returns a `PolicyReformAnalysis`: `decile_impacts`,
  `program_statistics`, `baseline_poverty` / `reform_poverty` (by measure and demographic
  group), `baseline_inequality` / `reform_inequality` (Gini, top shares). Each
  `OutputCollection` exposes `.outputs` (typed) and `.dataframe`.
- `calculate_budgetary_impact` partitions into `total` / `federal` / `state` /
  `unattributed`. Sign convention: **positive = government better off**. `total` is
  Δhousehold_tax − Δhousehold_benefits plus shared-funding health-program cost
  (Medicaid/CHIP/MSP), so it captures cascading interactions — never score a reform by
  summing the directly-modified program variable alone.
- **Memory/time**: a full US population simulation is tens of GB of RAM and several minutes;
  a baseline+reform pair with full outputs took ~15 minutes on a 128 GB machine. Run ONE
  heavy simulation pipeline at a time. Household calculations are the cheap path — prefer
  them whenever the question is about specific households.
- `Simulation(policy={...})` takes the same flat reform dict as `calculate_household`.

### Aggregates and filters

For a single number (program spending, revenue, caseload), use `Aggregate` /
`ChangeAggregate` instead of the full analysis bundle:

```python
from policyengine.outputs import Aggregate, AggregateType

ca_snap = Aggregate(
    simulation=baseline,
    variable="snap",
    aggregate_type=AggregateType.SUM,
    filter_variable="state_code",
    filter_variable_eq="CA",
)
ca_snap.run()
ca_snap.result
```

### The managed country-package surface (MicroSeries)

`managed_microsimulation` returns a country-package `Microsimulation` pinned to the certified
bundle — useful when you want the familiar `.calc()` / MicroSeries analyst surface:

```python
import policyengine as pe

sim = pe.us.managed_microsimulation()               # certified default dataset
income = sim.calc("household_net_income", period=2026, map_to="person")
income.mean()          # weighted mean
income.median()        # weighted median
income.gini()          # weighted Gini
(income < 30_000).mean()   # weighted share
```

MicroSeries (from `microdf-python`, still a live dependency of policyengine-us and core)
embeds survey weights in every operation. Discipline:

- **Never** strip weights: no `np.array(series)`, `.values`, `.to_numpy()`, `.astype(...)`
  mid-analysis, and never fetch `household_weight`/`person_weight` yourself — `map_to=`
  handles entity projection and weighting.
- Weighted stats are the methods themselves: `.sum()`, `.mean()`, `.median()`,
  `.quantile(q)`, `.gini()`, `.top_x_pct_share(x)`. (`decile_values()` / `percentile()` do
  not exist.)
- Don't subtract boolean MicroSeries (numpy ≥2.4 raises `TypeError`): compute
  `.mean()` rates first, then subtract floats.
- US `Microsimulation` uses `.calc(...)`; UK uses `.calculate(...)`.
- Arbitrary dataset URIs require `allow_unmanaged=True` — if you reach for that, you are
  leaving the certified bundle and should say so in your results.

Direct `from policyengine_us import Microsimulation` (unmanaged, whatever data it defaults
to) is for country-model development inside the model repos — not for analysis results you
plan to report.

## Datasets

Certified defaults resolve automatically — **do not pass raw `hf://` URIs**:

| Name | What | Notes |
|---|---|---|
| `populace_us_2024` | US default (Populace, ~57k households calibrated to ~30k+ admin targets) | public |
| `populace_us_2024_acs_local` | US local-area build (~1.6M households, ACS multispine, PUMA-assigned CD-119/county/state) | load **by name** for state/district work; never selected implicitly |
| `populace_uk_2023` | UK default (Populace) | private HF repo — set `HUGGING_FACE_TOKEN` |

The pre-2026 datasets are gone:
<!-- stale-ok -->
`enhanced_cps_2024` and `enhanced_frs_2023_24` are superseded by Populace, and the per-area
<!-- stale-ok -->
files (`hf://policyengine/policyengine-us-data/states/*.h5`, `districts/*.h5`) no longer
exist — policyengine-us-data is archived. **Local-area analysis = filter one national dataset
by its geography columns**, never a per-area file. See the policyengine-data skill for how
Populace is built and calibrated.

## Regional analysis

States (works on the certified national dataset — it carries `state_fips` / `state_code`):

```python
# Option A: filter any aggregate (see Aggregate example above).
# Option B: scope a Simulation to one state's rows.
from policyengine.core import Simulation
from policyengine.core.scoping_strategy import RowFilterStrategy

datasets = pe.us.ensure_datasets(datasets=["populace_us_2024_acs_local"], years=[2024])
dataset = datasets["populace_us_2024_acs_local_2024"]
ca = Simulation(
    dataset=dataset,
    tax_benefit_model_version=pe.us.model,
    scoping_strategy=RowFilterStrategy(variable_name="state_fips", variable_value=6),
)
# Registry of ready-made state regions with scoping strategies:
states = pe.us.model.region_registry.get_by_type("state")
```

Congressional districts (`district_geoid` = state FIPS × 100 + district number; at-large = 00):

```python
from policyengine.outputs import compute_us_congressional_district_impacts

impacts = compute_us_congressional_district_impacts(
    baseline_simulation=baseline, reform_simulation=reform,
)
for row in impacts.district_results:
    print(row["district_geoid"], row["avg_change"], row["winner_percentage"])
```

UK equivalents: `compute_uk_constituency_impacts` (groups by the dataset's
`constituency_code_oa` column) and `compute_uk_local_authority_impacts`.

For state and CD breakdowns, prefer `populace_us_2024_acs_local` (calibrated to state admin
totals and state/CD population); read its release-gate summary for reviewed limitations.

## Reform dictionaries and parameter paths

Three reform formats exist — match the surface you're using:

1. `calculate_household(reform={...})` and `Simulation(policy={...})`: **flat**
   `{"gov.path.to.param": value}`.
2. Country-package `Microsimulation(reform=...)` (managed or direct): date-ranged dicts —
   `{"gov.path": {"2026-01-01.2100-12-31": value}}` — passed directly, or wrapped with
   `Reform.from_dict(..., "policyengine_us")`. The UK package also accepts plain dicts and
   converts internally (its reform surface is `Scenario` — see the policyengine-uk skill).

Bracket/scale parameters index the scale node directly — there is **no `.brackets`** in the
path:

```python
"gov.irs.credits.ctc.amount.base[0].amount"        # correct
"gov.irs.credits.ctc.amount.base.brackets[0].amount"  # wrong — no such path
```

Discover and verify paths against the live parameter tree before using them:

<!-- verify -->
```python
from policyengine_us import CountryTaxBenefitSystem

p = CountryTaxBenefitSystem().parameters
assert p.gov.irs.credits.ctc.amount.base[0].amount("2026-01-01") == 2_200
# Browse: p.gov.irs.credits.ctc.amount.children keys, or grep the YAML tree in
# policyengine-us/policyengine_us/parameters/gov/.
```

Paths change names (e.g. `ctc.amount.base`, not `base_amount`) — a `ValueError` listing real
children means you guessed; browse instead. Always check the **baseline value in your
simulation year** before interpreting a reform (post-OBBBA law: CTC $2,200 in 2026, SALT cap
$40,400 JOINT in 2026, etc. — don't trust pre-2026 summaries).

## Cost methodology

- Population cost of a reform = change in government budget, from
  `calculate_budgetary_impact` (preferred: handles tax/benefit/health-program composition
  and the federal/state split).
- On the MicroSeries surface, Δ`household_net_income` total ≈ −Δbudget but **includes state
  tax interactions** (many states inherit federal `taxable_income`); federal-only revenue is
  Δ`income_tax`.
- Sanity-check against a back-of-envelope (rate × base × takeup) and, when one exists, a
  published score (JCT/CBO/TPC — see the policyengine-prior-scores skill) before reporting.

## Checking what you're running

<!-- verify -->
```python
import importlib.metadata as md
import json
from pathlib import Path

versions = {p: md.version(p) for p in ("policyengine", "policyengine-us")}
manifest = json.loads(
    Path(md.distribution("policyengine").locate_file("policyengine/data/bundle/manifest.json"))
    .read_text()
)
us = manifest["data_releases"]["us"]
print(versions, us["default_dataset"], us["build_id"])
assert us["default_dataset"].startswith("populace_us")
```

When the user asks for "the latest," verify the released version on PyPI
(`https://pypi.org/pypi/policyengine/json`) and install that exact version — never infer
"latest" from a lockfile or a stale local checkout.
