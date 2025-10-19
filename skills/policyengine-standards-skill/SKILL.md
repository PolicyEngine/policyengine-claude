---
name: policyengine-standards
description: PolicyEngine coding standards, formatters, CI requirements, and development best practices
---

# PolicyEngine Standards Skill

Use this skill to ensure code meets PolicyEngine's development standards and passes CI checks.

## When to Use This Skill

- Before committing code to any PolicyEngine repository
- When CI checks fail with linting/formatting errors
- Setting up a new PolicyEngine repository
- Reviewing PRs for standard compliance
- When AI tools generate code that needs standardization

## Critical Requirements

### Python Version
⚠️ **MUST USE Python 3.13** - Do NOT downgrade to older versions
- Check version: `python --version`
- Use `pyproject.toml` to specify version requirements

### Command Execution
⚠️ **ALWAYS use `uv run` for Python commands** - Never use bare `python` or `pytest`
- ✅ Correct: `uv run python script.py`, `uv run pytest tests/`
- ❌ Wrong: `python script.py`, `pytest tests/`
- This ensures correct virtual environment and dependencies

### Documentation (Python Projects)
⚠️ **MUST USE Jupyter Book 2.0 (MyST-NB)** - NOT Jupyter Book 1.x
- Build docs: `myst build docs` (NOT `jb build`)
- Use MyST markdown syntax

## Before Committing - Checklist

1. **Format code**: `make format` or language-specific formatter
2. **Run tests**: `make test` to ensure all tests pass
3. **Check linting**: Ensure no linting errors
4. **Use config files**: Prefer config files over environment variables
5. **Reference issues**: Include "Fixes #123" in commit message

## Python Standards

### Formatting
- **Formatter**: Black with 79-character line length
- **Command**: `make format` or `black . -l 79`
- **Check without changes**: `black . -l 79 --check`

```bash
# Format all Python files
make format

# Check if formatting is needed (CI-style)
black . -l 79 --check
```

### Code Style
```python
# Imports: Grouped and alphabetized
import os
import sys
from pathlib import Path  # stdlib

import numpy as np
import pandas as pd  # third-party

from policyengine_us import Simulation  # local

# Naming conventions
class TaxCalculator:  # CamelCase for classes
    pass

def calculate_income_tax(income):  # snake_case for functions
    annual_income = income * 12  # snake_case for variables
    return annual_income

# Type hints (recommended)
def calculate_tax(income: float, state: str) -> float:
    """Calculate state income tax.

    Args:
        income: Annual income in dollars
        state: Two-letter state code

    Returns:
        Tax liability in dollars
    """
    pass

# Error handling - catch specific exceptions
try:
    result = simulation.calculate("income_tax", 2024)
except KeyError as e:
    raise ValueError(f"Invalid variable name: {e}")
```

### Testing
```python
import pytest

def test_ctc_calculation():
    """Test Child Tax Credit calculation for family with 2 children."""
    situation = create_family(income=50000, num_children=2)
    sim = Simulation(situation=situation)
    ctc = sim.calculate("ctc", 2024)[0]

    assert ctc == 4000, "CTC should be $2000 per child"
```

**Run tests:**
```bash
# All tests
make test

# Or with uv
uv run pytest tests/ -v

# Specific test
uv run pytest tests/test_tax.py::test_ctc_calculation -v

# With coverage
uv run pytest tests/ --cov=policyengine_us --cov-report=html
```

## JavaScript/React Standards

### Formatting
- **Formatters**: Prettier + ESLint
- **Command**: `npm run lint -- --fix && npx prettier --write .`
- **CI Check**: `npm run lint -- --max-warnings=0`

```bash
# Format all files
make format

# Or manually
npm run lint -- --fix
npx prettier --write .

# Check if formatting is needed (CI-style)
npm run lint -- --max-warnings=0
```

### Code Style
```javascript
// Use functional components only (no class components)
import { useState, useEffect } from "react";

function TaxCalculator({ income, state }) {
  const [tax, setTax] = useState(0);

  useEffect(() => {
    // Calculate tax when inputs change
    calculateTax(income, state).then(setTax);
  }, [income, state]);

  return (
    <div>
      <p>Tax: ${tax.toLocaleString()}</p>
    </div>
  );
}

// File naming
// - Components: PascalCase.jsx (TaxCalculator.jsx)
// - Utilities: camelCase.js (formatCurrency.js)

// Environment config - use config file pattern
// src/config/environment.js
const config = {
  API_URL: process.env.NODE_ENV === 'production'
    ? 'https://api.policyengine.org'
    : 'http://localhost:5000'
};
export default config;
```

### React Component Size
- Keep components under 150 lines after formatting
- Extract complex logic into custom hooks
- Split large components into smaller ones

## Version Control Standards

### Changelog Management

**CRITICAL**: For PRs, ONLY modify `changelog_entry.yaml`. NEVER manually update `CHANGELOG.md` or `changelog.yaml`.

**Correct Workflow:**
1. Create `changelog_entry.yaml` at repository root:
   ```yaml
   - bump: patch  # or minor, major
     changes:
       added:
       - Description of new feature
       fixed:
       - Description of bug fix
       changed:
       - Description of change
   ```

2. Commit ONLY `changelog_entry.yaml` with your code changes

3. GitHub Actions automatically updates `CHANGELOG.md` and `changelog.yaml` on merge

**DO NOT:**
- ❌ Run `make changelog` manually during PR creation
- ❌ Commit `CHANGELOG.md` or `changelog.yaml` in your PR
- ❌ Modify main changelog files directly

### Git Workflow

1. **Create branches on PolicyEngine repos, NOT forks**
   - Forks cause CI failures due to missing secrets
   - Request write access if needed

2. **Branch naming**: `feature-name` or `fix-issue-123`

3. **Commit messages**:
   ```
   Add CTC reform analysis for CRFB report

   - Implement household-level calculations
   - Add state-by-state comparison
   - Create visualizations

   Fixes #123
   ```

4. **PR description**: Include "Fixes #123" to auto-close issues

### Common Git Pitfalls

**Never do these:**
- ❌ Force push to main/master
- ❌ Commit secrets or `.env` files
- ❌ Skip hooks with `--no-verify`
- ❌ Create versioned files (app_v2.py, component_new.jsx)

**Always do:**
- ✅ Fix original files in place
- ✅ Run formatters before pushing
- ✅ Reference issue numbers in commits
- ✅ Watch CI after filing PR

## Common AI Pitfalls

Since many PRs are AI-generated, watch for these common mistakes:

### 1. File Versioning
**❌ Wrong:**
```bash
# Creating new versions instead of fixing originals
app_new.py
app_v2.py
component_refactored.jsx
```

**✅ Correct:**
```bash
# Always modify the original file
app.py  # Fixed in place
```

### 2. Formatter Not Run
**❌ Wrong:** Committing without formatting (main cause of CI failures)

**✅ Correct:**
```bash
# Python
make format
black . -l 79

# React
npm run lint -- --fix
npx prettier --write .
```

### 3. Environment Variables
**❌ Wrong:**
```javascript
// React env vars without REACT_APP_ prefix
const API_URL = process.env.API_URL;  // Won't work!
```

**✅ Correct:**
```javascript
// Use config file pattern instead
import config from './config/environment';
const API_URL = config.API_URL;
```

### 4. Using Wrong Python Version
**❌ Wrong:** Downgrading to Python 3.10 or older

**✅ Correct:** Use Python 3.13 as specified in project requirements

### 5. Manual Changelog Updates
**❌ Wrong:** Running `make changelog` and committing `CHANGELOG.md`

**✅ Correct:** Only create `changelog_entry.yaml` in PR

## Repository Setup Patterns

### Python Package Structure
```
policyengine-package/
├── policyengine_package/
│   ├── __init__.py
│   ├── core/
│   ├── calculations/
│   └── utils/
├── tests/
│   ├── test_calculations.py
│   └── test_core.py
├── pyproject.toml
├── Makefile
├── CLAUDE.md
├── CHANGELOG.md
└── README.md
```

### React App Structure
```
policyengine-app/
├── src/
│   ├── components/
│   ├── pages/
│   ├── config/
│   │   └── environment.js
│   └── App.jsx
├── public/
├── package.json
├── .eslintrc.json
├── .prettierrc
└── README.md
```

## Makefile Commands

Standard commands across PolicyEngine repos:

```bash
make install    # Install dependencies
make test       # Run tests
make format     # Format code
make changelog  # Update changelog (automation only, not manual)
make debug      # Start dev server (apps)
make build      # Production build (apps)
```

## CI Stability

### Common CI Issues

**1. Fork PRs Fail**
- **Problem**: PRs from forks don't have access to repository secrets
- **Solution**: Create branches directly on PolicyEngine repos

**2. GitHub API Rate Limits**
- **Problem**: Smoke tests fail with 403 errors
- **Solution**: Re-run failed jobs (different runners have different limits)

**3. Linting Failures**
- **Problem**: Code not formatted before commit
- **Solution**: Always run `make format` before committing

**4. Test Failures in CI but Pass Locally**
- **Problem**: Missing `uv run` prefix
- **Solution**: Use `uv run pytest` instead of `pytest`

## Best Practices Checklist

### Code Quality
- [ ] Code formatted with Black (Python) or Prettier (JS)
- [ ] No linting errors
- [ ] All tests pass
- [ ] Type hints added (Python, where applicable)
- [ ] Docstrings for public functions/classes
- [ ] Error handling with specific exceptions

### Version Control
- [ ] Only `changelog_entry.yaml` created (not CHANGELOG.md)
- [ ] Commit message references issue number
- [ ] Branch created on PolicyEngine repo (not fork)
- [ ] No secrets or .env files committed
- [ ] Original files modified (no _v2 or _new files)

### Testing
- [ ] Tests written for new functionality
- [ ] Tests pass locally with `make test`
- [ ] Coverage maintained or improved
- [ ] Edge cases handled

### Documentation
- [ ] README updated if needed
- [ ] Code comments for complex logic
- [ ] API documentation updated if needed
- [ ] Examples provided for new features

## Quick Reference

### Format Commands by Language

**Python:**
```bash
make format                # Format code
black . -l 79 --check      # Check formatting
uv run pytest tests/ -v    # Run tests
```

**React:**
```bash
make format                              # Format code
npm run lint -- --max-warnings=0         # Check linting
npm test                                 # Run tests
```

### Pre-Commit Checklist
```bash
# 1. Format
make format

# 2. Test
make test

# 3. Check linting
# Python: black . -l 79 --check
# React: npm run lint -- --max-warnings=0

# 4. Stage and commit
git add .
git commit -m "Description

Fixes #123"

# 5. Push and watch CI
git push
```

## Resources

- **Main CLAUDE.md**: `/PolicyEngine/CLAUDE.md`
- **Python Style**: PEP 8, Black documentation
- **React Style**: Airbnb React/JSX Style Guide
- **Testing**: pytest documentation, Jest/RTL documentation
- **Writing Style**: See policyengine-writing-skill for blog posts, PR descriptions, and documentation

## Examples

See PolicyEngine repositories for examples of standard-compliant code:
- **policyengine-us**: Python package standards
- **policyengine-app**: React app standards
- **givecalc**: Streamlit app standards
- **crfb-tob-impacts**: Analysis repository standards
