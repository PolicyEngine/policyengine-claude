## Running costs

<!-- Fill this in before the first deploy, and update it in any PR that changes a
     declared exception. Prices: see the policyengine-cloud-costs skill. -->

| Question | Answer |
|---|---|
| What runs while nobody uses it? | Nothing: every minimum is 0. |
| Most it can cost in an hour | `compute`: 10 containers × 1 core / 2 GiB ≈ 10 × $0.063 = $0.63/hour |
| How the bill is checked | Monthly: `modal billing report --for "last month" --tag-names project --json`, apps tagged `project=TOOL_NAME`; compare with the row above |
| Copies and how each one ends | PR previews (`TOOL_NAME-pr-N`): stopped when the PR closes, by `.github/workflows/stop-preview-app.yml` |
| Where secrets live | Modal secret `TOOL_NAME`; GitHub Actions secrets `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`. Nothing in the repo. |
| Owner, and when it is reviewed or retired | @OWNER; review by YYYY-MM-DD |

### Declared exceptions

Settings that differ from the defaults on purpose. Each one also has a
`# cost-ok: <rule> <reason>; until <date>` comment where it is set.

| Setting | Where | Why | Until | Cost |
|---|---|---|---|---|
| none | | | | |

<!-- Example row:
| `min_containers=2` on `compute` (MO1) | backend/app.py | Launch-day traffic; a cold start takes 17 s | 2026-11-30 | 2 × $0.063 × 24 ≈ $3/day |
-->
