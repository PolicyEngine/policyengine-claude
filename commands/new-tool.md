---
description: Scaffold a new PolicyEngine interactive tool (Next.js 14 + Tailwind 4 + design system + embedding boilerplate)
---

# New interactive tool scaffold

Creates a complete project for a standalone PolicyEngine interactive tool that embeds in policyengine.org.

## Step 1: Gather requirements

Ask the user for:
1. **Tool name** (kebab-case, e.g., `marriage`, `aca-calc`, `salary-sacrifice-tool`)
2. **Countries** (us, uk, or both)
3. **Data pattern** — how the tool gets model results:
   - **A) Precomputed** — Static JSON or CSV shipped with the app (best for finite parameter spaces)
   - **B) PolicyEngine API** — Direct calls to `api.policyengine.org/us/calculate` (best for household calculators)
   - **C) Custom Modal API** — Python serverless function with policyengine-us/uk (best when main API doesn't support needed variables/reforms)
4. **Brief description** of what the tool calculates

## Step 2: Create the project

```bash
# Create Next.js 14 + Tailwind project
bunx create-next-app@14 TOOL_NAME --js --app --tailwind --eslint --no-src-dir --import-alias "@/*"
cd TOOL_NAME

# Install dependencies
bun add @policyengine/design-system recharts
bun add -D vitest
```

If using code highlighting:
```bash
bun add prism-react-renderer
```

## Step 3: Generate project files

Create the following files with the content specified below. Replace `TOOL_NAME`, `TOOL_TITLE`, `DESCRIPTION`, and `COUNTRY_ID` with actual values.

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

### app/globals.css

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

### app/page.jsx

```jsx
"use client";

import { useState } from "react";

const PE_LOGO_URL =
  "https://raw.githubusercontent.com/PolicyEngine/policyengine-app-v2/main/app/public/assets/logos/policyengine/white.png";

function getCountryFromHash() {
  if (typeof window === "undefined") return "us";
  const params = new URLSearchParams(window.location.hash.slice(1));
  return params.get("country") || "us";
}

export default function Home() {
  const [countryId] = useState(getCountryFromHash());
  const isEmbedded =
    typeof window !== "undefined" && window.self !== window.top;

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
    <div className="min-h-screen">
      <header
        style={{
          backgroundColor: "var(--pe-color-primary-700)",
          color: "white",
          padding: "var(--pe-space-lg) var(--pe-space-xl)",
        }}
      >
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={PE_LOGO_URL} alt="PolicyEngine" className="h-7" />
            <h1 className="text-xl font-semibold">TOOL_TITLE</h1>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto p-6">
        {/* Your tool UI goes here */}
      </main>
    </div>
  );
}
```

### vercel.json

```json
{
  "framework": "nextjs"
}
```

## Step 4: Data pattern boilerplate

Based on the user's choice, add the appropriate data fetching code.

**For Pattern B (PolicyEngine API):** Create `lib/api.js`:

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

And `lib/api.js`:

```js
const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://policyengine--TOOL_NAME-calculate.modal.run";

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
vercel env add NEXT_PUBLIC_API_URL production
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
bun run dev
```

## Reference

See these skills for detailed guidance:
- `policyengine-interactive-tools-skill` — Embedding, hash sync, country detection
- `policyengine-design-skill` — Token reference
- `policyengine-vercel-deployment-skill` — Deployment patterns
