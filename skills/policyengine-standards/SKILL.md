---
name: policyengine-standards
description: |
  PolicyEngine coding standards, environment setup, formatters, changelog, and CI requirements
  across every repo — what makes a PR pass and merge cleanly. Covers uv + .venv, ruff, bun,
  towncrier changelog fragments, the "wait for CI" PR pattern, and the repo-rename checklist.
  Triggers: "CI failing", "linting", "formatting", "before committing", "PR standards",
  "code style", "ruff", "prettier", "changelog", "towncrier", "create a PR", "wait for CI",
  "rename a repo", "set up the venv", "which Python version".
metadata:
  category: process
---

# PolicyEngine development standards

Load this before committing to, reviewing, or setting up any PolicyEngine repository. It
encodes the org conventions that CI enforces — the things a frontier model would otherwise
guess wrong. For prose style (blog posts, PR bodies, docs) see the policyengine-writing skill.

## Environment: uv + a local .venv

All PolicyEngine Python work uses [`uv`](https://docs.astral.sh/uv/) with a `.venv` at the
repository root. Never use bare `pip`, and never run bare `python`/`pytest`.

```bash
uv venv                       # creates ./.venv (uv picks the interpreter from pyproject.toml)
uv pip install -e ".[dev]"    # editable install with dev extras
uv run pytest                 # run anything through uv so it uses ./.venv
```

- **Python version is per-repo — check `pyproject.toml`** (`requires-python`). The org spans
  the 3.13/3.14 era; there is no single global version. Do not downgrade a repo to satisfy a
  stale assumption, and do not hardcode a version across repos.
- `uv run <cmd>` guarantees the command runs in the repo's `.venv` with its locked deps. Bare
  `python script.py` / `pytest` is the most common cause of "works locally, fails in CI".
- Verifying "latest": if asked for the latest version of a package, read PyPI
  (`https://pypi.org/pypi/<pkg>/json` → `info.version`) immediately before pinning. Never
  infer "latest" from a lockfile, a local install, or search snippets.

## Documentation builds

Python docs use **Jupyter Book 2.0 (MyST-NB)** — build with `myst build docs`, never `jb build`
(that is Jupyter Book 1.x). Use MyST markdown syntax.

## Before committing — checklist

1. Write the test first (TDD, below).
2. Format: `make format` (or `uv run ruff format .` for Python, `bun run lint -- --fix && bunx prettier --write .` for JS).
3. Run tests: `make test` (or `uv run pytest`).
4. Add a changelog fragment (towncrier, below).
5. Reference the issue in the PR: "Fixes #123".

## Creating pull requests

### The CI waiting problem

**Common failure pattern:**
```
User: "Create a PR and mark it ready when CI passes"
Claude: "I've created the PR as draft. CI will take a while, I'll check back later..."
[Chat ends - Claude never checks back]
Result: PR stays in draft, user has to manually check CI and mark ready
```

### Solution: use the /create-pr command

When creating PRs, use the `/create-pr` command. It creates the PR as draft, actually waits
for CI (polls every 15 seconds), marks it ready when CI passes, and reports failures with
details. It works because the command carries explicit polling logic that Claude executes, so
it waits instead of giving up.

### If /create-pr is not available

Implement the polling pattern directly:

```bash
# 1. Create PR as draft. Create the branch ON the PolicyEngine repo, not a fork.
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
      echo "All CI passed. Marking ready..."
      gh pr ready $PR_NUMBER
      break
    else
      echo "CI failed. PR remains draft."
      gh pr checks $PR_NUMBER
      break
    fi
  fi

  sleep $POLL_INTERVAL
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done
```

**Never say "I'll check back later"** — the chat session ends. Default to draft PRs; mark ready
only when the user asks or CI is already verified green. Merge only after every check passes
and the PR is `MERGEABLE`.

## Test-driven development

PolicyEngine follows TDD: write the test (RED), implement (GREEN), refactor. In multi-agent
encoding workflows, test authoring and rule implementation proceed independently from the same
regulations so the test is not shaped to the implementation.

**Country models test with YAML integration cases**, not hand-built Python situations. A case
declares inputs and expected outputs against named variables; the runner builds the simulation:

```yaml
# policyengine_us/tests/.../ctc.yaml
- name: CTC for a married couple with two children
  period: 2026
  input:
    people:
      parent1: {age: 40, employment_income: 75_000}
      parent2: {age: 40, employment_income: 50_000}
      child1: {age: 5, is_tax_unit_dependent: true}
      child2: {age: 8, is_tax_unit_dependent: true}
    tax_units:
      tax_unit:
        members: [parent1, parent2, child1, child2]
        filing_status: JOINT
  output:
    ctc: 4_400   # $2,200 per child under post-OBBBA law in 2026
```

Run country-model YAML tests through the core test runner (this is what `make test` wraps):

```bash
uv run policyengine-core test policyengine_us/tests/policy/ -c policyengine_us
```

For non-model Python packages, write `pytest` tests under `tests/` mirroring the source layout;
run with `uv run pytest tests/ -v`. Test behavior, not implementation; give tests clear names
and docstrings citing the regulation. Do not assert magic numbers without a comment explaining
the source. For analysis-side calculations, drive them through the `policyengine` package (see
that skill) rather than reaching into a country package directly.

## Python standards

- **Formatter**: ruff, default settings — **88-character line length** (PolicyEngine does not
  set a custom width; do not reformat to 79). There is **no `black`** in the toolchain.
  - Format: `uv run ruff format .`
  - CI-style check: `uv run ruff format --check .`
- Imports grouped (stdlib, third-party, local) and alphabetized within groups.
- `snake_case` for functions/variables, `CamelCase` for classes.
- Type hints on public APIs; docstrings on public functions/classes; catch specific exceptions.
- One variable per file in country models (`variables/gov/...`), with statutory citations in
  comments. See the policyengine-model-development skill.

## JavaScript / React standards

New standalone tools and app-v2 use **bun** (`bun install`, `bun run`, `bunx`) — not npm/npx.

- Format: `bun run lint -- --fix && bunx prettier --write .`
- CI-style check: `bun run lint -- --max-warnings=0` (CI treats warnings as errors)
- Functional components with hooks only (no class components).
- PascalCase for component files, camelCase for utilities; keep components small and extract
  complex logic into hooks. See the policyengine-app skill for app-v2 specifics (ui-kit tokens,
  Vite `app/` + Next.js `website/`).

## Changelog: match the repo's mechanism

**Never edit `CHANGELOG.md` by hand.** Two live conventions:

- **Python repos (country models, core, policyengine.py, populace): towncrier.** Add a
  fragment under `changelog.d/`, commit it with your code; CI compiles fragments and bumps
  the version on merge. In these repos the old single-file format
  <!-- stale-ok -->
  (`changelog_entry.yaml`) is deprecated — do not recreate it.

  ```bash
  echo "Describe the change." > changelog.d/<branch-name>.<type>.md
  ```

  Fragment types: `added` (minor), `changed` (patch), `fixed` (patch), `removed` (minor),
  `breaking` (major). Do not run `make changelog` during PR creation, and do not commit
  `CHANGELOG.md` in your PR.

- **policyengine-app-v2** still appends user-facing lines to the rolling
  <!-- stale-ok -->
  `changelog_entry.yaml` at its root — that is the live convention there; follow it.

When in doubt, check which of `changelog.d/` or the yaml file exists at the repo root and
has recent commits.

## Git workflow

See the parent `PolicyEngine/CLAUDE.md` for the full workflow. Key points:

- **Branch on the PolicyEngine repo, not a fork** — fork PRs fail CI because they cannot access
  repository secrets (data/API tokens).
- Run `make format` (or the language formatter) before every commit.
- Never create versioned copies of files (`app_v2.py`, `Component_new.jsx`) — edit in place.
- Include "Fixes #123" in the PR description.

## Repo rename checklist

When renaming a PolicyEngine repository, references to the old name are hardcoded across the
org. Follow this to avoid broken links, builds, and embeds.

### 1. Search the org for all references

```bash
gh api "/search/code?q=org:PolicyEngine+OLD_REPO_NAME" --paginate | jq '.items[] | {repo: .repository.full_name, path: .path}'
```

Review every result — some are docs/changelogs (safe to update later), others break builds if
not updated before the rename.

### 2. Common places where repo names are hardcoded

| Location | What to look for | Example |
|----------|-----------------|---------|
| **GitHub Actions workflows** | `PUBLIC_URL`, checkout paths, artifact names | `PUBLIC_URL: https://policyengine.github.io/OLD_NAME` |
| **Iframe embeds in policyengine-app-v2** | `src` URLs in page components | components referencing `OLD_NAME.github.io` |
| **README badges and links** | Shield.io badges, repo links | `![CI](https://github.com/PolicyEngine/OLD_NAME/actions/...)` |
| **package.json / pyproject.toml** | `name`, `repository`, `homepage` fields | `"name": "old-name"` |
| **GitHub Pages URLs** | Any URL containing `policyengine.github.io/OLD_NAME` | Links in docs, blog posts, other READMEs |
| **CLAUDE.md** | Repo-specific instructions referencing the old name | Paths, URLs, skill references |
| **Import paths (Python)** | Package name derived from repo name | `from old_name import ...` |
| **Vercel / deployment configs** | Project names, domain aliases | `vercel.json`, Vercel dashboard settings |
| **policyengine-skills source** | Skill files referencing the repo | Links in `SKILL.md` files |

### 3. Cross-repo coordination

If the renamed repo is embedded in another site (iframe or GitHub Pages), **both repos need
updates**:

1. **In the renamed repo**: update `PUBLIC_URL` and self-referencing URLs in workflows, configs, docs.
2. **In the embedding repo**: update iframe `src` URLs, links, and any CI that depends on the old name.
3. **Deploy order**: push the renamed repo first (so the new URL is live), then the embedding repo.

### 4. After renaming

- GitHub redirects the old repo URL, but **GitHub Pages URLs do not redirect** —
  `policyengine.github.io/old-name` will 404.
- Verify GitHub Pages is re-enabled under the new repo settings if it was active.
- Re-run the org-wide search to catch anything missed:
  ```bash
  gh api "/search/code?q=org:PolicyEngine+OLD_REPO_NAME" --paginate | jq '.total_count'
  ```
- Update external references (policyengine.org posts, Notion, other READMEs) that link to the
  old GitHub Pages URL.

## Related skills

- **policyengine-writing** — prose style for PR bodies, blog posts, and docs.
- **policyengine-model-development** — country-model variable/parameter/test conventions.
- **policyengine-app** — app-v2 (ui-kit tokens, bun, Vite/Next layout) standards.
- **policyengine-plugin-maintenance** — standards for this skills repo and the Claude wrapper.
