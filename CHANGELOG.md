# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.13.0] - 2026-03-01

### Added

- Add changelog enforcement and auto version bumping — fragment-based changelog entries in `changelog.d/`, CI check that blocks PRs without fragments, and automatic version bump + CHANGELOG.md generation on merge to main

## [3.11.0] - 2026-02-26

### Added

- `/review-program` command — consolidated PR review combining code validation + PDF audit in one pass; works for any PR type (state programs, federal parameters, infrastructure, API, frontend)
- `/backdate-program` command — multi-agent orchestration for backdating state program parameters with research, reference/formula audit, implementation, and built-in review phases
- `--600dpi` flag for both commands to handle scanned docs and dense tables
- `--local-diff` flag for `/review-program` to review unpushed local work (reads `git diff` instead of `gh pr diff`)
- `--skip-pdf` flag for `/review-program` to skip PDF acquisition on infrastructure/refactoring PRs
- Two-stage mismatch verification in `/review-program` Phase 5: code-path tracing (Step 5C) filters false positives before 600 DPI visual verification (Step 5D)
- Self-learning lessons mechanism in `/backdate-program` Phase 8: session checklist → persistent local lessons → PR to plugin repo (`lessons/agent-lessons.md`)
- `in_effect` and `regional_in_effect` boolean toggle patterns added to parameter-patterns and variable-patterns skills (with CT TFA production code examples)
- Implementation agents (parameter-architect, rules-engineer) now load lessons files on startup to prevent known mistakes
- Write tool added to `reference-validator` and `program-reviewer` agents
- Edit tool added to `edge-case-generator` agent
- `/tmp` cleanup at start of both commands to prevent stale data from previous runs

### Changed

- `/backdate-program` Phase 6 now invokes `/review-program --local --full` instead of separate `/review-pr` + `/audit-state-tax`
- `/backdate-program` Phase 5 now pushes to remote before Phase 6 review-fix loop
- `/backdate-program` Phase 8C uses temporary clone instead of modifying plugin install directory
- `/review-program` scope-aware agent selection: skips regulatory/reference validators for non-program PRs

## [3.9.1] - 2026-02-18

### Added

- Add parameter structure transition pattern (flat to bracket) to parameter-patterns and variable-patterns skills
- Add new bracket pattern using `.inf` for adding brackets to existing scales without breaking prior years

## [3.7.0] - 2026-02-16 17:53:45

### Added

- /audit-seo command for cross-repo SEO auditing with 4 specialist agents
- seo-meta-checker agent for meta tags, OG tags, Twitter cards, and canonical URLs
- seo-crawlability-checker agent for robots.txt, sitemap, routing, SSR, and hosting
- seo-performance-checker agent for bundle sizes, code splitting, fonts, and images
- seo-content-checker agent for heading hierarchy, semantic HTML, and accessibility
- seo-checklist-skill with SEO first principles for PolicyEngine web apps

## [3.6.1] - 2026-02-01 13:43:05

### Added

- Add reference-validator to encode-policy Phase 5 for parameter reference validation
- Add absolute_error_margin guidance to testing patterns skill
- Add AskUserQuestion prompts to review-pr and fix-pr commands for PR selection

## [3.5.0] - 2026-01-31 11:55:22

### Added

- Add policyengine-research-lookup-skill for finding blog posts, proof points, and published analyses
- Register research-lookup skill in analysis-tools and complete plugins
- Add policyengine-api-v2-skill for working with the next-generation microservices API
- Content generation plugin for creating social images and social posts from blog articles

## [3.4.1] - 2026-01-31 00:00:00

### Added

- SessionStart hook that auto-detects PolicyEngine repos and injects instructions to use specialized plugin agents

### Changed

- pr-pusher, rules-engineer, ci-fixer now use `uv run black` for consistent formatting with CI
- Added explicit guidance about using `uv sync --extra dev` before formatting

## [1.0.0] - 2025-10-18 00:00:00

### Added

- Initial plugin marketplace release with 18 agents, 3 commands, 3 skills



[3.13.0]: https://github.com/PolicyEngine/policyengine-claude/compare/3.11.0...3.13.0
[3.11.0]: https://github.com/PolicyEngine/policyengine-claude/compare/3.10.0...3.11.0
[3.9.1]: https://github.com/PolicyEngine/policyengine-claude/compare/3.7.0...3.9.1
[3.7.0]: https://github.com/PolicyEngine/policyengine-claude/compare/3.6.1...3.7.0
[3.6.1]: https://github.com/PolicyEngine/policyengine-claude/compare/3.5.0...3.6.1
[3.5.0]: https://github.com/PolicyEngine/policyengine-claude/compare/3.4.1...3.5.0
[3.4.1]: https://github.com/PolicyEngine/policyengine-claude/compare/1.0.0...3.4.1

