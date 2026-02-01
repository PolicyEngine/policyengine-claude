# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.6.2] - 2026-02-01

### Fixed

- Fix SessionStart hook schema - wrap prompt in nested `hooks` array to match expected structure

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



[3.6.2]: https://github.com/PolicyEngine/policyengine-claude/compare/3.6.1...3.6.2
[3.6.1]: https://github.com/PolicyEngine/policyengine-claude/compare/3.5.0...3.6.1
[3.5.0]: https://github.com/PolicyEngine/policyengine-claude/compare/3.4.1...3.5.0
[3.4.1]: https://github.com/PolicyEngine/policyengine-claude/compare/1.0.0...3.4.1

