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
- `--log-to <dest>[,<dest>...]` (override auto-routing; see Phase 8). Examples: `--log-to archive`, `--log-to "archive,issue:policyengine-{country}-data"` (country auto-substituted from `--country`), `--log-to draft:policyengine-app/src/posts/articles/arpa-ctc.md`
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
- **`structural`** — write `/tmp/{policy_id}-structural-backlog.md` with the model-change estimate. Optionally open a GitHub issue against `policyengine-{country}` if `--open-issue`. EXIT.
- **`parametric`** — proceed.

Capture `reform_dict` from the classifier output.

## Phase 3 — Find anchor scores

Invoke `prior-scores-finder` (loads the `policyengine-prior-scores` skill internally):

```
prior-scores-finder
  reform=<provisions+description>
  jurisdiction=<jurisdiction>
```

Returns `anchors[]`. If empty, surface "novel reform — no PE prior found" in the final report. The comparison will rely on fiscal notes / think-tank scores.

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

## Prior anchors
| Prior | Year | Cost | Poverty Δ | URL |
|---|---|---|---|---|
| Restoration of ARPA CTC | 2023 | $100B/yr | -37% child | ... |

## Our microsim result
| Metric | Value |
|---|---|
| 10yr cost | $1,450B |
| Child poverty Δ | -34.1% |
| ... | ... |

## Comparison
**Verdict:** PASS
Headline metrics within tolerance band. See normalization notes.

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
