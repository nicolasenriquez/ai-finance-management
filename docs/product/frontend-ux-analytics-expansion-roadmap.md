# Frontend UX and Analytics Expansion Roadmap

## Purpose

This roadmap defines how to evolve the current frontend from a table-first MVP into a high-value analytics workspace while preserving existing reliability, accessibility, and finance-safe behavior.

It integrates:

- in-depth findings from `ultimate-react-course` review
- current backend/frontend contract boundaries in this repository
- delivery order before database hardening expansion

## Current Implementation Baseline (2026-03-28)

- Workspace routes are implemented and active:
  - `/portfolio/home`
  - `/portfolio/analytics`
  - `/portfolio/risk`
  - `/portfolio/transactions`
- Backend contracts implemented for workspace analytics:
  - `/api/portfolio/time-series`
  - `/api/portfolio/contribution`
  - `/api/portfolio/risk-estimators`
- Period enum is locked and enforced end-to-end (`30D`, `90D`, `252D`, `MAX`).
- Risk methodology metadata is surfaced in UI from API payload (`window_days`, `return_basis`, `annualization_basis`, `as_of_timestamp`).
- Transactions v1 scope remains ledger-history-only; market-refresh diagnostics are deferred.
- Route-level evidence is captured for workspace + baseline portfolio routes:
  - accessibility: `docs/evidence/frontend/accessibility-scan-2026-03-28.md`
  - keyboard: `docs/evidence/frontend/keyboard-walkthrough-2026-03-28.md`
  - CWV: `docs/evidence/frontend/cwv-report-2026-03-28.md`

## Decision: React + Vite Now, Next.js Later by Gate

### Decision now

Stay on the current `React + Vite` stack for the next delivery phases.

### Why

- Current product is API-first with FastAPI backend already in place.
- Immediate value is UX/UI + analytics depth, not SSR migration.
- A framework migration now would add high migration cost while backend analytics endpoints still need expansion.
- Current frontend already meets strong accessibility/performance gates and can scale with charting + modular architecture.

### Re-evaluate Next.js only when these gates are true

- Need for SEO or public indexable pages becomes explicit.
- Need for server component composition across authenticated frontend use cases is proven.
- Need for edge rendering/caching strategy cannot be solved cleanly with current deployment model.
- Frontend API boundary for analytics is stable enough to justify framework migration cost.

## Delivery Phases

## Phase A: Frontend Foundation Consolidation (short)

### Objectives

- Formalize frontend pattern baseline from the course review.
- Lock architecture conventions for pages/features/ui/services/hooks.
- Introduce charting foundation and dashboard layout primitives.

### Deliverables

- Architecture decision note linking to SOT analysis
- Chart library decision and base chart components
- Shared dashboard layout primitives
- UI token extension for analytics modules

### Exit Criteria

- New analytics screens can be built without one-off patterns.
- All new components align with existing accessibility and formatting standards.

### Chart Foundation Lock (v1)

- `Recharts` is the locked v1 chart foundation for workspace routes.
- Re-evaluation is allowed only with explicit route-level evidence on `/portfolio/home`, `/portfolio/analytics`, and `/portfolio/risk`.
- Evidence must show a sustained blocker after optimization attempts:
  - CWV regression attributable to chart rendering (`LCP` > `2.5s` p75 or `INP` > `200ms` p75),
  - unresolved accessibility blocker that cannot be solved safely with current chart primitives, or
  - required product interaction not implementable with maintainable complexity.
- Any chart-library switch requires a documented decision artifact with side-by-side evidence.

## Phase B: Analytics API Contract Expansion

### Objectives

- Add backend endpoints required for historical and analytical visualizations.
- Keep fail-fast semantics and explicit provenance for every derived metric.

### Candidate API surfaces

- portfolio value time series
- periodic PnL aggregates (daily/weekly/monthly)
- contribution by symbol
- volatility and drawdown-ready series inputs

### Exit Criteria

- Typed contracts documented and validated.
- Frontend can render charts without inventing unsupported metrics client-side.

## Phase C: UX/UI Dashboard Expansion

### Objectives

- Introduce multi-tab IA:
  - `Home`
  - `Analytics`
  - `Risk`
  - `Transactions`
- Replace table-only first impression with dashboard-first workflow.

### Transactions Scope Lock (v1)

- `Transactions` is ledger-history-only in v1.
- Market-refresh diagnostics are deferred to a separate operator-facing follow-up capability and must not be mixed into the v1 transaction-history contract.

### Deliverables

- Home summary with KPI cards, trend chart, top movers, and transaction highlights
- Analytics tab with performance and attribution charts
- Updated navigation and responsive behavior

### Exit Criteria

- Users can understand portfolio state and trend in first viewport.
- Drill-down from summary to lot detail remains deterministic and clear.

## Phase D: Risk and Quant Estimators

### Objectives

- Add explicit risk analytics from persisted ledger + market data.
- Keep metric definitions auditable and deterministic.

### Approved v1 quant stack policy

- Accepted runtime stack for canonical estimator computation: `numpy`, `pandas`, `scipy`.
- `pandas-ta` is optional for non-canonical analytics overlays and must not be the source of truth for risk metrics.
- Rejected for this phase: `zipline`, `zipline-reloaded`, `pyfolio`, `pyrisk`, `mibian`, `backtrader`, `QuantLib-Python`.
- Dependency governance: pin exact versions in `pyproject.toml` and `uv.lock`; any upgrade requires estimator fixture comparison and documented review.

### Frozen v1 estimator methodology contract

- Default estimator windows: `30`, `90`, `252` trading-day periods.
- Return basis semantics: baseline estimators use `simple` returns unless metadata explicitly declares `log`.
- Annualization basis semantics: annualized metrics use explicit basis metadata with default `252` trading days unless endpoint contract explicitly overrides it.
- Required response metadata fields:
  - `estimator_id`
  - `window_days`
  - `return_basis`
  - `annualization_basis.kind`
  - `annualization_basis.value`
  - `as_of_timestamp`

### Initial metric set

- rolling volatility
- max drawdown
- VaR / CVaR (clearly documented assumptions)
- Sharpe/Sortino (with explicit risk-free and period basis)
- concentration metrics

### Exit Criteria

- Risk tab provides actionable insights with transparent formulas/provenance.
- Metrics are validated by tests and documented with scope limitations.

## Phase E: Optional Next.js Spike (conditional)

### Objective

Run a bounded spike only if migration gates are satisfied.

### Scope

- one route vertical slice
- measure build/runtime complexity, DX impact, deployment impact
- compare against current Vite route

### Exit Criteria

- explicit go/no-go decision with evidence
- no full migration without approved decision artifact

## Standards and Quality Gates (Non-Negotiable)

- Keep existing frontend reliability rules:
  - explicit loading/empty/error states
  - no silent fallback for unsupported data
- Keep finance-safe formatting and decimal correctness.
- Maintain WCAG 2.2 AA and Core Web Vitals evidence.
- Preserve typed API boundaries and test coverage expansion with each phase.

## Immediate Execution Order

1. Publish SOT analysis and governance in docs (done with this roadmap set).
2. Open a dedicated change proposal for Phase A + Phase B.
3. Implement analytics API contracts needed for charts before UI-heavy implementation.
4. Deliver `Home` and `Analytics` tabs first, then `Risk`.
5. Run optional Next.js spike only after Phase C or later.
