---
description: Orchestrates multi-agent workflow to create a PolicyEngine dashboard from a natural-language description
---

# Creating dashboard from description

Coordinate the multi-agent workflow to create a complete PolicyEngine dashboard. The user provides a natural-language description (typically 2-3 paragraphs) of what the dashboard should do.

**Input:** $ARGUMENTS should contain or reference the dashboard description. If $ARGUMENTS is empty, use `AskUserQuestion`:

```
question: "Please describe the dashboard you want to create (2-3 paragraphs covering purpose, audience, key metrics, and any specific policy variables)."
header: "Description"
options: [] (free text — let the user type via "Other")
```

**Precondition:** Run this from inside a dashboard repository created via `/init-dashboard`. The command assumes the current working directory IS the dashboard repo with `.claude/settings.json` already configured.

## Phase 1: Plan

Invoke @complete:dashboard:dashboard-planner agent to:
- Analyze the natural-language description
- Research existing PolicyEngine dashboards for patterns
- Map requirements to PolicyEngine variables and API v2 alpha endpoints
- Determine data pattern (api-v2-alpha default, custom-backend escape hatch)
- Design components, charts, and test criteria
- Write `plan.yaml` to the working directory

**Quality Gate**: The agent returns a structured plan and human-readable summary.

### Human Approval Gate

Present the plan summary to the user. The plan includes:
1. Dashboard name, purpose, and audience
2. Data pattern and justification
3. Component list (inputs, charts, metrics)
4. API endpoints needed
5. Test plan

Present the plan summary, then use `AskUserQuestion`:

```
question: "How does this implementation plan look?"
header: "Plan review"
options:
  - label: "Approve"
    description: "Proceed with implementation as planned"
  - label: "Modify"
    description: "Request changes to specific sections before proceeding"
  - label: "Reject"
    description: "Start over with a different approach"
```

**Do NOT proceed until the user selects "Approve".**

If the user selects "Modify" (or provides changes via "Other"):
1. Edit `plan.yaml` with the requested changes
2. Re-present the updated plan
3. Ask for approval again using `AskUserQuestion`

## Phase 2: Scaffold

After plan approval, invoke @complete:dashboard:dashboard-scaffold agent to:
- Generate project structure into the current working directory (Next.js App Router, React, TypeScript, Tailwind, CI)
- Create API client stubs matching the plan
- Set up embedding boilerplate
- Create `CLAUDE.md` and `README.md`
- Create feature branch and push

**Quality Gate**: Build passes, initial test passes.

Report to user:
> Scaffold generated in current directory.
> Feature branch: `feature/initial-implementation`
> Scaffold builds and tests pass. Proceeding to implementation.

## Phase 3: Implement

### Step 3A: Backend

Invoke @complete:dashboard:backend-builder agent to:
- Build typed API stubs (if api-v2-alpha pattern) with fixture data
- OR build Modal backend (if custom-backend pattern)
- Create React Query hooks
- Write API tests

### Step 3B: Frontend

Invoke @complete:dashboard:frontend-builder agent to:
- Study referenced app-v2 component patterns
- Implement input forms from the plan
- Implement charts following app-v2 patterns with Tailwind + PE design tokens
- Implement metric cards
- Wire page component with React Query
- Implement responsive design using Tailwind utility classes
- Write component tests

## Phase 4: Integrate

Invoke @complete:dashboard:dashboard-integrator agent to:
- Wire frontend components to API client
- Build request builders (form state → API request)
- Build response transformers (API response → component props)
- Implement loading, error, and empty states
- Configure caching
- Verify end-to-end data flow

## Phase 5: Validate

Invoke all four validator agents **in parallel** using the Task tool:

| Agent | Domain | Model |
|-------|--------|-------|
| @complete:dashboard:dashboard-build-validator | Build + tests | sonnet |
| @complete:dashboard:dashboard-design-validator | Design tokens, typography, responsive | sonnet |
| @complete:dashboard:dashboard-architecture-validator | Tailwind v4, Next.js, ui-kit, package manager | sonnet |
| @complete:dashboard:dashboard-plan-validator | API contract, components, embedding, states | opus |

Each returns a structured report with PASS/FAIL per check. Merge the four reports into a single validation summary.

**Quality Gate**: All four reports show all checks passing.

### Iteration Loop

If any validator reports failures:

1. **Route each failure to the appropriate builder agent:**
   - Build failures → whichever agent owns the failing code
   - Design compliance failures → frontend-builder
   - Architecture failures → dashboard-scaffold (or frontend-builder for class usage)
   - Plan compliance failures → frontend-builder, backend-builder, or integrator depending on the gap

2. **Re-invoke the appropriate agent** with the specific failures to fix.

3. **Re-run all four validators in parallel** after fixes.

4. **Maximum 3 iteration cycles.** If still failing after 3 cycles, present the remaining failures and use `AskUserQuestion`:

   ```
   question: "There are still validation failures after 3 fix cycles. How would you like to proceed?"
   header: "Failures"
   options:
     - label: "Accept as-is"
       description: "Proceed to review with the remaining issues noted"
     - label: "Keep fixing"
       description: "Try another round of fixes"
     - label: "Stop"
       description: "Stop the workflow here so you can investigate manually"
   ```

## Phase 6: Human Review

After validation passes (or the user accepts remaining issues):

### Commit and Present for Review

```bash
git add -A
git commit -m "Implement dashboard from plan"
git push
```

**Present to the user:**

> ## Dashboard ready for review
>
> Repository: `PolicyEngine/{name}`
> Branch: `feature/initial-implementation`
>
> ### Validation results
> [Summary from validator - X/10 categories passed]
>
> ### What's implemented
> - [List components from plan]
> - Data pattern: [api-v2-alpha / custom-backend]
> - [Note about stub data if api-v2-alpha]
>
> ### Next steps
> 1. Review the code on the feature branch
> 2. Run `bun run dev` to see the dashboard locally
> 3. Request any changes (I can make them on the branch)
> 4. When satisfied, merge `feature/initial-implementation` into `main`
> 5. Run `/deploy-dashboard` to deploy
>
> **Note:** If using the api-v2-alpha data pattern, the dashboard currently uses
> stub data. Real API integration will be connected when the v2 alpha alignment
> agent is available.

## Phase 6.5: Update Overview

Invoke @complete:dashboard:dashboard-overview-updater agent to:
- Check if any dashboard ecosystem components changed during this run
- Update the `/dashboard-overview` command if needed

This phase is silent — it does not require user interaction.

**WORKFLOW COMPLETE.** The user now owns the branch and decides when to merge and deploy.

## Error Handling

### Error Categories

| Category | Example | Action |
|----------|---------|--------|
| **Recoverable** | Test failure, lint error, type mismatch | Validator catches → fix cycle |
| **Blocking** | GitHub API down, bun install fails | Stop and report to user |
| **Plan issue** | Description too vague, no matching PE variables | Return to Phase 1 |

### Error Handling by Phase

- **Phase 1 (Plan)**: If planner can't produce a plan, ask user for clarification.
- **Phase 2 (Scaffold)**: If file generation or bun install fails, report error and STOP.
- **Phase 3 (Implement)**: If agent fails, report which agent and what error. Wait for user.
- **Phase 4 (Integrate)**: If wiring fails, report type mismatches. May need Phase 3 re-run.
- **Phase 5 (Validate)**: Iteration loop handles most failures. Stop after 3 cycles if unresolved.
- **Phase 6 (Review)**: Present whatever state the dashboard is in.

### Escalation

1. Agent encounters error → attempt fix within agent
2. Fix fails → validator catches on next cycle
3. Validator fix cycle fails 3 times → report to user
4. Never proceed to next phase with a broken build

## Execution Instructions

**YOUR ROLE**: You are an orchestrator ONLY. You must:
1. Invoke agents using the Task tool
2. Wait for their completion
3. Check quality gates
4. Present results to the user at approval gates
5. Proceed to the next phase only after gates pass

**YOU MUST NOT**:
- Write dashboard code yourself
- Skip the Phase 1 human approval gate
- Skip the Phase 6 human review
- Deploy the dashboard (that's `/deploy-dashboard`)
- Merge any branches

**Execution Flow:**

1. **Phase 1**: Plan → present to user → WAIT for approval
2. **Phase 2**: Scaffold → verify build → report
3. **Phase 3A**: Backend → report
4. **Phase 3B**: Frontend → report
5. **Phase 4**: Integrate → smoke check → report
6. **Phase 5**: Run 4 validators in parallel → merge reports
7. **Phase 5 loop**: Route failures → re-validate (max 3 cycles)
8. **Phase 6**: Commit → present to user → DONE
9. **Phase 6.5**: Update overview (silent)
