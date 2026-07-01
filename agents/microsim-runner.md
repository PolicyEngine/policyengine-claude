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
2. **Local path (heavy, more flexible):** install the `policyengine` package and run via `Microsimulation`.

## Inputs

- `reform_dict`: PolicyEngine parameter changes (from `parameter-locator`)
- `jurisdiction`: `{country, state?}` (e.g., `{country: us, state: ri}` or `{country: us}` for federal)
- `year`: simulation year (default `2026`)
- `mode`: `api` (default) or `local`

## Process — API path

Load the `policyengine-python-client` skill for current endpoint shapes.

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

**Critical:** the URL is `/economy/{reform_policy_id}/over/{baseline_policy_id}`, NOT `/over/1`. The `over/{N}` segment is the **baseline policy ID** to diff against, not a year count. Common baseline IDs:

| Country | Current-law baseline policy_id |
|---|---|
| US | `2` |
| UK | (verify per-environment; typically `1` or `2`) |

Calling `/over/1` against an arbitrary reform usually returns a misleading parse error or computes against a stale baseline. Always use the documented current-law baseline.

```python
region = state.lower() if state else "us"
baseline_id = 2  # US current law — verify
url = f"https://api.policyengine.org/us/economy/{policy_id}/over/{baseline_id}"
response = requests.get(url, params={
    "region": region,
    "time_period": str(year),
    "dataset": "enhanced_cps",  # advertised name; backed by populace-us-2024 as of PE-US 1.729.0
})
```

**Dataset naming — IMPORTANT:**

The deployed API advertises only two dataset names at `/us/metadata/economy_options/datasets`:

| Advertised name | Default? | Backing data (as of PE-US 1.729.0) |
|---|---|---|
| `cps` | **yes** | Current Population Survey raw |
| `enhanced_cps` | no | Enhanced CPS, now backed by populace-us-2024 |

**Use `enhanced_cps`** for all production microsims — it's the calibration-grade dataset that matches PE's published research (the raw `cps` default is much smaller and lacks the calibrations). The data backing `enhanced_cps` has evolved over time (Enhanced CPS → populace-us-2024); always read the actual `data_version` returned in the response to confirm what backed the run.

**Do NOT use `enhanced_cps_2024` or year-suffixed variants** — these names are NOT advertised, so the API silently falls back to its default (`cps`), producing results that look plausible but use raw CPS rather than enhanced.

### Dataset honored validation (REQUIRED)

After the run completes, the runner MUST validate the dataset that actually backed the simulation:

```python
result = response.json()
data_version = result["result"]["data_version"]
model_version = result["result"]["model_version"]

# Surface to the comparator's input so the analyst sees what backed the run
return {
    "result": result["result"],
    "data_version": data_version,
    "model_version": model_version,
    "dataset_requested": "enhanced_cps",
    "dataset_backing": "populace-us-2024" if "populace" in data_version else ("enhanced_cps" if "enhanced" in data_version else "cps-raw"),
    "dataset_honored": "populace" in data_version or "enhanced" in data_version,
}
```

If `dataset_honored: false` (the API returned raw CPS when we asked for enhanced), the comparator should flag the run as "raw-CPS-backed; not publication-grade" and either re-run with corrected request or downgrade the verdict.

**Polling:** the response often starts with `status: "computing"` (or similar). Wait 30s and retry. Real-world wall-clock for a US economy-wide reform is **5-10 minutes**, not 1-3 minutes as some older docs suggest. Retry up to ~20 minutes before giving up.

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
    &dataset={dataset}
```

Response while computing:

```json
{
  "status": "computing",
  "progress": 0.3,
  "message": "Queued 2029 (3 of 10 complete)...",
  "completed_years": ["2026", "2027", "2028"],
  "computing_years": ["2029"],
  "queued_years": ["2030", "2031", "2032", "2033", "2034", "2035"],
  "result": null,
  "error": null
}
```

When `status: "ok"`, `result` contains per-year budgetary data plus (typically) the summed multi-year total. Read `data_version` and `model_version` from `result` as usual.

**Polling cadence:** the endpoint returns quickly; poll every 30-60s while `status == "computing"`. Wall-clock for a full 10-year US run is typically 15-25 min (depends on API queue).

**Fallback:** if the budget-window endpoint returns an error (older PE-{country} releases without it), fall back to N parallel calls to the single-year endpoint. Log the fallback so the analyst knows the runner degraded gracefully.

```python
def run_horizon(country, policy_id, baseline_id, start_year, window_size):
    url = (
        f"https://api.policyengine.org/{country}/economy/{policy_id}/over/{baseline_id}/budget-window"
        f"?region={country}&start_year={start_year}&window_size={window_size}&dataset=enhanced_cps"
    )
    while True:
        r = requests.get(url).json()
        if r["status"] != "computing":
            return r["result"]
        time.sleep(60)
```

**Do NOT compute a naive `yr1 × N` extrapolation.** If the horizon is `1`, report yr-1 cost only in the archive. If the horizon is `10` (or a custom multi-year list), use the budget-window endpoint and report the actual per-year cost table AND the summed multi-year cost.

### Step 2b: Real response shape

The API returns **raw baseline and reform LEVELS**, not deltas. The agent must compute deltas itself. Top-level keys (representative):

```json
{
  "status": "ok",
  "result": {
    "budget": {
      "budgetary_impact": ...,
      "tax_revenue_impact": ...,
      "state_tax_revenue_impact": ...,
      "benefit_spending_impact": ...,
      "households": ...,
      "baseline_net_income": ...,
      "reform_net_income": ...
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

There is **no native 10-year endpoint** as of 2026-07. The pipeline handles multi-year scoring through the horizon prompt in `/analyze-policy` (see Phase 0) and the multi-year runner block below (parallel per-year API calls).

**Naive `yr1 × N` extrapolation is banned.** It silently misstates 10-year totals whenever the baseline evolves over the window (inflation-indexed thresholds, 2030 OBBBA snap-back, phase-out schedules, TCJA-style sunsets). Empirical case from 2026-07-01 std-ded +$1K: yr1×10 = $178.6B understated the real 10-year cost ($196.10B) by 10%. If the analyst asks for a single year, the archive reports one year — no fabricated 10-year total.

If a 10-year cost is required, run all 10 years via `run_horizon(policy_id, baseline_id, years=range(2026, 2036))` and sum the actual per-year budgetary impacts.

## Process — Local path

Load the `policyengine-microsimulation` skill for current import patterns.

```python
from policyengine import Microsimulation
sim_baseline = Microsimulation()
sim_reform = Microsimulation(reform=reform_dict)
cost = (sim_baseline.calculate("household_net_income", year).sum() -
        sim_reform.calculate("household_net_income", year).sum())
# ...
```

For state-only impacts, subset by `state_code_str`. For district-level, load the `policyengine-district-analysis` skill.

## Output

The agent normalizes the raw API response into this canonical shape. **Always include the raw response path** so downstream agents can re-check the source levels.

```json
{
  "policy_id": "97748",
  "baseline_policy_id": "2",
  "jurisdiction": {"country": "us", "state": null},
  "year": 2026,
  "execution_mode": "api",
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

**Sign conventions:**
- `annual_cost_billion`: positive = revenue/spending COST to government (reform makes the gov spend more or collect less). For a cap repeal like SALT, this is a positive number (revenue loss to gov).
- `gini_pct_change_relative` (e.g., -2.0%): change relative to baseline Gini. Use this for comparison to published PE scores, which typically report relative change.
- `gini_pp_change_absolute` (e.g., -0.81pp): absolute percentage-point change. Use for tolerance bands.

The comparator agent expects BOTH absolute and relative values for Gini — published priors don't always specify which they report.

## Failure modes & known gotchas

- **API timeout:** retry with backoff. Cache `policy_id` to avoid recompute. Real wall-clock is 5-10 minutes for full US economy; don't time out under 20 minutes.
- **Unsupported jurisdiction:** if `country=ca`, surface that Canada has no microdata — only household calculations are supported.
- **Reform-dict syntax error:** PE API returns 400; surface the error so `parameter-locator` can fix the snippet.
- **Silently-wrong reforms:** the API may accept a half-baked reform-dict (e.g., setting CTC bracket amounts without enabling `phase_out.arpa.in_effect`) and return numbers that look plausible but are wrong. ALWAYS sanity-check the result against the prior anchor before continuing. If cost is off by >30%, suspect a missing toggle/switch and re-read the country-model formula file.
- **`Infinity` encoding depends on the parameter's value type.** The policy DB stores reform-dicts as JSON in a MySQL JSON column, which rejects bare `Infinity`.
  - **Float-typed parameters** (caps, thresholds, amounts): accept either the string `".inf"` OR a large numeric like `1e15`. Prefer `.inf` for clarity.
  - **Integer-typed parameters** (ages, qualifying-children counts): the string `".inf"` fails silently — the POST is accepted but the `/economy` call later returns `status: "error", message: null` with no diagnostic. Use a large *integer* like `999` instead.
  - When unsure, read the YAML — if it has `value_type: int` or values look like integers (no decimal), use the integer form.
- **Wrong baseline ID:** calling `/over/1` against an arbitrary reform returns a parse error or a stale baseline. Always use `/over/{baseline_policy_id}` — see Step 2.
- **Multi-year discontinuities:** TCJA / OBBBA / similar regime-shift parameters make single-year results unrepresentative of a 10-year window. When the reform touches a parameter that sunsets or inflates, run all 10 years (`--horizon 10`) — do NOT extrapolate. The 2026-07-01 std-ded +$1K empirical case: yr1×10 = $178.6B understated the real 10-year cost ($196.10B) by 10%.

## Hand-off

Returns the impact JSON. Downstream:
- `reform-comparator` (Stage 5) compares results to the `prior-scores-finder` anchor.
- `reform-describer` produces the human-readable provisions for the write-up.
- The /analyze-policy command formats the final report.

**This agent does NOT write to any database.** Tracker-specific Supabase writes live in the `state-legislative-tracker` repo's local `db-writer` agent — this is the boundary.
