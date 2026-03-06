# SDK Audit: Current State vs Upstream

## Architecture

The SDK has two layers:

1. **Mirror layer** (`sdk/agents/`, `sdk/commands/`, `sdk/skills/`) — copies of the upstream `.md` files that the prompt loader reads at runtime
2. **Code layer** (`sdk/src/`) — TypeScript orchestrator that invokes agents via `@anthropic-ai/claude-agent-sdk`, records telemetry to Supabase, and manages quality gates + human gates

The mirror layer exists because the prompt loader (`src/prompt-loader.ts`) reads agent `.md` files from `sdk/agents/dashboard/` and resolves skills from `sdk/skills/`. It doesn't read from the top-level `agents/` or `skills/` directories.

## Two Sources of Truth Problem

**Every `.md` file exists in two places.** The "upstream" copies at `agents/`, `commands/`, `skills/` and the "SDK mirror" copies at `sdk/agents/`, `sdk/commands/`, `sdk/skills/`.

The prompt loader ONLY reads from `sdk/`. The upstream copies are what the Claude Code plugin uses when someone runs `/create-dashboard` interactively. The SDK ignores them completely.

### Current Drift

| File | Status |
|------|--------|
| 10 agents | IDENTICAL (synced on feature branch) |
| 3 of 4 commands | IDENTICAL |
| `deploy-dashboard.md` | **DRIFTED** — SDK has stale `git checkout move-to-api-v2`, upstream has `git checkout main` |
| 8 of 10 skills | IDENTICAL |
| `policyengine-api-v2-skill` | **DRIFTED** — emoji in headers, npm vs bun |
| `policyengine-standards-skill` | **HEAVILY DRIFTED** — SDK has legacy changelog system, npm everywhere, massive extra content |

**Root cause:** There is no mechanism to keep these in sync. Every upstream change must be manually copied to SDK mirrors. This will keep breaking.

---

## SDK Orchestrator vs create-dashboard.md

### What create-dashboard.md says (the command):

```
Phase 1: Plan (dashboard-planner, opus) → HUMAN APPROVAL
Phase 2: Scaffold (dashboard-scaffold, opus) → build+test gate
Phase 3A: Backend (backend-builder, opus) → no gates
Phase 3B: Frontend (frontend-builder, opus) → no gates
Phase 4: Integrate (dashboard-integrator, sonnet) → bun run dev smoke check, no tests
Phase 5: 4 validators in parallel (build, design, architecture, plan) → fix loop, max 3
Phase 6: Commit + push → HUMAN REVIEW
Phase 6.5: Update overview (silent, sonnet)
```

### What the SDK orchestrator actually does (`types.ts` + `orchestrator.ts`):

```
Phase 1: Plan (dashboard-planner, opus) → human gate ✓
Phase 2: Scaffold (dashboard-scaffold, opus) → build gate, test gate ✓
Phase 3: Backend (backend-builder, opus) → type_check gate, test gate ✗ WRONG
Phase 4: Frontend (frontend-builder, opus) → build gate, test gate ✗ WRONG
Phase 5: Integrate (dashboard-integrator, sonnet) → build gate, test gate ✗ WRONG
Phase 6: 2 validators in parallel (dashboard-validator + dashboard-design-token-validator) ✗ WRONG
Phase 7: Review (commit + push) ✓
Phase 8: Overview (dashboard-overview-updater, sonnet, silent) ✓
```

### Breaking Issues

| # | Issue | Severity |
|---|-------|----------|
| 1 | **Validators reference deleted agents** — `types.ts` references `dashboard-validator` and `dashboard-design-token-validator`, both deleted. The prompt loader will crash with `ENOENT` trying to read `sdk/agents/dashboard/dashboard-validator.md`. | **FATAL** |
| 2 | **2 validators instead of 4** — The command says run 4 in parallel. The SDK runs 2 in parallel. | BREAKING |
| 3 | **Phases 3-5 have quality gates that should be removed** — Backend has `type_check + test`, frontend has `build + test`, integrate has `build + test`. Command says no intermediate gates. | WRONG |
| 4 | **No `bun run dev` smoke check** — The integrator phase has no smoke check in the SDK. Command says to do one. | MISSING |
| 5 | **Validation loop doesn't parse results** — `runValidationPhases` just checks if agents complete without error (line 463: `const validatorPassed = validatorResult !== null`). It doesn't parse the PASS/FAIL structured reports. Fix routing doesn't exist. | INCOMPLETE |
| 6 | **Deploy command has stale branch ref** — `sdk/commands/deploy-dashboard.md` still says `git checkout move-to-api-v2` | WRONG |

### Redundant / Questionable

| # | Issue |
|---|-------|
| 7 | **`quality-gates.ts` runs `bun run build` and `bunx vitest run`** — but the command says only test at scaffold and validate stages. The SDK attaches gates to every phase. |
| 8 | **Phase ordering uses integers** — `types.ts` uses `order: 1-8` but there's no `3A`/`3B` split. Backend and frontend run sequentially (order 3, 4) not concurrently. |
| 9 | **Prompt loader strips "First: Load Required Skills" section** but the 4 new validators don't all have that section — `dashboard-build-validator` has no skill references at all. Not breaking, but the regex won't match. |
| 10 | **Human gates are readline-based** — They work for CLI but won't scale to any other interface. |

---

## What the SDK Code Does (step by step)

### Entry point: `src/index.ts`
1. Parse CLI args (optional description, `--skip-init`)
2. Validate config (requires `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`)
3. If no `--skip-init`: run `initRepository()` which creates GitHub repo, clones it
4. Call `runDashboard(name, description, cwd)`

### Orchestrator: `src/orchestrator.ts`
1. Create a `dashboard_runs` row in Supabase
2. Loop through `PHASE_SEQUENCE` from `types.ts`
3. For each phase:
   - Load the agent `.md` file via `prompt-loader.ts`
   - Resolve and inject skill content via `skill-resolver.ts`
   - Call `@anthropic-ai/claude-agent-sdk`'s `query()` with the composed prompt
   - Stream results, capture usage/cost/duration
   - Record `phase_runs` row in Supabase
   - Run quality gates if configured (build, test, type_check)
   - Record `quality_gates` rows in Supabase
4. Special handling:
   - Plan phase → human approval via readline
   - Validation phases → run 2 in parallel, iterate on failure
   - Review phase → `git add -A && git commit && git push`
5. On completion: update `dashboard_runs` with totals
6. On failure: mark `dashboard_runs` as failed

### Prompt loader: `src/prompt-loader.ts`
1. Read agent `.md` from `sdk/agents/dashboard/`
2. Parse YAML frontmatter (name, model, tools, description)
3. Extract skill references (patterns: `**policyengine-*-skill**` and `Skill: policyengine-*-skill`)
4. Load each skill's `SKILL.md` content from `sdk/skills/`
5. Strip the "First: Load Required Skills" section (since skills are injected, not fetched via Skill tool)
6. Compose: `description + agent body + skill sections`
7. Hash the composed prompt (for dedup/caching in telemetry)

### Quality gates: `src/quality-gates.ts`
- `build` → `bun run build`
- `test` → `bunx vitest run`
- `type_check` → `bunx tsc --noEmit`
- Runs sequentially, short-circuits on first failure

### Human gates: `src/human-gates.ts`
- `requestPlanApproval()` → A/M/R choice
- `requestValidationDecision()` → A/K/S choice
- `askForDescription()` → free text
- `askForDashboardName()` → free text
- `askForClonePath()` → choice + optional free text

### Telemetry: `src/telemetry/`
- Supabase client (anon key, RLS enabled)
- Records: run lifecycle, phase start/end, quality gate results
- Tracks: duration, token usage, cost, model, session_id, prompt hash

---

## What Can Just Be Copied from Commands → SDK

| Source | Target | Notes |
|--------|--------|-------|
| `commands/deploy-dashboard.md` → `sdk/commands/deploy-dashboard.md` | Direct copy | Fix the stale branch ref |

The other commands and all agents/skills are already identical on the feature branch (I synced them). The real work is in `src/`.

## What Must Be Rewritten in `src/`

| File | What needs to change |
|------|---------------------|
| `src/phases/types.ts` | Replace 2-validator `PHASE_SEQUENCE` with 4-validator. Remove quality gates from backend/frontend/integrate. Add `validate_build`, `validate_design`, `validate_architecture`, `validate_plan`. |
| `src/orchestrator.ts` | Rewrite `runValidationPhases` to spawn 4 parallel agents. Remove the old 2-parallel logic. Consider parsing PASS/FAIL from results. |
| `src/quality-gates.ts` | Only used by scaffold now. Consider simplifying or removing the per-phase gate config entirely. |

## Structural Recommendation: Eliminate the Mirror Problem

The two-source-of-truth problem is the root cause of all drift. Options:

**Option A: SDK reads from top-level dirs.** Change `prompt-loader.ts` to read from `agents/` and `skills/` instead of `sdk/agents/` and `sdk/skills/`. Delete all SDK mirrors. The SDK and the plugin share the same files.

**Option B: Generate SDK mirrors.** A script copies from upstream → SDK on every commit/release. Still two copies but automated.

**Option C: Symlinks.** `sdk/agents → ../agents`, `sdk/skills → ../skills`. Git doesn't love symlinks but it works.

Option A is the cleanest. The only reason SDK mirrors exist is because the prompt loader hardcodes `sdk/agents/dashboard/` as its path. Changing two path constants eliminates the entire mirror layer.
