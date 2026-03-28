## Why

The current frontend is reliable but still table-first, which limits usability for portfolio monitoring and decision workflows. We need a dashboard-grade analytics workspace before database hardening so users can read trends, risk, and context in the first viewport without inferring metrics manually.

## What Changes

- Add a multi-route analytics workspace with navigation for `Home`, `Analytics`, `Risk`, and `Transactions`.
- Add chart-driven UX modules (KPI cards, trend charts, contribution views, risk views) on top of typed backend analytics contracts.
- Extend backend portfolio analytics with explicit time-series and risk-input endpoints required by charts.
- Add an operations-first quant computation contract for estimator pipelines (sorted/tz-aware series, explicit missing-data policy, explicit frequency/calendar alignment, and deterministic event-time joins).
- Add explicit estimator methodology metadata (return basis, window, annualization basis, and estimator-specific parameters) so frontend can render interpretable risk context.
- Freeze v1 chart-analytics period enum (`30D`, `90D`, `252D`, `MAX`) and reject unsupported periods explicitly.
- Freeze v1 `Transactions` route to ledger-event history only; defer market-refresh diagnostics to follow-up scope.
- Keep fail-fast semantics and provenance explicit for all derived metrics surfaced in UI.
- Preserve existing lot-detail drill-down behavior while improving route composition, layout hierarchy, and dashboard usability.
- Add documentation and acceptance evidence for chart-heavy accessibility/performance behavior.

## Capabilities

### New Capabilities

- `frontend-analytics-workspace`: Defines dashboard information architecture, route structure, and chart-centric UX behavior for portfolio workflows.
- `portfolio-risk-estimators`: Defines deterministic risk/estimator metric contracts derived from persisted ledger plus persisted market data.

### Modified Capabilities

- `portfolio-analytics`: Expand API requirements beyond grouped summary + lot detail to include chart-ready time-series and attribution/risk input surfaces with explicit provenance.
- `frontend-release-readiness`: Extend release-readiness requirements from summary/lot-detail-only MVP views to the new analytics workspace routes and chart modules.

## Impact

- Affected code:
  - frontend routes, layout, feature modules, chart components, and API hooks
  - backend `app/portfolio_analytics/` schemas/routes/service for new read-only analytics endpoints
  - potential shared market-data read helpers for historical/time-series retrieval
  - backend quant computation kernels and estimator regression fixtures aligned with NumPy/pandas/SciPy standards
- Affected APIs:
  - new portfolio analytics read endpoints for chart/risk inputs
  - existing summary/lot endpoints remain supported and deterministic
- Affected docs:
  - product roadmap and frontend UX planning docs
  - frontend architecture/API guides and release checklist evidence references
  - standards-aligned estimator methodology and validation evidence references
- Dependencies:
  - `Recharts` as v1 chart foundation library (re-evaluate only with explicit performance evidence)
  - approved/pinned quant dependency stack for estimator computation (`numpy`, `pandas`, `scipy`)
  - operations guidance from `docs/standards/numpy-standard.md`, `docs/standards/pandas-standard.md`, and `docs/standards/scipy-standard.md`
  - typed response contracts and test coverage for new analytics surfaces
