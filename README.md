# PolicyEngine Claude

Official Claude Code plugin marketplace for PolicyEngine development - agents, commands, and skills for tax and benefit microsimulation.

## Overview

This plugin provides a complete development toolkit for PolicyEngine repositories, including:

- **18 Specialized Agents** - Automated workflows for implementing, testing, and reviewing tax/benefit rules
- **3 Slash Commands** - Multi-agent orchestration workflows
- **3 Skills** - Reference documentation and best practices

## Quick Start

### Installation

```bash
# Add PolicyEngine marketplace
/plugin marketplace add PolicyEngine/policyengine-claude

# For country model development (policyengine-us, policyengine-uk, etc.)
/plugin install country-models@policyengine-claude

# For API development (policyengine-api)
/plugin install api-development@policyengine-claude

# For App development (policyengine-app)
/plugin install app-development@policyengine-claude

# For analysis repositories (crfb-tob-impacts, newsletters, etc.)
/plugin install analysis-tools@policyengine-claude

# Or install everything
/plugin install complete@policyengine-claude
```

### Auto-Install for Teams

Add to your project's `.claude/settings.json`:

```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["country-models@policyengine-claude"]
  }
}
```

When team members trust the repository, the plugin auto-installs!

## What's Included

### 🤖 Agents (18 Total)

#### Country Models (15 agents)

For developing tax and benefit rules in `policyengine-us`, `policyengine-uk`, `policyengine-canada`, etc.

**Multi-Agent Workflow:**
- `document_collector` - Gathers authoritative sources (regulations, state plans)
- `test-creator` - Creates tests from documentation (isolated from implementation)
- `rules-engineer` - Implements variables and parameters (isolated from tests)
- `parameter-architect` - Designs parameter structures
- `rules-reviewer` - Reviews implementation against documentation

**Validation & Quality:**
- `policy-domain-validator` - Validates federal/state separation, naming conventions
- `reference-validator` - Checks citations and documentation
- `cross-program-validator` - Ensures consistency across programs
- `implementation-validator` - Verifies zero hard-coded values
- `performance-optimizer` - Identifies vectorization opportunities
- `documentation-enricher` - Enhances code documentation

**CI & Integration:**
- `ci-fixer` - Fixes continuous integration failures
- `isolation-setup` - Sets up git worktrees for isolated development
- `isolation-enforcement` - Ensures test/implementation isolation
- `edge-case-generator` - Creates comprehensive test cases

#### API Development (1 agent)

For `policyengine-api` (Flask backend):
- `api-reviewer` - Reviews API implementations for performance, security, REST practices

#### App Development (1 agent)

For `policyengine-app` (React frontend):
- `app-reviewer` - Reviews React code for component quality, performance, UX

#### Shared (2 agents)

- `policy-domain-validator` - Domain validation across all repos
- `reference-validator` - Reference checking across all repos

### 🎯 Slash Commands (3 Total)

**`/encode-policy <program-name>`**
- Orchestrates complete multi-agent workflow to implement new government programs
- Coordinates: document collection → parallel test/implementation → validation → PR creation
- Example: `/encode-policy Idaho LIHEAP`

**`/review-pr [pr-number]`**
- Comprehensive PR review using validation agents (read-only)
- Posts findings to GitHub without making changes
- Example: `/review-pr 123` or `/review-pr` (uses current branch)

**`/fix-pr [pr-number]`**
- Fixes issues found in PR review
- Applies corrections and pushes updates
- Example: `/fix-pr 123`

### 📚 Skills (3 Total)

**`policyengine-us-skill`**
- Situation creation patterns (single, married, families)
- Common variables reference (income, deductions, benefits, taxes)
- Using axes for parameter sweeps
- Policy reform definitions
- Helper functions and examples

**`policyengine-analysis-skill`**
- Impact analysis patterns (distributional, case studies)
- Plotly visualizations with PolicyEngine branding
- Streamlit dashboard templates
- Jupyter notebook best practices
- Reform analysis templates

**`policyengine-standards-skill`**
- Python standards (Black, 79-char, `uv run`)
- React standards (Prettier + ESLint)
- Changelog management (`changelog_entry.yaml`)
- Git workflow (no forks, issue references)
- Common AI pitfalls

## Available Plugins

### 1. `country-models` (Recommended for Country Repos)

**Use in:** `policyengine-us`, `policyengine-uk`, `policyengine-canada`, `policyengine-il`, `policyengine-ng`

**Includes:**
- 15 country model agents
- 3 slash commands (`/encode-policy`, `/review-pr`, `/fix-pr`)
- 2 skills (`policyengine-us-skill`, `policyengine-standards-skill`)

**Example workflow:**
```bash
# Implement new program
/encode-policy California EITC

# Review existing PR
/review-pr 456

# Fix issues
/fix-pr 456
```

### 2. `api-development`

**Use in:** `policyengine-api`

**Includes:**
- 1 API reviewer agent
- 1 skill (`policyengine-standards-skill`)

### 3. `app-development`

**Use in:** `policyengine-app`

**Includes:**
- 1 App reviewer agent
- 1 skill (`policyengine-standards-skill`)

### 4. `analysis-tools`

**Use in:** `crfb-tob-impacts`, `newsletters`, `givecalc`, dashboards, analysis notebooks

**Includes:**
- 3 skills (all: US patterns, analysis patterns, coding standards)
- No agents (analysis repos use skills as reference)

**Example usage:**
```
You: "Create a Streamlit dashboard analyzing CTC reform impacts"

Claude: [Uses policyengine-analysis-skill for dashboard patterns]
        [Uses policyengine-us-skill for simulation setup]
        [Uses policyengine-standards-skill for code quality]
```

### 5. `complete`

**Use for:** Full PolicyEngine development across all repo types

**Includes:** Everything (all agents, commands, skills)

## How It Works

### Three-Layer Architecture

1. **Skills (Knowledge Layer)** - Reference documentation, automatically loaded
2. **Agents (Execution Layer)** - Specialized workers, explicitly invoked
3. **Commands (Orchestration Layer)** - Multi-agent workflows, user-invoked

### Example: Implementing a New Program

```bash
# User runs command
/encode-policy Massachusetts SNAP

# Command orchestrates agents:
1. @document_collector gathers MA SNAP regulations
2. @test-creator writes tests (isolated)
3. @rules-engineer implements rules (isolated)
4. @policy-domain-validator validates implementation
5. @ci-fixer fixes any CI issues
6. Creates PR and posts to GitHub

# Agents reference skills:
- rules-engineer uses policyengine-us-skill for patterns
- All agents use policyengine-standards-skill for code quality
```

## Repository-Specific Usage

### Country Models (policyengine-us, policyengine-uk, etc.)

```bash
# Install plugin
/plugin install country-models@policyengine-claude

# Implement new program
/encode-policy [program-name]

# Review PR
/review-pr [pr-number]

# Fix PR issues
/fix-pr [pr-number]
```

### Analysis Repos (crfb-tob-impacts, newsletters, etc.)

```bash
# Install plugin
/plugin install analysis-tools@policyengine-claude

# Claude auto-uses skills when you ask:
"Create a policy impact analysis comparing baseline vs reform"
"Build a Streamlit dashboard for state-by-state comparisons"
"Write a Jupyter notebook analyzing distributional impacts"
```

### API/App Repos

```bash
# API
/plugin install api-development@policyengine-claude

# App
/plugin install app-development@policyengine-claude

# Invoke reviewers explicitly
"Review this Flask endpoint for performance issues"
"Review this React component for best practices"
```

## Multi-Agent Workflow

The country-models plugin implements a sophisticated isolated development workflow:

### Phase 1: Documentation
`@document_collector` gathers authoritative sources and posts to GitHub issue

### Phase 2: Parallel Development (Isolated)
- `@test-creator` writes tests from documentation ONLY (never sees implementation)
- `@rules-engineer` implements from documentation ONLY (never sees test expectations)

### Phase 3: Integration & Validation
- Merge test and implementation branches
- `@policy-domain-validator` checks federal/state separation
- `@reference-validator` checks citations
- `@cross-program-validator` ensures consistency

### Phase 4: CI & PR
- `@ci-fixer` resolves any CI failures
- Create/update PR
- `@rules-reviewer` provides final review

### Why Isolation?

Developing tests and implementation separately prevents implementation bias:
- Tests verify **what the law says**
- Implementation codes **what the law says**
- Both work from the **same authoritative source**
- Only the reviewer sees both to catch discrepancies

## Key Principles

### Source Authority
Statutes > Regulations > Official Websites > Secondary Sources

### Zero Hard-Coded Values
All values must be in parameters, never in code:
```python
# ❌ Wrong
ctc_amount = 2000

# ✅ Correct
ctc_amount = parameters("gov.irs.credits.ctc.amount.base_amount")
```

### Vectorization
No if-elif-else with household data:
```python
# ❌ Wrong
if age < 18:
    eligible = True
else:
    eligible = False

# ✅ Correct
eligible = age < 18  # NumPy array operation
```

### Documentation
Every parameter must trace to primary source:
```yaml
reference:
  - title: "IRC Section 24(a)"
    href: "https://www.law.cornell.edu/uscode/text/26/24"
```

## Migrating from Submodules

### Old Way (Deprecated)
```bash
git submodule add https://github.com/PolicyEngine/.claude.git .claude
```

**Problems:** Git complexity, update synchronization, symlink issues

### New Way (Plugin System)
```bash
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install country-models@policyengine-claude
```

**Benefits:** No Git complexity, global installation, easy updates, selective installation

### Migration Steps

1. **Remove submodule:**
   ```bash
   git submodule deinit -f .claude
   git rm -f .claude
   rm -rf .git/modules/.claude
   ```

2. **Add plugin auto-install:**
   Create/update `.claude/settings.json`:
   ```json
   {
     "plugins": {
       "marketplaces": ["PolicyEngine/policyengine-claude"],
       "auto_install": ["country-models@policyengine-claude"]
     }
   }
   ```

3. **Commit and push:**
   ```bash
   git add .claude/settings.json
   git commit -m "Migrate from .claude submodule to policyengine-claude plugin"
   git push
   ```

4. **Team members:** Trust repo and plugin auto-installs!

## Development

### Contributing

To improve agents, commands, or skills:

1. Fork this repository
2. Make changes to the appropriate files
3. Test with Claude Code
4. Submit PR with `changelog_entry.yaml`:
   ```yaml
   - bump: patch
     changes:
       changed:
       - Improved X agent to handle Y case
   ```

### Plugin Structure

```
policyengine-claude/
├── .claude-plugin/
│   └── marketplace.json       # Plugin configuration
├── agents/
│   ├── country-models/        # Country package agents
│   ├── api/                   # API agents
│   ├── app/                   # App agents
│   └── shared/                # Shared resources
├── commands/
│   ├── encode-policy.md       # Main workflow
│   ├── review-pr.md           # PR review
│   └── fix-pr.md              # PR fixes
├── skills/
│   ├── policyengine-us-skill/
│   ├── policyengine-analysis-skill/
│   └── policyengine-standards-skill/
└── README.md
```

## Versioning

Follows semantic versioning:
- **Major**: Breaking changes to agent/command/skill structure
- **Minor**: New agents, commands, or skills
- **Patch**: Improvements, bug fixes, clarifications

Current version: **1.0.0**

## Support

- **Issues**: https://github.com/PolicyEngine/policyengine-claude/issues
- **Discussions**: https://github.com/PolicyEngine/policyengine-claude/discussions
- **Email**: hello@policyengine.org

## Related Resources

- **PolicyEngine Main**: https://github.com/PolicyEngine
- **Documentation**: https://policyengine.org/docs
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **Plugin Documentation**: https://docs.claude.com/en/docs/claude-code/plugins

## License

MIT License - see LICENSE file for details.

---

**PolicyEngine** - Computing the impact of public policy for everyone

Maintained by the PolicyEngine team with ❤️
