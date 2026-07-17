---
name: policyengine-tools
description: |
  Load when building a standalone PolicyEngine interactive tool, calculator, or dashboard
  that deploys to Vercel and embeds into policyengine.org as a Next.js multizone.
  Covers the required stack (Next App Router + Tailwind v4 + @policyengine/ui-kit + bun),
  multizone zone config (basePath/assetPrefix, host rewrites, apps.json), Modal backends
  (gateway + worker + polling), chart patterns, and the dual-mode SEO strategy.
  Triggers: new tool, standalone calculator, dashboard, embed in policyengine.org, multizone,
  basePath, assetPrefix, appZoneRoutes, Modal backend, scale to zero, vercel --scope
  policy-engine, ui-kit theme.css, recharts colors.
  NOT for: developing policyengine.org itself (use policyengine-app) or token values
  (policyengine-design).
metadata:
  category: apps
---

# PolicyEngine standalone tools

How to build calculators, dashboards, and visualizations that deploy independently to Vercel
and slot into **policyengine.org** as Next.js multizones. New tools are their own repos; the
host (`policyengine-app-v2/website/`) proxies a URL path to each tool's Vercel deployment.

## Required stack

- **Next.js (App Router)** — not Pages Router, not Vite as the app bundler (Vite only backs
  Vitest). `next.config.ts` + `app/` with `layout.tsx` + `page.tsx`, TypeScript.
- **Tailwind v4, CSS-first** — no `tailwind.config.{ts,js}`. `globals.css` is exactly:
  ```css
  @import "tailwindcss";
  @import "@policyengine/ui-kit/theme.css";   /* both required; Tailwind must come first */
  ```
- **PostCSS is required for Next** — create `postcss.config.mjs` with
  `{ plugins: { "@tailwindcss/postcss": {} } }` and install `@tailwindcss/postcss` + `postcss`
  as devDeps. (A Vite tool uses the `@tailwindcss/vite` plugin instead and needs no PostCSS
  config.) The theme.css header itself states `@tailwindcss/postcss` is mandatory — the older
  "no postcss.config" guidance was wrong.
- **`@policyengine/ui-kit`** (`bun add @policyengine/ui-kit`) — use its components before
  building your own. See policyengine-design for the full 0.4.0 export list.
- **bun** for everything (`bun install`, `bun run build`, `bunx`; `bun.lock` committed).
- **Vercel** deploy under the `policy-engine` scope. Static-only tools may use
  `output: 'export'`; tools with a Modal backend stay server-rendered.

Scaffold: `bunx create-next-app@latest my-tool --ts --app --tailwind --eslint --import-alias "@/*"`,
then `bun add @policyengine/ui-kit` and set up `globals.css` as above.

## ui-kit components (verified 0.4.0)

Prefer these over hand-rolled equivalents; import from `@policyengine/ui-kit`:

| Need | Component |
|---|---|
| Page shell / layout | `DashboardShell`, `SidebarLayout`, `SingleColumnLayout`, `InputPanel`, `ResultsPanel`, `Stack`, `Group`, `Container` |
| Header + footer | `Header`, `Footer` (Header props: `navItems`, `logoSrc`, `linkComponent`, `countries` — **not** `variant`/`navLinks`) |
| Inputs | `CurrencyInput`, `NumberInput`, `SelectInput`, `CheckboxInput`, `SliderInput`, `InputGroup` |
| Primitives | `Button`, `Card`, `Badge`, `Tabs`, `Dialog`, `Select`, `Tooltip`, `Alert`, `Switch`, `SegmentedControl`, … |
| Display | `MetricCard`, `SummaryText`, `DataTable`, `PolicyEngineWatermark` |
| Charts | `ChartContainer`, `PEBarChart`, `PELineChart`, `PEAreaChart`, `PEWaterfallChart` |
| Maps | `USDistrictChoroplethMap`, `UKConstituencyChoroplethMap`, `HexagonalMap`, `HouseholdGraph` |
| Utils | `formatCurrency`, `formatPercent`, `formatNumber`, `cn`, `logos` |

Only build custom when nothing above fits. `getCssVar()` does not exist — SVG accepts `var()`.

## Multizone integration

The host proxies a path to your tool via `rewrites` in
`policyengine-app-v2/website/next.config.ts`. `basePath` governs **route URLs**;
`assetPrefix` governs **static asset URLs** (`_next/static/*`). Pick the zone pattern from
how many public paths the zone owns:

- **Path-mounted** (one public path matching the kebab repo name): `basePath: '/us/my-tool'`.
  Server-rendered builds need no `assetPrefix` — `basePath` scopes `_next/static` automatically.
- **Root-served** (multiple public paths, e.g. `/us/api` + `/uk/api`): no `basePath`; set
  `assetPrefix: '/_zones/<repo-name>'` so assets don't collide with the host.

Host rewrite (in `beforeFiles`, so it beats the dynamic `[slug]` route), hardcoded to the
zone's **production Vercel URL**:

```ts
{ source: '/us/my-tool',        destination: 'https://my-tool.vercel.app/us/my-tool' },
{ source: '/us/my-tool/:path*', destination: 'https://my-tool.vercel.app/us/my-tool/:path*' },
```

**Static-export zones** (`output: 'export'`) need three coordinated pieces — omit any and
that environment 404s its JS/CSS:

1. Zone `next.config.mjs` exports a **function** and phase-gates the prefix so `next dev`
   still resolves assets: `assetPrefix: phase === PHASE_DEVELOPMENT_SERVER ? undefined : '/_zones/my-tool'`,
   plus `output: 'export'`, `basePath`, `trailingSlash: true`.
2. Zone `vercel.json` with `"framework": null` (the Next preset silently drops `vercel.json`
   rewrites), explicit `buildCommand`/`outputDirectory: "out"`, `"trailingSlash": true`, and
   self-rewrites mapping basePath routes + `/_zones/<repo>/_next/*` onto the export root. Use
   regex `:path(.*)` (not `:path*`) so trailing-slash URLs match.
3. Host asset rewrite: `{ source: '/_zones/my-tool/:path*', destination: 'https://my-tool.vercel.app/_zones/my-tool/:path*' }`.

Mandatory rules:

- **Cross-zone navigation uses `<a>`, not `next/link`** — client-side routing breaks across zones.
- **Favicon via the file convention** — drop `app/icon.png` (and `app/apple-icon.png`, PNG
  only, 180×180). Next auto-prefixes the basePath. Do **not** use `metadata.icons` URLs; they
  are not basePath-prefixed and 404 under multizone.
- Render shared chrome from ui-kit (`Header`/`Footer`) so the zone looks native.
- App-specific provenance (policyengine.py version, static-estimate caveats) belongs in the
  tool's methodology footnote, never the shared header/footer.

### Deployment gotchas

- **Vercel auto-assigns a non-deterministic URL suffix** (e.g. `marriage-zeta-beryl.vercel.app`).
  Read the actual URL after first deploy and hardcode *that* in the host rewrite / apps.json —
  never guess it.
- **Deployment Protection returns 401.** Custom aliases can inherit protection; use the
  auto-assigned production `*.vercel.app` URL as the rewrite/iframe source, and disable
  Deployment Protection for the project if the host proxy gets 401s.
- Deploy with `vercel --prod --scope policy-engine`. If `package.json` is in a subdir, set the
  Vercel project Root Directory in the dashboard — don't fight it with a root `vercel.json`
  `cd subdir &&` command (the framework detector fails: "No Next.js version detected").

### Legacy iframe embedding

Only for legacy tools and the `obbba-iframe` / `custom` apps.json types — new tools use
multizone. Register in `policyengine-app-v2/website/src/data/apps.json` (`type`, `slug`,
`title`, `source` = auto-assigned Vercel URL, `countryId`, and for `displayWithResearch`:
`image`, `date`, `authors`). Embedded tools read country from the injected hash
(`const isEmbedded = window.self !== window.top`; `#country=uk`) and point share URLs at
`policyengine.org/{country}/{slug}`, not the Vercel URL.

## Data and backend patterns

Never paste ad-hoc computed numbers into source. Always: Python script → data file
(JSON/CSV) → frontend imports it. Pick by need:

- **A — Precomputed JSON/CSV**: finite scenarios (legislative trackers, static analyses). A
  `scripts/*.py` microsimulation writes to `public/data/`; the frontend imports it. Zero
  latency, works offline.
- **B — v1 PolicyEngine API** (`https://api.policyengine.org`): household-level calc across
  user-entered income/family/state. `POST /{country}/calculate` with a household payload, or
  the stateful household/economy flow. Always up to date; network latency. See policyengine-api.
- **C — Custom Modal backend**: only when the v1 API can't do it (society-wide microsim,
  custom reform params, non-standard entities). Pattern below.

### Pattern C: Modal gateway + worker + polling

Society-wide microsims exceed Modal's ~150 s gateway timeout, so use non-blocking job submit +
poll. Two resource profiles: a **cheap always-on gateway** (HTTP routing only, no policyengine
dep) and **expensive workers that scale to zero**.

Four files keep module-level imports safe (policyengine/pydantic only exist inside the Modal
image, not at import time):

| File | Module-level imports | Role |
|---|---|---|
| `backend/_image_setup.py` | none (imports inside the fn body) | `snapshot_models()` run at image build for fast cold starts |
| `backend/simulation.py` | `policyengine_us`/`_uk` (captured in the snapshot) | pure business logic, no Modal |
| `backend/app.py` | only `modal` | worker functions |
| `backend/modal_app.py` | `modal`, `fastapi`, `pydantic` | lightweight gateway |

Worker functions get high CPU/memory but **must** scale to zero — never set `keep_warm` or
`min_containers`; the image snapshot (`.run_function(snapshot_models)`) makes cold starts ~2 s.

```python
# backend/app.py — workers
import modal
from _image_setup import snapshot_models
app = modal.App("my-tool-workers")
image = (modal.Image.debian_slim(python_version="3.11")
         .pip_install("policyengine-us==X.Y.Z", "pydantic")   # pin to the current PyPI release
         .run_function(snapshot_models)
         .add_local_file("backend/simulation.py", remote_path="/root/simulation.py"))

@app.function(image=image, cpu=8.0, memory=32768, timeout=3600)   # no keep_warm / min_containers
def compute_statewide(params: dict) -> dict:
    from simulation import run_statewide
    return run_statewide(params)
```

```python
# backend/modal_app.py — gateway (spawn + poll)
import modal
from fastapi import FastAPI
app = modal.App("my-tool")
web_app = FastAPI()

@web_app.post("/submit/{endpoint}")
def submit(endpoint: str, params: dict):
    fn = modal.Function.from_name("my-tool-workers", "compute_statewide")
    return {"job_id": fn.spawn(params).object_id}

@web_app.get("/status/{job_id}")
def status(job_id: str):
    from modal.functions import FunctionCall
    call = FunctionCall.from_id(job_id)
    try:
        return {"status": "ok", "result": call.get(timeout=0)}
    except TimeoutError:
        return {"status": "computing"}

@app.function(image=modal.Image.debian_slim().pip_install("fastapi", "pydantic"), memory=256)
@modal.asgi_app()          # full FastAPI app; use @modal.fastapi_endpoint for a single route
def fastapi_app():
    return web_app
```

The frontend submits then polls with a React Query hook (`refetchInterval` while
`status === "computing"`). Deploy footgun: **`unset MODAL_TOKEN_ID MODAL_TOKEN_SECRET`
before `modal deploy`** — a stale token env var silently deploys to the wrong workspace.
Deploy workers first (builds the snapshot), then the gateway; URL is
`https://policyengine--my-tool-fastapi-app.modal.run`. Set it as `NEXT_PUBLIC_API_URL` in
Vercel. Modal apps can silently disappear — if the frontend gets network errors, `curl` the
URL and redeploy on 404.

## Charts

Prefer ui-kit's chart components (`PEBarChart`, `PELineChart`, `ChartContainer`) — they own
round-tick and formatting logic. When hand-rolling Recharts:

- **Colors: pass `var(--chart-1)` … `var(--chart-5)` directly** to SVG `fill`/`stroke`; grid
  and chrome use `var(--border)` / `var(--foreground)`. Never hardcode hex.
- **Round ticks: set `niceTicks="snap125"` on every numeric `<XAxis>`/`<YAxis>`** (recharts
  ≥3.8 — a PolicyEngine-contributed prop; verify your resolved recharts version first, e.g.
  app-v2's lockfile still resolves 3.7.0 where the prop is silently ignored). `snap125` snaps
  tick steps to {1, 2, 2.5, 5}×10ⁿ for human-round labels; pair it with
  `domain={["auto", "auto"]}` because the default `[0, 'auto']` domain clamps the minimum and
  breaks tick calculation for data that doesn't start at 0. Below 3.8, control ticks with
  `tickFormatter`, `tickCount`, or an explicit `ticks={[…]}` array.
- **Tooltip**: set `separator=": "` (the default has a leading space).
- **Currency: sign before symbol** — `-$31`, never `$-31`. Use `Intl.NumberFormat` (or
  ui-kit's `formatCurrency`), never string concatenation:
  ```ts
  const fmt = (v: number) => v.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  ```
- Wrap in `ResponsiveContainer` with an explicit height; `dot={false}` for dense lines.

See policyengine-design for the color tokens and the Plotly house style (maps/Python).

## SEO (dual-mode)

Most SEO is generic; the PolicyEngine-specific part is **dual-mode canonical**. A tool exists
at both its `*.vercel.app` URL and the `policyengine.org/{country}/{slug}` path. Set a single
`<link rel="canonical">` pointing at the **policyengine.org path** (the surface users, ads,
and Google should index) to avoid duplicate-content dilution. Under Next multizone the host
route is the public URL, so per-route `generateMetadata` (title, description, canonical, OG)
must be server-rendered — do not gate SEO tags on `isEmbedded`.

## Verification

`curl` 200 does not mean the app renders — `bun run build` is the compile check. Check
`lsof -i :<port>` before claiming the dev server runs. You cannot visually verify; hand off to
the user after a green build. Sentence case on all UI text. Add PR CI (`bun install`, lint,
test, `bun run build`) before launch.

## Related skills

- policyengine-app — the host site (policyengine.org) and its multizone registry
- policyengine-design — ui-kit 0.4.0 components, tokens, chart colors, Plotly style
- policyengine-api — v1/v2 API surfaces for Pattern B
- policyengine (Python) — microsimulation for Pattern A/C data scripts
