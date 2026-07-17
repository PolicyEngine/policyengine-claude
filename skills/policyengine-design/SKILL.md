---
name: policyengine-design
description: |
  Load when styling any PolicyEngine frontend — choosing colors, fonts, spacing, chart colors,
  or consuming @policyengine/ui-kit. Covers the two-import globals.css, the three-layer
  theme.css (@theme vs @theme inline), verified 0.4.0 token values and component exports, the
  dark-mode contract, and the Plotly chart house style.
  Triggers: PolicyEngine colors, design tokens, brand palette, teal, CSS variables, theme.css,
  ui-kit, @theme, @theme inline, dark mode, chart colors, fill var(--chart-1), Plotly format_fig,
  never hardcode hex, DashboardShell, Header.
  NOT for: multizone/deploy wiring (use policyengine-tools) or app-v2 internals (policyengine-app).
metadata:
  category: apps
---

# PolicyEngine design system

Design tokens live as CSS custom properties in **`@policyengine/ui-kit/theme.css`**. Every
frontend imports that one file. The canonical version is **`@policyengine/ui-kit ^0.4.0`** —
the version app-v2 pins. Ignore claims tied to 0.5/0.6/0.9; treat 0.4.0 as ground truth and
re-check `node_modules/@policyengine/ui-kit` when precision matters.

## Setup: the two imports

```css
/* globals.css — order matters; Tailwind must come first */
@import "tailwindcss";
@import "@policyengine/ui-kit/theme.css";
```

Next.js needs `postcss.config.mjs` = `{ plugins: { "@tailwindcss/postcss": {} } }` (install
`@tailwindcss/postcss` + `postcss`). A Vite app uses the `@tailwindcss/vite` plugin instead —
no PostCSS config. Do **not** add `postcss-import` or `autoprefixer` (`@tailwindcss/postcss`
handles both), and do **not** add a second `@import "tailwindcss"` (theme.css does not import
it). If the consumer's own utility classes go missing in a monorepo, scope source detection:
`@import "tailwindcss" source("./src");`.

## The three-layer theme.css

`theme.css` (source: ui-kit `src/theme/tokens.css`, vendored from design-system v0.3.0) has
three layers:

```
Layer 1  :root { --primary: #2C7A7B; --chart-1: #319795; ... }   raw shadcn/ui semantic values
Layer 2  @theme inline { --color-primary: var(--primary); }       bridge :root → Tailwind utilities
Layer 3  @theme { --color-teal-500: #319795; --text-sm: 14px; }   brand palette, fonts, sizes, spacing
```

### `@theme` vs `@theme inline` — the mechanism

- **`@theme inline`** keeps the `var()` reference, so the utility resolves it **at runtime**.
  Use it whenever a token points at a `:root` variable — that is what lets `bg-primary` follow
  a `.dark` override. All shadcn/ui semantic tokens use `@theme inline`.
- **`@theme`** bakes a **literal** value into the generated CSS at build time. Use it for the
  fixed brand palette (`teal-500` is always `#319795`), font sizes, spacing, breakpoints.

Getting these backwards is the classic bug: `@theme { --color-primary: var(--primary); }` bakes
the literal string `var(--primary)` and never re-resolves.

## Consuming tokens by context

| Context | How | Example |
|---|---|---|
| React (semantic) | Tailwind semantic class | `className="bg-primary text-foreground"` |
| React (brand) | Tailwind brand class | `className="bg-teal-500 text-gray-600"` |
| Recharts / SVG | `var()` directly in fill/stroke | `fill="var(--chart-1)"` |
| Inline style | `var()` | `style={{ color: "var(--primary)" }}` |
| Python / Plotly | hex + CSS-var comment | `TEAL = "#319795"  # --chart-1` |

Namespace → utility mapping (Tailwind v4): `--color-*` → `bg-*`/`text-*`/`border-*`/`fill-*`;
`--text-*` → font-size utilities; `--font-*` → `font-*`; `--radius-*` → `rounded-*`;
`--spacing-*` → `p-*`/`m-*`/`gap-*`/`w-*`/`h-*`; `--breakpoint-*` → `sm:`/`md:`/`lg:`.
**Never hardcode hex or font names** when a token exists.

## Colors (verified 0.4.0)

**Teal (brand):** 50 `#E6FFFA` · 100 `#B2F5EA` · 200 `#81E6D9` · 300 `#4FD1C5` · 400 `#38B2AC`
· 500 `#319795` (main brand) · 600 `#2C7A7B` (= `--primary`) · 700 `#285E61` · 800 `#234E52`
· 900 `#1D4044`.

**Semantic (`:root`):** `--primary` `#2C7A7B` · `--background` `#FFFFFF` · `--foreground`
`#000000` · `--muted` `#F2F4F7` · `--muted-foreground` `#475569` · `--border` `#E2E8F0` ·
`--card` `#FFFFFF` · `--destructive` `#EF4444` · `--ring` `#319795`.

**Charts (`--chart-1` … `--chart-5`):** `#319795` (teal) · `#0EA5E9` (blue) · `#285E61`
(dark teal) · `#026AA2` (dark blue) · `#64748B` (slate). Exactly five.

**Status fills:** success `#22C55E` · warning `#FEC601` · error `#EF4444` · info `#1890FF`.
These are fills for dots/badges/tints — not guaranteed AA as text on white.

**Gray is Slate-flavored:** 500 `#64748B`, 600 `#475569`, 700 `#344054`, 900 `#101828`.

## Typography, spacing, radius

- **Two fonts only:** Inter (`--font-sans`, everything) and JetBrains Mono (`--font-mono`,
  code). Load Inter via Google Fonts (`family=Inter:wght@400;500;600;700&display=swap`).
- **Sizes:** `text-xs` 12 · `sm` 14 · `base` 16 · `lg` 18 · `xl` 20 · `2xl` 24 · `3xl` 28 ·
  `4xl` 32 (each with a matching line-height).
- **Radius:** base `--radius` 6px; semantic `--radius-chip` 2 / `--radius-element` 4 /
  `--radius-container` 8 / `--radius-feature` 12; Tailwind `rounded-sm/md/lg/xl`.
- **Named spacing:** `--spacing-header` 58px (`h-header`), `--spacing-sidebar` 280px
  (`w-sidebar`), `--spacing-content` 976px (`max-w-content`).
- **Breakpoints:** xs 36rem · sm 48rem · md 62rem · lg 75rem · xl 88rem · 2xl 96rem.
- **Sentence case** on all UI text — capitalize only the first word and proper nouns.

## ui-kit component library (0.4.0)

`@policyengine/ui-kit` is a shadcn/radix component library plus the theme. Tokens are consumed
**via CSS only** — at 0.4.0 the package exports **no JS `palette`/`colors` object** and **no
`/legacy` shim**. Subpath exports: `./primitives`, `./layout`, `./inputs`, `./display`,
`./charts`, `./visualization`, `./utils`, `./assets`, `./theme.css`, `./styles.css`.

- **Layout/shell:** `DashboardShell`, `SidebarLayout`, `SingleColumnLayout`, `InputPanel`,
  `ResultsPanel`, `Header`, `Footer`, `Stack`, `Group`, `Container`. There is **no
  `PolicyEngineShell`/`PolicyEngineHeader`/`PolicyEngineFooter`** — those names do not exist;
  use `DashboardShell` / `Header` / `Footer`.
- **`Header` API (0.4.0):** `navItems: {label, href, children?}[]`, `logoSrc`, `logoHref`,
  `linkComponent`, `countries`, `currentCountry`, `onCountryChange`. It renders a sticky
  teal-gradient bar. Older `variant`/`logo`/`navLinks`/`children` props are gone.
- **Primitives:** `Button`, `Card`(+parts), `Badge`, `Tabs`, `Dialog`, `Sheet`, `Tooltip`,
  `Select`, `DropdownMenu`, `Input`, `Alert`, `Popover`, `Switch`, `Checkbox`, `Accordion`,
  `SegmentedControl`, … **Inputs:** `CurrencyInput`, `NumberInput`, `SelectInput`,
  `CheckboxInput`, `SliderInput`, `InputGroup`. **Display:** `MetricCard`, `SummaryText`,
  `DataTable`, `PolicyEngineWatermark`. **Utils:** `formatCurrency`, `formatPercent`,
  `formatNumber`, `cn`, `logos` (`logos.tealWordmark`/`tealSquare`/`whiteWordmark`/`whiteSquare`).

The favicon SVG ships at `@policyengine/ui-kit/favicon.svg` (teal square).

## Dark mode (accurate 0.4.0 contract)

theme.css declares `@custom-variant dark (&:is(.dark *))`, so a `.dark` class on an ancestor
activates `dark:` utilities. **But 0.4.0 ships no dark token values** — there is no
`.dark {}` / `:root.dark {}` block redefining the semantic vars. Toggling `.dark` alone does
**not** recolor `bg-primary`/`bg-background`. A consumer that wants dark mode must define its
own overrides:

```css
.dark { --background: #0B0E14; --foreground: #FFFFFF; --card: #111827; --border: #1F2937; }
```

Prefer the CSS-var form for charts (`fill="var(--chart-1)"`) so they follow any dark override
automatically. Do not claim built-in dark mode at this version.

## Charts

- **Recharts / SVG:** pass `var(--chart-1)`…`var(--chart-5)` to `fill`/`stroke`; grid/chrome
  use `var(--border)`, `var(--foreground)`, `var(--font-sans)`. SVG resolves `var()` natively —
  no helper. Round ticks: `niceTicks="snap125"` on numeric axes (recharts ≥3.8,
  PolicyEngine-contributed; see the policyengine-tools skill for the version gate and the
  `domain={["auto", "auto"]}` pairing). Conventions: gains `--chart-1`; losses `--chart-5`
  or `--destructive`; neutral `--border`.
- **Plotly (Python maps/charts)** — house style: white `plot_bgcolor`/`paper_bgcolor`, Inter
  font, teal series, logo bottom-right. Reference tokens by hex with a CSS-var comment.
  Sketch:
  ```python
  def format_fig(fig):
      fig.update_layout(font=dict(family="Inter", color="black", size=14),
                        plot_bgcolor="white", paper_bgcolor="white", template="plotly_white")
      # add_layout_image with a CHECKED-IN local logo asset (xref/yref="paper", bottom-right).
      return fig
  ```
  Use a local logo file copied into the repo — do not hotlink a raw GitHub URL.

## Migrating off the old design-system

<!-- stale-ok -->
`@policyengine/design-system` is deprecated; use `@policyengine/ui-kit`. The migration is a
consumption-model change, not a rename: drop the old JS token imports and consume ui-kit's
CSS vars via `theme.css` (there is no ui-kit JS token object to import at 0.4.0). Watch the
gray shift — the old design-system used Tailwind-3 grays (`#6B7280` at 500) while ui-kit uses
Slate (`#64748B` at 500), so grays change visibly; migrate per-usage, don't bulk-`sed`.
app-v2 keeps a **local** `@/designTokens` JS shim (its own `colors`/`spacing`/`typography`
objects mirroring theme.css) for inline styles during its migration — that shim is app-v2's,
not an export of ui-kit.

## Common mistakes

- Creating `tailwind.config.ts` — Tailwind v4 is CSS-first; all config is in `@theme`.
- `getCssVar()` / `getComputedStyle()` for chart colors — SVG takes `var()` directly.
- Old `pe-*`-prefixed classes (`bg-pe-primary-500`) — use `bg-teal-500` / `bg-primary`.
- Hardcoding hex in components — use the Tailwind class or `var()`.

## Related skills

- policyengine-tools — building/deploying tools that consume these tokens
- policyengine-app — app-v2's ui-kit + local designTokens hybrid
