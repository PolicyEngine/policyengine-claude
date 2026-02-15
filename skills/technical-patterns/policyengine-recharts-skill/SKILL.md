---
name: policyengine-recharts
description: Recharts chart patterns, formatting, and styling for PolicyEngine apps
---

# PolicyEngine Recharts charts

Use this skill when creating or modifying charts in PolicyEngine applications. PolicyEngine favors **Recharts** over Plotly for frontend charts due to its dramatically smaller bundle size and React-native SVG rendering.

## Why Recharts

- **85% smaller bundle**: Recharts ~120 KB vs Plotly.js ~3+ MB gzipped
- **React-native**: SVG components, no external library injection
- **SSR-friendly**: Works with Next.js and Vite SSR
- **Tree-shakeable**: Import only what you use

## Installation

```bash
npm install recharts
```

Do NOT install `plotly.js` or `react-plotly.js` for new projects.

## Common imports

```typescript
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ReferenceDot, ReferenceLine, ResponsiveContainer, Label,
} from "recharts";
```

## Nice axis ticks (CRITICAL)

Recharts' default tick generation produces ugly non-round numbers (e.g., $6,000, $28,000, $51,000). This is a known long-standing issue (recharts/recharts#2140, #777, #1164).

**Always use explicit ticks with a `niceTicks()` helper:**

```typescript
/**
 * Compute nice round tick values for a chart axis starting at 0.
 */
function niceTicks(dataMax: number, targetCount: number = 5): number[] {
  if (dataMax <= 0) return [0];
  const rawStep = dataMax / targetCount;
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const normalized = rawStep / magnitude;

  let niceStep: number;
  if (normalized <= 1) niceStep = 1 * magnitude;
  else if (normalized <= 2) niceStep = 2 * magnitude;
  else if (normalized <= 2.5) niceStep = 2.5 * magnitude;
  else if (normalized <= 5) niceStep = 5 * magnitude;
  else niceStep = 10 * magnitude;

  const niceMax = Math.ceil(dataMax / niceStep) * niceStep;
  const ticks: number[] = [];
  for (let v = 0; v <= niceMax; v += niceStep) {
    ticks.push(Math.round(v * 1e10) / 1e10);
  }
  return ticks;
}
```

Apply to axes:

```tsx
const xMax = Math.max(...data.map(d => d.x));
const yMax = Math.max(...data.map(d => d.y));
const xTicks = niceTicks(xMax);
const yTicks = niceTicks(yMax);

<XAxis
  dataKey="x"
  type="number"
  domain={[0, xTicks[xTicks.length - 1]]}
  ticks={xTicks}
  tickFormatter={tickFormatter}
/>
<YAxis
  domain={[0, yTicks[yTicks.length - 1]]}
  ticks={yTicks}
  tickFormatter={tickFormatter}
/>
```

## Tooltip separator

Recharts default tooltip separator is ` : ` (with leading space). Always set `separator=": "` on the Tooltip component.

```tsx
<Tooltip
  contentStyle={TOOLTIP_STYLE}
  separator=": "
  formatter={(value: number) => [formatCurrency(value), "Label"]}
/>
```

## Standard chart template

```tsx
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Label, ReferenceDot,
} from "recharts";

interface DataPoint { x: number; y: number; }

export default function MyChart({ data, highlightX }: {
  data: DataPoint[];
  highlightX?: number;
}) {
  const fmt = (v: number) => v.toLocaleString("en-US", {
    style: "currency", currency: "USD", maximumFractionDigits: 0,
  });
  const xMax = Math.max(...data.map(d => d.x));
  const yMax = Math.max(...data.map(d => d.y));
  const xTicks = niceTicks(xMax);
  const yTicks = niceTicks(yMax);

  const highlightPoint = highlightX != null
    ? data.reduce((best, d) =>
        Math.abs(d.x - highlightX) < Math.abs(best.x - highlightX) ? d : best,
        data[0])
    : null;

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={data} margin={{ left: 20, right: 30, top: 10, bottom: 20 }}>
        <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" />
        <XAxis
          dataKey="x" type="number"
          domain={[0, xTicks[xTicks.length - 1]]} ticks={xTicks}
          tickFormatter={fmt}
          tick={{ fontFamily: "Inter, sans-serif", fontSize: 12 }}
        >
          <Label value="X axis" position="bottom" offset={0} />
        </XAxis>
        <YAxis
          domain={[0, yTicks[yTicks.length - 1]]} ticks={yTicks}
          tickFormatter={fmt}
          tick={{ fontFamily: "Inter, sans-serif", fontSize: 12 }}
        >
          <Label value="Y axis" angle={-90} position="insideLeft" offset={-5} />
        </YAxis>
        <Tooltip separator=": " formatter={(v: number) => [fmt(v), "Value"]} />
        <Line type="monotone" dataKey="y" stroke="#319795" strokeWidth={3} dot={false} />
        {highlightPoint && (
          <ReferenceDot x={highlightPoint.x} y={highlightPoint.y} r={6}
            fill="#1D4044" stroke="#1D4044" />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
```

## Chart types

| Use case | Component | Notes |
|----------|-----------|-------|
| Single line series | `LineChart` + `Line` | Most common |
| Multiple lines | `LineChart` + multiple `Line` | Different `stroke` colors |
| Filled area | `AreaChart` + `Area` | Good for cumulative/stacked |
| Stacked areas | `ComposedChart` + multiple `Area` | Set `fillOpacity={1}` |
| Bar chart | `BarChart` + `Bar` | Use `fill` not `stroke` |
| Mixed line + area | `ComposedChart` | Combine `Line` and `Area` |

## PolicyEngine styling

```typescript
// Colors (from @policyengine/design-system or hardcoded)
const TEAL_PRIMARY = "#319795";   // Primary series
const DARK_TEAL = "#1D4044";     // Reference dots
const GRID_COLOR = "#E2E8F0";    // Grid lines
const TEAL_LIGHT = "rgba(49, 151, 149, 0.15)";  // Light fill
const TEAL_MEDIUM = "rgba(49, 151, 149, 0.35)"; // Medium fill

// Font
const CHART_FONT = {
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontSize: 12,
};

// Tooltip
const TOOLTIP_STYLE = {
  background: "#fff",
  border: "1px solid #E2E8F0",
  borderRadius: 6,
  padding: "8px 12px",
};
```

## Key rules

1. **Always use `niceTicks()`** - never rely on Recharts auto-tick generation
2. **Always set `domain={[0, max]}`** - axes must start at 0
3. **Always set `type="number"` on XAxis** when using numeric data keys
4. **Always set `separator=": "`** on Tooltip
5. **Always wrap in `ResponsiveContainer`** with explicit height
6. **Use `dot={false}`** on Line components for clean curves with many data points
7. **Use `ReferenceDot`** to highlight the user's current selection
8. **Teal (#319795) is the primary chart color** - matches PolicyEngine brand
9. **Negative currency: sign before symbol** - Always format as `-$31`, never `$-31`

## Currency formatting

**Never manually concatenate currency symbols** (`` `$${value}` ``). Use `Intl.NumberFormat` with `style: 'currency'`, which handles negative sign placement correctly.

```typescript
// WRONG — produces "$-31"
const fmt = (v: number) => `$${v.toLocaleString()}`;

// CORRECT — produces "-$31" (Intl handles sign placement)
const fmt = (v: number) => v.toLocaleString("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
});
```

In policyengine-app-v2, use `formatParameterValue()` from `@/utils/chartValueUtils` or `formatCurrency()` from `@/utils/formatters` — both use `Intl.NumberFormat` internally.
