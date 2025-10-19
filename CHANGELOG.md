# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
