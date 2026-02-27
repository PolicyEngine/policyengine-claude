---
name: policyengine-modal-deployment
description: Deploying PolicyEngine backend APIs to Modal — workspace setup, authentication, deployment commands, environments, and troubleshooting
---

# PolicyEngine Modal deployment

How to deploy PolicyEngine backend APIs (custom Modal backends for dashboards and interactive tools) to Modal under the PolicyEngine organizational workspace.

**This skill applies only when a dashboard or tool uses the `custom-backend` data pattern.** If the project uses `api-v2-alpha` (stub data or direct API calls), no Modal deployment is needed.

## Workspace

PolicyEngine uses a shared Modal workspace called `policyengine`. All backend deployments MUST target this workspace — never a personal workspace.

### Environments

The `policyengine` workspace has three environments:

| Environment | Web suffix | URL pattern | Purpose |
|-------------|-----------|-------------|---------|
| `main` | _(empty)_ | `policyengine--<app>-<func>.modal.run` | Production |
| `staging` | `staging` | `policyengine-staging--<app>-<func>.modal.run` | Pre-production testing |
| `testing` | `testing` | `policyengine-testing--<app>-<func>.modal.run` | Development/CI |

Default to `main` for production deployments.

## Authentication

### Prerequisites

1. A Modal account linked to the PolicyEngine workspace (ask a workspace owner for an invite)
2. The Modal CLI installed: `pip install modal`
3. A token for the `policyengine` workspace stored in a local profile

### Setting up authentication

```bash
# Create a token for the policyengine workspace (opens browser)
modal token new --profile policyengine

# Activate the profile
modal profile activate policyengine

# Verify — must show "Workspace: policyengine"
modal token info
```

### Verifying authentication before deploy

**HUMAN GATE:** Before any deployment, verify the active workspace:

```bash
modal token info
modal profile list
```

Expected output from `modal profile list`:
```
┏━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃   ┃ Profile      ┃ Workspace    ┃
┡━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ • │ policyengine │ policyengine │
└───┴──────────────┴──────────────┘
```

The `•` indicates the active profile. If `policyengine` is not active or not present:

> **Authentication required.** Your Modal CLI is not configured for the `policyengine` workspace.
>
> Run:
> ```bash
> modal token new --profile policyengine
> modal profile activate policyengine
> ```
>
> If you don't have access to the PolicyEngine workspace, ask a workspace owner to invite you at https://modal.com/settings/policyengine

**Do NOT proceed with deployment until `modal token info` shows `Workspace: policyengine`.**

### Critical: environment variable override

Modal CLI respects `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` environment variables, which **override** the profile. If these are set (e.g., from a CI environment), the CLI will deploy to whatever workspace those tokens belong to — potentially a personal workspace.

**Always unset before deploying:**
```bash
unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET
```

## App structure

### Naming convention

The Modal app name MUST match the dashboard/tool repo name in kebab-case:

```python
app = modal.App("my-dashboard-name")
```

This keeps the app name consistent with the GitHub repo and Vercel project.

### Image and dependencies

Build a container image with the required Python packages:

```python
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "policyengine-us>=1.155.0",  # Pin minimum version
        "fastapi[standard]",
        "numpy",
        "pandas",
    )
    .env({"NUMEXPR_MAX_THREADS": "4"})
    .add_local_dir("api", "/root/api")          # Local source code
    .add_local_file("config.yaml", "/root/config.yaml")  # Config files
)
```

**Guidelines:**
- Use `debian_slim` with Python 3.12 or 3.13
- Pin minimum versions for `policyengine-us` / `policyengine-uk`
- Use `.add_local_dir()` / `.add_local_file()` for project source code
- Use `.env()` for non-secret environment variables
- Set memory and timeout on the function, not the image

### Web endpoint patterns

#### Simple endpoint (single function)

For tools with one calculation endpoint:

```python
@app.function(image=image, timeout=300, memory=2048)
@modal.web_endpoint(method="POST")
def calculate(data: dict) -> dict:
    from policyengine_us import Simulation
    # Build simulation from data, return results
    return {"result": value}
```

URL: `https://policyengine--<app-name>-calculate.modal.run`

#### Full FastAPI app (multiple endpoints)

For dashboards with multiple API routes:

```python
@app.function(image=image, timeout=300, memory=2048)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    from api.main import app as api
    return api
```

URL: `https://policyengine--<app-name>-fastapi-app.modal.run`

#### Health check endpoint

Every Modal backend SHOULD include a health check:

```python
@app.function(image=image)
@modal.web_endpoint(method="GET")
def health():
    return {"status": "ok"}
```

### Function configuration

| Parameter | Default | Recommended for PE | Purpose |
|-----------|---------|-------------------|---------|
| `timeout` | 60s | 300 | PolicyEngine simulations can take minutes |
| `memory` | 128MB | 2048 | PE models are memory-intensive |
| `@modal.concurrent(max_inputs=N)` | 1 | 100 | Handle concurrent requests without cold starts |

### Secrets

Store sensitive values as Modal Secrets (not in code or `.env` files):

```bash
# Create a secret
modal secret create my-secret API_KEY=abc123

# List secrets
modal secret list
```

Reference in code:
```python
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("my-secret")],
)
def my_function():
    import os
    api_key = os.environ["API_KEY"]  # Injected by Modal
```

Existing secrets in the `policyengine` workspace:
- `policyengine-logfire` — logging/observability
- `gcp-credentials` — Google Cloud access
- `huggingface-token` — HuggingFace model access
- `anthropic-api-key` — Anthropic API access

## Deployment

### Deploy command

```bash
# 1. Ensure correct workspace
unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET
modal token info  # Verify "Workspace: policyengine"

# 2. Deploy to production
modal deploy modal_app.py --env main

# 3. Deploy to staging (for testing)
modal deploy modal_app.py --env staging
```

**Flags:**
- `--env main` / `--env staging` / `--env testing` — target environment
- `--name TEXT` — override the deployment name (rarely needed)
- `--tag TEXT` — tag the deployment with a version string
- `--stream-logs` — stream container logs during deployment

### Verify deployment

```bash
# List deployed apps
modal app list --env main

# Health check
curl -s -w "\n%{http_code}" https://policyengine--DASHBOARD_NAME-health.modal.run

# Test the endpoint
curl -X POST https://policyengine--DASHBOARD_NAME-calculate.modal.run \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### Connecting to Vercel frontend

After Modal deployment, set the API URL as an environment variable in the Vercel project:

```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://policyengine--DASHBOARD_NAME-calculate.modal.run
vercel --prod --force --yes --scope policy-engine
```

The `--force` flag is required to rebuild with the new environment variable.

### Redeployment

Redeploying an existing app is the same command — Modal handles zero-downtime transitions:
1. New containers build while old ones handle requests
2. New containers start accepting requests
3. Old containers finish in-flight requests then terminate

```bash
modal deploy modal_app.py --env main
```

### Stopping an app

**WARNING: This is destructive and irreversible.** A stopped app cannot be restarted; you must redeploy.

```bash
modal app stop <app-name>
```

## Monitoring

```bash
# View logs for a deployed app
modal app logs <app-name>

# List all apps and their status
modal app list --env main
```

App states:
- `deployed` — running and accepting requests
- `ephemeral` — temporary (from `modal serve`)
- `stopped` — permanently stopped

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `modal token info` shows wrong workspace | Wrong profile active | `modal profile activate policyengine` |
| Deploy goes to personal workspace | `MODAL_TOKEN_ID` env var set | `unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET` |
| 404 on endpoint URL | App stopped or never deployed | `modal deploy modal_app.py --env main` |
| Cold start latency (5-15s) | No warm containers | Add `@modal.concurrent(max_inputs=100)` |
| `MemoryError` during simulation | Container memory too low | Increase `memory=` (try 4096) |
| Timeout error | Simulation exceeds limit | Increase `timeout=` (try 600) |
| Python dependency conflict | Version mismatch | Pin exact versions in `.pip_install()` |
| Missing local files in container | Forgot `.add_local_dir()` | Add source dirs to image definition |
| Modal app silently disappeared | Unknown — can happen | `curl` the URL; if 404, redeploy |

## What NOT to do

- MUST NOT deploy to a personal workspace — always use the `policyengine` workspace
- MUST NOT leave `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` env vars set when deploying via profile
- MUST NOT use `modal run` for production deployments — use `modal deploy`
- MUST NOT use `modal serve` for production — it creates ephemeral apps that stop when you close your terminal
- MUST NOT skip health check verification after deployment
- MUST NOT use generic app names — always match the dashboard/tool repo name
- MUST NOT hardcode secrets in Python code — use Modal Secrets
- MUST NOT deploy without confirming the target workspace with `modal token info`

## Related skills

- **policyengine-vercel-deployment-skill** — Frontend deployment to Vercel
- **policyengine-interactive-tools-skill** — Pattern C (custom Modal API) for interactive tools
- **policyengine-dashboard-workflow-skill** — Full dashboard creation workflow
