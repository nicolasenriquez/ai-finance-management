## Why

The repository has already delivered the market-data persistence boundary, the `yfinance` provider path, and the operator refresh workflow needed to populate persisted price history. The next Phase 6 step is to use that persisted market data to expand portfolio analytics with explicit market-enriched KPIs, instead of keeping the summary contract permanently limited to ledger-only fields.

## What Changes

- Expand the grouped portfolio summary contract with market-enriched KPI fields derived from persisted ledger truth plus persisted market-data snapshots.
- Expose explicit pricing provenance in analytics responses so clients can see which market-data snapshot or pricing timestamp was used.
- Keep valuation behavior fail-fast and bounded: no ledger mutation, no public market-data routes, no FX-sensitive inference beyond the approved current pricing contract.
- Add backend tests, API/schema updates, and frontend contract/documentation updates for the enriched summary behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `portfolio-analytics`: Extend the grouped portfolio analytics contract from ledger-only KPIs to include explicit market-enriched valuation fields and pricing provenance.

## Impact

- Affected code: `app/portfolio_analytics/`, selective read helpers in `app/market_data/`, portfolio analytics tests, and frontend summary contract/rendering code.
- Affected APIs: `GET /api/portfolio/summary` response schema and related frontend API typings/tests.
- Affected docs: `docs/product/{roadmap.md,decisions.md,frontend-mvp-prd-addendum.md}`, `docs/guides/{portfolio-ledger-and-analytics-guide.md,validation-baseline.md}`, and `CHANGELOG.md`.
- Systems: persisted market-data snapshot selection, validation evidence, and the Phase 6 handoff from operator refresh readiness into analytics consumption.
