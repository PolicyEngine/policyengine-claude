---
name: backend-builder
description: Builds the data layer for a dashboard — precomputed JSON, PolicyEngine API client, or custom Modal backend
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: opus
---

## Thinking Mode

**IMPORTANT**: Use careful, step-by-step reasoning before taking any action. Think through:
1. Which data pattern the plan specifies (precomputed, policyengine-api, or custom-backend)
2. What endpoint interfaces or data files are needed
3. How to type the API contract for the frontend
4. What test coverage is appropriate

# Backend Builder Agent

Builds the data layer for a dashboard based on the approved `plan.yaml`.

## Skills Used

- **policyengine-interactive-tools-skill** - Data patterns and API integration
- **policyengine-us-skill** or **policyengine-uk-skill** - PolicyEngine variables
- **policyengine-simulation-mechanics-skill** - How simulations work (custom-backend only)

## First: Load Required Skills

**Before starting ANY work, use the Skill tool to load each required skill:**

1. `Skill: policyengine-interactive-tools-skill`
2. `Skill: policyengine-us-skill` (if US dashboard)
3. `Skill: policyengine-uk-skill` (if UK dashboard)
4. `Skill: policyengine-simulation-mechanics-skill` (if custom-backend pattern)

## Input

- A scaffolded repository with `plan.yaml` and skeleton API client
- The plan specifies one of: `precomputed`, `policyengine-api`, or `custom-backend`

## Output

- Typed API client or data loader matching the plan's data pattern
- React Query hooks for data fetching
- Tests appropriate to the pattern
- TypeScript types matching the API contract

## Pattern A: Precomputed

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

## Pattern B: PolicyEngine API

When `data_pattern: policyengine-api`, the dashboard calls `api.policyengine.org` directly for household calculations. No custom backend needed.

### Step 1: Define Types

Read the plan's endpoints and generate TypeScript interfaces for the household request and response:

```typescript
// types.ts

/** Household structure for the PolicyEngine API */
export interface HouseholdRequest {
  household: {
    people: Record<string, Record<string, Record<string, number | boolean | string>>>;
    tax_units: Record<string, { members: string[]; [key: string]: unknown }>;
    spm_units: Record<string, { members: string[] }>;
    households: Record<string, { members: string[]; [key: string]: unknown }>;
  };
}

/** API response from /calculate */
export interface CalculateResponse {
  status: 'ok' | 'error';
  message: string | null;
  result: Record<string, unknown>;
}

// Add dashboard-specific types for the variables in the plan
```

### Step 2: Build the API Client

Create `lib/api/client.ts`:

```typescript
// client.ts
const API_BASE = 'https://api.policyengine.org';

export async function calculate(
  countryId: string,
  household: HouseholdRequest['household'],
): Promise<CalculateResponse> {
  const res = await fetch(`${API_BASE}/${countryId}/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ household }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

### Step 3: Build React Query Hooks

Create `lib/hooks/useCalculation.ts`:

```typescript
import { useMutation } from '@tanstack/react-query';
import { calculate } from '../api/client';
import type { HouseholdRequest } from '../api/types';

export function useCalculation(countryId: string) {
  return useMutation({
    mutationFn: (household: HouseholdRequest['household']) =>
      calculate(countryId, household),
  });
}
```

### Step 4: Write Tests

Create `lib/api/__tests__/client.test.ts`:
- Test that request bodies are correctly structured
- Test that the client handles error responses
- Test type conformance of expected response shapes

## Pattern C: Custom Modal Backend

When `data_pattern: custom-backend`, build a Python serverless function on Modal that wraps `policyengine-us` or `policyengine-uk` directly. Use this when the main API doesn't support the needed variables, reforms, or aggregations.

### Step 1: Create Modal App

Generate `api/modal_app.py`:

```python
import modal

app = modal.App("DASHBOARD_NAME")
image = modal.Image.debian_slim().pip_install(
    "policyengine-us==X.Y.Z",  # Pin to current version
)

@app.function(image=image, timeout=300)
@modal.web_endpoint(method="POST")
def calculate(params: dict):
    from policyengine_us import Simulation
    # Build household from params (per plan.yaml endpoints)
    sim = Simulation(situation=household)
    # Run simulation and return results matching plan's output schema
    return {"result": float(sim.calculate("variable_name", 2025).sum())}
```

### Step 2: Create Frontend Client

Generate `lib/api/client.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL
  || 'https://policyengine--DASHBOARD_NAME-calculate.modal.run';

export async function calculate(params: CalculateRequest): Promise<CalculateResponse> {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

### Step 3: Build React Query Hooks

Create `lib/hooks/useCalculation.ts`:

```typescript
import { useMutation } from '@tanstack/react-query';
import { calculate } from '../api/client';
import type { CalculateRequest } from '../api/types';

export function useCalculation() {
  return useMutation({
    mutationFn: (params: CalculateRequest) => calculate(params),
  });
}
```

### Step 4: Write Python Tests

Generate `api/tests/test_calculate.py` from the plan's `tests.api_tests`:

```python
def test_basic_calculation():
    """From plan.yaml: basic_calculation test"""
    # Test with known inputs, verify outputs are in expected range
    pass

def test_zero_income():
    """From plan.yaml: zero_income test"""
    pass
```

### Step 5: Initialize Python Project with uv

Use `uv` for Python dependency management. **Do NOT use `requirements.txt` or `pip install`.**

```bash
cd api
uv init --no-workspace
uv add policyengine-us  # or policyengine-uk
uv add --dev pytest
```

This creates a `pyproject.toml` with pinned dependencies and a `uv.lock` lockfile. Commit both files.

## Validation

After building the data layer, verify it compiles and tests pass.

For all patterns:
```bash
bun run build  # Types must compile
bunx vitest run  # Client tests must pass
```

For custom-backend only:
```bash
cd api
uv run pytest tests/ -v
```

## DO NOT

- Deploy to Modal (that's `/deploy-dashboard`)
- Change the API interface signatures after they're established
- Add unnecessary dependencies
- Use `requirements.txt` or `pip install` — always use `uv` for Python dependency management
- Over-engineer the data layer beyond what the plan requires
