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
  - executive KPI snapshot + period waterfall + trend preview + deterministic drill-down links
- `/portfolio/analytics`
  - trend + contribution modules + attribution waterfall (`Preview` framing in navigation)
- `/portfolio/risk`
  - estimator cards/charts + methodology metadata + explainability (`Interpretation` framing in navigation)
- `/portfolio/reports`
  - quant scorecards + benchmark omission context + report lifecycle states + HTML preview
- `/portfolio/transactions`
  - ledger-event-only table and filters (v1 scope)

## Chart Composition and Storytelling Contract

- Home, Analytics, and Risk chart surfaces must use shared composition primitives for:
  - consistent panel/header/body spacing
  - responsive chart containers
  - short + long chart interpretation copy
- Route storytelling sequence:
  - Home: snapshot triage
  - Analytics: attribution and contribution diagnostics
  - Risk: methodology-sensitive interpretation
  - Quant/Reports: diagnostics + report artifact lifecycle
- Guardrails:
  - no mixed-unit risk chart on a single shared axis
  - no high-cardinality pie/donut usage for ranked contribution views
  - no workflow-critical actions hidden only in transient hover tooltips

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
- `lifecycle_status: ready | expired | unavailable`
- `scope: portfolio | instrument_symbol`
- `instrument_symbol: str | null`
- `period: 30D | 90D | 252D | MAX`
- `benchmark_symbol: str | null`
- `generated_at: datetime`
- `expires_at: datetime`
- `report_url_path: str`

Behavior notes:

- Report controls must expose explicit action lifecycle states (`loading`, `error`, `unavailable`, `ready`).
- Report generation and artifact preview are owned by `/portfolio/reports`; Home links to that route instead of owning workflow execution.

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
- `/portfolio/analytics`
  - empty when trend points or contribution rows are empty
- `/portfolio/risk`
  - empty when metrics are empty
  - explicit warning variants for unsupported or insufficient scope
- `/portfolio/reports`
  - quant scorecards: explicit loading/empty/error states
  - report lifecycle: explicit loading/error/unavailable/ready states
  - preview retry remains deterministic and keyboard accessible
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

- Home: KPI snapshot and drill-down links only (no report generation controls).
- Risk: interpretation-sensitive risk metrics with methodology context as primary surface.
- Quant/Reports: quant diagnostics, benchmark omission context, report lifecycle controls, and artifact preview.

## KPI Explainability and Labeling Contract

Promoted KPIs and key chart metrics must expose a shared explainability affordance that includes:

- definition
- why it matters
- interpretation guidance
- formula or basis
- comparison context
- caveats
- current-context note when data supports it

### Promoted KPI Baseline (Phase F)

| KPI | Route owner | Definition | Why it matters |
| --- | --- | --- | --- |
| Market value | Home | Total marked-to-market value of open positions from persisted snapshot coverage. | Establishes current portfolio size/exposure for top-level triage. |
| Unrealized gain | Home | Difference between current market value and open cost basis. | Shows whether open holdings are above/below entry basis. |
| Period change | Home | Latest portfolio value minus first value in selected period. | Signals short-to-medium directional movement before deeper attribution. |
| Top contribution PnL | Analytics | Per-symbol contribution to selected-period PnL. | Identifies strongest positive/negative drivers and concentration effects. |
| Risk estimator value | Risk | Windowed estimator output with methodology metadata. | Supports return-vs-risk interpretation with explicit calculation context. |
| Quant scorecard metrics | Quant/Reports | QuantStats-derived diagnostics scoped by period and benchmark context. | Supports advanced diagnostics and report workflow decisions. |

### Why-it-matters Copy Rules

- Keep `why it matters` tied to a user decision, not to implementation detail.
- Avoid generic phrasing (`important metric`) without action context.
- Mention comparison anchor when relevant (period, benchmark, threshold).
- Keep copy deterministic and consistent across routes for same KPI.

Naming guidance for ambiguous shorthand:

- `PnL` -> `Unrealized P&L vs cost basis`
- `Trendline` -> `Trend estimate`
- `S&P 500 Proxy` -> `S&P 500 benchmark (normalized)`
- `NASDAQ-100 Proxy` -> `NASDAQ-100 benchmark (normalized)`

## Action Placement and False-Affordance Policy

- Workflow actions must be persistent and testable (for example in panel/header action groups).
- Tooltip actions are informational only unless fully functional and duplicated in one stable surface.
- Non-functional analytical actions must not be rendered.
- `Analyze Risk` deep-link belongs to stable surfaces (for example Home trend action).
- `Export CSV` is only allowed when an explicit deterministic export contract is shipped.

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
