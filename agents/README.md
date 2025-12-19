# PolicyEngine Claude Agents

This repository contains specialized Claude agents for PolicyEngine development across different types of repositories.

## Repository Structure

```
agents/
├── country-models/              # Agents for country packages (policyengine-us, policyengine-uk, etc.)
│   ├── ci-fixer.md              # Fixes CI issues iteratively
│   ├── cross-program-validator.md # Validates program interactions
│   ├── document-collector.md    # Collects authoritative sources
│   ├── documentation-enricher.md # Enriches code with examples
│   ├── edge-case-generator.md   # Generates edge case tests
│   ├── implementation-validator.md # Validates implementations
│   ├── integration-agent.md     # Advanced merge workflows
│   ├── isolation-enforcement.md # Enforces agent isolation
│   ├── isolation-setup.md       # Sets up isolation environment
│   ├── issue-manager.md         # Manages GitHub issues and PRs
│   ├── parameter-architect.md   # Designs parameter structures
│   ├── performance-optimizer.md # Optimizes calculations
│   ├── pr-pusher.md             # Formats and pushes PRs
│   ├── program-reviewer.md      # Reviews regulatory compliance
│   ├── rules-engineer.md        # Implements rules from documentation
│   ├── test-creator.md          # Creates tests from documentation
│   └── workflow.md              # Multi-agent workflow documentation
├── api/                         # Agents for policyengine-api
│   └── api-reviewer.md          # Reviews API implementations
├── app/                         # Agents for policyengine-app
│   └── app-reviewer.md          # Reviews React app code
├── shared/                      # Shared resources across all repos
│   ├── policyengine-standards.md # Common standards and patterns
│   ├── model-evaluator.md       # Evaluates model outputs
│   └── pr-merge-checklist.md    # PR merge checklist
├── branch-comparator.md         # Compares branches for differences
├── legislation-statute-analyzer.md # Analyzes legislative text
└── reference-validator.md       # Validates parameter references
```

## Usage

Install via Claude Code plugin marketplace:

```bash
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install country-models@policyengine-claude
```

Or add to your repo's `.claude/settings.json` for auto-install:

```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["country-models@policyengine-claude"]
  }
}
```

## Agent Categories

### Country Models (policyengine-us, policyengine-uk, etc.)
These agents support the multi-agent development workflow for implementing tax and benefit rules with proper isolation and verification.

### API (policyengine-api)
Agents focused on Flask API development, performance, security, and proper REST practices.

### App (policyengine-app)
Agents for React application development, focusing on component quality, performance, and user experience.

### Shared
Resources and agents that apply across all PolicyEngine repositories.

## Multi-Agent Workflow (Country Models)
For country model development, we use an isolated multi-agent approach:
1. **Document Collector** gathers authoritative sources
2. **Test Creator** writes tests (without seeing implementation)
3. **Rules Engineer** implements rules (without seeing test expectations)
4. **Implementation Validator** verifies implementation quality and compliance
5. **Supervisor** orchestrates and ensures quality

See `country-models/workflow.md` for detailed workflow documentation.

## Complete Agent Directory

### Country Models Agents (16)

| Agent | Description | Primary Use Case |
|-------|-------------|------------------|
| **ci-fixer** | Runs tests locally, fixes issues iteratively | Automated CI/CD pipeline fixing |
| **cross-program-validator** | Validates interactions between benefit programs | Preventing integration issues |
| **document-collector** | Gathers authoritative documentation | Research and documentation collection |
| **documentation-enricher** | Enriches code with examples and references | Improving code documentation |
| **edge-case-generator** | Generates comprehensive edge case tests | Test coverage improvement |
| **implementation-validator** | Validates implementations for quality | Code quality assurance |
| **integration-agent** | Advanced merge workflows | Branch management |
| **issue-manager** | Finds or creates GitHub issues and PRs | Issue tracking and management |
| **parameter-architect** | Designs comprehensive parameter structures | System design |
| **performance-optimizer** | Optimizes benefit calculations for performance | Performance tuning |
| **pr-pusher** | Formats and pushes PRs | PR quality control |
| **program-reviewer** | Reviews government program implementations | Regulatory compliance |
| **rules-engineer** | Implements government benefit program rules | Policy implementation |
| **test-creator** | Creates comprehensive integration tests | Test development |
| **isolation-setup** | Sets up git worktrees for isolated development | Development environment |
| **isolation-enforcement** | Enforces test/implementation isolation | Multi-agent workflow |

### Root-Level Agents (3)

| Agent | Description | Primary Use Case |
|-------|-------------|------------------|
| **branch-comparator** | Compares branches for differences | Identifying changes between development branches |
| **legislation-statute-analyzer** | Analyzes legislative text and identifies statutes | Legal document analysis |
| **reference-validator** | Validates that all parameters have proper references | Documentation validation |

### API-Specific Agents

| Agent | Description | Location |
|-------|-------------|----------|
| **api-reviewer** | Reviews API implementations for REST best practices | `api/` |

### App-Specific Agents

| Agent | Description | Location |
|-------|-------------|----------|
| **app-reviewer** | Reviews React app code for quality and performance | `app/` |

### Shared Resources

| Resource | Description | Purpose |
|----------|-------------|---------|
| **policyengine-standards** | Common standards and patterns | Code consistency |
| **model-evaluator** | Evaluates model outputs | Quality assurance |
| **pr-merge-checklist** | PR merge checklist | Quality control |

## Key Principles

1. **Source Authority**: Statutes > Regulations > Websites
2. **Isolation**: Tests and implementation developed separately
3. **Vectorization**: No if-elif-else with household data
4. **Documentation**: Every value traces to primary source
5. **Testing**: Document calculations with regulation references

## Total Agent Count

- **Country Models**: 16 agents
- **Root-Level**: 3 agents
- **API**: 1 agent
- **App**: 1 agent
- **Total**: 21 agents