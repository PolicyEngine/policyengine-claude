---
name: generate-content
description: Generate social images and posts from a blog post or announcement
arguments:
  - name: source
    description: URL or file path to the blog post/announcement
    required: true
  - name: audiences
    description: Comma-separated list of audiences (uk, us, global)
    default: "uk,us"
  - name: outputs
    description: Comma-separated list of outputs (social-image, social-copy, all)
    default: "all"
---

# Content generation command

Generate branded PolicyEngine content from a source blog post or announcement.

## What this command does

Orchestrates the content-generation pipeline through two dedicated agents:

1. `content-orchestrator` (agent) — parses the source, generates localized variants (UK/US spelling, references, framing), and renders the outputs (social images via Chrome headless, social copy for LinkedIn/X).
2. `neutrality-reviewer` (agent) — reviews the generated copy for advocacy language, speculation, or one-sided framing before publish. See `targets/claude/agents/shared/neutrality-reviewer.md`.

The command is the entry point; the agents own the mechanics. Loads `content-generation` skill for templates and `policyengine-writing` skill for the tone standard.

## Usage

```bash
# Generate all content for UK and US audiences
/generate-content --source https://policyengine.org/uk/research/policyengine-10-downing-street

# Generate only social images for UK
/generate-content --source ./blog-post.md --audiences uk --outputs social-image
```

## Output structure

```
output/
├── social/
│   ├── social-uk.png
│   └── social-us.png
└── copy/
    └── social-posts.md
```

## Required information

The command will prompt for any missing information:
- **Headline**: Main announcement headline
- **Quote**: Pull quote for social image
- **Quote attribution**: Name and title of person quoted
- **Headshot URL**: URL to headshot image for quote block

## Customization

Edit the template in `skills/content/content-generation-skill/templates/`:
- `social-image.html` - Social media image template
