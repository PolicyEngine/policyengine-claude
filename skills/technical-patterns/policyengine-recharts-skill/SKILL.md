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
bun install recharts
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

Recharts' default tick generation produces ugly non-round numbers. Since **v3.8.0**, Recharts has a built-in `niceTicks` prop that solves this natively.

**Always set `niceTicks="snap125"` on every `<XAxis>` and `<YAxis>`:**

```tsx
<XAxis
  dataKey="x"
  type="number"
  niceTicks="snap125"
  domain={["auto", "auto"]}
  tickFormatter={tickFormatter}
/>
<YAxis
  niceTicks="snap125"
  domain={["auto", "auto"]}
  tickFormatter={tickFormatter}
/>
```

The `snap125` algorithm snaps tick step sizes to **{1, 2, 2.5, 5} × 10^n**, producing human-friendly round labels like `0, 5, 10, 15, 20` instead of `0, 4, 8, 12, 16`. It may leave some blank space at chart edges — this is the correct trade-off for readability.

**Do NOT:**
- Use a custom `niceTicks()` helper function — the built-in prop replaces it
- Use `niceTicks` as a bare boolean or `niceTicks="auto"` — always specify `"snap125"` explicitly
- Manually compute ticks arrays — let Recharts handle it

**`niceTicks` enum values** (always use `"snap125"`):

| Value | Behavior | Use? |
|-------|----------|------|
| `"snap125"` | Snaps to {1,2,2.5,5} multiples — roundest labels | **Always use this** |
| `"adaptive"` | Space-efficient, less round labels | No |
| `"auto"` | Context-dependent, mirrors v2 behavior | No |
| `"none"` | No rounding, raw d3 ticks | No |

**Always pair with `domain={["auto", "auto"]}`** — the default domain `[0, 'auto']` clamps the minimum to 0, which breaks tick calculation for data that doesn't start at 0 (e.g., all-negative values).

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

SVG `fill` and `stroke` attributes accept `var()` directly -- no helper function is needed to resolve CSS custom properties. Use the shadcn/ui chart color variables (`--chart-1` through `--chart-5`) for series colors and standard semantic variables for UI elements:

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
  const highlightPoint = highlightX != null
    ? data.reduce((best, d) =>
        Math.abs(d.x - highlightX) < Math.abs(best.x - highlightX) ? d : best,
        data[0])
    : null;

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={data} margin={{ left: 20, right: 30, top: 10, bottom: 20 }}>
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
        <XAxis
          dataKey="x" type="number"
          niceTicks="snap125" domain={["auto", "auto"]}
          tickFormatter={fmt}
          tick={{ fontFamily: "var(--font-sans)", fontSize: 12 }}
        >
          <Label value="X axis" position="bottom" offset={0} />
        </XAxis>
        <YAxis
          niceTicks="snap125" domain={["auto", "auto"]}
          tickFormatter={fmt}
          tick={{ fontFamily: "var(--font-sans)", fontSize: 12 }}
        >
          <Label value="Y axis" angle={-90} position="insideLeft" offset={-5} />
        </YAxis>
        <Tooltip separator=": " formatter={(v: number) => [fmt(v), "Value"]} />
        <Line type="monotone" dataKey="y" stroke="var(--chart-1)" strokeWidth={3} dot={false} />
        {highlightPoint && (
          <ReferenceDot x={highlightPoint.x} y={highlightPoint.y} r={6}
            fill="var(--chart-3)" stroke="var(--chart-3)" />
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

Never hardcode hex colors in frontend chart code. Use CSS custom properties directly via `var()` in SVG attributes:

```typescript
// Chart series colors (shadcn/ui chart palette)
// Use these for data series — lines, areas, bars, dots
// --chart-1  Primary series (first line/bar)
// --chart-2  Secondary series
// --chart-3  Tertiary series / reference dots
// --chart-4  Fourth series
// --chart-5  Fifth series

// Semantic UI colors — use for chart chrome (grids, borders, backgrounds)
// --border       Grid lines, axis lines
// --background   Tooltip background
// --foreground   Axis labels, tick text
// --primary      Interactive UI elements (buttons, links)
// --font-sans    Font family

// Usage in JSX — pass var() directly to SVG attributes:
<Line stroke="var(--chart-1)" />
<Area fill="var(--chart-2)" stroke="var(--chart-2)" />
<ReferenceDot fill="var(--chart-3)" stroke="var(--chart-3)" />
<CartesianGrid stroke="var(--border)" />

// Tooltip style object
const TOOLTIP_STYLE = {
  background: "var(--background)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  padding: "8px 12px",
};
```

See `policyengine-design-skill` for the full token reference.

## Key rules

1. **Always set `niceTicks="snap125"`** on every `<XAxis>` and `<YAxis>` — never omit it, never use the bare boolean or `"auto"`
2. **Always set `domain={["auto", "auto"]}`** — required for `niceTicks` to compute correct domains
3. **Always set `type="number"` on XAxis** when using numeric data keys
4. **Always set `separator=": "`** on Tooltip
5. **Always wrap in `ResponsiveContainer`** with explicit height
6. **Use `dot={false}`** on Line components for clean curves with many data points
7. **Use `ReferenceDot`** to highlight the user's current selection
8. **Use CSS variables for chart colors** -- pass `var(--chart-1)` through `var(--chart-5)` directly to SVG `fill`/`stroke` attributes; never hardcode hex values
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

In policyengine-app-v2, use `formatParameterValue()` from `@/utils/chartValueUtils` or `formatCurrency()` from `@/utils/formatters` -- both use `Intl.NumberFormat` internally.
