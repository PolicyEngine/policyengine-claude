---
name: python
description: Python environment setup and package management for PolicyEngine projects — always use uv, Python 3.13, and uv pip install
triggers:
  - "set up python"
  - "install python"
  - "python environment"
  - "virtual environment"
  - "venv"
  - "pip install"
  - "install packages"
  - "uv"
  - "python version"
  - "create environment"
---

# Python Environment — PolicyEngine Standard

All PolicyEngine Python work uses **uv** with **Python 3.13** and a local `.venv`.

## Required tools

- [`uv`](https://docs.astral.sh/uv/) — fast Python package and project manager
- Python 3.13 (installed/managed via uv)

Install uv if not present:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Creating a new environment

Always create a `.venv` at the project root using Python 3.13:

```bash
uv venv --python 3.13
source .venv/bin/activate
```

On Windows:

```bash
uv venv --python 3.13
.venv\Scripts\activate
```

---

## Installing packages

Always use `uv pip install`, never bare `pip install`:

```bash
# Install a package
uv pip install policyengine

# Install from requirements file
uv pip install -r requirements.txt

# Install the current project in editable mode
uv pip install -e .

# Install with extras
uv pip install -e ".[dev]"
```

---

## Running Python

After activating the venv, run Python normally:

```bash
python script.py
python -m pytest
```

Or run without activating using uv:

```bash
uv run python script.py
uv run pytest
```

---

## Checking the environment

```bash
# Confirm Python version (should be 3.13.x)
python --version

# Confirm uv is being used
which pip   # should point to .venv
uv pip list
```

---

## Common patterns

### New repo setup

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Adding a dependency to pyproject.toml, then syncing

```bash
# Edit pyproject.toml to add the dependency, then:
uv pip install -e .
```

### Running tests

```bash
uv run pytest
# or after activating:
pytest
```

---

## Resolving venv conflicts

If you see a warning like:
```
warning: `VIRTUAL_ENV=/Users/.../.venv` does not match the project environment path `.venv` and will be ignored
```

This means a *different* venv is active (e.g. a global one at `~/.venv`). Fix with:

```bash
# Option 1: Deactivate and use uv run
deactivate
uv run python script.py

# Option 2: Use --active flag to force uv to use the active env
uv run --active python script.py

# Option 3: Activate the correct project venv explicitly
source /path/to/project/.venv/bin/activate
python script.py
```

**Do not** mix venvs between projects. Each project should have its own `.venv` at the repo root.

## Rules

- **Never** use `python -m venv` — always `uv venv`
- **Never** use bare `pip install` — always `uv pip install`
- **Always** target Python 3.13 (`--python 3.13`)
- **Always** create the venv at the project root as `.venv`
- Use `uv run <cmd>` as an alternative to activating the venv manually
- If a venv conflict warning appears, use `deactivate` then `uv run`
