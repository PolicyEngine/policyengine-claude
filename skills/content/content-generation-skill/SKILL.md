# Content generation skill

Use this skill when generating marketing content from PolicyEngine blog posts, research, or announcements. This includes newsletters, social media images, and social post copy.

## Overview

This skill provides templates and patterns for generating consistent, branded PolicyEngine content across multiple channels and audiences (UK, US, global).

## Content types

### Social media images

1200x630 PNG images for LinkedIn, X (Twitter), and Facebook with:
- PolicyEngine brand colors (teal #319795, dark background #1a2332)
- Inter font family
- Headline with teal highlight
- Optional headshot with quote
- PolicyEngine logo
- Audience-appropriate flags

### Newsletters

HTML email templates for Mailchimp with:
- Responsive table-based layout (email client compatible)
- Hero section with gradient
- Quote blocks with headshots
- Feature highlight sections
- CTAs with proper button styling
- Mailchimp merge tags for personalization

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

### Newsletter template

```
audience: "uk" | "us" | "global"
hero_label: Badge text (e.g., "Major announcement")
hero_title: Main headline
hero_subtitle: Supporting text
quote_text: Pull quote
quote_author: Author name
quote_title: Author title
quote_image: Author headshot URL
main_content: HTML content for main story
sections: Array of additional sections
cta_primary_text: Primary button text
cta_primary_url: Primary button URL
cta_secondary_text: Secondary button text (optional)
cta_secondary_url: Secondary button URL (optional)
```

## Workflow

1. **Parse source** - Extract key information from blog post/announcement
2. **Generate variants** - Create UK and US versions with appropriate localization
3. **Render assets** - Generate images via Chrome headless, HTML for newsletters
4. **Create drafts** - Upload to Mailchimp, save files locally
5. **Output summary** - Provide paths and links to all generated content

## Brand guidelines

### Colors
- Primary teal: #319795
- Light teal: #5EEAD4
- Dark background: #1a2332 / #0F172A
- Text gray: #94A3B8
- White: #FFFFFF

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
- Mailchimp API key (for newsletter drafts)
