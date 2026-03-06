# Dashboard Workflow Audit

## Workflow Overview

```
/init-dashboard → creates GitHub repo, clones, sets up plugin config
/create-dashboard → orchestrates 8 agents across 7 phases:
  Phase 1: Plan (dashboard-planner) → HUMAN APPROVAL
  Phase 2: Scaffold (dashboard-scaffold)
  Phase 3A: Backend (backend-builder)
  Phase 3B: Frontend (frontend-builder)
  Phase 4: Integrate (dashboard-integrator)
  Phase 5A: Validate (dashboard-validator)
  Phase 5B: Spec validate (dashboard-design-token-validator)
  Phase 6: Human review → commit
  Phase 6.5: Update overview (dashboard-overview-updater)
/deploy-dashboard → Vercel + Modal + apps.json registration
```

## Issues

### Broken

**1. Data pattern mismatch (planner → backend-builder can't communicate)**

The planner outputs `data_pattern: api-v2-alpha` or `custom-backend`. The backend-builder expects `precomputed`, `policyengine-api`, or `custom-backend`. The planner will write `api-v2-alpha` to plan.yaml, then the backend-builder won't recognize it. It has patterns for `precomputed` and `policyengine-api` that the planner will never produce, and has no handler for `api-v2-alpha`.

**2. `cd frontend` in integrator (would fail)**

Integrator Step 7 says `cd frontend` but the scaffold creates everything at the repo root (`app/`, `components/`, `lib/`). There is no `frontend/` subdirectory.

**3. Stale branch references (may 404)**

- Frontend-builder Step 1: `gh api '...?ref=move-to-api-v2'`
- Deploy-dashboard Step 5: `git checkout move-to-api-v2`

Both reference a feature branch that may be merged/deleted.

### Wasteful

**4. 4x build/test runs (only 2 needed)**

| Phase | What runs | Purpose |
|-------|-----------|---------|
| 2 (Scaffold) | `bun install && bun run build && bunx vitest run` | Verify empty scaffold works |
| 3A (Backend) | `bun run build && bunx vitest run` | Verify API types compile |
| 4 (Integrator) | `bun run dev` + `bunx vitest run` | Verify e2e flow |
| 5A (Validator) | `bun install && bun run build && bunx vitest run` | Comprehensive final check |

Only Phase 2 and Phase 5A are needed. Phase 3A and 4 are intermediate checks that Phase 5A redoes.

**5. Phase 5A vs 5B validator overlap**

Both validators independently grep for hardcoded hex colors, old `pe-*` classes, `getCssVar` usage, and hardcoded `font-family`. Same patterns, same files, separate reports. Should be one agent, or 5B should only check framework/tooling compliance (Next.js, Tailwind v4 infrastructure).

**6. Integrator duplicates frontend-builder wiring**

Frontend-builder Step 5 already wires React Query hooks, builds request objects via `simulation.mutate(buildRequest(values))`, and handles loading/error states. The integrator then does the same: build request builders, build response transformers, wire React Query hooks, handle loading/error/empty states. Either the frontend-builder should stop at rendering with mock data, or the integrator should be eliminated.

**7. Overview-updater is always a no-op**

Phase 6.5 runs `dashboard-overview-updater` after `/create-dashboard`. But `/create-dashboard` creates a dashboard in a separate repo — it never modifies policyengine-claude. The overview lists ecosystem components (agents, commands, skills) which only change when policyengine-claude itself is modified.

**8. ~30 skill loads with heavy duplication**

Each agent loads 3-5 skills. Across 8 agents: `policyengine-interactive-tools-skill` loaded 4x, `policyengine-design-skill` loaded 4x, `policyengine-frontend-builder-spec-skill` loaded 3x. Not fixable architecturally (agents are separate processes), but worth noting.

### Inconsistent / Confusing

**9. `@policyengine/design-system` vs `@policyengine/ui-kit` naming**

The old package name `@policyengine/design-system` appears in `create-dashboard.md` Phase 5B description and `dashboard-overview.md` tech stack table. Everything else correctly says `@policyengine/ui-kit`.

**10. Workflow skill and create-dashboard command can drift**

`policyengine-dashboard-workflow-skill/SKILL.md` mirrors `create-dashboard.md`. They describe the same workflow but can (and have) drifted — the skill mentions "API v2 Alpha" while the backend-builder uses different terminology. Two sources of truth for one workflow.

**11. Dead `.claude/settings.json` creation in scaffold**

`/init-dashboard` creates `.claude/settings.json`. The scaffold agent has a full code block for creating it too, guarded by "Skip if it already exists." Since `/init-dashboard` is a documented prerequisite, this is dead code.
