## Why

Phase 6 remains blocked by concrete live `yfinance` behavior on required and starter symbols: some symbols return empty history for the configured `5y` period even though they may have shorter available history, and some symbols return valid price rows without currency metadata. The next change must absorb those operational gaps safely and explicitly before market-enriched analytics can be treated as ready.

## What Changes

- Add a bounded shorter-period history fallback ladder for `empty history` responses so the adapter can retry the same symbol with narrower periods before classifying it as failed.
- Add an auditable operational currency fallback for missing `yfinance` currency metadata, defaulting to `USD` for the current provider path only when price rows are otherwise valid and no explicit invalid currency is returned.
- Cap per-symbol recovery pressure by separating transport retries from semantic fallbacks, keeping both bounded and configurable.
- Extend refresh outcome evidence so operators can see which symbols used shorter-history fallback and which symbols used assumed default currency, alongside the existing retry and failed-symbol diagnostics.
- Update deterministic tests, operational docs, and validation guidance for the new recovery contract.
- Keep current non-goals explicit: no market-enriched analytics expansion, no public market-data routes, no scheduler/queue infrastructure, and no mutation of canonical or ledger truth.

## Capabilities

### New Capabilities

### Modified Capabilities
- `market-data-provider-adapter`: Expand the approved live-provider recovery contract to include bounded shorter-period history fallback, auditable default-currency assignment, and explicit caps on per-symbol recovery attempts.
- `market-data-operations`: Extend staged refresh controls and typed run evidence so recovery behavior remains auditable while `core` stays strict and `100/200` preserve bounded non-portfolio tolerance.

## Impact

- Affected code: `app/core/config.py`, `app/market_data/{providers/yfinance_adapter.py,service.py,schemas.py}`, and related tests.
- Affected runtime behavior: required symbols such as `QQQM` may recover through shorter-period history fetches, and symbols with valid rows but missing currency metadata may continue with explicit default `USD` assignment under the approved operational contract.
- Affected docs: `docs/guides/{yfinance-integration-guide.md,validation-baseline.md}`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `README.md`, and `CHANGELOG.md`.
- Follow-on leverage: this is the operational stabilization step needed before a later proposal can expand portfolio analytics to market-enriched valuation metrics.
