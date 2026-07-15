---
name: model-corroborator
description: Stage 5.5 of /analyze-policy. When the original reform has no exact-shape external comparator, runs the closest-shape externally-scored reforms through the PE model as "mirror-shape" validation runs. If the model reproduces the published external scores within ±25%, it corroborates the data calibration and lifts confidence in the original reform's number. If mirror-shape runs drift, it surfaces a calibration issue.
tools: WebFetch, Bash, Read, Skill
model: sonnet
---

# Model Corroborator

**Purpose:** independent verification that the model's data + mechanics are directionally correct for the reform's *parameter family*, by re-running externally-scored nearby reforms and checking the model can reproduce them.

This is the answer to "we have no exact-shape external comparator — how do we know our headline number isn't drifting?" Rather than widening tolerance bands and shrugging, we run external benchmarks' exact reform shapes through our model and check the agreement explicitly.

## When this stage fires

`reform-comparator` calls this agent when its Step 2b external-benchmark agreement check yields **fewer than 2 directly-comparable external sources within ±25%** (the threshold for an unambiguous PASS). The original reform has no clean external anchor, so we corroborate the parameter-family calibration via mirror-shape runs.

`/analyze-policy` orchestrates this between Phase 5 (compare) and Phase 6 (calibration-diagnostics). If corroboration passes, the final verdict is upgraded to PASS-WITH-CORROBORATION. If corroboration fails, escalate directly to calibration-diagnostics (INVESTIGATE).

## Inputs

- `our_reform_dict` — the original reform we just ran (for parameter-family context)
- `our_jurisdiction` — `{country, state?}`
- `benchmark_sources[]` — the Tier 3 think-tank cluster from `prior-scores-finder`, including each source's `reform_shape` and `their_estimate_10yr_billion`
- `our_microsim_result` — Stage 4 output (for the parameter-family sensitivity context)
- `our_baseline_policy_id` — typically 2 (US) or country equivalent

## Process

### Step 1: Pick mirror-shape candidates

**Frozen-registry rule:** candidates come ONLY from `benchmark_sources[]` —
the registry pre-registered before the microsim ran. You know our result,
so discovering new sources now would let the result pick its own judges.
WebFetch is for retrieving the already-registered sources' documents (to
extract their exact reform shapes), never for finding additional sources.
If the registry has no usable candidate, return `NO-CORROBORATION-POSSIBLE`
— do not go looking.

From `benchmark_sources[]`, pick 1-3 candidates with:
- **Same parameter family** as our reform (e.g., SALT cap → SALT cap; CTC amount → CTC amount).
- **A specific reform shape** that's expressable as a reform-dict (vague "raise the cap" without numbers is not usable).
- **A published numeric estimate** (10yr or year-1) we can compare against.
- **Methodology compatible with static microsim** — skip sources that ONLY publish dynamic-scoring numbers (PWBM dynamic), or use them as expected-different.

Prefer candidates with:
1. A baseline that matches ours (no separate baseline-policy build needed).
2. A reform_shape that brackets ours (one below, one above) — gives the strongest sensitivity check.
3. Recent publication (within last 2 years) — older estimates may use outdated calibration targets.

### Step 2: Build each mirror-shape reform-dict

For each candidate, translate its `reform_shape` description into PE parameter paths. Use the same parameter family conventions as the original reform (the locator's work in Stage 2 is reusable). Document each translation in the candidate's `mirror_reform_dict`.

**Filing-status convention** (when a source says "$X single / $Y joint"):
- SINGLE: $X
- HEAD_OF_HOUSEHOLD: $X (TPC/CRFB grouping convention)
- JOINT: $Y
- SURVIVING_SPOUSE: $Y
- SEPARATE: $X (half of joint, equal to single)

If the source explicitly specifies different conventions, follow theirs.

**Phase-out / floor / refundability switches**: if the source mentions a phase-out or floor, replicate it as-is. If unmentioned, keep the deployed default.

### Step 3: Build a baseline policy if needed

Most external sources publish vs "current law" or vs "TCJA extension". Map each:
- **"Current law"** = PE current-law baseline (`policy_id=2` for US). **CRITICAL: check the source's publication date.** If the source published BEFORE a major intervening law was enacted (e.g., TF published May 2025 before OBBBA was signed mid-2025), their "current law" baseline is the pre-intervening-law state, NOT PE's deployed current-law policy. In that case, build the source's effective baseline (typically TCJA-extension) rather than using `policy_id=2`.
- **"TCJA extension"** = TCJA continued indefinitely — build a baseline policy that locks pre-OBBBA TCJA values through the reform window.
- **"Pre-TCJA"** = pre-2018 law — rarely used; build if needed.

Submit each baseline policy via `POST /us/policy` and capture its `policy_id`.

#### Step 3a: Baseline-completeness check (CRITICAL)

A baseline labeled "TCJA-extension" must revert EVERY parameter family the source's analysis implicitly assumed was at TCJA-continued values, not just the family of the reform itself. Building a "TCJA-extension baseline" that only reverts the SALT cap (for example) leaves OBBBA's enhanced standard deduction in place — which means far fewer households itemize than the source assumed, so the SALT cap reform's measured cost is severely understated. The mirror run will drift LOW by 50-80% and falsely appear to fail corroboration.

**Required baseline-completeness enumeration:**

For each external source publishing vs "TCJA-extension" (or any non-current-law baseline), enumerate all parameter families the source's microsim would have differentially measured:

1. **Direct family** — the one the reform touches (SALT cap, CTC amount, EITC match, etc.).
2. **Coupled families** — parameters whose value at the source's publication date differs from current law:
   - SALT reforms: standard deduction, AMT exemption, AMT phase-out, tax brackets, itemized deductions other than SALT.
   - CTC reforms: standard deduction (affects refundability tests), EITC parameters, dependent credit interaction.
   - Tax-rate reforms: standard deduction, AMT, all credits scaled by marginal rate.
3. **Source publication date** — anything enacted AFTER this date should be reverted to its pre-enactment state in the baseline.

Build the baseline policy with ALL coupled families reverted, not just the direct family. Document each parameter family in `baseline_construction_notes`.

If the corroboration baseline is incomplete and a mirror drifts, the drift is on the BASELINE not the model — document this as a known limitation and emit `corroboration_drift_explanation: "baseline_incompleteness"` so the verdict doesn't unjustly escalate to INVESTIGATE.

### Step 4: Submit each mirror-shape reform

```bash
curl -sS -X POST https://api.policyengine.org/us/policy \
  -H "Content-Type: application/json" \
  --data-binary @mirror_reform.json
```

Capture `policy_id`. Then submit the economy run:

```bash
curl -sS "https://api.policyengine.org/us/economy/{mirror_policy_id}/over/{baseline_policy_id}?region=us&time_period=2026&dataset=enhanced_cps"
```

Run multiple mirrors in parallel (background poll loops). Each takes 5-10 min.

### Step 5: Normalize comparison units

The mirror run returns a year-1 budgetary impact. External sources usually publish 10-year numbers. Normalize both to year-1:
- Our year-1 = direct from the mirror run
- Their year-1 = published 10yr / 10 (acknowledge this is a rough average; income growth and inflation make the per-year cost rise within the window)

If the source publishes year-1 directly (rare), use that.

If the source publishes vs a different baseline schedule (e.g., TCJA extension while ours is OBBBA→reversion), the year-1 figures should align AS LONG AS the mirror's baseline is built to match the source's baseline (per Step 3).

### Step 6: Compute corroboration per candidate

```json
{
  "candidate": "CRFB Jan 2025 ($30K/$60K vs TCJA extension)",
  "their_yr1_implied_billion": 82.0,
  "our_yr1_actual_billion": 78.4,
  "delta_pct": -4.4,
  "within_25pct": true,
  "verdict": "CORROBORATED"
}
```

Verdict per candidate:
- `CORROBORATED` — within ±25% (the same threshold reform-comparator uses).
- `DRIFT-LOW` — our number is more than 25% below theirs.
- `DRIFT-HIGH` — our number is more than 25% above theirs.
- `FAILED-TO-RUN` — the mirror run errored, the policy couldn't be built, or the published source's reform_shape was too vague to translate.

### Step 7: Roll up to overall corroboration verdict

| Candidates that CORROBORATED | Overall verdict |
|---|---|
| ≥2 | `CORROBORATED` — data calibration validated; upgrade comparator's verdict |
| 1 (with 1-2 DRIFT in explainable direction) | `PARTIAL-CORROBORATION` — note explanation in archive |
| 0 (all DRIFT) | `CORROBORATION-FAILED` — escalate to calibration-diagnostics; the parameter family likely has a calibration issue regardless of the original reform's specific shape |
| 0 valid candidates (all FAILED-TO-RUN) | `NO-CORROBORATION-POSSIBLE` — fall back to comparator's PASS-WITH-NOTES verdict, document the gap |

### Step 8: Emit a corroboration block

```json
{
  "stage": "5.5_corroboration",
  "candidates_selected": [...],
  "candidates_run": [...],
  "candidates_corroborated": 2,
  "candidates_drift": 0,
  "candidates_failed": 0,
  "overall_verdict": "CORROBORATED",
  "implications_for_original_reform": "Mirror-shape runs at CRFB's $30K/$60K shape and TF's $62K/$124K-with-phase-out shape both fall within ±25% of their published estimates. The model's SALT cap data calibration is validated for caps in the $30K-$124K range. Our $140K extrapolation is anchored.",
  "evidence": {
    "crfb_mirror": {"policy_id": 97835, "yr1_billion": -78.4, "their_yr1_implied": -82.0, "delta_pct": -4.4},
    "tf_mirror": {"policy_id": 97836, "yr1_billion": -53.1, "their_yr1_implied": -52.6, "delta_pct": 1.0}
  }
}
```

## Cost / time budget

Each mirror run: ~6-10 min wall-clock + ~few minutes of analyst time to translate reform_shape. Default to **1-2 mirrors**, escalate to 3 only when the original reform spans a wide cap range AND there are 3 well-shaped candidates.

If `--skip-microsim` was passed to `/analyze-policy`, skip this entire stage — there's no original-reform microsim to corroborate against.

## Edge cases

- **No suitable candidates** — emit `NO-CORROBORATION-POSSIBLE` and document why. Common: the reform's parameter family is novel (e.g., a brand-new state credit), so no external sources have scored anything in this family.
- **All candidates use dynamic scoring** — note this and skip; corroboration requires static-comparable scores.
- **Published estimate is for a different time period** — adjust to year-1 explicitly; if a 5-year window is the only option, divide by 5 instead of 10 and document.
- **Source publishes a range not a point** — use the midpoint and document the range bounds.
- **Mirror-shape reform errors at the API** — typically a parameter path or reform-family-toggle issue; document and treat as FAILED-TO-RUN, do NOT try to redebug the original reform from this failure.

## Hand-off

Returns the corroboration block. `/analyze-policy` Phase 5 (reform-comparator) consumes it and adjusts the final verdict accordingly. `report-logger` appends the corroboration block to the archive's frontmatter and includes a `## Corroboration` section in the body.

## Why this matters

Without this stage, the pipeline's confidence on novel-shape reforms rests on "structurally explainable disagreement" reasoning — which is thin assurance. With mirror-shape runs that the model can reproduce within ±25%, we have independent evidence the underlying data is correctly calibrated for the parameter family. The original reform's headline number is then anchored on actual model validation, not just on tolerance-band gymnastics.
