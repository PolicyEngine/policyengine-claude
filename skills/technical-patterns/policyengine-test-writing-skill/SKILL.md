---
name: policyengine-test-writing
description: |
  This skill should be used when writing unit tests, integration tests, or test fixtures for
  PolicyEngine frontend apps, APIs, SDKs, and standalone tools. NOT for country model packages
  (policyengine-us, policyengine-uk, etc.) — those use YAML-based tests with their own conventions.
  Covers the Given-When-Then naming convention, fixture extraction, edge case coverage, and the
  rule that only modified test files should be run.
  Triggers: "write tests", "add tests", "unit test", "test file", "test coverage", "write a test for",
  "test this function", "test this component", "given when then", "test fixtures", "mock setup",
  "edge cases", "test naming", "test convention"
---

# PolicyEngine Test Writing

Standard conventions for writing tests in PolicyEngine frontend apps, APIs, SDKs, and standalone tools.
These rules apply to every language and framework (Vitest, pytest, etc.) unless a project-specific
override exists.

## Country model packages — use different conventions

**Do NOT apply this skill to country model packages** (`policyengine-us`, `policyengine-uk`,
`policyengine-canada`, etc.). Those repos use YAML-based tests with entirely different structure,
naming, and tooling. For country packages, use these instead:

- **`policyengine-testing-patterns-skill`** (`skills/technical-patterns/policyengine-testing-patterns-skill/SKILL.md`) — YAML test structure, naming conventions (`variable_name.yaml`, `integration.yaml`), period handling, error margins, and quality standards
- **`test-creator` agent** (`agents/country-models/test-creator.md`) — Automated agent that creates comprehensive YAML integration tests for government benefit program implementations

Country model tests are `.yaml` files that live alongside the variables they test, not `.test.ts` or
`.test.py` files in a separate `tests/` directory.

## Core Principles

### 1. Given-When-Then Naming

Every test name follows the pattern `test__given_X_condition__then_Y_occurs`:

```typescript
// TypeScript / Vitest
test("test__given_valid_income__then_tax_is_calculated", () => { ... });
test("test__given_negative_income__then_error_is_thrown", () => { ... });
test("test__given_zero_children__then_ctc_is_zero", () => { ... });
```

```python
# Python / pytest
def test__given_valid_income__then_tax_is_calculated():
    ...
def test__given_negative_income__then_error_is_thrown():
    ...
```

Inside the test body, organize code into three clearly commented sections:

```typescript
test("test__given_user_clicks_submit__then_form_is_submitted", async () => {
  // Given
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  render(<Form onSubmit={onSubmit} />);

  // When
  await user.click(screen.getByRole("button", { name: /submit/i }));

  // Then
  expect(onSubmit).toHaveBeenCalledOnce();
});
```

### 2. One Test File Per Source File

Each source file gets exactly one corresponding test file named `test_FILENAME`:

| Source file | Test file |
|---|---|
| `utils/formatCurrency.ts` | `tests/unit/utils/test_formatCurrency.test.ts` |
| `components/MetricCard.tsx` | `tests/unit/components/test_MetricCard.test.tsx` |
| `lib/api/client.ts` | `tests/unit/lib/api/test_client.test.ts` |
| `services/simulation.py` | `tests/unit/services/test_simulation.py` |

The test file mirrors the source directory structure under a `tests/` root.

### 3. Fixtures Live Separately

All mocks, setup code, patches, constants, and test data must be extracted to a fixture file with the same name in a `fixtures/` directory:

```
tests/
├── fixtures/
│   ├── utils/
│   │   └── test_formatCurrency.ts    ← mocks, constants, helpers
│   ├── components/
│   │   └── test_MetricCard.ts
│   └── lib/
│       └── api/
│           └── test_client.ts
├── unit/
│   ├── utils/
│   │   └── test_formatCurrency.test.ts   ← imports from fixtures
│   ├── components/
│   │   └── test_MetricCard.test.tsx
│   └── lib/
│       └── api/
│           └── test_client.test.ts
```

**What goes in fixtures:**
- Mock data objects and factory functions
- Descriptive constants (no magic numbers in tests)
- `vi.fn()` / `MagicMock` setup helpers
- Patch targets and mock response builders
- Shared `beforeEach` / `afterEach` setup functions

**What stays in the test file:**
- `describe` / `test` blocks
- The Given-When-Then logic
- `expect` / `assert` statements

Import everything from the fixture:

```typescript
import {
  VALID_HOUSEHOLD,
  EMPTY_HOUSEHOLD,
  mockApiSuccess,
  mockApiError,
  EXPECTED_TAX_AMOUNT,
} from "@/tests/fixtures/lib/api/test_client";
```

### 4. Test Edge Cases and Failure Paths

Every test file must cover, at minimum:

- **Happy path**: Normal inputs produce expected outputs
- **Boundary values**: Zero, empty string, empty array, min/max values
- **Error cases**: Invalid inputs, network failures, missing data
- **Null/undefined**: What happens with missing or nullable fields
- **Type coercion traps**: String "0" vs number 0, empty object vs null

Structure the `describe` block to make coverage obvious:

```typescript
describe("calculateTax", () => {
  // Happy path
  test("test__given_valid_income__then_correct_tax_returned", () => { ... });
  test("test__given_income_at_bracket_boundary__then_correct_bracket_applied", () => { ... });

  // Edge cases
  test("test__given_zero_income__then_zero_tax", () => { ... });
  test("test__given_negative_income__then_throws_error", () => { ... });

  // Error handling
  test("test__given_api_timeout__then_error_propagated", () => { ... });
  test("test__given_malformed_response__then_fallback_used", () => { ... });
});
```

### 5. Run Only What Changed

After writing or modifying test files, run **only** those specific tests — never the entire suite:

```bash
# TypeScript / Vitest — run specific test file(s)
bunx vitest run tests/unit/utils/test_formatCurrency.test.ts

# Python / pytest — run specific test file(s)
pytest tests/unit/variables/test_income.py -v
```

After tests pass, run formatters and typecheckers **only on modified files**:

```bash
# TypeScript — typecheck and lint only changed files
bunx tsc --noEmit
bunx eslint tests/unit/utils/test_formatCurrency.test.ts tests/fixtures/utils/test_formatCurrency.ts

# Python — format and lint only changed files
black tests/unit/variables/test_income.py tests/fixtures/variables/test_income.py
ruff check tests/unit/variables/test_income.py tests/fixtures/variables/test_income.py
```

**Never run the full test suite or full linter unless explicitly asked.** Large codebases take minutes to lint/test; running everything wastes time and produces noise unrelated to the changes.

## Framework-Specific Notes

### Vitest (TypeScript / React)

```typescript
import { describe, test, expect, vi, beforeEach } from "vitest";
```

- Use `vi.fn()` for mocks, `vi.mock()` for module mocks
- Use `vi.clearAllMocks()` in `beforeEach`
- For React components, prefer accessibility selectors (`getByRole`, `getByLabelText`) over test IDs
- Use `userEvent.setup()` for user interactions (not `fireEvent`)
- Use `waitFor` for async state updates

### pytest (Python)

```python
import pytest
from unittest.mock import MagicMock, patch
```

- Use `@pytest.fixture` for setup, import from fixture files
- Use `@pytest.mark.parametrize` for data-driven tests
- Use `pytest.raises(ExceptionType)` for error assertions
- Mark slow tests with `@pytest.mark.slow`

## What to Test

- Public API surface (exported functions, component props, class methods)
- State transitions and side effects
- Data transformations and calculations
- Error handling and recovery paths
- Boundary conditions and edge cases

## What NOT to Test

- Third-party library internals (Recharts rendering, Mantine components, pandas operations)
- Private implementation details that may change
- CSS/styling (unless testing conditional class application)
- Simple pass-through getters with no logic

## Detailed Reference

For fixture best practices, mock patterns, and accessibility selector priority, consult:
- **`references/fixture-patterns.md`** — Comprehensive fixture organization and mock examples
