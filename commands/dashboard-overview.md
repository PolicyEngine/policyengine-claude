---
description: Lists all available tools, commands, skills, and agents in the dashboard builder ecosystem
---

# Dashboard builder ecosystem overview

Display a complete inventory of all tools, commands, skills, and agents available in the PolicyEngine dashboard builder workflow.

## Commands

| Command | Description |
|---------|-------------|
| `/create-dashboard` | Orchestrates multi-agent workflow: creates repo, plans, scaffolds, implements, validates, and commits a dashboard |
| `/deploy-dashboard` | Deploys a completed dashboard to Vercel (and optionally Modal) and registers it in the app |
| `/dashboard-overview` | This command — lists all dashboard builder ecosystem components |

## Agents

| Agent | Phase | Description |
|-------|-------|-------------|
| `dashboard-planner` | 1 — Plan | Analyzes natural-language descriptions and produces structured plan YAML |
| `dashboard-scaffold` | 2 — Scaffold | Generates Next.js + Tailwind project structure into the current repo |
| `backend-builder` | 3A — Implement | Builds API stubs for v2 alpha integration or custom Modal backends |
| `frontend-builder` | 3B — Implement | Builds React components with Tailwind + PE design tokens |
| `dashboard-integrator` | 4 — Integrate | Wires frontend components to backend API client, handles data flow |
| `dashboard-build-validator` | 5 — Validate | Runs build and test suite |
| `dashboard-design-validator` | 5 — Validate | Checks design tokens, typography, sentence case, responsive |
| `dashboard-architecture-validator` | 5 — Validate | Checks Tailwind v4, Next.js, ui-kit, package manager |
| `dashboard-plan-validator` | 5 — Validate | Checks API contract, components, embedding, states vs plan |
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
| `policyengine-modal-deployment-skill` | Modal deployment for custom dashboard backends |
| `policyengine-standards-skill` | Code quality and CI/CD standards |
| `policyengine-writing-skill` | PolicyEngine writing style for blog posts, documentation, and reports |
| `policyengine-us-skill` | US tax/benefit variables and programs |
| `policyengine-uk-skill` | UK tax/benefit variables and programs |
| `policyengine-tailwind-shadcn-skill` | Tailwind CSS v4 + shadcn/ui integration patterns and conventions |
| `policyengine-ui-kit-consumer-skill` | @policyengine/ui-kit consumer setup, CSS configuration, and troubleshooting |

## Workflow phases

```
Phase 0:  Init repo (creates GitHub repo + clones locally, or uses existing)
Phase 1:  Plan (dashboard-planner) → HUMAN APPROVAL
Phase 2:  Scaffold (dashboard-scaffold) → quality gates (build + test)
Phase 3:  Backend + Frontend (PARALLEL)
Phase 4:  Integrate (dashboard-integrator)
Phase 5:  Validate (4 validators in parallel) ─┐
          build, design, architecture, plan    │ ← max 3 fix cycles
          Fix → re-validate ───────────────────┘
Phase 6:  Human review → commit and push
Phase 7:  Update overview (dashboard-overview-updater, silent)

Separately: /deploy-dashboard (after merge to main)
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js (App Router) + TypeScript |
| Styling | Tailwind CSS + `@policyengine/ui-kit` tokens |
| Charts | Recharts (line, bar, area) + Plotly (choropleths) |
| Data fetching | TanStack React Query |
| Testing | Vitest + React Testing Library |
| Deployment | Vercel (frontend) + Modal (backend, if custom) |
