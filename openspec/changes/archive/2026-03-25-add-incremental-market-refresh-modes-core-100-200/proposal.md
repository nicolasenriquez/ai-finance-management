## Why

The repository already has a stable `yfinance` refresh path and a versioned symbol universe (`core`, `starter_100`, `starter_200`), but operational refresh still runs one fixed scope. We need a controlled onboarding path for real-data testing that expands coverage step-by-step without increasing risk abruptly.

## What Changes

- Add an explicit refresh scope mode (`core`, `100`, `200`) to the operator-facing refresh workflow, with `core` as the default for backward compatibility.
- Extend the local command surface (`market-refresh-yfinance`, `data-sync-local`) to accept a scope selector and propagate it through data-sync and market-data service boundaries.
- Keep fail-fast semantics and all-or-nothing provider ingest for each selected scope; no partial success behavior.
- Preserve and extend structured run evidence so outputs and logs identify which refresh scope was executed.
- Add test coverage and runbook guidance for staged real-data onboarding (`core -> 100 -> 200`) including explicit smoke evidence capture per stage.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `market-data-operations`: full-refresh behavior and outcome evidence are updated to support explicit scope modes (`core`, `100`, `200`) resolved from the existing versioned universe contract.
- `data-sync-operations`: local refresh/sync entrypoints are updated to accept and propagate refresh scope mode while preserving deterministic fail-fast stage order.

## Impact

- Affected code: `app/market_data/service.py`, `app/data_sync/service.py`, `scripts/data_sync_operations.py`, `justfile`, and relevant tests.
- Affected docs: `docs/guides/{yfinance-integration-guide.md,local-workflow-justfile.md,validation-baseline.md}`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, and `CHANGELOG.md`.
- Runtime behavior: refresh remains manual and schedule-ready, but operators can choose staged scope for controlled real-data onboarding.
- Non-goals: no scheduler/queue infrastructure, no public market-data API route expansion, no ledger/canonical mutation, and no market-value KPI/API/frontend expansion in this change.
