---
name: backend-builder
description: Builds the data layer for a dashboard — precomputed JSON, PolicyEngine API client, or custom Modal backend
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: opus
---

## Thinking Mode

**IMPORTANT**: Use careful, step-by-step reasoning before taking any action. Think through:
1. Which data pattern the plan specifies (precomputed, policyengine-api, or custom-modal)
2. What endpoint interfaces or data files are needed
3. How to type the API contract for the frontend
4. What test coverage is appropriate

# Backend Builder Agent

Builds the data layer for a dashboard based on the approved `plan.yaml`.

## Skills Used

- **policyengine-tools** - Data patterns, API integration, and Modal backend architecture
- **policyengine-api-access** - The dashboard API for pages, and server credentials for a backend that calls the Public API (policyengine-api and custom-modal)
- **policyengine-us** or **policyengine-uk** - PolicyEngine variables
- **policyengine** - Python simulation mechanics, reform dictionaries, and parameter path syntax (custom-modal only)
- **policyengine-cloud-costs** - Modal defaults (scale to zero, `max_containers`, measured sizes) and how to declare an exception (custom-modal only)

## Backend Selection Priority

**Always prefer simpler patterns.** The plan's `data_pattern` comes from the four options in the `policyengine-tools` skill's "Data and backend patterns", checked in this order. Check it against them before building a custom backend:

1. **Are the inputs a small, fixed set known before deploying?** → Use Pattern A/D (`precomputed` / `precomputed-csv`)
2. **Can the dashboard API give each result as it is?** It calculates households (every charted input in `axes` in the same call), stores a parameter reform and compares it with current law across the economy, and reads country metadata. → Use Pattern B (`policyengine-api`)
3. **Does it need a Public API route outside those four, used unchanged?** → Ask for a new dashboard operation (policyengine-api-access), and precompute until it ships
4. **Otherwise: outputs specific to this dashboard that the Public API's economy result doesn't include and precomputing can't cover, or a dataset the Public API doesn't serve.** → Use Pattern C (`custom-modal`) with gateway + polling

A structural reform goes into the country package as a contributed reform switched on by a `gov.contrib.…` parameter, and then uses Pattern B; it is not a reason for Pattern C.

**The Public API's model version** is a reason for `custom-modal` only while the `policyengine` package's model bundle isn't updated weekly; the plan says what the check in "Data and backend patterns" found and which release the dashboard needs. A `custom-modal` dashboard's presets come from its backend's pinned release, not the dashboard API, so the page shows one model release.

**Not a reason for `custom-modal`:** a feature coming close to a rate limit; keep the page within the budget in policyengine-api-access, and precompute what can't fit.

Pattern C is the most complex and should be the last resort. If the plan specifies `custom-modal`, the plan MUST include a `reason` explaining why Pattern B is insufficient.

## First: Load Required Skills

**Before starting ANY work, use the Skill tool to load each required skill:**

1. `Skill: policyengine-tools`
2. `Skill: policyengine-api-access` (if policyengine-api pattern, or a custom-modal backend that calls the Public API)
3. `Skill: policyengine-us` (if US dashboard)
4. `Skill: policyengine-uk` (if UK dashboard)
5. `Skill: policyengine` (if custom-modal pattern — **required** for simulation mechanics and correct reform parameter paths)
6. `Skill: policyengine-cloud-costs` (if custom-modal pattern)

## Input

- A scaffolded repository with `plan.yaml` and skeleton API client
- The plan specifies a `data_pattern` chosen from the patterns defined in the `policyengine-tools` skill (loaded in the First step)

## Output

- Typed API client or data loader matching the plan's data pattern
- React Query hooks for data fetching
- Tests appropriate to the pattern
- TypeScript types matching the API contract

## Pattern A: Precomputed JSON (`precomputed`)

When `data_pattern: precomputed`, the dashboard ships static JSON files with pre-run results. No backend, no API calls at runtime.

### Step 1: Create Data Files

Generate JSON files in `public/data/` based on the plan's data requirements:

```
public/data/
  results.json        # or split by dimension:
  results_by_state.json
  results_by_year.json
```

Data should be structured for direct consumption by the frontend — no post-processing needed.

### Step 2: Build the Data Loader

Create `lib/api/client.ts`:

```typescript
// client.ts

export interface DashboardData {
  // Types matching the JSON structure from plan.yaml
}

export async function loadData(): Promise<DashboardData> {
  const res = await fetch('/data/results.json');
  if (!res.ok) throw new Error(`Failed to load data: ${res.status}`);
  return res.json();
}
```

### Step 3: Build React Query Hooks

Create `lib/hooks/useData.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { loadData } from '../api/client';

export function useDashboardData() {
  return useQuery({
    queryKey: ['dashboard-data'],
    queryFn: loadData,
    staleTime: Infinity,  // Static data never goes stale
  });
}
```

### Step 4: Write Tests

Create `lib/api/__tests__/client.test.ts`:
- Test that JSON files parse correctly
- Test that data matches expected TypeScript types
- Test that all expected keys/dimensions are present

## Pattern B: the dashboard API (`policyengine-api`)

When `data_pattern: policyengine-api`, the page calls www.policyengine.org's dashboard API through `@policyengine/api-client`. The website's server adds PolicyEngine's credential and forwards each operation to the Public API, so no custom backend is needed. **The page never calls `api.policyengine.org`**: the Public API is becoming callable only by PolicyEngine's servers. The `policyengine-api-access` skill has the four operations, polling, the origins the dashboard API accepts, and its errors.

### Step 1: Install the client and define types

```bash
bun add @policyengine/api-client
```

Read the plan's endpoints and write the household and result types. Use `type` aliases: the client takes `Record<string, unknown>`, which an `interface` is not assignable to.

```typescript
// types.ts

/**
 * A household in PolicyEngine's situation format: values keyed by year, and null for
 * each output to calculate. The group entities differ by country (US: tax_units,
 * spm_units, families, marital_units, households; UK: benunits, households); read them
 * from the country's metadata. `axes` varies one input over a range (integrator Step 6).
 */
export type Household = {
  people: Record<string, Record<string, Record<string, number | boolean | string | null>>>;
  axes?: Array<Array<{ name: string; period: string; min: number; max: number; count: number }>>;
  [groupEntities: string]: unknown;
};

/** A calculated value: one value, or a list over the points when the household has axes */
export type CalculatedValue = number | boolean | string | null | Array<number | boolean | string | null>;

/** The calculated household: the request's shape, with the requested variables filled in */
export type CalculatedHousehold = Record<string, unknown>;

/**
 * One variable from a calculated household, for example
 * readVariable(result, 'households', 'household', 'household_net_income', '2026').
 * Null when the household did not ask for it.
 */
export function readVariable(
  result: CalculatedHousehold,
  entityGroup: string,
  entity: string,
  variable: string,
  year: string,
): CalculatedValue {
  const entities = result[entityGroup] as Record<string, Record<string, unknown>> | undefined;
  const values = entities?.[entity]?.[variable] as Record<string, CalculatedValue> | undefined;
  return values?.[year] ?? null;
}

// Add dashboard-specific types for the variables in the plan
```

### Step 2: Build the API client

Create `lib/api/client.ts`:

```typescript
// client.ts
import { createPolicyEngineApiClient } from '@policyengine/api-client';
import type { CalculatedHousehold, Household } from './types';

// The default base URL, https://www.policyengine.org, works from the dashboard's
// www.policyengine.org path, its team previews (*-policy-engine.vercel.app), localhost, and
// its own *.vercel.app host once website/src/data/appZoneRoutes.ts names it.
const policyengine = createPolicyEngineApiClient();

export function calculate(
  countryId: 'us' | 'uk',
  household: Household,
  signal?: AbortSignal,
): Promise<CalculatedHousehold> {
  return policyengine.calculateHousehold<CalculatedHousehold>(
    { country: countryId, household },
    { signal },
  );
}
```

For a reform, pass its parameter changes as `policy` to `calculateHousehold`. For an economy-wide comparison, store the reform with `createPolicy` and poll with `compareEconomy` (current law's policy ID is 2 for `us`, 1 for `uk`).

### Step 3: Build React Query Hooks

Create `lib/hooks/useCalculation.ts`:

```typescript
import { useMutation } from '@tanstack/react-query';
import { calculate } from '../api/client';
import type { Household } from '../api/types';

export function useCalculation(countryId: 'us' | 'uk') {
  return useMutation({
    mutationFn: (household: Household) => calculate(countryId, household),
  });
}
```

### Step 4: Write Tests

Create `lib/api/__tests__/client.test.ts`. `client.ts` builds its client when it loads, so mock the package (`vi.mock('@policyengine/api-client', …)`) before importing it; no test calls the network:
- Test that request bodies are correctly structured
- Test that `PolicyEngineApiError` from a refused request reaches the UI's error state
- Test type conformance of expected response shapes

## Pattern C: Custom API on Modal (`custom-modal`) — Gateway + Polling

When `data_pattern: custom-modal`, build a two-layer architecture on Modal: a lightweight **gateway** that manages job submission/polling, and **worker** functions that run the heavy policyengine computations. This mirrors the pattern used by PolicyEngine API v2's simulation service.

**Why not synchronous HTTP?** Modal's dev gateway (`modal serve`) and production gateway have a ~150s timeout. US statewide microsimulations take 2-5+ minutes, causing HTTP 303 redirects that browser `fetch()` cannot follow for POST requests. The gateway + polling architecture avoids this entirely.

**Backend structure:** The backend uses a **three-file structure** to avoid a common crash-loop where module-level imports of pydantic or policyengine fail because those packages are only available inside the Modal function's image, not at module import time.

| File | Purpose | Module-level imports |
|------|---------|---------------------|
| `backend/_image_setup.py` | Standalone snapshot function — runs during image build | None (all inside function body) |
| `backend/app.py` | Modal app + function decorators | Only `modal` |
| `backend/simulation.py` | Pure business logic | top-level `policyengine` (population — managed path) + `policyengine_us`/`_uk` `Simulation` (household); captured in image snapshot |
| `backend/modal_app.py` | Lightweight gateway (FastAPI) | `modal`, `fastapi`, `pydantic` |

### Step 1: Look Up the Latest policyengine Version

**Before writing any code**, look up the latest version of the top-level `policyengine` package from PyPI. Do NOT guess or use a version from memory — it releases frequently and stale versions will have bugs.

```bash
pip index versions policyengine 2>/dev/null | head -1
```

Use the version number returned (must be `>=5.0.1`) in the `pip_install()` call below. Install `policyengine[us]` (or `policyengine[uk]`) rather than a bare country package: the extra pins an exactly-matched `policyengine-us`/`policyengine-uk` + `policyengine-core` and carries the certified data-bundle manifest, so population results are reproducible and their provenance is known.

### Step 2: Create Image Setup

Generate `backend/_image_setup.py`. This is a **standalone function with no package imports at module level** — it runs during image build via `.run_function()`:

```python
def snapshot_models():
    """Pre-load models (and certified data) at image build time for fast cold starts."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Pre-loading tax-benefit system...")
    from policyengine_us import CountryTaxBenefitSystem  # or policyengine_uk
    CountryTaxBenefitSystem()
    # Microsimulation endpoints only: also construct the managed microsim once so the
    # certified dataset lands in the image's Hugging Face cache — cold starts then skip
    # the download. Omit for household-only dashboards (it adds GBs to the image).
    import policyengine as pe
    pe.us.managed_microsimulation()
    logger.info("Models pre-loaded into image snapshot")
```

UK microsimulation dashboards: the certified UK dataset lives in a **private** Hugging Face
repo, so `pe.uk.managed_microsimulation()` needs `HUGGING_FACE_TOKEN` available during the
image build (attach it as a Modal secret to the snapshot function and the worker functions).

### Step 3: Create Simulation Logic

Generate `backend/simulation.py`. This is **pure business logic** — no Modal imports. policyengine imports are at module level because they are captured in the image snapshot.

**Population/statewide endpoints go through policyengine.py's managed path** — `pe.us.managed_microsimulation()` (policyengine>=5.0.1), which returns a country-package `Microsimulation` pinned to the certified data bundle, with the same weighted MicroSeries interface (`.calc()` US / `.calculate()` UK) and provenance stamped on `sim.policyengine_bundle`. A directly-imported country-package `Microsimulation` is deprecated for analysis: its default dataset can lag the certified bundle, so results are not provenance-known.

```python
import policyengine as pe                # managed analysis surface — snapshotted at build time
from policyengine_us import Simulation   # household-level calculations only
from pydantic import BaseModel           # Available in image

# Pydantic models, constants, and helper functions live here.
# Each endpoint in plan.yaml gets a run_*() function.

def run_household(params: dict) -> dict:
    # Build household from params (per plan.yaml endpoints)
    sim = Simulation(situation=params["household"])
    return {"net_income": float(sim.calculate("household_net_income", 2025).sum())}

def run_statewide(params: dict) -> dict:
    baseline = pe.us.managed_microsimulation()
    reform_sim = pe.us.managed_microsimulation(reform=params["reform"])
    # ... compute and return impacts via weighted MicroSeries (.calc(...))
    return {
        "revenue_change": ..., "winners": ..., "losers": ...,
        "provenance": baseline.policyengine_bundle,  # model + data release pins
    }
```

### Step 3b: Verify All Parameter Paths

**CRITICAL — every parameter path used in `Reform.from_dict()` or reform dictionaries MUST be verified against the actual YAML files.** Incorrect paths cause silent failures or runtime errors like "Could not find the parameter". Consult the `policyengine` skill's "Reform dictionaries and parameter paths" section for the bracket path syntax rules.

**Common mistakes:**
- **Off-by-one indexing**: Some parameters use 1-indexed keys (e.g., `gov.irs.income.bracket.rates` has keys `1`-`7`, not `0`-`6`). Always check whether the YAML uses a list (0-indexed) or explicit integer keys (use those exact keys).
- **Missing sub-keys on bracket scales**: Bracket/scale parameters (YAML `brackets:` list) require `.amount` or `.rate` after the index. E.g., `gov.irs.credits.eitc.max[0].amount`, NOT `gov.irs.credits.eitc.max[0]`.
- **Filing-status-indexed parameters**: Some parameters have sub-keys by filing status (e.g., `gov.irs.credits.ctc.phase_out.threshold[SINGLE]`).

**Verification procedure for every parameter path:**

1. Find the YAML file in the `policyengine-us` (or `policyengine-uk`) parameters directory:
   ```bash
   # Convert dotted path to directory path and search
   find $(python3 -c "import policyengine_us; import os; print(os.path.dirname(policyengine_us.__file__))") \
     -path "*/parameters/gov/irs/income/bracket.yaml" 2>/dev/null
   ```

2. Read the YAML and check whether the parameter uses:
   - **Explicit integer keys** (e.g., `1:`, `2:`, `3:`) → use those exact indices: `path[1]`, `path[2]`
   - **A `brackets:` list** → use 0-indexed with sub-key: `path[0].amount`, `path[0].rate`
   - **Filing-status sub-keys** → append `[SINGLE]`, `[JOINT]`, etc.

3. Verify programmatically (if policyengine is installed locally):
   ```python
   from policyengine_us import CountryTaxBenefitSystem
   p = CountryTaxBenefitSystem().parameters
   # Navigate and confirm the path resolves:
   print(p.gov.irs.income.bracket.rates[1]("2026-01-01"))  # Should return 0.10
   ```

**Do NOT guess parameter paths from memory.** Always verify against the actual YAML files.

### Step 4: Create Worker App

Generate `backend/app.py`. Only `modal` at module level. Imports business logic **inside each function body**:

```python
import modal
from pathlib import Path
from _image_setup import snapshot_models

_BACKEND_DIR = Path(__file__).parent
app = modal.App("DASHBOARD_NAME-workers", tags={"project": "DASHBOARD_NAME"})  # tag every app of the tool, so its bill adds up in one query
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("policyengine[us]==LATEST_VERSION", "pydantic")  # Pinned — looked up from PyPI in Step 1; pins the country model + certified data bundle
    .run_function(snapshot_models)
    .add_local_file(str(_BACKEND_DIR / "simulation.py"), remote_path="/root/simulation.py")
)

@app.function(image=image, cpu=1.0, memory=2048, timeout=600, max_containers=10, min_containers=0)
def compute_household(params: dict) -> dict:
    from simulation import run_household
    return run_household(params)

# Population run: replace the TODO declaration with the measured peak before merging.
@app.function(
    image=image,
    cpu=2.0,  # a simulation runs on one thread; a statewide worker has run on 2 cores
    memory=32768,  # cost-ok: RS1 TODO measured peak memory plus a fifth
    timeout=3600,
    max_containers=4,
    min_containers=0,
)
def compute_statewide(params: dict) -> dict:
    from simulation import run_statewide
    return run_statewide(params)
```

Create one `@app.function` per endpoint in the plan. Set `timeout`, `cpu`, `memory` and `max_containers` from the plan's `worker_*` values, and keep `min_containers=0`. Microsimulation endpoints need at least `timeout=3600`. Any value the plan's `cost_plan.declared_exceptions` lists gets a `# cost-ok: <rule> <reason>` comment on its setting (see the policyengine-cloud-costs skill); a population worker keeps its memory `TODO` declaration until a measured run replaces it, and the cost checker warns until then.

### Step 5: Create Gateway

Generate `backend/modal_app.py`. The gateway is **lightweight** — no policyengine in its image. It spawns worker jobs and polls for results:

```python
import modal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = modal.App("DASHBOARD_NAME", tags={"project": "DASHBOARD_NAME"})

gateway_image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "fastapi", "pydantic",
)

WORKER_APP = "DASHBOARD_NAME-workers"

# Map endpoint names to worker function names
FUNCTION_MAP = {
    "household-impact": "compute_household",
    "statewide-impact": "compute_statewide",
}

web_app = FastAPI()
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SubmitResponse(BaseModel):
    job_id: str

class StatusResponse(BaseModel):
    status: str  # "computing" | "ok" | "error"
    result: dict | None = None
    message: str | None = None

@web_app.post("/submit/{endpoint}")
def submit(endpoint: str, params: dict):
    if endpoint not in FUNCTION_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown endpoint: {endpoint}")
    fn = modal.Function.from_name(WORKER_APP, FUNCTION_MAP[endpoint])
    call = fn.spawn(params)
    return SubmitResponse(job_id=call.object_id)

@web_app.get("/status/{job_id}")
def status(job_id: str):
    from modal.functions import FunctionCall
    call = FunctionCall.from_id(job_id)
    try:
        result = call.get(timeout=0)
        return StatusResponse(status="ok", result=result)
    except TimeoutError:
        return StatusResponse(status="computing")
    except Exception as e:
        return StatusResponse(status="error", message=str(e))

@app.function(image=gateway_image)
@modal.asgi_app()
def fastapi_app():
    return web_app
```

### Step 6: Create Frontend Polling Client

Generate `lib/api/client.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL
  || 'https://policyengine--DASHBOARD_NAME-fastapi-app.modal.run';

interface JobResponse { job_id: string }

export interface StatusResponse {
  status: 'computing' | 'ok' | 'error';
  result?: unknown;
  message?: string;
}

export async function submitJob(endpoint: string, params: unknown): Promise<string> {
  const res = await fetch(`${API_URL}/submit/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Submit failed: ${res.status}`);
  const data: JobResponse = await res.json();
  return data.job_id;
}

export async function pollStatus(jobId: string): Promise<StatusResponse> {
  const res = await fetch(`${API_URL}/status/${jobId}`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}
```

### Step 7: Build Polling React Query Hooks

Create `lib/hooks/useCalculation.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { submitJob, pollStatus } from '../api/client';
import type { StatusResponse } from '../api/client';

export function useAsyncCalculation<T>(
  queryKey: unknown[],
  endpoint: string,
  params: unknown,
  options?: { enabled?: boolean },
) {
  const [jobId, setJobId] = useState<string | null>(null);

  // Reset jobId when params change
  useEffect(() => { setJobId(null); }, [JSON.stringify(params)]);

  // Step 1: Submit job
  const submit = useQuery({
    queryKey: [...queryKey, 'submit'],
    queryFn: async () => {
      const id = await submitJob(endpoint, params);
      setJobId(id);
      return id;
    },
    enabled: options?.enabled ?? true,
  });

  // Step 2: Poll for results
  const poll = useQuery<StatusResponse>({
    queryKey: [...queryKey, 'poll', jobId],
    queryFn: () => pollStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) =>
      query.state.data?.status === 'computing' ? 2000 : false,
  });

  return {
    isLoading: submit.isLoading || (!!jobId && poll.isLoading),
    isComputing: poll.data?.status === 'computing',
    isError: submit.isError || poll.data?.status === 'error',
    data: poll.data?.status === 'ok' ? (poll.data.result as T) : undefined,
    error: poll.data?.message || submit.error?.message,
  };
}
```

### Step 8: Write Python Tests

Generate `backend/tests/test_simulation.py` from the plan's `tests.api_tests`:

```python
def test_basic_calculation():
    """From plan.yaml: basic_calculation test"""
    # Test with known inputs, verify outputs are in expected range
    pass

def test_zero_income():
    """From plan.yaml: zero_income test"""
    pass
```

### Step 9: Initialize Python Project with uv

<!-- stale-ok -->
Use `uv` for Python dependency management. **Do NOT use `requirements.txt` or `pip install`.**

```bash
cd backend
uv init --no-workspace
uv add "policyengine[us]"  # or "policyengine[uk]" — pins the country model + certified data bundle
uv add --dev pytest
```

This creates a `pyproject.toml` with pinned dependencies and a `uv.lock` lockfile. Commit both files.

### Modal Timeout Reference

| Context | Default timeout | Max timeout | Notes |
|---------|----------------|-------------|-------|
| `@app.function(timeout=...)` | 300s | 86,400s (24h) | Set per-function |
| `modal serve` dev gateway | ~150s | Not configurable | Returns HTTP 303 on timeout |
| `modal deploy` prod gateway | ~150s | Not configurable | Returns HTTP 303 on timeout |

**US statewide microsimulations take 2-5+ minutes.** This exceeds the gateway timeout, which is why synchronous HTTP calls fail for microsimulation endpoints. The gateway + polling architecture avoids this by using non-blocking job submission. Household-level simulations typically complete in 10-40s.

**Cold starts:** With `.run_function(snapshot_models)`, cold starts are ~2s because the tax-benefit system is pre-loaded into the image. Without the snapshot, cold starts take 3-5 minutes as policyengine must initialize from scratch.

## Pattern D: Precomputed CSV (`precomputed-csv`)

When `data_pattern: precomputed-csv`, the dashboard ships CSV files generated by a Python microsimulation pipeline. Follow Pattern A but use CSV files in `public/data/` instead of JSON, and parse them at runtime with a lightweight CSV parser.

See the `policyengine-tools` skill for the precomputed data pattern; existing examples include the `snap-bbce-repeal` and `uk-spring-statement-2026` repos.

## DO NOT

- Deploy to Modal (that's `/deploy-dashboard`)
- Change the API interface signatures after they're established
- Add unnecessary dependencies
<!-- stale-ok -->
- Use `requirements.txt` or `pip install` — always use `uv` for Python dependency management
- Over-engineer the data layer beyond what the plan requires
