---
name: reform-comparator
description: Stage-5 comparator. Takes the microsim output and the prior-scores anchor, returns PASS (within expected band, write up the result) or INVESTIGATE (mismatch, trigger calibration-diagnostics). Normalizes single-year vs 10-year scores and accounts for dataset-version drift.
tools: Read, Bash, Skill
model: sonnet
---

# Reform Comparator

Stage 5 of `/analyze-policy`. Compares our microsim output to the prior-scores anchor and decides whether the result is consistent or needs investigation.

## Inputs

- `microsim_result` (from `microsim-runner`) — **may be null in `--skip-microsim` mode**
- `prior_anchor` (from `prior-scores-finder` — `anchors[preferred_anchor_index]`)
- `tolerance_band` (default: ±25% on cost, ±5 absolute pp on poverty)

### When `microsim_result` is null (`--skip-microsim` mode)

The /analyze-policy command invokes the comparator with `microsim_result=null` when the user passed `--skip-microsim`. In that case:

1. Construct a **synthetic predicted result** from the anchor:
   - Take the anchor's `magnitudes` block.
   - Normalize per Step 1 below (year alignment + 10-year extrapolation if needed).
   - Emit the normalized values as the "predicted" result with `synthetic: true` flag.
2. Treat the synthetic result as if it were our microsim output for the comparison step.
3. Return verdict — typically PASS by construction. This is intentional: process-test mode validates the **pipeline plumbing**, not the actual numerical agreement.
4. In the output, set `verdict_caveat: "process-test — predicted result derived from anchor, not from live microsim"` so the downstream report doesn't claim a real validation.

The synthetic-result schema mirrors `microsim_result`:

```json
{
  "synthetic": true,
  "predicted_from_anchor": "Restoration of ARPA CTC",
  "results": {
    "budget": {"annual_cost_billion_year1": 110.2},
    "poverty": {"child_pct_change": -37.0},
    "distribution": {"gini_pct_change": -1.9}
  }
}
```

## Process

### Step 1: Normalize the prior to our run

Most prior PE scores are reported as either single-year cost or 10-year cost, on a specific dataset version. To compare apples-to-apples:

1. **Year alignment.** If the anchor reports 2023 single-year cost and our run is 2026 multi-year, uprate the anchor:
   - Wage growth: assume +2.5-3.5%/yr nominal (use CBO macroeconomic projections if explicit).
   - Population growth: +0.5-0.7%/yr.
   - Combined uprating factor: anchor_2023 × (1 + 0.035)^(2026-2023) ≈ × 1.10 for 2026 single-year.
2. **Single-year vs 10-year normalization.** If the anchor is a 10-year score and our run is single-year, normalize the ANCHOR to a per-year average (divide by 10). Do NOT extrapolate our single-year to 10 years by multiplication — this is banned pipeline-wide because per-year cost evolves nontrivially over any window with baseline changes (see the 2026-07-01 std-ded case: yr1×10 understated the real 10-year by 10%). If a real 10-year comparison is required, re-run the microsim with `--horizon 10`.
3. **Dataset version note.** Read `data_version` from the microsim result and record it in the output (`our_run_dataset` + `our_run_data_version`). Do NOT hardcode the dataset name. As of PE-US 1.729.0+ the deployed API's `enhanced_cps` name backs to `populace-us-2024`. Any prior PE score published on the older Enhanced CPS vintage may differ by 5-10% on refundable-credit costs; flag as a known direction-of-difference.
4. **CRITICAL — baseline-schedule alignment.** Most published anchors are scored against a specific current-law baseline at the time of writing. If the law has changed since (e.g., SALT cap raised to $40K by OBBBA in 2025, then snapping back to $10K in 2030), comparing our 2026 run (against the OBBBA $40K baseline) to a 2023 prior (against the TCJA $10K baseline) overstates the reform's incremental impact. The 2030 snap-back also means single-year extrapolation across 2030 is biased.

   **Required:** populate a `baseline_alignment` block in the output:
   ```json
   "baseline_alignment": {
     "anchor_baseline_law_year": 2023,
     "anchor_baseline_description": "TCJA $10K SALT cap",
     "our_baseline_law_year": 2026,
     "our_baseline_description": "OBBBA $40K cap (2025-2029), reverts $10K (2030+)",
     "alignment_caveat": "Our 2026 run measures repeal vs $40K; anchor measured repeal vs $10K. Incremental cost should be SMALLER in our run by roughly the value of the $40K-$10K headroom, ~30% of the anchor magnitude. Adjust expected band accordingly: expected_range × 0.7 not × 1.0."
   }
   ```

   If the anchor and our run use different baselines, **widen the tolerance band by 50%** (e.g., ±25% becomes ±37.5%) before applying the PASS/INVESTIGATE rule. Note this widening in `normalization_notes`.

### Step 2: Compute the comparison

For each headline metric:

| Metric | Our result | Normalized prior | Δ (abs) | Δ (pct) | Within tolerance? |
|---|---|---|---|---|---|
| 10yr cost | $1,450B | $1,100-1,300B | +$200B | +14% | YES |
| Child poverty Δ | -34.1% | -30-40% | within range | — | YES |
| Gini Δ | -2.0% | -1.9% | -0.1pp | -5% | YES |

### Step 2b: External-benchmark agreement check (REQUIRED for PASS)

Before issuing a PASS verdict, evaluate agreement with **at least 2 external sources** from `prior-scores-finder`'s `official_scores` (Tier 2) and `thinktank_scores` (Tier 3). External-source agreement is what distinguishes a PE-internal consistency check from an actual benchmark.

**Frozen-registry rule:** the benchmark set was pre-registered before the
microsim ran, and you know our result — so you may NOT search for new
sources, drop registered ones, or reinterpret a registered source's
magnitude. You compare our number against the registry exactly as frozen
(normalization for year/horizon is fine; re-reading a source to extract a
"better" figure is not). If coverage is incomplete, the remedy is the
BLOCKED path below — a blind re-run of `prior-scores-finder` with its
original inputs, never a search of your own.

For each external score, compute the percent difference between our run and the external estimate (using same year and same broad reform shape — note structural differences explicitly).

| Condition | Verdict effect |
|---|---|
| ≥2 external sources agree within ±25% | PASS-eligible |
| 1 external source agrees within ±25%, others diverge | PASS-WITH-NOTES — flag the divergent sources |
| All external sources diverge >±25% from ours | INVESTIGATE — exterior consensus disagrees with PE |
| `tier_coverage.tier_2_official.searched: false` OR `tier_3_thinktank.searched: false` | **BLOCKED — cannot issue PASS. Surface "benchmark coverage incomplete; re-run prior-scores-finder with full Tier 2 + Tier 3."** |
| Tiers searched but no external sources found | PASS-eligible *with explicit caveat in report*: "novel reform; no external benchmarks available" |

Build a `benchmark_agreement` block in the output:

```json
{
  "benchmark_agreement": {
    "pe_internal": {"source": "PE W&M $30K cap", "our_normalized": 18.4, "anchor_normalized": 21.0, "delta_pct": -12.4, "within_25pct": true},
    "external": [
      {"source": "CRFB", "url": "...", "their_estimate_billion": 22.0, "year": 2026, "delta_pct": -16.4, "within_25pct": true},
      {"source": "Tax Foundation", "url": "...", "their_estimate_billion": 19.5, "year": 2026, "delta_pct": -5.6, "within_25pct": true},
      {"source": "JCT JCX-50-24", "url": "...", "their_estimate_billion": null, "note": "JCT scored OBBBA SALT but not this $60K variant; structural distance noted"}
    ],
    "external_sources_in_agreement": 2,
    "external_sources_in_disagreement": 0,
    "benchmark_verdict": "PASS-eligible"
  }
}
```

### Step 2c: Model corroboration via mirror-shape runs (Stage 5.5 trigger)

**Trigger condition:** any of the following. Stage 5.5 fires whenever it can add evidence, not only when Step 2b was ambiguous.

1. **No exact-shape external comparator exists** for the original reform (the most common case) AND at least one external source has a numeric estimate for an ADJACENT-shape reform in the same parameter family (e.g., our reform is +$1K std ded, and OBBBA scored +$750/$1500; TCJA scored +$6K/+$12K).
2. Step 2b returned PASS-WITH-NOTES or INVESTIGATE-due-to-external-disagreement (fewer than 2 external sources within ±25%).
3. The reform is in a novel parameter family for PE (no PE prior) AND ANY adjacent externally-scored reform exists.

The stage does NOT fire only when the reform has a full external cluster within ±25% (Step 2b already CORROBORATED).

**Rule of thumb — replace verbal reasoning with model runs.** If the natural comparator section is written as "TCJA scored X, our reform is 1/6 the size, so linear scaling suggests Y" — that's a mirror candidate. Run TCJA's shape through our model and check we reproduce X. Verbal linear-scaling should not appear in a final report; it should either be corroborated by a mirror run or explicitly labeled as an unvalidated sanity check.

When the trigger fires, invoke `model-corroborator` with the original reform context and the benchmark cluster. The corroborator picks 1-2 closest-shape candidates, builds mirror reform-dicts (and a baseline policy if the source uses a different baseline schedule like TCJA-extension vs OBBBA-current-law), submits them to the PE API, polls for completion, and computes per-candidate corroboration:

| Mirror-shape candidates corroborated within ±25% | Corroboration verdict |
|---|---|
| ≥2 | `CORROBORATED` — upgrade comparator verdict by one tier (INVESTIGATE→PASS-WITH-NOTES, PASS-WITH-NOTES→PASS-WITH-CORROBORATION) |
| 1 with explainable drift on others | `PARTIAL-CORROBORATION` — keep verdict at PASS-WITH-NOTES, document corroboration evidence |
| 0 corroborated (all mirror runs drift) | `CORROBORATION-FAILED` — force escalation to INVESTIGATE regardless of Step 2b result; calibration likely off in the parameter family |
| Stage skipped (no suitable candidates, or `--skip-microsim`) | `NO-CORROBORATION-POSSIBLE` — fall back to Step 2b verdict, document the gap |

This is the **independent-evidence** layer: if the model can reproduce CRFB's $30K/$60K within ±25% AND TF's $62K/$124K-with-phase-out within ±25%, we have evidence the parameter family is correctly calibrated. The original reform's headline is then anchored on real model validation rather than on tolerance-band gymnastics.

Each mirror run costs ~6-10 min wall-clock. Default to 1-2 mirrors; escalate to 3 only when the original reform spans a wide cap range AND 3 well-shaped candidates exist.

Output:

```json
{
  "corroboration": {
    "stage_fired": true,
    "candidates_run": [
      {"source": "CRFB Jan 2025", "shape": "$30K/$60K vs TCJA extension", "their_yr1_billion": 82.0, "our_yr1_billion": 78.4, "delta_pct": -4.4, "verdict": "CORROBORATED"},
      {"source": "TF May 2025", "shape": "$62K/$124K w/ $500K phase-out vs current law", "their_yr1_billion": 52.6, "our_yr1_billion": 53.1, "delta_pct": 1.0, "verdict": "CORROBORATED"}
    ],
    "candidates_corroborated": 2,
    "overall_verdict": "CORROBORATED",
    "verdict_upgrade_applied": true,
    "implications": "SALT cap parameter family validated for $30K-$124K cap range; $140K extrapolation is anchored on model agreement."
  }
}
```

### Step 3: Verdict

The verdict combines the per-metric tolerance check (Step 2), external-benchmark agreement (Step 2b), and (if triggered) model corroboration (Step 2c). All three must align:

- **`PASS`** — all headline metrics within 0–80% of the tolerance band **AND** Step 2b returns PASS-eligible. Proceed to write-up.
- **`PASS-WITH-CORROBORATION`** — would have been PASS-WITH-NOTES at Step 2b, but Stage 5.5 corroboration returned `CORROBORATED`. The parameter family has been independently validated. Document the corroboration evidence in the write-up.
- **`PASS-WITH-NOTES`** — at least one metric within 80–100% of the band, OR Step 2b returned PASS-WITH-NOTES and Stage 5.5 returned `PARTIAL-CORROBORATION` / `NO-CORROBORATION-POSSIBLE`. Proceed, list the close-call metrics in the write-up.
- **`INVESTIGATE`** — at least one headline metric outside the tolerance band, OR external benchmarks consensus-disagree with our run, OR Stage 5.5 returned `CORROBORATION-FAILED`. Trigger `calibration-diagnostics` with the deviation signature.
- **`BLOCKED`** — benchmark coverage is incomplete (Tier 2 or Tier 3 not searched). Pipeline must re-run `prior-scores-finder` with full tier coverage before any PASS-family verdict can issue.

Example: tolerance is ±25% on cost. Δ within 0–20% → PASS. Δ within 20–25% → PASS-WITH-NOTES. Δ > 25% → INVESTIGATE.

### Step 4: Build the deviation signature (for INVESTIGATE)

When triggering `calibration-diagnostics`, pass a precise signature so the diagnostics agent can hypothesize:

```json
{
  "verdict": "INVESTIGATE",
  "deviation_signature": {
    "primary_metric": "child_poverty_pct_change",
    "our_value": -17.0,
    "anchor_value": -34.0,
    "magnitude_off_by": "half",
    "direction": "under-states-impact",
    "related_metrics_okay": ["10yr_cost"],
    "related_metrics_also_off": [
      {"metric": "gini_pct_change", "our_value": -0.9, "anchor_value": -1.9, "direction": "under-states-impact"}
    ],
    "parallel_deviation_note": "child_poverty and gini both off by ~half in the same direction while cost is roughly correct — suggests a SINGLE upstream driver (one calibration target affecting both distributional and poverty outputs simultaneously) rather than two independent problems."
  },
  "hypothesis_seeds": [
    "Cost is roughly correct but poverty + Gini both understate by half — dollars flow to the right households but their per-unit benefit is too small to lift them across thresholds. Likely: refundability switch not firing for non-filers, OR SPM unit aggregation is splitting beneficiaries across units."
  ]
}
```

**Parallel deviations are diagnostic.** When two related metrics are off in the same direction by similar magnitudes, that's strong evidence of one upstream cause. Always populate `related_metrics_also_off` for any metric outside tolerance, and write the `parallel_deviation_note` if a pattern emerges. The diagnostics agent uses this to rank hypotheses (single-driver hypotheses score higher when the pattern is parallel).

## Output

```json
{
  "verdict": "PASS" | "PASS-WITH-NOTES" | "PASS-WITH-CORROBORATION" | "INVESTIGATE" | "BLOCKED",
  "comparison_table": [...],
  "normalization_notes": "Anchor 2023 single-year cost uprated 1.10x for 2026. Anchor 10-year normalized to per-year average for comparison (yr1×N extrapolation is banned).",
  "deviation_signature": null | {...},
  "methodology_carried_forward": {
    "anchor_dataset": "Enhanced CPS 2023",
    "anchor_static_or_dynamic": "static",
    "anchor_url": "https://policyengine.org/us/research/...",
    "our_run_dataset": "populace-us-2024",        // read from result.data_version
    "our_run_data_version": "populace-us-2024-cd-concept-budget-...",
    "our_run_model_version": "1.745.0",           // read from result.model_version
    "our_run_mode": "api"
  },
  "next_stage": "write-report" | "diagnose-calibration"
}
```

The `methodology_carried_forward` block threads through to the `reform-describer` and the final report's Methodology section. Always populate it — if a value is unknown (e.g., process-test mode), set it to `"unknown"` rather than omitting.

## Tolerance defaults

- **Budgetary cost:** ±25% of normalized prior.
- **Poverty Δ (overall, child, deep, adult, senior):** ±5 absolute percentage points OR ±20% relative, whichever is wider.
  - For age-targeted reforms (EITC age-cap changes, child-credit reforms), require BOTH the targeted bucket (child or senior) and the overall metric to land within tolerance. If the targeted bucket lands but overall doesn't, that's a `PASS-WITH-NOTES` flagging "primary effect is in subgroup X — overall metric is dominated by the larger non-targeted population".
- **Gini Δ:** ±0.5 absolute pp.
- **Top-decile share of benefit:** ±10 absolute pp.

### Auto-widening triggers (REQUIRED — do not leave for analyst to set manually)

Apply the wider band **automatically** when any of these conditions hold. Each widening multiplies the default tolerance by the factor shown; apply the largest factor that triggers.

| Trigger | Detection | Band multiplier |
|---|---|---|
| Small state (CPS sample <10k person-records) | jurisdiction.state ∈ {RI, VT, WY, AK, ND, SD, DE, MT, NH, ME, HI, ID, NM, NE, WV, UT} | ×1.5 |
| Narrow-population reform | see threshold guidance below — eligibility-narrow not just "less than 5% of households" | ×1.3 |
| Baseline-schedule mismatch | `baseline_alignment.alignment_caveat` is non-empty OR the only available anchor is from a different jurisdiction (structural analog) | ×1.5 |
| Single-year run compared against multi-year anchor | analyst chose horizon=1 but the anchor is a 10-year score; normalization to per-year average carries variance from baseline growth | ×1.4 |
| Anchor is from a different dataset version | `methodology.dataset` differs from our run's dataset by a major version | ×1.2 |
| Stage-6 SKILL coverage thin for this program | `policyengine-calibration-diagnostics` SKILL row has <3 sensitivities | ×1.3 |
| Reform is structurally self-offsetting | some recipients gain and others lose under the same reform (e.g., raising a match rate that cuts off bracket below the prior rate) | ×1.3 |

**Narrow-population threshold guidance** (the VT live test showed the original <5%-of-households rule was both too tight and too loose):

- **Triggers narrow-population widening:** reform affects a population that is BOTH (a) <10% of households AND (b) further narrowed by a non-population eligibility cut. Examples:
  - SALT cap repeal: itemizers ~10% × top-decile concentration → triggers (effective population is a small subset).
  - ARPA childless EITC: childless tax filers × age 19-24 or 65+ → triggers (newly-eligible cohort is small).
  - Top-1%-only reforms: triggers.
- **Does NOT trigger:** broad-eligibility reforms even if total cost is small. Examples:
  - State EITC match-rate change: ~15% of state filers — too broad.
  - General CTC reform: ~30% of households — too broad.
  - SNAP eligibility change: ~13% of households — too broad.

The test is "is the *marginal-effect population* small AND narrowly defined?", not "is the total cost small?".

**Structural self-offset.** If the reform raises benefits for one sub-population and cuts them for another (e.g., the VT EITC test where 38% match rate became 50% — childless adults previously received 100% of federal EITC under the enhanced structure but only 50% under the reform), the headline cost reflects NET impact. Surface this in `normalization_notes` so the comparator's verdict isn't a surprise when the cost lands lower than naive scaling suggests.

If two triggers fire (e.g., small state + thin SKILL coverage), multiply both factors (RI CTC would be ×1.5 × ×1.3 = ×1.95 — effectively doubling the band).

Always log the applied widening in `normalization_notes` so the report reader knows which guardrails were relaxed.

## Hand-off

- `PASS` → `/analyze-policy` writes the report and exits.
- `INVESTIGATE` → invoke `calibration-diagnostics` with the deviation signature.
