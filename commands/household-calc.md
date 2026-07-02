---
description: Calculate benefits, taxes, and net income for a single household under baseline or a reform — the standalone entry for household-level questions
---

# Household calculation

Answer "what would this specific household get?" questions. Standalone entry for household-level microsimulation — not population-level (`/analyze-policy` handles that).

## When to use

- "What would a single parent making $35K with two kids get from SNAP + CTC in Texas?"
- "How does a married couple filing jointly in California with $200K W-2 income + $30K SALT compare under the current cap vs $60K cap?"
- "What's the effective marginal tax rate for a childless adult earning $18/hr in New York?"

Do NOT use for population-level questions ("how many households benefit"; "what's the aggregate cost") — those need `/analyze-policy` or the microsimulation skill.

## Arguments

`$ARGUMENTS` — natural-language household description + question. Include:
- Country (`US`, `UK`, `CA`) and state / province if relevant
- Household composition (single, married, dependents with ages)
- Income sources ($ amounts for wages, SS, unemployment, etc.)
- The question — baseline benefits? A specific reform? A marginal-rate calculation?

Flags:
- `--year YYYY` (default: current tax/benefit year)
- `--reform <preset-name-or-dict>` — apply a preset reform (see `presets/reforms/`) or a raw reform-dict JSON before calculating
- `--reform-file PATH` — load reform-dict from a file

## What this command does

1. Loads the appropriate country skill (`policyengine-us` / `policyengine-uk` / `policyengine-canada`) — these carry the correct API patterns for the current package version.
2. Constructs a `Simulation` (household-level, not `Microsimulation`) using the parsed household description.
3. Calculates the variables the user asked about (net income, specific benefit, tax owed, marginal rate).
4. Reports baseline values, reform values (if `--reform`), and the delta.
5. Optionally cites the parameter paths that drove each result so the analyst can trace numbers back to statute.

## Related

- `/analyze-policy` — population-level version. Use when the question is about aggregate cost or distribution, not a single household.
- `/prior-scores` — consult external benchmark cluster for the reform without running any microsim.
- `policyengine-us` skill — the underlying API pattern reference.
