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

## Report Format

```
## Architecture Compliance Report

### Summary
- PASS: X/5 checks
- FAIL: Y/5 checks

### Results

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Tailwind CSS v4 | PASS/FAIL | ... |
| 2 | Next.js App Router | PASS/FAIL | ... |
| 3 | ui-kit integration | PASS/FAIL | ... |
| 4 | Package manager | PASS/FAIL | ... |
| 5 | Tailwind classes used | PASS/FAIL | ... |

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
