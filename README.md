# PolicyEngine Claude

Official Claude Code plugin for PolicyEngine - a comprehensive knowledge base for users, analysts, and contributors across the entire PolicyEngine ecosystem.

## Overview

PolicyEngine Claude provides agents, slash commands, and skills for working with PolicyEngine's 40+ repository ecosystem:

- **🤖 18 Specialized Agents** - Automated workflows for development
- **🎯 3 Slash Commands** - Multi-agent orchestration
- **📚 14 Skills** - Knowledge base for users, analysts, and contributors

## Three Audiences, One Plugin

### 👥 For Users
Learn to use PolicyEngine web apps, understand calculations, and interpret results.

**Install:**
```bash
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install essential@policyengine-claude
```

**Includes:**
- `policyengine-user-guide-skill` - Using the platform
- `policyengine-us-skill` - Understanding US programs
- `policyengine-writing-skill` - Communication style

### 📊 For Analysts
Create policy analyses, build dashboards, and conduct research using PolicyEngine programmatically.

**Install:**
```bash
/plugin install analysis-tools@policyengine-claude
```

**Includes:**
- `policyengine-python-client-skill` - Programmatic access
- `policyengine-analysis-skill` - Analysis patterns
- `microdf-skill` - Data analysis utilities
- `policyengine-us-skill` - Simulation patterns
- `policyengine-writing-skill` - Report writing

### 💻 For Contributors
Develop PolicyEngine software across country models, API, app, and data packages.

**Install:**
```bash
# For country model development
/plugin install country-models@policyengine-claude

# For API development
/plugin install api-development@policyengine-claude

# For app development
/plugin install app-development@policyengine-claude

# For data science
/plugin install data-science@policyengine-claude
```

## Skills Overview (14 Total)

### User-Facing Skills

**1. policyengine-user-guide** 🆕
- Using policyengine.org web apps
- Creating reforms through UI
- Understanding household and population results
- Interpreting metrics (Gini, poverty, etc.)

**2. policyengine-python-client** 🆕
- Programmatic API access
- Using policyengine.py package
- Batch calculations
- Rate limits and authentication

### Core Platform Skills

**3. policyengine-core** 🆕
- Simulation engine architecture
- Variable and parameter systems
- Vectorization requirements
- Formula patterns
- Multi-audience: explains what Core is (users), how it works (analysts), how to develop it (contributors)

**4. policyengine-us** ✅ Enhanced
- US tax and benefit system
- Situation creation patterns
- Variable reference (400+ variables)
- Using axes for parameter sweeps
- Multi-audience: what's modeled (users), how to use (analysts), how to develop (contributors)

**5. policyengine-api** 🆕
- Flask REST API patterns
- Endpoint structure
- Caching strategy (Redis)
- Background jobs (RQ)
- Multi-audience: what API does (users), how to call it (analysts), how to develop (contributors)

**6. policyengine-app** 🆕
- React application patterns
- Component structure
- Routing and state management
- Chart integration (Plotly)
- Multi-audience: app features (users), URL structure (analysts), development patterns (contributors)

### Analysis and Data Skills

**7. policyengine-analysis** ✅ Enhanced
- Impact analysis patterns
- Streamlit dashboards
- Jupyter notebooks
- Plotly visualizations with PolicyEngine branding
- Multi-audience: how analysis works (users), analysis code patterns (analysts)

**8. microdf** 🆕
- Weighted pandas DataFrames
- Inequality metrics (Gini, top shares)
- Poverty calculations
- Survey microdata analysis
- Multi-audience: what microdf does (users), how to use (analysts), how to develop (contributors)

### Data Ecosystem Skills

**9. microimpute** 🆕
- ML-based variable imputation
- Multiple methods (linear, random forest, quantile forest, XGBoost)
- Quantile loss benchmarking
- Used in policyengine-us-data to fill missing survey variables

**10. microcalibrate** 🆕
- Survey weight calibration to population targets
- L0 regularization for dataset sparsification
- Automatic hyperparameter tuning (Optuna)
- Interactive dashboard at microcalibrate.vercel.app

**11. l0** 🆕
- PyTorch L0 regularization for neural networks
- Intelligent sampling and feature selection
- Used by microcalibrate for household selection
- Based on Louizos et al. (2017) paper

### Design and Standards Skills

**12. policyengine-design** 🆕
- PolicyEngine visual identity (colors, fonts, logos)
- Chart branding (Plotly format_fig pattern)
- Streamlit theme configuration
- Color palette and usage guidelines (v1: #39C6C0, v2: #319795)
- Multi-audience: recognizing brand (users), applying branding (analysts/contributors)

**13. policyengine-standards** ✅
- Code formatting (Black, Prettier)
- Git workflow
- Changelog management
- CI requirements
- Common AI pitfalls

**14. policyengine-writing** ✅
- Active voice, quantitative language
- Sentence case for headings
- Neutral, objective tone
- Blog post and PR description patterns

## Agents (18 Total)

### Country Model Agents (15)

**Multi-agent workflow:**
- `document_collector` - Gather authoritative sources
- `test-creator` - Write tests from documentation (isolated)
- `rules-engineer` - Implement variables/parameters (isolated)
- `rules-reviewer` - Review implementation
- `parameter-architect` - Design parameter structures

**Validators:**
- `policy-domain-validator` - Federal/state separation, naming
- `reference-validator` - Citations and documentation
- `cross-program-validator` - Cross-program consistency
- `implementation-validator` - Zero hard-coded values
- `performance-optimizer` - Vectorization opportunities

**Quality and CI:**
- `documentation-enricher` - Enhance documentation
- `edge-case-generator` - Comprehensive test cases
- `ci-fixer` - Fix CI failures
- `isolation-setup` - Git worktrees for isolated development
- `isolation-enforcement` - Ensure test/implementation isolation

### Other Agents (3)

- `api-reviewer` - Review Flask/API code
- `app-reviewer` - Review React/app code

## Slash Commands (3 Total)

**`/encode-policy <program-name>`**
- Orchestrate complete multi-agent workflow
- Implement new government programs
- Example: `/encode-policy Idaho LIHEAP`

**`/review-pr [pr-number]`**
- Comprehensive PR review (read-only)
- Post findings to GitHub
- Example: `/review-pr 123`

**`/fix-pr [pr-number]`**
- Apply fixes from review
- Push updates automatically
- Example: `/fix-pr 123`

## Available Plugins (6)

| Plugin | Audience | Agents | Commands | Skills |
|--------|----------|--------|----------|--------|
| **essential** | Users | 0 | 0 | 3 |
| **country-models** | Contributors | 15 | 3 | 5 |
| **api-development** | Contributors | 1 | 0 | 6 |
| **app-development** | Contributors | 1 | 0 | 6 |
| **analysis-tools** | Analysts | 0 | 0 | 7 |
| **data-science** | Analysts/Contributors | 0 | 0 | 8 |
| **complete** | All | 18 | 3 | 14 |

## Installation

### For End Users

```bash
# Add marketplace
/plugin marketplace add PolicyEngine/policyengine-claude

# Install essentials
/plugin install essential@policyengine-claude
```

### For Policy Analysts

```bash
# Add marketplace
/plugin marketplace add PolicyEngine/policyengine-claude

# Install analysis tools
/plugin install analysis-tools@policyengine-claude
```

### For Contributors

**In specific repos (auto-install):**

Each PolicyEngine repo has `.claude/settings.json` that auto-installs the appropriate plugin:

```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["country-models@policyengine-claude"]
  }
}
```

**Result:** When you trust the repo, the plugin auto-installs!

## Multi-Repo Architecture

### The PolicyEngine Ecosystem

```
Layer 0: Foundation
├── L0 (PyTorch regularization for sparsification)

Layer 1: Core Engine
├── policyengine-core (simulation engine)

Layer 2: Country Models (depend on core)
├── policyengine-us (US federal + 50 states)
├── policyengine-uk (UK tax and benefits)
├── policyengine-canada (Canada federal + provincial)
├── policyengine-il (Israel)
└── policyengine-ng (Nigeria)

Layer 3: Data Utilities
├── microdf (weighted DataFrames for analysis)
├── microimpute (ML variable imputation)
└── microcalibrate (survey calibration, uses L0)

Layer 4: Enhanced Data (depend on country models + data utilities)
├── policyengine-us-data (enhanced CPS, uses microimpute + microcalibrate)
└── policyengine-uk-data (enhanced FRS)

Layer 5: Services
├── policyengine-api (v1 - production Flask API)
├── policyengine-api-v2 (v2 - monorepo with 3 microservices, in development)
└── policyengine.py (Python client)

Layer 6: Interfaces
├── policyengine-app (v1 - production React app)
└── policyengine-app-v2 (v2 - Next.js + Mantine, in development)

Layer 7: Applications
├── Analysis repos (crfb-tob-impacts, newsletters, dashboards)
└── Calculators (givecalc, salt-amt-calculator, ctc-calculator)
```

**Version status:**
- ✅ v1 APIs and apps are current production
- 🚧 v2 APIs and apps are in active development
- Skills cover both where relevant, with migration notes

### Skills Point to Repos

Skills use a **pointer pattern** - they provide stable principles and point to current implementation:

```markdown
## For Contributors

**To see current implementation:**
```bash
cat policyengine_api/endpoints/economy.py
```

**To find patterns:**
```bash
grep -r "cache_key" policyengine_api/
```
```

**Benefits:**
- ✅ No version drift - skills point to code
- ✅ Branch-aware - reads from your checkout
- ✅ Single source of truth - code is documentation
- ✅ Cross-repo learning - can explore related repos

### Multi-Repo Workflows

**Example: API contributor understanding country models**
```bash
# Working in policyengine-api
cd policyengine-api

# Claude has policyengine-api-skill installed
# Need to understand variable structure

# Claude can add related repo
/add-dir ../policyengine-us

# Now Claude can read both repos
# Uses policyengine-us-skill to understand variables
# Uses policyengine-api-skill to create endpoint
```

**Example: Analyst debugging data issues**
```bash
# Working in analysis repo
cd crfb-tob-impacts

# Has analysis-tools plugin
# Includes: microdf-skill, policyengine-us-skill

# Can install additional skills on-demand
/plugin install policyengine-us-data-skill@policyengine-claude

# Now can understand data pipeline issues
```

## Repository-Specific Auto-Install

Each repo type installs appropriate plugins:

| Repository | Plugin | What It Includes |
|------------|--------|------------------|
| policyengine-us | country-models | 15 agents, 3 commands, 5 skills |
| policyengine-uk | country-models | 15 agents, 3 commands, 5 skills |
| policyengine-api | api-development | 1 agent, 5 skills |
| policyengine-app | app-development | 1 agent, 5 skills |
| crfb-tob-impacts | analysis-tools | 6 skills |
| givecalc | analysis-tools | 6 skills |
| microdf | data-science | 4 skills |

## How Skills Serve Multiple Audiences

Each skill organized with sections:

```markdown
# Skill Name

## For Users 👥
[What this is, why it matters]

## For Analysts 📊
[How to use it programmatically]

## For Contributors 💻
[How to develop it]
**Current implementation:**
```bash
cat path/to/current/code.py
```
```

**Example: policyengine-us-skill**

- **Users** learn what programs are modeled (EITC, CTC, SNAP, etc.)
- **Analysts** learn situation creation and variable reference
- **Contributors** learn where to find implementation (`policyengine_us/variables/`)

## Key Innovation: Documentation Pointers

Instead of duplicating code, skills **point to repos**:

**Traditional approach (version drift):**
```markdown
## API Endpoint Pattern

```python
# Hardcoded example from when skill was written
# Gets outdated as code evolves
@app.route("/us/calculate")
def calculate():
    # Old pattern from 6 months ago
```
```

**PolicyEngine approach (always current):**
```markdown
## API Endpoint Pattern

**Current implementation:**
```bash
cat policyengine_api/endpoints/economy.py
```

**Pattern demonstrated:**
- Request validation
- Cache checking
- Computation
- Error handling
```

**Benefits:**
- Always shows current code
- Works with feature branches
- Single source of truth
- No maintenance burden

## Use Cases

### Use Case 1: User Learning the Platform

```
User: "How do I calculate how much I'd save from donating to charity?"

Claude: [Has policyengine-user-guide-skill]
"Go to policyengine.org/us/household, enter your income and donation amount.
The calculator shows your tax savings..."

[Points to givecalc for more advanced calculator]
```

### Use Case 2: Analyst Creating Impact Study

```
User in crfb-tob-impacts: "Analyze CTC expansion proposal"

Claude: [Has analysis-tools plugin]
[Uses policyengine-python-client-skill for API access]
[Uses policyengine-analysis-skill for dashboard patterns]
[Uses microdf-skill for inequality calculations]
[Uses policyengine-writing-skill for blog post]

Creates: Analysis notebook + Streamlit dashboard + blog post draft
```

### Use Case 3: Contributor Implementing New Program

```
User in policyengine-us: "/encode-policy California EITC"

Claude: [Has country-models plugin]
[Invokes @document_collector] → Gathers CA EITC regulations
[Invokes @test-creator + @rules-engineer in parallel] → Isolated development
[Uses policyengine-core-skill for variable patterns]
[Uses policyengine-standards-skill for code quality]
[Uses policyengine-writing-skill for PR description]

Creates: Tests + Implementation + PR
```

### Use Case 4: Cross-Repo Debugging

```
User in policyengine-api: "Why is EITC calculation wrong?"

Claude: [Has api-development plugin]
"Let me check the endpoint... and the variable implementation"

/add-dir ../policyengine-us

[Reads API endpoint code using policyengine-api-skill]
[Reads EITC variable code using policyengine-us-skill]
[Compares and identifies discrepancy]

"The API is passing the wrong year parameter to the simulation..."
```

## Installation by Use Case

### I want to: Use PolicyEngine

```bash
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install essential@policyengine-claude
```

### I want to: Analyze policies with Python

```bash
/plugin install analysis-tools@policyengine-claude
```

### I want to: Contribute to policyengine-us

```bash
# Automatic when you trust policyengine-us repo
# Or manually:
/plugin install country-models@policyengine-claude
```

### I want to: Develop the API

```bash
# Automatic when you trust policyengine-api repo
# Or manually:
/plugin install api-development@policyengine-claude
```

### I want to: Develop the React app

```bash
# Automatic when you trust policyengine-app repo
# Or manually:
/plugin install app-development@policyengine-claude
```

### I want to: Work with data packages

```bash
/plugin install data-science@policyengine-claude
```

### I want to: Everything

```bash
/plugin install complete@policyengine-claude
```

## Skills Catalog

| Skill | Users | Analysts | Contributors | Key Topics |
|-------|-------|----------|--------------|------------|
| policyengine-user-guide | ✅ | ⚪ | ⚪ | Web app usage, understanding results |
| policyengine-python-client | ⚪ | ✅ | ⚪ | API access, policyengine.py package |
| policyengine-core | ✅ | ✅ | ✅ | Simulation engine, architecture |
| policyengine-us | ✅ | ✅ | ✅ | US tax/benefit system, variables |
| policyengine-api | ⚪ | ✅ | ✅ | REST endpoints (v1), caching, services |
| policyengine-app | ⚪ | ⚪ | ✅ | React components (v1), routing, charts |
| policyengine-analysis | ✅ | ✅ | ⚪ | Impact studies, dashboards, notebooks |
| microdf | ✅ | ✅ | ✅ | Inequality, poverty, weighted stats |
| microimpute | ⚪ | ✅ | ✅ | ML imputation, quantile forest |
| microcalibrate | ⚪ | ✅ | ✅ | Survey calibration, L0 sparsity |
| l0 | ⚪ | ✅ | ✅ | Regularization, sampling gates |
| policyengine-design | ✅ | ✅ | ✅ | Colors (v1/v2), fonts, logos, branding |
| policyengine-standards | ⚪ | ⚪ | ✅ | Code formatting, Git, CI |
| policyengine-writing | ✅ | ✅ | ✅ | Active voice, quantitative, neutral |

## Team Setup

### Auto-Install in Repositories

Add to `.claude/settings.json` in each repo:

**policyengine-us:**
```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["country-models@policyengine-claude"]
  }
}
```

**policyengine-api:**
```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["api-development@policyengine-claude"]
  }
}
```

**crfb-tob-impacts (analysis repo):**
```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["analysis-tools@policyengine-claude"]
  }
}
```

**Result:** Team members trust repo → plugin auto-installs → everyone has same knowledge base!

## Plugin Distribution Strategy

### Essential (For Everyone)
- **Target:** All PolicyEngine users
- **What:** Basic platform knowledge
- **Skills:** user-guide, policyengine-us, writing

### Country Models (For Country Package Development)
- **Target:** Contributors to policyengine-us, policyengine-uk, etc.
- **What:** Multi-agent workflow + simulation knowledge
- **Agents:** 15 specialized agents
- **Commands:** /encode-policy, /review-pr, /fix-pr
- **Skills:** user-guide, core, us, standards, writing

### API Development (For API Contributors)
- **Target:** policyengine-api contributors
- **What:** API patterns and review
- **Agents:** api-reviewer
- **Skills:** api, core, us, standards, writing

### App Development (For App Contributors)
- **Target:** policyengine-app contributors
- **What:** React patterns and review
- **Agents:** app-reviewer
- **Skills:** app, api, us, standards, writing

### Analysis Tools (For Policy Analysts)
- **Target:** Analysis repos, researchers
- **What:** Analysis patterns and tools
- **Skills:** user-guide, python-client, us, analysis, microdf, writing

### Data Science (For Data Package Contributors)
- **Target:** Data package contributors
- **What:** Data analysis utilities
- **Skills:** microdf, us, standards, writing

## Multi-Repo Best Practices

### Working Across Repositories

**Use /add-dir to work with multiple repos:**

```bash
# Start in one repo
cd policyengine-us

# Add related repo
/add-dir ../policyengine-core

# Claude can now read files from both repos
# Skills point to files in both repos
```

**Benefits:**
- Single Claude session across repos
- Skills work across repo boundaries
- Understand dependencies
- Debug cross-repo issues

### Hierarchical CLAUDE.md Files

You can have CLAUDE.md in parent directory:

```
/Users/you/PolicyEngine/
├── CLAUDE.md                    # Loaded when in any child repo
├── policyengine-us/
│   └── CLAUDE.md                # Also loaded when in this repo
├── policyengine-api/
│   └── CLAUDE.md                # Also loaded when in this repo
└── crfb-tob-impacts/
    └── CLAUDE.md                # Also loaded when in this repo
```

**Claude loads:**
- Parent CLAUDE.md (if exists)
- Current repo CLAUDE.md (if exists)
- Plugin skills (based on auto_install)

## Migrating from Submodules

### Old Way (Deprecated)
```bash
git submodule add https://github.com/PolicyEngine/.claude.git .claude
git submodule update --init --recursive
```

**Problems:**
- Git submodule complexity
- Update synchronization
- Symlink issues
- Per-repo configuration

### New Way (Plugin System)
```bash
# Just add settings.json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["country-models@policyengine-claude"]
  }
}
```

**Benefits:**
- No Git complexity
- Auto-install for team
- Easy updates
- Works globally

### Migration PRs Filed

- PolicyEngine/policyengine-us#6692
- PolicyEngine/policyengine-uk#1362
- PolicyEngine/crfb-tob-impacts#24
- PolicyEngine/givecalc#43

## Contributing

### Adding New Skills

1. **Create skill directory:**
   ```bash
   mkdir skills/my-new-skill
   ```

2. **Create SKILL.md with sections:**
   ```markdown
   ---
   name: my-skill
   description: Brief description
   ---

   # Skill Name

   ## For Users 👥
   [What it is]

   ## For Analysts 📊
   [How to use it]

   ## For Contributors 💻
   [How to develop it]
   **Current implementation:**
   ```bash
   cat path/to/code.py
   ```
   ```

3. **Add to marketplace.json**

4. **Test with Claude Code**

5. **Submit PR with changelog_entry.yaml**

### Skill Guidelines

**DO include:**
- ✅ Multi-audience sections (users, analysts, contributors)
- ✅ Stable principles and patterns
- ✅ Pointers to current implementation (file paths)
- ✅ Commands to explore repos (cat, grep, tree, ls)
- ✅ Cross-references to related skills
- ✅ Real examples from PolicyEngine repos

**DON'T include:**
- ❌ Hardcoded file contents (point to files instead)
- ❌ Version-specific implementation details
- ❌ Duplicate information from other skills
- ❌ Unstable, rapidly-changing patterns

### Testing Skills

```bash
# Install locally
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install my-plugin@policyengine-claude

# Ask Claude to use the skill
"Use the my-skill to help me with X"

# Verify Claude can find and use it
```

## Version History

**v2.0.0** - Comprehensive multi-audience skills
- Added 6 new skills (user-guide, python-client, core, api, app, microdf)
- Enhanced existing skills with multi-audience sections
- Added essential and data-science plugins
- Introduced documentation pointer pattern

**v1.0.0** - Initial release
- 18 agents for country model development
- 3 slash commands
- 4 skills (us, analysis, standards, writing)

## Support

- **Issues:** https://github.com/PolicyEngine/policyengine-claude/issues
- **Discussions:** https://github.com/PolicyEngine/policyengine-claude/discussions
- **Email:** hello@policyengine.org

## Related Resources

- **PolicyEngine Main:** https://github.com/PolicyEngine
- **Website:** https://policyengine.org
- **Documentation:** https://policyengine.org/us/docs
- **Claude Code Docs:** https://docs.claude.com/en/docs/claude-code
- **Plugin Docs:** https://docs.claude.com/en/docs/claude-code/plugins

## License

MIT License - see LICENSE file for details.

---

**PolicyEngine** - Computing the impact of public policy for everyone

**Note:** This may be the first comprehensive multi-repo, multi-audience Claude Code plugin marketplace. If you're building a similar multi-repo system, feel free to use this as a reference!
