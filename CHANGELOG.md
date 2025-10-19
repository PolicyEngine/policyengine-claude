# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
