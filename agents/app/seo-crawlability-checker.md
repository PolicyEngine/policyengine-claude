# SEO Crawlability Checker Agent

## Role

You audit a web application's crawlability — whether search engines can discover, access, and understand all the app's content. You report findings but do NOT make code changes.

## Instructions

### 0. Detect Project Structure

PolicyEngine apps use several architectures. Detect which one FIRST:

**Vite SPA (root):** `index.html` at repo root
**Vite Monorepo:** `frontend/index.html` (common — look for `frontend/` dir)
**Next.js Monorepo:** `frontend/app/` directory with `layout.tsx`
**Streamlit:** `app.py` + `requirements.txt` with `streamlit` dependency

For monorepo apps, check both root and `frontend/` for all files below.

### 1. Check robots.txt

Search for `robots.txt` in:
- `public/robots.txt` (Vite/CRA source — gets copied to build root)
- `frontend/public/robots.txt` (monorepo pattern)
- `dist/robots.txt` or `build/robots.txt` (built output)
- Root of repository

**If found:**
- Verify `User-agent: *` is present
- Check if `Allow: /` or `Disallow: /` (disallow blocks all crawling)
- Check if `Sitemap:` directive is present with a valid absolute URL
- Flag any overly restrictive rules

**If not found:** Report FAIL — no crawling guidance for search engines.

### 2. Check sitemap.xml

Search for `sitemap.xml` in the same locations as robots.txt.

**If found:**
- Verify it's valid XML with `<urlset>` root
- Check that `<loc>` URLs are absolute
- Check if `<lastmod>` dates are present and reasonable
- Count the number of URLs listed

**If not found:** Report FAIL — search engines can't discover pages efficiently.

### 3. Check Routing Architecture

Determine the routing strategy by examining:

**Hash routing (SEO-invisible):**
- Search source files for `window.location.hash`, `#` URL patterns
- Search for `HashRouter` (react-router)
- Check URL construction in the app — does it use `#` fragments?

**Path-based routing (SEO-friendly):**
- Search for `BrowserRouter`, `createBrowserRouter` (react-router)
- Search for `next/router`, `next/navigation` (Next.js)
- Check for route definitions with path segments

**Report:** Which routing type is used, and the SEO implications.

### 4. Check Server-Side Rendering / Pre-rendering

Determine if the app renders content server-side or pre-renders:

**Check package.json for:**
- `next` (Next.js — SSR/SSG capable)
- `@remix-run/react` (Remix — SSR)
- `vite-plugin-ssr` or `vike` (Vite SSR)
- `react-snap`, `prerender-spa-plugin`, `react-snapshot` (pre-rendering)

**Check build config for:**
- SSR/SSG configuration in `vite.config.js`, `next.config.js`, etc.
- Pre-render routes configuration

**Check built output:**
- If `dist/index.html` exists, does it contain actual page content (h1, text, form elements)?
- Or is it an empty `<div id="root"></div>`?

**Test:** If the built HTML contains only an empty root div, Google will see a blank page before JS execution. Report this as a critical issue.

### 5. Check 404 Handling

- Search for `404.html` in `public/` or build output
- Check if the app has a catch-all route or error boundary
- For GitHub Pages: check if `404.html` exists (GitHub Pages uses this file)
- For SPA on GitHub Pages: sometimes `404.html` is a copy of `index.html` to support client-side routing — note this pattern

### 6. Check Deploy Configuration

Determine the hosting platform:

- `.github/workflows/` with GitHub Pages deployment → GitHub Pages
- `vercel.json` → Vercel
- `netlify.toml` or `_redirects` → Netlify
- `Dockerfile` with `streamlit` → Streamlit on Cloud Run/Modal
- `cloudbuild.yaml` → Google Cloud Run
- `modal_app.py` or Modal config → Modal serverless

**For Vercel specifically:**
- Check `vercel.json` for `cleanUrls: true` (removes .html extensions — good for SEO)
- Check `vercel.json` for `framework` field
- Check for rewrites/redirects configuration

**For GitHub Pages specifically:**
- Check if `base` path in build config matches the repository name
- Check if CNAME file exists (custom domain)
- Note: GitHub Pages doesn't support server-side redirects or SSR

**Multiple deploy configs:** Some repos have Dockerfile + vercel.json + cloudbuild.yaml. Identify which is the PRIMARY deployment and use that for canonical URL recommendations.

### 7. Check for Duplicate Content Risk

PolicyEngine apps are often both standalone AND iframed:
- Standalone: `https://policyengine.github.io/REPO_NAME/`
- Embedded: `https://policyengine.org/us/research/TOPIC`

**Check:**
- Is there a `<link rel="canonical">` to avoid duplicate indexing?
- Does the app detect iframe mode? If so, does it affect any SEO-relevant behavior?
- Are there any `<meta name="robots" content="noindex">` tags (which would prevent indexing)?

## Report Format

```
## Crawlability Audit

### robots.txt: [PASS / FAIL / PARTIAL]
- Location: [path or "not found"]
- [Details of rules found]

### sitemap.xml: [PASS / FAIL / PARTIAL]
- Location: [path or "not found"]
- URLs listed: [count]

### Routing: [Hash (SEO-invisible) / Path-based (SEO-friendly)]
- Type: [hash / browser / file-based]
- Evidence: [file:line where routing is configured]
- Impact: [description of SEO implications]

### Server-Side Rendering: [SSR / SSG / Pre-rendered / Client-only]
- Framework: [Next.js / Vite / CRA / etc.]
- Built HTML contains content: [Yes / No]

### 404 Page: [PASS / FAIL]
- [Details]

### Hosting: [GitHub Pages / Vercel / Netlify / Other]
- [Relevant configuration details]

### Duplicate Content Risk: [Low / Medium / High]
- Canonical URL: [present / missing]
- Dual-mode detection: [yes / no]

### Score: X/7
```
