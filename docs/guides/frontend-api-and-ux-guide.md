# Frontend API And UX Guide

## Purpose

This guide defines the implementation contract between backend portfolio APIs and frontend route behavior.
It documents the current workspace-first IA, state mapping rules, and methodology metadata surfaced to users.

## API Endpoints

- Summary: `GET /api/portfolio/summary`
- Lot detail: `GET /api/portfolio/lots/{instrument_symbol}`
- Time series: `GET /api/portfolio/time-series?period={30D|90D|252D|MAX}`
- Contribution: `GET /api/portfolio/contribution?period={30D|90D|252D|MAX}`
- Risk estimators: `GET /api/portfolio/risk-estimators?window_days={30|90|252}`
- Quant metrics: `GET /api/portfolio/quant-metrics?period={30D|90D|252D|MAX}`
- Quant report generate: `POST /api/portfolio/quant-reports`
- Quant report artifact: `GET /api/portfolio/quant-reports/{report_id}`

## Route Information Architecture

- `/portfolio`
  - grouped summary table
  - deterministic drill-down to lot detail
- `/portfolio/:symbol`
  - lot-level ledger detail + dispositions
- `/portfolio/home`
  - KPI cards + trend chart + deterministic drill-down links
  - supplemental quant preview + report actions (section-scoped state)
- `/portfolio/analytics`
  - trend + contribution modules (`Preview` framing in navigation)
- `/portfolio/risk`
  - estimator cards/charts + methodology metadata (`Interpretation` framing in navigation)
- `/portfolio/transactions`
  - ledger-event-only table and filters (v1 scope)

## Environment And API Prefix Resolution

- Route prefix is backend-configured (`settings.api_prefix`), default `/api`.
- Frontend composes relative API paths and must not hardcode host-specific URLs.

## Response Contracts

### Summary Response

- `as_of_ledger_at: datetime`
- `pricing_snapshot_key: str | null`
- `pricing_snapshot_captured_at: datetime | null`
- `rows: PortfolioSummaryRow[]`

Behavior notes:

- Symbols are canonical uppercase.
- Rows are symbol-sorted deterministically.
- Valuation fields are snapshot-derived and may be null on closed rows.
- One consistent persisted snapshot must back one response.

### Lot Detail Response

- `as_of_ledger_at: datetime`
- `instrument_symbol: str`
- `lots: PortfolioLotDetailRow[]`

Behavior notes:

- Input symbol may be mixed case; UI renders canonical uppercase output.
- Not-found (`404`) remains explicit, never collapsed into empty.

### Time Series Response

- `as_of_ledger_at: datetime`
- `period: 30D | 90D | 252D | MAX`
- `frequency: str`
- `timezone: str`
- `points: [{ captured_at, portfolio_value_usd, pnl_usd }]`

Behavior notes:

- Point order is deterministic (ascending by `captured_at`).
- Frontend charts must use server payload values directly; no inferred synthetic rows.

### Contribution Response

- `as_of_ledger_at: datetime`
- `period: 30D | 90D | 252D | MAX`
- `rows: [{ instrument_symbol, contribution_pnl_usd, contribution_pct }]`

Behavior notes:

- Rows represent persisted-truth contribution outputs; frontend may sort for display but must keep numeric payload unchanged.

### Risk Estimators Response

- `as_of_ledger_at: datetime`
- `window_days: 30 | 90 | 252`
- `metrics: PortfolioRiskEstimatorMetric[]`

Required per-metric methodology metadata:

- `estimator_id`
- `value`
- `window_days`
- `return_basis` (`simple` or `log`)
- `annualization_basis.kind` (`trading_days`)
- `annualization_basis.value` (default v1 basis `252`)
- `as_of_timestamp`

### Quant Metrics Response

- `as_of_ledger_at: datetime`
- `period: 30D | 90D | 252D | MAX`
- `benchmark_symbol: str | null`
- `metrics: PortfolioQuantMetric[]`
- `benchmark_context: { benchmark_symbol, omitted_metric_ids, omission_reason }`

Behavior notes:

- Benchmark-relative metrics (for example alpha/beta) are optional and may be omitted explicitly.
- Frontend must render `benchmark_context.omission_reason` and `omitted_metric_ids` when provided.
- Omission is explicit and is not equivalent to successful metric computation.

### Quant Report Generation Response

- `report_id: str`
- `scope: portfolio | instrument_symbol`
- `instrument_symbol: str | null`
- `period: 30D | 90D | 252D | MAX`
- `benchmark_symbol: str | null`
- `generated_at: datetime`
- `expires_at: datetime`
- `report_url_path: str`

Behavior notes:

- Report controls must expose explicit action lifecycle states (`loading`, `error`, `ready`).
- Report action failures are section-scoped and must not replace Home core context.

## Normalization And Validation Rules

- Supported chart period enum is fixed to `30D`, `90D`, `252D`, `MAX`.
- Unsupported period query values must be normalized client-side before API call; unsupported backend responses remain explicit errors.
- Risk window mapping is deterministic:
  - `30D -> 30`
  - `90D -> 90`
  - `252D -> 252`
  - `MAX -> 252` (v1 bounded window contract)
- Unsupported risk windows are explicit backend validation failures and must not silently downgrade.

## Numeric Handling And Precision Safety

- Treat financial values as decimal-safe strings at contract boundaries.
- Do not use binary float math for money equality/aggregation logic.
- Formatting rules:
  - quantity-like: keep high precision; trim display-only trailing zeros where intended
  - money-like: USD with 2 decimals
  - percent-like: 2 decimals + `%`

## UX State Mapping

Each route must render explicit `loading`, `empty`, and `error` states:

- `/portfolio/home`
  - empty when summary rows or trend points are empty
  - quant/report modules use section-scoped loading/empty/error states
- `/portfolio/analytics`
  - empty when trend points or contribution rows are empty
- `/portfolio/risk`
  - empty when metrics are empty
  - explicit warning variants for unsupported or insufficient scope
- `/portfolio/transactions`
  - empty when filtered ledger events are empty

## Error Handling Contract

- `404`: explicit not-found messaging (do not coerce to empty state)
- `409`: explicit insufficient-history/scope messaging when backend rejects unsupported coverage
- `422`: explicit validation error for unsupported period/window values
- `5xx`: explicit transient error + retry action

## Deferred Boundaries (v1)

- `Transactions` route remains ledger-event-only.
- Market-refresh diagnostics are intentionally deferred to an operator-facing follow-up and are out of v1 UX/API scope.

## Quant Placement Matrix

- Home: KPI + supplemental quant preview + report actions; optional quant/report failures remain section-scoped.
- Risk: interpretation-sensitive risk metrics with methodology context as primary surface.
- Quant reports: generated artifacts remain explicit actions with typed scope and lifecycle states.

## Accessibility And Performance Evidence Requirements

- Keyboard navigation must cover summary row activation and workspace tab navigation.
- Accessibility scan scope must include:
  - `/portfolio`
  - `/portfolio/VOO`
  - `/portfolio/UNKNOWN`
  - `/portfolio/ERR500`
  - `/portfolio/home`
  - `/portfolio/analytics`
  - `/portfolio/risk`
  - `/portfolio/transactions`
- CWV evidence must include workspace routes (`home`, `analytics`, `risk`, `transactions`) plus portfolio baseline routes.
