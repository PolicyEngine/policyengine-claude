---
name: policyengine-standards
description: |
  PolicyEngine coding standards, formatters, CI requirements, and development best practices.
  Triggers: "CI failing", "linting", "formatting", "before committing", "PR standards", "code style", "ruff formatter", "prettier", "pre-commit"
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

1. **Write tests first** (TDD - see below)
2. **Format code**: `make format` or language-specific formatter
3. **Run tests**: `make test` to ensure all tests pass
4. **Check linting**: Ensure no linting errors
5. **Use config files**: Prefer config files over environment variables
6. **Reference issues**: Include "Fixes #123" in commit message

## Creating Pull Requests

### The CI Waiting Problem

**Common failure pattern:**
```
User: "Create a PR and mark it ready when CI passes"
Claude: "I've created the PR as draft. CI will take a while, I'll check back later..."
[Chat ends - Claude never checks back]
Result: PR stays in draft, user has to manually check CI and mark ready
```

### Solution: Use /create-pr Command

**When creating PRs, use the /create-pr command:**

```bash
/create-pr
```

**This command:**
- ✅ Creates PR as draft
- ✅ Actually waits for CI (polls every 15 seconds)
- ✅ Marks ready when CI passes
- ✅ Reports failures with details
- ✅ Handles timeouts gracefully

**Why this works:**
The command contains explicit polling logic that Claude executes, so it actually waits instead of giving up.

### If /create-pr is Not Available

**If the command isn't installed, implement the pattern directly:**

```bash
# 1. Create PR as draft
# CRITICAL: Use --repo flag to create PR in upstream repo from fork
gh pr create --repo PolicyEngine/policyengine-us --draft --title "Title" --body "Body"
PR_NUMBER=$(gh pr view --json number --jq '.number')

# 2. Wait for CI (ACTUALLY WAIT - don't give up!)
POLL_INTERVAL=15
ELAPSED=0

while true; do  # No timeout - wait as long as needed
  CHECKS=$(gh pr checks $PR_NUMBER --json status,conclusion)
  TOTAL=$(echo "$CHECKS" | jq '. | length')
  COMPLETED=$(echo "$CHECKS" | jq '[.[] | select(.status == "COMPLETED")] | length')

  echo "[$ELAPSED s] CI: $COMPLETED/$TOTAL completed"

  if [ "$COMPLETED" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
    FAILED=$(echo "$CHECKS" | jq '[.[] | select(.conclusion == "FAILURE")] | length')
    if [ "$FAILED" -eq 0 ]; then
      echo "✅ All CI passed! Marking ready..."
      gh pr ready $PR_NUMBER
      break
    else
      echo "❌ CI failed. PR remains draft."
      gh pr checks $PR_NUMBER
      break
    fi
  fi

  sleep $POLL_INTERVAL
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

# Important: No timeout! Population simulations can take 30+ minutes.
```

**CRITICAL:** Never say "I'll check back later" — the chat session ends. Always use the polling loop above to actually wait. Default to creating PRs as draft; only create as ready when user explicitly requests it or CI is already verified.

## Test-Driven Development (TDD)

PolicyEngine follows TDD: write test first (RED), implement (GREEN), refactor. In multi-agent workflows, @test-creator and @rules-engineer work independently from the same regulations. See policyengine-core-skill for details.

**Example test:**
```python
def test_ctc_for_two_children():
    """Test CTC calculation for married couple with 2 children."""
    situation = create_married_couple(income_1=75000, income_2=50000, num_children=2, child_ages=[5, 8])
    sim = Simulation(situation=situation)
    ctc = sim.calculate("ctc", 2026)[0]
    assert ctc == 4400, "CTC should be $2,200 per child"
```

### Running Tests

```bash
# Python
make test                    # All tests
uv run pytest tests/ -v      # With uv
uv run pytest tests/test_credits.py::test_ctc -v  # Specific test

# React
make test                    # All tests
bun test -- --watch          # Watch mode
```

### Test quality

- Test behavior, not implementation; clear names; docstrings with regulation citations
- Avoid: testing private methods, mocking everything, magic numbers without explanation

## Python Standards

### Formatting
- **Formatter**: Ruff
- **Command**: `make format` or `ruff format .`
- **Check without changes**: `ruff format --check .`

```bash
# Format all Python files
make format

# Check if formatting is needed (CI-style)
ruff format --check .
```

### Code Style
- **Imports**: Grouped (stdlib, third-party, local) and alphabetized
- **Naming**: CamelCase for classes, snake_case for functions/variables
- **Type hints**: Recommended, especially for public APIs
- **Docstrings**: Required for public functions/classes (Google style)
- **Error handling**: Catch specific exceptions, not bare `except`

## JavaScript/React Standards

### Formatting
- **Formatters**: Prettier + ESLint
- **Command**: `bun run lint -- --fix && bunx prettier --write .`
- **CI Check**: `bun run lint -- --max-warnings=0`

```bash
# Format all files
make format

# Or manually
bun run lint -- --fix
bunx prettier --write .

# Check if formatting is needed (CI-style)
bun run lint -- --max-warnings=0
```

### Code Style
- Functional components only (no class components), hooks for state
- File naming: PascalCase.jsx for components, camelCase.js for utilities
- Use `src/config/environment.js` pattern for env config (not REACT_APP_ env vars)
- Keep components under 150 lines; extract complex logic into custom hooks

## Version Control Standards

### Changelog Management

**CRITICAL**: NEVER manually update `CHANGELOG.md`. Check which system the repo uses, then follow that system.

**How to tell which system a repo uses:**
1. Check if the repo has a `changelog.d/` directory -- if yes, use **towncrier** (new system)
2. If no `changelog.d/` but the repo uses `changelog_entry.yaml`, use the **legacy system**

#### New system: towncrier (`changelog.d/` fragments)

Used by: policyengine-claude, and newer repos with a `changelog.d/` directory.

```bash
echo "Description of change." > changelog.d/branch-name.added.md
```

Fragment filename format: `{name}.{type}.md`
Types: `added` (minor), `changed` (patch), `fixed` (patch), `removed` (minor), `breaking` (major)

GitHub Actions runs `towncrier build` on merge to compile fragments into CHANGELOG.md.

#### Legacy system: `changelog_entry.yaml`

Used by: policyengine-us, policyengine-uk, and other country model repos.

Create `changelog_entry.yaml` at repository root:
```yaml
- bump: patch  # or minor, major
  changes:
    added:
    - Description of new feature
    fixed:
    - Description of bug fix
```

GitHub Actions automatically updates `CHANGELOG.md` and `changelog.yaml` on merge.

**DO NOT (either system):**
- Run `make changelog` manually during PR creation
- Commit `CHANGELOG.md` in your PR
- Modify main changelog files directly

### Git workflow and common pitfalls

See the parent `PolicyEngine/CLAUDE.md` for full git workflow, branch naming, commit message format, and common AI pitfalls (file versioning, formatter not run, env vars, wrong Python version). Key points:

- Create branches on PolicyEngine repos, NOT forks (forks fail CI)
- Always run `make format` before committing
- Never create versioned files (app_v2.py, component_new.jsx)
- Include "Fixes #123" in PR descriptions

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

## CI stability

See `PolicyEngine/CLAUDE.md` for full CI stability details (fork failures, rate limits, linting). Quick fixes: use `make format` before committing, use `uv run pytest` not bare `pytest`, create branches on PolicyEngine repos not forks.

## Repo rename checklist

When renaming a PolicyEngine repository, references to the old name are often hardcoded across the org. Follow this checklist to avoid broken links, builds, and embeds.

### 1. Search the org for all references

```bash
# Find every file in the org that mentions the old repo name
gh api "/search/code?q=org:PolicyEngine+OLD_REPO_NAME" --paginate | jq '.items[] | {repo: .repository.full_name, path: .path}'
```

Review every result -- some will be docs/changelogs (safe to update later), others will break builds if not updated before the rename.

### 2. Common places where repo names are hardcoded

| Location | What to look for | Example |
|----------|-----------------|---------|
| **GitHub Actions workflows** | `PUBLIC_URL`, checkout paths, artifact names | `PUBLIC_URL: https://policyengine.github.io/OLD_NAME` |
| **Iframe embeds in policyengine-app-v2** | `src` URLs in page components | `app/src/pages/*.jsx` referencing `OLD_NAME.github.io` |
| **README badges and links** | Shield.io badges, repo links | `![CI](https://github.com/PolicyEngine/OLD_NAME/actions/...)` |
| **package.json / pyproject.toml** | `name`, `repository`, `homepage` fields | `"name": "old-name"` |
| **GitHub Pages URLs** | Any URL containing `policyengine.github.io/OLD_NAME` | Links in docs, blog posts, other READMEs |
| **CLAUDE.md** | Repo-specific instructions that reference the old name | Paths, URLs, skill references |
| **Import paths (Python)** | Package name derived from repo name | `from old_name import ...` |
| **Vercel / deployment configs** | Project names, domain aliases | `vercel.json`, Vercel dashboard settings |
| **policyengine-claude skills** | Skill files that reference the repo | Links in `SKILL.md` files across this plugin |

### 3. Cross-repo coordination

If the renamed repo is embedded in another site (e.g., via iframe or GitHub Pages), **both repos need updates**:

1. **In the renamed repo**: Update `PUBLIC_URL` and any self-referencing URLs in workflows, configs, and docs.
2. **In the embedding repo**: Update iframe `src` URLs, links, and any CI that depends on the old name.
3. **Deploy order**: Push the renamed repo's changes first (so the new URL is live), then update the embedding repo.

### 4. After renaming

- GitHub automatically redirects the old repo URL, but **GitHub Pages URLs do not redirect** -- `policyengine.github.io/old-name` will 404.
- Verify GitHub Pages is re-enabled under the new repo settings if it was active.
- Run the org-wide search again to catch anything you missed:
  ```bash
  gh api "/search/code?q=org:PolicyEngine+OLD_REPO_NAME" --paginate | jq '.total_count'
  ```
- Update any external references (blog posts on policyengine.org, Notion docs, etc.) that link to the old GitHub Pages URL.

## Resources

- **Main CLAUDE.md**: `/PolicyEngine/CLAUDE.md`
- **Python Style**: PEP 8, Ruff documentation
- **React Style**: Airbnb React/JSX Style Guide
- **Testing**: pytest documentation, Jest/RTL documentation
- **Writing Style**: See policyengine-writing-skill for blog posts, PR descriptions, and documentation

## Examples

See PolicyEngine repositories for examples of standard-compliant code:
- **policyengine-us**: Python package standards
- **policyengine-app**: React app standards
- **crfb-tob-impacts**: Analysis repository standards
