# Worked Example: Tracing `snap` end-to-end

> **Note:** This example is specific to the **policyengine-us-data** pipeline (CPS ASEC,
> IRS PUF, policy_data.db, target_config.yaml). Other country pipelines (e.g.,
> policyengine-uk-data using FRS/SPI) have different survey sources, imputation steps,
> and calibration infrastructure. Apply the same reasoning but look for the equivalent
> files in the relevant pipeline — load the country-specific domain skill for guidance.

**Scenario:** SNAP benefit values in an H5 file look unexpectedly low. Trace the variable
end-to-end to understand what it represents and where its value comes from.

---

**Step 1 — Find the variable definition**
```bash
grep -r "class snap\b" policyengine_us/variables/ --include="*.py" -l
# → policyengine_us/variables/gov/usda/snap/snap.py
```

**Step 2 — Check the variable type and entity**

Opening `snap.py`:
```python
class snap(Variable):
    value_type = float
    entity = SPMUnit        # defined at SPM unit level, not household or person
    definition_period = MONTH
    reference = "https://www.law.cornell.edu/uscode/text/7/2017#a"

    def formula(spm_unit, period, parameters):
        ...
```

`snap` has a `formula` → it is a **calculated variable**. It will NOT be stored in the H5
file. The simulation recomputes it at runtime from its dependencies.

**Step 3 — Check the legal reference**

Open `https://www.law.cornell.edu/uscode/text/7/2017#a` (7 U.S.C. § 2017). This defines
the SNAP allotment as the maximum allotment minus 30% of net income, subject to minimum
benefit rules. Verify the formula body reflects these conditions — specifically what
eligibility conditions, income deductions, and phase-out rules it applies or omits.
Note any simplifications or assumptions in the implementation that diverge from the
statutory text.

**Step 4 — Read the formula dependencies**

```python
def formula(spm_unit, period, parameters):
    takes_up = spm_unit("takes_up_snap_if_eligible", period)
    is_in_microsim = hasattr(spm_unit.simulation, "dataset")
    if parameters(period).gov.usda.snap.abolish_snap:
        return 0
    elif parameters(period).gov.simulation.reported_snap:
        return spm_unit("snap_reported", period)   # microsim: use reported value
    else:
        value = add(spm_unit, period, [
            "snap_normal_allotment",
            "snap_emergency_allotment",
            "dc_snap_temporary_local_benefit",
        ])
        if is_in_microsim:
            return value * takes_up   # microsim: apply take-up factor
        else:
            return value              # policy analysis: full benefit, no take-up
```

There are three critically different code paths here — which one runs depends on
parameter flags and runtime context, not on anything visible in the H5 file:

1. **`reported_snap = True`** (microsimulation mode): returns `snap_reported` directly.
   This is the path the data pipeline typically exercises. The formula variables
   (`snap_normal_allotment`, etc.) are not used at all.

2. **`reported_snap = False`, in microsim** (simulation has a `dataset` attribute):
   calculates the full allotment from formula variables, then multiplies by
   `takes_up_snap_if_eligible`. Take-up is applied automatically — you cannot
   disable it from the formula side.

3. **`reported_snap = False`, not in microsim** (policy analysis mode):
   returns the full calculated allotment with no take-up adjustment.

**Definition period mismatch:** `snap` is `MONTH`-period; `snap_reported` is `YEAR`-period.
When `reported_snap = True`, the engine divides the annual reported value by 12 to fit
the monthly context. If you compare H5 `snap_reported` values (annual) against simulated
`snap` values (monthly), you must account for this scaling.

In microsimulation mode with `reported_snap = True`, trace `snap_reported` next.

**Step 5 — Trace the input variable `snap_reported`**
```bash
grep -r "class snap_reported" policyengine_us/variables/ --include="*.py" -l
# → policyengine_us/variables/.../snap_reported.py
```
`snap_reported` has no formula → **input variable**, defined on `SPMUnit`, `definition_period = YEAR`.
This IS stored in the H5 file.

**Step 6 — Find it in the data pipeline**
```bash
grep -n "snap_reported" policyengine_us_data/datasets/cps/cps.py
# → snap_reported="SPM_SNAPSUB"
```
`snap_reported` maps directly to the `SPM_SNAPSUB` column from the CPS ASEC — the
Census-reported SNAP subsidy amount at the SPM unit level. This is a direct survey
extraction, not an imputation.

**Step 7 — Check calibration targets**

First check `target_config.yaml` to see if `snap` is listed as a calibration target
and at what geographic granularity:
```bash
grep -n -A2 "variable: snap" policyengine_us_data/policyengine_us_data/calibration/target_config.yaml
# → - variable: snap
# →   geo_level: state
# → - variable: snap
# →   geo_level: national
```

`snap` is targeted at both state and national levels. This means the L0 calibration
optimization adjusts household weights so that `sum(snap * weight)` matches
administrative SNAP totals at each geographic level — but it does this by changing
weights only, not the underlying `snap_reported` microdata values.

Next, inspect the actual target values the calibration is trying to hit. These are
stored in the policy database:
```bash
sqlite3 policyengine_us_data/policyengine_us_data/db/policy_data.db \
  "SELECT * FROM targets WHERE variable = 'snap' LIMIT 20;"
```

This shows the administrative benchmarks (e.g., USDA SNAP program totals by state)
that weights are being optimized against. If a weighted SNAP total deviates from
expectations, compare it against these target values directly:
- A large gap between the H5 weighted total and the target suggests calibration
  didn't converge well for that geography (check calibration logs or loss values)
- A target that itself looks wrong points to a data issue in the ETL scripts
  that populate the database (look in `db/etl_*.py`)
- A target that no longer exists (`# REMOVED` in target_config.yaml) means the
  variable was dropped from calibration and aggregates are now unconstrained

**Step 8 — Watch for non-obvious eligibility conditions**

Even if the microdata and calibration look correct, SNAP values can be wrong because
of implicit conditions in the model that are easy to miss:

- **Unit size excludes ineligible members.** `snap_unit_size` subtracts members who
  are ineligible students or immigration-ineligible. Allotments, deductions, and FPG
  thresholds all use this reduced unit size. If person-level eligibility flags are
  wrong, the entire allotment calculation is off.

- **`snap_normal_allotment` has `defined_for = "is_snap_eligible"`**, meaning it
  returns zero (silently) for ineligible units. Ineligible units in aggregate
  statistics count as $0 — they are not excluded from the denominator.

- **Categorical eligibility via SSI or TANF.** An SPM unit can become eligible
  because it receives any SSI or TANF, bypassing income and asset tests entirely.
  If those benefit amounts are wrong in your dataset, eligibility will be wrong too.

- **FPG uses fiscal-year timing**, not calendar-year. January–September calculations
  use the previous fiscal year's poverty guidelines. If you compare against
  calendar-year published FPG tables, values will appear off for those months.

**Step 9 — Watch for user-applied filters that the formula doesn't require**

A common source of aggregate discrepancies is filters that users or analysts apply
when computing totals from the H5 file, which do not reflect how SNAP is actually
defined. For example:

- **Household vs. SPM unit**: SNAP is defined on `SPMUnit`, not `Household`. If
  weights or aggregations are applied at the household level, unit-level values will
  be double-counted or missed depending on how SPM units map to households.

The general rule: when an aggregate from the H5 diverges from an administrative total,
check whether any filter applied to the data is more restrictive than the variable's
own `defined_for` and eligibility conditions. The formula is the specification — any
additional filter is an assumption that needs justification.

---

**Conclusion:**
- Individual `snap_reported` values come from CPS `SPM_SNAPSUB` (direct survey, Stage A)
- Weighted SNAP aggregates are constrained to USDA administrative totals via calibration (Stage D)
- If weighted totals look wrong → compare against `policy_data.db` targets, check
  calibration convergence, and inspect `target_config.yaml` for removed targets
- If individual record values look wrong → investigate CPS extraction (`SPM_SNAPSUB`
  column), the `takes_up_snap_if_eligible` stochastic assignment in `cps.py`, or
  whether the `reported_snap` parameter is set correctly for your simulation context
- If aggregates look wrong even with correct microdata → check whether any user-applied
  filters are more restrictive than the variable's own eligibility conditions
