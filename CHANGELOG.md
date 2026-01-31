# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.4.1] - 2026-01-31

### Changed
- **pr-pusher, rules-engineer, ci-fixer** - Use `uv run black` instead of bare `black` command to ensure version matches uv.lock and CI
- **Formatting guidance** - Added explicit guidance about using `uv sync --extra dev` before formatting to ensure correct tool versions

## [3.4.0] - 2026-01-31

### Added
- **SessionStart hook** - Auto-detects PolicyEngine repos and injects instructions to use specialized plugin agents (rules-engineer, ci-fixer, pr-pusher, etc.) instead of general-purpose agents

## [3.3.3] - 2025-12-23

### Added
- **Parameter formatting validation** - implementation-validator now checks description, label, and values formatting
- **Skill validation sections** - All 13 agents now have "Before Completing: Validate Against Skills" reminder
- **Formatting issues in review-pr** - Review report now includes parameter and variable formatting issues

### Changed
- **implementation-validator report** - Added Parameter Formatting Issues table section
- **rules-engineer** - Now references policyengine-code-style-skill patterns in validation step

## [3.3.2] - 2025-12-23

### Added
- **All agents to marketplace.json** - Added 17 agents to `country-models` plugin and 25 agents to `complete` plugin (Issue #36)
- **`--local` flag for review-pr** - Skip GitHub posting with `--local` flag
- **`--local` flag for fix-pr** - Skip GitHub pushing/posting with `--local` flag
- **Interactive prompt for review-pr** - Asks user before posting to GitHub (unless `--local` used)
- **Interactive prompt for fix-pr** - Asks user before pushing to GitHub (unless `--local` used)

### Changed
- **review-pr asks upfront** - Posting mode prompt moved to Step 1 (before review starts)
- **fix-pr asks upfront** - Posting mode prompt moved to Step 1 (before fixes start)

## [3.3.1] - 2025-12-18

### Changed
- **README updates** - Updated all README files to reflect v3.3.0 changes
- **Agent count** - Updated from 22 to 21 (naming-coordinator deleted)
- **Skill count** - Updated from 14 to 24 (accurate count)
- **Plugin tables** - Updated agent and skill counts in all plugin descriptions

### Added
- **v3.3.0 version history** - Added to main README
- **New skills in skills/README** - policyengine-code-organization-skill, policyengine-simulation-mechanics-skill

### Removed
- **naming-coordinator references** - Removed from all READMEs
- **Submodule instructions** - Replaced with plugin installation instructions

## [3.3.0] - 2025-12-18

### Changed
- **review-pr command redesigned** - Simplified from 6 phases to 4, reduced from 6 agents to 4, added priority-based output (Critical/Should/Suggestions)
- **fix-pr command rewritten** - Now 5 phases with dependency-order fixing (parameters → variables → tests → format), clear issue-to-agent mapping
- **encode-policy continuous regulatory verification** - Added 3 checkpoints: after Phase 2 (specification review), after 3A (parameter verification), after 3C (logic review)
- **reference-validator redesigned** - Now 5-phase workflow with skills, detailed reference format rules, source priority hierarchy
- **Phase 7 simplified** - Now 'Final Review & PR Description' since regulatory issues caught earlier via checkpoints

### Added
- **Regulatory Checkpoint 1** - Verify specification is complete before development
- **Regulatory Checkpoint 2** - Verify parameter values match sources before variables
- **Regulatory Checkpoint 3** - Verify implementation logic matches regulations after variables
- **Reference clickability rule** - When clicking link, user must see the parameter value
- **Detailed section requirement** - References must include full subsection (e.g., `42 USC 8624(b)(2)(B)` not just `42 USC 8624`)
- **Source priority hierarchy** - Official government sources required; nonprofit/news only as last resort
- **Issue-to-agent mapping** in fix-pr - Clear table of which agent fixes which issue type
- **Dependency-order fixing** - Fix parameters before variables before tests
- **policyengine-code-organization-skill** - New skill for folder structure and naming conventions (extracted from naming-coordinator)

### Removed
- **Duplicate implementation-validator calls** in review-pr (was called in Steps 1 and 3)
- **documentation-enricher from review-pr** - Had Edit tools, review-pr is read-only
- **Hardcoded 'MaxGhenis' username** in review-pr - Now uses dynamic `gh api user`
- **naming-coordinator agent** - Converted to policyengine-code-organization-skill

### Renamed
- **policyengine-implementation-patterns-skill** → **policyengine-variable-patterns-skill**

## [3.2.4] - 2025-12-18

### Changed
- **Renamed tanf-program-reviewer to program-reviewer** - Generalized for any government program, not just TANF
- **review-pr command** - Added Step 6: Regulatory Review using program-reviewer
- **encode-policy Phase 4 restructured** - Split into 4A (parameter-architect) then 4B (test-creator + rules-engineer in parallel)
- **encode-policy Phase 5 simplified** - Just changelog, `make format`, push (testing moved to Phase 6)
- **encode-policy Phase 6 restructured** - Step 6A (implementation-validator) → Step 6B (ci-fixer runs tests locally)
- **ci-fixer runs tests locally** - No longer waits for GitHub CI (30+ min), uses `policyengine-core test` directly
- **implementation-validator check order** - Now checks Parameters → Variables → Tests (foundation first)
- **issue-manager hybrid approach** - Stops and asks user if existing issue/PR found; proceeds autonomously if none found
- **document-collector PDF handling** - Notes PDFs in sources.md for future reference, doesn't block workflow

### Added
- **Bracket-style age eligibility parameters** - Single file with thresholds instead of separate min/max files
- **PDF page number clarification** - `#page=XX` is FILE position (not printed page number)
- **State-specific program naming** - TEA (Arkansas), OWF (Ohio), CalWORKs (California), etc.
- **State-specific terminology** - Need standard vs payment standard variations
- **"Legal Code is Source of Truth" principle** - Law comes first, patterns are tools
- **`adds` vs `add()` enforcement** - Use `adds = [...]` for pure sums, `add()` for sum + operations, never manual `a + b`
- **`add() > 0` pattern** - Instead of `spm_unit.members` + `spm_unit.any()`
- **"Break out complex expressions"** - Named variables for clarity (e.g., `benefit_amount = max_(...)`)
- **Person vs Group entity verification** - Check if amounts apply per-person or per-group
- **Reference format rules** - Use tuple `()` not list `[]`, no `documentation` field
- **Test coverage rule** - Variables with `formula` need tests; `adds` variables don't
- **Test input mismatch guidance** - Fix test inputs to match federal baseline, don't create wrapper variables

## [3.1.4] - 2025-12-09

### Added
- **Error handling framework** in encode-policy - Error categories (recoverable, delegation, blocking), phase-specific handling, escalation path
- **Skill loading** to test-creator (added `policyengine-implementation-patterns-skill`) and pr-pusher (added `policyengine-standards-skill`)

### Changed
- **ci-fixer workflow** - Updated to use simple branch naming (`<state-code>-<program>`) instead of old `integration/<program>-<date>` pattern
- **integration-agent** - Added note clarifying it's for advanced workflows only (standard workflow uses single branch)
- **parameter-architect templates** - Now points to policyengine-parameter-patterns-skill Section 2.2 instead of having separate templates

### Fixed
- **Branch naming consistency** - ci-fixer.md now uses same `<state-code>-<program>` pattern as issue-manager and encode-policy
- Removed obsolete merge steps from ci-fixer (agents now work on same branch, no merging needed)

## [3.1.3] - 2025-12-09

### Added
- **Skill loading instructions** for all 13 country-models agents - agents now explicitly load required skills before starting work
- **Balanced code comments** guidance in rules-engineer - regulation references, step numbers, non-obvious logic (aim for 2-4 comments per formula)
- **State program naming** guidance in naming-coordinator - use state's actual program names (e.g., `nc_workfirst` not `nc_tanf`, `oh_owf` not `oh_tanf`)
- **Derived values guidance** in document-collector and parameter-architect - store rates not dollar amounts when value is percentage of FPL/SMI, must have legal proof
- **Variable reference format** in rules-engineer - PDF links must include `#page=XX`

### Changed
- **Unified commit strategy** - document-collector, test-creator, and rules-engineer now create files only; pr-pusher handles all commits
- **Cross-fork PR workflow** - issue-manager, create-pr command, and policyengine-standards-skill now use `--repo PolicyEngine/policyengine-us` for cross-fork PRs
- **Simple branch naming** - issue-manager now uses `<state-code>-<program>` (e.g., `or-tanf`) instead of `integration/<program>-<date>`
- **Single folder storage** - document-collector now saves all documentation to `sources/working_references.md` only (removed dual storage)
- **Reference format** in policyengine-parameter-patterns-skill - title must include full section path with all subsections, PDF links must include `#page=XX`

### Fixed
- encode-policy command now references correct folder path (`sources/working_references.md`) and branch naming convention
- Clarified that unused `parameters` in formulas is OK if there's state-specific logic (not a sign of unnecessary wrapper)

## [3.1.2] - 2025-12-08

### Added
- Added UK legislation reference guidance to `policyengine-uk-skill`:
  - Documentation on using legislation.gov.uk for parameter references
  - Key legislation sources for UK benefits (Universal Credit Regulations 2013, Welfare Reform Act 2012)
  - Universal Credit parameter reference patterns (standard allowance, work capability, etc.)
  - Annual uprating order references for benefit amounts
  - Step-by-step guide for finding correct legislation sections

## [3.1.1] - 2025-11-25

### Fixed
- Added `Skill` tool to 16 agents that reference skills but couldn't invoke them:
  - **Country-models agents (15):** rules-engineer, program-reviewer, ci-fixer, test-creator, parameter-architect, implementation-validator, edge-case-generator, documentation-enricher, cross-program-validator, document-collector, performance-optimizer, naming-coordinator, integration-agent, issue-manager, pr-pusher
  - **Other agents (1):** reference-validator
- Agents can now dynamically load PolicyEngine skills (policyengine-implementation-patterns-skill, policyengine-parameter-patterns-skill, etc.) instead of just referencing them in documentation

## [3.1.0] - 2025-11-25

### Changed
- Upgraded all 15 country-models agents from `model: sonnet` to `model: opus` (Opus 4.5)

## [3.0.1] - 2025-11-25

### Fixed
- Fix duplicate agent registration by removing explicit `agents` arrays from country-models and complete plugins
- Claude Code auto-discovers agents from the `agents/` directory, so listing them explicitly caused duplicates

## [3.0.0] - 2025-11-25

### Changed
- Simplified encode-policy workflow from 9 phases to 8 (removed branch merging phase)
- All agents now work on same branch (no git worktrees needed)
- Keep PR as draft (don't auto-mark ready)
- Working files now saved to `sources/` folder for reference
- Renamed `document_collector.md` to `document-collector.md` for consistent naming
- Added shared/ agents and workflow.md to marketplace.json

### Added
- Added all 7 technical pattern skills to ci-fixer and program-reviewer agents
- Added minimal comments guidance to rules-engineer and code-style-skill

### Removed
- Removed `documentation` field from templates (use `reference` URL instead)

## [2.0.0] - 2025-10-18

### Added
- **New slash command:**
  - `/create-pr` - Create PR as draft, poll CI status, mark ready when passed (solves "I'll check back later" problem)
- **10 new skills** for comprehensive PolicyEngine knowledge base:
  - `policyengine-user-guide-skill` - Using PolicyEngine web apps for all users
  - `policyengine-python-client-skill` - Programmatic access via Python/API
  - `policyengine-core-skill` - Core simulation engine architecture and patterns
  - `policyengine-api-skill` - Flask API development and integration patterns (v1)
  - `policyengine-app-skill` - React app development and component patterns (v1)
  - `microdf-skill` - Weighted DataFrames for inequality and poverty analysis
  - `microimpute-skill` - ML-based variable imputation (replaces synthimpute)
  - `microcalibrate-skill` - Survey weight calibration with L0 regularization
  - `l0-skill` - PyTorch L0 regularization for sparsification
  - `policyengine-design-skill` - Visual identity, colors, fonts, logos (covers v1 and v2 transition)
- **2 new plugins:**
  - `essential` - For all PolicyEngine users (user-guide, us, writing skills)
  - `data-science` - For data package contributors (microdf, microimpute, microcalibrate, l0, us, design, standards, writing)

### Changed
- **Multi-audience approach** - All skills now organized with "For Users", "For Analysts", "For Contributors" sections
- **Enhanced existing skills:**
  - `policyengine-us-skill` - Added user and analyst sections explaining what's modeled and how to use
  - `policyengine-analysis-skill` - Added user section explaining how analysis works
  - `policyengine-standards-skill` - Added TDD section, PR workflow guidance, CI waiting pattern (teaches Claude to use /create-pr command)
- **Documentation pointer pattern** - Skills now point to current repo code instead of duplicating it
- **Marketplace reorganization:**
  - Renamed/reorganized plugins for clarity (country-models, api-development, app-development, analysis-tools, data-science, complete)
  - Updated descriptions to reflect multi-audience purpose
  - Version bump to 2.0.0 across all plugins
- **README rewrite** - Comprehensive documentation of multi-repo, multi-audience approach

### Deprecated
- **synthimpute** - Archived, replaced by microimpute + microcalibrate
- References to synthimpute removed from ecosystem documentation

### Notes
- **v1/v2 transition:** Skills document both API v1 (production) and API v2 (development), and app v1 (production) and app v2 (development)
- **Complete ecosystem map:** Added ECOSYSTEM.md documenting full dependency graph
- **Data pipeline:** Complete coverage of data enhancement workflow (L0 → microimpute → microcalibrate → policyengine-us-data)

### Breaking Changes
- Plugin structure changed - users need to reinstall from marketplace
- Some plugin names changed (e.g., skills separated by audience)
- Marketplace version bumped to 2.0.0
- Data-science plugin now includes 8 skills (was 4)

## [1.0.0] - 2025-10-18

### Added
- Initial release of PolicyEngine Claude plugin marketplace
- **Agents (18 total):**
  - Country models: 15 agents for multi-agent workflow (document collector, test creator, rules engineer, reviewers, validators, optimizers, CI fixer)
  - API development: 1 agent for Flask/backend review
  - App development: 1 agent for React/frontend review
  - Shared: 2 validation agents for cross-repo use
- **Slash Commands (3 total):**
  - `/encode-policy` - Orchestrate full implementation workflow
  - `/review-pr` - Comprehensive PR review
  - `/fix-pr` - Automated PR fixes
- **Skills (3 total):**
  - `policyengine-us-skill` - PolicyEngine-US patterns and simulation workflows
  - `policyengine-analysis-skill` - Analysis patterns for research repositories
  - `policyengine-standards-skill` - Coding standards and CI requirements
- **Plugin Distribution:**
  - `country-models` - For country package development
  - `api-development` - For API development
  - `app-development` - For app development
  - `analysis-tools` - For analysis repositories
  - `complete` - Everything included
- Plugin marketplace configuration (`.claude-plugin/marketplace.json`)
- Comprehensive README with installation and usage instructions
- MIT License
- Migration guide from submodule to plugin system

### Changed
- Migrated from git submodule approach to Claude Code plugin system
- Unified agents from `PolicyEngine/.claude` with skills from `policyengine-skills`
- Organized agents into category subdirectories (country-models, api, app, shared)

[1.0.0]: https://github.com/PolicyEngine/policyengine-claude/releases/tag/v1.0.0
