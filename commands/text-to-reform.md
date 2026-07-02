---
description: Convert a bill / URL / natural-language description into a validated reform-dict — Stage 1+2 of /analyze-policy without running the microsim
---

# Text to reform-dict

Standalone entry for bill → reform-dict translation. Runs the first two stages of `/analyze-policy` (understand + classify) and stops before the microsim.

## When to use

- "I have a bill (or link, or description) — what parameters does it touch?"
- "Would this even be modelable in PolicyEngine, before I invest in scoring it?"
- "Can I get a validated reform-dict I can then submit to `api.policyengine.org` myself?"

Do NOT use if you want the impact numbers — that's `/analyze-policy` end-to-end.

## Arguments

Same argument shape as `/analyze-policy`:

- State + bill number: `UT SB60`, `RI H7127`
- Federal bill: `US HR1234`, `US S5678`
- URL: a bill / proposal / order URL
- Description: `"ARPA-style federal CTC expansion: $3,600 ages 0-5, $3,000 ages 6-17, fully refundable"`
- Preset: `preset:<name>` — load from `presets/reforms/<name>.yaml`

Flags:
- `--country {us|uk|ca}` (default `us`)

## What this command does

1. `policy-text-researcher` fetches the bill/URL/description and extracts structured provisions with baseline_value / reform_value pairs.
2. `parameter-locator` (per provision, in parallel) maps each provision to PolicyEngine YAML paths. Runs the 5 pre-flight checks: master existence → deployed API existence → date coverage → formula liveness → reform-family toggles → per-year row coverage.
3. `reform-classifier` aggregates the per-provision verdicts and returns one of:
   - `parametric` — emits a full reform-dict + confidence
   - `deployed-model-lag` — parameter exists on master but not yet on deployed API; includes fallback advice
   - `structural` — needs model extension; emits parameter family + formula edit estimate
   - `not-possible` — outside PE's scope

## Output

The final reform-dict (JSON) ready to submit to `POST /{country}/policy` on the PE API. Plus the pre-flight check log so the analyst can see what was verified.

If the verdict is `structural` or `not-possible`, the output is the classification rationale rather than a reform-dict.

## Related

- `/analyze-policy` — the full pipeline. Runs this and then microsim + comparison + write-up.
- `/prior-scores` — parallel entry to consult external scorekeepers for the same reform.
- `presets/reforms/` — the preset library. If a reform is already in there, you don't need this command.
