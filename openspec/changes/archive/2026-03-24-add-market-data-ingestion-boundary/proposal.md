## Why

The next roadmap phase depends on adding market data without weakening the ledger-first trust boundary that is already in place. The repository also has a workflow gap because global OpenSpec spec validation is still red for legacy spec-format reasons, which will reduce planning and archive confidence for future changes if left unaddressed.

## What Changes

- Add a dedicated market-data ingestion boundary that stores quotes and price history separately from canonical transactions, ledger truth, and derived analytics tables.
- Define idempotent market-data refresh behavior with explicit source provenance, snapshot timestamps, and read-only downstream consumption expectations.
- Anchor the first market-data slice to the instrument universe already present in persisted `dataset_1` ledger truth, including current symbol-format edge cases such as dotted tickers like `BRK.B`.
- Clarify that current portfolio analytics remain ledger-only and must not expand into valuation or FX-sensitive KPIs as part of this change.
- Add implementation and validation tasks to normalize the current OpenSpec spec-format baseline for legacy `pdf-ingestion` and `pdf-preflight-analysis` specs so `openspec validate --specs --all` can become a trustworthy repo gate again.

## Capabilities

### New Capabilities
- `market-data-ingestion`: Persistence and refresh boundary for quote and price-history data that remains separate from transaction and ledger truth.

### Modified Capabilities

## Impact

- Affected code: new backend feature slice for market-data schemas/models/services/tests plus migrations and supporting configuration.
- Affected systems: PostgreSQL schema, future broker API ingestion boundary, analytics read path contracts, and validation workflow.
- Affected docs: roadmap/backlog alignment, ledger-and-analytics guidance, database standards as needed, validation baseline, and changelog.
- Initial scope guardrail: the first persistence boundary must support the current `dataset_1` instrument set (`AMD`, `APLD`, `BBAI`, `BRK.B`, `GLD`, `GOOGL`, `HOOD`, `META`, `NVDA`, `PLTR`, `QQQM`, `SCHD`, `SCHG`, `SMH`, `SOFI`, `SPMO`, `TSLA`, `UUUU`, `VOO`) before broader source expansion.
- Non-goals for this change: no live provider integration, no valuation API expansion, no frontend market-value UI, no FX-rate support, and no mutation of canonical or ledger rows during quote refresh.
