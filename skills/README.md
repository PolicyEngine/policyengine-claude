# PolicyEngine Claude Skills

This directory contains specialized skills for PolicyEngine development. Skills provide domain-specific knowledge and guidance for working with PolicyEngine repositories and tools. They are now organized into logical categories for easier navigation and discovery.

## Directory Structure

```
skills/
├── technical-patterns/      # Implementation patterns and best practices
│   ├── policyengine-aggregation-skill/
│   ├── policyengine-code-style-skill/
│   ├── policyengine-variable-patterns-skill/
│   ├── policyengine-parameter-patterns-skill/
│   ├── policyengine-period-patterns-skill/
│   ├── policyengine-review-patterns-skill/
│   ├── policyengine-testing-patterns-skill/
│   └── policyengine-vectorization-skill/
│
├── domain-knowledge/        # Country/region specific knowledge
│   ├── policyengine-uk-skill/
│   └── policyengine-us-skill/
│
├── tools-and-apis/         # PolicyEngine tools and APIs
│   ├── policyengine-api-skill/
│   ├── policyengine-app-skill/
│   ├── policyengine-core-skill/
│   └── policyengine-python-client-skill/
│
├── data-science/           # Data manipulation and analysis libraries
│   ├── l0-skill/
│   ├── microcalibrate-skill/
│   ├── microdf-skill/
│   └── microimpute-skill/
│
├── documentation/          # Writing, standards, and guides
│   ├── policyengine-design-skill/
│   ├── policyengine-standards-skill/
│   ├── policyengine-user-guide-skill/
│   └── policyengine-writing-skill/
│
└── analysis/              # Policy analysis and research
    └── policyengine-analysis-skill/
```

## Skill Categories

### 📐 Technical Patterns (`technical-patterns/`)

Implementation patterns, testing standards, and coding best practices that ensure consistent, high-quality PolicyEngine implementations.

| Skill | Description | Key Topics |
|-------|-------------|------------|
| **policyengine-aggregation-skill** | Variable aggregation patterns | Using `adds` attribute and `add()` function for summing across entities |
| **policyengine-code-style-skill** | Code writing style guide | Formula optimization, eliminating unnecessary variables, direct returns |
| **policyengine-variable-patterns-skill** | Variable implementation patterns | No hard-coding, federal/state separation, metadata standards |
| **policyengine-parameter-patterns-skill** | Parameter creation patterns | YAML structure, naming conventions, metadata requirements |
| **policyengine-period-patterns-skill** | Period handling patterns | Converting between YEAR/MONTH periods, testing with different periods |
| **policyengine-review-patterns-skill** | Code review patterns | Validation checklist, common issues, review standards |
| **policyengine-testing-patterns-skill** | Test creation patterns | YAML structure, naming conventions, period restrictions, quality standards |
| **policyengine-vectorization-skill** | Vectorization patterns | NumPy operations, where/select usage, avoiding scalar logic |

### 🌍 Domain Knowledge (`domain-knowledge/`)

Country and region-specific tax and benefit system knowledge.

| Skill | Description | Focus Area |
|-------|-------------|------------|
| **policyengine-uk-skill** | UK tax and benefit microsimulation | Patterns, situation creation, and workflows for UK policy |
| **policyengine-us-skill** | US tax and benefit microsimulation | Patterns, situation creation, and workflows for US policy |

### 🛠️ Tools and APIs (`tools-and-apis/`)

Knowledge about PolicyEngine's core tools, APIs, and applications.

| Skill | Description | Focus Area |
|-------|-------------|------------|
| **policyengine-api-skill** | PolicyEngine API | Flask REST service powering policyengine.org |
| **policyengine-app-skill** | PolicyEngine React web application | User interface at policyengine.org |
| **policyengine-core-skill** | PolicyEngine Core simulation engine | The foundation powering all PolicyEngine calculations |
| **policyengine-python-client-skill** | Python client usage | Programmatic access via Python or REST API |

### 📊 Data Science (`data-science/`)

Specialized data manipulation and statistical analysis tools.

| Skill | Description | Technical Focus |
|-------|-------------|-----------------|
| **l0-skill** | L0 regularization | Neural network sparsification and intelligent sampling |
| **microcalibrate-skill** | Survey weight calibration | Matching population targets in enhanced microdata |
| **microdf-skill** | Weighted pandas DataFrames | Survey microdata analysis, inequality, poverty calculations |
| **microimpute-skill** | ML-based variable imputation | Filling missing values in survey data |
| **policyengine-uk-data-skill** | UK survey data enhancement | FRS with WAS imputation patterns |

### 📝 Documentation (`documentation/`)

Standards for writing, design, and user guidance.

| Skill | Description | Application |
|-------|-------------|-------------|
| **policyengine-design-skill** | Visual identity | Colors, fonts, logos, branding for all PolicyEngine materials |
| **policyengine-standards-skill** | Coding standards | Formatters, CI requirements, development best practices |
| **policyengine-user-guide-skill** | Using PolicyEngine web apps | Analyzing tax and benefit policy impacts |
| **policyengine-writing-skill** | Writing style guide | Blog posts, documentation, PR descriptions, research reports |

### 🔍 Analysis (`analysis/`)

Policy analysis and research methodologies.

| Skill | Description | Primary Use |
|-------|-------------|-------------|
| **policyengine-analysis-skill** | Common analysis patterns | CRFB, newsletters, dashboards, impact studies |

## Skill Structure

Each skill follows a consistent structure with a `SKILL.md` file:

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

## How Skills Work with Agents

Skills complement agents by providing:
- **Knowledge Base**: Skills contain domain expertise that agents reference
- **Agent Guidance**: Agents use skills for specific technical knowledge
- **Consistency**: Shared understanding across all agents

Example workflow:
1. Agent receives task requiring PolicyEngine knowledge
2. Agent consults relevant skill(s) for patterns and best practices
3. Agent implements solution following skill guidelines
4. Result aligns with PolicyEngine standards

## Contributing New Skills

To add a new skill:

1. **Choose the right category** based on the skill's focus:
   - `technical-patterns/` for implementation patterns
   - `domain-knowledge/` for country-specific knowledge
   - `tools-and-apis/` for tool-specific skills
   - `data-science/` for data analysis skills
   - `documentation/` for standards and guides
   - `analysis/` for research methodologies

2. **Create the skill directory**: `skills/[category]/your-skill-name/`

3. **Add `SKILL.md`** (note: uppercase) with proper metadata header

4. **Follow the established structure** (For Users, For Analysts, For Contributors)

5. **Include practical examples** and troubleshooting guidance

6. **Update this README** to include your skill in the appropriate category table

7. **Update marketplace.json** to register the skill in appropriate plugins

## Key Principles

1. **Accuracy**: All information verified against actual code
2. **Organization**: Skills grouped logically for easy discovery
3. **Practicality**: Focus on real-world usage patterns
4. **Clarity**: Clear explanations for different audiences
5. **Maintenance**: Keep skills updated with codebase changes
6. **Completeness**: Cover common scenarios and edge cases

## Quick Reference

- **Need to implement a new benefit?** → Check `technical-patterns/` skills
- **Working with US/UK systems?** → See `domain-knowledge/` skills
- **Building an API endpoint?** → Consult `tools-and-apis/policyengine-api-skill`
- **Writing documentation?** → Review `documentation/` skills
- **Analyzing policy impacts?** → Use `analysis/policyengine-analysis-skill`
- **Processing survey data?** → Explore `data-science/` skills

## Version History

- **v2.0.0** - Major reorganization into categorical folders for better navigation
- **v1.0.0** - Initial skills collection