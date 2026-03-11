---
description: Orchestrates multi-agent workflow to create a PolicyEngine dashboard from a natural-language description
---

# Creating Dashboard: $ARGUMENTS

Coordinate a multi-agent workflow to plan, scaffold, implement, validate, and commit a production-ready PolicyEngine dashboard application.

## Arguments

`$ARGUMENTS` should contain:
- **Dashboard description** (required) — a natural-language description of the desired dashboard
- **Options**:
  - `--repo NAME_OR_PATH` — use an existing repo (searches sibling of cwd, `~/Documents/PolicyEngine/`, `~/PolicyEngine/`, `~/`)
  - `--skip-init` — use current working directory as the repo (no repo creation or cloning)
  - `--skip-validate` — skip the Phase 5 validation loop

**Examples:**
```
/create-dashboard A dashboard showing child poverty rates by state under different CTC reform scenarios
/create-dashboard --repo child-poverty-dashboard "Add a comparison mode showing baseline vs reform"
/create-dashboard --skip-init "Build a SNAP eligibility calculator for a single household"
/create-dashboard --skip-validate "A simple income tax calculator using the PolicyEngine API"
```

---

## Constants

```
DASHBOARD_NAME = derived from description or user input
REPO_PATH      = absolute path to the dashboard repository
PREFIX         = /tmp/dashboard-{DASHBOARD_NAME}
PLUGIN_ROOT    = directory containing this plugin (use: dirname of agents/dashboard/*.md)
```

---

## YOUR ROLE: ORCHESTRATOR ONLY

**CRITICAL — Context Window Protection:**
- You are an orchestrator. You do NOT write code, build components, or implement features.
- ALL implementation work is delegated to agents via the Task tool.
- You only read files marked "Short" in the handoff table (max 20 lines each).
- When spawning agents, point them to files on disk — do NOT paste file contents into prompts.

**You DO:**
- Parse arguments
- Create repos and clone (Phase 0)
- Spawn agents (in parallel where possible)
- Run quality gates via Bash (build, test)
- Read SHORT summary files (≤20 lines)
- Present checkpoints to user via AskUserQuestion
- Commit and push (Phase 6)

**You MUST NOT:**
- Write any code yourself
- Read full implementation files (plan.yaml, component files, etc.)
- Fix any issues manually — delegate to agents

---

## Context Window Protection

### Disk File Handoff Table

| File | Writer | Reader | Size |
|------|--------|--------|------|
| `{REPO_PATH}/plan.yaml` | planner agent | All subsequent agents | Full |
| `{PREFIX}-plan-summary.md` | planner agent | Orchestrator | Short ≤20 |
| `{PREFIX}-build-report.md` | build-validator | Orchestrator | Short ≤15 |
| `{PREFIX}-design-report.md` | design-validator | Orchestrator | Short ≤15 |
| `{PREFIX}-arch-report.md` | arch-validator | Orchestrator | Short ≤15 |
| `{PREFIX}-plan-report.md` | plan-validator | Orchestrator | Short ≤15 |

---

## Phase 0: Parse Arguments & Initialize Repository

### Step 0A: Parse Arguments & Clean Up

```
Parse $ARGUMENTS:
- DESCRIPTION: the natural-language dashboard description
- OPTIONS: --repo, --skip-init, --skip-validate
```

Clean up leftover files from previous runs:
```bash
rm -f /tmp/dashboard-*-plan-summary.md /tmp/dashboard-*-build-report.md /tmp/dashboard-*-design-report.md /tmp/dashboard-*-arch-report.md /tmp/dashboard-*-plan-report.md
```

Resolve `PLUGIN_ROOT` — find the directory containing this plugin:
```bash
# Find the agents directory to determine plugin root
find ~ -maxdepth 6 -path '*/policyengine-claude/agents/dashboard/dashboard-planner.md' -not -path '*/node_modules/*' 2>/dev/null | head -1 | xargs dirname | xargs dirname | xargs dirname
```

### Step 0B: Determine Repository Path

**If `--skip-init`**: Set `REPO_PATH` to the current working directory. Skip to Phase 1.

**If `--repo NAME_OR_PATH`**: Search for the repo:
1. If it's an absolute path → use directly
2. If it contains slashes → resolve relative to cwd
3. Otherwise search: sibling of cwd → `~/Documents/PolicyEngine/{NAME}` → `~/PolicyEngine/{NAME}` → `~/{NAME}`
4. Set `REPO_PATH` to the found path. Skip to Phase 1.

**Otherwise**: Create a new repository:

1. Derive a dashboard name from the description (kebab-case, 2-4 words), then ask user:

```
AskUserQuestion:
  Question: "What should the GitHub repository be named?"
  Options:
    - "{auto-derived-name}" (Recommended)
    - "Let me type a name"
```

Set `DASHBOARD_NAME` from the answer.

2. Check GitHub auth and org membership:
```bash
gh api user --jq '.login'
```
If this fails, tell the user to run `gh auth login` and STOP.

```bash
gh api orgs/PolicyEngine/memberships/{username} --jq '.role'
```
If not admin or member, report and STOP.

3. Create the repo:
```bash
gh repo create PolicyEngine/{DASHBOARD_NAME} --public --description "PolicyEngine {DASHBOARD_NAME} dashboard"
```

4. Ask where to clone:

```
AskUserQuestion:
  Question: "Where should I clone the repository?"
  Options:
    - "{sibling-of-cwd}/{DASHBOARD_NAME}" (Recommended)
    - "~/Documents/PolicyEngine/{DASHBOARD_NAME}"
    - "Let me specify a path"
```

5. Clone and initial commit:
```bash
gh repo clone PolicyEngine/{DASHBOARD_NAME} "{CLONE_PATH}"
cd {CLONE_PATH} && git add -A && git commit --allow-empty -m "Initialize dashboard repository" && git push -u origin main
```

6. Set `REPO_PATH = {CLONE_PATH}`.

Set `PREFIX = /tmp/dashboard-{DASHBOARD_NAME}`.

---

## Phase 1: Plan (Human Gate)

### Step 1A: Spawn planner agent

Spawn a **general-purpose** agent ("dashboard-planner"):

```
subagent_type: "general-purpose"

"You are the dashboard-planner agent for the PolicyEngine dashboard builder.

WORKING DIRECTORY: {REPO_PATH}
Use absolute paths for all Read/Write/Edit/Glob/Grep operations.
Prefix all Bash commands with: cd {REPO_PATH} &&

DASHBOARD DESCRIPTION:
{DESCRIPTION}

Read and follow the complete instructions in:
{PLUGIN_ROOT}/agents/dashboard/dashboard-planner.md

ADDITIONAL REQUIREMENTS:
- Write plan.yaml to {REPO_PATH}/plan.yaml
- Also write a SHORT summary (≤20 lines) to {PREFIX}-plan-summary.md containing:
  - Dashboard name and purpose
  - Data pattern chosen and why
  - Number and types of components
  - Key API endpoints or data sources
  - Any questions or concerns about the description"
```

### Step 1B: Plan approval

Read `{PREFIX}-plan-summary.md` (SHORT file). Present the summary to the user:

```
AskUserQuestion:
  Question: "Here's the dashboard plan. How should we proceed?"
  Options:
    - "Approve — start building" (Recommended)
    - "Modify — I have feedback"
    - "Reject — start over"
```

**If "Approve"**: Continue to Phase 2.

**If "Modify"**: Ask follow-up question for feedback. Then re-spawn planner agent with extra context:

```
"User feedback on your previous plan:
{USER_FEEDBACK}

Read the existing plan.yaml in {REPO_PATH} and update it based on this feedback.
Write updated plan.yaml and updated {PREFIX}-plan-summary.md."
```

Then repeat Step 1B (approval loop).

**If "Reject"**: STOP.

---

## Phase 2: Scaffold (Quality Gates)

### Step 2A: Spawn scaffold agent

Spawn a **general-purpose** agent ("dashboard-scaffold"):

```
subagent_type: "general-purpose"

"You are the dashboard-scaffold agent for the PolicyEngine dashboard builder.

WORKING DIRECTORY: {REPO_PATH}
Use absolute paths for all Read/Write/Edit/Glob/Grep operations.
Prefix all Bash commands with: cd {REPO_PATH} &&

Read and follow the complete instructions in:
{PLUGIN_ROOT}/agents/dashboard/dashboard-scaffold.md

The approved plan.yaml is at: {REPO_PATH}/plan.yaml"
```

### Step 2B: Quality gates

After the agent completes, run quality gates:

```bash
cd {REPO_PATH} && bun run build 2>&1 | tail -50
```

```bash
cd {REPO_PATH} && bunx vitest run 2>&1 | tail -50
```

**If both pass** (exit code 0): Continue to Phase 3.

**If either fails**: Re-spawn scaffold agent with error context:

```
"Quality gate failed. Fix the issues:

Command: {FAILED_COMMAND}
Exit code: {EXIT_CODE}
Output:
{STDERR_AND_STDOUT}

Fix the issues in {REPO_PATH} and ensure both build and tests pass."
```

Max 2 retries. If still failing after retries:

```
AskUserQuestion:
  Question: "Build/tests still failing after 2 fix attempts. What should we do?"
  Options:
    - "Continue anyway — I'll fix manually later"
    - "Stop"
```

---

## Phase 3: Backend + Frontend (PARALLEL)

Spawn **both agents in a single message** so they run concurrently:

### Agent 1: backend-builder

```
subagent_type: "general-purpose"
run_in_background: true

"You are the backend-builder agent for the PolicyEngine dashboard builder.

WORKING DIRECTORY: {REPO_PATH}
Use absolute paths for all Read/Write/Edit/Glob/Grep operations.
Prefix all Bash commands with: cd {REPO_PATH} &&

Read and follow the complete instructions in:
{PLUGIN_ROOT}/agents/dashboard/backend-builder.md

The approved plan.yaml is at: {REPO_PATH}/plan.yaml"
```

### Agent 2: frontend-builder

```
subagent_type: "general-purpose"
run_in_background: true

"You are the frontend-builder agent for the PolicyEngine dashboard builder.

WORKING DIRECTORY: {REPO_PATH}
Use absolute paths for all Read/Write/Edit/Glob/Grep operations.
Prefix all Bash commands with: cd {REPO_PATH} &&

Read and follow the complete instructions in:
{PLUGIN_ROOT}/agents/dashboard/frontend-builder.md

The approved plan.yaml is at: {REPO_PATH}/plan.yaml"
```

Wait for both agents to complete before proceeding.

---

## Phase 4: Integrate

Spawn a **general-purpose** agent ("dashboard-integrator"):

```
subagent_type: "general-purpose"

"You are the dashboard-integrator agent for the PolicyEngine dashboard builder.

WORKING DIRECTORY: {REPO_PATH}
Use absolute paths for all Read/Write/Edit/Glob/Grep operations.
Prefix all Bash commands with: cd {REPO_PATH} &&

Read and follow the complete instructions in:
{PLUGIN_ROOT}/agents/dashboard/dashboard-integrator.md

The approved plan.yaml is at: {REPO_PATH}/plan.yaml"
```

---

## Phase 5: Validation (4 Parallel Validators + Fix Routing)

**Skip this phase if `--skip-validate` flag is set.**

### Validation Loop (max 3 cycles)

```
ROUND = 1
MAX_ROUNDS = 3
PENDING_VALIDATORS = [build, design, architecture, plan]  # all 4 initially
```

### Step 5A: Run validators

Spawn **all pending validators in a single message**, each with `run_in_background: true`.

For each validator, use this prompt template:

```
subagent_type: "general-purpose"
run_in_background: true

"You are the {VALIDATOR_NAME} agent for the PolicyEngine dashboard builder.

WORKING DIRECTORY: {REPO_PATH}
Use absolute paths for all Read/Write/Edit/Glob/Grep operations.
Prefix all Bash commands with: cd {REPO_PATH} &&

Read and follow the complete instructions in:
{PLUGIN_ROOT}/agents/dashboard/{VALIDATOR_FILE}

The plan.yaml is at: {REPO_PATH}/plan.yaml

ADDITIONAL: Write your report to {PREFIX}-{REPORT_FILE} in addition to returning it."
```

Validator details:

| Validator | Agent file | Report file |
|-----------|-----------|-------------|
| build | `dashboard-build-validator.md` | `build-report.md` |
| design | `dashboard-design-validator.md` | `design-report.md` |
| architecture | `dashboard-architecture-validator.md` | `arch-report.md` |
| plan | `dashboard-plan-validator.md` | `plan-report.md` |

Wait for all validators to complete.

### Step 5B: Parse results

Read each validator's SHORT report. Look for PASS or FAIL.

**If all pass**: Exit validation loop, continue to Phase 6.

**If any fail**: Collect the failure details from each failed validator.

### Step 5C: Route failures to builders

Use this routing table to determine which builder agent should fix each failure:

| Failed Validator | Failure contains | Route to builder |
|------------------|-----------------|-----------------|
| build | (any failure) | `dashboard-scaffold.md` |
| design | (any failure) | `frontend-builder.md` |
| architecture | "tailwind", "next.js", "package manager" | `dashboard-scaffold.md` |
| architecture | "ui-kit", or other | `frontend-builder.md` |
| plan | "api contract" | `backend-builder.md` |
| plan | "component", "chart" | `frontend-builder.md` |
| plan | "embedding", "loading", "error" | `dashboard-integrator.md` |

Group failures by target builder. For each builder that needs to fix issues, spawn it:

```
subagent_type: "general-purpose"

"You are the {BUILDER_NAME} agent. Fix the following validation failures:

WORKING DIRECTORY: {REPO_PATH}
Use absolute paths. Prefix Bash with: cd {REPO_PATH} &&

Read the full instructions in:
{PLUGIN_ROOT}/agents/dashboard/{BUILDER_FILE}

VALIDATION FAILURES TO FIX:
{LIST_OF_FAILURES_FROM_REPORTS}

Fix each issue, ensuring the build and tests still pass.
Run: cd {REPO_PATH} && bun run build && bunx vitest run"
```

### Step 5D: Re-validate

After fixes, set `PENDING_VALIDATORS` to only the validators that failed (don't re-run passed ones).

Increment `ROUND`. If `ROUND <= MAX_ROUNDS`, go back to Step 5A.

If `ROUND > MAX_ROUNDS` and failures remain:

```
AskUserQuestion:
  Question: "Validation found {N} remaining issues after {MAX_ROUNDS} fix rounds. What should we do?"
  Options:
    - "Accept as-is — I'll fix manually"
    - "Keep trying one more round"
    - "Stop — don't commit"
```

**If "Accept"**: Continue to Phase 6.
**If "Keep trying"**: Increment MAX_ROUNDS by 1, go back to Step 5A.
**If "Stop"**: STOP.

---

## Phase 6: Review & Commit (Human Gate)

Present a summary to the user:

```
## Dashboard Build Complete

**Repository**: {REPO_PATH}
**Phases completed**: plan → scaffold → backend + frontend → integrate → validate

### How to run locally

cd {REPO_PATH}
make dev            # Start full dev stack
make dev-frontend   # Frontend only
make test           # Run tests
make build          # Production build

### Next steps

After reviewing locally, commit and push. Then use /deploy-dashboard to deploy.
```

```
AskUserQuestion:
  Question: "Ready to commit and push to GitHub?"
  Options:
    - "Commit and push" (Recommended)
    - "Stop — I want to review locally first"
```

**If "Commit and push"**:
```bash
cd {REPO_PATH} && git add -A && git commit -m "Implement dashboard from plan" && git push origin HEAD
```

Report the result to the user with the repo URL.

**If "Stop"**: Report that code is ready locally at `{REPO_PATH}` and the user can commit when ready.

---

## Phase 7: Overview Update (Silent)

Spawn the overview updater in the background — no need to wait:

```
subagent_type: "general-purpose"
run_in_background: true

"You are the dashboard-overview-updater agent.

Read and follow: {PLUGIN_ROOT}/agents/dashboard/dashboard-overview-updater.md"
```

---

## Error Handling

| Category | Example | Action |
|----------|---------|--------|
| **GitHub auth failure** | `gh api user` fails | Tell user to run `gh auth login`, STOP |
| **Repo already exists** | `gh repo create` says exists | Tell user to use `--repo NAME`, STOP |
| **Build failure** | `bun run build` fails | Re-run scaffold with error context (max 2 retries) |
| **Test failure** | `bunx vitest run` fails | Re-run scaffold with error context (max 2 retries) |
| **Validation failure** | Validator reports FAIL | Route to builder, re-validate (max 3 cycles) |
| **Agent failure** | Agent errors or doesn't complete | Report to user, suggest re-running that phase |
| **User rejects plan** | "Reject" at plan approval | STOP |

### Escalation Path

1. Agent encounters error → Attempt fix via re-spawning agent
2. Fix fails after max retries → Report to user with AskUserQuestion
3. User chooses to stop → STOP cleanly
4. Never proceed past a human gate without approval

---

## Execution Instructions

**YOUR ROLE**: You are an orchestrator ONLY. You must:
1. Invoke agents using the Task tool with `subagent_type: "general-purpose"`
2. Wait for agent completion (or use `run_in_background: true` for parallel)
3. Read ONLY short summary/report files (≤20 lines)
4. Run quality gates via Bash
5. Present checkpoints to user via AskUserQuestion
6. Proceed to the next phase after approval

**YOU MUST NOT**:
- Write any code yourself
- Fix any issues manually
- Read full implementation files
- Skip human gates

**IMPORTANT — Agent Working Directory**:
Every agent prompt MUST include:
```
WORKING DIRECTORY: {REPO_PATH}
Use absolute paths for all Read/Write/Edit/Glob/Grep operations.
Prefix all Bash commands with: cd {REPO_PATH} &&
```
This ensures agents work in the correct directory regardless of Claude Code's cwd.

**Execution Flow (CONTINUOUS)**:

Execute all phases sequentially without stopping (unless a STOP condition is hit):

0. **Phase 0**: Parse args, init repo (or use existing)
1. **Phase 1**: Plan → HUMAN APPROVAL (approve/modify/reject)
2. **Phase 2**: Scaffold → quality gates (build + test, max 2 retries)
3. **Phase 3**: Backend + Frontend (PARALLEL — spawn both in one message)
4. **Phase 4**: Integrate
5. **Phase 5**: Validate (4 validators parallel, fix routing, max 3 cycles) — skip if `--skip-validate`
6. **Phase 6**: Review → HUMAN APPROVAL → commit and push
7. **Phase 7**: Overview update (silent, background)
