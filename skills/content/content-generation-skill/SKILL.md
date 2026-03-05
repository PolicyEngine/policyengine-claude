---
name: content-generation
description: Generate marketing content from PolicyEngine blog posts - social media images, social post copy, and branded assets
---

# Content generation skill

Use this skill when generating marketing content from PolicyEngine blog posts, research, or announcements. This includes social media images and social post copy.

## Overview

This skill provides templates and patterns for generating consistent, branded PolicyEngine content across multiple channels and audiences (UK, US, global).

## Content types

### Social media images

1200x630 PNG images for LinkedIn, X (Twitter), and Facebook with:
- PolicyEngine brand colors from design tokens (teal primary, dark background)
- Inter font family
- Headline with teal highlight
- Optional headshot with quote
- PolicyEngine logo
- Audience-appropriate flags

### Newsletters (future)

Newsletter generation is planned for a future release. The agent can generate newsletter HTML ad-hoc following brand guidelines, but there is no template file yet.

### Social post copy

Platform-optimized text for:
- LinkedIn (professional tone, can be longer)
- X/Twitter (concise, hashtags)
- Threads/Bluesky (conversational)

## Audience localization

Content is localized for different audiences:

| Aspect | UK | US |
|--------|----|----|
| Spelling | modelling, centre | modeling, center |
| References | 10 Downing Street | UK Prime Minister's office |
| Context | Direct announcement | "Same tech that powers PolicyEngine US" |
| Flags | 🇬🇧 | 🇺🇸 🇬🇧 |
| Sections | No NSF mention | Include NSF/POSE if relevant |

## Template variables

### Social image template

```
headline: Main headline text
headline_highlight: Text to highlight in teal (optional)
subtext: Supporting description
flags: Emoji flags to display (e.g., "🇬🇧" or "🇺🇸 🇬🇧")
headshot_url: URL or path to headshot image
quote: Pull quote text
attribution_name: Quote attribution name
attribution_title: Quote attribution title/role
logo_path: Path to PolicyEngine logo
```

## Workflow

1. **Parse source** - Extract key information from blog post/announcement
2. **Generate variants** - Create UK and US versions with appropriate localization
3. **Render assets** - Generate images via Chrome headless
4. **Generate social copy** - Create platform-optimized posts for LinkedIn/X
5. **Output summary** - Provide paths to all generated content

## Brand guidelines

### Colors

Source of truth: `policyengine-design-skill` and `@policyengine/design-system` CSS tokens.
Social image generation runs in headless Chrome with design tokens loaded, so use CSS vars where possible. Fallback hex values for non-browser contexts:

| Token | CSS var | Hex |
|-------|---------|-----|
| Primary teal | `--pe-color-primary-500` | #319795 |
| Light teal | `--pe-color-primary-200` | #81E6D9 |
| Dark background | (custom) | #1a2332 |
| Text gray | `--pe-color-gray-400` | #9CA3AF |
| White | `--pe-color-bg-primary` | #FFFFFF |

### Typography
- Font family: Inter (Google Fonts)
- Headlines: 800 weight, -0.02em letter-spacing
- Body: 400 weight
- Labels: 700 weight, 0.1em letter-spacing, uppercase

### Logo
- White version for dark backgrounds
- Teal version for light backgrounds
- Minimum height: 28px

## Dependencies

- Google Chrome (for headless screenshot)
