---
description: Search the local analyses archive for prior /analyze-policy runs — did we already score this? What did we conclude?
---

# Prior analysis lookup

Search the analyses/ archive without invoking the full pipeline. Answers "have we already analyzed this?" and "what did we find?"

## When to use

- Before running `/analyze-policy` — check whether this reform has been scored recently. Datasets and models evolve, but if a near-identical analysis exists from days ago the archived numbers may be reusable.
- After deploying a policy change to PE-US: find every archived analysis that touched the parameter family, so the team can flag which ones need re-running.
- Exploring "what does PE think about SALT reforms?" as a research question.

## Arguments

`$ARGUMENTS` — a natural-language query. The command parses it into filters for `scripts/analyses_kb.py search`.

Flags:
- `--country {us|uk|ca}` — filter by jurisdiction
- `--state <code>` — filter by US state / UK country
- `--family <tag>` — filter by parameter-family tag (`salt`, `ctc`, `eitc`, `cdcc`, `standard-deduction`, etc.)
- `--verdict <verdict>` — filter by verdict (`PASS`, `PASS-WITH-NOTES`, `PASS-WITH-CORROBORATION`, `INVESTIGATE`, `structural`, `not-possible`, `deployed-model-lag`, `BLOCKED`)
- `--similar-to <archive-file>` — find analyses similar to an existing archive (jaccard over tags + jurisdiction)
- `--duplicates` — surface near-duplicate archived runs

## What this command does

Under the hood: `python3 scripts/analyses_kb.py search|similar|duplicates` with the parsed filter.

For each hit, surfaces:
- Date, verdict, title
- File path (relative to repo)
- Headline numbers if the frontmatter has them (year-1 cost, 10-year cost, poverty change, Gini change)
- Any GitHub issues opened by the analysis (`issues_opened` in frontmatter)

## Output

Ranked list of matching archived analyses. For each, a link to the file + a one-line summary. If `--duplicates`, pairs with jaccard scores.

## Related

- `/analyze-policy` — run a NEW analysis. This command is the "check first" step you should reflex to before running one.
- `scripts/analyses_kb.py` — the underlying CLI. This command is a thin wrapper so it appears in the slash-command catalog.
- `analyses/README.md` — canonical frontmatter schema.
