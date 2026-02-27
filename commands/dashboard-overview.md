---
description: Lists all available tools, commands, skills, and agents in the dashboard builder ecosystem
---

# Dashboard builder ecosystem overview

Display a complete inventory of all tools, commands, skills, and agents available in the PolicyEngine dashboard builder workflow.

## Commands

| Command | Description |
|---------|-------------|
| `/create-dashboard` | Orchestrates multi-agent workflow to create a PolicyEngine dashboard from a natural-language description |
| `/deploy-dashboard` | Deploys a completed dashboard to Vercel (and optionally Modal) and registers it in the app |
| `/dashboard-overview` | This command — lists all dashboard builder ecosystem components |

## Agents

| Agent | Phase | Description |
|-------|-------|-------------|
| `dashboard-planner` | 1 — Plan | Analyzes natural-language descriptions and produces structured plan YAML |
| `dashboard-scaffold` | 2 — Scaffold | Creates new GitHub repo with Next.js + Tailwind project structure |
| `backend-builder` | 3A — Implement | Builds API stubs for v2 alpha integration or custom Modal backends |
| `frontend-builder` | 3B — Implement | Builds React components with Tailwind + PE design tokens |
| `dashboard-integrator` | 4 — Integrate | Wires frontend components to backend API client, handles data flow |
| `dashboard-validator` | 5A — Validate | Validates dashboard against plan requirements (10 categories) |
| `dashboard-design-token-validator` | 5B — Validate | Validates frontend spec compliance (Tailwind, Next.js, design tokens) |
| `dashboard-overview-updater` | Post — Update | Updates this overview if ecosystem components changed |

## Skills

| Skill | Purpose |
|-------|---------|
| `policyengine-frontend-builder-spec-skill` | Mandatory frontend technology requirements (Next.js, Tailwind CSS, design tokens) |
| `policyengine-dashboard-workflow-skill` | Reference for the create/deploy dashboard workflow |
| `policyengine-interactive-tools-skill` | Embedding patterns, hash sync, country detection |
| `policyengine-design-skill` | Design tokens, visual identity, colors, typography, spacing |
| `policyengine-recharts-skill` | Recharts chart component patterns and styling |
| `policyengine-app-skill` | app-v2 component architecture reference |
| `policyengine-api-v2-skill` | API v2 endpoint catalog and async patterns |
| `policyengine-vercel-deployment-skill` | Vercel deployment configuration |
| `policyengine-standards-skill` | Code quality and CI/CD standards |
| `policyengine-us-skill` | US tax/benefit variables and programs |
| `policyengine-uk-skill` | UK tax/benefit variables and programs |

## Workflow phases

```
Phase 0:  Permission check
Phase 1:  Plan (dashboard-planner) → HUMAN APPROVAL
Phase 2:  Scaffold (dashboard-scaffold)
Phase 3A: Backend (backend-builder)
Phase 3B: Frontend (frontend-builder)
Phase 4:  Integrate (dashboard-integrator)
Phase 5A: Validate (dashboard-validator) ─┐
Phase 5B: Spec validate (dashboard-design-token-validator) │ ← max 3 fix cycles
          Fix → re-validate ──────────────┘
Phase 6:  Human review → commit
Phase 6.5: Update overview (dashboard-overview-updater, silent)

Separately: /deploy-dashboard (after merge to main)
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js (App Router) + TypeScript |
| Styling | Tailwind CSS + `@policyengine/design-system` tokens |
| Charts | Recharts (line, bar, area) + Plotly (choropleths) |
| Data fetching | TanStack React Query |
| Testing | Vitest + React Testing Library |
| Deployment | Vercel (frontend) + Modal (backend, if custom) |
