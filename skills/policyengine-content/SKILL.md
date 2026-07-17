---
name: policyengine-content
description: |
  Generate branded social assets from a PolicyEngine blog post or announcement — 1200x630 social
  images and platform-optimized post copy for LinkedIn/X, localized for UK/US audiences.
  Triggers: "make a social image", "social card for this post", "generate content", "LinkedIn post
  for", "X post for", "promote this blog post", "social copy", "announcement graphic".
metadata:
  category: process
---

# PolicyEngine content generation

Turn a published post or announcement into shareable social assets: a 1200x630 image and
platform copy. This skill supplies the template and the token/brand rules; the workflow itself
runs through a command and agent.

## Workflow entry

- **`/generate-content`** (command) is the entry point. It takes a `source` (post URL or file),
  `audiences` (default `uk,us`), and `outputs` (default `all`).
- It dispatches the **`content-orchestrator`** agent, which parses the source, generates
  localized variants, fills this skill's template, and renders each image by screenshotting the
  filled HTML in **headless Chrome** (`--headless --screenshot --window-size=1200,630`).
- The **`neutrality-reviewer`** agent then checks the generated copy for advocacy, speculation,
  or one-sided framing before anything is published.

Do not hand-render assets when the command exists — invoke `/generate-content` and let the agents
own the mechanics. Follow the **policyengine-writing** skill for the copy's tone and neutrality.

## The template (live)

`templates/social-image.html` in this skill dir is the live template the orchestrator fills and
screenshots. Keep it. It renders standalone in headless Chrome, so it carries literal hex values
(dark background `#1a2332`, teal accents) rather than importing a stylesheet — headless Chrome
does not resolve the app's CSS. Its `{{placeholders}}`:

```
headline_prefix, headline_highlight, subtext, badge, flags,
quote, attribution_name, attribution_title, headshot_url, logo_url
```

Notes that matter for Chrome-headless rendering: position the logo with `top:` not `bottom:`;
inline external images as data URIs (or download them locally first) so they load; always
preview the rendered PNG before using it.

## Design tokens

The source of truth for color is **`@policyengine/ui-kit`** (`theme.css`), not any older package.
In app/chart/SVG contexts, import the theme and reference CSS variables — never hardcode hex:

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
/* then: var(--primary), var(--chart-1), var(--border), var(--color-gray-400) */
```

| Role | ui-kit variable | Hex |
|------|-----------------|-----|
| Primary teal | `--primary` (a.k.a. `--color-teal-600`) | #2C7A7B |
| Bright teal (highlight) | `--color-teal-500` | #319795 |
| Light teal | `--color-teal-200` | #81E6D9 |
| Muted text | `--color-gray-400` | #9CA3AF |
| Surface / card | `--background`, `--card` | theme-dependent |

The standalone template is the one place literal hexes are correct; keep its palette in step with
these ui-kit values. Do **not** use the deprecated `@policyengine/design-system` package or its
`--pe-color-*` variable prefix. <!-- stale-ok --> The `@policyengine/design-system` `--pe-color-*` tokens are retired; migrate any lingering reference to the ui-kit variables above.

Broader chart and social-image visual standards live with the **policyengine-design** skill.

## Typography and logo

- Font: Inter — headlines 800 weight, `-0.02em` tracking; labels 700, uppercase, `0.1em` tracking.
- Logo: use the PolicyEngine logo from ui-kit or a checked-in local asset; never hotlink a raw
  GitHub URL. White logo on dark backgrounds, teal on light; minimum height ~28px.

## Audience localization

| Aspect | UK | US |
|--------|----|----|
| Spelling | modelling, centre, organisation | modeling, center, organization |
| PM reference | 10 Downing Street | UK Prime Minister's office |
| Framing | direct announcement | "same tech that powers PolicyEngine US" |
| Flags | UK | US + UK |
| NSF/POSE mention | omit | include if relevant |

## Related skills

- **policyengine-writing** — tone and neutrality for the post copy.
- **policyengine-design** — chart and social-image visual standards, ui-kit usage.
- **policyengine-research-lookup** — find the source post to promote.
