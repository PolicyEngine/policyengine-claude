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

## Stack

- Vite + React (JSX, not TypeScript unless complex)
- `@policyengine/design-system` for tokens (CSS import or npm)
- Plain CSS with CSS custom properties (not vanilla-extract — standalone tools are small)
- Deploy to Vercel under `policy-engine` scope (see `policyengine-vercel-deployment-skill`)
- Vitest for testing

## Data and computation patterns

Choose based on what the tool needs from PolicyEngine:

### Pattern A: Precomputed data

Best when the parameter space is small enough to enumerate, or the tool shows static analysis results.

**When to use:** Dashboards showing pre-run scenarios, legislative trackers, tools where inputs map to a finite set of outputs.

```
┌─────────────┐    ┌──────────┐    ┌───────────┐
│ Python script│───>│ JSON file│───>│ React app │
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
│ React app │───>│ api.policyengine │───>│ Results  │
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
│ React app │───>│ Modal serverless │───>│ policyengine │
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
const API_URL = import.meta.env.VITE_API_URL || "https://policyengine--my-tool-calculate.modal.run";

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
vercel env add VITE_API_URL production
# Enter: https://policyengine--my-tool-calculate.modal.run
vercel --prod --force --yes --scope policy-engine
```

**Pros:** Full control over calculations, can use any policyengine variables/reforms, can do microsimulation. **Cons:** Cold starts (5-15s first call), Modal costs, must pin policyengine version, must redeploy when policy rules update.

**Failure mode:** Modal apps can silently disappear. If frontend gets network errors, `curl` the Modal URL — if 404, redeploy.

## Scaffolding a new tool

```bash
npm create vite@latest my-tool -- --template react
cd my-tool
npm install @policyengine/design-system
npm install -D vitest
```

**vite.config.js:**
```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/",
});
```

**index.html — add Inter font and tokens.css:**
```html
<head>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://unpkg.com/@policyengine/design-system/dist/tokens.css">
</head>
```

Or import locally:
```css
/* styles.css */
@import '@policyengine/design-system/tokens.css';
```

**Use the CSS variables:**
```css
body {
  font-family: var(--pe-font-family-primary);
  color: var(--pe-color-text-primary);
  background: var(--pe-color-bg-primary);
}

.button-primary {
  background: var(--pe-color-primary-500);
  color: white;
  border-radius: var(--pe-radius-md);
  padding: var(--pe-space-sm) var(--pe-space-lg);
}
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

**App types:** `iframe` (standard), `streamlit` (adds `?embedded=true`), `obbba-iframe` (special layout), `custom` (React component).

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

**For standard charts:** Recharts is the PE standard:
```bash
npm install recharts
```

**For simple visualizations:** Use SVG directly. The marriage calculator uses hand-rolled SVG heatmaps.

**Color conventions:**
- Positive/bonus: `var(--pe-color-primary-500)` (`#319795`)
- Negative/penalty: `var(--pe-color-gray-600)` or `var(--pe-color-error)`
- Neutral: `var(--pe-color-gray-200)`

**Inverted metrics (taxes):** When positive delta means bad (more taxes), pass `invertDelta` to your chart component to flip labels and colors.

## Mobile responsiveness

```css
/* Tablet — sidebar collapses to top */
@media (max-width: 768px) { ... }

/* Phone — form rows stack */
@media (max-width: 480px) {
  .form-row { flex-direction: column; }
}

/* Small tablet — tighten spacing */
@media (max-width: 1024px) { ... }
```

**Key patterns:**
- Collapsible sidebar with summary toggle on mobile
- Sticky first column on data tables for horizontal scroll
- Reduce chart heights on small screens
- Stack form fields vertically below 480px

## Testing

```bash
npm install -D vitest
npx vitest run
```

Test API responses against Python fixtures for numerical accuracy. See `PolicyEngine/marriage/tests/` for examples.

## Checklist for new tools

- [ ] Vite + React scaffold with `base: "/"`
- [ ] `@policyengine/design-system` tokens (CSS import or CDN)
- [ ] Inter font loaded via Google Fonts
- [ ] Sentence case on all UI text
- [ ] Data pattern chosen (precomputed / API / Modal)
- [ ] Country detection from hash (`#country=uk`)
- [ ] Hash sync with postMessage to parent
- [ ] Share URLs point to policyengine.org
- [ ] Hide country toggle when embedded
- [ ] Registered in apps.json (with cover image if `displayWithResearch`)
- [ ] Deployed to Vercel under `policy-engine` scope
- [ ] Mobile responsive (768px, 480px breakpoints)
- [ ] Tests passing

## Related skills

- `policyengine-design-skill` — Full token reference
- `policyengine-vercel-deployment-skill` — Vercel deployment patterns
- `policyengine-app-skill` — app-v2 development (different from standalone tools)
