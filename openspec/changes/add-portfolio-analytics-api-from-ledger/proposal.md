## Why

The repository now has persisted canonical records, a derived portfolio ledger, and a frozen dataset-1 v1 accounting policy, but it still lacks a consumable analytics API for grouped portfolio views and lot-level drill-down. This is the next natural step because Phase 4 depends on exposing trustworthy portfolio analytics from ledger truth before any frontend MVP can be connected.

## What Changes

- Add a portfolio analytics service layer that computes grouped portfolio summaries from derived ledger and lot state.
- Add typed FastAPI endpoints for grouped portfolio analytics and lot-level detail views.
- Freeze a first analytics contract that is explicitly explainable from ledger truth and does not silently depend on missing market data.
- Add unit and integration coverage for analytics formulas, response shapes, and end-to-end API behavior.
- Update product and validation documentation to record the analytics API boundary and its initial KPI scope.

## Capabilities

### New Capabilities
- `portfolio-analytics`: Ledger-backed grouped portfolio analytics and lot-detail API responses for the Phase 4 MVP boundary.

### Modified Capabilities
- `portfolio-ledger`: Clarify that Phase 4 analytics consume ledger and lot truth without changing canonical ledger derivation behavior.

## Impact

- Affected code: new `app/portfolio_analytics/` feature slice, router registration in `app/main.py`, analytics tests, and possible shared schemas only if reused by 3+ slices.
- Affected APIs: new FastAPI analytics endpoints for grouped portfolio data and lot-level detail.
- Dependencies: existing PostgreSQL ledger tables (`portfolio_transaction`, `dividend_event`, `lot`, `lot_disposition`) and async SQLAlchemy access patterns.
- Systems: documentation, validation baseline, OpenSpec specs/tasks, and later frontend integration planning.
