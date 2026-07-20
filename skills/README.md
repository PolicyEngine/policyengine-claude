# PolicyEngine skills

Portable `SKILL.md` knowledge for AI agents working on PolicyEngine. Rebuilt from
scratch in July 2026 around one principle: **skills carry only knowledge a frontier
model cannot derive** — current API shapes, pinned dataset names, org conventions,
and verified gotchas. Anything a strong model already knows (generic Python, React,
SEO, testing advice) does not belong here.

Every skill lives in a flat directory: `skills/<name>/SKILL.md`, with its category
declared in frontmatter `metadata.category`. Code examples marked `<!-- verify -->`
are executed by CI against the latest released `policyengine` stack
(`tests/test_skill_examples.py`); `<!-- verify: slow -->` marks population-scale
examples run at authoring time and on demand. `tests/test_no_stale_references.py`
lints the whole tree against the failure modes that rotted the previous catalog
(archived-repo dataset URIs, deleted APIs, phantom methods).

## Catalog

### Analysis

| Skill | What it carries |
|---|---|
| **policyengine** | The canonical Python interface: `pe.us/uk.calculate_household`, population `Simulation` + `economic_impact_analysis` + `calculate_budgetary_impact`, Populace datasets, regional analysis, reform formats, MicroSeries weighting discipline |
| **policyengine-prior-scores** | Published reform-score anchors (JCT/CBO/TPC/PE) and the scorekeepers registry, with comparability caveats |

### Domain knowledge

| Skill | What it carries |
|---|---|
| **policyengine-us** | US entities, program landscape, current-law (post-OBBBA) values, SNAP mechanics, parameter-tree map |
| **policyengine-uk** | UK entities (benunit), BHC/AHC poverty, reform APIs, private population data access |
| **policyengine-canada** | Household-only Canada calculations (no representative microdata) |
| **policyengine-healthcare** | Medicaid/ACA/CHIP modeling, including the health-benefits-excluded-from-net-income gotcha |

### Model development

| Skill | What it carries |
|---|---|
| **policyengine-model-development** | Country-model engineering with per-topic references: variables, parameters, periods and aggregation, vectorization, YAML tests, in-model reforms, style |

### Data

| Skill | What it carries |
|---|---|
| **policyengine-data** | The Populace stack: certified releases, dataset registry, local-area filtering philosophy, fit/calibrate/L0 concepts, where to file data work |
| **policyengine-calibration-diagnostics** | Deviation-signature → calibration-lever sensitivity registry |

### Apps

| Skill | What it carries |
|---|---|
| **policyengine-app** | Developing policyengine-app-v2 (policyengine.org) |
| **policyengine-tools** | Building standalone tools/dashboards: Next.js + Tailwind v4 + ui-kit spec, multizone, Modal backends, Vercel |
| **policyengine-design** | Design tokens, `@policyengine/ui-kit` consumption, chart styling, design-system migration |
| **policyengine-api** | The REST APIs: v1 production endpoints, api-v2 alpha status |

### Process

| Skill | What it carries |
|---|---|
| **policyengine-writing** | Editorial law: neutrality, quantitative language, sentence case |
| **policyengine-standards** | uv/bun, ruff, towncrier changelogs, CI gates, PR discipline |
| **policyengine-research-lookup** | Finding existing PolicyEngine research and proof points |
| **policyengine-user-guide** | Using the policyengine.org web app |
| **policyengine-content** | Social image/copy generation for posts |
| **policyengine-github-agent** | GitHub bot operating rules |
| **policyengine-plugin-maintenance** | Maintaining this repo: structure, bundles, wrapper build, tests |

### Workflows (shared canonical definitions)

Each workflow has one canonical behavioral definition at
`skills/<name>/references/workflow.md` — phases, roles, gates, artifact contracts. The
skill's `SKILL.md` is the cross-client launcher: Claude Code gives a skill precedence
over a same-named command, so the skill is the entry point on both surfaces.
`references/claude-launcher.md` carries the Claude-only role/agent mapping, and the
matching file in `targets/claude/commands/` is a compatibility stub for older Claude
Code versions. Edit the canonical file, never a launcher, to change behavior.

| Skill | What it carries |
|---|---|
| **encode-policy-v2** | Implement a new state benefit program end to end |
| **review-program** | Review a PolicyEngine PR, including PDF-cited values |
| **fix-pr** | Apply review findings to a PR |

## Authoring rules

1. Verify every API claim by executing it or reading the live source; never write
   from memory. The pre-rebuild catalog taught a household API that had been deleted
   upstream and quickstarts that crashed — they shipped for months because nothing
   executed them. Verification cuts both ways: check claims against the *ecosystem's
   current release*, not just a locally-installed (possibly stale) version — this
   rebuild briefly misjudged a real recharts 3.8 prop as fabricated by checking a
   lockfile-pinned 3.7 install.
2. Only non-derivable content. If a paragraph would be true of any project, cut it.
3. One home per fact; cross-reference sibling skills instead of duplicating.
4. Mark runnable examples with `<!-- verify -->` (fast, asserted, household-tier)
   or `<!-- verify: slow -->` (population-tier). Never mark a block you haven't run.
5. Frontmatter: `name` (= directory name), `description` (triggers included,
   ≤1024 chars — Codex hard limit), `metadata.category`.
6. Deliberate references to superseded things (history notes) take a
   `<!-- stale-ok -->` marker on the preceding line to pass the anti-rot lint.
