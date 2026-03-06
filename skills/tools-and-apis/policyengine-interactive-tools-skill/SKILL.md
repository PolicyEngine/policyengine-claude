---
name: policyengine-interactive-tools
description: Building standalone interactive calculators and dashboards that embed in policyengine.org
---

# PolicyEngine interactive tools

How to build standalone React apps (calculators, dashboards, visualizations) that embed in policyengine.org via iframe.

## Examples

- Marriage calculator (`PolicyEngine/marriage`) — uses PolicyEngine API
- GiveCalc (`PolicyEngine/givecalc`) — custom Modal API with policyengine-us
- ACA reforms calculator (`PolicyEngine/aca-calc`) — precomputed data
- State legislative tracker (`PolicyEngine/state-legislative-tracker`) — static data
- UK salary sacrifice tool (`PolicyEngine/uk-salary-sacrifice-analysis`)
- SNAP BBCE repeal dashboard (`PolicyEngine/snap-bbce-repeal`) — precomputed CSV dashboard

## Stack

**Next.js 14 + Tailwind 4 + Recharts** for all tools (embeddable and standalone).

| Component | Choice |
|-----------|--------|
| Framework | Next.js 14 (App Router) |
| CSS | Tailwind 4 with `@policyengine/ui-kit` theme |
| Charts | Recharts |
| Code highlighting | Prism React Renderer |
| Testing | Vitest |
| Deploy | Vercel under `policy-engine` scope |
| Package manager | `bun` (not npm) |

**Requirements:**
- `@policyengine/ui-kit` theme (installed via `bun add @policyengine/ui-kit`)
- Inter font via Google Fonts CDN
- Recharts for charts
- **NEVER hardcode hex colors or font names** — always use CSS variables from the ui-kit theme (e.g., `var(--primary)`, `var(--chart-1)`, `var(--font-sans)`)
- **PolicyEngine logo** — always use the actual logo image, never styled text. Files at `policyengine-app-v2/app/public/assets/logos/policyengine/` (white.png for dark backgrounds, teal.png for light)
- Sentence case on all UI text

## CRITICAL: Never hardcode computed data

**NEVER manually copy numbers from ad-hoc calculations (bash, Python REPL, etc.) into source files.** All data displayed in charts or UI must come from a generation script that writes to a data file (JSON, CSV) which the frontend imports.

The correct flow is always:
```
Python script (reads reform/config) → data file (JSON/CSV) → frontend imports data file
```

Never:
```
Ad-hoc Python in terminal → copy numbers → paste into .tsx/.jsx file
```

If a repo has a data generation script (e.g., `scripts/generate_*.py`), update that script and re-run it. If one doesn't exist, create one. The script should:
1. Read its parameters from the repo's config files (e.g., `reform.json`)
2. Use vectorized simulation where possible (multiple persons in one `Simulation` call)
3. Write output to a JSON/CSV file that the frontend imports
4. Be re-runnable to regenerate data when parameters change

## Data and computation patterns

Choose based on what the tool needs from PolicyEngine:

### Pattern A: Precomputed JSON

Best when the parameter space is small enough to enumerate, or the tool shows static analysis results.

**When to use:** Dashboards showing pre-run scenarios, legislative trackers, tools where inputs map to a finite set of outputs.

```
┌─────────────┐    ┌──────────┐    ┌───────────┐
│ Python script│───>│ JSON file│───>│ Next.js   │
│ (one-time)  │    │ (static) │    │ (fast)    │
└─────────────┘    └──────────┘    └───────────┘
```

**Example:** State legislative tracker pre-computes budget impacts for every state bill and ships a JSON file.

```python
# scripts/precompute.py
from policyengine_us import Microsimulation

results = {}
for reform_id, reform in reforms.items():
    sim = Microsimulation(reform=reform)
    results[reform_id] = {
        "revenue_change": float(sim.calculate("revenue_change")),
        "poverty_change": float(sim.calculate("poverty_change")),
    }

with open("src/data/results.json", "w") as f:
    json.dump(results, f)
```

```jsx
// React — just reads the JSON
import results from "./data/results.json";

function Dashboard({ reformId }) {
  const data = results[reformId];
  return <MetricCard value={data.revenue_change} />;
}
```

**Pros:** Zero latency, no API costs, works offline. **Cons:** Can't handle continuous user inputs; stale if policy changes.

### Pattern B: PolicyEngine API

Best when the tool calculates household-level impacts with varying incomes/demographics. The main PolicyEngine API (`api.policyengine.org`) handles standard household simulations.

**When to use:** Tools where users enter income, family size, state, and see tax/benefit impacts. Works when all the variables you need are in the PolicyEngine API.

```
┌───────────┐    ┌──────────────────┐    ┌──────────┐
│ Next.js   │───>│ api.policyengine │───>│ Results  │
│ (browser) │<───│ .org/us/calculate │<───│          │
└───────────┘    └──────────────────┘    └──────────┘
```

**Example:** Marriage calculator sends household JSON and gets back tax/benefit amounts.

```js
// api.js
const API_BASE = "https://api.policyengine.org";

export async function calculateHousehold(countryId, household) {
  const res = await fetch(`${API_BASE}/${countryId}/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ household }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

**Household JSON structure:**
```json
{
  "people": {
    "head": { "age": { "2025": 40 }, "employment_income": { "2025": 50000 } },
    "spouse": { "age": { "2025": 35 }, "employment_income": { "2025": 30000 } }
  },
  "tax_units": { "tax_unit": { "members": ["head", "spouse"] } },
  "spm_units": { "spm_unit": { "members": ["head", "spouse"] } },
  "households": { "household": { "members": ["head", "spouse"], "state_code": { "2025": "CA" } } }
}
```

**Comparing scenarios:** To show the effect of marriage, call the API twice (unmarried vs married household) and diff the results.

**Pros:** Always up-to-date with latest policy rules, handles arbitrary inputs. **Cons:** Network latency (1-5s per call), rate limits, limited to variables the API supports.

### Pattern C: Custom API on Modal

Best when you need variables or calculations not in the main PolicyEngine API — custom reform parameters, non-standard entity structures, or computations that combine PolicyEngine with other models.

**When to use:** Tools that vary parameters not exposed by the main API (e.g., varying UBI amounts, custom phase-outs), or tools that need microsimulation (society-wide) results for arbitrary reforms.

```
┌───────────┐    ┌──────────────────┐    ┌──────────────┐
│ Next.js   │───>│ Modal serverless │───>│ policyengine │
│ (browser) │<───│ Python function  │<───│ -us (local)  │
└───────────┘    └──────────────────┘    └──────────────┘
```

**Example:** GiveCalc lets users specify custom giving amounts and calculates the tax benefit using policyengine-us with custom reform parameters.

```python
# modal_app.py
import modal

app = modal.App("my-tool")
image = modal.Image.debian_slim().pip_install("policyengine-us==1.x.x")

@app.function(image=image, timeout=300)
@modal.web_endpoint(method="POST")
def calculate(params: dict):
    from policyengine_us import Simulation
    household = params["household"]
    sim = Simulation(situation=household)
    return {
        "net_income": float(sim.calculate("household_net_income", 2025).sum()),
    }
```

**Deploy:**
```bash
# MUST unset env vars — keychain tokens override modal profile
unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET
modal deploy modal_app.py
```

**URL pattern:** `https://policyengine--my-tool-calculate.modal.run`

**Frontend:**
```js
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://policyengine--my-tool-calculate.modal.run";

async function calculate(params) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return res.json();
}
```

**Set Vercel env var:**
```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://policyengine--my-tool-calculate.modal.run
vercel --prod --force --yes --scope policy-engine
```

**Pros:** Full control over calculations, can use any policyengine variables/reforms, can do microsimulation. **Cons:** Cold starts (5-15s first call), Modal costs, must pin policyengine version, must redeploy when policy rules update.

**Failure mode:** Modal apps can silently disappear. If frontend gets network errors, `curl` the Modal URL — if 404, redeploy.

### Pattern D: Precomputed CSV dashboard

For analysis repos that precompute data with Python microsimulation pipelines:

```
┌─────────────────┐    ┌──────────┐    ┌────────────────┐
│ Python pipeline  │───>│ CSV files│───>│ Next.js app    │
│ (Microsimulation)│    │ public/  │    │ (static export)│
└─────────────────┘    └──────────┘    └────────────────┘
```

**Python side:** Pipeline generates CSVs to `public/data/`.
**Frontend side:** Fetch CSVs at runtime, parse with a lightweight CSV parser.

**Example:** `PolicyEngine/snap-bbce-repeal`, `PolicyEngine/uk-spring-statement-2026`.

## Scaffolding a new tool

```bash
bunx create-next-app@14 my-tool --js --app --tailwind --eslint --no-src-dir --import-alias "@/*"
cd my-tool
bun add @policyengine/ui-kit recharts
bun add -D vitest
```

### app/layout.jsx

```jsx
import "./globals.css";

export const metadata = {
  title: "TOOL_TITLE | PolicyEngine",
  description: "DESCRIPTION",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

### app/globals.css — import ui-kit theme

```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";

body {
  font-family: var(--font-sans);
  color: var(--foreground);
  background: var(--background);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

The single `@import "@policyengine/ui-kit/theme.css"` replaces the entire manual `@theme` block. It provides all color, spacing, and typography tokens as CSS variables that Tailwind 4 picks up automatically.

### Using tokens in components

Use Tailwind classes from the ui-kit theme:

```jsx
<div className="bg-muted border border-border rounded-lg p-4">
```

Or use `style=` with `var()` for inline styles:

```jsx
<div style={{
  backgroundColor: "var(--muted)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  padding: "1rem",
}}>
```

## Embedding in policyengine.org

### 1. Register in apps.json

Add entry to `policyengine-app-v2/app/src/data/apps/apps.json`:

```json
{
  "type": "iframe",
  "slug": "my-tool",
  "title": "My interactive tool",
  "description": "What this tool does",
  "source": "https://my-tool-auto-url.vercel.app/",
  "tags": ["us", "featured", "policy", "interactives"],
  "countryId": "us",
  "displayWithResearch": true,
  "image": "my-tool-cover.png",
  "date": "2026-02-14 12:00:00",
  "authors": ["author-slug"]
}
```

**App types:** `iframe` (standard), `obbba-iframe` (special layout), `custom` (React component).

**Multi-country:** Same slug, different `countryId`:
```json
{ "slug": "marriage", "countryId": "us", ... },
{ "slug": "marriage", "countryId": "uk", "displayWithResearch": false, ... }
```

**Source URL:** Use the auto-assigned Vercel production URL (e.g., `marriage-zeta-beryl.vercel.app`), not a custom alias — aliases may have deployment protection issues.

**Required fields for `displayWithResearch: true`:** `image`, `date`, `authors`.

### 2. Country detection

When embedded at `/uk/my-tool`, policyengine.org injects `#country=uk` into the iframe URL.

```js
// Read country from hash — independently of other params
function getCountryFromHash() {
  const params = new URLSearchParams(window.location.hash.slice(1));
  return params.get("country") || "us";
}

const [countryId, setCountryId] = useState(getCountryFromHash());
```

**Important:** Read country independently. Don't require `region` or `income` to be present — the parent may only send `#country=uk`.

### 3. URL hash synchronization

The parent app syncs the iframe hash to the browser URL bar:

```js
// Update hash when inputs change
const hash = `#region=CA&head=50000&spouse=40000`;
window.history.replaceState(null, "", hash);

// Notify parent
if (window.self !== window.top) {
  window.parent.postMessage({ type: "hashchange", hash }, "*");
}
```

**When embedded, skip the `country` param in hash** — it's redundant with the URL path:
```js
const isEmbedded = window.self !== window.top;
if (countryId !== "us" && !isEmbedded) params.set("country", countryId);
```

### 4. Share URLs

Point to policyengine.org, not the Vercel URL:
```js
function getShareUrl(countryId) {
  const hash = window.location.hash;
  if (window.self !== window.top) {
    return `https://policyengine.org/${countryId}/my-tool${hash}`;
  }
  return window.location.href;
}
```

### 5. Country toggle

Hide when embedded (country comes from the route):
```jsx
<InputForm countries={isEmbedded ? null : COUNTRIES} ... />
```

## Charts

**Recharts is the PE standard** for all charts:
```bash
bun add recharts
```

**For simple visualizations:** Use SVG directly. The marriage calculator uses hand-rolled SVG heatmaps.

**Color conventions:**
- Positive/bonus: `var(--chart-1)`
- Negative/penalty: `var(--chart-3)` or `var(--destructive)`
- Neutral: `var(--border)`

**Inverted metrics (taxes):** When positive delta means bad (more taxes), pass `invertDelta` to your chart component to flip labels and colors.

### Recharts + ui-kit tokens

Recharts accepts CSS variables directly via `fill` and `stroke` props:

```jsx
<BarChart data={data}>
  <CartesianGrid stroke="var(--border)" />
  <XAxis niceTicks domain={["auto", "auto"]} tick={{ fontSize: 12, fontFamily: "var(--font-sans)" }} />
  <YAxis niceTicks domain={["auto", "auto"]} tick={{ fontSize: 12, fontFamily: "var(--font-sans)" }} />
  <Bar dataKey="value" fill="var(--chart-1)" />
</BarChart>
```

**Always use `niceTicks`** on `<XAxis>` and `<YAxis>` — this snaps tick values to human-friendly round numbers (e.g., `[0, 5, 10, 15]` instead of `[0, 3.5, 7, 10.5]`). Accepts `true` (boolean) or enum values `'auto'`, `'nice'`, `'equidistant'`, `'none'`. Default to `niceTicks` (boolean) for simplicity.

**Always set `domain={["auto", "auto"]}`** on axes using `niceTicks` — the default recharts domain `[0, 'auto']` clamps the minimum to 0, which breaks tick calculation for data that doesn't start at 0 (e.g., all-negative values). Setting both ends to `"auto"` lets recharts compute the domain from the data.

**Format negative dollar values as `-$100`** not `$-100` — use a custom `tickFormatter` like:
```jsx
tickFormatter={(v) => v < 0 ? `-$${Math.abs(v)}` : `$${v}`}
```

**Never pass hardcoded hex values** like `fill="#319795"` to Recharts — always use CSS variables (e.g., `fill="var(--chart-1)"`).

## Code highlighting

For tools that show code or formulas, use **Prism React Renderer**:

```bash
bun add prism-react-renderer
```

## Mobile responsiveness

Use Tailwind responsive prefixes (`sm:`, `md:`, `lg:`) or custom media queries:

```css
/* Tablet — sidebar collapses to top */
@media (max-width: 768px) { ... }

/* Phone — form rows stack */
@media (max-width: 480px) {
  .form-row { flex-direction: column; }
}
```

**Key patterns:**
- Collapsible sidebar with summary toggle on mobile
- Sticky first column on data tables for horizontal scroll
- Reduce chart heights on small screens
- Stack form fields vertically below 480px

## Testing

```bash
bun add -D vitest
bunx vitest run
```

Test API responses against Python fixtures for numerical accuracy. See `PolicyEngine/marriage/tests/` for examples.

## Checklist for new tools

- [ ] Next.js 14 + Tailwind 4 scaffold
- [ ] `@policyengine/ui-kit` installed (`bun add @policyengine/ui-kit`)
- [ ] `@import "@policyengine/ui-kit/theme.css"` in `globals.css`
- [ ] Inter font loaded via Google Fonts CDN
- [ ] **Use Tailwind classes from ui-kit theme** — no hardcoded hex colors
- [ ] **Zero hardcoded font names** — all fonts via `var(--font-sans)`
- [ ] Recharts charts use `fill="var(--chart-1)"` pattern for SVG props (font, colors)
- [ ] Recharts axes use `niceTicks` with `domain={["auto", "auto"]}` for human-friendly tick values
- [ ] Negative dollar values formatted as `-$100` not `$-100`
- [ ] PE logo is an actual image, not styled text
- [ ] Sentence case on all UI text
- [ ] Data pattern chosen (precomputed JSON / precomputed CSV / API / Modal)
- [ ] Deployed to Vercel under `policy-engine` scope
- [ ] Mobile responsive (768px, 480px breakpoints)
- [ ] Tests passing

### Additional for embeddable tools
- [ ] Country detection from hash (`#country=uk`)
- [ ] Hash sync with postMessage to parent
- [ ] Share URLs point to policyengine.org
- [ ] Hide country toggle when embedded
- [ ] Registered in apps.json (with cover image if `displayWithResearch`)

## Related skills

- `policyengine-design-skill` — Full token reference
- `policyengine-vercel-deployment-skill` — Vercel deployment patterns
- `policyengine-app-skill` — app-v2 development (different from standalone tools)
