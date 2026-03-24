# Frontend Design System Guide (v1)

## Purpose

This guide defines the initial visual and interaction system for the frontend MVP.
It aims for professional clarity in a finance context while preserving ledger-first trust signals.

## Design Principles

- Trust over spectacle.
- Utility-first hierarchy.
- Explainability in every key metric.
- Consistency across summary and lot detail.
- Accessibility and performance are first-order design constraints.

## Visual Direction

Theme name: `Ledger Clarity`

Direction:

- Calm, high-contrast, data-dense UI
- Minimal decorative noise
- Strong emphasis on alignment, spacing rhythm, and numeric legibility
- Support both light and dark reading environments without changing semantic meaning

## Typography

Primary: `IBM Plex Sans`  
Secondary / numeric emphasis: `IBM Plex Mono`

Font stacks:

- Sans stack: `"IBM Plex Sans", "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif`
- Mono stack: `"IBM Plex Mono", "JetBrains Mono", "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`

Loading strategy:

- Prefer self-hosted `woff2` with `font-display: swap`.
- Preload primary regular and semibold fonts used above the fold.
- Keep fallback metrics close to reduce content shift during swap.
- Do not ship runtime `@import` or third-party stylesheet fetches for primary fonts in release builds.

Rules:

- Use tabular numerals where available for KPI columns.
- Keep headline scale restrained; prioritize table readability.
- Minimum body size: 16px.

## Color Tokens

Define CSS variables and keep usage semantic:

- `--color-bg`
- `--color-surface`
- `--color-border`
- `--color-text-primary`
- `--color-text-secondary`
- `--color-positive`
- `--color-negative`
- `--color-warning`
- `--color-focus-ring`

Recommended v1 values:

| Token | Value | Usage |
| --- | --- | --- |
| `--color-bg` | `#F6F8FB` | App background |
| `--color-surface` | `#FFFFFF` | Cards, tables, panels |
| `--color-border` | `#D8E0EA` | Dividers and table lines |
| `--color-text-primary` | `#0F172A` | Primary text and headings |
| `--color-text-secondary` | `#334155` | Secondary labels and helper text |
| `--color-positive` | `#0F766E` | Positive gains and success status |
| `--color-negative` | `#B91C1C` | Losses and error status |
| `--color-warning` | `#9A6700` | Warnings and scope limitations |
| `--color-focus-ring` | `#1D4ED8` | Keyboard focus ring |

Guidelines:

- Maintain WCAG AA contrast baseline.
- Use semantic status colors only with accompanying text labels/icons.
- Avoid pure black on pure white for long reading blocks.

### Dual-Theme Extension

The MVP may ship with a user-selectable light and dark theme as long as:

- semantic token names stay identical across themes
- contrast and focus visibility remain compliant in both themes
- theme switching does not change financial meaning or status color semantics
- the default theme respects the operating-system preference when no user override exists

Recommended dark-mode direction:

| Token | Value | Usage |
| --- | --- | --- |
| `--color-bg` | `#0A1622` | App background |
| `--color-surface` | `rgba(12, 26, 39, 0.82)` | Cards and tables |
| `--color-border` | `rgba(122, 151, 176, 0.20)` | Dividers |
| `--color-text-primary` | `#EDF4FB` | Primary text |
| `--color-text-secondary` | `#B6C8D9` | Secondary text |
| `--color-accent` | `#6FA8FF` | Links, focus-adjacent emphasis |
| `--color-positive` | `#5DD6BF` | Positive outcomes |
| `--color-negative` | `#FF8CAB` | Negative outcomes |
| `--color-warning` | `#F6BE5F` | Scope and warning notes |

## Spacing And Layout

Spacing scale:

- `4, 8, 12, 16, 24, 32, 48`

Recommended primitive aliases:

| Alias | Value |
| --- | --- |
| `--space-1` | `4px` |
| `--space-2` | `8px` |
| `--space-3` | `12px` |
| `--space-4` | `16px` |
| `--space-6` | `24px` |
| `--space-8` | `32px` |
| `--space-12` | `48px` |

Recommended component spacing:

| Component | Padding | Gap |
| --- | --- | --- |
| App shell content | `24px` desktop / `16px` mobile | `24px` |
| KPI strip card | `16px` | `8px` |
| Summary table cell | `12px 16px` | n/a |
| Lot detail section | `16px` | `12px` |
| Error/empty block | `16px` | `8px` |

Container rules:

- Max content width for desktop readability.
- Sticky table headers on large datasets.
- Preserve comfortable edge padding on mobile.

## Page Framing And Hierarchy

- Prefer compact workspace headers over editorial hero sections for analytics routes.
- The first viewport on standard laptop widths should show page title, ledger timestamp, scope note, and primary action/navigation without scrolling.
- Keep introductory copy to one short sentence; supporting explanation should not compete with the analytics content.
- Avoid stacking multiple explainer cards above the core data on summary and lot-detail screens.
- If extra trust context is needed, use one restrained panel or inline note rather than a second full narrative column.

## Component Primitives

- App shell (header + content frame)
- KPI strip
- Overview card grid
- Data table
- Symbol chip
- Status pill
- Timestamp badge (`as_of_ledger_at`)
- Inline error banner
- Empty-state block
- Skeleton loading rows
- Disclosure row for lot dispositions
- Theme toggle

## Data Table Standards

- Right-align numeric columns.
- Left-align symbol and descriptive text.
- Fixed column labels with glossary tooltips for finance terms.
- Preserve deterministic ordering unless user explicitly sorts.
- Provide keyboard focus and visible focus ring for row actions.

## Motion Standards

- Use subtle entrance and state transitions only.
- Avoid decorative motion loops in data-heavy views.
- Respect `prefers-reduced-motion: reduce`.
- Keep transition durations short and consistent.
- Theme transitions should feel immediate; avoid long cross-fades that can obscure data changes.

Recommended transition tokens:

- `--motion-fast: 120ms`
- `--motion-base: 180ms`
- `--motion-slow: 240ms`
- `--motion-ease: cubic-bezier(0.2, 0, 0, 1)`

## Responsive Rules

Breakpoints:

- `sm: 0-639`
- `md: 640-1023`
- `lg: 1024+`

Behavior:

- Desktop: full multi-column tables.
- Tablet: progressive column reduction with summary toggles.
- Mobile: stacked key metrics + horizontally scrollable data regions.
- Summary cards should collapse to a single-column stack on narrow screens before data-table readability is compromised.

## Content And Copy Rules

- Label unsupported values explicitly as `Not available in ledger-only v1`.
- Error language should state what failed and what user can do next.
- Avoid marketing-style hero copy for core analytics pages.
- Avoid repeating documentation-level explanations in the route header; put deep explanation in secondary notes only when it improves task completion.
- Use concise labels and consistent finance terminology.
- Derived overview cards must be labeled as derived from visible API rows when they are not backend-native fields.

## Recommended UI States

- Neutral: default ledger status
- Positive: gains/dividend net positive
- Negative: losses or error conditions
- Informational: as-of timestamp and scope limitations

## Extensibility Guidance

- Add new visual tokens only via semantic naming, not ad hoc page values.
- New KPI cards must include source explanation and scope note.
- Any future chart module must declare data freshness and source provenance.
- Theme additions should be made only through semantic tokens and documented parity checks for both light and dark modes.
