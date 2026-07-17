---
name: policyengine-api
description: |
  Load when consuming or developing the PolicyEngine REST APIs — the v1 Flask API at
  api.policyengine.org (production today) or the v2 alpha microservices in policyengine-api-v2.
  Covers the v1 endpoint surface (household calc, economy-over-baseline polling), the v2
  architecture (three services, uv/Docker/Cloud Run, OpenAPI client-gen), and when to use REST
  vs the Python package.
  Triggers: PolicyEngine API, api.policyengine.org, REST endpoint, household calculate, economy
  over baseline, v2 API, api-full, api-simulation, api-tagger, OpenAPI client, v2.api.policyengine.org.
  NOT for: Python analysis (use the policyengine skill) or calling the API from the app
  frontend (policyengine-app).
metadata:
  category: apps
---

# PolicyEngine APIs

Two APIs coexist: **v1** (`PolicyEngine/policyengine-api`, Flask) is production **today**, and
**v2** (`PolicyEngine/policyengine-api-v2`, FastAPI microservices) is in **alpha**.

**Pick the right client first.** If you are computing policy impacts **from Python**, use the
`policyengine` package (`pe.us.calculate_household`, `Simulation`, `economic_impact_analysis`)
— see the **policyengine** skill. It pins a certified model + data bundle and is reproducible.
Reach for REST only for **apps and external integrations** (JS frontends, third parties) that
need HTTP.

## v1 API — production (`https://api.policyengine.org`)

Flask (`policyengine_api`, Python 3.10/3.11). Country id (`us`, `uk`, `ca`, …) is the first
path segment. Verified route surface (`policyengine_api/routes/`, `api.py`):

| Route | Method | Purpose |
|---|---|---|
| `/{country}/metadata` | GET | variables, parameters, entities |
| `/{country}/calculate` | POST | stateless household calc (household JSON in, values out) |
| `/{country}/calculate-full` | POST | stateless full household calc |
| `/{country}/household` | POST | create a stored household |
| `/{country}/household/{id}` | GET/PUT | fetch/update a stored household |
| `/{country}/household/{id}/policy/{policyId}` | GET | household calc under a stored policy |
| `/{country}/policy` · `/{country}/policy/{id}` | POST · GET | store / fetch a reform policy |
| `/{country}/economy/{policyId}/over/{baselinePolicyId}` | GET | society-wide reform impact |
| `/{country}/simulation`, `/{country}/report` | POST/GET/PATCH | stored simulations / report output |
| `/specification` | GET | OpenAPI spec (also `/liveness-check`, `/readiness-check`) |

**The economy endpoint is asynchronous — poll it.** The same GET is re-issued until the job
finishes; the response is a status envelope, not the result on the first call:

```json
{ "status": "computing" | "ok" | "error",
  "queue_position": 3, "average_time": 42.0,
  "result": { /* deciles, poverty, budget… once status == "ok" */ },
  "policyengine_bundle": { "model_version": "…", "data_version": "…" } }
```

Query params on the economy call: `region` (`us`, or a two-letter state code; `uk`, etc.),
`time_period` (four-digit year), optional `dataset`. The household `POST /{country}/calculate`
body nests values by year (`{"people": {"you": {"age": {"2026": 40}}}, "households": {...}}`);
read `/{country}/metadata` for the exact variable and entity names rather than guessing.

## v2 API — alpha (`PolicyEngine/policyengine-api-v2`)

A monorepo of FastAPI microservices, **not yet the production default**. Prerequisites:
Docker + Compose, Python 3.13+, **uv**, gcloud, Terraform. `make up` runs all services on
ports 8081–8083; `make test-complete` runs unit + integration; `make deploy` builds images and
applies Terraform.

Three services:

| Service | Port | Role |
|---|---|---|
| `api-full` | 8081 | main API — household calculations, policies |
| `api-simulation` | 8082 | economic (society-wide) simulation engine |
| `api-tagger` | 8083 | Cloud Run revision / release management |

Stack (verified from `libs/policyengine-fastapi/pyproject.toml`): **FastAPI**
(`fastapi[standard]`) + **uvicorn**, **SQLModel / SQLAlchemy** for the datastore (sqlite for
desktop/testing via the shared `policyengine-fastapi` lib), OpenTelemetry instrumentation. It
is deployed to **Cloud Run** via Terraform. Each service generates an **OpenAPI spec and a
Python client library**; merges to main publish the client packages to **PyPI**. Structure:
`projects/` (the services + `policyengine-apis-integ` integration tests), `libs/` (shared
`policyengine-fastapi`), `deployment/` (docker-compose + terraform).

Note: this repo uses SQLModel/SQLAlchemy, **not Supabase** — an older skill claimed Supabase,
but there is no Supabase reference anywhere in the repo.

## Integration status

app-v2 already carries a **v2 alpha adapter** in `app/src/api/v2/`
(`API_V2_BASE_URL = process.env.NEXT_PUBLIC_API_V2_URL || 'https://v2.api.policyengine.org'`),
with endpoints per **policyengine-api-v2-alpha PR #77**. v2 calculations are **async job +
poll**, and it adds CRUD for households/policies/simulations. **Variation/axes household
calculations are not in v2** and remain on v1. Until v2 is promoted, keep new REST consumers on
v1 unless you specifically need a v2 capability.

## Related skills

- policyengine — Python analysis (the preferred path for computing impacts from Python)
- policyengine-app — how the app-v2 frontend calls v1 and the v2 adapter
- policyengine-tools — Modal backends for computations the API doesn't expose
