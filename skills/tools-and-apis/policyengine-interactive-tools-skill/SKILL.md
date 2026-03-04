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
| CSS | Tailwind 4 with `@theme` mapping PE tokens |
| Charts | Recharts |
| Code highlighting | Prism React Renderer |
| Testing | Vitest |
| Deploy | Vercel under `policy-engine` scope |
| Package manager | `bun` (not npm) |

**Requirements:**
- `@policyengine/design-system` tokens (CDN link in `layout.jsx`)
- Inter font via Google Fonts CDN
- Recharts for charts
- **NEVER hardcode hex colors or font names** — always use `var(--pe-color-*)` and `var(--pe-font-family-primary)`
- **PolicyEngine logo** — always use the actual logo image, never styled text. Files at `policyengine-app-v2/app/public/assets/logos/policyengine/` (white.png for dark backgrounds, teal.png for light)
- Sentence case on all UI text

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
    # Build household and reform from params
    sim = Simulation(situation=household, reform=reform)
    result = {
        "net_income_single": float(sim.calculate("household_net_income", 2025).sum()),
        "net_income_married": float(sim_married.calculate("household_net_income", 2025).sum()),
    }
    return result
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
bun add @policyengine/design-system recharts
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
          rel="stylesheet"
          href="https://unpkg.com/@policyengine/design-system/dist/tokens.css"
        />
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

**Important:** Load `tokens.css` via CDN `<link>` in `<head>`. The `@import` from `node_modules` does not work with the Next.js CSS pipeline.

### app/globals.css — map PE tokens into Tailwind `@theme`

```css
@import "tailwindcss";

@theme {
  --color-pe-primary-50: var(--pe-color-primary-50);
  --color-pe-primary-500: var(--pe-color-primary-500);
  --color-pe-primary-600: var(--pe-color-primary-600);
  --color-pe-primary-700: var(--pe-color-primary-700);

  --color-pe-gray-50: var(--pe-color-gray-50);
  --color-pe-gray-100: var(--pe-color-gray-100);
  --color-pe-gray-200: var(--pe-color-gray-200);

  --color-pe-error: var(--pe-color-error);

  --color-pe-bg-primary: var(--pe-color-bg-primary);
  --color-pe-text-primary: var(--pe-color-text-primary);
  --color-pe-text-secondary: var(--pe-color-text-secondary);
  --color-pe-text-tertiary: var(--pe-color-text-tertiary);

  --color-pe-border-light: var(--pe-color-border-light);
}

body {
  font-family: var(--pe-font-family-primary);
  color: var(--pe-color-text-primary);
  background: var(--pe-color-bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Using PE tokens in components

Use `style=` with `var()` for dynamic PE token values:

```jsx
<div style={{
  backgroundColor: "var(--pe-color-gray-50)",
  border: "1px solid var(--pe-color-border-light)",
  borderRadius: "var(--pe-radius-md)",
  padding: "var(--pe-space-lg)",
}}>
```

Or use Tailwind classes that reference the `@theme` mappings:

```jsx
<div className="bg-pe-gray-50 border border-pe-border-light rounded-md p-4">
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
- Positive/bonus: `var(--pe-color-primary-500)`
- Negative/penalty: `var(--pe-color-gray-600)` or `var(--pe-color-error)`
- Neutral: `var(--pe-color-gray-200)`

**Inverted metrics (taxes):** When positive delta means bad (more taxes), pass `invertDelta` to your chart component to flip labels and colors.

### Recharts + PE tokens

Recharts renders SVG, which **cannot inherit CSS custom properties** via `style=`. You must resolve token values at render time:

```jsx
/* Helper to read PE tokens for Recharts SVG props */
function getCssVar(name) {
  if (typeof window === "undefined") return "";
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

// In your chart component:
const primaryColor = getCssVar("--pe-color-primary-500");
const errorColor = getCssVar("--pe-color-error");
const gridColor = getCssVar("--pe-color-border-light");
const fontFamily = getCssVar("--pe-font-family-primary");

<BarChart data={data}>
  <CartesianGrid stroke={gridColor} />
  <XAxis tick={{ fontSize: 12, fontFamily }} />
  <YAxis tick={{ fontSize: 12, fontFamily }} />
  <Bar dataKey="value" fill={primaryColor} />
</BarChart>
```

**Never pass hardcoded hex values** like `fill="#319795"` to Recharts — always resolve from CSS variables.

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
- [ ] `@policyengine/design-system` tokens loaded via CDN `<link>` in layout.jsx
- [ ] PE tokens mapped in `globals.css` `@theme` block
- [ ] Inter font loaded via Google Fonts CDN
- [ ] **Zero hardcoded hex colors** — all colors via `var(--pe-color-*)`
- [ ] **Zero hardcoded font names** — all fonts via `var(--pe-font-family-primary)`
- [ ] Recharts charts use `getCssVar()` helper for SVG props (font, colors)
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
