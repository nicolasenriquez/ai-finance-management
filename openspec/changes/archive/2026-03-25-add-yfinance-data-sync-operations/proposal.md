## Why

The previous Phase 6 slice made `yfinance` refresh available at the service seam, but operational usage is still brittle and incomplete. A live smoke run exposed a real adapter-shape failure (`unsupported trading-date key for symbol 'AMD'`), and there is still no standardized local operator command flow to bootstrap `dataset_1` and refresh market data in one reproducible workflow.

## What Changes

- Harden the `yfinance` adapter normalization path so runtime `Close` payload shapes (series and tabular forms) map deterministically to trading-date keys and fail fast on unmappable rows.
- Add explicit local operator workflows for:
  - `dataset_1` bootstrap (ingest -> persist -> ledger rebuild)
  - full supported-universe market refresh via `yfinance`
  - combined local sync that runs both workflows in deterministic order.
- Expose these workflows through repo-native command surfaces (`just`) without introducing a new public market-data API route in this slice.
- Standardize run-result evidence (requested scope, provider/source identity, success/failure, and key counters) so local sync operations are auditable.
- Update roadmap/backlog/guides so Phase 6 execution reflects `yfinance`-first operational sync before multi-provider or broker-auth expansion.

## Capabilities

### New Capabilities
- `data-sync-operations`: Local operator command workflows for `dataset_1` bootstrap and `yfinance` market-data refresh with deterministic sequencing and explicit run evidence.

### Modified Capabilities
- `market-data-provider-adapter`: tighten normalization requirements for runtime `yfinance` payload shapes so symbol/time mapping remains safe and deterministic.
- `market-data-operations`: formalize operator entrypoints for refresh/sync execution while preserving fail-fast and non-partial semantics.

## Impact

- Affected code: `app/market_data/providers/yfinance_adapter.py`, `app/market_data/service.py`, command-entrypoint modules, and `justfile` recipes.
- Affected runtime behavior: local operators can execute one reproducible data-sync flow; refresh failures caused by payload-shape ambiguity become explicit and actionable.
- Affected docs: `docs/product/{roadmap.md,backlog-sprints.md}`, `docs/guides/{yfinance-integration-guide.md,validation-baseline.md,local-workflow-justfile.md}`, and `CHANGELOG.md`.
- Non-goals: no broker-authenticated providers, no background scheduler/queue infrastructure, no public market-data router in `app/main.py`, and no frontend valuation/UI expansion.
