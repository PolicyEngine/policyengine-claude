---
description: Implements the model extension behind a STRUCTURAL /analyze-policy verdict — baseline change for enacted law, gov/contrib reform for proposals — opens the policyengine-{country} PR, and records the re-run that completes the original analysis.
---

# Implement structural: $ARGUMENTS

When `/analyze-policy` classifies a reform as **STRUCTURAL**, the pipeline
stops with a backlog issue. This command picks that issue up and implements
the model extension, so the original analysis can re-run and publish.

## Arguments

`$ARGUMENTS` should contain ONE of:
- A structural backlog issue — `policyengine-us#9051` or the issue URL
- A structural-backlog report path — `/tmp/<id>-structural-backlog.md`
- The archived structural analysis — `analyses/<date>-<id>-structural.md`

Options:
- `--draft` — open the PR as draft
- `--no-rerun` — skip recording the pending re-run command

## Phase 1 — Read the spec and choose the mode

Read the backlog issue/report. It carries the classifier's findings: which
parameters/variables are missing, the empirical verification, and the size
estimate. Then choose:

- **Enacted law → BASELINE change.** The statute is current law; the model
  is simply behind. Edit `policyengine_us/parameters/...` (and variables if
  needed) directly — e.g. HI SB3125/Act 24: append bracket `[12]` @ 13% to
  the five `gov.states.hi.tax.income.rates.*` scales, inert before
  2027-01-01. NEVER implement enacted law under `gov/contrib/`.
- **Proposal → CONTRIB reform.** Not yet law; implement as a `gov/contrib/`
  factory reform with an `in_effect` toggle — delegate to `/encode-reform`,
  which owns that pattern, and stop here.

## Phase 2 — Implement (baseline mode)

Invoke the `structural-implementer` agent — it owns this whole phase
(statute verification, baseline edits, inertness + boundary tests, draft
PR). Its non-negotiables include re-deriving the spec from the ENROLLED
statute: backlog issues can be materially wrong (HI SB3125's issue said
"append one bracket"; the act replaced the whole rate table). For complex
multi-variable changes it may in turn use the country-models agents:

1. `rules-engineer` — the parameter-schema change (exact YAML edits,
   statutory references on every value: bill section + effective date, and
   inert defaults for periods before the effective date — a new bracket's
   pre-effective threshold is `.inf` or its rate matches the bracket below,
   whichever the surrounding schema convention uses) AND any variable/formula
   changes. A pure bracket append usually needs no formula edit; verify the
   rate scale is consumed generically before assuming.
2. `test-creator` — boundary tests proving: (a) pre-effective years are
   bit-identical to the old schema (the inertness test), (b) the new
   structure binds correctly in the effective year at, just below, and
   above each new threshold, per filing status.
3. Load `policyengine-standards`: changelog entry, formatting (`make
   format`), naming conventions.

## Phase 3 — PR and CI

Use the `/create-pr` flow (draft → CI green → ready): title names the
statute, body links the structural backlog issue (`Fixes
policyengine-{country}#NNN`), quotes the classifier's empirical
verification, and states the inertness guarantee. `ci-fixer` handles
iteration if CI fails.

## Phase 4 — Record the re-run

Unless `--no-rerun`: comment on the backlog issue with the exact re-run
command from the structural report (e.g. `/analyze-policy "US HI SB3125"
--year 2027`) and the condition ("after this PR is merged AND released to
the deployed API — check /us/metadata version"). The original run's
pre-registered benchmark registry stays frozen in the archive entry; the
re-run inherits it rather than re-searching.

## Boundaries

- Model PRs are reviewed by the country-model team — this command opens
  the PR; it does not merge it. The analysis stays blocked until the
  change reaches the DEPLOYED API, not just master.
- Scope is the structural gap named in the issue — no opportunistic
  refactors of surrounding parameters.
- If the gap turns out to be a formula rewrite rather than a schema
  extension (> ~2 days), stop and report — that is program-implementation
  work for `/encode-policy-v2`, not a structural patch.
