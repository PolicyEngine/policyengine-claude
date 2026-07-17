---
description: Audit a web app's SEO in a single read-only pass — meta tags, Open Graph, canonical, crawlability, plus the PolicyEngine embed/canonical gotchas
allowed-tools: Read, Glob, Grep, Bash, WebFetch, AskUserQuestion
---

# SEO audit: $ARGUMENTS

**Read-only.** Run every check yourself in one pass — no subagents. Report findings; make no code changes.

## Options
- `--url <URL>` — audit a deployed page directly (fetch its served HTML).
- `--repo OWNER/NAME` — shallow-clone to `/tmp/seo-audit-target` and audit its built `index.html`.
- `--local` — print findings only; skip the GitHub-issue prompt.
- No args — audit the current working directory's built output.

## Step 1: Get the HTML the crawler sees
- Deployed URL (`--url`, or a CNAME / `vercel.json` / Pages URL you locate): `WebFetch` it, or `curl -sL <URL>`. `curl` returns the raw pre-JS shell — that is what Googlebot indexes first.
- Local: build if needed (`bun install && bun run build`, else `npm`), then read `dist/index.html` or `build/index.html` (check a `frontend/` subdir too for monorepos).

## Step 2: Meta, Open Graph, canonical (check directly)
- `<title>` (unique, ≤60 chars) and `<meta name="description">` (≤160 chars).
- Open Graph: `og:title`, `og:description`, `og:image` (absolute URL), `og:url`, `og:type`.
- Twitter: `twitter:card`, `twitter:title`, `twitter:image`.
- `<link rel="canonical">` present and absolute (see Step 4 for which URL).
- Structured data (`application/ld+json`) where the page warrants it.

## Step 3: Crawlability
- `curl -sL <origin>/robots.txt` and `/sitemap.xml` — present, reachable, and the sitemap lists real URLs.
- SPA shells (Vite/CRA) ship a near-empty `<body>`; confirm prerendering/SSG (or Next.js SSR) so crawlers receive real content and headings, not just a loading div.
- Exactly one `<h1>`, sane heading hierarchy, and `lang` set on `<html>`.

## Step 4: PolicyEngine-specific atoms
1. **Dual-mode canonical.** PE tools run both standalone (Vercel/Pages) and embedded as an iframe/zone on policyengine.org. The `canonical` must point to the ONE indexable home (the standalone deploy) so the two copies don't compete as duplicate content.
2. **Multi-zone paths.** When the tool is a path-mounted zone under policyengine.org, its canonical / `og:url` / sitemap URLs must use the public `policyengine.org/<path>` URL — never the raw Vercel host or `_zones/` asset URL. See the `policyengine-tools` skill (multi-zone integration).
3. **`.github.io` Search Console (legacy note).** Project sites under `policyengine.github.io/<repo>` can't be independently verified in Search Console (the org owns the apex), so their standalone indexing was always weak. New tools deploy to Vercel — treat any `github.io` target as legacy.

## Step 5: Report
Group findings as Critical / Important / Suggestions, each paired with its fix. State the standalone URL, the embedding URL (if any), and the canonical strategy (present / missing / misconfigured).

Unless `--local`, offer to open a GitHub issue on the audited repo via `AskUserQuestion`. If yes:
```bash
gh issue create --repo "$REPO_FULL" \
  --title "SEO audit: {N} critical issues" \
  --body "$REPORT_BODY" --label "seo,audit"   # retry without --label if the labels don't exist
```
Report the issue URL.
