---
name: policyengine-data
description: |
  Load for PolicyEngine's data layer — how the microdata behind population microsimulations is
  built, calibrated, versioned, and named. Covers the current Populace stack (Frame kernel,
  populace-fit conditional models, populace-calibrate weights with L0 sparsity, build/release
  gates), the certified datasets that flow into policyengine bundles (populace_us_2024 sparse
  ~57k default, populace_us_2024_acs_local ~1.6M local-area, populace_uk_2023 private), the
  "one national dataset filtered by geography" local-area philosophy, the calibration
  diagnostics dashboard, and where data work goes now that policyengine-us-data is archived.
  Triggers: Populace, Frame, populace-fit, populace-calibrate, calibration target, survey
  weights, reweighting, imputation, QRF, quantile loss, L0 sparsity, sparse 57k, local-area
  data, ACS, FRS, WAS, enhanced microdata, DEFAULT_DATASET.
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

The current data stack is **Populace** (repo `PolicyEngine/populace`, local mirror
`~/PolicyEngine/populace`; read its `README.md` + `DESIGN.md`). It replaced the technique-named
packages of the previous stack (microdf / microimpute / microcalibrate / L0 /
policyengine-us-data), which shared no datatype and had their worst bugs at the seams between
flat DataFrames.

## The Populace architecture

Populace is one kernel datatype — the **`Frame`** — with packages as operators on it. It is a
PEP 420 namespace (`populace.*`) shipped as independently-installable shard distributions, so an
analyst doing imputation never has to install torch and vice versa. A `populace` metapackage
pins the constellation.

| Package | Import | Role | Succeeds |
|---|---|---|---|
| `populace-frame` | `populace.frame` | the kernel: `Frame`, typed weights, strata, links, weighted accounting, unit structure, the RulesEngine protocol | microdf, microunit |
| `populace-fit` | `populace.fit` | conditional models (weight-aware by construction) | ad-hoc imputation scripts |
| `populace-calibrate` | `populace.calibrate` | targets → calibrated weights (APG / L0) | microcalibrate |
| `populace-build` | `populace.build` | build plans, donor graphs, release gates, country build stages | one-off build drivers |
| `populace-data` | `populace.data` | published population registry + lazy engine loaders | country-specific data packages |

Key design facts (from `DESIGN.md`) that change how you reason about the data:

- **The `Frame` is a weighted sampling frame of entity tables.** Person + group-entity tables
  with explicit `person_<group>_id` linkage established once at assembly — no operator
  re-derives person↔unit attachment from a flat frame. It carries **typed weights**
  (`design | importance | calibrated`, one vector per weighted entity) with conservation
  invariants the kernel enforces (strata mass sums; no silent zeroing; no NaN/negative), and
  **strata** giving every record explicit provenance (`cps_passthrough`,
  `synthetic_conditional`, `tail_verbatim`, ...). Generation owns support (oversample where it
  is scarce); calibration owns representation.
- **The rules engine is an adapter, not a dependency.** `populace.frame.rules.RulesEngine` is a
  Protocol (`variable_entity`, `variable_dtype`, `entity_schema`, `materialize`,
  `export_contract`, `write_dataset`). Today's adapter is `policyengine_us`; the Axiom
  `rulespec-us` adapter is written against the same protocol so the swap is a new adapter, not a
  migration.
- **`populace-fit` is weight-aware by construction** — fits read the frame's typed weights;
  there is no unweighted default. Canonical model: regime-gated, chained quantile forests with
  weights materialized by weighted bootstrap.
- **`populace-calibrate` is the only place calibrated weights are produced.** Sparse
  target-matrix compilation + APG / L0 pruning is the core, not an option — "generate big then
  prune" is the intended design (300k → 3M → 30M candidate pools pruned to a compact frame). Its
  longitudinal rule: **one weight per trajectory** (multi-period targets stack as
  `(target, period)` constraint rows over one weight vector).
- **Process rules are as binding as the architecture:** behavioral contract tests in CI from day
  one (weighted fits shift draws toward the weighted truth; calibration conserves declared mass;
  unit assignment partitions exactly); constellation versioning (consumers pin the constellation,
  not git SHAs); artifacts embed a certificate of the rules-engine + package versions that
  produced them; stage manifests are versioned artifacts with invariant checks.

The long-run goal in `DESIGN.md` ("The commons") is a communal, continuously-improving synthetic
population where the three contribution types *are* the package decomposition — **records**
(new strata at honest weights, `frame`), **conditional structure** (fitted `P(y|x)` models,
`fit` — the only way private sources contribute), and **facts** (targets with standard errors,
`calibrate` — Ledger's lane). A contribution merges iff it improves the population's score on
held-out, rotated evidence without degrading a protected target family beyond tolerance.

## Certified releases → policyengine bundles

Builds that pass the release gates are published to Hugging Face (`policyengine/populace-us`,
`policyengine/populace-uk-private`) and referenced by name in the certified bundle manifest that
ships inside the `policyengine` package. Verified in policyengine 4.21.0 (`policyengine/data/
bundle/manifest.json`):

| Dataset | What | How to load |
|---|---|---|
| `populace_us_2024` | US default. Build J, sparse, ~57k households calibrated to tens of thousands of admin targets | resolves automatically; do not pass a raw URI |
| `populace_us_2024_acs_local` | US local-area build. Build L, ~1.6M households, ACS multispine, PUMA-assigned to CD-119 / county / state | load **by name**, never implicit |
| `populace_uk_2023` | UK default (Populace, FRS+WAS) | private HF repo — set `HUGGING_FACE_TOKEN` |

Verified manifest build ids (2026-07): US `populace_us_2024` @
`populace-us-2024-buildj-sparse-rmloss100-75d5add-20260710`; UK `populace_uk_2023` @
`populace-uk-2023-dd68c73-...`. The manifest also carries a `dataset_overlays` section (where the
`acs_local` overlay lives) and per-region `region_datasets`.

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
  `populace-us-2024-buildj-sparse-...-20260710` (Build J, 2026-07-10).
- **The country-package `DEFAULT_DATASET`** (what a bare
  `from policyengine_us import Microsimulation; Microsimulation()` uses, verified 1.764.6 at
  `policyengine_us/system.py`): the *same dataset family* `populace_us_2024` on
  `hf://datasets/policyengine/populace-us`, but pinned to an **earlier build**
  (`populace-us-2024-c86a631-...-20260619`, 2026-06-19).

Both are Populace `populace_us_2024` — even the country package's own test/dev default is now
Populace (its `test_microsim.py` asserts `"populace" in DEFAULT_DATASET`). The takeaway: the
country-package default can lag the certified bundle by a build. For reproducible, provenance-
known results, go through the managed `pe.*` surface (which pins the certified bundle) rather
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
`/calibration/dashboard/api/populace`). Use it to see which admin targets a release hits and
which it misses before trusting a number that depends on them. The `policyengine-calibration-
diagnostics` skill covers the sensitivity registry and the three-ring reading method that turns
those diagnostics into hypotheses about a score.

## Where data work goes

- **New data work → the `populace` repo.** Build plans, calibration targets, conditional models,
  release gates, the published registry.
<!-- stale-ok -->
- **`policyengine-us-data` is ARCHIVED (2026-07-02).** The US enhancement path it owned (CPS +
  IRS-PUF imputation, calibration, its enhanced-CPS H5 releases, and the per-state / per-district
  H5s) is superseded by Populace and its per-area files were removed. Treat that repo as
  read-only history; do not target it with PRs.
- **`policyengine-uk-data` is still live** as the UK *input* pipeline: it produces the enhanced
  FRS (Family Resources Survey, ~20k households) with wealth and other variables imputed from the
  Wealth and Assets Survey (WAS, ~20k households), which feeds the UK Populace build. UK
  imputations (e.g. wealth, student-loan balances) land here.

## Institutional knowledge (archived-repo concepts, current mechanics)

The previous stack's *packages* are superseded, but the *algorithms* they implemented are exactly
what Populace's `fit` and `calibrate` operators do. These concepts remain load-bearing:

**Conditional-distribution imputation (QRF).** Fill a variable missing from a recipient survey by
learning it from a donor that has it, conditioning on shared predictors. PolicyEngine uses
**quantile regression forests**, which predict the full conditional distribution (not a point
estimate), so imputation preserves marginal shape, conditional relationships, and uncertainty —
you sample from `P(y | x)` rather than pasting a mean. Quality is scored with **quantile loss**
(lower is better; a distributional metric, unlike MSE). Classic US application: impute detailed
tax-return components (capital-gains split, dividends) from the IRS PUF onto the CPS. Classic UK
application: impute wealth from WAS onto FRS. In Populace this is `populace-fit`
(weighted-bootstrap QRF, regime-gated), and the fit reads the frame's weights by construction.

**Calibration = reweighting to hit targets.** Given estimate contributions per record and known
population totals, solve for weights so weighted sums match. The core relation:

```
achieved = estimate_matrix.T @ weights     # want: achieved ≈ targets
relative_error = abs(achieved - targets) / targets   # the diagnostic reported per target
```

Calibration owns *representation* (imputation/generation owns *support*). In Populace this is
`populace-calibrate`, which is uncertainty-weighted evidence combination against targets with
standard errors, not exact-hit — and the only producer of `calibrated` weights.

**L0 sparsity — the sparse-57k-vs-dense story.** To keep the calibrated frame small and fast,
weights are pushed toward exact zero with **L0 regularization** via **Hard-Concrete gates**
(Louizos, Welling & Kingma 2017, arXiv:1712.01312) — a differentiable relaxation of the
non-differentiable L0 norm. Conceptually `effective_weight = weight * gate`, with the gate driven
toward 0 or 1 and a penalty on the count of non-zero gates:

```
loss = target_matching_loss + l0_lambda * count_nonzero(weights)
```

This is why the certified US default is **sparse (~57k households)**: most candidate records are
pruned to zero weight. The tradeoff — and the reason denser builds are sometimes kept — is that a
record whose distinctive input **no target constrains** can be pruned away, so a reform that
depends on an *untargeted* variable can under-read on the sparse default (a reform can even score
near `$0` if its operative base was pruned). When a result looks suspiciously small, check whether
the reform's base is a calibration target (see `policyengine-calibration-diagnostics`); if not, a
denser build may be the right dataset. In Populace this pruning is `populace-calibrate`'s L0
(`target_records`) path, integral to "generate big then prune."

**Fast-mode builds in CI.** Data-pipeline steps (fitting, calibration) are expensive, so builds
honor a reduced-work mode for CI — fewer epochs / trees / a sampled frame — gated on an
environment flag rather than a code change, so tests exercise the real pipeline at small scale.
Reduce *hyperparameters and sample size*, never the correctness logic (don't skip validation or
swap algorithms). Populace additionally emits pre-release **staging telemetry by default** (a
`progress.json` / `events.ndjson` run under `runs/<run_id>/`) so every candidate shows on the
staging dashboard before it is published; disable with `--no-staging`.

## Related skills

- `policyengine` — using these datasets in household and population runs; `ensure_datasets`,
  `managed_microsimulation`, regional filtering.
- `policyengine-calibration-diagnostics` — the sensitivity registry + the live per-target
  diagnostics API for explaining a score gap.
- `policyengine-uk` / `policyengine-us` — country-model specifics that consume this data.
