---
name: policyengine-design
description: |
  PolicyEngine design system — tokens, typography, colors, charts, and branding for all project types.
  Triggers: "brand colors", "design tokens", "PolicyEngine colors", "typography", "font", "color palette", "CSS variables", "pe-color", "design system", "branding guidelines"
---

# PolicyEngine design system

This mirrored skill defers to the canonical documentation in:

- `/Users/maxghenis/policyengine-skills/skills/documentation/policyengine-design-skill/SKILL.md`

## Default guidance

- For new standalone tools and dashboards, use `@policyengine/ui-kit` as the design-token source of truth
- Import tokens with `@import "@policyengine/ui-kit/theme.css"` after `@import "tailwindcss"`
- Use CSS variables such as `var(--primary)`, `var(--chart-1)`, `var(--border)`, and `var(--font-sans)` instead of hardcoded hex values
- Use checked-in or package-provided PolicyEngine logos; never hotlink raw GitHub asset URLs

## Legacy repo warning

Some older repos still use `@policyengine/design-system`. Treat that as a migration detail for those repos only. Do not copy the legacy package or CDN pattern into new work.
