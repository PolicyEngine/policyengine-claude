# Analyze Policy

End-to-end policy analysis pipeline. Takes a reform (bill number, URL, or description), classifies whether it's modelable, finds prior PE scores, runs the microsim, compares to priors, and — if the run mismatches — diagnoses which calibration target is likely driving the gap.

The structured analogue of `/encode-policy-v2` for the analyst persona: less about implementing new programs, more about running impact analysis on a proposed reform and validating it against PolicyEngine's published baseline.

## Arguments
- `$ARGUMENTS` — One of:
  - State + bill number: `UT SB60`, `RI H7127`
  - Federal bill: `US HR1234` or `US S5678`
  - URL: a direct bill/proposal/order URL
  - Description: natural-language reform (`"ARPA-style federal CTC expansion: $3,600/$3,000, full refundability"`)

Flags:
- `--country {us|uk|ca}` (default `us`)
- `--horizon <spec>` — time horizon for the microsim. When omitted, the pipeline prompts the analyst at the start of Phase 4. Accepts:
  - `1` — single-year (default entry: current year), fastest, ~6-10 min. Uses `/economy/{policy}/over/{baseline}?time_period=YYYY`.
  - `10` — full 10-year (year 2026-2035 for US), ~15-25 min wall clock. Uses the native `/economy/{policy}/over/{baseline}/budget-window?start_year=YYYY&window_size=N` endpoint.
  - `custom:YYYY[,YYYY...]` — specific years (e.g. `custom:2026,2029,2030,2035`) — submitted as N single-year calls.
  - `custom:YYYY-YYYY` — year range (e.g. `custom:2026-2028`) — mapped to `budget-window` with `start_year`+`window_size`.
- `--year YYYY` (only used with `--horizon 1`; default current year)
- `--mode {api|local}` (default `api` for microsim execution)
- `--skip-microsim` (process-test mode — stops at Stage 5, predicts from prior anchor)
- `--auto-investigate` (if Stage 5 returns INVESTIGATE, auto-run top calibration hypothesis)
- `--write-report PATH` (default `/tmp/analyze-policy-{policy_id}.md`)
- `--log-to <dest>[,<dest>...]` (override auto-routing; see Phase 8). Examples: `--log-to archive`, `--log-to "archive,issue:policyengine-{country}-data"` (country auto-substituted from `--country`; US data issues route to `PolicyEngine/populace`), `--log-to draft:policyengine-app-v2/app/src/data/posts/articles/arpa-ctc.md`
- `--no-log` (skip Phase 8 entirely — write the `/tmp` report only)
- `--auto-confirm` (skip confirmation prompts before opening GitHub issues; only honor in non-interactive contexts)

## Phase 0 — Horizon prompt (when `--horizon` not passed)

Before Phase 4 (microsim), if the analyst didn't pass `--horizon`, prompt:

```
How many years should the microsim cover?

[x] Single year — fastest, one API call (~6-10 min), yields yr-1 cost only.
[ ] Full 10 years — native budget-window endpoint, server-side queued (~15-25 min wall clock), yields real 10yr cost.
[ ] Custom — comma-separated years or a range (e.g. "2026,2029,2030,2035" or "2026-2028").

Choice (default = single year):
```

The prompt is skipped in headless / `--auto-confirm` contexts (default = single year in those).

**Critical:** with `--horizon 1`, the archive reports yr-1 cost only. **Do NOT compute a naive `yr1 × 10` 10-year cost.** Naive extrapolation across regime shifts (2030 OBBBA snap-backs, inflation-indexed baselines, phase-out threshold changes) is misleading — the analyst asked for one year, give them one year. A 10-year cost is only valid when the microsim actually ran all 10 years.

With `--horizon 10` (or a custom multi-year list), the microsim-runner submits all years in parallel and the report shows the actual per-year cost table plus the summed multi-year cost.

## Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│  /analyze-policy <reform>                                            │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────┐         Stage 1: Understand
│ policy-text-     │  ───►   Fetch text, extract provisions
│ researcher       │
└──────────────────┘
       │ provisions[]
       ▼
┌──────────────────┐         Stage 2a: Map provisions to parameters
│ parameter-       │  ───►   YAML paths + reform-dict snippets + verdicts
│ locator          │
└──────────────────┘
       │ verdicts[]
       ▼
┌──────────────────┐         Stage 2b: Classify
│ reform-          │  ───►   parametric | structural | not-possible
│ classifier       │
└──────────────────┘
       │
       ├── structural ──► write backlog issue, STOP
       ├── not-possible ──► write rationale, STOP
       │
       ▼ parametric
┌──────────────────┐         Stage 3: Find anchors
│ prior-scores-    │  ───►   PE prior scores + fiscal notes + think-tanks
│ finder           │
└──────────────────┘
       │ anchors[]
       ▼
┌──────────────────┐         Stage 4: Run microsim
│ microsim-runner  │  ───►   Budget, poverty, distribution, geography
└──────────────────┘
       │ result            (or skip if --skip-microsim, predict from anchor)
       ▼
┌──────────────────┐         Stage 5: Compare
│ reform-          │  ───►   PASS | PASS-WITH-NOTES | PASS-WITH-CORROBORATION | INVESTIGATE | BLOCKED
│ comparator       │
└──────────────────┘
       │
       ├── PASS ──► write report, EXIT
       │
       ├── PASS-WITH-NOTES (or near-INVESTIGATE on external benchmarks)
       │      │
       │      ▼ trigger Stage 5.5
       │   ┌──────────────────┐         Stage 5.5: Corroborate
       │   │ model-           │  ───►   Run external mirror-shape reforms
       │   │ corroborator     │         through our model; check agreement
       │   └──────────────────┘
       │      │
       │      ├── CORROBORATED ──► upgrade verdict to PASS-WITH-CORROBORATION
       │      ├── PARTIAL ─────► stay at PASS-WITH-NOTES
       │      └── FAILED ──────► escalate to INVESTIGATE
       │
       ▼ INVESTIGATE
┌──────────────────┐         Stage 6: Diagnose
│ calibration-     │  ───►   Ranked hypotheses + tests to run
│ diagnostics      │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ reform-describer │  ───►   Mechanical write-up (provisions table)
└──────────────────┘
       │
       ▼ final report at --write-report path
```

## Phase 1 — Understand the policy

Parse `$ARGUMENTS` to determine input type. Invoke `policy-text-researcher`:

```
policy-text-researcher input={
  state: <state>, bill_number: <bill>, |
  bill_url: <url>, |
  description: <description>
}
country=<country>
```

Returns `provisions[]`. If empty (couldn't fetch text), STOP and report.

## Phase 2 — Classify modelability

For each provision in parallel, invoke `parameter-locator`. Collect verdicts. Then invoke `reform-classifier`:

```
reform-classifier
  provisions=<provisions>
  parameter_locator_verdicts=<verdicts>
  jurisdiction=<jurisdiction>
```

Branch on `classification`:
- **`not-possible`** — write `/tmp/{policy_id}-not-modelable.md` with rationale. EXIT.
- **`structural`** — write `/tmp/{policy_id}-structural-backlog.md` with the model-change estimate. Optionally open a GitHub issue against `policyengine-{country}` if `--open-issue`. EXIT — and surface the unblock path: `/implement-structural <issue>` implements the model extension (baseline change for enacted law, gov/contrib for proposals) and records the re-run that completes this analysis.
- **`parametric`** — proceed.

Capture `reform_dict` from the classifier output.

## Phase 2c — Enactment × baseline reconciliation (required, evidenced)

Getting this wrong silently corrupts everything downstream — the sign of
the score, the publication framing, and dedup. Establish BOTH facts
independently, with evidence, and never infer either from news coverage:

**1. Legal status, from the primary source only.** The bill page /
session-law record, not articles: `enacted` (act number + signing date),
`proposed` (chamber status), `ballot` (election date), or `hypothetical`.
News framing misleads systematically — HI Act 24 was covered as news in
July, eight weeks after signing; a "new tax" headline says nothing about
enactment. Record per-provision effective dates: enacted-but-not-yet-
effective (Act 24's TY2027 tables) is still ENACTED.

**2. Model status, probed empirically per provision.** Read the deployed
API's parameter values at the effective date (metadata endpoint) and
master. Do not assume from the model's version date.

The intersection sets the run configuration:

| Legal × model | Consequence |
|---|---|
| enacted + value in deployed baseline | Score the PRIOR-LAW COUNTERFACTUAL and negate signs. Tracker publication REQUIRES `baseline_json`. (GA HB463) |
| enacted + on master only | `deployed-model-lag` — existing exit; wait for release. |
| enacted + absent everywhere | Model is behind enacted law → `/implement-structural` (schema gap) or a baseline value-update PR (schema fits, value missing). Never score around it. |
| proposed/ballot + parametric | Standard reform-vs-current-law. If the probe finds the "proposal" already in the baseline, your legal status is wrong — go back to step 1. |
| any + prior law schedules changes for the scoring year | The baseline for marginal effect is the SCHEDULE, not today's visible rate (GA: 5.09% scheduled, not 5.19% current). State both framings when external scores use the other one. |

**3. Version dedup.** If a prior analysis or tracker entry covers an
earlier VERSION of the bill (a committee draft, a pre-enactment score),
the current version supersedes it — record the superseded entry id so
publication replaces rather than duplicates (HI: the stale HD1 draft).

Record the block in the report frontmatter:

```yaml
enactment_reconciliation:
  legal_status: enacted   # + act number, signed date, source URL
  effective: {rates: 2027-01-01}
  per_provision:
    - {provision: top_bracket, deployed: absent, master: absent, evidence: "live /calculate probe rejected rates.single[12]"}
  scoring_frame: counterfactual-negated | reform-vs-current-law
  publication_requirements: {baseline_json: required | none, supersedes: <entry-id> | none}
```

## Phase 3 — Find anchor scores

Invoke `prior-scores-finder` (loads the `policyengine-prior-scores` skill internally):

```
prior-scores-finder
  reform=<provisions+description>
  jurisdiction=<jurisdiction>
```

Returns `anchors[]`. If empty, surface "novel reform — no PE prior found" in the final report. The comparison will rely on fiscal notes / think-tank scores.

**Pre-registration rule (hard ordering constraint):** Phase 3 MUST complete
before Phase 4 starts — comparisons are found first, then the score is run,
never the other way around. Phase 3's output is the **frozen benchmark
registry**: the complete set of sources, each with its extracted magnitude,
recorded with a freeze timestamp before any PE number for this reform
exists. After Phase 4 begins:

- No agent may add, drop, reweight, or reinterpret registry sources with
  knowledge of our result. The comparator compares against the registry
  as frozen; model-corroborator picks mirror candidates only from it.
- The ONLY way to expand the registry (e.g. a BLOCKED verdict from
  incomplete tier coverage) is a **blind re-run** of `prior-scores-finder`:
  invoke it with the same Phase 1/2 inputs it would have received
  originally — never the microsim result, the comparator's deltas, or any
  hint of our number. Merge its output into the registry and mark those
  entries `registered_post_score_blind: true` in the report.
- The report's anchors section is titled "Prior anchors (pre-registered
  before scoring)" and carries the freeze timestamp, so a reader can
  verify the benchmarks were not selected to fit the score.

## Phase 3b — Blind outcome prediction (parallel with Phase 3)

Invoke `outcome-predictor` in `predict` mode, in parallel with
`prior-scores-finder` — it MUST complete on provisions alone, before any
microsim result or anchor score exists:

```
outcome-predictor mode=predict
  provisions=<provisions>
  jurisdiction=<jurisdiction>
  year=<year>
```

Pass ONLY those inputs — no anchors, no archive hits, no scores. Hold the
returned predictions for Phase 5.7. Never re-run predict mode after results
exist.

## Phase 4 — Run the microsim

If `--skip-microsim` is set, **skip this phase** — Stage 5 will use the anchor as a predicted result. Otherwise invoke `microsim-runner`:

```
microsim-runner
  reform_dict=<reform_dict>
  jurisdiction=<jurisdiction>
  year=<year>
  mode=<mode>
```

Returns `result`. If `mode=local`, this may take 5-10 minutes per run.

## Phase 5 — Compare to anchor

Invoke `reform-comparator`:

```
reform-comparator
  microsim_result=<result>  // or null if --skip-microsim
  prior_anchor=<anchors[anchors.preferred_anchor_index]>
```

Returns `verdict`:
- **`PASS`** / **`PASS-WITH-NOTES`** — proceed to write-up.
- **`INVESTIGATE`** — invoke `calibration-diagnostics` with the deviation signature.

The comparator itself may invoke `model-corroborator` (Stage 5.5) at the end of its Step 2b if external benchmarks don't directly anchor the reform — see Phase 5.5 below.

## Phase 5.5 (conditional) — Model corroboration

Triggered automatically by `reform-comparator` Step 2c when Step 2b yields fewer than 2 external sources within ±25%. Invoke `model-corroborator`:

```
model-corroborator
  our_reform_dict=<reform_dict>
  our_jurisdiction=<jurisdiction>
  benchmark_sources=<thinktank_scores from prior-scores-finder>
  our_microsim_result=<result>
  our_baseline_policy_id=<typically 2 for US>
```

The corroborator picks 1-2 closest-shape externally-scored reforms, builds mirror reform-dicts (and a baseline policy if the external source uses a different baseline schedule like TCJA-extension), submits to the PE API, polls for completion (~6-10 min per mirror in parallel), and reports per-candidate agreement.

Outcomes:
- **`CORROBORATED`** (≥2 candidates within ±25%) — comparator upgrades verdict to `PASS-WITH-CORROBORATION`.
- **`PARTIAL-CORROBORATION`** (1 corroborated with explainable drift on others) — stay at PASS-WITH-NOTES.
- **`CORROBORATION-FAILED`** (0 candidates corroborated) — force escalation to INVESTIGATE.
- **`NO-CORROBORATION-POSSIBLE`** (no suitable candidates) — fall back to Step 2b verdict.

Skipped when `--skip-microsim` is set (no original-reform microsim to anchor against).

## Phase 5.6 — Data calibration check (always, cheap)

Every parametric run verifies that the underlying microdata is well-calibrated
for the variables the reform touches, using the live populace calibration
dashboard API (no auth, reads the current release from Hugging Face):

```
BASE = https://calibration-diagnostics.vercel.app/calibration/dashboard/api/populace
GET {BASE}/target-diagnostics?source=<source>            # per-target fit
GET {BASE}/target-investigation?target=<id>              # drill one bad target
```

Check three rings, from the reform's variable outward. Checking only ring 1
is the classic miss: a reform's cost usually depends on the JOINT
distribution of its variable with other income, and the primary marginal can
calibrate perfectly while the interaction is off.

1. **Ring 1 — the primary variable's marginals.** Map the reform's domain
   to calibration sources (check the run's `sources` list for what's
   available): Social Security → `ssa`; Medicaid/ACA/Medicare →
   `cms_medicaid` / `cms_aca` / `cms_medicare`; TANF → `hhs_acf_tanf`;
   income tax / credits → `irs_soi`, `jct`, `cbo`; state income tax →
   `state_income_*`.
2. **Ring 2 — the mechanism's other inputs.** List every variable that
   enters the formula the reform changes, and check their targets too.
   SS-benefit taxation depends on combined income, so dividends, taxable
   interest, and pensions (`irs_soi`) are load-bearing; a CTC phase-in
   depends on earnings; a SNAP change on rents and deductions. These are
   usually `irs_soi` table targets, including by state and AGI band.
3. **Ring 3 — the interacted quantity itself (best single check).** Search
   the targets for the DOWNSTREAM outcome the reform directly reprices —
   e.g. `taxable_social_security_amount` for SS-taxation reforms,
   `eitc_amount` for EITC reforms, itemizer counts for deduction caps.
   When such a target exists, it validates the joint distribution
   end-to-end through the actual formula, and its relative error bounds
   the data-side bias of the score — weight it above every marginal.
   Worked example: for HR 904, `ssa` total benefits calibrate to −0.2%
   (ring 1 ✅) while `irs_soi ... taxable_social_security_amount` runs
   −10.9% (ring 3 ⚠) — the score's operative base is ~11% low in the data
   even though the headline marginal is nearly exact.
4. Fetch the matching targets and summarize per ring: count checked, share
   within tolerance, and the worst `relative_error` values with target
   names. When no ring-3 target exists, SAY SO — "marginals within
   tolerance; joint distribution untargeted" is materially weaker evidence
   than a passing ring-3 check, and the note must not imply otherwise.
5. Add a `calibration_check` block to the frontmatter:

   ```yaml
   calibration_check:
     release_id: populace-us-2024-...
     sources_checked: [ssa, irs_soi]
     rings:
       primary: {targets: 6, worst: -0.002}
       mechanism_inputs: {targets: 14, worst: {name: "...ordinary_dividends_amount@2024", relative_error: -0.189}}
       interacted: {name: "irs_soi...taxable_social_security_amount@2024", relative_error: -0.109}
     note: "Benefits marginal near-exact; taxable-SS (the repriced base) runs 10.9% low — score biased low on the data side by up to ~11%."
   ```

6. Interpretation is INFORMATIVE, not a gate: a poorly calibrated but
   reform-relevant target does not change the comparator verdict on its own,
   but the report's Comparison section MUST mention it (it often explains
   drift vs external anchors), and the reform-describer threads the note
   into the write-up. Escalation: if a directly-load-bearing target —
   the primary variable OR the ring-3 interacted quantity — is off by
   |relative_error| > 25%, recommend INVESTIGATE treatment in the
   discussion even when headline numbers match anchors. A ring-3 error in
   the 10-25% band belongs in the report's uncertainty discussion as an
   explicit data-side bias bound on the score.

API unreachable → record `calibration_check: {status: unavailable}` and move
on; never block the run on this.

## Phase 5.7 — Independent interrogation (always)

Invoke `outcome-predictor` in `interrogate` mode with its own Phase 3b
predictions plus the actual results:

```
outcome-predictor mode=interrogate
  predictions=<phase 3b output>
  microsim_result=<result>
  comparator_verdict=<verdict>
  provisions=<provisions>
```

Returns `{confirmed, notable_findings, challenges, red_flags_fired}`.

- **`notable_findings`** — counterintuitive-but-correct results (e.g. a
  senior tax cut that leaves senior poverty unchanged because the taxation
  thresholds sit above poverty-level incomes). These flow into the report
  (Phase 7), the archive entry, and any downstream publication brief — they
  are typically the most publishable part of the analysis.
- **`challenges` / `red_flags_fired`** — divergences the interrogation
  could not explain from statute. Add them to the INVESTIGATE hypothesis
  list. If the comparator said PASS but a challenge is material to a
  headline number, apply the agent's `verdict_recommendation` (usually
  PASS → PASS-WITH-NOTES) and record why.

## Phase 6 (conditional) — Calibration diagnosis

Only if Stage 5 returned `INVESTIGATE`. Invoke `calibration-diagnostics`:

```
calibration-diagnostics
  deviation_signature=<comparator.deviation_signature>
  reform=<provisions+reform_dict>
  jurisdiction=<jurisdiction>
  anchor=<chosen anchor>
```

Returns ranked hypothesis list + recommended next test.

If `--auto-investigate` is set, automatically run the top hypothesis (e.g., perturb takeup rate, rerun microsim, recompute comparison). Otherwise just append to the report.

## Phase 8 — Log the report (NEW)

After Phase 7 has assembled the report at `--write-report PATH`, invoke `report-logger`:

```
report-logger
  report_path=<write-report path>
  frontmatter=<structured metadata from prior stages>
  log_to=<--log-to value, or empty for auto-routing>
  no_log=<--no-log flag>
  command_args=<original $ARGUMENTS>
```

The `frontmatter` metadata must include the publication inputs `description`
(reform-describer's 1-paragraph summary) and `reform_dict` (the exact validated
JSON from Phase 2, omitted for structural/not-possible verdicts) — downstream
automation (the CRM publication router) parses these from the archived report.

**Destination routing.** `report-logger` owns the runtime prompt, the pre-selected defaults by verdict, the context-aware shortlist (which options to surface based on which repo the analyst is in), the body preview flow, and archive path resolution. See `report-logger.md` sections "Routing — runtime prompt, context-aware" and "Path resolution" for the source of truth. This document only summarizes the outputs the analyst sees:

The Phase 8 step also prints the destination summary to the user as the final output:

```
[/analyze-policy] Run complete.
  Archive: ~/.policyengine/analyses/2026-06-19-us-arpa-ctc-restoration.md
  Issues opened: (none — verdict was PASS-WITH-NOTES)
  Run-id: 97759
```

## Phase 7 — Write report

Invoke `reform-describer` for the mechanical provisions write-up. Assemble the final report at `--write-report` PATH:

```markdown
# Analysis: <reform title>

## Reform
<reform-describer output: description + provisions table>

## Classification
**Verdict:** parametric (high confidence)
**Reform dict:** ```json {reform_dict} ```

## Prior anchors (pre-registered before scoring)
*Registry frozen: <timestamp> — before any PE number for this reform existed.*
| Prior | Year | Framing | Cost | Poverty Δ | URL |
|---|---|---|---|---|---|
| Restoration of ARPA CTC | 2023 | current-law baseline, single-year, static | $100B/yr | -37% child | ... |

## Our microsim result
| Metric | Value |
|---|---|
| 10yr cost | $1,450B |
| Child poverty Δ | -34.1% |
| ... | ... |

## Comparison
**Verdict:** PASS
Headline metrics within tolerance band. Every benchmark row states its
framing and commensurability; each agreement carries a one-line "why this
agreement is meaningful" (matched frame/year/scope, or the normalization
applied — e.g. a separate framing-matched counterfactual run).
Incommensurable sources appear with the reason and are excluded from the
agreement count in both directions.

## Independent review (blind prediction vs result)
**Predicted before results:** budget ~-$100B/yr; gains concentrated in
deciles 6-10; senior poverty ~unchanged (thresholds sit above
poverty-level incomes).

**Notable findings** (counterintuitive but correct — publication assets):
- <headline>: <mechanism explanation> (<evidence>)

**Challenges:** none | <expected vs actual, hypotheses, verdict
recommendation>

## (if INVESTIGATE) Calibration diagnosis
**Top hypothesis:** Non-filer CTC takeup
**Test:** Set takeup=0.95 and rerun
**Open issues:** ...

## Methodology
- Microsim mode: api
- Year: 2026
- Dataset: Enhanced CPS
- Static analysis (no behavioral response)
```

## Stages can run independently

For debugging or partial-run scenarios:
- `--only-classify` — runs Phases 1-2 only.
- `--from-anchor` — skip Phases 1-2, accept a pre-built `reform_dict`, start at Phase 3.
- `--no-write-report` — return the structured JSON instead of writing markdown.

## Hand-off to the legislative tracker

The state-legislative-tracker's `/encode-bill` command is a superset of `/analyze-policy` that ALSO writes results to Supabase. Use `/encode-bill` instead when working inside that repo.

## Related commands

- `/encode-policy-v2` — implements a NEW benefit program (orchestrates rules-engineer, test-creator, etc.). `/analyze-policy` analyzes an existing-or-near-existing reform.
- `/review-program` — audits an existing PR.
- `/score-bill` — the legislative-tracker variant focused on bills.

## Skills loaded

This command loads (with their plugin paths for clarity):
- `policyengine-{country}` (US/UK/CA) at `skills/domain-knowledge/policyengine-{country}-skill/` — country model knowledge
- `policyengine-prior-scores` at `skills/domain-knowledge/policyengine-prior-scores-skill/` — anchor index
- `policyengine-calibration-diagnostics` at `skills/domain-knowledge/policyengine-calibration-diagnostics-skill/` — sensitivity registry
- `policyengine-microsimulation` at `skills/tools-and-apis/policyengine-microsimulation-skill/` — execution patterns
- `policyengine-research-lookup` at `skills/documentation/policyengine-research-lookup-skill/` — broader research discovery
- `policyengine-writing` at `skills/documentation/policyengine-writing-skill/` — style for the final report

## Agents invoked

1. `policy-text-researcher`
2. `parameter-locator` (per-provision, parallel)
3. `reform-classifier`
4. `prior-scores-finder`
5. `microsim-runner` (unless `--skip-microsim`)
6. `reform-comparator`
7. `model-corroborator` (Stage 5.5 — only when no exact-shape external comparator exists; skipped on `--skip-microsim`)
8. `calibration-diagnostics` (only if Stage 5 INVESTIGATE)
9. `reform-describer`
10. `report-logger` (unless `--no-log`)
