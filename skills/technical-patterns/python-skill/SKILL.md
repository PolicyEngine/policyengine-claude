---
name: python
description: |
  ALWAYS LOAD THIS SKILL before setting up any Python environment or installing packages.
  Defines the standard: uv, Python 3.13, uv pip install, .venv at project root.
  Triggers: "set up python", "install python", "create a venv", "virtual environment",
  "pip install", "install packages", "uv pip", "uv venv", "python version",
  "VIRTUAL_ENV", "venv conflict", "which python", "activate", "deactivate",
  "run the script", "run with uv", "uv run", "pyproject.toml", "install dependencies",
  "install requirements", "install the package", "editable install", "pip install -e",
  "latest package", "latest version", "current version", "newest version".
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

### Verifying latest package versions

If the user asks for the "latest", "current", or "newest" version of a Python
package, verify it from PyPI immediately before installing or pinning it.
Do not treat search snippets, local installed versions, lockfiles, stale docs,
or repo dependency constraints as proof of latest.

```bash
export PACKAGE=policyengine

# Authoritative PyPI metadata.
python - <<'PY'
import json
import os
import urllib.request

package = os.environ["PACKAGE"]
with urllib.request.urlopen(
    f"https://pypi.org/pypi/{package}/json",
    timeout=20,
) as response:
    print(json.load(response)["info"]["version"])
PY

# Cross-check available versions when pip can reach PyPI.
python -m pip index versions "$PACKAGE"
```

Then install the exact verified version and confirm the resolved distribution:

```bash
VERSION=1.2.3
uv pip install "${PACKAGE}==${VERSION}"

python - <<'PY'
from importlib import metadata
import os

package = os.environ["PACKAGE"]
print(f"{package}=={metadata.version(package)}")
direct_url = metadata.distribution(package).read_text("direct_url.json")
if direct_url:
    print(direct_url)
PY
```

For extras, query the base distribution and pin the extra install to that same
version, for example `uv pip install "policyengine[us]==4.14.2"`.

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
