---
name: policyengine-api
description: |
  Load when developing the PolicyEngine REST APIs or writing server code against them — the v1
  Flask API at api.policyengine.org (the Public API, production today, callable only with a
  server credential) or the v2 alpha microservices in policyengine-api-v2. Covers the v1
  endpoint surface (household calc, economy-over-baseline polling), the v2 architecture (three
  services, uv/Docker/Cloud Run, OpenAPI client-gen), and when to use REST vs the Python package.
  Triggers: PolicyEngine API, api.policyengine.org, REST endpoint, household calculate, economy
  over baseline, v2 API, api-full, api-simulation, api-tagger, OpenAPI client, v2.api.policyengine.org.
  NOT for: Python analysis (use the policyengine skill), or reaching the API from a dashboard
  page or your own server (policyengine-api-access).
metadata:
  category: apps
---

# PolicyEngine APIs

Two APIs coexist: **v1** (`PolicyEngine/policyengine-api`, Flask) is production **today**, and
**v2** (`PolicyEngine/policyengine-api-v2`, FastAPI microservices) is in **alpha**.

**Pick the right client first.** If you are computing policy impacts **from Python**, use the
`policyengine` package (`pe.us.calculate_household`, `Simulation`, `economic_impact_analysis`)
— see the **policyengine** skill. It pins a certified model + data bundle and is reproducible.

**Who may call v1.** The Public API is becoming callable only by PolicyEngine's own servers,
each with its own Auth0 client-credentials token (a server credential) in
`Authorization: Bearer`. Once that requirement is on, every other request gets 401. Browser
code never calls it: dashboard pages use www.policyengine.org's dashboard API through
`@policyengine/api-client`. The **policyengine-api-access** skill covers both routes, getting a
client, and the errors.

## v1 API — production (`https://api.policyengine.org`)

Flask (`policyengine_api`, Python 3.10/3.11). Country id (`us`, `uk`, `ca`, …) is the first
path segment. Every route except the public ones below needs a server credential once the
requirement is on. Verified route surface (`policyengine_api/routes/` and `api.py`; the public
`/health` and `/v2/openapi.json` are in `policyengine_api/fastapi_routes/`):

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
| `/{country}/economy/{policyId}/over/{baselinePolicyId}/budget-window` | GET | budget impact for each year of a window |
| `/{country}/simulation`, `/{country}/report` | POST/GET/PATCH | stored simulations / report output |
| `/health` | GET, HEAD | health check; public |
| `/v2/openapi.json` | GET | OpenAPI schema; public |

**The economy endpoint is asynchronous — poll it.** The same GET is re-issued until the job
finishes; the response is a status envelope, not the result on the first call:

```json
{ "status": "computing" | "ok" | "error",
  "message": null,
  "result": { /* budget, poverty, deciles…, plus model_version, data_version and
                 policyengine_bundle, once status == "ok" */ } }
```

While the job runs, the envelope can also carry stage fields, such as `stage`, `progress`,
`progress_max` and `segments`, and a failed run answers HTTP 502 with `status: "error"`.
The budget-window route adds `progress`, the `completed_years`, `computing_years` and
`queued_years` lists, and `error` to the same three keys. It reports a failed batch with HTTP 200,
`status: "error"` and the reason in `error`, and answers HTTP 502 only when it can't reach
the simulation service.

Query params on the annual economy call: `region` (`us`, `state/ca` or a bare `ca`,
`congressional_district/CA-01`, `uk`, etc.), `time_period` (a four-digit year that
`/{country}/metadata` lists under `economy_options.time_period`), and optional `version`,
`target` and `spm`; UK runs also take `breakdown`. The budget-window route takes `region`,
`start_year`, `window_size`, `version`, `spm` and `target` (`general` only). The API answers
HTTP 400 to any other parameter, such as `dataset`, or `breakdown` on the budget-window route.
The executor selects data by region: national runs use the default that
`/{country}/metadata` lists under `economy_options.datasets`, and US state and district
runs use ACS-local data. The gateway's `policyengine_bundle` describes the app default,
so it cannot identify a regional run's file. Preserve the worker's top-level `dataset`
when supplied (UK local-area breakdowns include it), and its `data_version`; leave an
unverified dataset name null. The budget-window result reports
no dataset or model versions, so do not fill those from current metadata.
The household `POST /{country}/calculate`
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
calculations are not in v2** and remain on v1. Until v2 is promoted, keep new server-side REST
consumers on v1 unless you specifically need a v2 capability.

## Related skills

- policyengine — Python analysis (the preferred path for computing impacts from Python)
- policyengine-api-access — reaching v1 from dashboard pages (the dashboard API) and from servers (a server credential)
- policyengine-app — how the app-v2 frontend calls v1 and the v2 adapter
- policyengine-tools — Modal backends for computations the API doesn't expose
