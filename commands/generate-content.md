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

1. **Parses the source** - Extracts title, key quotes, author info, and main content
2. **Generates localized variants** - Creates UK and US versions with appropriate:
   - Spelling (modeling vs modelling)
   - References (10 Downing Street vs UK Prime Minister's office)
   - Context framing
   - Flags and regional sections
3. **Renders outputs**:
   - **Social images**: 1200x630 PNGs via Chrome headless
   - **Social copy**: Platform-optimized text for LinkedIn/X

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
