---
name: policyengine-us-data-pipeline
description: |
  Investigates how a variable flows through the policyengine-us-data pipeline:
  which step sets its microdata value, what administrative targets constrain its
  weighted aggregate, and where in the code each implementation choice lives.
  Use this skill when you need to trace a variable from raw survey through
  imputation, calibration targets, and L0 weight optimization — or when you need
  to locate and fetch diagnostics for a specific pipeline run from HuggingFace.
  Triggers: "pipeline trace", "where does this value come from", "imputation source",
  "calibration target", "policy_data.db", "target_config.yaml", "build_package",
  "fit_weights", "matrix builder", "L0 calibration", "takeup in calibration",
  "source impute", "QRF imputation", "run ID", "pipeline diagnostics", "HuggingFace artifacts",
  "why is this aggregate wrong", "debug h5", "trace pipeline", "implementation choice",
  "how is this calculated in the pipeline", "unified_calibration", "matrix_builder",
  "calibration package", "calibration convergence", "domain variable", "stratum",
  "aca_ptc calibration", "snap calibration", "employment income imputation"
---

# PolicyEngine US Data Pipeline — Investigator Guide

This skill helps navigate the policyengine-us-data pipeline to locate where
implementation choices live and how pipeline stages relate to each other.
It is a starting point for investigation, not a reference manual.

## CRITICAL: Verify Against Code

The descriptions here reflect the pipeline as understood when written. The pipeline
evolves. Use this skill to identify *which file or function* is likely responsible for
a behavior, then **read that file** and confirm. Report what the code actually does —
not what this skill predicted. If something has changed, note the discrepancy.

The skill's job is to cut the time spent finding the right place. The explanation of
how something actually works must come from reading the code directly.

---

## 1. What the Pipeline Does — Conceptual Overview

Understanding the pipeline's purpose prevents misattributing problems to the wrong stage.

### Microdata and weights are separate concerns

The pipeline produces two things: **microdata values** (what each record says) and
**household weights** (how much each record counts). These are set at different stages
and must be reasoned about separately. Calibration never edits individual record values —
it only changes weights. So if a variable is wrong at the record level, calibration
cannot fix it.

### What imputation is

The CPS survey is the primary microdata source. It covers demographics, income, and
program participation, but lacks detailed tax information and some financial variables.
**Imputation** fills these gaps by statistically matching CPS records to donor surveys
that do contain them (IRS PUF, ACS, SIPP, SCF). The matching is done via Quantile
Random Forest (QRF): a model trained on the donor survey that predicts the target
variable given a set of predictors available in both surveys. The predictor set is the
key implementation choice — it determines what variation the imputed values can capture.
If state is not a predictor, the imputation cannot be state-specific.

### What calibration does

Even with good microdata, survey weights don't match administrative totals — the CPS
doesn't perfectly represent every geography or income group. **Calibration** corrects this
by solving an optimization problem: find a new set of household weights such that, when
you multiply each record's variable values by its weight and sum, the result matches
published administrative benchmarks (e.g., USDA SNAP totals by state, IRS income totals
by AGI bracket).

This is implemented via a **calibration matrix** (Stage 2) and an **L0-regularized
optimizer** (Stage 3). The matrix encodes, for each target, how much each cloned record
would contribute to that target at weight 1. The optimizer adjusts weights to minimize
squared relative errors across all targets simultaneously, with a sparsity penalty that
drives most weights to zero. The result is a sparse weight array — most records are
dropped; the retained ones have adjusted weights.

A critical implication: calibration can only match targets that are representable as
a weighted sum over records. If the variable whose aggregate you care about is a formula
variable (computed by PolicyEngine at simulation time), the matrix builder must run
PolicyEngine to compute it before building the matrix row. This is why the matrix builder
(`calibration/unified_matrix_builder.py`) is one of the most important files to read
when investigating calibration behavior — it is where the connection between
administrative targets and PolicyEngine formulas is made concrete.

### What the H5 files are

The final output of the pipeline is a set of H5 files — one per geographic area. Each
stores only **input variables** (values from Stage 1 microdata) and their calibrated
weights. Formula variables are not stored; they are recomputed at simulation time by
the PolicyEngine engine. This means that when you load an H5 and run a simulation, the
simulation recalculates formula variables using the stored inputs and the country model's
current formula definitions. The H5 value and the simulated value for a formula variable
will only agree if the country model version matches the one used during pipeline build.

---

## 2. Pipeline Shape

The pipeline has 6 stages. The first builds the calibration database; the next 5 run
on Modal and are tracked together under a single **run ID**.

```
Stage 0  make database      Builds policy_data.db — calibration targets from admin sources
                            Starting point: db/

Stage 1  build_datasets     Sets all microdata values. Raw CPS → cloned + imputed dataset.
                            Starting point: modal_app/data_build.py, datasets/cps/, calibration/

Stage 2  build_package      Runs PolicyEngine on cloned records to build the calibration matrix.
                            Starting point: modal_app/remote_calibration_runner.py,
                                           calibration/unified_matrix_builder.py

Stage 3  fit_weights        L0-regularized optimization. Finds weights that match targets.
                            Starting point: calibration/unified_calibration.py, utils/l0.py

Stage 4  publish_and_stage  Applies weights, writes H5 files, validates, stages to HuggingFace.
                            Starting point: modal_app/local_area.py,
                                           calibration/publish_local_area.py

Stage 5  promote            Moves staged H5s to production on HuggingFace. No new computation.
                            Starting point: modal_app/pipeline.py::promote_run()
```

**Separation of concerns:** Stages 1 and 2–3 are cleanly separated — microdata values are
frozen after Stage 1; Stages 2–3 only touch weights. A wrong aggregate can come from a
wrong microdata value (Stage 1 bug) or from miscalibration (Stage 2–3 issue). Knowing
which it is determines where to look.

---

## 2. Run ID and HuggingFace Artifact Linkage

**Run ID format:** `{version}_{sha[:8]}_{timestamp}`

Every artifact from a run is associated with this ID. When reviewing an H5 file, find its
run ID to locate all associated diagnostics and base datasets on HuggingFace.

**HF repo:** `policyengine/policyengine-us-data` (model repo)

The run metadata (`meta.json`) lives in the pipeline volume at `runs/{run_id}/meta.json`
and records which steps completed, their timings, and the git SHA.

**Diagnostics path on HF:**
```
calibration/runs/{run_id}/diagnostics/
  calibration_log.csv         ← per-epoch per-target errors (Stage 3)
  unified_diagnostics.csv     ← full optimization log (Stage 3)
  unified_run_config.json     ← hyperparameters used (Stage 3)
  validation_results.csv      ← per-area H5 validation (Stage 4)
  national_validation.txt     ← national validation output (Stage 4)
```

**Base dataset paths on HF** (per run, not under run ID — verify current paths in
`modal_app/pipeline.py::stage_base_datasets()`):
```
calibration/source_imputed_*.h5     ← microdata input to calibration
calibration/policy_data.db          ← targets used in this run
datasets/*.h5                       ← earlier pipeline intermediates
```

To fetch: use `huggingface_hub.hf_hub_download()` with
`repo_id="policyengine/policyengine-us-data"`, `repo_type="model"`.

---

## 3. Investigating a Variable — Navigation by Question

### "Where does the microdata value come from?" (Stage 1)

There are four possible origins. Check them in order — the first match is the answer:

1. **Direct CPS column** — `datasets/cps/cps.py`
2. **PUF QRF imputation** (tax variables) — `calibration/puf_impute.py`
3. **CPS-only second-stage QRF** (non-tax variables) — `datasets/cps/extended_cps.py`
4. **ACS/SIPP/SCF source imputation** (rent, assets, tips) — `calibration/source_impute.py`

For imputed variables, the most important implementation detail is the **predictor set** —
it determines what demographic and geographic variation the model captures. Read the
`*_PREDICTORS` constants in the relevant file. Note that some donor surveys lack state
identifiers, making those imputations state-blind at the microdata level.

Takeup booleans (`takes_up_*`) are a fifth case — see below.

### "Is there a calibration target?" (Stage 0 + Stage 2)

Two places to check, in order:

1. `calibration/target_config.yaml` — include/exclude rules that gate which DB targets
   enter the calibration matrix. If a variable is excluded here, calibration ignores it
   regardless of what is in the database.

2. `storage/calibration/policy_data.db` — the `target_overview` view is the primary
   query interface. Check `active`, `geo_level`, `domain_variable`, and `source`.
   The `source` column points to the ETL script (`db/etl_*.py`) that populated the target;
   read that script to understand what population the target represents.

If a target exists but the aggregate still looks wrong, the question becomes whether it
is a Stage 1 (microdata) or Stage 3 (optimization convergence) problem. Check Stage 1
first — if individual record values are systematically wrong, calibration cannot fix them
by weight adjustment alone.

### "How does feature X interact across stages?" — Cross-Stage Tracing

Some implementation choices touch multiple stages. When investigating these, the key is
to trace forward: where is it first set, what does each subsequent stage do with it?

**Example: takeup**

Takeup is not confined to one stage — it appears in three:

- **Stage 1** (`utils/takeup.py`, called from `datasets/cps/cps.py`): boolean takeup
  values are assigned to each cloned record using seeded Bernoulli draws at parametric
  rates. These values are frozen into the source-imputed dataset.

- **Stage 2** (`calibration/unified_matrix_builder.py`): when building the calibration
  matrix, takeup-affected targets are handled specially. Read the matrix builder to
  understand exactly how — the implementation here directly determines what the optimizer
  is trying to match for any variable whose aggregate depends on takeup.

- **Stage 4** (`calibration/publish_local_area.py`): when H5 files are assembled per area,
  takeup may be re-evaluated. Read this file to confirm whether the takeup in the final H5
  reflects Stage 1 values, or whether it is recomputed.

This forward trace is the pattern for any cross-cutting concern. Start at Stage 1 (where
is it first set?), check Stage 2 (does the matrix builder treat it specially?), then
Stage 4 (does the H5 builder change it?).

**Example: stratum domain constraints**

Domain constraints (e.g., `tax_unit_is_filer = 1` for IRS SOI targets, `snap > 0` for
SNAP-recipient targets) are defined in Stage 0 (`db/`) and consumed in Stage 2
(`calibration/unified_matrix_builder.py`). They determine which records contribute to
which calibration targets. A target with a domain constraint calibrates only the subpopulation
satisfying that constraint — weights are adjusted to match admin data for that subgroup,
not the full population. This is why comparing a full-population aggregate against an
IRS-sourced target will always show a gap: the target was never meant to cover non-filers.

To investigate a specific domain constraint: read how the matrix builder filters records
when it encounters a constraint variable, then trace back to `db/create_initial_strata.py`
to see how the stratum was constructed.

---

## 4. Key Entry Points

These are starting files for each major question. Read them — don't assume what they
contain matches what is described here.

| Starting question | Where to start |
|---|---|
| How is variable X extracted from CPS? | `datasets/cps/cps.py` |
| What variables are QRF-imputed and how? | `calibration/puf_impute.py`, `datasets/cps/extended_cps.py`, `calibration/source_impute.py` |
| How are takeup booleans assigned? | `utils/takeup.py` |
| Which targets are active and at what granularity? | `calibration/target_config.yaml`, then `policy_data.db` |
| Where do target values come from? | `db/etl_*.py` — one file per data source; check `source` column in DB |
| How is the calibration matrix constructed? | `calibration/unified_matrix_builder.py` |
| How does the L0 optimizer work? | `calibration/unified_calibration.py`, `utils/l0.py` |
| How are H5 files assembled per area? | `calibration/publish_local_area.py` |
| How is an H5 validated post-build? | `calibration/validate_h5_quality.py`, `calibration/sanity_checks.py` |
| What artifacts does a run produce and where? | `modal_app/pipeline.py::run_pipeline()` |
| How are diagnostics uploaded to HF? | `modal_app/pipeline.py::upload_run_diagnostics()`, `stage_base_datasets()` |

---

## 5. Investigation Best Practices

### Establish version and run identity first

Before interpreting any artifact or diagnostic, confirm which run produced it. The run ID
encodes the package version and git SHA — check that the SHA matches the code you are
reading. A diagnostic from one run interpreted against a different version of the code
will be misleading. When in doubt, fetch `meta.json` from the run to confirm the SHA, then
check out that commit before reading implementation files.

### Locate the stage before reading implementation

Ask: at which pipeline stage does this behavior occur? An imputed value is a Stage 1
question; a calibrated aggregate is a Stage 2–3 question; a value in a final H5 is a
Stage 4 question. Reading the wrong stage's code wastes time and may produce a
plausible-sounding but wrong explanation. The stage taxonomy in Section 2 is a starting
point — verify it by reading the pipeline orchestrator (`modal_app/pipeline.py`) to
confirm what each step actually does.

### Trace cross-stage relationships, not just the target stage

Most interesting behaviors involve more than one stage. When you find the relevant
file, always ask:
- What does this stage receive as input, and where did that input come from?
- What does this stage produce, and what does the next stage do with it?

For example, a variable's calibrated aggregate depends on: how it is imputed (Stage 1),
how the matrix row is constructed (Stage 2), whether it has an active target with the
right constraints (Stage 0 + Stage 2), and whether calibration converged for it (Stage 3).
Explaining the aggregate correctly requires tracing all four.

### Use the variable-tracing skill for the formula side

When a calibration target involves a variable that is computed by PolicyEngine (rather
than stored directly in the H5), you need to understand both the data pipeline side and
the formula side. Load the **policyengine-variable-tracing** skill to trace the variable's
formula, entity, definition period, and dependencies in the country model. This matters
because:
- The matrix builder runs PolicyEngine to compute the variable for each record; if the
  formula has changed between pipeline runs, the matrix rows and the H5 simulation output
  may disagree
- A variable calibrated against an admin total may have a formula that only activates
  under certain conditions (`defined_for`, parameter switches, eligibility gates) —
  these conditions determine which records actually contribute to the calibration target
- Input variables that feed a formula variable's calibration target have their own
  imputation path in Stage 1; tracing the formula's dependencies reveals which imputed
  inputs matter most for the calibrated aggregate

### When something looks wrong, distinguish microdata from weights

The first diagnostic split is always: is the individual record value wrong, or is the
weighted aggregate wrong despite correct individual values?

- Read a sample of individual records from the source-imputed H5 to assess microdata quality
- Compare the weighted aggregate against the target in `policy_data.db` to assess calibration
- If the microdata looks correct but the aggregate is off, the issue is in Stage 2–3
- If individual records look wrong, the issue is in Stage 1 — no amount of calibration can fix it

---

## Related Skills

- **policyengine-variable-tracing** — Variable definitions, formula types, and dependency
  tracing in the country model (policyengine-us). Load alongside this skill when you need
  to understand both the data pipeline value and how PolicyEngine computes the variable at
  simulation time.
- **policyengine-us-data** — Cross-repo workflow for adding new variables to the pipeline
  (`FINANCIAL_SUBSET`, version bumps, `IMPUTED_VARIABLES`).
- **microcalibrate** — L0, entropy balancing, and QRF imputation methods in general.
