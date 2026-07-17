---
description: Write unit tests for source files, matching the target repo's observed test conventions
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# Write unit tests

Write well-structured unit tests that match the conventions the target repository
**actually uses** — discover them from existing tests, never impose an external template.

**Important:** This command is for frontend apps, APIs, SDKs, and standalone tools. It is
NOT for country model packages (`policyengine-us`, `policyengine-uk`, etc.), which use
YAML-based tests — for those, load the `policyengine-model-development` skill
(references/tests.md) and use the `test-creator` agent instead.

## Step 1: Identify target files

Ask the user which file(s) to test. If none specified, ask:

> Which source file(s) should I write tests for?

Read each source file thoroughly before writing any tests. Understand:
- All exported functions, classes, components, and their signatures
- Happy path behavior
- Error handling and edge cases
- Dependencies that need mocking

## Step 2: Detect the framework and the repo's real conventions

| Indicator | Framework |
|---|---|
| `vitest` in package.json | Vitest |
| `pytest` in pyproject.toml | pytest |
| `jest` in package.json | Jest (legacy repos) |

Then read 2-3 existing test files near your target and copy their observed conventions:
directory layout, file naming, describe/test phrasing, mock style, and any shared
test-utils imports. In policyengine-app-v2, for example, tests live under
`app/src/tests/` as `Name.test.ts(x)` — plain describe/test names, no
given/when/then scaffolding, no separate fixtures tree. Other repos differ; the
existing tests are the spec. If a project-level test CLAUDE.md or config exists, it
overrides everything here.

## Step 3: Write test files

Place and name new tests exactly as the repo's existing tests do. Whatever the naming
style, every test file must cover:

- Happy path
- Edge cases (zero, empty, null, boundary values)
- Expected error/failure paths
- Component tests: user-visible behavior (render output, interactions), not implementation details

Extract shared constants/mocks into the repo's established pattern (inline `const`s at
the top of the test file, or the repo's test-utils module — whichever neighbors use).

## Step 4: Run only the files you wrote

```bash
# Vitest
bunx vitest run path/to/file1.test.ts path/to/file2.test.ts

# pytest
uv run pytest path/to/test_file1.py path/to/test_file2.py -v
```

Fix any failures. Re-run only the failing files until all pass.

## Step 5: Format and typecheck only changed files

```bash
# TypeScript
bunx tsc --noEmit
bunx eslint path/to/file.test.ts --fix

# Python
uv run ruff format path/to/test_file.py
uv run ruff check path/to/test_file.py --fix
```

**NEVER run the full test suite, full linter, or full formatter unless the user explicitly
asks.** Only operate on files you wrote or modified.

## Step 6: Report results

Summarize what was written:

| Source file | Test file | Tests | Status |
|---|---|---|---|
| `lib/api/client.ts` | `src/tests/unit/lib/api/client.test.ts` | 8 | Passing |

Include the test output showing all tests passing.
