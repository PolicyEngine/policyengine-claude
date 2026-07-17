---
name: policyengine-plugin-maintenance
description: |
  Maintaining the policyengine-skills source repo and its generated policyengine-claude wrapper —
  adding or editing skills, bundles, and the Claude/Codex targets, and keeping the verification
  harness green. For maintaining the catalog, not for using PolicyEngine.
  Triggers: "update plugin", "add a skill", "edit a bundle", "fix skill routing", "wrong skill
  loaded", "rebuild the wrapper", "plugin maintenance", "policyengine-skills",
  "policyengine-claude", "stale reference test", "verify example failing", "skill frontmatter".
metadata:
  category: process
---

# Maintaining the PolicyEngine skills catalog

> This skill is for maintaining the skills SOURCE repo and the Claude wrapper — not for using
> PolicyEngine.

## Repository shape (rebuilt)

Flat, category-tagged skills compiled into install profiles, then rendered into per-target
wrappers.

- `skills/<name>/SKILL.md` — one flat directory per skill (no `domain-knowledge/`,
  `tools-and-apis/` nesting). Frontmatter is `name` (equal to the dir name), a `description:`
  block that carries trigger phrases and stays under 1024 characters (hard Codex limit), and
  `metadata.category`. Supporting files sit beside SKILL.md — e.g.
  `skills/policyengine-content/templates/social-image.html`.
- `bundles/*.json` — install profiles. Each lists the skills, commands, and agents it ships by
  path. `complete.json` is the recommended everything bundle; the rest are scoped (essential,
  country-models, analysis-tools, app-development, api-development, data-science,
  dashboard-builder, content).
- `targets/claude/` — the Claude wrapper source: `marketplace.template.json`, `agents/`,
  `commands/`, `hooks/hooks.json`, `lessons/`. `targets/codex/` is the Codex target.
- `scripts/build_claude_wrapper.py` — compiles the bundles and marketplace template into the
  generated `policyengine-claude` marketplace, validating that every referenced skill, command,
  and agent path exists (and normalizing plugin entries for the current Claude Code schema).
- `presets/`, `analyses/`, `dashboard/`, `mcp/` — analysis infrastructure consumed by the
  commands and agents.

## Build and publish

CI (`.github/workflows/test.yml`) runs `uv run pytest` and smoke-builds the wrapper on every PR.
On merge to main, `sync-claude.yml` builds the wrapper and rsyncs it into
`PolicyEngine/policyengine-claude` — the marketplace repo users actually install — committing as
the sync bot. Build and test locally with:

```bash
uv run pytest                       # full lint + unit suite
python3 scripts/build_claude_wrapper.py --source-root . --output-root build/policyengine-claude
```

## The verification harness (do not defeat it)

The rebuild exists because the old catalog shipped API claims nothing had ever executed —
some deleted upstream, some never real. Two tests hold the line; treat them as the
definition of "done", not as obstacles.

### Executable examples — `tests/test_skill_examples.py`

A ```python fence whose immediately preceding non-empty line is exactly the verify marker
`<!-- verify -->` is a **fast** example: self-contained, household-tier, and it must assert
something. The harness executes every such block in a subprocess (300s timeout) and fails if it
exits non-zero. The `<!-- verify: slow -->` variant marks population-scale examples (multi-GB
data, tens of GB of RAM); those run only when `PE_SKILLS_RUN_SLOW=1` is set — at authoring time
and on demand, not in PR CI. The module skips entirely when `policyengine` is not installed, so
it runs in a dedicated CI job that installs the stack (the default job passes
`--ignore=tests/test_skill_examples.py`). A guard test also fails if zero fast examples are found,
so the harness cannot silently go blind.

**Discipline: never place a verify marker on a block you have not actually run successfully.** A
green marker on an unrun block is precisely the failure the rebuild removed. Run it in a
policyengine venv first, watch it assert, then add the marker.

### Anti-rot lint — `tests/test_no_stale_references.py`

Scans `skills/`, `targets/`, `docs/`, `bundles/`, and `presets/` (`.md`, `.json`, `.yaml`,
`.yml`, `.py`, `.sh`, `.html`) for a table of regexes that each name a dead API, path, dataset,
or package the pre-rebuild catalog leaked: the archived us-data Hugging Face URI, per-state and
per-district H5 filenames, the retired enhanced-CPS/FRS dataset names, the deprecated per-entry
changelog YAML, v1 app source paths, legacy UI libraries app-v2 no longer uses, deleted
household-impact functions from policyengine.py, the old design-system package as an install
target, and non-uv pip installs. The authoritative pattern-and-reason list
lives in the test's `FORBIDDEN` table — read it there rather than duplicating it. Any hit fails
CI. A line opts out when the marker `<!-- stale-ok -->` sits on it or on the line directly above,
reserved for a deliberate "this is the superseded thing" history or migration note.

### The rule behind both

**Every code or API claim must be verified against live code before you commit it** — run it in a
policyengine venv, or cite the exact mirror source file you read. If you cannot verify a claim,
delete it. A skill that is precise per token beats one that is comprehensive and wrong.

## How skill matching works

1. Each `SKILL.md` frontmatter `description` is surfaced to the model at session start.
2. Order matters: skills listed earlier in a bundle appear earlier in the system prompt and get
   matched preferentially. List common-query skills before niche ones in the bundle.
3. The model invokes a skill by matching the query against its description, and may skip a skill
   if it thinks it can answer without it — so descriptions must carry explicit trigger phrases.

### Writing a description that routes correctly

- Lead with when to load it; include concrete trigger phrases users actually type.
- To keep a skill from loading on the wrong query, add an explicit "NOT for: … (use <skill>)"
  clause — the flagship `policyengine` skill does this to hand off to model-development and api.
- Cross-reference siblings by name instead of duplicating their content.
- Keep the whole description under 1024 characters.

## Making local edits take effect

Claude Code caches plugins and does not pick up edits to cache files directly. After changing
source, rebuild the wrapper, clear the cache, and start a new session:

```bash
python3 scripts/build_claude_wrapper.py --source-root . --output-root build/policyengine-claude
rm -rf ~/.claude/plugins/cache/policyengine-claude
```

To publish for everyone: open a PR to `policyengine-skills` main; on merge, the sync workflow
pushes the wrapper to `policyengine-claude`; users clear their cache and restart to pick it up.

## Updating examples (e.g. annual year bump)

Because examples are executable and CI-checked, update them by editing and re-running, not by
blind find/replace. When you bump the analysis year, or a law change moves a baseline (e.g.
post-OBBBA CTC), re-run each affected verify block in a policyengine venv and confirm the new
asserted value before committing. Never rewrite a marked block and leave it unrun.

## Related skills

- **policyengine-standards** — the uv/ruff/bun/towncrier/CI conventions the repo's own code follows.
- **policyengine-writing** — sentence case, neutrality, and density the skill prose follows.
