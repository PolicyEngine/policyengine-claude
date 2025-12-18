# PolicyEngine Claude Agents

This repository contains specialized Claude agents for PolicyEngine development across different types of repositories.

## Repository Structure

```
agents/
├── country-models/              # Agents for country packages (policyengine-us, policyengine-uk, etc.)
│   ├── ci-fixer.md              # Fixes CI issues iteratively
│   ├── cross-program-validator.md # Validates program interactions
│   ├── document_collector.md    # Collects authoritative sources
│   ├── documentation-enricher.md # Enriches code with examples
│   ├── edge-case-generator.md   # Generates edge case tests
│   ├── implementation-validator.md # Validates implementations
│   ├── isolation-enforcement.md # Enforces agent isolation
│   ├── isolation-setup.md       # Sets up isolation environment
│   ├── parameter-architect.md   # Designs parameter structures
│   ├── performance-optimizer.md # Optimizes calculations
│   ├── rules-engineer.md        # Implements rules from documentation
│   ├── test-creator.md          # Creates tests from documentation
│   └── workflow.md              # Multi-agent workflow documentation
├── api/                         # Agents for policyengine-api
│   └── api-reviewer.md          # Reviews API implementations
├── app/                         # Agents for policyengine-app
│   └── app-reviewer.md          # Reviews React app code
├── shared/                      # Shared resources across all repos
│   ├── policyengine-standards.md # Common standards and patterns
│   └── model-evaluator.md       # Evaluates model outputs
├── branch-comparator.md         # Compares branches for differences
├── ci-fixer.md                  # Creates PR, monitors CI, fixes issues
├── cross-program-validator.md   # Validates benefit program interactions
├── document_collector.md        # Gathers authoritative documentation
├── documentation-enricher.md    # Enriches code with examples and references
├── edge-case-generator.md       # Generates comprehensive edge case tests
├── implementation-validator.md  # Validates implementations for quality
├── integration-agent.md         # Merges branches and fixes integration issues
├── issue-manager.md             # Manages GitHub issues for implementations
├── legislation-statute-analyzer.md # Analyzes legislative text
├── naming-coordinator.md        # Establishes naming conventions
├── parameter-architect.md       # Designs parameter structures
├── performance-optimizer.md     # Optimizes benefit calculations
├── pr-pusher.md                 # Ensures PRs are properly formatted
├── reference-validator.md       # Validates parameter references
├── rules-engineer.md            # Implements government benefit rules
├── program-reviewer.md         # Reviews government program implementations
└── test-creator.md              # Creates integration tests
```

## Usage

Each PolicyEngine repository should add this as a git submodule:

```bash
git submodule add https://github.com/PolicyEngine/.claude.git .claude
```

Then agents will be available at `.claude/agents/[category]/[agent].md`

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

### Core Agents

| Agent | Description | Primary Use Case |
|-------|-------------|------------------|
| **branch-comparator** | Compares branches for differences | Identifying changes between development branches |
| **ci-fixer** | Creates PR, monitors CI, fixes issues iteratively | Automated CI/CD pipeline fixing |
| **cross-program-validator** | Validates interactions between benefit programs | Preventing integration issues |
| **document_collector** | Gathers authoritative documentation | Research and documentation collection |
| **documentation-enricher** | Enriches code with examples and references | Improving code documentation |
| **edge-case-generator** | Generates comprehensive edge case tests | Test coverage improvement |
| **implementation-validator** | Validates implementations for quality | Code quality assurance |
| **integration-agent** | Merges branches and fixes integration issues | Branch management |
| **issue-manager** | Finds or creates GitHub issues | Issue tracking and management |
| **legislation-statute-analyzer** | Analyzes legislative text and identifies statutes | Legal document analysis |
| **naming-coordinator** | Establishes variable naming conventions | Code consistency |
| **parameter-architect** | Designs comprehensive parameter structures | System design |
| **performance-optimizer** | Optimizes benefit calculations for performance | Performance tuning |
| **pr-pusher** | Ensures PRs are properly formatted | PR quality control |
| **reference-validator** | Validates that all parameters have proper references | Documentation validation |
| **rules-engineer** | Implements government benefit program rules | Policy implementation |
| **program-reviewer** | Reviews government program implementations | Regulatory compliance |
| **test-creator** | Creates comprehensive integration tests | Test development |

### API-Specific Agents

| Agent | Description | Location |
|-------|-------------|----------|
| **api-reviewer** | Reviews API implementations for REST best practices | `api/` |

### App-Specific Agents

| Agent | Description | Location |
|-------|-------------|----------|
| **app-reviewer** | Reviews React app code for quality and performance | `app/` |

### Country Models Agents

These agents are specifically designed for country-specific implementations (policyengine-us, policyengine-uk, etc.):

| Agent | Description | Special Focus |
|-------|-------------|---------------|
| **ci-fixer** | Country-specific CI fixing | Policy logic understanding |
| **cross-program-validator** | Validates program interactions | Federal/state interactions |
| **document_collector** | Collects country-specific sources | Legal documents |
| **documentation-enricher** | Adds policy-specific examples | Regulation references |
| **edge-case-generator** | Generates policy edge cases | Benefit scenarios |
| **implementation-validator** | Validates against standards | PolicyEngine patterns |
| **isolation-enforcement** | Enforces test/implementation isolation | Multi-agent workflow |
| **isolation-setup** | Sets up isolation environment | Development environment |
| **parameter-architect** | Designs federal/state parameters | Hierarchical structure |
| **performance-optimizer** | Optimizes vectorized calculations | NumPy operations |
| **rules-engineer** | Implements with zero hard-coding | Parameterization |
| **test-creator** | Creates realistic test scenarios | Manual calculations |

### Shared Resources

| Resource | Description | Purpose |
|----------|-------------|---------|
| **policyengine-standards** | Common standards and patterns | Code consistency |
| **model-evaluator** | Evaluates model outputs | Quality assurance |

## Key Principles

1. **Source Authority**: Statutes > Regulations > Websites
2. **Isolation**: Tests and implementation developed separately
3. **Vectorization**: No if-elif-else with household data
4. **Documentation**: Every value traces to primary source
5. **Testing**: Document calculations with regulation references