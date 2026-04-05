# Portfolio Visualization Standard: Passive-Investor Analytics UX

## Overview

This standard defines how portfolio and finance visualizations are selected, implemented, and validated in this repository.

It is optimized for a **passive-investor** product posture:

- long-horizon portfolio monitoring
- benchmark-aware performance interpretation
- diversification and concentration analysis
- downside-risk and recovery visibility
- explainable, deterministic financial analytics

This standard is intentionally **not** optimized for intraday trading-terminal UX.

## Scope

Applies to:

- frontend analytics workspace routes:
  - `/portfolio/home`
  - `/portfolio/analytics`
  - `/portfolio/risk`
  - `/portfolio/reports`
  - `/portfolio/:symbol` (lot detail drill-down)
- backend contracts consumed by these visualizations:
  - `summary`, `time-series`, `contribution`, `risk-estimators`, `risk-evolution`,
    `return-distribution`, `efficient-frontier`, `health-synthesis`, `quant-metrics`
- portfolio + crypto + personal-finance interpretation modules that run on persisted ledger truth

Does not apply to:

- trade execution workflows
- order routing or broker mutation interfaces
- speculative signal dashboards without deterministic portfolio context

## Product Posture

Visualization decisions must prioritize the user questions that matter for passive investing:

1. How is my portfolio evolving?
2. How am I performing versus benchmark?
3. Where is concentration risk?
4. What downside and recovery profile am I carrying?
5. Are long-horizon outcomes robust across start windows?

If a visualization does not answer one of these questions, it should not be promoted to first-view surface.

## Core Selection Framework

Use chart type by analytical task, not aesthetic preference.

### Change over time

Preferred: line / area + optional contribution bars.

Use for:

- portfolio value history
- benchmark overlay
- cumulative and excess return trajectories
- rolling estimator trends

### Part-to-whole

Preferred: sorted bars or treemap.

Use for:

- asset-class allocation
- sector/category allocation
- geography/currency mix
- crypto category exposure

### Ranking / concentration

Preferred: ordered horizontal bars.

Use for:

- top holdings by weight
- top sector concentration
- contribution leaders and detractors

### Deviation from baseline

Preferred: diverging bars / drawdown curves / excess-return bars.

Use for:

- benchmark spread
- drawdown versus zero (peak)
- overweight/underweight diagnostics

### Distribution

Preferred: histogram / bucketed bars / box-like summaries.

Use for:

- monthly or annual return distribution
- deterministic bucket frequencies
- tail-risk concentration signals

### Correlation / relationship

Preferred: scatter / matrix-style heatmap / network view when domain-fit.

Use for:

- risk vs return positioning
- cross-symbol co-movement
- efficient-frontier and volatility-return diagnostics

## Required Visualization Set By Priority

### P0 (must exist and remain reliable)

- Portfolio vs benchmark trend line
- Allocation view (bars and/or treemap)
- Concentration ranking (top holdings/sectors)
- Drawdown visualization
- Holdings table with drill-down to lot detail

### P1 (high-value analytical depth)

- Monthly performance heatmap
- Rolling returns / rolling risk estimators
- Return-distribution histogram
- Excess-return or benchmark-spread view

### P2 (advanced diagnostics)

- Risk-return scatter
- Correlation cluster/heatmap
- Efficient frontier + weight comparison
- Net-worth waterfall decomposition

## Route-Level Minimum Contracts

### `/portfolio/home`

Must prioritize:

- high-signal KPI interpretation
- trend preview with benchmark context
- allocation/concentration snapshot
- explicit trust/freshness context

Home is an executive summary surface, not a dense quant workbench.

### `/portfolio/analytics`

Must prioritize:

- time-series trend analysis
- contribution leaders + waterfall
- interpretation of period impact concentration

### `/portfolio/risk`

Must prioritize:

- estimator set with methodology metadata
- drawdown path timeline
- rolling volatility/beta timeline
- return distribution + tail diagnostics

### `/portfolio/reports`

Must prioritize:

- quant diagnostics lifecycle states
- bounded Monte Carlo controls and results
- efficient frontier and contribution risk budget
- monthly return heatmap and health bridge context

### `/portfolio/:symbol`

Must prioritize:

- precise holdings/lot explainability
- drill-down support from summary and hierarchy views

## Financial Unit and Contract Rules

### Unit integrity is mandatory

- `percent` values must not be multiplied or divided again in presentation.
- `ratio` values may be multiplied by 100 only at formatting boundaries where explicitly intended.
- Money values stay in currency formatting utilities.
- Chart axis labels must state units (`%`, ratio, USD) where ambiguity is possible.

### Deterministic contract handling

- Frontend must consume backend contract fields as delivered.
- Unsupported scope/symbol combinations must fail explicitly with factual UI state.
- No silent fallback or fabricated values when a metric is unavailable.

### Baseline and context

- Benchmark context must be present when the chart implies relative performance.
- Risk charts must expose methodology context and interpretation thresholds where available.
- Freshness/provenance tokens must remain visible in route-level workspace framing.

## Composition and Layout Rules

- Every chart block must have:
  - title
  - concise subtitle describing analytical intent
  - explicit loading/ready/error/unavailable state behavior
- Prefer one primary analytical job per route first viewport.
- Keep dense detail below first-view interpretation layer.
- Favor direct data labels for key points over oversized legend dependence.

## Interaction Rules

- Tooltips must reveal exact value and key context (benchmark delta, period, scope).
- Key filters must support period, scope, instrument symbol, and benchmark where applicable.
- Toggles should preserve interpretation continuity:
  - normalized vs absolute
  - portfolio vs instrument scope
  - value vs percentage
- Drill-down path must remain coherent:
  - Portfolio -> grouped concentration -> holding -> lot detail

## Accessibility Rules (WCAG 2.2 AA Baseline)

- Text contrast must meet AA (`4.5:1`; large text `3:1`).
- Keyboard focus indicator must be visible for all keyboard-operable controls.
- Pointer targets should satisfy minimum target size (`24x24 CSS px`) or spacing exception criteria.
- Do not rely on red/green color alone to encode gain/loss state.
- Dense tables/charts must keep keyboard reachability and readable labels.

## Visual Semantics Rules

- Keep semantic color mapping consistent across routes:
  - portfolio primary series
  - benchmark comparison series
  - positive/negative/neutral tones
  - risk severity tones
- Avoid alarmist or gamified visual language.
- Motion must be restrained and comprehension-focused.

## Anti-Patterns (do not promote as primary)

- Candlestick-first dashboard layouts for passive-investor routes
- Gauge/speedometer-heavy KPI surfaces
- Pie/donut overuse when precise comparison is needed
- Confusing multi-axis charts without explicit analytical justification
- Decorative chart duplication that delays decision-critical interpretation

## Testing and Validation Rules

### Frontend tests

Add or preserve tests for:

- route primary-job rendering contracts
- chart unit formatting and no double-scaling regressions
- benchmark context visibility
- loading/error/unavailable state determinism
- keyboard navigation and focus visibility on chart controls

### Backend/contract tests

Add or preserve tests for:

- visualization payload completeness and schema invariants
- scope/symbol validation failures as explicit client errors
- deterministic methodology metadata on risk/quant endpoints

### Validation commands

```bash
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test
npm --prefix frontend run build
uv run pytest -v app/portfolio_analytics/tests
```

## Implementation Checklist For New Visual Modules

Before shipping a new chart module:

1. Identify the analytical question category (change, part-to-whole, ranking, deviation, distribution, correlation).
2. Confirm contract fields and units from backend schema.
3. Define state behavior (`loading`, `ready`, `unavailable`, `error`, `blocked`) explicitly.
4. Add benchmark/baseline context if interpretation requires comparison.
5. Verify keyboard/focus/contrast/target-size behavior.
6. Add regression tests for unit correctness and interaction behavior.
7. Update docs/guides if the module changes route-level interpretation semantics.

## Alignment With Existing Codebase

This standard is aligned with current delivered workspace architecture:

- shared route shell and trust-state framing
- Core 10 first-view interpretation layers
- advanced-risk-lab modules (frontier + concentration)
- deterministic return-distribution and risk-evolution modules
- quant/report lifecycle and bounded Monte Carlo controls
- holdings and lot-detail drill-down pathways

## Resources

### Chart-selection frameworks

- Financial Times Visual Vocabulary:
  - https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary
  - https://raw.githubusercontent.com/Financial-Times/chart-doctor/main/visual-vocabulary/Visual-vocabulary-en.pdf
- Tableau chart selection guide:
  - https://help.tableau.com/current/pro/desktop/en-us/what_chart_example.htm
  - https://www.tableau.com/learn/whitepapers/which-type-chart-or-graph-right-for-you-ungated

### Accessibility (official)

- WCAG contrast minimum (SC 1.4.3):
  - https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- WCAG focus visible (SC 2.4.7):
  - https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- WCAG target size minimum (SC 2.5.8):
  - https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum

### Passive-investor analytics references

- Portfolio Charts drawdowns:
  - https://portfoliocharts.com/charts/drawdowns/
- Portfolio Charts rolling returns:
  - https://portfoliocharts.com/charts/rolling-returns/
- Portfolio Charts heat map:
  - https://portfoliocharts.com/charts/heat-map/
- Portfolio Charts annual returns:
  - https://portfoliocharts.com/charts/annual-returns/

---

**Last Updated:** 2026-04-05
