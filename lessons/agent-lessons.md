# Agent Lessons Learned

Accumulated from /backdate-program runs across all contributors.
Loaded by implementation agents on future runs.

## New Lessons from KY K-TAP (2026-02-26)

### PARAMETER
- Never use value=0 as a sentinel to mean "not in effect"; always create a separate boolean `_in_effect` parameter with `values: {date: true/false}` entries.
- If a parameter value is unchanged across eras, keep only one entry at the earliest applicable date; do not duplicate the same value at later dates.

### REFERENCE
- Verify subsection citations match the actual content described; adjacent subsections often cover different provisions (e.g., child support vs. earned income disregard).

### TEST
- Always check the formula's actual input variable names before writing tests; use the variable the formula reads (e.g., `employment_income_before_lsr`), not a similar-sounding upstream variable.
- TANF/cash assistance test households must include at least one child; single adults without children are demographically ineligible.

### FORMULA
- When a provision changes form across eras (e.g., flat+percentage to percentage-only), use `if p.provision_in_effect:` branching with a boolean parameter — do not collapse into a "unified" formula that uses 0 as a sentinel value.
- Period-level boolean switches use Python `if p.flag:` (scalar per-period); entity-level conditions use `where()` (vectorized) — never mix these up.

### WORKFLOW
- The review-fix loop must continue until 0 critical issues are found OR the max round limit is reached; never stop early when criticals remain, even if other severity levels are clean.
- When an implementation agent creates a correct pattern (e.g., an `_in_effect` boolean), do not instruct them to remove it in favor of a "simpler" approach that introduces an anti-pattern; trust domain-specific correctness over superficial simplicity.
# New Lessons from Indiana TANF Backdating Session

## PARAMETER
- Always verify the full range of dimension values (e.g., family sizes 1–N) against source tables; never trust a summarizer or consolidator that truncates a table early — go back to the PDF.
- When backdating `max_unit_size` or similar dimension-cap parameters, verify they match the largest dimension present in the source tables for that era; do not assume the cap changed just because the program reformed.

## REFERENCE
- PDF text extraction can misidentify state or program names from headers, footers, or watermarks; always verify the actual data content of a PDF rather than flagging it based on extracted metadata strings alone.
