---
description: Scaffold a new PolicyEngine interactive tool (Vite + React + design system + embedding boilerplate)
---

# New interactive tool scaffold

Creates a complete project for a standalone PolicyEngine interactive tool that embeds in policyengine.org.

## Step 1: Gather requirements

Ask the user for:
1. **Tool name** (kebab-case, e.g., `marriage`, `aca-calc`, `salary-sacrifice-tool`)
2. **Countries** (us, uk, or both)
3. **Data pattern** — how the tool gets model results:
   - **A) Precomputed** — Static JSON shipped with the app (best for finite parameter spaces)
   - **B) PolicyEngine API** — Direct calls to `api.policyengine.org/us/calculate` (best for household calculators)
   - **C) Custom Modal API** — Python serverless function with policyengine-us/uk (best when main API doesn't support needed variables/reforms)
4. **Brief description** of what the tool calculates

## Step 2: Create the project

```bash
# Create Vite + React project
npm create vite@latest TOOL_NAME -- --template react
cd TOOL_NAME

# Install dependencies
npm install @policyengine/design-system
npm install -D vitest

# If using Recharts for charts:
npm install recharts
```

## Step 3: Generate project files

Create the following files with the content specified below. Replace `TOOL_NAME`, `TOOL_TITLE`, `DESCRIPTION`, and `COUNTRY_ID` with actual values.

### vite.config.js

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/",
});
```

### index.html

Replace the default `<head>` content with:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>TOOL_TITLE — PolicyEngine</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/@policyengine/design-system/dist/tokens.css">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### src/main.jsx

```jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

### src/App.jsx

```jsx
import { useState } from "react";

function getCountryFromHash() {
  const params = new URLSearchParams(window.location.hash.slice(1));
  return params.get("country") || "us";
}

export default function App() {
  const [countryId] = useState(getCountryFromHash());
  const isEmbedded = window.self !== window.top;

  function updateHash(params) {
    const p = new URLSearchParams();
    // Add your params here, e.g.: p.set("income", params.income);
    if (countryId !== "us" && !isEmbedded) p.set("country", countryId);
    const hash = `#${p.toString()}`;
    window.history.replaceState(null, "", hash);
    if (isEmbedded) {
      window.parent.postMessage({ type: "hashchange", hash }, "*");
    }
  }

  function getShareUrl() {
    const hash = window.location.hash;
    if (isEmbedded) {
      return `https://policyengine.org/${countryId}/TOOL_NAME${hash}`;
    }
    return window.location.href;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>TOOL_TITLE</h1>
        <p>DESCRIPTION</p>
      </header>
      <main className="app-main">
        {/* Your tool UI goes here */}
      </main>
    </div>
  );
}
```

### src/styles.css

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--pe-font-family-primary);
  color: var(--pe-color-text-primary);
  background: var(--pe-color-bg-primary);
  line-height: 1.5;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--pe-space-lg) var(--pe-space-xl);
}

.app-header {
  margin-bottom: var(--pe-space-3xl);
}

.app-header h1 {
  font-size: var(--pe-font-size-2xl);
  font-weight: var(--pe-font-weight-bold);
  margin-bottom: var(--pe-space-xs);
}

.app-header p {
  color: var(--pe-color-text-secondary);
  font-size: var(--pe-font-size-sm);
}

.button-primary {
  background: var(--pe-color-primary-500);
  color: white;
  border: none;
  border-radius: var(--pe-radius-md);
  padding: var(--pe-space-sm) var(--pe-space-xl);
  font-family: inherit;
  font-size: var(--pe-font-size-sm);
  font-weight: var(--pe-font-weight-semibold);
  cursor: pointer;
  transition: background 0.15s;
}

.button-primary:hover {
  background: var(--pe-color-primary-600);
}

.button-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .app {
    padding: var(--pe-space-md) var(--pe-space-lg);
  }
}

@media (max-width: 480px) {
  .app-header h1 {
    font-size: var(--pe-font-size-xl);
  }
}
```

### favicon.svg

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <circle cx="16" cy="16" r="14" fill="#319795"/>
  <text x="16" y="21" text-anchor="middle" font-family="system-ui" font-size="16" font-weight="700" fill="white">$</text>
</svg>
```

## Step 4: Data pattern boilerplate

Based on the user's choice, add the appropriate data fetching code.

**For Pattern B (PolicyEngine API):** Create `src/api.js`:

```js
const API_BASE = "https://api.policyengine.org";

export async function calculate(countryId, household) {
  const res = await fetch(`${API_BASE}/${countryId}/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ household }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

**For Pattern C (Modal API):** Create `modal_app.py`:

```python
import modal

app = modal.App("TOOL_NAME")
image = modal.Image.debian_slim().pip_install("policyengine-us==X.Y.Z")

@app.function(image=image, timeout=300)
@modal.web_endpoint(method="POST")
def calculate(params: dict):
    from policyengine_us import Simulation
    # Build household from params
    sim = Simulation(situation=household)
    return {"result": float(sim.calculate("variable_name", 2025).sum())}
```

And `src/api.js`:

```js
const API_URL = import.meta.env.VITE_API_URL || "https://policyengine--TOOL_NAME-calculate.modal.run";

export async function calculate(params) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

## Step 5: Initialize git and deploy

```bash
# Initialize repo
git init
git add -A
git commit -m "Initial scaffold for TOOL_TITLE"

# Create GitHub repo under PolicyEngine org
gh repo create PolicyEngine/TOOL_NAME --public --source=.
git push -u origin main

# Deploy to Vercel
vercel link --scope policy-engine
vercel --prod --yes
```

If using Pattern C (Modal):
```bash
unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET
modal deploy modal_app.py
vercel env add VITE_API_URL production
# Enter the Modal URL
vercel --prod --force --yes --scope policy-engine
```

## Step 6: Register in apps.json

Add entry to `policyengine-app-v2/app/src/data/apps/apps.json`. Use the auto-assigned Vercel production URL (not a custom alias).

## Step 7: Verify

```bash
# Check deployment
curl -s -o /dev/null -w "%{http_code}" https://VERCEL_URL/

# Start dev server for local development
npm run dev
```

## Reference

See these skills for detailed guidance:
- `policyengine-interactive-tools-skill` — Embedding, hash sync, country detection
- `policyengine-design-skill` — Token reference
- `policyengine-vercel-deployment-skill` — Deployment patterns
