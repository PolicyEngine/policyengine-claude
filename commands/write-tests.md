---
description: Write unit tests for source files using Given-When-Then conventions, fixture extraction, and edge case coverage
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# Write unit tests

Write well-structured unit tests following PolicyEngine conventions. Load the `policyengine-test-writing` skill first for full details on naming, fixtures, and edge cases.

**Important:** This command is for frontend apps, APIs, SDKs, and standalone tools. It is NOT for country model packages (`policyengine-us`, `policyengine-uk`, etc.), which use YAML-based tests. For country packages, use the `policyengine-testing-patterns-skill` and the `test-creator` agent instead.

## Step 1: Identify target files

Ask the user which file(s) to test. If none specified, ask:

> Which source file(s) should I write tests for?

Read each source file thoroughly before writing any tests. Understand:
- All exported functions, classes, components, and their signatures
- Happy path behavior
- Error handling and edge cases
- Dependencies that need mocking

## Step 2: Detect the project's test framework

Look for existing test configuration:

```bash
# Check for vitest, pytest, jest, etc.
```

| Indicator | Framework |
|---|---|
| `vitest` in package.json | Vitest |
| `pytest` in pyproject.toml or requirements | pytest |
| `jest` in package.json | Jest |

Also find the existing test directory structure:

```bash
# Look for existing tests to match conventions
```

If a project-level test CLAUDE.md or test config exists, read it and follow any project-specific overrides (e.g., custom import paths like `@test-utils`).

## Step 3: Create fixture files

For each source file, create a fixture file first. The fixture file goes in `tests/fixtures/` mirroring the source directory structure, named `test_FILENAME` (same extension as the test file).

**Include in the fixture:**
- Descriptive constants for all test inputs (no magic numbers)
- Mock data objects representing realistic scenarios
- Mock builder functions (e.g., `mockFetchSuccess`, `mockApiError`)
- Setup/teardown helpers
- Variants for edge cases (empty, null, boundary, error)

**Example fixture layout:**
```
tests/fixtures/
└── lib/
    └── api/
        └── test_client.ts     ← constants, mocks, helpers
```

## Step 4: Write test files

Create test files in `tests/unit/` (or `tests/integration/` for integration tests), mirroring the source structure. Name them `test_FILENAME.test.{ts,tsx,py}`.

**Every test must:**
1. Be named `test__given_X_condition__then_Y_occurs`
2. Have three commented sections: `// Given`, `// When`, `// Then`
3. Import all data and mocks from the fixture file (nothing hardcoded inline)
4. Cover at minimum:
   - Happy path
   - Edge cases (zero, empty, null, boundary values)
   - Expected error/failure paths
   - One assertion per test when practical

**Structure:**
```typescript
describe("FunctionOrComponentName", () => {
  // Happy path
  test("test__given_valid_input__then_expected_output", () => { ... });

  // Edge cases
  test("test__given_empty_input__then_handles_gracefully", () => { ... });
  test("test__given_boundary_value__then_correct_behavior", () => { ... });

  // Error cases
  test("test__given_invalid_input__then_throws_error", () => { ... });
  test("test__given_network_failure__then_error_propagated", () => { ... });
});
```

## Step 5: Run only the files you wrote

After writing, run ONLY the test files you created or modified:

```bash
# Vitest
bunx vitest run path/to/test_file1.test.ts path/to/test_file2.test.ts

# pytest
pytest path/to/test_file1.py path/to/test_file2.py -v
```

Fix any failures. Re-run only the failing files until all pass.

## Step 6: Format and typecheck only changed files

After tests pass, run formatters and typecheckers on ONLY the files you wrote or modified (test files + fixture files):

```bash
# TypeScript
bunx tsc --noEmit
bunx eslint path/to/test_file.test.ts path/to/fixture_file.ts --fix

# Python
black path/to/test_file.py path/to/fixture_file.py
ruff check path/to/test_file.py path/to/fixture_file.py --fix
```

**NEVER run the full test suite, full linter, or full formatter unless the user explicitly asks.** Only operate on files you wrote or modified.

## Step 7: Report results

Summarize what was written:

| Source file | Test file | Fixture file | Tests | Status |
|---|---|---|---|---|
| `lib/api/client.ts` | `tests/unit/lib/api/test_client.test.ts` | `tests/fixtures/lib/api/test_client.ts` | 8 | Passing |

Include the test output showing all tests passing.
