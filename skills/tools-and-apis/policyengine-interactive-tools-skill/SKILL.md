---
name: policyengine-interactive-tools
description: Building standalone interactive calculators and dashboards that embed in policyengine.org
---

# PolicyEngine interactive tools

This mirrored skill should stay thin. The canonical source of truth lives in:

- `/Users/maxghenis/policyengine-skills/targets/claude/commands/new-tool.md`
- `/Users/maxghenis/policyengine-skills/skills/tools-and-apis/policyengine-interactive-tools-skill/SKILL.md`
- `/Users/maxghenis/policyengine-skills/skills/documentation/policyengine-design-skill/SKILL.md`

## Current standard for new tools

- Use **Next.js 14 + Tailwind 4 + `@policyengine/ui-kit` + Recharts**
- Use `@import "tailwindcss";` followed by `@import "@policyengine/ui-kit/theme.css";`
- Copy the PolicyEngine logo/favicon locally from `@policyengine/ui-kit`; never hotlink raw GitHub asset URLs
- Prefer the PolicyEngine API before building a custom Modal backend
- If you need Modal, use the **gateway + worker + polling** pattern rather than a single synchronous `@modal.web_endpoint`
- Add pull-request CI (`.github/workflows/ci.yml`) before launch; at minimum run install + build, and run lint/test when the scripts exist
- Register new tools in `policyengine-app-v2/website/src/data/apps.json`
- Update `policyengine-app-v2/website/next.config.ts` when the tool needs a rewrite/proxy path

## Legacy repo warning

Several production repos are still useful for policy logic and data-shape examples, but they are **not** scaffolding templates for new tools. Do not copy Vite-era apps, CDN-loaded design-system tokens, or other legacy setup into new repos.

Use the canonical files above for the full workflow, scaffold examples, embedding patterns, and checklist.
