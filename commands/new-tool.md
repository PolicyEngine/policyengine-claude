---
description: Scaffold a new PolicyEngine interactive tool (Next.js 14 + Tailwind 4 + ui-kit theme + embedding boilerplate)
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
bun add @policyengine/ui-kit recharts
bun add -D vitest
```

Copy the favicon:
```bash
mkdir -p public
cp node_modules/@policyengine/ui-kit/src/assets/logos/policyengine/teal-square.svg public/favicon.svg
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
  icons: { icon: "/favicon.svg" },
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

### app/globals.css

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

The single `@import "@policyengine/ui-kit/theme.css"` provides all design tokens (colors, spacing, typography, chart colors) as CSS variables that Tailwind 4 picks up automatically. No manual `@theme` block needed.

### app/page.jsx

```jsx
"use client";

import { useState } from "react";
import { DashboardShell, Header, logos } from "@policyengine/ui-kit";

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
    <DashboardShell>
      <Header
        variant="dark"
        logo={<img src={logos.whiteWordmark} alt="PolicyEngine" className="h-5" />}
      >
        <span className="ml-2 font-bold text-white">TOOL_TITLE</span>
      </Header>
      <main className="max-w-6xl mx-auto p-6">
        {/* Your tool UI goes here */}
      </main>
    </DashboardShell>
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

> **Prefer Pattern B** (PolicyEngine API) unless the tool needs microsimulation,
> custom reforms, or variables not in the API. Pattern C is significantly more complex
> and should be the last resort.

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

**For Pattern C (Custom Modal API — gateway + polling):**

Pattern C uses a **three-file backend structure** mirroring policyengine-api-v2's simulation service: a standalone image setup, a worker app, and pure simulation logic. A lightweight gateway manages job submission/polling. This avoids Modal's ~150s gateway timeout and a common crash-loop where module-level imports fail.

First, look up the latest package version from PyPI. Do NOT guess or use a version from memory:

```bash
pip index versions policyengine-us 2>/dev/null | head -1
# or for UK: pip index versions policyengine-uk 2>/dev/null | head -1
```

Create `backend/_image_setup.py` (standalone snapshot function, no package imports at module level):

```python
def snapshot_models():
    """Pre-load models at image build time for fast cold starts."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Pre-loading tax-benefit system...")
    from policyengine_us import CountryTaxBenefitSystem  # or policyengine_uk
    CountryTaxBenefitSystem()
    logger.info("Models pre-loaded into image snapshot")
```

Create `backend/simulation.py` (pure logic, policyengine at module level — captured in snapshot):

```python
from policyengine_us import Simulation  # Snapshotted at build time

def run_compute(params: dict) -> dict:
    sim = Simulation(situation=params["household"])
    return {"result": float(sim.calculate("variable_name", 2025).sum())}
```

Create `backend/app.py` (worker app, only `modal` at module level):

```python
import modal
from pathlib import Path
from _image_setup import snapshot_models

_BACKEND_DIR = Path(__file__).parent
app = modal.App("TOOL_NAME-workers")
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("policyengine-us==LATEST_VERSION", "pydantic")
    .run_function(snapshot_models)
    .add_local_file(str(_BACKEND_DIR / "simulation.py"), remote_path="/root/simulation.py")
)

@app.function(image=image, cpu=8.0, memory=32768, timeout=3600)
def compute(params: dict) -> dict:
    from simulation import run_compute
    return run_compute(params)
```

Create `backend/modal_app.py` (lightweight gateway, no policyengine):

```python
import modal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = modal.App("TOOL_NAME")
gateway_image = modal.Image.debian_slim(python_version="3.11").pip_install("fastapi", "pydantic")
WORKER_APP = "TOOL_NAME-workers"
FUNCTION_MAP = {"calculate": "compute"}

web_app = FastAPI()
web_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@web_app.post("/submit/{endpoint}")
def submit(endpoint: str, params: dict):
    if endpoint not in FUNCTION_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown endpoint: {endpoint}")
    fn = modal.Function.from_name(WORKER_APP, FUNCTION_MAP[endpoint])
    call = fn.spawn(params)
    return {"job_id": call.object_id}

@web_app.get("/status/{job_id}")
def status(job_id: str):
    from modal.functions import FunctionCall
    call = FunctionCall.from_id(job_id)
    try:
        result = call.get(timeout=0)
        return {"status": "ok", "result": result}
    except TimeoutError:
        return {"status": "computing"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.function(image=gateway_image)
@modal.asgi_app()
def fastapi_app():
    return web_app
```

And `lib/api.js` (polling client):

```js
const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://policyengine--TOOL_NAME-fastapi-app.modal.run";

export async function submitJob(endpoint, params) {
  const res = await fetch(`${API_URL}/submit/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Submit failed: ${res.status}`);
  const data = await res.json();
  return data.job_id;
}

export async function pollStatus(jobId) {
  const res = await fetch(`${API_URL}/status/${jobId}`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json(); // { status: "computing" | "ok" | "error", result?, message? }
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

If using Pattern C (Modal gateway + worker):
```bash
unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET
# Deploy worker first (includes image snapshot — first build takes ~5 min)
modal deploy backend/app.py
# Deploy gateway (lightweight job submission/polling)
modal deploy backend/modal_app.py
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://policyengine--TOOL_NAME-fastapi-app.modal.run
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
