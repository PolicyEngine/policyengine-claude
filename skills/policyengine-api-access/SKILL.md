---
name: policyengine-api-access
description: |
  Load before writing or reviewing code that reaches the PolicyEngine Public API
  (api.policyengine.org) from a dashboard, tool, backend, Modal app, Vercel function or CI
  job. The Public API serves only PolicyEngine's servers: pages call www.policyengine.org's
  dashboard API through @policyengine/api-client, and servers send their own Auth0
  client-credentials token. Covers the rules, the four dashboard operations, polling, allowed
  origins, cached server tokens, getting a client, local development and previews, asking for a
  new operation, and 401/403/429/503.
  Triggers: api.policyengine.org, Public API, dashboard API, @policyengine/api-client, household
  calculate from the browser, economy comparison polling, NEXT_PUBLIC_API_URL, VITE_API_URL,
  Auth0 client credentials, server token, PUBLIC_API_SERVER_CLIENT_IDS, Authentication is
  required, CORS error from the API.
  NOT for: Python analysis (policyengine skill) or the Public API's own endpoints and code
  (policyengine-api).
metadata:
  category: apps
---

# Reaching the Public API from dashboards and servers

The Public API (`PolicyEngine/policyengine-api`, https://api.policyengine.org) is becoming
callable only by PolicyEngine's own servers. Once its credential requirement is switched on, it
answers every request without a server credential with 401, except `GET`/`HEAD /health`,
`GET /v2/openapi.json` and CORS preflights. Anything in browser code is public, so a page cannot hold that
credential. Pages go through a server that does.

## The rules

1. **Browser code never calls the Public API**: not `api.policyengine.org`, and not its Cloud
   Run addresses (`policyengine-api-….a.run.app`, `policyengine-api-staging-….a.run.app`,
   or a tagged revision's `…---policyengine-api-….a.run.app`). Browser code is everything that
   runs in the page: components, hooks, client modules, static exports and anything a bundler
   puts in the page.
2. **No Public API credential or address goes in a `NEXT_PUBLIC_*` or `VITE_*` variable.**
   Next.js and Vite copy those values into the page's JavaScript. That covers the Auth0
   client ID and secret, tokens, and the Public API's URL.
3. **One Auth0 client per calling server**, never shared between callers or copied into
   another repository. The client ID is how the Public API's records identify the caller.

## Which route to use

| Where the code runs | How it reaches the Public API |
|---|---|
| A dashboard page (browser) | www.policyengine.org's dashboard API, through `@policyengine/api-client` |
| A dashboard's precompute script (presets, fixed grids) | The same place as the page's live calculations, so both use one model release: on Pattern B, the dashboard API, with plain HTTPS requests and no credential, within the budget below ("From a dashboard's precompute script"); on Pattern C, the backend's pinned `policyengine` release in its own process. A precomputed-only dashboard uses the dashboard API, or the pinned package when policyengine-tools' model-version check allows it |
| A dashboard's own backend (Modal, Cloud Run, a Vercel function) | Runs `policyengine` in its own process and doesn't call the Public API (policyengine-tools, Pattern C). Only a backend that already has a client sends its token in `Authorization: Bearer` |
| Any other CI job or script | Its own Auth0 client, one token per job run |
| Python analysis or a notebook | The `policyengine` package (policyengine skill), not REST |

The dashboard API serves `us` and `uk` only. A dashboard for another country, such as Canada,
precomputes its results with that country's package (`policyengine-canada`) or, when it can't,
runs that package in its own backend (policyengine-tools, Pattern C).

If a backend exists only to relay one of the four dashboard operations, drop it and call the
dashboard API from the page instead. Whether a dashboard needs a backend at all is settled by
the four options, checked in order, in policyengine-tools' "Data and backend patterns".

## From pages: the dashboard API

www.policyengine.org (`website/` in `PolicyEngine/policyengine-app-v2`) serves four operations.
Its server adds PolicyEngine's credential, so a dashboard needs none, and dashboards never see
the Public API's paths.

```bash
npm install @policyengine/api-client
```

```ts
import {
  createPolicyEngineApiClient,
  EconomyComparisonTimeoutError,
  PolicyEngineApiError,
} from "@policyengine/api-client";

const policyengine = createPolicyEngineApiClient();

const household = await policyengine.calculateHousehold({
  country: "us",
  household: {
    people: { you: { age: { 2026: 40 }, employment_income: { 2026: 50000 } } },
    households: { your_household: { members: ["you"], household_net_income: { 2026: null } } },
  },
  policy: { "gov.irs.credits.ctc.amount.base[0].amount": { "2026-01-01.2100-12-31": 3000 } },
});

const reformId = await policyengine.createPolicy({
  country: "us",
  parameters: { "gov.irs.credits.ctc.amount.base[0].amount": { "2026-01-01.2100-12-31": 3000 } },
});
const impact = await policyengine.compareEconomy(
  { country: "us", policy: reformId, baseline: 2, region: "us", year: 2026 },
  { onProgress: (answer) => console.log(answer.status) },
);

const metadata = await policyengine.getMetadata("uk");
```

| Operation | Request | Answer |
|---|---|---|
| `POST /api/household/calculate` | JSON `{country, household, policy?}`; `policy` is parameter changes, current law when omitted | The Public API's `{status, message, result}`; `calculateHousehold` resolves with `result` |
| `POST /api/policies` | JSON `{country, parameters}` | `{id}`: 201 for a new policy, 200 for an identical stored one; `createPolicy` resolves with the ID |
| `GET /api/economy/compare` | Query `country`, `policy`, `baseline`, `region`, `year`, each exactly once | `{status: "computing" \| "ok" \| "error", result, …}`, never cached |
| `GET /api/metadata/{country}` | — | `{status, message, result}`, cached by browsers for an hour (`max-age=3600`) |

- `country` is `us` or `uk`. An unknown body field (household calculation, policies) or query
  parameter (economy comparison) is refused with 400, and a body whose `Content-Type` is not
  JSON with 415.
- `policy` and `baseline` are policy IDs (whole numbers). `baseline` is current law's ID:
  2 for `us`, 1 for `uk` (`result.current_law_id` in the metadata). `year` is four digits;
  `region` is `us`, `uk` or a sub-national region such as `state/ca`, at most 200 characters.
- The household and parameter shapes are the Public API's (`household` nests values by year;
  read variable and parameter names from the metadata). See the policyengine-api skill.
- `POST /api/household/calculate` is the Public API's `/{country}/calculate`, which adds no
  variables the household leaves out: ask for each output by naming it on its entity
  with `null` for the year (`income_tax: { 2026: null }`). To vary an input for a chart, send
  one household with `axes` (`[[{ name: "employment_income", period: "2026", min: 0, max:
  200000, count: 41 }]]`) and its value `null`; each output comes back as a list over the
  points. Never send one calculation per point: the limit is 30 a minute.
- Each method takes `{ signal }` to cancel. The result type is a type argument
  (`calculateHousehold<MyHousehold>(…)`), not checked at run time.

**Polling.** `compareEconomy` reads the comparison every 5 seconds until `status` is `ok`, and
gives up after 30 minutes with `EconomyComparisonTimeoutError`. After a 429 it waits for
`Retry-After`, or 60 seconds (`RATE_LIMIT_WAIT_MILLISECONDS`, the firewall's window) when there
is none, but never less than one interval or one second, and keeps polling. A page on another
origin cannot read the firewall's 429 (see rate limits below), so there polling stops with
`status` `null`. After a 502, 503 or 504 it waits for `Retry-After`, or one interval, and the
fourth such failure since the last answer ends polling. A comparison
that failed (502 with
`status: "error"` and `retry_after_seconds`) is thrown at once: the Public API keeps that
failure for `retry_after_seconds`, so polling sooner returns it again. Keep
`intervalMilliseconds` at a few seconds. Use `getEconomyComparison` for one read.

**Where pages may call it from.** The client's default `baseUrl` is
`https://www.policyengine.org`. The dashboard API answers browser requests from:
- pages on www.policyengine.org itself, which is how dashboards served through the website's
  rewrites (`website/src/data/appZoneRoutes.ts`) reach it: same origin, no CORS;
- `http://localhost` and `http://127.0.0.1` on any port;
- the PolicyEngine team's Vercel hosts, `*-policy-engine.vercel.app`: its previews and each
  project's `<project>-policy-engine.vercel.app` host;
- each dashboard's own `*.vercel.app` host named in `appZoneRoutes.ts`.

Every other origin gets 403, "Pages on this origin may not call the dashboard API.", and the
request never reaches the Public API. Allowed request headers are `Content-Type`,
`Authorization` and `PolicyEngine-Unauthenticated-User`; the client sends no cookies
(`credentials: "omit"`).

**Serve a new dashboard through a www.policyengine.org rewrite.** Add its rewrite to
`appZoneRoutes.ts` (policyengine-tools, "Multizone integration") and deploy that change
before, or with, the first release whose pages call the dashboard API. Pages served through
the rewrite are then same-origin on www.policyengine.org, and the dashboard's own
`*.vercel.app` host is allowed automatically. A dashboard served only from somewhere else (a
Modal URL, a custom domain, or a `*.vercel.app` host that `appZoneRoutes.ts` doesn't name and
that doesn't end in `-policy-engine.vercel.app`) gets 403, which the browser shows as a CORS
error, until its exact host is added to the dashboard API's allow list in
`website/src/lib/dashboardApi/cors.ts` in PolicyEngine/policyengine-app-v2 and that change is
deployed. The allow list takes only exact host names, never a pattern such as `*.vercel.app`
or `*.modal.run`, because anyone can deploy there.

The order matters only for the shorter host. A project's `<project>-policy-engine.vercel.app`
host is allowed from its first deploy, so a page opened there works before the rewrite exists;
`/deploy-dashboard` relies on that when it deploys first and adds the rewrite afterwards. Its
`<project>.vercel.app` host, or any other alias, is refused until the rewrite naming it is
deployed, so a release that sends readers to that host needs the rewrite first.

**Rate limits.** www.policyengine.org's Vercel firewall limits each IP address in
fixed 60-second windows, counted per Vercel region: 30 household calculations, 120
economy-comparison reads, and 300 policy creations and metadata reads together. Everyone behind one address, such
as an office network, shares them. Over a limit the firewall answers before the dashboard API
runs: 429, text/plain "Too Many Requests", no `Retry-After` (so `retryAfterSeconds` is `null`)
and no CORS headers. A page on www.policyengine.org reads that 429; a page on another origin,
such as `http://localhost` in development, gets a network failure (`status` `null`). Requests
are accepted again when the window ends. Calculate on a user's action or after a debounce, not
on every keystroke.

**Stay at half of each limit.** Design a page so one person's normal use takes at most 15
household calculations, 60 economy-comparison reads, and 150 policy creations and metadata
reads in any minute. Everyone behind one address shares the limits, so the rest is theirs.
When a calculation is refused for the limit anyway (429 on www.policyengine.org, `status`
`null` elsewhere), keep the last answer on screen and say that everyone on the same network,
such as a workshop or an office, shares a limit on calculations a minute, and that the page can
calculate again within a minute. Don't send the calculation again until then.

- Make one household calculation per user action where you can: put every charted input in
  `axes` in that one call (separate inner lists give a grid over two inputs), and ask for each
  year's outputs in the same household.
- Keep answers in the page, and don't calculate again for inputs that haven't changed.
- Precompute fixed households, such as presets, and comparisons of fixed policies. A page
  that also calculates live through the dashboard API computes its presets through the
  dashboard API too, so both use the same model release ("From a dashboard's precompute
  script", below).
- `compareEconomy` reads every 5 seconds, which is 12 reads a minute for each comparison in
  progress, so run at most five comparisons at once, and one where you can.
- Don't load the metadata in a page unless the page needs it: the US metadata is about 75 MB
  uncompressed. Take the variable and parameter names and labels the page needs at build
  time. A page that does need it reads it once per page load.

A feature that can't fit this budget, even with `axes`, is precomputed; only one that can't be
precomputed goes to the dashboard's own backend (policyengine-tools, "Data and backend
patterns").

**From a dashboard's precompute script.** On Pattern B, and on a precomputed-only dashboard
unless policyengine-tools' model-version check lets its script run the pinned package, a Python
script that builds a dashboard's presets or fixed grids at build time calls the same dashboard
API, so its results match what the page calculates live. On Pattern C it runs the backend's
pinned `policyengine` release instead (the route table above). It sends no credential and no `Origin` header, which the dashboard API accepts
from servers. This path is only for a dashboard's own build-time presets and grids. Any other
script, especially a larger or recurring one, gets its own client ("Getting a client", below).
Keep it within the budget: one calculation per preset or grid slice, with the slice's charted
input in `axes`, at most 15 a minute, and a wait for the next window after a 429. Run a long
sweep from CI rather than from an office network, whose limit everyone there shares while it
runs:

```python
import time

import requests

HOUSEHOLD_CALCULATION = "https://www.policyengine.org/api/household/calculate"


def calculate_household(country: str, household: dict, policy: dict | None = None) -> dict:
    """One household calculation through the dashboard API, the model the page uses."""
    body = {"country": country, "household": household}
    if policy:
        body["policy"] = policy
    while True:
        # The route waits up to 750 s for the Public API and runs for at most 800 s.
        response = requests.post(HOUSEHOLD_CALCULATION, json=body, timeout=900)
        if response.status_code == 429:
            time.sleep(60)  # this minute's limit is used up; never retry at once
            continue
        response.raise_for_status()
        time.sleep(4)  # at most 15 calculations a minute
        return response.json()["result"]
```

Fixed comparisons of a policy with current law work the same way through `/api/policies` and
`/api/economy/compare`. Poll the way `compareEconomy` does for pages: read every 5 seconds until
`status` is `ok`, and give up after 30 minutes; after a 429, wait for `Retry-After`, or 60 seconds
when there is none; after another 502, 503 or 504, wait for `Retry-After`, or 5 seconds, and
stop after the fourth in a row; and stop at once on a failed comparison (502 with
`status: "error"` and `retry_after_seconds`), because the Public API returns the same failure
until `retry_after_seconds` has passed. A loop that only waits for `ok` keeps reading a failed
comparison until the job's time limit, which is six hours by default on GitHub Actions.

## From servers: your own Auth0 client

A server (a PolicyEngine service, a CI job, or a dashboard backend that already has a client)
calls the Public API directly with an Auth0 client-credentials token. A new dashboard's backend
doesn't: it runs `policyengine` in its own process (policyengine-tools, Pattern C) and needs no
client. The token comes from the Public API's own tenant:

| | Production | Staging |
|---|---|---|
| Auth0 tenant (`POLICYENGINE_API_AUTH0_DOMAIN`) | `policyengine-api.uk.auth0.com` | `policyengine-api-staging.uk.auth0.com` |
| Audience (`POLICYENGINE_API_AUTH0_AUDIENCE`) | `https://api.policyengine.org/` | `https://staging-api.policyengine.org/` |
| Public API (`POLICYENGINE_API_URL`) | `https://api.policyengine.org` | the staging Cloud Run service, given with the client |

The token request is `POST https://<tenant>/oauth/token` with JSON
`{"grant_type": "client_credentials", "client_id": …, "client_secret": …, "audience": …}`.
Send the answer's `access_token` as `Authorization: Bearer <token>` on every request.
A client token from the sign-in tenants (`auth.policyengine.org`,
`policyengine-dev.uk.auth0.com`) is refused with 401.

Other headers, when a server acts for a browser:
- a signed-in user's Auth0 token goes in `PolicyEngine-User-Authorization: Bearer <token>`,
  never in `Authorization`;
- `PolicyEngine-Unauthenticated-User: <uuid>` is passed on unchanged;
- send at most one of each; two `Authorization` headers are refused.

**Cache the token across instances.** Tokens last 24 hours, and Auth0 counts the
machine-to-machine tokens it issues per tenant per month. Never request a token per request.
Without a shared store each instance requests one when it starts, which is fine for a few
long-lived instances (a Cloud Run service with a low maximum) but not where instances start
often, such as Modal containers:
- **Python (Modal, Cloud Run, scripts):** copy `templates/public_api_token.py`. It keeps the
  token in memory and, when given one, in a store the instances share (a `modal.Dict` on Modal;
  any object with `get` and item assignment), replaces it five minutes before it expires,
  raises a 401 without requesting another token, and never follows a redirect. Its docstring
  has the Modal wiring.
- **Vercel functions:** keep it in Vercel Runtime Cache, as app-v2's
  `packages/public-api-forwarding/src/accessToken.ts` does:

  ```ts
  import { getCache } from "@vercel/functions";

  type CachedToken = { accessToken: string; refreshAtMilliseconds: number };
  const tokenCache = getCache({ namespace: "policyengine-public-api" });

  const cached = (await tokenCache.get(cacheKey)) as CachedToken | null | undefined;
  if (!cached || Date.now() >= cached.refreshAtMilliseconds) {
    // Request a token; accessToken and expiresIn (seconds) come from Auth0's answer. Keep it
    // until five minutes before it expires, or halfway through a shorter life.
    const keepSeconds = expiresIn - Math.min(300, expiresIn / 2);
    const refreshAtMilliseconds = Date.now() + keepSeconds * 1000;
    await tokenCache.set(cacheKey, { accessToken, refreshAtMilliseconds }, { ttl: Math.max(1, Math.floor(keepSeconds)) });
  }
  ```

  The key is the tenant, audience and client ID, never the secret. Requests that arrive while a
  token is being fetched should wait for that one request.
- **CI:** request one token at the start of the job and reuse it for every request in the job.

Also:
- **Store the five variables in a secret store**, under the names app-v2 and the template use:
  `POLICYENGINE_API_URL`, `POLICYENGINE_API_AUTH0_DOMAIN`, `POLICYENGINE_API_AUTH0_AUDIENCE`,
  `POLICYENGINE_API_AUTH0_CLIENT_ID` and `POLICYENGINE_API_AUTH0_CLIENT_SECRET`. That is a Modal
  secret, Vercel environment variables (the secret marked sensitive), or GitHub Actions secrets
  and variables. Never the repository, never a `NEXT_PUBLIC_*` or `VITE_*` name.
- **Never follow redirects.** A followed 307 or 308 re-sends the token request's body, client
  secret included, to wherever it points, and Python's `urllib` also copies `Authorization` to a
  redirect's target. The template turns redirects off for both requests; in `fetch`, pass
  `redirect: "error"`.
- **Cache what does not change.** `/{country}/metadata` is about 10 MB compressed; read it once
  per deployment or hour, not per request.

### Getting a client

1. Ask for a client for your caller in a new issue in `PolicyEngine/policyengine-api`, in
   PolicyEngine's Slack, or both. Say which repository and service it is, and which
   environments it needs: production, and staging if previews or local work call the Public
   API too.
2. The Public API's maintainers create a machine-to-machine application in each tenant, with only the
   `client_credentials` grant and a grant for that tenant's audience, and put the secret straight
   into your caller's secret store. A secret never goes in an issue, a chat message, a PR or a
   file.
3. They add the client ID to `PUBLIC_API_SERVER_CLIENT_IDS` in policyengine-api's GitHub
   `production` (and `staging`) environment and redeploy the Public API.
4. **Only then deploy code that sends the token.** A valid token of a client that is not on the
   list gets 401 today, even while requests without any `Authorization` header are still served.
5. Check it: `GET /health` with the token answers 200. The Public API checks a sent token on
   every route, including `/health`, so 401 there means the client, tenant or audience is wrong.

## Local development and previews

- **Dashboard pages:** a dashboard on `http://localhost:<port>` or on its team preview
  (`*-policy-engine.vercel.app`) calls the production dashboard API at www.policyengine.org
  through CORS, with nothing to configure and no credential on the developer's machine. To try a
  change to the dashboard API before it is deployed, pass that website preview's URL as
  `baseUrl`; website previews call the Public API's staging service.
- **Servers:** production deployments use the production tenant, client and Public API;
  preview and development deployments use the staging tenant, a staging client and the
  staging service. On Vercel, set the five variables per environment (Production; Preview and
  Development), then run `vercel env pull .env.local` for local work, which writes the
  Development values. Vercel cannot mark Development values sensitive, so only staging values go
  there. On Modal, keep production and staging values in separate secrets.
- Never point a preview or a local run at the production Public API with the production client.

## Asking for a new dashboard operation

The dashboard API has exactly the four operations above. Ask for a new one only when a page
needs a Public API route outside them, used unchanged, that other dashboards would plausibly
use too, such as the budget-window comparison. "Used unchanged" means the page sends inputs
the route already accepts and uses its answer as it comes back, with nothing computed on top.
Anything else the four can't give is precomputed, fixed in the country package or the Public
API, or, last, the dashboard's own backend (policyengine-tools, "Data and backend patterns").
The Public API's model being older than the one you need is a reason for none of these
while the `policyengine` package's model bundle is updated weekly; policyengine-tools' "Data
and backend patterns" says how to check.

Adding one is a change to
`PolicyEngine/policyengine-app-v2`: a route under `website/src/app/api/` and its check in
`website/src/lib/dashboardApi/operations.ts`, a method in `packages/api-client`, and a new
release of `@policyengine/api-client`. Ask for it in a new issue in
`PolicyEngine/policyengine-app-v2`, in PolicyEngine's Slack, or both, naming the Public API
call it maps to, the request and answer shapes the dashboard needs, how often a page calls it, and whether its answers can be
cached. Until it ships, do not call the Public API from the page as a stopgap; precompute the
data.

## Errors

`@policyengine/api-client` throws `PolicyEngineApiError` with `status` (`null` when no answer
could be read), `message`, `body` and `retryAfterSeconds`. The dashboard API's own errors are
`{"status": "error", "message": …, "result": null}`; the Public API's 401 and 503 bodies have
`status` and `message` only. Read `message`.

| Status | From | Meaning | What to do |
|---|---|---|---|
| 400 | Dashboard API | A missing or unknown field, or a malformed value | Fix the request; `message` names the field |
| 401 | Public API | `{"status":"error","message":"Authentication is required"}` with `WWW-Authenticate: Bearer`. Usually the server's own token: an invalid or expired token, a client not on the allow list, a client token from another tenant, two `Authorization` headers, or, once the requirement is on, no server credential. A user route answers the same when the server forwards no user credential | Server: do not request another token, which would be refused too and counts against the tenant's monthly allowance. On a user route, check first that the request forwarded the user's credential; otherwise check that the client is listed in that environment and that its tenant and audience match, and report it. Page: the website's own credential failed; show an error, do not retry in a loop |
| 401 | Public API user routes | `WWW-Authenticate: Bearer error="invalid_token"` and "The bearer access token is invalid": the forwarded `PolicyEngine-User-Authorization` token is invalid or expired | Keep the server token; the user signs in again |
| 403 | Dashboard API | "Pages on this origin may not call the dashboard API." The page's origin is not allowed | Serve the page through its rewrite in `appZoneRoutes.ts`, or add its exact host to the allow list in `cors.ts`. A cross-origin page cannot read this answer: the browser reports a CORS error and the client throws with `status` `null` |
| 403 | Public API user routes | A forwarded `PolicyEngine-User-Authorization` token is a machine-to-machine token, not a user's | Forward only a signed-in user's own token there |
| 404 | Dashboard API | An unknown country in `/api/metadata/{country}` | Use `us` or `uk` |
| 415 | Dashboard API | The body's `Content-Type` is not JSON | Send `Content-Type: application/json`; the client does |
| 429 | Dashboard API firewall | "Too Many Requests" as text/plain, with no `Retry-After` and no CORS headers: one IP address passed a per-minute limit | Wait for the 60-second window to end before sending again; never retry at once. On another origin (localhost) the page sees a network failure with `status` `null` instead, so treat repeated `null` statuses during heavy use the same way |
| 429 | The Public API's load balancer | Too many requests from one IP address, not JSON | Server: wait `Retry-After` when present, otherwise back off (5 s, then doubling). Requests with a bearer token skip its per-address limits on `/{country}/metadata`, `/{country}/calculate` and `/{country}/calculate-full` |
| 502 | Dashboard API | Auth0 refused or did not answer the website's token request, the Public API could not be reached or answered with a redirect, or the Public API's answer to `POST /api/policies` named no policy ID | Retry later with back-off |
| 502 | Public API, economy comparison | `status: "error"` with `retry_after_seconds`: the comparison failed | Show the failure; do not ask again before `retry_after_seconds` |
| 503 | Public API | `{"status":"error","message":"Authentication is unavailable"}`: it could not check the token (Auth0's signing keys unreachable, or its own settings) | Keep the token; retry with back-off. It is not a refusal of the client |
| 503 | Dashboard API | Its own settings are missing or incomplete, for example on a website preview | Not retryable; report it to the website's maintainers |
| 504 | Dashboard API | The Public API did not answer in time (750 s for a household calculation, 40 s for a policy or a comparison read, 60 s for metadata) | Retry later with back-off. A household calculation has already waited 750 s, so a page shows the failure instead of retrying it |

## Related skills

- policyengine-api — the Public API's endpoints, household and policy shapes, and the v2 alpha
- policyengine-tools — building and embedding a standalone tool; its data patterns
- policyengine-app — policyengine.org itself, including `appZoneRoutes.ts`
- policyengine-cloud-costs — Modal and Cloud Run settings and secrets for a backend
