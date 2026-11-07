---
name: policyengine-data
description: |
  Load for PolicyEngine's data layer — how Microcosm builds, calibrates, versions, and names the
  microdata behind population runs. Covers the Microcosm stack (Frame kernel, microcosm-fit
  conditional models, microcosm-calibrate weights with opt-in L0 pruning, build/release gates),
  the certified datasets in policyengine bundles (populace_us_2024 57k-household frozen-support
  default, populace_us_2024_acs_local ~1.6M local-area, microcosm_uk_2024_25 private),
  local-area runs as one national dataset plus a geography filter, the calibration diagnostics
  dashboard, and where data work goes since PolicyEngine archived policyengine-us-data.
  Triggers: Microcosm, Frame, microcosm-fit, microcosm-calibrate, calibration target, survey
  weights, reweighting, imputation, QRF, quantile loss, L0 sparsity, sparse 57k, dense_no_l0,
  local-area data, ACS, FRS, WAS, enhanced microdata, DEFAULT_DATASET.
  NOT for: running simulations (see policyengine) or diagnosing a specific score mismatch (see
  policyengine-calibration-diagnostics).
metadata:
  category: data
---

# PolicyEngine data

How the microdata behind PolicyEngine population runs is built, calibrated, versioned, and
named. For *using* datasets in a simulation, see the `policyengine` skill (this skill is about
where the data comes from). For diagnosing why one score disagrees with a benchmark, see
`policyengine-calibration-diagnostics`.

The current data stack is **Microcosm** (repo `PolicyEngine/microcosm`, local mirror
`~/PolicyEngine/microcosm`; read its `README.md` + `DESIGN.md`). It replaced the technique-named
packages of the previous stack (microdf / microimpute / microcalibrate / L0 /
policyengine-us-data), which shared no datatype and had their worst bugs at the seams between
flat DataFrames.

## The Microcosm architecture

Microcosm is one kernel datatype — the **`Frame`** — with packages as operators on it. It is a
PEP 420 namespace (`microcosm.*`) shipped as independently-installable shard distributions, so an
analyst doing imputation never has to install torch and vice versa. Microcosm releases pin the
shards as a constellation.

| Package | Import | Role | Succeeds |
|---|---|---|---|
| `microcosm-frame` | `microcosm.frame` | the kernel: `Frame`, typed weights, strata, links, weighted accounting, unit structure, the RulesEngine protocol | microdf, microunit |
| `microcosm-fit` | `microcosm.fit` | conditional models (weight-aware by construction) | ad-hoc imputation scripts |
| `microcosm-calibrate` | `microcosm.calibrate` | targets → calibrated weights (Adam; opt-in L0 pruning, or L1 via `prox`) | microcalibrate |
| `microcosm-build` | `microcosm.build` | build plans, donor graphs, release gates, country build stages | one-off build drivers |
| `microcosm-data` | `microcosm.data` | published population registry + lazy engine loaders | country-specific data packages |

Key design facts (from `DESIGN.md`) that change how you reason about the data:

- **The `Frame` is a weighted sampling frame of entity tables.** Person + group-entity tables
  with explicit `person_<group>_id` linkage established once at assembly — no operator
  re-derives person↔unit attachment from a flat frame. It carries **typed weights**
  (`design | importance | calibrated`, one vector per weighted entity) with conservation
  invariants the kernel enforces (strata mass sums; no silent zeroing; no NaN/negative), and
  **strata** giving every record explicit provenance (`cps_passthrough`,
  `synthetic_conditional`, `tail_verbatim`, ...). Generation owns support (oversample where it
  is scarce); calibration owns representation.
- **The rules engine is an adapter, not a dependency.** `microcosm.frame.rules.RulesEngine` is a
  Protocol (`variable_entity`, `variable_dtype`, `entity_schema`, `materialize`,
  `export_contract`, `write_dataset`). Today's adapter is `policyengine_us`; the Axiom
  `rulespec-us` adapter is written against the same protocol so the swap is a new adapter, not a
  migration.
- **`microcosm-fit` is weight-aware by construction** — fits read the frame's typed weights;
  there is no unweighted default. Canonical model: regime-gated, chained quantile forests with
  weights materialized by weighted bootstrap.
- **Only `microcosm-calibrate` produces calibrated weights.** `DESIGN.md` calls sparse
  target-matrix compilation plus APG / L0 pruning "the core, not an option" and
  generate-big-then-prune "the intended asymptotic design (300k → 3M → 30M pools)". The code
  keeps pruning opt-in: `calibrate()` defaults to `l0_lambda=0.0` and no `target_records`, and
  treats `method="apg"` as a deprecated alias for Adam (see "L0 sparsity" below for what the US
  builds ran). The calibrator's longitudinal rule: **one weight per trajectory** (multi-period
  targets stack as `(target, period)` constraint rows over one weight vector).
- **Process rules are as binding as the architecture:** behavioral contract tests in CI from day
  one (weighted fits shift draws toward the weighted truth; calibration conserves declared mass;
  unit assignment partitions exactly); constellation versioning (consumers pin the constellation,
  not git SHAs); artifacts embed a certificate of the rules-engine + package versions that
  produced them; stage manifests are versioned artifacts with invariant checks.

The long-run goal in `DESIGN.md` ("The commons") is a communal, continuously-improving synthetic
population where the three contribution types *are* the package decomposition — **records**
(new strata at honest weights, `frame`), **conditional structure** (fitted `P(y|x)` models,
`fit` — the only way private sources contribute), and **facts** (targets with standard errors,
`calibrate` — Chronicle's lane). A contribution merges iff it improves the population's score on
held-out, rotated evidence without degrading a protected target family beyond tolerance.

## Certified releases → policyengine bundles

Builds that pass the release gates are published to Hugging Face (`policyengine/populace-us`,
`policyengine/populace-uk-private`) and referenced by name in the certified bundle manifest that
ships inside the `policyengine` package. `populace-*` ids name Microcosm releases. These rows match
policyengine 6.16.0 (`policyengine/data/bundle/manifest.json`) and the Hugging Face release
manifests it pins, as of 2026-11-06:

| Dataset | What | How to load |
|---|---|---|
| `populace_us_2024` | US default. Build P (57,240 households, calibrated to 5,659 targets) plus one person-level SPM flag, `is_spm_independent_minor_role` | resolves automatically; do not pass a raw URI |
| `populace_us_2024_acs_local` | US local-area build. Build O, 1,586,908 households: 2024 ACS records, which keep their observed state and PUMA and draw a 119th-Congress district and county from population-weighted PUMA overlaps, plus donor records that keep their block-based district and county | load **by name**. The manifest's `region_datasets` makes it the `dataset_path` of the state and congressional-district entries in policyengine.py's region registry, but `Simulation` and the district-impact functions use whatever dataset you pass |
| `microcosm_uk_2024_25` | UK default (Microcosm) | private HF repo — set `HUGGING_FACE_TOKEN` |
| `microcosm_uk_2024_25_dense` | UK build for constituency and local-authority runs (the manifest's `region_datasets`) | private HF repo |

Manifest build ids (bundle 6.16.0, as of 2026-11-06): US `populace_us_2024` @
`populace-us-2024-spm-20260915`; US `populace_us_2024_acs_local` @
`populace-us-2024-buildo-acs-local-766b7c7-20261017T030317Z`; UK `microcosm_uk_2024_25` @
`microcosm-uk-2024-25-national-20261025T091414Z-a6299504`. The manifest also carries per-region
`region_datasets` and a `dataset_overlays` section that lists other UK builds (the FRS builds and
the older `populace_uk_2023`).

### The two defaults, precisely

There are two "default dataset" surfaces and they are *not* the same pin — know which one your
code path hits:

<!-- verify -->
```python
from policyengine_us.system import DEFAULT_DATASET
assert "populace_us_2024" in DEFAULT_DATASET
assert "hf://datasets/policyengine/populace-us" in DEFAULT_DATASET
```

- **The pe.py managed default** (what `pe.us.calculate_household`, `managed_microsimulation`, and
  `ensure_datasets` resolve): `populace_us_2024` at the **bundle-manifest** build —
  `populace-us-2024-spm-20260915` (bundle 6.16.0).
- **The country-package `DEFAULT_DATASET`** (what a bare <!-- stale-ok -->
  `from policyengine_us import Microsimulation; Microsimulation()` uses, in `policyengine_us/system.py`
  on policyengine-us main as of 2026-11-06): the *same dataset family* `populace_us_2024` on
  `hf://datasets/policyengine/populace-us`, pinned to release `populace-us-2024-spm-20260909`. That
  release holds the same H5 bytes as the bundle's `populace-us-2024-spm-20260915` (sha256
  `6496cc43…`, which `DEFAULT_DATASET_SHA256` also pins), so today both surfaces load identical data.

Both are Microcosm `populace_us_2024` — even the country package's own test/dev default is now
Microcosm (its `test_microsim.py` asserts `"populace" in DEFAULT_DATASET`). The takeaway: the two
pins live in separate repos, so the country-package default can drift from the certified bundle
when a new build lands. For reproducible, provenance-known results, go through the managed `pe.*` surface (which pins the certified bundle) rather
than a bare country-package `Microsimulation()`.

## Local-area analysis: one national dataset, filtered

The local-area philosophy is **one national dataset filtered by geography columns, never a file
per area.** `populace_us_2024_acs_local` is a single ~1.6M-household frame carrying `state_fips`,
`congressional_district_geoid`, county, etc.; you scope it with a row filter, not by downloading
a per-state or per-district file. The old per-area H5 artifacts no longer exist. See the
`policyengine` skill for the `RowFilterStrategy` / `region_registry` / `compute_*_impacts`
mechanics. This is why "give me the New York dataset" is the wrong mental model: there is one
dataset, and New York is a filter on it.

## Calibration diagnostics

Per-target calibration fit for the current release is browsable — no auth, reads the live release
from Hugging Face — at **`calibration-diagnostics.vercel.app`** (JSON API under
`/calibration/dashboard/api/microcosm`). Use it to see which admin targets a release hits and
which it misses before trusting a number that depends on them. The `policyengine-calibration-
diagnostics` skill covers the sensitivity registry and the three-ring reading method that turns
those diagnostics into hypotheses about a score.

## Where data work goes

- **New data work → the `microcosm` repo.** Build plans, calibration targets, conditional models,
  release gates, the published registry.
<!-- stale-ok -->
- **`policyengine-us-data` is ARCHIVED (2026-07-02).** The US enhancement path it owned (CPS +
  IRS-PUF imputation, calibration, its enhanced-CPS H5 releases, and the per-state / per-district
  H5s) is superseded by Microcosm and its per-area files were removed. Treat that repo as
  read-only history; do not target it with PRs.
- **`policyengine-uk-data` is still live** as the UK *input* pipeline: it produces the enhanced
  FRS (Family Resources Survey, ~20k households) with wealth and other variables imputed from the
  Wealth and Assets Survey (WAS, ~20k households), which feeds the UK Microcosm build. UK
  imputations (e.g. wealth, student-loan balances) land here.

## Institutional knowledge (archived-repo concepts, current mechanics)

The previous stack's *packages* are superseded, but the *algorithms* they implemented are exactly
what Microcosm's `fit` and `calibrate` operators do. These concepts remain load-bearing:

**Conditional-distribution imputation (QRF).** Fill a variable missing from a recipient survey by
learning it from a donor that has it, conditioning on shared predictors. PolicyEngine uses
**quantile regression forests**, which predict the full conditional distribution (not a point
estimate), so imputation preserves marginal shape, conditional relationships, and uncertainty —
you sample from `P(y | x)` rather than pasting a mean. Quality is scored with **quantile loss**
(lower is better; a distributional metric, unlike MSE). Classic US application: impute detailed
tax-return components (capital-gains split, dividends) from the IRS PUF onto the CPS. Classic UK
application: impute wealth from WAS onto FRS. In Microcosm this is `microcosm-fit`
(weighted-bootstrap QRF, regime-gated), and the fit reads the frame's weights by construction.

**Calibration = reweighting to hit targets.** Given estimate contributions per record and known
population totals, solve for weights so weighted sums match. The core relation:

```
achieved = estimate_matrix.T @ weights     # want: achieved ≈ targets
relative_error = abs(achieved - targets) / targets   # the diagnostic reported per target
```

Calibration owns *representation* (imputation/generation owns *support*). In Microcosm this is
`microcosm-calibrate`, which is uncertainty-weighted evidence combination against targets with
standard errors, not exact-hit — and the only producer of `calibrated` weights.

**L0 sparsity.** `microcosm-calibrate` can prune a candidate pool with **L0 regularization**
through **Hard-Concrete gates** (Louizos, Welling & Kingma 2017, arXiv:1712.01312), a
differentiable relaxation of the non-differentiable L0 norm. The solver multiplies each record's
weight by a gate and adds `l0_lambda` times the expected number of open gates to the loss
(`microcosm.calibrate.gates.HardConcrete`, `microcosm.calibrate.solve`):

```
effective_weight = weight * gate
loss = target_matching_loss + l0_lambda * expected_open_gates
```

Pruning is opt-in. `calibrate()` turns the gates on only when you pass `target_records` (the
solver then searches `l0_lambda` until the non-zero count tracks that budget) or a positive
`l0_lambda`, and `calibrate_l0_refit` prunes, then refits ordinary calibration on the survivors.
Without gates, Adam works on log-weights, so every weight stays positive. The US builder
(`tools/build_us_fiscal_refresh_release.py`) still runs L0 + refit by default; its help text
marks the dense arm, `--dense-default-dataset`, "Diagnostic only" and tells release builds to
leave it unset. Yet no US national build published on Hugging Face from 2026-07-01 on ran L0.
The build manifests of the 2026-07-01 release, of Builds I, J, M, N, O-sparse and P, and of the
2026-09-30 and 2026-10-24 builds all record `dense_no_l0`, a label the builder writes only on
that dense arm. Build H's published dense arm, a branch, has no build manifest, but its
diagnostics record `l0_lambda` 0 over its whole 337,704-household pool, and the SPM releases
inherit Build P's calibration (`calibration.mode: inherited`).

**Where the US default's 57,240 households come from.** No build in the default's published
lineage ran L0; each calibration in it worked on a fixed list of households. The Hugging Face
release manifests trace that list back to a 2026-07-01 release:

- `populace_us_2024` @ `populace-us-2024-spm-20260915` adds one SPM role variable to Build P
  (`populace-us-2024-buildp-sparse-rmloss100-cae8640-20260728T011454Z`) and keeps every other
  Build P variable exact, weights included (`source_enrichment.json`:
  `all_preexisting_variables_exact: true`).
- Build P froze its support before calibrating (`selection_source.mode: "frozen_support"`). It
  matched a named list of 57,240 households onto its 337,704-household candidate pool by stable
  source identity and dropped the rest (`select_frozen_support`, now in
  `microcosm.build.us_runtime.warm_start_selection`), then calibrated all 57,240 with no L0 term.
  Its build manifest records `method: "dense_no_l0"`, `sparse: false` and 6,000 epochs, and its
  `calibration_diagnostics.json` records Adam with `l0_lambda` 0.0.
- Build P's list comes from Build I's (identity hash `152baca3`) through Build M's 9-household
  swap, which adds the 9 Keogh-distribution carriers Build I lacked and drops the 9 non-carrier
  ASEC-channel households with the lowest base weights (`buildm-keogh-carrier-protect-swap`,
  PolicyEngine/microcosm#434). Build I, in turn, swapped 100 households in the support of
  `populace-us-2024-sparse-l0-refit-57k-71a0887-national-only-20260701`
  (`buildi-warmstart-misc-protect-swap`). PolicyEngine/microcosm#359 says the swap removed the
  100 negative miscellaneous-income carriers with the largest losses, which calibration had
  pushed to the weight cap, and added 100 high-AGI households with no miscellaneous income.
- Despite its id, that 2026-07-01 release also records `dense_no_l0`: 1,500 epochs on 57,240
  households, starting from weights in a local run file
  (`out/…/refit-selected-current-surface-a7a77c4-20260701/…`) that it did not publish. Its
  manifests do not record the pool that run chose from or how it chose.
  PolicyEngine/microcosm#328 calls that run "the informed-L0 step", and the builder's help text
  on main says its default `--l0-refit-lambda-share` "reproduces the current 57k-household US
  fiscal surface run from the 337k support".

So the 57k size comes from a selection that an unpublished run produced before the 2026-07-01
release (an L0 run, per microcosm#328 and the builder's help text) and that the national builds
I, J, M, N, O-sparse and P carried forward by identity, not from pruning in the current build.

Dense calibration still concentrates the weight. Build P's calibration artifact
(`populace_us_2024_calibration.npz`, whose `household_weight` vector the H5 ships) holds no exact
zeros, but 40,600 of its 57,240 households weigh less than 1, 42,903 ended below 1% of their
starting weight, and 12,329 hold 99% of the total weight. Build P's diagnostics report an
effective sample size of 9,174 and count 48,096 households as non-zero (`n_nonzero`, weights
above the solver's prune threshold of 1e-6 × the mean starting weight); the other 9,144 together
hold less than one ten-millionth of the weight.

**What this means for a reform.** A reform whose base no calibration target pins down can mis-read
on the default in either direction, down to near `$0`, for three reasons. First, the loss sees only
targeted quantities: Build P ran with `l0_lambda`, `l1_lambda` and `l2_lambda` all 0, and its hard
limits keep the total fixed and cap each weight at 5 times its starting value (which already
includes a 5.33x rescale to the Census population, so about 27 times the household's weight in the
candidate pool) but set no floor. The solve pushed 6,139 households, holding 53% of the weight, to
within 0.2% of that cap and sank 42,903 below 1% of their starting weight, so an untargeted variable
can read high when its carriers sit at the cap and low when they sank. Second, each target's loss
term stops growing at a 100% miss (`target_loss_scales.cap: 1.0`), so a target that ends further off
no longer pulls on the weights; Build P ended with 37 such targets
(`past_cap_census.final_past_cap`). microcosm#359 reports one case: Build H's unpublished frozen-57k
arm overshot its miscellaneous-income net-loss target by 322%, more than three times the loss cap,
after the solve pushed that loss's carriers to the weight cap. Third, a frozen support holds only
the records its selection kept, so an input that a later build restores can have almost no carriers.
Build P's own manifest gives the example: Build I's list "predates the keogh restoration and carried
~$0.1M unweighted of the $148.97M weighted source mass" of Keogh distributions, which the
`keogh_distribution_neutralization` reform-coverage probe caught (microcosm#434 reports a structural
zero).

When a result looks too small or too large, check whether a calibration target covers the reform's
base and how far it ended from that target (`relative_error`; see
`policyengine-calibration-diagnostics`). Then count the households that carry the base, the weight
they hold and their effective sample size; with 40,600 households below a weight of 1, a raw count
overstates the support. If the support looks thin, report it with the result and raise it in
`PolicyEngine/microcosm`, where microcosm#434's protect-swap shows one fix. As of 2026-11-06, the
two newest US national builds on Hugging Face
(`populace-us-2024-0fb05b6-4b57d15a287c-20260930T150401Z` and
`populace-us-2024-b5db384-8b0c1950b65f-20261024T083103Z`) skip the selection and calibrate a
352,932-household pool in full. Bundle 6.16.0 pins neither, but both use policyengine-us 2.2.1, the
version the bundle pins, so they work as a cross-check: load one through the country package with
the URI form `DEFAULT_DATASET` uses,
`hf://datasets/policyengine/populace-us/populace_us_2024.h5@<release id>` (a 2.5 GB file). They also
fit different target sets (5,694 and 6,102 targets, against Build P's 5,659), so a gap between
either one and the default flags a support question without measuring the support effect.

**Fast-mode builds in CI.** Data-pipeline steps (fitting, calibration) are expensive, so builds
honor a reduced-work mode for CI — fewer epochs / trees / a sampled frame — gated on an
environment flag rather than a code change, so tests exercise the real pipeline at small scale.
Reduce *hyperparameters and sample size*, never the correctness logic (don't skip validation or
swap algorithms). Microcosm additionally emits pre-release **staging telemetry by default** (a
`progress.json` / `events.ndjson` run under `runs/<run_id>/`) so every candidate shows on the
staging dashboard before it is published; disable with `--no-staging`.

## Related skills

- `policyengine` — using these datasets in household and population runs; `ensure_datasets`,
  `managed_microsimulation`, regional filtering.
- `policyengine-calibration-diagnostics` — the sensitivity registry + the live per-target
  diagnostics API for explaining a score gap.
- `policyengine-uk` / `policyengine-us` — country-model specifics that consume this data.
