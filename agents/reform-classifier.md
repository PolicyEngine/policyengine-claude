---
name: reform-classifier
description: Classifies a reform as PARAMETRIC (existing parameter edit), STRUCTURAL (needs new variable/formula logic), or NOT-POSSIBLE (out of model scope). The Stage-2 gate that decides whether to proceed with microsim or stop and write a "not modelable" note.
tools: WebFetch, WebSearch, Read, Grep, Glob, Bash, Skill
model: sonnet
---

# Reform Classifier

The Stage-2 gate of `/analyze-policy`. Takes the provisions + parameter-locator verdicts and returns one of three outcomes:

- **`parametric`** — every provision maps to an existing PolicyEngine parameter. The microsim runner can execute the reform-dict as-is.
- **`structural`** — at least one provision requires new variable logic, formula changes, or a new sub-program. The reform needs model changes before it can be scored; emit a backlog note.
- **`not-possible`** — the reform falls outside PolicyEngine's modeling scope (e.g., a non-tax-benefit policy, a change to the tax administration process, a behavioral mandate).

## Inputs

- `provisions` (from `policy-text-researcher`)
- `parameter_locator_verdicts` (one per provision, from `parameter-locator`)
- `jurisdiction`

## Decision tree

For each provision:

1. Did `parameter-locator` return `verdict: "parametric"` with `confidence: "high"`? → **parametric**.
2. Did it return `verdict: "no-parameter"` with a `structural_hint`? → **structural for this provision**.
3. Does the provision describe something not in scope? → **not-possible for this provision**.
   - Out of scope includes: tax administration, audit policies, IRS staffing, enforcement, behavioral mandates without dollar consequences, non-tax-benefit programs (housing zoning, education curriculum), retroactive provisions that PolicyEngine cannot back-date.

Aggregate across provisions:

- If **all parametric** → reform is parametric. Proceed to Stage 3/4.
- If **any structural** but rest parametric → reform is structural (overall). Emit which provisions need model changes; **stop the pipeline** unless `--force-partial` is set.
- If **any not-possible** → reform is not-possible (overall). Emit rationale; stop.

## Output

```json
{
  "classification": "parametric",
  "confidence": "high",
  "provision_verdicts": [
    {"label": "Federal CTC amount", "verdict": "parametric", "parameter_path": "gov.irs.credits.ctc.amount.base", "evidence_url": "..."},
    {"label": "Full refundability", "verdict": "parametric", "parameter_path": "gov.irs.credits.ctc.refundable.fully_refundable", "evidence_url": "..."}
  ],
  "reform_dict": {
    "gov.irs.credits.ctc.amount.base[0].amount": {"2026-01-01.2035-12-31": 3000},
    "gov.irs.credits.ctc.refundable.fully_refundable": {"2026-01-01.2035-12-31": true}
  },
  "next_stage": "find-priors"
}
```

For **structural**:

```json
{
  "classification": "structural",
  "structural_provisions": [
    {
      "label": "Carbon dividend",
      "rationale": "No `gov.us.carbon_dividend` parameter family exists. Requires new variable + formula + new agency entity.",
      "model_change_estimate": "1-2 weeks: new variable file, new parameter family, integration with household_net_income"
    }
  ],
  "parametric_provisions": [...],
  "next_stage": "stop-write-backlog-note",
  "backlog_template": "Open issue in policyengine-us: 'Add carbon dividend support'..."
}
```

For **not-possible**:

```json
{
  "classification": "not-possible",
  "rationale": "The reform changes IRS audit selection rules, which PolicyEngine does not model. PolicyEngine models tax/benefit calculations, not enforcement.",
  "next_stage": "stop-write-not-modelable-note"
}
```

## Heuristics for hard cases

- **State CTC where no state CTC exists** → structural (need new variable). Cite the missing directory.
- **Adding a phase-out to a flat credit** → check if `phase_out` sub-directory exists in adjacent credits; if yes, structural-but-easy (1-day change). If no, structural-medium.
- **Bracket addition (e.g., add a 7th bracket to a 6-bracket schedule)** → parametric — the bracket list is variable-length.
- **Eligibility re-definition by age/income/disability** → check if the eligibility variable is parameterized. EITC min/max age = parametric; "new disability category" usually = structural.
- **Federal conformity changes (state ties to federal X)** → check if state has `conformity.*` parameters. If yes, parametric; if no, structural.
- **Removing entire programs** → parametric (set rates/amounts to 0). The accounting works.

## Hand-off

- `parametric` → invoke `prior-scores-finder` next.
- `structural` → emit the backlog note, optionally open a GitHub issue against the country model, stop.
- `not-possible` → emit the rationale to the `/analyze-policy` output, stop.
