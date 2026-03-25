## Why

The market-data ingestion boundary is now implemented, but the repository still lacks the first real external provider adapter needed to prove that boundary against live provider semantics. Sprint 5.2 is the next roadmap item, and `yfinance` is the lowest-friction first provider for validating fetch, normalization, provenance, and fail-fast behavior without expanding ledger truth or frontend valuation scope.

## What Changes

- Add the first external market-data provider adapter using `yfinance` for historical and reference price retrieval across the current `dataset_1` symbol universe.
- Normalize `yfinance` responses into the existing `app/market_data` ingestion contract with explicit `source_type`, `source_provider`, `snapshot_key`, symbol/time-key rules, and frozen first-slice price semantics.
- Add provider configuration, runtime isolation for provider fetches, structured logging, and explicit failure behavior for invalid payloads, provider outages, or unsafe symbol/time normalization cases.
- Define deterministic snapshot identity inputs and all-or-nothing batch behavior so one unsafe provider row cannot silently produce a partial persisted snapshot.
- Add deterministic tests using fixtures or mocked provider responses so automated validation does not depend on live network access.
- Update implementation-facing documentation and delivery records to reflect the first provider adapter and its non-goals.

## Capabilities

### New Capabilities
- `market-data-provider-adapter`: External provider fetch and normalization boundary that feeds the existing market-data ingestion slice, with `yfinance` as the first supported adapter.

### Modified Capabilities

## Impact

- Affected code: `app/market_data/` service boundaries, provider adapter modules, schemas if needed, configuration, and tests.
- Affected dependencies: add `yfinance` as an application dependency if not already present.
- Affected runtime behavior: async request handling must not be blocked by provider fetches, and provider batch failures must remain explicit rather than degrading into partial persistence.
- Affected systems: external market-data fetch flow, internal market-data persistence path, and repository validation strategy for provider-backed behavior.
- Affected docs: roadmap/backlog alignment, provider standards/guides, validation baseline, and changelog.
- Non-goals for this change: no broker transaction import, no canonical transaction mutation, no valuation or FX analytics expansion, no frontend market-value UI, and no live-network dependency in CI.
