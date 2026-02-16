---
description: Audit a web app's SEO — meta tags, crawlability, performance, and content structure
---

# SEO Audit: $ARGUMENTS

**READ-ONLY MODE**: This command audits a web application's SEO readiness and reports findings. It does NOT make code changes. Use the findings to create follow-up tasks or PRs.

## Options

- `--local` — Show findings locally only, skip GitHub posting
- `--repo OWNER/NAME` — Audit a specific GitHub repo (clones it to /tmp)
- No arguments — Audit the current working directory

## Examples

```bash
/audit-seo                                    # Audit current repo, prompt for posting
/audit-seo --local                            # Audit current repo, show locally only
/audit-seo --repo PolicyEngine/us-marriage-incentive   # Audit a specific repo
/audit-seo --repo PolicyEngine/us-marriage-incentive --local
```

---

## Phase 0: Parse Arguments & Setup

```
Parse $ARGUMENTS:
- LOCAL_ONLY: true if --local flag present
- REPO_ARG: value after --repo if present (e.g., "PolicyEngine/us-marriage-incentive")
- If no --repo: use current working directory
```

### Determine Posting Mode

**If `--local` flag**: Skip prompt, proceed in local-only mode.

**If no flag**: Use `AskUserQuestion`:
```
Question: "Post SEO audit findings to GitHub when complete?"
Options:
  - "Yes, create a GitHub issue with findings" (default)
  - "No, show locally only"
```

### Determine Target Repository

**If `--repo` is provided:**
```bash
# Clone to temp directory
gh repo clone $REPO_ARG /tmp/seo-audit-target -- --depth 1
AUDIT_DIR="/tmp/seo-audit-target"
```

**If no `--repo`:**
```bash
AUDIT_DIR="$(pwd)"
```

Verify this is a web application by checking for `index.html`, `frontend/index.html`, `frontend/app/layout.tsx`, or `package.json` with a frontend framework dependency. Also check for Streamlit apps (`app.py` + `requirements.txt` with `streamlit`).

---

## Phase 1: Gather Context

Collect information about the project:

```bash
# Get repo info
REPO_NAME=$(basename $(git -C $AUDIT_DIR remote get-url origin 2>/dev/null) .git || basename $AUDIT_DIR)
REPO_FULL=$(git -C $AUDIT_DIR remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||')

# Check for built output (root and monorepo)
ls $AUDIT_DIR/dist/ 2>/dev/null || ls $AUDIT_DIR/build/ 2>/dev/null
ls $AUDIT_DIR/frontend/dist/ 2>/dev/null || ls $AUDIT_DIR/frontend/build/ 2>/dev/null

# Detect project structure
ls $AUDIT_DIR/frontend/package.json 2>/dev/null  # monorepo?
ls $AUDIT_DIR/frontend/app/layout.tsx 2>/dev/null  # Next.js?
ls $AUDIT_DIR/app.py 2>/dev/null  # Streamlit?

# Identify framework (check both root and frontend/)
cat $AUDIT_DIR/package.json | grep -E '"(react|vue|svelte|next|vite|gatsby)"'
cat $AUDIT_DIR/frontend/package.json 2>/dev/null | grep -E '"(react|vue|svelte|next|vite|gatsby)"'

# Check hosting
ls $AUDIT_DIR/.github/workflows/ 2>/dev/null
cat $AUDIT_DIR/vercel.json 2>/dev/null
cat $AUDIT_DIR/netlify.toml 2>/dev/null
```

**Document:**
- Repository name and URL
- Project structure (Vite SPA, Vite Monorepo, Next.js Monorepo, Streamlit)
- Framework (React, Vue, Next.js, Streamlit, etc.)
- Build tool (Vite, CRA, Webpack, etc.)
- Hosting platform (GitHub Pages, Vercel, Netlify, Cloud Run, Modal)
- Whether built output exists locally

---

## Phase 2: Run Build (if needed)

If no `dist/` or `build/` directory exists, attempt to build:

```bash
cd $AUDIT_DIR
npm install 2>/dev/null || yarn install 2>/dev/null
npm run build 2>/dev/null || yarn build 2>/dev/null
```

The built output is needed for accurate bundle size analysis and to check what HTML Google actually receives.

If the build fails, note this and continue with source-only analysis.

---

## Phase 3: Spawn Specialist Agents

Spawn all four agents in parallel using `run_in_background: true` with `subagent_type: general-purpose`.

### Agent 1: Meta Tag Checker

Invoke **seo-meta-checker** agent:
```
Audit the web application at $AUDIT_DIR for SEO meta tags.
Follow the instructions in agents/app/seo-meta-checker.md.
Read the index.html file and check all meta tags, OG tags, Twitter cards, canonical URL, and structured data.
Report findings in the specified format.
```

### Agent 2: Crawlability Checker

Invoke **seo-crawlability-checker** agent:
```
Audit the web application at $AUDIT_DIR for crawlability.
Follow the instructions in agents/app/seo-crawlability-checker.md.
Check robots.txt, sitemap.xml, routing type, SSR/pre-rendering, 404 handling, and duplicate content risk.
Report findings in the specified format.
```

### Agent 3: Performance Checker

Invoke **seo-performance-checker** agent:
```
Audit the web application at $AUDIT_DIR for SEO-impacting performance issues.
Follow the instructions in agents/app/seo-performance-checker.md.
Check bundle sizes, code splitting, image optimization, font loading, and render-blocking resources.
Report findings in the specified format.
```

### Agent 4: Content & Structure Checker

Invoke **seo-content-checker** agent:
```
Audit the web application at $AUDIT_DIR for content structure and semantic HTML.
Follow the instructions in agents/app/seo-content-checker.md.
Check heading hierarchy, semantic elements, link quality, accessibility, and content quality.
Report findings in the specified format.
```

---

## Phase 4: Collect & Score Results

Wait for all agents to complete. Aggregate their scores.

### Scoring

Each agent scores their domain out of their total checks. Combine into an overall score:

| Category | Agent | Max Points | Weight |
|----------|-------|-----------|--------|
| Meta Tags | seo-meta-checker | 18 | 30% |
| Crawlability | seo-crawlability-checker | 7 | 30% |
| Performance | seo-performance-checker | 7 | 20% |
| Content & Structure | seo-content-checker | 7 | 20% |

**Overall Score** = weighted average, expressed as percentage (0-100%).

### Score Interpretation

| Score | Rating | Meaning |
|-------|--------|---------|
| 80-100% | Excellent | SEO-ready, minor improvements possible |
| 60-79% | Good | Fundamentals covered, some gaps |
| 40-59% | Needs Work | Significant gaps affecting discoverability |
| 20-39% | Poor | Major issues preventing indexing |
| 0-19% | Critical | Essentially invisible to search engines |

---

## Phase 5: Compile Report

### Determine Deployed URL

Try to determine the live URL:
- Check for CNAME file in `public/` or repo root
- Check GitHub Pages settings: `https://{org}.github.io/{repo}/`
- Check vercel.json or netlify.toml for custom domains
- If policyengine.org embeds the app, note both URLs

### Report Structure

```markdown
## SEO Audit Report: {REPO_NAME}

**Score: XX/100 ({Rating})**
**Deployed URL:** {URL or "Unknown"}
**Framework:** {React/Vue/etc.} + {Vite/CRA/etc.}
**Hosting:** {GitHub Pages/Vercel/Netlify}

---

### Summary

| Category | Score | Status |
|----------|-------|--------|
| Meta Tags | X/18 | {emoji} |
| Crawlability | X/7 | {emoji} |
| Performance | X/7 | {emoji} |
| Content & Structure | X/7 | {emoji} |

### Critical Issues (must fix)

1. **{Issue}** — {Description and why it matters}
2. ...

### Important Issues (should fix)

1. **{Issue}** — {Description}
2. ...

### Suggestions (nice to have)

1. **{Issue}** — {Description}
2. ...

---

### Detailed Findings

#### Meta Tags
{Full report from seo-meta-checker}

#### Crawlability
{Full report from seo-crawlability-checker}

#### Performance
{Full report from seo-performance-checker}

#### Content & Structure
{Full report from seo-content-checker}

---

### Standalone + Iframe Assessment

- **Standalone URL:** {GitHub Pages URL}
- **Embedded on:** {policyengine.org URL if detectable}
- **Canonical strategy:** {Present/Missing/Misconfigured}
- **Duplicate content risk:** {Low/Medium/High}

### Next Steps

1. {Prioritized action item}
2. {Prioritized action item}
3. ...

---
*Audited by `/audit-seo` — PolicyEngine Claude Plugin*
```

---

## Phase 6: Post Results

**If user chose local-only mode**: Display the full report in the terminal.

**If user chose to post to GitHub**: Create a GitHub issue on the audited repo.

```bash
gh issue create \
  --repo "$REPO_FULL" \
  --title "SEO Audit: Score XX/100 — {N} critical issues found" \
  --body "$REPORT_BODY" \
  --label "seo,audit"
```

If the `seo` or `audit` labels don't exist, create the issue without labels:
```bash
gh issue create \
  --repo "$REPO_FULL" \
  --title "SEO Audit: Score XX/100 — {N} critical issues found" \
  --body "$REPORT_BODY"
```

Report the issue URL to the user.

---

## Key Rules

1. **READ-ONLY**: Never edit files. This is an audit.
2. **Build if possible**: Bundle sizes from built output are more accurate than estimates.
3. **Account for dual-mode**: Always check for standalone + iframe usage patterns.
4. **Prioritize findings**: Critical > Important > Suggestions.
5. **Be actionable**: Every finding should include what to do about it.
6. **Score consistently**: Use the same scoring across all repos for comparison.

---

## Pre-Flight Checklist

Before starting:
- [ ] I will NOT make any code changes
- [ ] I will ask about posting mode FIRST (unless --local flag used)
- [ ] I will run all 4 specialist checks
- [ ] I will account for the standalone + iframe dual-mode
- [ ] I will prioritize findings by severity
- [ ] I will include actionable next steps

Start by parsing arguments, then proceed through all phases.
