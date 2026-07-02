---
description: Consult external scorekeepers (JCT, CBO, OBR, IFS, PBO, CRFB, TPC, etc.) for a reform without running the microsim
---

# Prior scores lookup

Standalone entry for external-benchmark research. Runs `prior-scores-finder` (Stage 3 of `/analyze-policy`) without the microsim or comparison stages.

## When to use

- "What has JCT / CBO scored on this reform shape?"
- "Have any think-tanks published estimates for a similar SALT cap change?"
- "I already have a rough sense of my number; I just want to see whose external estimates I should benchmark against."

Do NOT use this to substitute for a microsim — this just aggregates what OTHER organizations have scored. `/analyze-policy` compares PE's own model against them.

## Arguments

`$ARGUMENTS` — a reform description or bill reference. Same argument shape as `/analyze-policy`.

Flags:
- `--country {us|uk|ca}` — determines which scorekeepers to consult (from `presets/scorekeepers.yaml`)
- `--tier {2|3|all}` — Tier 2 = official fiscal offices (JCT, CBO, OBR, PBO); Tier 3 = think-tanks (CRFB, TPC, IFS, etc.); `all` = both. Default `all`.
- `--domain <tag>` — restrict to scorekeepers marked as covering this domain (`tax`, `benefits`, `healthcare`, `distributional`, etc.)

## What this command does

1. Loads the scorekeepers registry (`presets/scorekeepers.yaml`) filtered by country + tier + domain.
2. Also consults Tier 0 (local `analyses/` archive) via `scripts/analyses_kb.py` — surfaces prior PE runs on the same parameter family.
3. Also consults Tier 1 (PolicyEngine published research) via the `policyengine-prior-scores` skill.
4. Iterates through each scorekeeper's `search_hints`, runs WebSearch queries, and extracts headline magnitudes.
5. Returns a structured benchmark cluster ready to feed into a research writeup — same shape as `benchmark_sources[]` in an archived analysis.

## Output

Ranked list of external scores with:
- Source name + URL
- Their estimate (10-year cost, per-year cost, poverty change, or whatever they published)
- Reform shape they scored (may differ from yours — note structural distance)
- Methodology notes (static / dynamic, dataset, baseline)

## Related

- `/analyze-policy` — the full pipeline invokes this in Stage 3, then compares PE's microsim against the results.
- `presets/scorekeepers.yaml` — the registry. Add a new scorekeeper by appending to this file; no code change required.
- `scripts/scorekeepers.py list --country {us|uk|ca}` — CLI equivalent.
