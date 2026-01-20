---
name: generate-content
description: Generate newsletters, social images, and posts from a blog post or announcement
arguments:
  - name: source
    description: URL or file path to the blog post/announcement
    required: true
  - name: audiences
    description: Comma-separated list of audiences (uk, us, global)
    default: "uk,us"
  - name: outputs
    description: Comma-separated list of outputs (newsletter, social-image, social-copy, all)
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
   - **Newsletters**: HTML emails ready for Mailchimp
   - **Social copy**: Platform-optimized text for LinkedIn/X
4. **Creates drafts** - Optionally uploads newsletters to Mailchimp as drafts

## Usage

```bash
# Generate all content for UK and US audiences
/generate-content --source https://policyengine.org/uk/research/policyengine-10-downing-street

# Generate only social images for UK
/generate-content --source ./blog-post.md --audiences uk --outputs social-image

# Generate newsletters only
/generate-content --source https://policyengine.org/us/research/some-post --outputs newsletter
```

## Output structure

```
output/
├── social/
│   ├── social-uk.png
│   └── social-us.png
├── newsletters/
│   ├── newsletter-uk.html
│   └── newsletter-us.html
└── copy/
    └── social-posts.md
```

## Required information

The command will prompt for any missing information:
- **Headline**: Main announcement headline
- **Quote**: Pull quote for social image and newsletter
- **Quote attribution**: Name and title of person quoted
- **Headshot URL**: URL to headshot image for quote block
- **CTAs**: Links for newsletter buttons

## Integration with Mailchimp

If `MAILCHIMP_API_KEY` is set, the command can create draft campaigns:
- Automatically segments by audience (UK vs non-UK subscribers)
- Sets subject line and preview text
- Uploads HTML content

## Customization

Edit templates in `skills/content/content-generation-skill/templates/`:
- `social-image.html` - Social media image template
- `newsletter-base.html` - Newsletter HTML template
