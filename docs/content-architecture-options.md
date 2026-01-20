# Content generation architecture options

## Current landscape

### Repositories involved

| Repo | Purpose | Content format | Current automation |
|------|---------|----------------|-------------------|
| **policyengine-app-v2** | Blog posts | Markdown + JSON index | None - manual file creation |
| **newsletters** | Email campaigns | HTML files | `/create-newsletter`, `/upload-draft` commands |
| **policyengine-claude** | Claude plugins | Skills/templates | `content-orchestrator` agent (new) |
| **teamverse** | Internal team tool | Unknown | Unknown |

### Current content flow

```
Blog post written → Manual copy to:
  ├── app-v2/articles/*.md + posts.json + image
  ├── newsletters/editions/*.html (reformatted)
  ├── Social media (copy/paste)
  └── teamverse (unknown)
```

**Problems:**
1. Same content duplicated 3-4 times with manual reformatting
2. No single source of truth
3. Templates scattered across repos
4. No automated testing for rendered output
5. Inconsistent branding (different templates diverge over time)
6. No validation that all channels received the content

---

## Option A: Centralized content package (policyengine-content)

**Philosophy:** Content is data. A single Python package owns all content generation, templates, and rendering.

### Structure

```
policyengine-content/
├── policyengine_content/
│   ├── models/
│   │   ├── post.py           # BlogPost, Newsletter, SocialPost models
│   │   └── audience.py       # UK, US, Global audience config
│   ├── templates/
│   │   ├── social/           # Social image HTML templates
│   │   ├── newsletter/       # Email HTML templates
│   │   └── blog/             # Blog post templates (if needed)
│   ├── renderers/
│   │   ├── social.py         # Chrome headless image rendering
│   │   ├── newsletter.py     # HTML email rendering
│   │   └── validators.py     # Output validation (dimensions, colors)
│   ├── publishers/
│   │   ├── mailchimp.py      # Newsletter upload (from newsletters repo)
│   │   ├── github.py         # PR creation for app-v2
│   │   └── social.py         # Buffer/Hootsuite API (future)
│   └── cli.py                # Command-line interface
├── tests/
│   ├── test_renderers.py     # Visual regression tests
│   └── fixtures/             # Test data, expected outputs
└── pyproject.toml
```

### Workflow

```
Source (Google Doc or Markdown)
    │
    ▼
policyengine-content parse
    │
    ├──► policyengine-content render social --audience uk,us
    │       └──► /tmp/social-uk.png, /tmp/social-us.png
    │
    ├──► policyengine-content render newsletter --audience uk,us
    │       └──► /tmp/newsletter-uk.html, /tmp/newsletter-us.html
    │
    └──► policyengine-content render blog
            └──► /tmp/blog-post.md + posts.json entry

policyengine-content publish
    ├──► PR to app-v2 with blog post + image
    ├──► Mailchimp draft campaigns
    └──► Social posts to Buffer (optional)
```

### Integration with other repos

- **app-v2**: Package creates PRs via GitHub API
- **newsletters**: Package replaces `newsletter_uploader`, `/create-newsletter` calls package
- **policyengine-claude**: Plugin wraps package CLI
- **teamverse**: Package provides API or teamverse calls package

### Pros
- Single source of truth for templates and branding
- Testable with visual regression tests
- Versioned - templates change with version bumps
- CLI usable outside Claude
- Other tools (teamverse, CI/CD) can use same package

### Cons
- New repo to maintain
- Requires porting newsletter_uploader code
- More complex than current approach

---

## Option B: Content-as-data in app-v2

**Philosophy:** The blog post IS the source of truth. Everything else is derived.

### Structure

Extend app-v2's post format:

```yaml
# app/src/data/posts/articles/10-downing-street.md
---
title: PolicyEngine powers rapid policy analysis at No 10 Downing Street
description: Our CTO spent six months as an Innovation Fellow...
date: 2026-01-20
tags: [global, org, featured]
authors: [max-ghenis]
image: policyengine-10-downing-street.png

# Extended metadata for content generation
social:
  headline_prefix: "PolicyEngine powers"
  headline_highlight: "10 Downing Street"
  quote: "Now decision-makers have evidence when they need it most."
  quote_attribution: Nikhil Woodruff
  quote_title: Co-founder & CTO, PolicyEngine
  headshot: nikhil-woodruff.webp

newsletter:
  hero_label: Major announcement
  sections:
    - type: quote
    - type: body
    - type: features
      items: [modern-tech, calibration, coverage, local-area]
---

Blog post content here...
```

### Workflow

```
app-v2 post with extended frontmatter
    │
    ▼
GitHub Action or Claude command
    │
    ├──► Generate social images from frontmatter
    ├──► Generate newsletter HTML from frontmatter + content
    └──► Generate social copy from content

PR includes:
  - Blog post markdown
  - Generated social images
  - Generated newsletter (or link to newsletters repo PR)
```

### Integration

- **app-v2**: Source of truth, GitHub Actions generate assets
- **newsletters**: Receives generated HTML via PR or API
- **policyengine-claude**: Helps author extended frontmatter
- **teamverse**: Reads from app-v2 API or posts.json

### Pros
- Blog post is canonical - everything derived from it
- No new repo
- Content versioned with blog posts
- Easy to regenerate assets from source

### Cons
- Couples content generation to app-v2
- Extended frontmatter adds complexity to post format
- GitHub Actions for rendering may be slow/fragile

---

## Option C: Newsletters repo as content hub

**Philosophy:** Newsletters already have automation. Expand it to be the content hub.

### Structure

```
newsletters/
├── content/
│   ├── sources/              # Source documents (markdown)
│   │   └── 2026-01-20-10-downing-street.md
│   ├── generated/
│   │   ├── social/           # Generated social images
│   │   ├── blog/             # Generated blog post markdown
│   │   └── newsletters/      # Generated newsletter HTML
│   └── templates/            # Move templates here
├── src/
│   └── policyengine_content/ # Expanded from newsletter_uploader
├── scripts/
│   └── publish_to_app_v2.py  # Create PRs to app-v2
└── .claude/
    └── commands/
        ├── create-content.md # New: generates all content types
        └── publish.md        # New: pushes to all destinations
```

### Workflow

```
/create-content --source https://docs.google.com/... --audiences uk,us

Generates:
  content/generated/social/10-downing-street-uk.png
  content/generated/social/10-downing-street-us.png
  content/generated/newsletters/2026-01-20-uk.html
  content/generated/newsletters/2026-01-20-us.html
  content/generated/blog/10-downing-street.md

/publish --target all
  ├──► PR to app-v2
  ├──► Mailchimp drafts
  └──► Social copy to clipboard/file
```

### Integration

- **app-v2**: Receives PRs from newsletters repo
- **newsletters**: Becomes the content hub
- **policyengine-claude**: Commands call newsletter repo scripts
- **teamverse**: Could pull from newsletters repo

### Pros
- Builds on existing automation
- Keeps all content generation in one place
- Newsletter expertise already there

### Cons
- Repo name becomes misleading ("newsletters" doing blog posts)
- Tight coupling between newsletter and blog workflows
- May outgrow the repo's scope

---

## Option D: Decentralized with shared templates

**Philosophy:** Keep repos separate but share templates and branding through a common package.

### Structure

```
policyengine-brand/              # Tiny package - just templates and tokens
├── policyengine_brand/
│   ├── tokens.py               # Colors, fonts, spacing
│   ├── templates/
│   │   ├── social-image.html
│   │   └── newsletter-base.html
│   └── render.py               # Minimal rendering utilities
└── pyproject.toml

# Each repo depends on policyengine-brand
newsletters/                     # Uses brand templates
policyengine-claude/             # Uses brand templates
app-v2/                          # Uses brand tokens for consistency
teamverse/                       # Uses brand templates
```

### Workflow

Each repo maintains its own automation but pulls templates from shared package:

```python
from policyengine_brand import render_social_image, tokens

image = render_social_image(
    headline="PolicyEngine powers",
    highlight="10 Downing Street",
    # ...
)
```

### Pros
- Minimal coupling between repos
- Templates stay consistent via package updates
- Each team owns their workflow
- Easy to adopt incrementally

### Cons
- Still duplicated automation logic
- Coordination overhead when templates change
- No single place to generate all content types

---

## Recommendation

**Option A (Centralized package)** is best if:
- Content generation is frequent (weekly+)
- Multiple people create content
- Testing and reliability are important
- You want CLI tools outside Claude

**Option B (Content-as-data in app-v2)** is best if:
- Blog posts are the primary output
- You want minimal new infrastructure
- GitHub Actions are acceptable for generation

**Option D (Shared templates)** is best if:
- You want incremental adoption
- Teams prefer autonomy
- Content generation is infrequent

### My recommendation: Option A (policyengine-content)

For PolicyEngine's scale and the importance of consistent, high-quality content across channels:

1. **Create `policyengine-content` package** with:
   - Content models (BlogPost, Newsletter, SocialPost)
   - Renderers with visual regression tests
   - Publishers for GitHub PRs, Mailchimp, (future: social APIs)
   - CLI interface

2. **Migrate incrementally**:
   - Port `newsletter_uploader` first
   - Add social image rendering
   - Add blog post generation
   - Add app-v2 PR creation

3. **Integration**:
   - `policyengine-claude` wraps CLI with agent
   - `newsletters` deprecates local uploader, uses package
   - `teamverse` calls package API
   - CI can use package for automated content generation

4. **Testing**:
   - Visual regression tests for rendered output
   - Edge color checks (no white ribbons)
   - Dimension validation
   - Branding consistency checks

---

## Questions to resolve

1. **What is teamverse?** Need to understand its role to design integration
2. **Who creates content?** Affects whether CLI or Claude integration is primary
3. **Frequency?** Daily → invest in automation; Monthly → simpler is fine
4. **Social media publishing?** Manual or automated (Buffer, Hootsuite)?
5. **Approval workflow?** Who reviews before publishing?
