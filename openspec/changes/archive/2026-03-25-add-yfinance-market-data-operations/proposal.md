## Why

The repository now has a working `yfinance` adapter and a durable market-data ingestion boundary, but it still lacks an operator-safe workflow for actually populating and refreshing market data in a repeatable way. Since `yfinance` is the current time-efficient and cost-efficient source for this project, the next slice should make that single-provider path operational before introducing broader provider abstractions.

## What Changes

- Add a `yfinance`-backed market-data operations slice that refreshes the supported symbol universe through one explicit manual workflow, with scheduling posture documented but not overbuilt.
- Define the current source-of-symbol-truth rule for refresh operations so the system knows exactly which symbols should be fetched now and how that scope stays aligned with current `dataset_1` / persisted ledger support.
- Add operator-facing execution rules for full refresh runs, explicit success/failure reporting, and deterministic snapshot provenance so refresh behavior is reproducible and auditable.
- Keep `yfinance` as the intentional current provider path for this phase, while documenting multi-provider expansion as a later follow-up rather than a requirement of this change.
- Update roadmap, backlog, validation guidance, and market-data documentation so the current Phase 6 direction reflects `yfinance` operationalization rather than premature broker-authenticated expansion.

## Capabilities

### New Capabilities
- `market-data-operations`: Manual and schedule-ready market-data refresh workflow for the supported symbol universe using the existing persistence and provenance contracts.

### Modified Capabilities
- `market-data-provider-adapter`: Clarify that `yfinance` is the current operational provider for this phase and that refresh orchestration must preserve its existing fail-fast, deterministic, and non-partial ingest rules.

## Impact

- Affected code: `app/market_data/` orchestration boundaries, configuration, operator entrypoints, and tests.
- Affected runtime behavior: market-data refresh becomes a first-class operational workflow rather than an internal helper-only path.
- Affected systems: current market-data population workflow, local operator validation flow, and documentation for Phase 6 planning.
- Affected docs: `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md}`, `docs/standards/yfance-standard.md`, and `CHANGELOG.md`.
- Non-goals for this change: no broker-authenticated provider integration, no transaction-import reconciliation, no public market-data API expansion, no portfolio valuation/unrealized KPI expansion, and no frontend market-value UI changes.
