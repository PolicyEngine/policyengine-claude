---
name: policyengine-design
description: |
  PolicyEngine design system — tokens, typography, colors, charts, and branding for all project types.
  Triggers: "brand colors", "design tokens", "PolicyEngine colors", "typography", "font", "color palette", "CSS variables", "design system", "branding guidelines"
---

# PolicyEngine design system

Single source of truth for PolicyEngine's visual identity. Design tokens are defined as CSS custom properties in `@policyengine/ui-kit/theme.css`. Every frontend project imports this single CSS file.

**When to use which format:**

| Context | Approach | Example |
|---------|----------|---------|
| **React components** | Tailwind semantic classes | `className="bg-primary text-foreground"` |
| **Brand palette** | Tailwind direct classes | `className="bg-teal-500 text-gray-600"` |
| **Recharts (SVG)** | CSS vars directly in fill/stroke | `fill="var(--chart-1)"` |
| **Inline styles** | CSS vars | `style={{ color: "var(--primary)" }}` |
| **Python (Plotly)** | Hex with CSS var comment | `TEAL = "#319795"  # --chart-1` |
| **`<meta>` tags, static HTML** | Hex values with CSS var name in comment | `content="#319795"` |

Python has no CSS runtime, so hex values are acceptable — but always comment with the CSS var name so values stay traceable to the design system.

## The ui-kit theme

**Install:**
```bash
bun install @policyengine/ui-kit
```

**Import the theme CSS in your `globals.css`:**
```css
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

The first line enables Tailwind v4 utilities. The second provides all PE design tokens, `@theme` configuration, and base styles. Both are required — see `policyengine-ui-kit-consumer-skill` for details.

**Source:** `PolicyEngine/policyengine-ui-kit/src/theme/tokens.css`

The theme CSS has three layers:
1. **`:root`** — shadcn/ui semantic variables (`--primary`, `--background`, `--chart-1`, etc.)
2. **`@theme inline`** — Bridges `:root` vars to Tailwind utilities (`bg-primary`, `text-foreground`)
3. **`@theme`** — Brand palette (`bg-teal-500`, `text-gray-600`), font sizes, spacing, breakpoints

## Colors

### Primary — teal

| Token | Hex | Tailwind class | Usage |
|-------|-----|---------------|-------|
| `teal-500` | `#319795` | `bg-teal-500` | **Main brand color** — charts, highlights |
| `teal-400` | `#38B2AC` | `bg-teal-400` | Lighter interactive elements |
| `teal-600` | `#2C7A7B` | `bg-teal-600` / `bg-primary` | Hover state, buttons |
| `teal-700` | `#285E61` | `bg-teal-700` | Active/pressed state |
| `teal-50` | `#E6FFFA` | `bg-teal-50` | Tinted backgrounds |
| `teal-800` | `#234E52` | `bg-teal-800` | Dark text on light teal |

### Semantic (shadcn/ui)

| Role | CSS variable | Tailwind class | Hex |
|------|-------------|---------------|-----|
| Primary | `--primary` | `bg-primary` | `#2C7A7B` |
| Background | `--background` | `bg-background` | `#FFFFFF` |
| Foreground | `--foreground` | `text-foreground` | `#000000` |
| Muted | `--muted` | `bg-muted` | `#F2F4F7` |
| Muted foreground | `--muted-foreground` | `text-muted-foreground` | `#6B7280` |
| Border | `--border` | `border-border` | `#E2E8F0` |
| Destructive | `--destructive` | `bg-destructive` | `#EF4444` |
| Card | `--card` | `bg-card` | `#FFFFFF` |
| Ring | `--ring` | `ring-ring` | `#319795` |

### Charts

| CSS variable | Tailwind class | Hex | Usage |
|-------------|---------------|-----|-------|
| `--chart-1` | `fill-chart-1` | `#319795` | Primary series (teal) |
| `--chart-2` | `fill-chart-2` | `#0EA5E9` | Secondary series (blue) |
| `--chart-3` | `fill-chart-3` | `#285E61` | Tertiary series (dark teal) |
| `--chart-4` | `fill-chart-4` | `#026AA2` | Quaternary series (dark blue) |
| `--chart-5` | `fill-chart-5` | `#6B7280` | Quinary series (gray) |

### Additional semantic colors

| Color | Hex | Tailwind class |
|-------|-----|---------------|
| Success | `#22C55E` | `text-success` / `bg-success` |
| Error | `#EF4444` | `text-destructive` / `bg-destructive` |
| Warning | `#FEC601` | `text-warning` / `bg-warning` |
| Info | `#1890FF` | `text-info` / `bg-info` |

### Gray scale

| Token | Hex | Tailwind class |
|-------|-----|---------------|
| `gray-50` | `#F9FAFB` | `bg-gray-50` |
| `gray-100` | `#F2F4F7` | `bg-gray-100` |
| `gray-200` | `#E2E8F0` | `bg-gray-200` |
| `gray-500` | `#6B7280` | `text-gray-500` |
| `gray-600` | `#4B5563` | `text-gray-600` |
| `gray-700` | `#344054` | `text-gray-700` |

## Typography

### Font families

**Two font families only: Inter + JetBrains Mono.** No serif fonts, no Roboto, no Public Sans.

| Context | Font | CSS variable | Tailwind |
|---------|------|-------------|----------|
| **Everything** (UI, charts, blog, tools) | Inter | `--font-sans` | `font-sans` |
| **Code** | JetBrains Mono | `--font-mono` | `font-mono` |

**Loading Inter:**
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Font sizes

| Tailwind class | Size | Usage |
|---------------|------|-------|
| `text-xs` | 12px | Small labels, captions |
| `text-sm` | 14px | Body text, form labels |
| `text-base` | 16px | Large body text |
| `text-lg` | 18px | Subheadings |
| `text-xl` | 20px | Section titles |
| `text-2xl` | 24px | Page titles |
| `text-3xl` | 28px | Large headings |

### Sentence case

All UI text uses sentence case — capitalize only the first word and proper nouns.

- "Your saved policies" not "Your Saved Policies"
- "Tax liability by income" not "Tax Liability by Income"
- Proper nouns stay capitalized: "Child Tax Credit", "PolicyEngine", "California"

## Spacing

Standard Tailwind spacing classes (`p-4`, `gap-2`, `m-6`) use the default Tailwind scale. Named spacing tokens:

| Token | Value | Tailwind class |
|-------|-------|---------------|
| Header | 58px | `h-header` |
| Sidebar | 280px | `w-sidebar` |
| Content | 976px | `max-w-content` |

### Border radius

| Tailwind class | Value |
|---------------|-------|
| `rounded-sm` | 4px |
| `rounded-md` | 6px |
| `rounded-lg` | 8px |

## Chart branding

### Recharts (React tools)

```tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

<BarChart data={data}>
  <XAxis dataKey="name" style={{ fontFamily: "var(--font-sans)" }} />
  <YAxis style={{ fontFamily: "var(--font-sans)" }} />
  <Tooltip separator=": " />
  <Bar dataKey="value" fill="var(--chart-1)" />
</BarChart>
```

SVG `fill` and `stroke` attributes accept `var()` directly — no helper function needed.

### Plotly (Python)

```python
import plotly.graph_objects as go

TEAL = "#319795"  # --chart-1
CHART_FONT = "Inter"
LOGO_URL = "https://raw.githubusercontent.com/PolicyEngine/policyengine-app-v2/main/app/public/assets/logos/policyengine/teal.png"

def format_fig(fig):
    fig.update_layout(
        font=dict(family=CHART_FONT, color="black", size=14),
        plot_bgcolor="white",
        paper_bgcolor="white",
        template="plotly_white",
        height=600,
        width=800,
        margin=dict(l=60, r=40, t=40, b=60),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color="rgba(0,0,0,0)"),
    )
    fig.add_layout_image(dict(
        source=LOGO_URL,
        xref="paper", yref="paper",
        x=1.0, y=-0.10,
        sizex=0.10, sizey=0.10,
        xanchor="right", yanchor="bottom",
    ))
    return fig
```

### Chart color conventions

| Meaning | CSS variable | Hex |
|---------|-------------|-----|
| Positive / bonus / gains | `--chart-1` | `#319795` |
| Negative / penalty / losses | `--chart-5` or `--destructive` | `#6B7280` or `#EF4444` |
| Neutral / baseline | `--border` | `#E2E8F0` |
| Multi-series | `--chart-1` through `--chart-5` | See chart table above |

**Inverted metrics (taxes):** When a positive delta means bad (higher taxes), use `invertDelta` logic to show "Penalty" label and swap colors.

### Chart typography

- **Axis labels and titles:** `var(--font-sans)`, 14px
- **Tick labels:** `var(--font-sans)`, 12px
- **Legend:** `var(--font-sans)`, horizontal, above chart

## Logos

All logo files in `policyengine-app-v2/app/public/assets/logos/policyengine/`:

| File | Background | Format |
|------|-----------|--------|
| `teal.png` / `teal.svg` | Light | Wide |
| `teal-square.png` / `teal-square.svg` | Light | Square (for chart watermarks) |
| `white.png` / `white.svg` | Dark | Wide |
| `white-square.svg` | Dark | Square |

**Raw URL for charts:**
```
https://raw.githubusercontent.com/PolicyEngine/policyengine-app-v2/main/app/public/assets/logos/policyengine/teal.png
```

## Using tokens by project type

| Project type | Token source | Font setup |
|-------------|-------------|------------|
| **Standalone tool** | `@import "@policyengine/ui-kit/theme.css"` | Google Fonts: Inter |
| **app-v2** | `import { colors } from '@/designTokens'` | Built-in (Mantine + Inter) |
| **Python chart** | Hardcode or load `tokens.json` from `@policyengine/design-system` | Inter for Plotly |
| **Blog HTML** | Hardcode from token values | Google Fonts: Inter |

## Accessibility

- Teal `#319795` on white passes WCAG AA for large text (3.8:1)
- `text-foreground` (`#000000`) on white passes AAA (21:1)
- `text-muted-foreground` (`#6B7280`) on white passes AA (4.6:1)
- Never rely on color alone — use labels, patterns, or position to convey meaning
- Ensure chart data series are distinguishable in grayscale

## Related skills

- `policyengine-interactive-tools-skill` — Building standalone tools that use these tokens
- `policyengine-vercel-deployment-skill` — Deploying standalone tools
- `policyengine-app-skill` — app-v2 development
- `policyengine-writing-skill` — Content style (complements visual style)
