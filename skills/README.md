# PolicyEngine Claude Skills

This directory contains specialized skills for PolicyEngine development. Skills provide domain-specific knowledge and guidance for working with PolicyEngine repositories and tools.

## Available Skills

### Core PolicyEngine Skills

| Skill | Description | Focus Area |
|-------|-------------|------------|
| **policyengine-core-skill** | PolicyEngine Core simulation engine | The foundation powering all PolicyEngine calculations |
| **policyengine-us-skill** | US tax and benefit microsimulation | Patterns, situation creation, and workflows for US policy |
| **policyengine-uk-skill** | UK tax and benefit microsimulation | Patterns, situation creation, and workflows for UK policy |
| **policyengine-api-skill** | PolicyEngine API | Flask REST service powering policyengine.org |
| **policyengine-app-skill** | PolicyEngine React web application | User interface at policyengine.org |

### Technical Pattern Skills

| Skill | Description | Key Topics |
|-------|-------------|------------|
| **policyengine-aggregation-skill** | Variable aggregation patterns | Using `adds` attribute and `add()` function for summing across entities |
| **policyengine-period-patterns-skill** | Period handling patterns | Converting between YEAR/MONTH periods, testing with different periods |
| **policyengine-testing-patterns-skill** | Test creation patterns | YAML structure, naming conventions, period restrictions, quality standards |
| **policyengine-implementation-patterns-skill** | Variable implementation patterns | No hard-coding, federal/state separation, metadata standards |
| **policyengine-parameter-patterns-skill** | Parameter creation patterns | YAML structure, naming conventions, metadata requirements |
| **policyengine-vectorization-skill** | Vectorization patterns | NumPy operations, where/select usage, avoiding scalar logic |
| **policyengine-review-patterns-skill** | Code review patterns | Validation checklist, common issues, review standards |
| **policyengine-code-style-skill** | Code writing style guide | Formula optimization, eliminating unnecessary variables, direct returns |

### Analysis and Research Skills

| Skill | Description | Primary Use |
|-------|-------------|-------------|
| **policyengine-analysis-skill** | Common analysis patterns | CRFB, newsletters, dashboards, impact studies |
| **policyengine-user-guide-skill** | Using PolicyEngine web apps | Analyzing tax and benefit policy impacts |
| **policyengine-python-client-skill** | Python client usage | Programmatic access via Python or REST API |

### Data Processing Skills

| Skill | Description | Technical Focus |
|-------|-------------|-----------------|
| **microdf-skill** | Weighted pandas DataFrames | Survey microdata analysis, inequality, poverty calculations |
| **microimpute-skill** | ML-based variable imputation | Filling missing values in survey data |
| **microcalibrate-skill** | Survey weight calibration | Matching population targets in enhanced microdata |
| **l0-skill** | L0 regularization | Neural network sparsification and intelligent sampling |

### Standards and Best Practices

| Skill | Description | Application |
|-------|-------------|-------------|
| **policyengine-standards-skill** | Coding standards | Formatters, CI requirements, development best practices |
| **policyengine-writing-skill** | Writing style guide | Blog posts, documentation, PR descriptions, research reports |
| **policyengine-design-skill** | Visual identity | Colors, fonts, logos, branding for all PolicyEngine materials |

## Skill Structure

Each skill follows a consistent structure:

```yaml
---
name: skill-name
description: Brief description of what the skill covers
---

# Skill Name

## For Users 👥
[User-friendly explanation]

## For Analysts 📊
[Technical details for analysis]

## For Contributors 💻
[Development guidelines]

## Resources
[Links and references]
```

## Using Skills

Skills are automatically available in Claude Code and can be invoked when relevant tasks arise. They provide:

1. **Domain Knowledge**: Deep understanding of specific PolicyEngine components
2. **Code Patterns**: Best practices and common patterns for that area
3. **Troubleshooting**: Common issues and their solutions
4. **Examples**: Real-world usage examples from the codebase

## Skill Categories

### 1. Core Engine Skills
- Focus on the simulation engine and core infrastructure
- Cover variables, parameters, entities, and periods
- Emphasize vectorization and performance

### 2. Country-Specific Skills
- Implement specific tax and benefit rules
- Handle federal/state/local hierarchies
- Provide realistic test scenarios

### 3. Application Skills
- Web app development (React)
- API development (Flask)
- User interface and experience

### 4. Data Science Skills
- Statistical analysis and calibration
- Machine learning for imputation
- Microdata processing

### 5. Standards Skills
- Code quality and formatting
- Writing and documentation
- Visual design and branding

## Contributing New Skills

To add a new skill:

1. Create a new directory: `skills/your-skill-name/`
2. Add `skill.md` with proper metadata header
3. Follow the established structure (For Users, For Analysts, For Contributors)
4. Include practical examples and troubleshooting
5. Add to this README's skill directory

## Integration with Agents

Skills complement agents by providing:
- **Knowledge Base**: Skills contain domain expertise
- **Agent Guidance**: Agents use skills for specific tasks
- **Consistency**: Shared understanding across all agents

Example workflow:
1. Agent receives task requiring PolicyEngine knowledge
2. Agent consults relevant skill for patterns and best practices
3. Agent implements solution following skill guidelines
4. Result aligns with PolicyEngine standards

## Key Principles

1. **Accuracy**: All information verified against actual code
2. **Practicality**: Focus on real-world usage patterns
3. **Clarity**: Clear explanations for different audiences
4. **Maintenance**: Keep skills updated with codebase changes
5. **Completeness**: Cover common scenarios and edge cases