---
description: End-to-end reform pipeline in one command — scan the news for a modelable reform in a topic area, score and verify it with /analyze-policy (incl. the data-calibration check), then publish to the bill tracker or a dashboard.
---

# Reform Pipeline: $ARGUMENTS

The single-command version of the CRM research pipeline: discover → score →
verify → publish, with confirmation gates inline instead of the Command
Center. Use this when you want to drive the whole chain yourself for a topic
("healthcare", "child tax credit", "Utah income tax") rather than waiting for
the newsroom's scheduled discovery.

## Arguments

`$ARGUMENTS` should contain:
- **Topic or reform** (required) — a policy area to scan for ("healthcare",
  "social security taxation"), OR a concrete reform/bill id ("UT SB60") to
  skip discovery and go straight to scoring.
- **Options**:
  - `--country {us|uk|ca}` (default `us`)
  - `--horizon {1|10}` (default `1`; 10-year adds 15-25 min of API compute)
  - `--publish {auto|tracker|dashboard|none}` (default `auto` — route by the
    standard rules; `none` stops after the verified analysis)
  - `--auto-confirm` — skip the confirmation gates (headless / CI use)
  - `--dry-run` — publication workflows run with `dry_run=true` (compute +
    validate, no Supabase writes / PRs / pushes)

**Examples:**
```
/reform-pipeline healthcare
/reform-pipeline "social security taxation" --publish dashboard --horizon 10
/reform-pipeline "UT SB60" --publish tracker --dry-run
```

## Phase 0 — Clarify (skipped with `--auto-confirm` or when fully specified)

Before scanning anything, resolve what's underspecified with ONE
AskUserQuestion round (ask only the questions the arguments left open —
a concrete bill id leaves nothing to ask):

1. **Sources** (multi-select): where should discovery look?
   - CRM newsroom (needs `CRM_API_URL` + `CRM_API_TOKEN`; only offer when reachable)
   - Web news search (last 14 days)
   - Bill trackers (congress.gov federal search; state bills named in coverage)
   - Default: all available.
2. **Scope** (when the topic doesn't imply it): federal, a specific state,
   or either — this changes both where to look and the eventual publication
   route (state → tracker, federal → dashboard).
3. **Publication intent** (when `--publish` wasn't passed): auto-route /
   bill tracker / dashboard / analysis only. Sets the `--publish` value.
4. **Recency window** only if the user's phrasing suggests older material
   ("that bill from March") — default 14 days otherwise, don't ask.

With `--auto-confirm`: all available sources, either scope, auto-route,
14 days.

## Phase 1 — Discover (skipped when a concrete bill/reform was given)

Find the single most prominent, concrete, MODELABLE reform in the topic:

1. **Scan the sources chosen in Phase 0** (parallel):
   - WebSearch: recent news (window from Phase 0) on `<topic> bill OR reform OR tax OR benefit <country>` — prefer coverage that names a specific bill.
   - For US topics, also check bill trackers: congress.gov search for the topic (federal), and note any state bills the coverage names.
   - If the CRM newsroom API is reachable (`CRM_API_URL` + `CRM_API_TOKEN` env set), query it for recent high-relevance items on the topic and merge them into the pool. Optional — absence is normal outside the CRM environment.
2. **Extract the reform** using the same conservatism as the CRM's discovery:
   a concrete parametric change (rates, thresholds, credit amounts,
   eligibility limits). Prefer a bill identifier (`US HR904`, `UT SB60`) over
   a prose description — the scoring stage fetches bill text itself.
   Structural proposals (brand-new programs, novel administrative rules) are
   NOT modelable — say so and stop rather than burning a scoring run.
3. **Dedup before proposing** (both checks):
   - `/prior-analysis <reform>` — did an /analyze-policy run already score this?
   - The public bill tracker (read-only): does `state-legislative-tracker`'s `research` table already cover it? (Query the tracker Supabase anon endpoint or check policyengine.org/us/bill-tracker.)
   Already covered → report where, and stop.

**Gate 1 (skip with `--auto-confirm`):** present the discovered reform —
title, the exact scoring command, source links — via AskUserQuestion:
proceed / pick a different candidate / stop.

## Phase 2 — Score & verify

Run the full scoring pipeline inline:

```
/analysis-tools:analyze-policy "<reform>" --country <country> --horizon <horizon> --auto-confirm
```

This covers: bill text → provisions → parameter mapping → classification →
prior scores → microsim → comparison against external anchors → **the Phase
5.6 data-calibration check** (is the populace release well-calibrated for
this reform's variables?) → report + archive.

Branch on the verdict:
- **PASS / PASS-WITH-NOTES / PASS-WITH-CORROBORATION** → continue to Phase 3.
- **INVESTIGATE** → report the calibration diagnosis and STOP — unverified
  numbers never publish. The auto-filed policyengine-{country}-data issue is
  the follow-up thread.
- **structural / not-possible** → report why and STOP.

## Phase 3 — Route & publish

Apply the standard routing rules (identical to the CRM publication router):
- non-US, federal US, missing reform_dict, |10yr| ≥ $50B, |yr1| ≥ $10B, or
  heavy coverage → **dashboard**
- otherwise (routine state bill) → **bill tracker**
- `--publish tracker|dashboard` overrides; `--publish none` stops here.

**Gate 2 (skip with `--auto-confirm`):** show the route, the literal workflow
inputs, and what "publish" means for that route (tracker: hidden `in_review`
entry + a bill-review PR whose merge publishes; dashboard: a new repo is
built and pushed, deploy stays manual). Confirm before dispatching.

Dispatch (requires `gh` with repo write access):

```bash
# tracker route
gh workflow run publish-reform.yml --repo PolicyEngine/state-legislative-tracker \
  -f id=<slug> -f state=<state> -f label="<label>" -f reform_json='<reform_dict>' \
  -f title="<title>" -f description="<provisions summary>" -f tags="<tags>" \
  -f source_url="<primary source>" -f dry_run=<--dry-run?>

# dashboard route
gh workflow run create-dashboard.yml --repo PolicyEngine/policyengine-skills \
  -f brief="<brief + validation context (verdict, costs, anchors)>" \
  -f repo_name=<slug>-dashboard -f reform_json='<reform_dict>' \
  -f horizon=<horizon> -f dry_run=<--dry-run?>
```

Then watch to completion and report the outcome links:

```bash
gh run watch --repo <repo> --exit-status
gh run download <run-id> --name publication-result --dir /tmp/pub-result
```

## Final output

A summary the analyst can forward: the reform, the verdict with headline
numbers, the calibration-check note, what was published where (PR link /
repo link), and the remaining human step (merge the bill-review PR, or
`/deploy-dashboard`).

## Boundaries

- One reform per run — the highest-confidence candidate. Re-run for more.
- Never publishes anything that didn't PASS verification.
- The CRM's Command Center remains the preferred entry for
  newsroom-discovered reforms (its dedup and audit trail persist in the
  manager_actions table); this command is for analyst-driven, on-demand runs.
