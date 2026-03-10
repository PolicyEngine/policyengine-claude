---
name: dashboard-architecture-validator
description: Validates Tailwind v4, Next.js App Router, ui-kit integration, and package manager usage
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Dashboard Architecture Validator

Checks that the dashboard uses the correct framework, styling infrastructure, and package manager.

## Skills Used

- **policyengine-frontend-builder-spec-skill** — Authoritative spec to validate against

## First: Load Required Skills

1. `Skill: policyengine-frontend-builder-spec-skill`

After loading the skill, extract every MUST / MUST NOT statement and validate each one.

## Checks

### 1. Tailwind CSS v4

**Required:**
```bash
# globals.css has @import "tailwindcss"
grep -n '@import.*tailwindcss' app/globals.css

# globals.css imports ui-kit theme
grep -n '@policyengine/ui-kit/theme.css' app/globals.css

# tailwindcss in package.json
grep '"tailwindcss"' package.json
```

**Prohibited:**
```bash
# No tailwind.config.ts/js
test ! -f tailwind.config.ts && test ! -f tailwind.config.js

# No postcss.config
test ! -f postcss.config.js && test ! -f postcss.config.mjs

# No @tailwind directives
grep -rn '@tailwind' app/ --include='*.css'

# No CSS module files
find . -name '*.module.css' -not -path './node_modules/*' -not -path './.next/*'

# No plain CSS files besides globals.css
find . -name '*.css' -not -name 'globals.css' -not -path './node_modules/*' -not -path './.next/*'
```

### 2. Next.js App Router

**Required:**
```bash
ls app/layout.tsx
ls app/page.tsx
grep '"next"' package.json
```

**Prohibited:**
```bash
# No Vite
test ! -f vite.config.ts && test ! -f vite.config.js

# No Pages Router
test ! -d pages
```

### 3. ui-kit Integration

```bash
# In package.json
grep '@policyengine/ui-kit' package.json

# Actually imported in components
grep -rn "from '@policyengine/ui-kit'" app/ components/ --include='*.tsx' --include='*.ts'

# No CDN link for design-system
grep -rn 'unpkg.com/@policyengine/design-system' app/ --include='*.tsx'
```

### 4. Package Manager

```bash
# bun.lock exists
test -f bun.lock

# No package-lock.json
test ! -f package-lock.json
```

### 5. Tailwind Classes Used

```bash
# Verify className attributes exist in components
grep -rn 'className=' components/ app/ --include='*.tsx' | head -20
```

### 6. Modal Backend Structure (custom-modal only)

**Only run this check if `plan.yaml` has `data_pattern: custom-modal`.** Skip entirely for other patterns.

This validates the three-file backend structure that mirrors policyengine-api-v2's simulation service and prevents module-level import crash-loops.

**Required files:**
```bash
test -f backend/_image_setup.py && echo "PASS" || echo "FAIL: _image_setup.py missing"
test -f backend/app.py && echo "PASS" || echo "FAIL: app.py missing"
test -f backend/simulation.py && echo "PASS" || echo "FAIL: simulation.py missing"
test -f backend/modal_app.py && echo "PASS" || echo "FAIL: modal_app.py missing"
```

**_image_setup.py must have NO module-level policyengine/pydantic imports:**
```bash
grep -n '^from policyengine\|^import policyengine\|^from pydantic\|^import pydantic' backend/_image_setup.py
# Should find NOTHING — all imports must be inside function bodies
```

**app.py must have NO module-level policyengine/pydantic imports:**
```bash
grep -n '^from policyengine\|^import policyengine\|^from pydantic\|^import pydantic' backend/app.py
# Should find NOTHING — only `modal` at module level
```

**app.py must use .run_function for image snapshot:**
```bash
grep -n 'run_function' backend/app.py
# Should find the snapshot call
```

**simulation.py must have policyengine imports at module level (snapshotted):**
```bash
grep -n '^from policyengine\|^import policyengine' backend/simulation.py
# Should find at least one import
```

**Gateway must NOT include policyengine:**
```bash
grep -n 'policyengine' backend/modal_app.py
# Should find NOTHING — gateway is lightweight
```

## Report Format

```
## Architecture Compliance Report

### Summary
- PASS: X/6 checks (or X/5 if not custom-modal)
- FAIL: Y checks

### Results

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Tailwind CSS v4 | PASS/FAIL | ... |
| 2 | Next.js App Router | PASS/FAIL | ... |
| 3 | ui-kit integration | PASS/FAIL | ... |
| 4 | Package manager | PASS/FAIL | ... |
| 5 | Tailwind classes used | PASS/FAIL | ... |
| 6 | Modal backend structure | PASS/FAIL/SKIP | ... |

### Failures (if any)

#### Check N: [name]
- **Found**: [violation]
- **Expected**: [correct approach]
- **Fix**: [specific action]
```

## DO NOT

- Fix any issues — report only
- Modify any files
- Maintain a hardcoded list of spec requirements — derive them from the loaded skill
