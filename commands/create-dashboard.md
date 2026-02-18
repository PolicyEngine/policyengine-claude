---
description: Orchestrates multi-agent workflow to create a PolicyEngine dashboard from a natural-language description
---

# Creating dashboard from description

Coordinate the multi-agent workflow to create a complete PolicyEngine dashboard. The user provides a natural-language description (typically 2-3 paragraphs) of what the dashboard should do.

**Input:** $ARGUMENTS should contain or reference the dashboard description. If $ARGUMENTS is empty, ask the user to describe the dashboard they want.

## Phase 0: Permission Check

Before anything else, verify the user can create repositories in the PolicyEngine GitHub organization:

```bash
gh api orgs/PolicyEngine/memberships/$( gh api user --jq '.login' ) --jq '.role' 2>&1
```

**If the command succeeds** and returns `admin` or `member`: proceed to Phase 1.

**If the command fails** (404, 403, or any error): stop immediately and display:

> **Permission check failed.** The `/create-dashboard` workflow needs to create a new repository under the `PolicyEngine` GitHub organization, but your current GitHub account does not appear to have the required permissions.
>
> To use this workflow, you need:
> - **Membership** in the [PolicyEngine GitHub organization](https://github.com/PolicyEngine)
> - **Repository creation** privileges within the org
>
> Please ask a PolicyEngine org admin to add your GitHub account, then try again.

**Do NOT proceed past this point if the permission check fails.**

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

**Ask the user:**
> Here is the implementation plan for your dashboard. Please review:
>
> [plan summary]
>
> You can:
> - **Approve** to proceed with implementation
> - **Modify** specific sections (tell me what to change)
> - **Reject** to start over with a different approach

**Do NOT proceed until the user explicitly approves.**

If the user requests modifications:
1. Edit `plan.yaml` with the requested changes
2. Re-present the updated plan
3. Wait for approval again

## Phase 2: Scaffold

After plan approval, invoke @complete:dashboard:dashboard-scaffold agent to:
- Create a new GitHub repository under `PolicyEngine/`
- Generate project structure (Vite, React, TypeScript, CI)
- Create API client stubs matching the plan
- Set up embedding boilerplate
- Create `CLAUDE.md` and `README.md`
- Make initial commit on `main`, then create feature branch
- Push feature branch

**Quality Gate**: Repository exists, build passes, initial test passes.

Report to user:
> Repository created: `PolicyEngine/{name}`
> Feature branch: `feature/initial-implementation`
> Scaffold builds and tests pass. Proceeding to implementation.

## Phase 3: Implement

### Step 3A: Backend

Invoke @complete:dashboard:backend-builder agent to:
- Build typed API stubs (if api-v2-alpha pattern) with fixture data
- OR build Modal backend (if custom-backend pattern)
- Create React Query hooks
- Write API tests

**Quality Gate**: API client compiles. Stub tests pass (or Python tests for custom backend).

### Step 3B: Frontend

Invoke @complete:dashboard:frontend-builder agent to:
- Study referenced app-v2 component patterns
- Implement input forms from the plan
- Implement charts following app-v2 patterns with design system tokens
- Implement metric cards
- Wire App.tsx with React Query
- Implement responsive CSS
- Write component tests

**Quality Gate**: All components render. Component tests pass. Build compiles.

## Phase 4: Integrate

Invoke @complete:dashboard:dashboard-integrator agent to:
- Wire frontend components to API client
- Build request builders (form state → API request)
- Build response transformers (API response → component props)
- Implement loading, error, and empty states
- Configure caching
- Verify end-to-end data flow

**Quality Gate**: Build compiles. All tests pass. Data flows from input to output.

## Phase 5: Validate

Invoke @complete:dashboard:dashboard-validator agent to run the full validation suite:

1. Build verification
2. Test suite
3. Design token compliance (no hardcoded colors/spacing)
4. Typography (Inter font, sentence case)
5. Responsive design (768px, 480px breakpoints)
6. Embedding compliance (country detection, hash sync, share URLs)
7. API contract compliance
8. Component completeness (all plan components implemented)
9. Loading/error state coverage

**The validator returns a structured report with PASS/FAIL per category.**

### Iteration Loop

If the validator reports failures:

1. **Determine which agent should fix each failure:**
   - Design token / CSS issues → frontend-builder
   - API type mismatches → backend-builder or integrator
   - Missing data flow → integrator
   - Missing components → frontend-builder
   - Test failures → whichever agent owns the failing code

2. **Re-invoke the appropriate agent** with the specific failures to fix.

3. **Re-run the validator** after fixes.

4. **Maximum 3 iteration cycles.** If still failing after 3 cycles:
   - Present the remaining failures to the user
   - Ask if they want to continue fixing or accept the current state

## Phase 6: Human Review

After validation passes (or the user accepts remaining issues):

### Commit and Present for Review

```bash
cd /tmp/DASHBOARD_NAME
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
> 2. Run `npm run dev` in `frontend/` to see the dashboard locally
> 3. Request any changes (I can make them on the branch)
> 4. When satisfied, merge `feature/initial-implementation` into `main`
> 5. Run `/deploy-dashboard` to deploy
>
> **Note:** If using the api-v2-alpha data pattern, the dashboard currently uses
> stub data. Real API integration will be connected when the v2 alpha alignment
> agent is available.

**WORKFLOW COMPLETE.** The user now owns the branch and decides when to merge and deploy.

## Error Handling

### Error Categories

| Category | Example | Action |
|----------|---------|--------|
| **Recoverable** | Test failure, lint error, type mismatch | Validator catches → fix cycle |
| **Blocking** | GitHub API down, npm install fails | Stop and report to user |
| **Plan issue** | Description too vague, no matching PE variables | Return to Phase 1 |

### Error Handling by Phase

- **Phase 1 (Plan)**: If planner can't produce a plan, ask user for clarification.
- **Phase 2 (Scaffold)**: If repo creation fails, report error and STOP.
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
3. **Phase 3A**: Backend → verify → report
4. **Phase 3B**: Frontend → verify → report
5. **Phase 4**: Integrate → verify → report
6. **Phase 5**: Validate → iterate if needed → report
7. **Phase 6**: Commit → present to user → DONE
