## Why

Phase F hardened layout and explainability, but the risk/quant experience remains mostly point-in-time. For long-term investing decisions, users need path-aware diagnostics (risk evolution over time and probabilistic outcomes), not only snapshot cards.

## What Changes

- Add deterministic Monte Carlo simulation support for both `portfolio` scope and explicit `instrument_symbol` scope.
- Add risk-evolution datasets for timeline storytelling: drawdown path, rolling volatility, rolling beta, and return-distribution buckets.
- Promote Risk route visualization from static-only cards to mixed view: guardrailed cards + trend timelines + distribution context.
- Extend Quant/Reports to include simulation assumptions/outputs and explicit lifecycle handling for simulation-enabled artifacts.
- Keep fail-fast semantics for invalid simulation/risk parameters and insufficient data windows.
- Expand metric explainability to include interpretation bands and threshold-context copy.
- Add profile-calibrated Monte Carlo scenario comparison (`Conservative`, `Balanced`, `Growth`) so users can compare three bust/goal threshold levels in one deterministic run.
- Add historical-threshold calibration controls (`monthly` or `annual` basis) so default profile thresholds are grounded in persisted realized return behavior.
- Add Monte Carlo profile configuration guidance module in Quant/Reports (editable presets + interpretation guidance) without removing manual parameter controls.
- Make profile-scenario comparison enabled by default in Monte Carlo diagnostics while preserving live manual overrides (`sims`, horizon, `bust`, `goal`, `seed`) in the same surface.
- Add a compact profile-control UI contract (`Enable profile compare`, `Calibration basis`, `Apply profile`) designed for button/checkcombo interaction patterns.
- Add side-by-side scenario visualization requirements so the three profile outcomes are readable at a glance (panoramic comparison first, drill-down second).
- Clarify portfolio P&L taxonomy in product contracts (realized vs unrealized vs period change vs total return) and avoid mixing business-statement P&L components (`COGS`, `OPEX`, `EBITDA`) that are not portfolio KPIs in this app scope.
- Add route-level placement guidance for P&L context:
  - `Home`: compact executive P&L snapshot
  - `Analytics`: decomposition/trend attribution of P&L drivers
  - `Quant/Reports`: scenario-forward diagnostics and threshold probability context
- Add a portfolio-health synthesis layer that converts scattered KPI diagnostics into one interpretable view (`healthy`, `watchlist`, `stressed`) with explicit profile posture (`Conservative`, `Balanced`, `Aggressive`) and non-prescriptive rationale.
- Add deterministic health pillars (`Growth`, `Risk`, `Risk-Adjusted Quality`, `Resilience`) derived from approved KPI subsets and threshold bands already present in contracts.
- Add route-consistent health storytelling:
  - `Home`: health-at-a-glance panel + top 3 supporting/risk drivers
  - `Risk`: risk pillar deep-link context (why health is penalized or supported)
  - `Quant/Reports`: health-over-time snapshot and scenario sensitivity notes from Monte Carlo profile outcomes
- Add a concise KPI-priority model in UI copy (`Core 10` metrics first, advanced metrics second) to reduce interpretation noise for non-expert users.

## Extension 9: Frontend UI Polish and Table Semantics Hardening

- Harden dense analytical table readability and alignment contracts across Reports and Hierarchy modules.
- Redesign Quant period-lens rendering (`30D` / `90D` / `252D`) for faster scanability and professional numeric rhythm.
- Compact Quant report lifecycle action surface (scope + generate CTA + lifecycle status hierarchy) to reduce oversized vertical footprint.
- Improve symbol-contribution table semantics for directional clarity (`signed contribution` vs `absolute move share`) and faster top-mover interpretation.
- Set Portfolio Hierarchy default state to sector-collapsed and add sortable column affordances with explicit sort arrows and deterministic ordering.
- Apply spacing and control-placement polish for consistency across high-density panels while preserving current route behavior and core functionality.
- Reuse proven frontend architecture patterns from template investigation (UI primitive consistency, state-feedback density patterns) without stack migration or behavior drift.

## Capabilities

### New Capabilities
- `portfolio-monte-carlo-scenarios`: Deterministic QuantStats-based simulation contracts for portfolio and instrument scopes, including explicit assumptions and probability outcomes.

### Modified Capabilities
- `portfolio-analytics`: Add chart-ready risk-evolution and return-distribution datasets with deterministic scope/period semantics, plus portfolio-health synthesis outputs and supporting driver metadata.
- `portfolio-risk-estimators`: Extend risk interpretation contract with time-evolution context and threshold-aware metadata.
- `portfolio-quant-reporting`: Extend report-generation/retrieval contracts for simulation-aware quant diagnostics, lifecycle states, and health-summary inclusion.
- `portfolio-monte-carlo-scenarios`: Extend simulation contract to support profile scenario matrix outputs and historical calibration metadata.
- `frontend-analytics-workspace`: Add professional Risk and Quant/Reports visual modules for timeline diagnostics, distribution insight, simulation context, profile-scenario comparison controls, executive health synthesis UX, and table-semantics/UI-polish hardening for dense analytical surfaces.

## Impact

- Backend: `app/portfolio_analytics/{schemas.py,service.py,routes.py}` and related tests.
- Frontend: Home, Risk, Quant/Reports, and Portfolio Hierarchy modules for health synthesis, KPI-priority rendering, explainability copy, workflow state rendering, compact lifecycle actions, default-collapse/sorting ergonomics, and dense-table readability polish.
- OpenSpec/docs: capability specs, implementation tasks, frontend/API guide updates, QuantStats standard updates, and changelog closeout evidence.
- Dependencies: No new runtime package expected; uses existing pinned `quantstats` stack with stricter adapter/test coverage.
