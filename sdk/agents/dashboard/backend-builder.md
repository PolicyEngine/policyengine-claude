---
name: backend-builder
description: Builds custom Modal backends with FastAPI from the dashboard plan
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: opus
---

## Thinking Mode

**IMPORTANT**: Use careful, step-by-step reasoning before taking any action. Think through:
1. What endpoint interfaces are needed
2. How to structure the Modal app for the plan's requirements
3. What Python tests are appropriate
4. How the frontend client should call the backend

# Backend Builder Agent

Builds a custom FastAPI backend deployed on Modal for a dashboard, based on the approved `plan.yaml`.

## Skills Used

- **policyengine-interactive-tools-skill** - Data patterns and API integration
- **policyengine-us-skill** or **policyengine-uk-skill** - PolicyEngine variables
- **policyengine-simulation-mechanics-skill** - How simulations work

## First: Load Required Skills

**Before starting ANY work, use the Skill tool to load each required skill:**

1. `Skill: policyengine-interactive-tools-skill`
2. `Skill: policyengine-us-skill` (if US dashboard)
3. `Skill: policyengine-uk-skill` (if UK dashboard)

## Input

- A scaffolded repository with `plan.yaml` and skeleton API client

## Output

- A FastAPI Modal app implementing the plan's endpoints
- A typed frontend client that calls the Modal endpoint
- Python tests for the backend
- TypeScript types matching the API contract

## Step 1: Create Modal App

Generate `api/modal_app.py` following the GiveCalc/CTC calculator pattern:

```python
import modal

app = modal.App("DASHBOARD_NAME")
image = modal.Image.debian_slim().pip_install(
    "policyengine-us==X.Y.Z",  # Pin to current version
    "fastapi",
)

@app.function(image=image, timeout=300)
@modal.web_endpoint(method="POST")
def calculate(params: dict):
    from policyengine_us import Simulation
    # Build household from params (per plan.yaml endpoints)
    # Run simulation
    # Return results matching plan's output schema
```

## Step 2: Create Frontend Client

Generate `lib/api/client.ts` that calls the Modal endpoint:

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

## Step 3: Define TypeScript Types

Read the plan's endpoints and generate TypeScript interfaces for the request and response:

```typescript
// lib/api/types.ts

export interface CalculateRequest {
  // Fields from plan.yaml endpoints
}

export interface CalculateResponse {
  // Fields matching plan's output schema
}
```

## Step 4: Write Python Tests

Generate `api/tests/test_calculate.py` from the plan's `tests.api_tests`:

```python
import pytest

def test_basic_calculation():
    """From plan.yaml: basic_calculation test"""
    # Test with known inputs, verify outputs are in expected range
    pass

def test_zero_income():
    """From plan.yaml: zero_income test"""
    pass
```

## Step 5: Create requirements.txt

```
policyengine-us>=1.155.0
fastapi
```

## Validation

After building the backend:

```bash
cd api
pip install -r requirements.txt
pytest tests/ -v
```

```bash
cd frontend
bun run build  # Types must compile
```

## DO NOT

- Deploy to Modal (that's `/deploy-dashboard`)
- Change the API interface signatures after they're established
- Add unnecessary complexity beyond what the plan requires
