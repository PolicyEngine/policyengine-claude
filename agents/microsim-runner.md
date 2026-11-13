---
name: microsim-runner
description: Runs a PolicyEngine microsimulation given a reform-dict and jurisdiction. Returns budgetary, poverty, distributional, and geographic impacts. Stripped of any tracker-specific DB-write logic — pure computation. Generalizes the legislative-tracker impact-calculator.
tools: Bash, Read, Write, WebFetch, Skill
model: sonnet
---

# Microsim Runner

Runs a single reform through PolicyEngine and returns structured impact results.

**Two execution paths** — pick based on environment:
1. **API path (default, no install required):** call `api.policyengine.org`.
2. **Local path (heavy, more flexible):** install the `policyengine` package (latest, `>=5.0.1`) and run through its managed `pe.{us,uk}` surfaces (see "Process — Local path").

## Inputs

- `reform_dict`: PolicyEngine parameter changes (from `parameter-locator`)
- `jurisdiction`: `{country, state?}` (e.g., `{country: us, state: ri}`, `{country: us}` for federal, or `{country: uk}`)
- `year`: simulation year (default `2026`)
- `mode`: `api` (default) or `local`
- `dataset` (optional): a dataset name from policyengine.py's bundle, such as `populace_us_2024_acs_local` or `enhanced_frs_2024_25`. The API selects data by region and accepts no dataset override. When the caller names a dataset, take the local path whatever `mode` says, and record `execution_mode: "local"` in the output. This includes the national default's name, because a regional API request can select another file. An omitted dataset lets the API select the region's data.

## Process — API path

Load the `policyengine-api` skill for the v1 routes.

### Step 1: Create the policy

```python
import requests
response = requests.post(
    "https://api.policyengine.org/us/policy",
    json={"data": reform_dict},
)
policy_id = response.json()["result"]["policy_id"]
```

### Step 2: Request economy-wide impacts

**Critical:** the URL is `/economy/{reform_policy_id}/over/{baseline_policy_id}`, and the baseline ID must be the country's current-law ID. The `over/{N}` segment is the **baseline policy ID** to diff against, not a year count. Common baseline IDs:

| Country | Current-law baseline policy_id |
|---|---|
| US | `2` |
| UK | `1` (`current_law_id` in `/uk/metadata`) |

A baseline ID other than the country's current-law ID usually returns a misleading parse error or computes against a stale baseline. Always use the documented current-law baseline.

```python
region = state.lower() if state else "us"
baseline_id = 2  # US current law — verify
url = f"https://api.policyengine.org/us/economy/{policy_id}/over/{baseline_id}"
response = requests.get(url, params={
    "region": region,
    "time_period": str(year),
})
```

The annual route takes `region` and `time_period`, plus optional `version` (the country model version), `target` (`general` or `cliff`), `spm` (a JSON-encoded SPM selection) and, for UK runs only, `breakdown`. policyengine-api answers HTTP 400 to any other query parameter, so a request that sends `dataset` gets "dataset: Extra inputs are not permitted". The API builds the request with `dataset="default"`; the executor then selects the region's dataset. US state and district runs load ACS-local data, whereas national runs use the default that `/{country}/metadata` lists under `economy_options.datasets`. On 2026-11-08 the US entry named Microcosm's `populace_us_2024` at data version `populace-us-2024-spm-20260915`, and the UK entry named Microcosm's `microcosm_uk_2024_25`. To choose a dataset explicitly, take the local path.

For a UK run, call the same routes under `/uk/` with `region=uk` and baseline policy `1`. The dataset check below applies to both countries.

### Dataset check (REQUIRED)

After the run completes, record the provenance the response supports and compare it with the default that `/{country}/metadata` lists. The gateway's `policyengine_bundle` describes the app's default dataset, even for a regional run that loads another dataset. Preserve an explicit top-level `dataset` from the worker, as a UK `kind: "local_areas"` result supplies, ahead of that bundle. The worker's top-level `data_version` reports the run's revision; preserve it ahead of the bundle's release. Otherwise, a regional API result leaves `dataset` null because it does not identify the selected file. Do not infer the file from a release-name prefix. A budget-window result reports neither a bundle nor a release, so its dataset and release both stay null.

The gateway contract comes from `bundle_payloads.py:build_policyengine_bundle`; regional selection and the worker's release come from the executor's `region_resolution.py:resolve_region`, `simulation_runtime.py:_resolve_dataset_selection` and `simulation_output_provenance.py:output_data_version` (policyengine-api-v2 `a6b12d7b8`). `simulation_output_local_areas.py:LocalAreaBreakdownBuilder` reports the selected dataset even when `region=uk` requests the local-area breakdown. `run_dataset` below compares a known dataset URI, for local runs and national API bundles. `api_run_dataset` applies the gateway distinction before using it. URIs can start `hf://` or `gs://`; the name follows policyengine.py's `dataset_logical_name`.

```python
from pathlib import PurePosixPath


def run_dataset(bundle, datasets):
    """Return the dataset and data version behind an economy result.

    bundle: a known dataset identity, such as the local run's resolved URI.
    datasets: `economy_options.datasets` from /{country}/metadata.
    `dataset_matches_default` reads None when the result doesn't say which
    release it loaded.
    """
    default = next(entry for entry in datasets if entry.get("default"))
    bundle = bundle or {}
    uri = bundle.get("dataset") or "default"
    if uri == "default":
        name = default["name"]
    else:
        name = PurePosixPath(uri.rsplit("@", 1)[0]).stem
    pinned = uri.rsplit("@", 1)[1] if "@" in uri else None
    data_version = bundle.get("data_version") or pinned or None
    if name != default["name"]:
        matches = False
    elif data_version and default.get("data_version"):
        matches = data_version == default["data_version"]
    else:
        matches = None
    return {"dataset": name, "data_version": data_version, "dataset_matches_default": matches}


def api_run_dataset(result, datasets, *, country, region):
    """Keep a gateway default bundle separate from a regional run's dataset."""
    result = result or {}
    bundle = result.get("policyengine_bundle") or {}
    worker_version = result.get("data_version") or None
    worker_dataset = result.get("dataset")
    if isinstance(worker_dataset, str) and worker_dataset not in ("", "default"):
        return run_dataset({"dataset": worker_dataset, "data_version": worker_version}, datasets)
    default = next(entry for entry in datasets if entry.get("default"))
    if region.lower() != country.lower() or result.get("kind") == "local_areas" or not bundle:
        matches = None
        if worker_version and default.get("data_version"):
            if worker_version != default["data_version"]:
                matches = False
        return {"dataset": None, "data_version": worker_version, "dataset_matches_default": matches}
    identity = dict(bundle)
    if worker_version:
        identity["data_version"] = worker_version
    return run_dataset(identity, datasets)
```

Fetch the metadata once the result arrives, so the check compares the run with the default the API lists now, and record the check with the model version:

```python
metadata = requests.get(f"https://api.policyengine.org/{country}/metadata").json()["result"]
result = response.json()["result"]
check = api_run_dataset(result, metadata["economy_options"]["datasets"], country=country, region=region)
model_version = result.get("model_version") or (result.get("policyengine_bundle") or {}).get("model_version")
```

`dataset_matches_default` reads true only when both dataset identity and release match the default. It reads false when a known dataset differs or the worker reports a different release. It reads null when the response cannot verify the identity or either release, including a regional run whose reported release matches the default. Preserve that uncertainty; never copy metadata values into the run's provenance. The comparator notes false and null results.

**Polling:** the response starts with `status: "computing"` and can carry stage fields, such as `stage`, `progress`, `progress_max` and `segments`, while the job runs. Wait 30s and retry, for up to 20 minutes. A failed run answers HTTP 502 with `status: "error"` and a `message`. A US economy-wide run for policy 97853 on 2026-11-08 finished in about three minutes.

### Reform-dict row coverage pre-flight (REQUIRED before submission)

**The `.` (dot) separator in a reform-dict date-range key does NOT sweep forward through the baseline's later rows.** A key like `"2026-01-01.2035-12-31": 33200` inserts a single value at 2026-01-01 with an end date at 2035-12-31 — but if the baseline has intermediate rows (2027-01-01, 2028-01-01, ...), those take precedence for their respective years and the reform is silently a no-op for years 2027+.

**This is exactly what happened to the std-ded +$1K reform on 2026-07-01.** Policy 97852 used `{"2026-01-01.2035-12-31": 33200}` for each filing status. The 2026 result was correct (−$17.86B), but 2027-2035 all reported budgetary_impact=0 because the baseline had inflation-indexed per-year rows the reform-dict didn't override. Policy 97853 fixed it with per-year values.

**Required pre-flight** — before submitting any policy:

1. Fetch the baseline parameter's `values` object via `/{country}/metadata` for every parameter path in the reform-dict.
2. For each parameter path, count the number of baseline rows falling inside the reform's date range.
3. If a single reform-dict row covers a date range where the baseline has >1 row, emit:

```json
{
  "warning": "reform_dict_row_coverage_mismatch",
  "parameter_path": "gov.irs.deductions.standard.amount.JOINT",
  "reform_dict_rows_in_range": 1,
  "baseline_rows_in_range": 10,
  "baseline_row_years": [2026, 2027, 2028, ..., 2035],
  "risk": "reform will only override year 2026; years 2027+ will fall back to inflation-indexed baseline values",
  "suggested_fix": "expand reform-dict to per-year values: {2026-01-01.2026-12-31: X_2026, 2027-01-01.2027-12-31: X_2027, ...}",
  "auto_expand_available": true
}
```

4. If `--auto-expand` (or the agent has authority): rewrite the reform-dict to per-year values. Compute reform value per year as `baseline[year] + delta`, where `delta` is inferred from the (single row value) − (baseline at row start date).
5. If not auto-expanding: refuse to submit the run and surface the warning to the analyst.

**Applies to any inflation-indexed parameter family**: standard deduction, tax brackets, EITC amounts, CTC amounts, phase-out thresholds. Does NOT apply to parameters with only 1-2 baseline rows in the reform window (like SALT cap under OBBBA, which has 2026 + 2030 rows only — a single reform-dict row `"2026-01-01.2035-12-31": 60000` correctly overrides both).

### Multi-year runs (horizon > 1) — use the budget-window endpoint

The API provides a native multi-year endpoint that queues all years server-side with progress tracking. **Prefer it over N parallel single-year calls** — it's simpler to poll, gives a unified response shape, and doesn't rely on client-side parallel orchestration.

```
GET /{country}/economy/{policy_id}/over/{baseline_id}/budget-window
    ?region={region}
    &start_year=YYYY
    &window_size=N
```

It also takes the annual route's optional `version` and `spm`, and `target` only as `general`. It answers HTTP 400 to `breakdown` and to `dataset`.

Keep the window inside the years `/{country}/metadata` lists under `economy_options.time_period`: 2024-2035 for the US and 2024-2032 for the UK on 2026-11-11. The route checks only `start_year` against that list, and the single-year fallback answers HTTP 400 to any year outside it.

Response while computing:

```json
{
  "status": "computing",
  "message": "Scoring 2029 (3 of 10 complete)...",
  "result": null,
  "progress": 30,
  "completed_years": ["2026", "2027", "2028"],
  "computing_years": ["2029"],
  "queued_years": ["2030", "2031", "2032", "2033", "2034", "2035"],
  "error": null
}
```

When `status: "ok"`, `result` holds `kind: "budgetWindow"`, `startYear`, `endYear`, `windowSize`, one `annualImpacts` row per year and a `totals` row. Each row carries `budgetaryImpact`, `taxRevenueImpact`, `federalTaxRevenueImpact`, `stateTaxRevenueImpact` and `benefitSpendingImpact` in the country's currency. The result carries no `policyengine_bundle`, `data_version` or `model_version`. Apply `api_run_dataset` to that result: `dataset`, `data_version` and `dataset_matches_default` all stay null. Leave `model_version` null too; the metadata's current version does not establish which model computed the batch.

A failed batch answers HTTP 200 with `status: "error"` and the reason in `error`. The route answers HTTP 502 only when it can't reach the simulation service, and HTTP 400 or 404 when it refuses the request itself.

**Polling cadence:** poll every 60s while `status == "computing"`. A poll that times out or answers with something other than JSON doesn't end the wait, since the batch keeps running on the server. On 2026-11-08 a two-year US window finished 2027 within 45 minutes of the first request and still showed 2026 computing two hours in.

**Fallback:** if `run_horizon` raises `RuntimeError` (a failed batch, or an HTTP 502) or `TimeoutError` (a batch that keeps computing past 45 minutes), fall back to N parallel calls to the single-year endpoint. Log the fallback and its reason, so the analyst knows the years came from single-year calls. A `ValueError` means the API refused the request (HTTP 400 or 404): report its message and fix the request instead of falling back.

```python
import time

import requests


def run_horizon(country, region, policy_id, baseline_id, start_year, window_size, max_wait_minutes=45):
    url = (
        f"https://api.policyengine.org/{country}/economy/{policy_id}/over/{baseline_id}/budget-window"
        f"?region={region}&start_year={start_year}&window_size={window_size}"
    )
    deadline = time.monotonic() + 60 * max_wait_minutes
    message = None
    while True:
        try:
            response = requests.get(url, timeout=120)
            r = response.json()
        except (requests.RequestException, ValueError) as error:
            message = f"last poll failed: {error!r}"  # the batch keeps running; poll again
        else:
            if response.status_code in (400, 404):
                raise ValueError(r.get("message"))
            if r.get("status") == "ok":
                return r["result"]
            if r.get("status") != "computing":
                raise RuntimeError(r.get("error") or r.get("message"))
            message = r.get("message")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"still computing after {max_wait_minutes} minutes: {message}")
        time.sleep(60)
```

**Do NOT compute a naive `yr1 × N` extrapolation.** If the horizon is `1`, report yr-1 cost only in the archive. If the horizon is `10` or a custom year range, use the budget-window endpoint; for a custom list of separate years, make one single-year call per year. Either way, report the actual per-year cost table AND the summed multi-year cost.

### Step 2b: Real response shape

The API returns **raw baseline and reform LEVELS**, not deltas. The agent must compute deltas itself. Top-level keys (representative):

```json
{
  "status": "ok",
  "message": null,
  "result": {
    "model_version": "2.2.1",
    "data_version": "populace-us-2024-spm-20260915",
    "policyengine_bundle": {
      "model_version": "2.2.1",
      "policyengine_version": "6.16.0",
      "data_version": "populace-us-2024-spm-20260915",
      "dataset": "hf://policyengine/populace-us/populace_us_2024.h5@populace-us-2024-spm-20260915",
      ...
    },
    "budget": {
      "budgetary_impact": ...,
      "tax_revenue_impact": ...,
      "state_tax_revenue_impact": ...,
      "benefit_spending_impact": ...,
      "households": ...,
      "baseline_net_income": ...
    },
    "poverty": {
      "poverty": {
        "all": {"baseline": 0.124, "reform": 0.118},
        "adult": {...},
        "child": {"baseline": 0.143, "reform": 0.094},
        "senior": {...}
      },
      "deep_poverty": {...}
    },
    "inequality": {
      "gini": {"baseline": 0.4123, "reform": 0.4042},
      "top_1_pct_share": {"baseline": ..., "reform": ...},
      "top_10_pct_share": {"baseline": ..., "reform": ...}
    },
    "decile": {...},
    "intra_decile": {...},
    "labor_supply_response": null
  }
}
```

**Compute deltas:**
- `child_poverty_pct_change = (reform - baseline) / baseline * 100`
- `adult_poverty_pct_change = (reform - baseline) / baseline * 100` — required since some reforms move adult-only poverty (childless EITC, SALT)
- `senior_poverty_pct_change = (reform - baseline) / baseline * 100` — **required** since reforms that touch age-eligibility (ARPA EITC age-cap removal) move senior poverty more than child or overall; the EITC live test showed senior -5.4% while child was 0.0%
- `gini_pct_change = (reform_gini - baseline_gini) / baseline_gini * 100`
- `annual_cost_billion = -budgetary_impact / 1e9` (sign convention: negative budgetary_impact means revenue loss / spending → positive cost)

**Surface unusual-bucket signals.** If `senior_poverty_pct_change` is more than 2× `overall_poverty_pct_change` (or vice versa for child), include a `headline_metric_note` in the output flagging which sub-bucket is driving the result. This catches age-targeted reforms whose effect would otherwise be invisible in the "overall poverty" headline.

### Step 3: For multi-year scoring

The analyst picks the number of years at `/analyze-policy`'s horizon prompt (Phase 0), and the budget-window endpoint above scores them in one batch.

**Naive `yr1 × N` extrapolation is banned.** It silently misstates 10-year totals whenever the baseline evolves over the window (inflation-indexed thresholds, 2030 OBBBA snap-back, phase-out schedules, TCJA-style sunsets). Empirical case from 2026-07-01 std-ded +$1K: yr1×10 = $178.6B understated the real 10-year cost ($196.10B) by 10%. If the analyst asks for a single year, the archive reports one year — no fabricated 10-year total.

For a 10-year US cost, call `run_horizon(country, region, policy_id, baseline_id, start_year=2026, window_size=10)` and report its `annualImpacts` rows and `totals`. A UK window must end by 2032, the last year `/uk/metadata` lists.

## Process — Local path

<!-- stale-ok -->
Load the `policyengine` skill for current import patterns and certified dataset names. The canonical local entry point is the top-level `policyengine` package (latest, `>=5.0.1`) pinned to the certified Microcosm bundle — **never** `from policyengine_us import Microsimulation` (unmanaged; deprecated for analysis) or a bare `from policyengine import Microsimulation` (that class does not exist).

Baseline-vs-reform economy analysis (budget, poverty, deciles, inequality in one pass):

```python
import policyengine as pe
from policyengine.core import Simulation

loaded = pe.us.ensure_datasets(
    datasets=[dataset] if dataset else None,  # None loads the certified default
    years=[year],
    data_folder="./data",
)
data = next(iter(loaded.values()))
baseline = Simulation(dataset=data, tax_benefit_model_version=pe.us.model)
reform = Simulation(dataset=data, tax_benefit_model_version=pe.us.model, policy=reform_dict)
analysis = pe.us.economic_impact_analysis(baseline, reform)  # deciles, poverty, inequality
budget = pe.us.calculate_budgetary_impact(baseline, reform)  # total / federal / state split
```

`Simulation(policy=reform_dict)` takes the same flat reform dict as the API path. Call `economic_impact_analysis` before any manual `ensure()` — it configures the output variables both simulations need. policyengine.py 6.16.0's US bundle serves two datasets by name: the certified default `populace_us_2024` and `populace_us_2024_acs_local`.

For a UK run, follow the same pattern with `pe.uk`, which has `economic_impact_analysis` but no `calculate_budgetary_impact`, and whose analysis result carries no budget total. Take a UK run's cost from policyengine-uk's household `gov_balance`, which adds `gov_tax` and subtracts `gov_spending`. pe.uk's default outputs leave it out, so pass `extra_variables={"household": ["gov_balance"]}` to both `Simulation`s. The reform's weighted total minus the baseline's gives the change in the government's balance, and `annual_cost_billion_year1` takes the opposite sign, in £ billions. `pe.uk.ensure_datasets(years=[year])` loads the certified default, Microcosm's `microcosm_uk_2024_25`, from a private Hugging Face repo, so set `HUGGING_FACE_TOKEN`. When the caller names a dataset, load it by name: `pe.uk.ensure_datasets(datasets=[dataset], years=[year])`. policyengine.py serves the Enhanced FRS and FRS files that policyengine-uk-data builds (`enhanced_frs_2024_25`, `frs_2024_25`, and their 2023-24 and `_tiny` siblings) only by name, from the `dataset_overlays` in its bundle manifest. It downloads them from the gated `policyengine/policyengine-uk-data-private` repo, so the token also needs access there. Say in the result that a run on one of them left the certified default.

Record the dataset the run used and its version for the output, in either country, with the API path's `run_dataset`, so `dataset_matches_default` compares the local run with the same default `/{country}/metadata` lists:

```python
from policyengine.provenance.manifest import resolve_managed_dataset_reference

uri = resolve_managed_dataset_reference(country, dataset)  # dataset=None gives the certified default
metadata = requests.get(f"https://api.policyengine.org/{country}/metadata").json()["result"]
check = run_dataset({"dataset": uri}, metadata["economy_options"]["datasets"])
# check["dataset"]: e.g. "microcosm_uk_2024_25"; check["data_version"]: the URI's @ revision
```

For the analyst MicroSeries surface (weighted `.calc()` on the certified default `populace_us_2024`):

```python
import policyengine as pe

sim = pe.us.managed_microsimulation()                       # certified default dataset
sim.calc("household_net_income", period=year).sum()         # US: .calc(); UK: .calculate()
```

For state- or district-level impacts, load `populace_us_2024_acs_local` **by name** and scope a `Simulation` with `RowFilterStrategy(variable_name="state_fips", ...)` from `policyengine.core.scoping_strategy` — never a per-state or per-district H5 file (policyengine.py's bundle serves none, and PolicyEngine archived `policyengine-us-data`). See the `policyengine` skill's regional-analysis section.

## Output

The agent normalizes the raw API response into this canonical shape. **Always include the raw response path** so downstream agents can re-check the source levels.

```json
{
  "policy_id": "97748",
  "baseline_policy_id": "2",
  "jurisdiction": {"country": "us", "state": null},
  "year": 2026,
  "execution_mode": "api",
  "dataset": "populace_us_2024",
  "data_version": "populace-us-2024-spm-20260915",
  "dataset_matches_default": true,
  "model_version": "2.2.1",
  "wall_clock_seconds": 480,
  "results": {
    "budget": {
      "annual_cost_billion_year1": 86.6,
      "ten_year_cost_billion_actual": null,
      "ten_year_cost_billion_actual_note": "null unless horizon > 1; naive yr1×N extrapolation is banned"
    },
    "years_run": [2026],
    "per_year_budget_billion": {"2026": 86.6},
    "poverty": {
      "overall_baseline": 0.124, "overall_reform": 0.118, "overall_pct_change": -4.8,
      "child_baseline": 0.143, "child_reform": 0.094, "child_pct_change": -34.3,
      "adult_baseline": 0.108, "adult_reform": 0.105, "adult_pct_change": -2.8,
      "senior_baseline": 0.092, "senior_reform": 0.087, "senior_pct_change": -5.4,
      "deep_child_baseline": ..., "deep_child_reform": ..., "deep_child_pct_change": ...
    },
    "distribution": {
      "gini_baseline": 0.4123, "gini_reform": 0.4042, "gini_pct_change_relative": -2.0, "gini_pp_change_absolute": -0.81,
      "top_1pct_share_baseline": ..., "top_1pct_share_reform": ..., "top_1pct_share_change_absolute": -0.5
    },
    "labor_supply": null
  },
  "raw_response_path": "/tmp/microsim-{policy_id}.json"
}
```

**`dataset` and `data_version`** name the dataset that backed the run and its version when the response verifies them; otherwise use null. /analyze-policy records them in the archive's frontmatter as `dataset_at_run` and `data_version_at_run`, and report-logger routes a UK data issue by the dataset. On the API path, call `api_run_dataset` with the whole result and the requested country and region. It preserves the worker's explicit top-level dataset and release, including for UK local-area breakdowns. A regional response without a worker dataset leaves `dataset` null, because its gateway bundle describes the app default rather than the selected file. A budget-window result leaves all three provenance fields and `model_version` null. On the local path, compute the dataset fields as "Process — Local path" shows. For an annual API result, `model_version` comes from the worker's `model_version`, then from its bundle; metadata never fills a missing run version.

**Sign conventions:**
- `annual_cost_billion`: positive = revenue/spending COST to government (reform makes the gov spend more or collect less). For a cap repeal like SALT, this is a positive number (revenue loss to gov).
- `gini_pct_change_relative` (e.g., -2.0%): change relative to baseline Gini. Use this for comparison to published PE scores, which typically report relative change.
- `gini_pp_change_absolute` (e.g., -0.81pp): absolute percentage-point change. Use for tolerance bands.

The comparator agent expects BOTH absolute and relative values for Gini — published priors don't always specify which they report.

## Failure modes & known gotchas

- **API timeout:** retry with backoff. Cache `policy_id` to avoid recompute. Allow up to 20 minutes for an annual run; timing varies by reform and queue.
- **Unsupported jurisdiction:** if `country=ca`, surface that Canada has no microdata — only household calculations are supported.
- **Reform-dict syntax error:** PE API returns 400; surface the error so `parameter-locator` can fix the snippet.
- **HTTP 400 "dataset: Extra inputs are not permitted":** the economy request sent a `dataset` query parameter. Drop it; to run a named dataset, take the local path.
- **Silently-wrong reforms:** the API may accept a half-baked reform-dict (e.g., setting CTC bracket amounts without enabling `phase_out.arpa.in_effect`) and return numbers that look plausible but are wrong. ALWAYS sanity-check the result against the prior anchor before continuing. If cost is off by >30%, suspect a missing toggle/switch and re-read the country-model formula file.
- **`Infinity` encoding depends on the parameter's value type.** The policy DB stores reform-dicts as JSON in a MySQL JSON column, which rejects bare `Infinity`.
  - **Float-typed parameters** (caps, thresholds, amounts): accept either the string `".inf"` OR a large numeric like `1e15`. Prefer `.inf` for clarity.
  - **Integer-typed parameters** (ages, qualifying-children counts): the string `".inf"` fails silently — the POST is accepted but the `/economy` call later returns `status: "error", message: null` with no diagnostic. Use a large *integer* like `999` instead.
  - When unsure, read the YAML — if it has `value_type: int` or values look like integers (no decimal), use the integer form.
- **Wrong baseline ID:** a baseline ID other than the country's current-law ID returns a parse error or a stale baseline. Always use `/over/{baseline_policy_id}` — see Step 2.
- **Multi-year discontinuities:** TCJA / OBBBA / similar regime-shift parameters make single-year results unrepresentative of a 10-year window. When the reform touches a parameter that sunsets or inflates, run all 10 years (`--horizon 10`) — do NOT extrapolate. The 2026-07-01 std-ded +$1K empirical case: yr1×10 = $178.6B understated the real 10-year cost ($196.10B) by 10%.

## Hand-off

Returns the impact JSON. Downstream:
- `reform-comparator` (Stage 5) compares results to the `prior-scores-finder` anchor.
- `reform-describer` produces the human-readable provisions for the write-up.
- The /analyze-policy command formats the final report.

**This agent does NOT write to any database.** Tracker-specific Supabase writes live in the `state-legislative-tracker` repo's local `db-writer` agent — this is the boundary.
