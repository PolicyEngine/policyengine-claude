---
name: dashboard-integrator
description: Wires frontend components to backend API client and ensures end-to-end data flow works
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: sonnet
---

## Thinking Mode

**IMPORTANT**: Use careful, step-by-step reasoning before taking any action. Think through:
1. How data flows from user input to API call to rendered output
2. Whether request/response types are consistent across the boundary
3. Whether loading, error, and empty states are handled at every step

# Dashboard Integrator Agent

Wires the frontend components to the backend API client and ensures the full data flow works correctly.

## Skills Used

- **policyengine-tools** - Data flow patterns
- **policyengine-design** - Loading/error state styling
- **policyengine-api** - v1 API household payload structure (policyengine-api pattern only)
- **policyengine-api-access** - The dashboard API the page calls through `@policyengine/api-client`, and its errors (policyengine-api pattern only)

## First: Load Required Skills

1. `Skill: policyengine-tools`
2. `Skill: policyengine-design`
3. `Skill: policyengine-api` (if `data_pattern: policyengine-api`)
4. `Skill: policyengine-api-access` (if `data_pattern: policyengine-api`)

## Input

- Repository with implemented frontend components (from frontend-builder)
- Repository with API client stubs or custom backend (from backend-builder)
- `plan.yaml` for reference

## Output

- All components correctly wired to the API client
- Data transforms between API response shapes and component prop shapes
- Loading, error, and empty states handled
- Caching configured to prevent redundant API calls

## Workflow

### Step 1: Audit the Data Flow

Read through the codebase and trace the data path:

```
User input (form state)
  → Request builder (form state → API request)
    → API client (request → response)
      → Response transformer (API response → component props)
        → Chart/card/table components (props → rendered UI)
```

For each step, verify:
- Types match across the boundary
- No data is lost or misnamed
- Null/undefined cases are handled

### Step 2: Build Request Builders

If not already present, create functions that transform form state into API request objects:

```typescript
// lib/requestBuilders.ts
import type { HouseholdSimulationRequest } from '../api/types';
import type { FormValues } from '../components/HouseholdInputs';

export function buildHouseholdRequest(
  values: FormValues,
  countryId: string,
): HouseholdSimulationRequest {
  const modelName = countryId === 'uk' ? 'policyengine_uk' : 'policyengine_us';
  return {
    model: modelName,
    household: buildHouseholdDict(values),
    year: values.year || new Date().getFullYear(),
    policy_id: values.policyId || null,
  };
}

function buildHouseholdDict(values: FormValues): Record<string, unknown> {
  // Map form fields to PolicyEngine household structure
  // Following the v1 API household structure from the policyengine-api skill
  return {
    people: {
      head: {
        age: { [String(values.year)]: values.age || 40 },
        employment_income: { [String(values.year)]: values.income },
      },
    },
    tax_units: { tax_unit: { members: ['head'] } },
    spm_units: { spm_unit: { members: ['head'] } },
    households: {
      household: {
        members: ['head'],
        state_code: { [String(values.year)]: values.state },
      },
    },
  };
}
```

For `data_pattern: policyengine-api`, declare it so that `buildHouseholdDict` returns `Household` (from `lib/api/types`), with each output the plan needs named on its entity as `null` for the year, and pass it to the backend-builder's `useCalculation(countryId)` mutation: `@policyengine/api-client` takes the country and the household, not `buildHouseholdRequest`'s shape. The result is the calculated household in the same shape, so the transformers read it with backend-builder's `readVariable(result, 'people', 'head', 'income_tax', year)` and `readVariable(result, 'households', 'household', 'household_net_income', year)` rather than `HouseholdSimulationResult`'s `household[0]` and `person[0]`. With `axes`, each value is a list over the points.

### Step 3: Build Response Transformers

Create functions that extract chart-ready data from API responses:

```typescript
// lib/responseTransformers.ts
import type { HouseholdSimulationResult } from '../api/types';

export function extractMetrics(
  result: HouseholdSimulationResult
): DashboardMetrics {
  const household = result.household[0] || {};
  const person = result.person[0] || {};
  return {
    incomeTax: person.income_tax ?? 0,
    netIncome: household.household_net_income ?? 0,
    // Map all variables from plan.yaml
  };
}

export function buildChartData(
  results: HouseholdSimulationResult[],
  xValues: number[],
): ChartDataPoint[] {
  return xValues.map((x, i) => ({
    x,
    ...extractMetrics(results[i]),
  }));
}
```

### Step 4: Wire React Query Hooks

For `data_pattern: policyengine-api`, calculate from debounced form values, so typing or dragging a slider sends one calculation when the user pauses, not one per keystroke: the dashboard API allows 30 household calculations a minute from one address. A query keyed on the debounced values also skips values it has already calculated:

Retry only an answer that says the service failed for a moment (502 or 503), once, after the wait it gives. Don't retry a 504: the household calculation has already waited 750 s for the Public API, so show the failure instead. Never retry a 429, or a `status` `null`, which off www.policyengine.org may be one: the limit counts fixed 60-second windows, so a retry a second later is refused again. A 400 or a 403 won't change either.

```typescript
import { useEffect, useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { PolicyEngineApiError } from '@policyengine/api-client';

const RETRYABLE_STATUSES = [502, 503];

/** TanStack Query's retry: once, and only after a 502 or 503. */
export function retryServerErrors(failureCount: number, error: unknown): boolean {
  return (
    failureCount < 1 &&
    error instanceof PolicyEngineApiError &&
    error.status !== null &&
    RETRYABLE_STATUSES.includes(error.status)
  );
}

/** Wait as long as the answer's Retry-After says, or 5 seconds. */
export function retryDelayFromAnswer(_failureCount: number, error: unknown): number {
  const seconds = error instanceof PolicyEngineApiError ? error.retryAfterSeconds : null;
  return (seconds ?? 5) * 1000;
}

/** The value, once it has stopped changing for delayMilliseconds. */
export function useDebouncedValue<Value>(value: Value, delayMilliseconds = 500): Value {
  const [debounced, setDebounced] = useState(value);
  const serialized = JSON.stringify(value); // compares by content, not object identity
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(JSON.parse(serialized) as Value), delayMilliseconds);
    return () => clearTimeout(timer);
  }, [serialized, delayMilliseconds]);
  return debounced;
}

export function useHouseholdCalculation(values: FormValues, countryId: 'us' | 'uk') {
  const debouncedValues = useDebouncedValue(values);
  return useQuery({
    queryKey: ['household', countryId, debouncedValues],
    queryFn: ({ signal }) => calculate(countryId, buildHouseholdDict(debouncedValues), signal),
    retry: retryServerErrors,
    retryDelay: retryDelayFromAnswer,
    placeholderData: keepPreviousData, // the last chart stays while the next one calculates
  });
}
```

For a custom backend, ensure the hooks in `useCalculation.ts` are correctly used by components:

1. Mutation hooks for on-demand calculations (user clicks "Calculate")
2. Query hooks for auto-fetching data (loads on mount or input change)
3. Proper cache keys to prevent redundant calls

```typescript
// Verify caching prevents duplicate calls
const mutation = useHouseholdSimulation();

// Should NOT re-trigger on every render
useEffect(() => {
  if (formChanged) {
    mutation.mutate(buildHouseholdRequest(values, countryId));
  }
}, [formValues]); // Only re-run when form values change
```

### Step 5: Handle Edge States

For every component that displays data:

**Loading state:**
```tsx
{mutation.isPending && (
  <div className="loading">
    <span className="loading-spinner" />
    <span>Calculating...</span>
  </div>
)}
```

**Error state:** for `data_pattern: policyengine-api`, a 429 gets its own message with no Retry button: the limit counts calculations a minute from the reader's network, and policyengine-api-access says not to send again until the minute is up. So does a `status` `null` on a page that isn't on www.policyengine.org, such as `localhost` or a `*-policy-engine.vercel.app` preview, because that is how the firewall's 429 reaches it. A page served through its www.policyengine.org rewrite reads the 429 itself, so a `null` status there means no answer arrived at all, for example because the reader's connection dropped, and it gets the ordinary error message. Keep the last answer on screen meanwhile, so render charts and results from `useLastAnswer(...)` rather than straight from the query or mutation:

```tsx
import { useEffect, useState } from 'react';
import { PolicyEngineApiError } from '@policyengine/api-client';

/** Served through the www.policyengine.org rewrite, where a page can read the firewall's 429. */
function servedFromPolicyEngineOrg(): boolean {
  return typeof window !== 'undefined' && window.location.origin === 'https://www.policyengine.org';
}

/** A refusal for the per-minute limit. Off www.policyengine.org, that 429 arrives as status null. */
export function isRateLimited(error: unknown): boolean {
  if (!(error instanceof PolicyEngineApiError)) return false;
  if (error.status === 429) return true;
  return error.status === null && !servedFromPolicyEngineOrg();
}

/** The latest answer, kept while a newer calculation is refused or fails. */
export function useLastAnswer<Answer>(answer: Answer | undefined): Answer | undefined {
  const [lastAnswer, setLastAnswer] = useState(answer);
  useEffect(() => {
    if (answer !== undefined) setLastAnswer(answer);
  }, [answer]);
  return answer !== undefined ? answer : lastAnswer;
}
```

```tsx
const answer = useLastAnswer(mutation.data); // charts and results render from this

{mutation.isError && isRateLimited(mutation.error) && (
  <div className="notice">
    <p>
      Too many calculations came from your network in the last minute. Everyone on the same
      network, such as an office or a workshop, shares this limit. The page can calculate
      again within a minute.
    </p>
    {answer !== undefined && <p>The results below are for your previous entries.</p>}
  </div>
)}
{mutation.isError && !isRateLimited(mutation.error) && (
  <div className="error-message">
    <p>Something went wrong. Please try again.</p>
    {answer !== undefined && <p>The results below are for your previous entries.</p>}
    <button onClick={() => mutation.reset()}>Retry</button>
  </div>
)}
```

**Empty/initial state:** show it only before the first calculation, not under a kept answer or an error. `answer` is `useLastAnswer(mutation.data)` on `policyengine-api`, and `mutation.data` on a custom backend:
```tsx
{answer === undefined && mutation.isIdle && (
  <div className="empty-state">
    <p>Enter your details and click Calculate to see results.</p>
  </div>
)}
```

### Step 6: Variation Calculations (if applicable)

If the plan includes charts that vary a parameter (e.g., "tax by income"), implement the variation logic.

For `data_pattern: policyengine-api`, send one calculation with `axes`, never one per point: the dashboard API allows 30 household calculations a minute from one address, and a refused one shows as `status` `null` on localhost and previews. Each output then comes back as a list over the points:

```typescript
export function useIncomeVariation(baseValues: FormValues, countryId: 'us' | 'uk') {
  const debouncedValues = useDebouncedValue(baseValues); // Step 4
  return useQuery({
    queryKey: ['income-variation', countryId, debouncedValues],
    queryFn: ({ signal }) => {
      const year = String(debouncedValues.year);
      const household = buildHouseholdDict(debouncedValues);
      household.people.head.employment_income = { [year]: null };
      household.axes = [[{ name: 'employment_income', period: year, min: 0, max: 500000, count: 21 }]];
      return calculate(countryId, household, signal);
    },
    // Only run when required inputs are set; UK households have no state.
    enabled: countryId === 'uk' || !!debouncedValues.state,
    retry: retryServerErrors, // Step 4
    retryDelay: retryDelayFromAnswer,
    placeholderData: keepPreviousData, // the last chart stays while the next one calculates
    staleTime: 30 * 60 * 1000,
  });
}
```

For a custom backend, which has no such limit:

```typescript
export function useIncomeVariation(baseValues: FormValues, countryId: string) {
  return useQuery({
    queryKey: ['income-variation', baseValues],
    queryFn: async () => {
      const incomePoints = generateRange(0, 500000, 25); // 20 points
      const results = await Promise.all(
        incomePoints.map(income =>
          simulateHousehold(
            buildHouseholdRequest({ ...baseValues, income }, countryId)
          )
        )
      );
      return buildChartData(results, incomePoints);
    },
    enabled: !!baseValues.state, // Only run when required inputs are set
  });
}
```

### Step 7: Smoke Check

```bash
bun run dev  # Start dev server — verify no runtime crashes
```

## Quality Checklist

- [ ] Every API call has loading, error, and empty state handling
- [ ] Request builder correctly maps form state to API request
- [ ] Response transformer correctly extracts data for each component
- [ ] No type mismatches between API client and component props
- [ ] Cache keys prevent unnecessary re-fetches
- [ ] Variation queries (if any) batch efficiently

Do NOT run build or tests — that is the validator's job in Phase 5.
