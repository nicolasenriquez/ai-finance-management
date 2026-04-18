# Trading Dashboard LLM Wiki

## Purpose

This is the canonical product and implementation-reference wiki for the compact trading dashboard rebuilt under:

- `openspec/changes/archive-v0-and-build-compact-trading-dashboard`

Use this wiki for:

- final preserve list
- final information architecture
- financial decision framework
- source-policy and provenance rules
- route/chart grammar constraints

## Refinement Priority

The implementation-facing route/storytelling memo is:

- [portfolio-dashboard-third-pass-refinement.md](./portfolio-dashboard-third-pass-refinement.md)

The third-pass memo and this wiki must stay aligned. This wiki is the broader business/source-policy reference; the third-pass memo is the route-composition steering artifact.

## Final Product Shape (Implemented)

The active frontend is a compact five-route dashboard shell:

1. `/portfolio/home`
2. `/portfolio/analytics`
3. `/portfolio/risk`
4. `/portfolio/signals` (visible label may be `Opportunities`)
5. `/portfolio/asset-detail/:ticker`

Default landing route:

- `/portfolio/home`

## Route Jobs and First-Surface Questions

### `/portfolio/home`

Primary question:

- How is my portfolio doing right now?

First-surface modules:

- KPI strip
- equity curve vs benchmark
- immediate attention panel
- top movers

Secondary modules:

- allocation snapshot
- holdings summary
- compact report utility disclosure

### `/portfolio/analytics`

Primary question:

- Why did the portfolio move?

First-surface modules:

- performance curve
- attribution waterfall
- contribution leaders

Secondary modules:

- monthly heatmap
- rolling return chart
- drill-down table

### `/portfolio/risk`

Primary question:

- How fragile is the portfolio?

First-surface modules:

- risk posture
- drawdown timeline
- return distribution

Secondary modules:

- risk/return scatter
- correlation heatmap
- concentration table

### `/portfolio/signals`

Primary question:

- Which opportunities deserve review?

First-surface modules:

- trend regime summary
- momentum ranking
- technical signals table
- watchlist panel

### `/portfolio/asset-detail/:ticker`

Primary question:

- What is happening with this asset?

First-surface modules:

- asset hero
- price action
- price-volume combo

Secondary modules:

- position detail
- benchmark-relative chart
- asset risk metrics
- narrative notes

Rule:

- Candlestick treatment is isolated to asset-detail.

## Final Preserve List (Behavior, Not Legacy Layout)

Preserve:

- hierarchy pivot behavior (grouped rows, expand/collapse, deterministic sort posture)
- compact report utility behavior (`Generate HTML report`, `Export analyst pack (.md)`)
- explicit lifecycle-state copy patterns (`loading`, `empty`, `ready`, `stale`, `unavailable`, `blocked`, `error`)
- typed finance-safe formatting and API boundaries that still pay rent

Do not preserve:

- route-heavy legacy workspace shell patterns
- repeated same-question visuals in first viewport

## Financial Decision Framework

The dashboard should encode this sequence:

1. Qualify the business fundamentally.
2. Confirm setup and timing context.
3. Size/guard risk before promotion.
4. Resolve decision state (`buy`, `add`, `wait`, `avoid`, `unavailable`).
5. Expose evidence/provenance for auditability.

Primary module storytelling contract:

- `what`
- `why`
- `action`
- `evidence`

## Source Policy Decisions (Canonical)

### Non-negotiable policy

- `yfinance` is the primary data source in this phase.
- `pandas` is transformation-only (not a source-of-truth provider).
- Every decision-relevant metric must show provenance/freshness metadata.
- Unsupported/proprietary signals must render explicit `unavailable`.

### Source contracts

- `market_prices`: OHLCV/time-series and related market context
- `fundamentals`: valuation/quality ratios and statement-derived context
- `reference_metadata`: symbol/session/reference context
- `derived_signals`: deterministic outputs computed from direct contracts

### Provenance UX contract

Each surfaced metric family should expose:

- `source_id`
- `as_of`
- `freshness_state` (`fresh`, `stale`, `delayed`, `unavailable`)
- `confidence_state` (`direct`, `derived`, `proxy`)

If freshness/confidence degrades, action guidance must downgrade instead of silently preserving high-confidence states.

## YFinance-First Extraction Map

### Direct (from yfinance)

- OHLCV / bars / session price context
- corporate actions (dividends/splits/actions)
- option-chain implied volatility context
- screener-backed valuation and quality fields where available (for example `P/E`, `PEG`, `P/B`, `ROE`, `ROA`, debt-to-equity, current ratio)

### Derived (from pandas over yfinance direct data)

- ATR and volatility context
- moving-average regime (for example 50D/200D state)
- support/resistance heuristics
- rolling return windows and benchmark spread
- drawdown depth/duration
- correlation and distribution summaries

### Explicitly non-native (render unavailable until custom contract exists)

- `J5`
- `JR4`
- green-on-green / red-on-red proprietary labels
- historical IV percentile as a first-class native feed
- custom exhaustion labels without declared deterministic rule contract

## Derivation Formulas (Implementation Contract)

Use deterministic formulas only:

- return: `(close_t / close_t-1) - 1`
- rolling return window: `(close_t / close_t-n) - 1`
- drawdown: `(close_t / running_max(close)) - 1`
- ATR: rolling mean of true-range series
- MA regime: relative ordering of short/long moving averages with explicit window parameters
- benchmark spread: `portfolio_return - benchmark_return`

All derivations should remain reproducible from direct source inputs.

## Route-Specific Chart Grammar

- `/portfolio/home`: line/track-based trend + compact tables/cards; no tactical candlestick dominance
- `/portfolio/analytics`: line (performance), waterfall (attribution), heatmap (monthly consistency), table (drill-down exactness)
- `/portfolio/risk`: area/list timeline (drawdown), histogram/distribution table (returns), scatter (risk/return), heatmap/table (correlation)
- `/portfolio/signals`: ranked lists and compact tactical tables; tactical overlays stay secondary to executive and risk routes
- `/portfolio/asset-detail/:ticker`: candlestick/price-action and price-volume combo are allowed and expected

Avoid across routes:

- decorative 3D
- gauge/radar novelty surfaces
- repeated visual encodings that answer the same question

## State and Reliability Rules

- Primary modules must support explicit loading/empty/unavailable/error/success feedback.
- Retryable failures must recover module rendering without shell collapse.
- Failure isolation is module-bounded; one degraded module must not take down the whole route.

## Validation Expectations

Before closeout, frontend must pass:

- `test`
- `lint` (or strict type-check gate)
- `build`

OpenSpec strict validation must be green for the change package.
