# Frontend API And UX Guide

## Purpose

This guide defines the implementation contract between backend portfolio APIs and frontend route behavior.
It documents the current workspace-first IA, state mapping rules, and methodology metadata surfaced to users.

## API Endpoints

- Summary: `GET /api/portfolio/summary`
- Lot detail: `GET /api/portfolio/lots/{instrument_symbol}`
- Time series: `GET /api/portfolio/time-series?period={30D|90D|252D|MAX}&scope={portfolio|instrument_symbol}&instrument_symbol={SYMBOL?}`
- Contribution: `GET /api/portfolio/contribution?period={30D|90D|252D|MAX}`
- Risk estimators: `GET /api/portfolio/risk-estimators?window_days={30|90|252}&period={30D|90D|252D|MAX}&scope={portfolio|instrument_symbol}&instrument_symbol={SYMBOL?}`
- Risk evolution: `GET /api/portfolio/risk-evolution?period={30D|90D|252D|MAX}&scope={portfolio|instrument_symbol}&instrument_symbol={SYMBOL?}`
- Return distribution: `GET /api/portfolio/return-distribution?period={30D|90D|252D|MAX}&scope={portfolio|instrument_symbol}&instrument_symbol={SYMBOL?}&bin_count={2..50}`
- Monte Carlo simulation: `POST /api/portfolio/monte-carlo`
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
  - estimator cards/charts + methodology metadata + explainability + drawdown/rolling/distribution modules (`Interpretation` framing in navigation)
- `/portfolio/reports`
  - quant scorecards + benchmark omission context + Monte Carlo workflow + report lifecycle states + HTML preview
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
- Query-scope rules are explicit:
  - `scope=portfolio` requires `instrument_symbol` to be omitted.
  - `scope=instrument_symbol` requires a non-empty canonical symbol value.
  - Unsupported `scope` values are explicit `422` validation failures.

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
- `timeline_context: { available, scope, instrument_symbol, period } | null`
- `guardrails: { mixed_units, unit_groups, guidance } | null`

Required per-metric methodology metadata:

- `estimator_id`
- `value`
- `window_days`
- `return_basis` (`simple` or `log`)
- `annualization_basis.kind` (`trading_days`)
- `annualization_basis.value` (default v1 basis `252`)
- `as_of_timestamp`
- `unit` (`percent | ratio | unitless`)
- `interpretation_band` (`favorable | caution | elevated_risk`)
- `timeline_series_id` (`str | null`)

Current v1 shipped estimator ids:

- `volatility_annualized`
- `max_drawdown`
- `beta`
- `downside_deviation_annualized`
- `value_at_risk_95`
- `expected_shortfall_95`

### Risk Evolution Response

- `as_of_ledger_at: datetime`
- `scope: portfolio | instrument_symbol`
- `instrument_symbol: str | null`
- `period: 30D | 90D | 252D | MAX`
- `rolling_window_days: int`
- `methodology: { drawdown_method, rolling_volatility_method, rolling_beta_method }`
- `drawdown_path_points: [{ captured_at, drawdown }]`
- `rolling_points: [{ captured_at, volatility_annualized, beta }]`

Behavior notes:

- Drawdown and rolling points are ordered by `captured_at` ascending.
- Rolling series values can be `null` when the rolling window has not been satisfied yet.

### Return Distribution Response

- `as_of_ledger_at: datetime`
- `scope: portfolio | instrument_symbol`
- `instrument_symbol: str | null`
- `period: 30D | 90D | 252D | MAX`
- `sample_size: int`
- `bucket_policy: { method, bin_count, min_return, max_return }`
- `buckets: [{ bucket_index, lower_bound, upper_bound, count, frequency }]`

Behavior notes:

- Bucket outputs are deterministic for equivalent persisted state + request parameters.
- Frontend must render `bucket_policy` context next to chart interpretation copy.

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
- `simulation_context_status: ready | unavailable | error`
- `simulation_context_reason: str | null`

Behavior notes:

- Report controls must expose explicit action lifecycle states (`loading`, `error`, `unavailable`, `ready`).
- Report generation and artifact preview are owned by `/portfolio/reports`; Home links to that route instead of owning workflow execution.

### Monte Carlo Response

- `as_of_ledger_at: datetime`
- `scope: portfolio | instrument_symbol`
- `instrument_symbol: str | null`
- `period: 30D | 90D | 252D | MAX`
- `simulation: { sims, horizon_days, seed, bust_threshold, goal_threshold }`
- `assumptions: { model, notes[] }`
- `summary: { start_value_usd, median_ending_value_usd, mean_ending_return, bust_probability, goal_probability, interpretation_signal }`
- `ending_return_percentiles: [{ percentile, value }]`
- `profile_comparison_enabled: bool`
- `calibration_context: { requested_basis, effective_basis, sample_size, lookback_start, lookback_end, used_fallback, fallback_reason }`
- `profile_scenarios: [{ profile_id, label, bust_threshold, goal_threshold, bust_probability, goal_probability, interpretation_signal }]`

Behavior notes:

- Requests are bounded and fail-fast (`422`) on invalid `sims`, `horizon_days`, `bust_threshold`, `goal_threshold`, or `seed`.
- Equivalent input state + seed must produce deterministic outputs.
- Insufficient aligned history remains explicit (`409`) and is not coerced.
- Profile comparison is rendered as a stable three-row matrix (`Conservative`, `Balanced`, `Growth`) for panoramic scan before deeper percentile drill-down.

## Normalization And Validation Rules

- Supported chart period enum is fixed to `30D`, `90D`, `252D`, `MAX`.
- Unsupported period query values must be normalized client-side before API call; unsupported backend responses remain explicit errors.
- Supported chart scope enum is fixed to `portfolio` and `instrument_symbol`.
- Client must not send `instrument_symbol` when scope is `portfolio`.
- Client must send non-empty `instrument_symbol` when scope is `instrument_symbol`.
- Monte Carlo envelope is bounded:
  - `sims: 250..5000`
  - `horizon_days: 5..756` (plus period-aware client caps)
  - `seed: 0..2147483647`
  - `bust_threshold: -0.95..0`
  - `goal_threshold: 0..3`
  - `enable_profile_comparison: boolean`
  - `calibration_basis: monthly | annual | manual`
  - when both thresholds are provided, `bust_threshold < goal_threshold`
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
  - Monte Carlo workflow: explicit unavailable/loading/error/ready states
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

## Dense-Table and Action-Density Contract (Phase G Extension 9.x)

- Quant lens must render as one semantic table with deterministic `30D`/`90D`/`252D` column alignment and tabular numeric rhythm.
- Quant report lifecycle controls must be grouped into one compact cluster:
  - scope selector(s)
  - primary generate action
  - lifecycle pill + stepper context
- Contribution tables must use explicit directional semantics labels:
  - `signed contribution`
  - `net share (vs net period)`
  - `absolute share`
- Hierarchy table must load sector groups collapsed by default and expose explicit sortable header controls with visible arrow state.

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
| Realized P&L | Home | Locked gain/loss from closed lots/events in persisted ledger history. | Distinguishes crystallized outcomes from floating mark-to-market values. |
| Period change (Period P&L) | Home | Latest portfolio value minus first value in selected period. | Signals short-to-medium directional movement before deeper attribution. |
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

Portfolio semantic boundary:

- Use investment P&L semantics (`realized`, `unrealized`, `period change`, `total return`) in workspace KPI copy.
- Do not introduce business income-statement lines (`COGS`, `OPEX`, `EBITDA`) as portfolio KPI fields in this workspace contract.

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
