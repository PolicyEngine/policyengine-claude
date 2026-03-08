# Fixture Patterns and Mock Best Practices

Detailed patterns for organizing test fixtures, writing descriptive mocks, and structuring test data.

## Fixture File Structure

Every test file has a corresponding fixture file. The fixture file exports everything the test needs except the test logic itself.

### TypeScript / Vitest Example

```
tests/
├── fixtures/
│   └── lib/
│       └── api/
│           └── test_client.ts
└── unit/
    └── lib/
        └── api/
            └── test_client.test.ts
```

**Fixture file** (`tests/fixtures/lib/api/test_client.ts`):

```typescript
import { vi } from "vitest";

// --- Constants ---

export const VALID_HOUSEHOLD_ID = "household-abc-123";
export const NON_EXISTENT_HOUSEHOLD_ID = "household-999-999";
export const MALFORMED_HOUSEHOLD_ID = "";

export const API_BASE_URL = "https://api.policyengine.org";

export const HTTP_STATUS = {
  OK: 200,
  BAD_REQUEST: 400,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
} as const;

// --- Mock Data ---

export const VALID_HOUSEHOLD_RESPONSE = {
  household_id: VALID_HOUSEHOLD_ID,
  country_id: "us",
  people: {
    adult: { age: { "2025": 30 }, employment_income: { "2025": 50000 } },
  },
};

export const EMPTY_HOUSEHOLD_RESPONSE = {
  household_id: VALID_HOUSEHOLD_ID,
  country_id: "us",
  people: {},
};

// --- Mock Builders ---

export function mockFetchSuccess(data: unknown) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: HTTP_STATUS.OK,
    json: vi.fn().mockResolvedValue(data),
  });
}

export function mockFetchError(status: number) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    statusText: status === HTTP_STATUS.NOT_FOUND ? "Not Found" : "Server Error",
  });
}

export function mockFetchNetworkError() {
  return vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
}

// --- Setup Helpers ---

export function setupFetchMock(mockFn: ReturnType<typeof vi.fn>) {
  global.fetch = mockFn;
}

export function teardownFetchMock() {
  vi.restoreAllMocks();
}
```

**Test file** (`tests/unit/lib/api/test_client.test.ts`):

```typescript
import { describe, test, expect, beforeEach, afterEach } from "vitest";
import { fetchHousehold } from "@/lib/api/client";
import {
  VALID_HOUSEHOLD_ID,
  NON_EXISTENT_HOUSEHOLD_ID,
  MALFORMED_HOUSEHOLD_ID,
  VALID_HOUSEHOLD_RESPONSE,
  HTTP_STATUS,
  mockFetchSuccess,
  mockFetchError,
  mockFetchNetworkError,
  setupFetchMock,
  teardownFetchMock,
} from "@/tests/fixtures/lib/api/test_client";

describe("fetchHousehold", () => {
  afterEach(() => teardownFetchMock());

  test("test__given_valid_id__then_household_returned", async () => {
    // Given
    setupFetchMock(mockFetchSuccess(VALID_HOUSEHOLD_RESPONSE));

    // When
    const result = await fetchHousehold(VALID_HOUSEHOLD_ID);

    // Then
    expect(result).toEqual(VALID_HOUSEHOLD_RESPONSE);
  });

  test("test__given_non_existent_id__then_error_thrown", async () => {
    // Given
    setupFetchMock(mockFetchError(HTTP_STATUS.NOT_FOUND));

    // When / Then
    await expect(fetchHousehold(NON_EXISTENT_HOUSEHOLD_ID)).rejects.toThrow();
  });

  test("test__given_network_failure__then_error_propagated", async () => {
    // Given
    setupFetchMock(mockFetchNetworkError());

    // When / Then
    await expect(fetchHousehold(VALID_HOUSEHOLD_ID)).rejects.toThrow("Failed to fetch");
  });

  test("test__given_empty_id__then_error_thrown", async () => {
    // Given / When / Then
    await expect(fetchHousehold(MALFORMED_HOUSEHOLD_ID)).rejects.toThrow();
  });
});
```

### Python / pytest Example

```
tests/
├── fixtures/
│   └── variables/
│       └── test_income.py
└── unit/
    └── variables/
        └── test_income.py
```

**Fixture file** (`tests/fixtures/variables/test_income.py`):

```python
import pytest
from unittest.mock import MagicMock

# --- Constants ---

STANDARD_INCOME = 50_000
ZERO_INCOME = 0
NEGATIVE_INCOME = -1_000
BRACKET_BOUNDARY_INCOME = 44_725  # 2024 22% bracket boundary

EXPECTED_TAX_AT_STANDARD = 6_307.50
EXPECTED_TAX_AT_ZERO = 0
EXPECTED_TAX_AT_BOUNDARY = 5_147.00

# --- Fixtures ---

@pytest.fixture
def mock_simulation():
    sim = MagicMock()
    sim.calculate.return_value = EXPECTED_TAX_AT_STANDARD
    return sim

@pytest.fixture
def household_with_income():
    return {
        "people": {"adult": {"employment_income": {"2025": STANDARD_INCOME}}},
        "tax_units": {"tax_unit": {"members": ["adult"]}},
    }
```

**Test file** (`tests/unit/variables/test_income.py`):

```python
import pytest
from tests.fixtures.variables.test_income import (
    STANDARD_INCOME,
    ZERO_INCOME,
    NEGATIVE_INCOME,
    BRACKET_BOUNDARY_INCOME,
    EXPECTED_TAX_AT_STANDARD,
    EXPECTED_TAX_AT_ZERO,
    EXPECTED_TAX_AT_BOUNDARY,
    mock_simulation,
    household_with_income,
)

class TestCalculateTax:
    def test__given_standard_income__then_correct_tax(self, mock_simulation):
        # Given
        mock_simulation.calculate.return_value = EXPECTED_TAX_AT_STANDARD

        # When
        result = mock_simulation.calculate("income_tax", 2025)

        # Then
        assert result == EXPECTED_TAX_AT_STANDARD

    def test__given_zero_income__then_zero_tax(self, mock_simulation):
        # Given
        mock_simulation.calculate.return_value = EXPECTED_TAX_AT_ZERO

        # When
        result = mock_simulation.calculate("income_tax", 2025)

        # Then
        assert result == EXPECTED_TAX_AT_ZERO

    @pytest.mark.parametrize("income,expected", [
        (STANDARD_INCOME, EXPECTED_TAX_AT_STANDARD),
        (ZERO_INCOME, EXPECTED_TAX_AT_ZERO),
        (BRACKET_BOUNDARY_INCOME, EXPECTED_TAX_AT_BOUNDARY),
    ])
    def test__given_various_incomes__then_correct_tax(self, income, expected):
        ...
```

## Descriptive Constants

Never use magic values in tests. Every literal should be a named constant from the fixture:

```typescript
// BAD — What do these mean?
const result = calculate("us", 50000, 2);

// GOOD — Self-documenting
import {
  TEST_COUNTRY_US,
  STANDARD_INCOME,
  TWO_CHILDREN,
} from "@/tests/fixtures/utils/test_calculate";

const result = calculate(TEST_COUNTRY_US, STANDARD_INCOME, TWO_CHILDREN);
```

## Grouping Constants

Organize related constants into typed objects:

```typescript
export const TEST_COUNTRIES = {
  US: "us",
  UK: "uk",
  CA: "ca",
} as const;

export const FILING_STATUS = {
  SINGLE: "single",
  MARRIED_JOINT: "married_filing_jointly",
  HEAD_OF_HOUSEHOLD: "head_of_household",
} as const;

export const INCOME_LEVELS = {
  ZERO: 0,
  POVERTY_LINE: 15_060,
  MEDIAN: 59_540,
  HIGH: 200_000,
  BRACKET_BOUNDARY_22: 44_725,
} as const;
```

## Mock Response Builders

Create reusable builders instead of inline mock objects:

```typescript
export function buildHousehold(overrides: Partial<Household> = {}): Household {
  return {
    country_id: "us",
    people: { adult: { age: { "2025": 30 } } },
    tax_units: { tax_unit: { members: ["adult"] } },
    ...overrides,
  };
}

export function buildApiResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(data),
  };
}
```

## React Component Fixtures

For React component tests, fixtures export props objects and render helpers:

```typescript
// fixtures/components/test_MetricCard.ts
import { vi } from "vitest";

export const DEFAULT_PROPS = {
  title: "Net income change",
  value: 1250,
  format: "currency" as const,
  delta: 5.2,
};

export const ZERO_VALUE_PROPS = {
  ...DEFAULT_PROPS,
  value: 0,
  delta: 0,
};

export const NEGATIVE_DELTA_PROPS = {
  ...DEFAULT_PROPS,
  value: -500,
  delta: -3.1,
};

export const LOADING_PROPS = {
  ...DEFAULT_PROPS,
  isLoading: true,
};

export const mockOnClick = vi.fn();
```

## Accessibility Selector Priority

When testing React components, prefer selectors that verify accessibility:

| Priority | Selector | Why |
|:---:|---|---|
| 1 | `getByRole("button", { name: /submit/i })` | Verifies element is an accessible button |
| 2 | `getByLabelText("Email address")` | Verifies form input has a label |
| 3 | `getByText("Welcome back!")` | Verifies visible content |
| 4 | `getByTestId("submit-btn")` | Last resort — no accessibility guarantee |

**Never use**: `getByClassName`, `getById`, `querySelector` — these test implementation details.
