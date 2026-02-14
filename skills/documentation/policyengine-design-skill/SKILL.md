---
name: policyengine-design
description: PolicyEngine design system — tokens, typography, colors, charts, and branding for all project types
---

# PolicyEngine design system

Single source of truth for PolicyEngine's visual identity. All tokens live in `@policyengine/design-system` (npm). Every project — app-v2, standalone tools, charts, Streamlit — should reference these values rather than hardcoding hex codes.

## The design system package

**Install:**
```bash
npm install @policyengine/design-system
```

**Three export formats:**

| Format | Import | Use case |
|--------|--------|----------|
| TypeScript | `import { colors } from '@policyengine/design-system/tokens'` | app-v2, any TS/JS project |
| JSON | `import tokens from '@policyengine/design-system/tokens.json'` | Python scripts, config files |
| CSS | `import '@policyengine/design-system/tokens.css'` | Standalone tools, plain HTML |

**CDN (no install):**
```html
<link rel="stylesheet" href="https://unpkg.com/@policyengine/design-system/dist/tokens.css">
```

**Source:** `PolicyEngine/policyengine-app-v2/packages/design-system/`

## Colors

### Primary — teal

| Token | Hex | Usage |
|-------|-----|-------|
| `primary.500` | `#319795` | **Main brand color** — buttons, links, active states |
| `primary.400` | `#38B2AC` | Lighter interactive elements |
| `primary.600` | `#2C7A7B` | Hover state |
| `primary.700` | `#285E61` | Active/pressed state |
| `primary.50` | `#E6FFFA` | Tinted backgrounds |
| `primary.800` | `#234E52` | Dark text on light teal |

CSS: `var(--pe-color-primary-500)` through `var(--pe-color-primary-900)`

### Gray

| Token | Hex | Usage |
|-------|-----|-------|
| `gray.50` | `#F9FAFB` | Subtle backgrounds |
| `gray.100` | `#F2F4F7` | Card backgrounds |
| `gray.200` | `#E2E8F0` | Borders, dividers |
| `gray.500` | `#6B7280` | Secondary text |
| `gray.600` | `#4B5563` | Chart secondary series |
| `gray.700` | `#344054` | Dark UI text |

### Blue (accent)

| Token | Hex | Usage |
|-------|-----|-------|
| `blue.500` | `#0EA5E9` | Informational highlights |
| `blue.700` | `#026AA2` | Chart secondary series |

### Semantic

| Color | Hex | CSS variable | Usage |
|-------|-----|-------------|-------|
| Success | `#22C55E` | `--pe-color-success` | Positive changes, gains |
| Error | `#EF4444` | `--pe-color-error` | Negative changes, losses |
| Warning | `#FEC601` | `--pe-color-warning` | Cautions, alerts |
| Info | `#1890FF` | `--pe-color-info` | Informational |

### Text

| Token | Hex | CSS variable |
|-------|-----|-------------|
| `text.primary` | `#000000` | `--pe-color-text-primary` |
| `text.secondary` | `#5A5A5A` | `--pe-color-text-secondary` |
| `text.tertiary` | `#9CA3AF` | `--pe-color-text-tertiary` |

### Background

| Token | Hex | CSS variable |
|-------|-----|-------------|
| `background.primary` | `#FFFFFF` | `--pe-color-bg-primary` |
| `background.secondary` | `#F5F9FF` | `--pe-color-bg-secondary` |
| `background.tertiary` | `#F1F5F9` | `--pe-color-bg-tertiary` |

### Legacy colors (deprecated)

These appear in older projects. Migrate to the values above.

| Old | Hex | Replacement |
|-----|-----|-------------|
| `TEAL_ACCENT` | `#39C6C0` | `primary.500` (`#319795`) |
| `BLUE_PRIMARY` | `#2C6496` | `blue.700` (`#026AA2`) |
| `DARK_GRAY` | `#616161` | `text.secondary` (`#5A5A5A`) |

## Typography

### Font families

| Context | Font | CSS variable |
|---------|------|-------------|
| **UI / standalone tools / charts** | Inter | `--pe-font-family-primary`, `--pe-font-family-chart` |
| **Long-form prose (blog, research)** | Roboto Serif | `--pe-font-family-prose` |
| **Body text (app-v2)** | Roboto | `--pe-font-family-body` |
| **Code** | JetBrains Mono | `--pe-font-family-mono` |

**Key rule: Inter for everything interactive — UI, charts, and tools.** Roboto Serif is reserved for long-form written content (blog posts, research articles). Serif fonts should never appear in buttons, form labels, chart labels, headings, or navigation.

**Loading fonts:**
```html
<!-- Inter — UI, charts, and interactive tools -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<!-- Roboto Serif — only needed for blog/research long-form content -->
<link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Font sizes

| Token | Size | Usage |
|-------|------|-------|
| `xs` | 12px | Small labels, captions |
| `sm` | 14px | Body text, form labels |
| `base` | 16px | Large body text |
| `lg` | 18px | Subheadings |
| `xl` | 20px | Section titles |
| `2xl` | 24px | Page titles |
| `3xl` | 28px | Large headings |

### Sentence case

All UI text uses sentence case — capitalize only the first word and proper nouns.

- "Your saved policies" not "Your Saved Policies"
- "Tax liability by income" not "Tax Liability by Income"
- Proper nouns stay capitalized: "Child Tax Credit", "PolicyEngine", "California"

## Spacing

| Token | Value | CSS variable |
|-------|-------|-------------|
| `xs` | 4px | `--pe-space-xs` |
| `sm` | 8px | `--pe-space-sm` |
| `md` | 12px | `--pe-space-md` |
| `lg` | 16px | `--pe-space-lg` |
| `xl` | 20px | `--pe-space-xl` |
| `2xl` | 24px | `--pe-space-2xl` |
| `3xl` | 32px | `--pe-space-3xl` |
| `4xl` | 48px | `--pe-space-4xl` |

### Border radius

| Token | Value | CSS variable |
|-------|-------|-------------|
| `sm` | 4px | `--pe-radius-sm` |
| `md` | 6px | `--pe-radius-md` |
| `lg` | 8px | `--pe-radius-lg` |

## Chart branding

### Plotly (Python)

```python
import plotly.graph_objects as go

# Import from tokens.json or hardcode
TEAL = "#319795"
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

### Recharts (React standalone tools)

```jsx
import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

<BarChart data={data}>
  <XAxis dataKey="name" style={{ fontFamily: "Inter" }} />
  <YAxis style={{ fontFamily: "Inter" }} />
  <Tooltip />
  <Bar dataKey="value" fill="#319795" />
</BarChart>
```

### Chart color conventions

| Meaning | Color | Hex |
|---------|-------|-----|
| Positive / bonus / gains | Teal | `#319795` |
| Negative / penalty / losses | Gray or red | `#4B5563` or `#EF4444` |
| Neutral / baseline | Light gray | `#E2E8F0` |
| Multi-series | Series array | `#319795`, `#0EA5E9`, `#285E61`, `#026AA2`, `#6B7280` |

**Inverted metrics (taxes):** When a positive delta means bad (higher taxes), use `invertDelta` logic to show "Penalty" label and swap colors.

### Chart typography

- **Axis labels and titles:** Inter, 14px
- **Tick labels:** Inter, 12px
- **Legend:** Inter, horizontal, above chart

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

## Streamlit apps

```toml
# .streamlit/config.toml
[theme]
base = "light"
primaryColor = "#319795"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#E6FFFA"
textColor = "#000000"

[client]
toolbarMode = "minimal"
```

## Using tokens by project type

| Project type | Token source | Font setup |
|-------------|-------------|------------|
| **app-v2** | `import { colors } from '@/designTokens'` | Built-in (Mantine + Inter) |
| **Standalone tool** | `@import tokens.css` or CDN link | Google Fonts: Inter |
| **Python chart** | Hardcode or load `tokens.json` | Inter for Plotly |
| **Streamlit** | `.streamlit/config.toml` | Default sans-serif |
| **Blog HTML** | Hardcode from token values | Google Fonts: Roboto |

## Accessibility

- Teal `#319795` on white passes WCAG AA for large text (3.8:1)
- `text.primary` (`#000000`) on white passes AAA (21:1)
- `text.secondary` (`#5A5A5A`) on white passes AA (7.4:1)
- Never rely on color alone — use labels, patterns, or position to convey meaning
- Ensure chart data series are distinguishable in grayscale

## Related skills

- `policyengine-interactive-tools-skill` — Building standalone tools that use these tokens
- `policyengine-vercel-deployment-skill` — Deploying standalone tools
- `policyengine-app-skill` — app-v2 development
- `policyengine-writing-skill` — Content style (complements visual style)
