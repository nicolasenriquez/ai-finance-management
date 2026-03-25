# YFinance Integration Guide

## Purpose

This guide defines how to use `yfinance` as the first external market-data provider in a way that fits current repository boundaries.

Use this guide for planning and implementation of Sprint `5.2` provider integration.

## Current Implementation Status (2026-03-25)

Implemented now:

- Adapter module: `app/market_data/providers/yfinance_adapter.py`
- Service orchestration entrypoint: `app/market_data/service.py::ingest_yfinance_daily_close_snapshot`
- Service-level full-refresh workflow: `app/market_data/service.py::refresh_yfinance_supported_universe`
- Supported-universe resolver: `app/market_data/service.py::list_supported_market_data_symbols`
- Local operator CLI entrypoints: `scripts/data_sync_operations.py` (`data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local`)
- Local operator just recipes: `just data-bootstrap-dataset1`, `just market-refresh-yfinance`, `just data-sync-local`
- Settings surface: `market_data_yfinance_period`, `market_data_yfinance_interval`, `market_data_yfinance_timeout_seconds`, `market_data_yfinance_max_retries`, `market_data_yfinance_retry_backoff_seconds`, `market_data_yfinance_auto_adjust`, `market_data_yfinance_repair`

First-slice semantics frozen in code:

- `interval` must be `1d`
- `price_value` is provider `Close`
- time key is `trading_date` (not `market_timestamp`)
- `auto_adjust` must be `False`
- `repair` must be `False`
- requested symbol coverage is all-or-nothing
- close-payload normalization supports both series and tabular runtime shapes; unsupported shapes fail fast

Automated coverage is deterministic:

- unit and integration tests use mocks/monkeypatching for provider behavior
- CI validation does not depend on live yfinance network calls

Operational posture in this slice:

- refresh orchestration is implemented at the service boundary and exposed through local command entrypoints
- combined local sync is deterministic and fail-fast (`bootstrap -> refresh`; refresh is skipped if bootstrap fails)
- scheduler/queue infrastructure is intentionally deferred
- public market-data route surface remains deferred in this change

## Scope and Non-Goals

In scope:

- fetch quote/history data from `yfinance`
- normalize provider responses into current market-data write contracts
- ingest via `app/market_data.service.ingest_market_data_snapshot`

Out of scope:

- replacing canonical transaction or ledger truth
- adding valuation KPIs or public market-data routes
- using live provider calls as the only test strategy

## Official Source Baseline

Primary references:

- https://ranaroussi.github.io/yfinance/index.html
- https://ranaroussi.github.io/yfinance/reference/yfinance.functions.html
- https://ranaroussi.github.io/yfinance/reference/index.html
- https://github.com/ranaroussi/yfinance

Legal and usage notes linked by provider docs/repository:

- https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm
- https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html

## Repository Contract to Preserve

Current write contract (already implemented):

- `source_type`
- `source_provider`
- `snapshot_key`
- `snapshot_captured_at`
- `prices[]` rows with:
  - `instrument_symbol`
  - exactly one of `market_timestamp` or `trading_date`
  - `price_value`
  - `currency_code`
  - optional `source_payload`

Current safety constraints:

- symbol set anchored to dataset-1 forms
- in-request duplicate symbol/time rejection
- deterministic insert-or-update behavior
- non-mutation of canonical/ledger/lot truth

## Suggested Adapter Boundary

Recommended execution shape:

1. `fetch` raw provider data
2. `normalize` raw responses to internal typed rows
3. `ingest` through `ingest_market_data_snapshot`

Keep provider specifics in one adapter module. Do not spread `yfinance` logic across service layers.

## Normalization Rules

- Normalize symbols to canonical uppercase while preserving valid punctuation (for example `BRK.B`).
- Do not infer missing symbols.
- Use explicit snapshot capture time in UTC.
- Use one market-time key per row:
  - prefer `market_timestamp` when provider returns timestamped bars
  - use `trading_date` for day-level series when timestamp precision is not meaningful
- Preserve provider raw fields in `source_payload` for audit/debug where useful.

## YFinance Fetch Defaults (First Slice)

Implemented defaults and constraints for deterministic behavior:

- day-level data only (`interval=1d`)
- explicit period from configuration (`market_data_yfinance_period`, default `5y`)
- explicit timeout and bounded retry/backoff
- explicit symbol list from supported universe
- no broad multi-feature payload expansion in this slice

When evaluating function options from official docs:

- confirm timezone behavior for combined downloads
- document and justify `auto_adjust` choice
- document and justify `repair` behavior

## Snapshot Key Strategy

`snapshot_key` should be deterministic and reproducible.

Current implemented format:

- `yf|d1|<interval>|<period>|aa<0|1>rp<0|1>|<snapshot-date>|s<symbol-count>|<symbol-fingerprint>`

Example:

- `yf|d1|1d|5y|aa0rp0|2026-03-24|s1|c7d3f5d6a5e2`

`symbol-fingerprint` is a bounded hash of the normalized symbol set to keep `snapshot_key` within the `String(128)` database constraint.

## Error Handling and Retries

- Missing/invalid provider response shape: fail fast with explicit client error.
- Network/provider transient failures: bounded retries with explicit logging.
- Hard provider failures: fail request explicitly; do not ingest partial rows silently.

## Logging Guidance

Use structured events with repository naming pattern.

Current service-level provider ingest events:

- `market_data.provider_ingest_started`
- `market_data.provider_ingest_completed`
- `market_data.provider_ingest_failed`

Include:

- `source_provider`
- `snapshot_key`
- symbol count
- duration where available
- error type/message on failures

## Testing Strategy

Required:

- unit tests for normalization and mapping edge cases
- unit tests for duplicate symbol/time detection behavior through service boundary
- integration tests proving non-mutation of canonical/ledger truth

Recommended:

- fixture-based adapter tests using saved provider response snapshots
- no live external calls in default CI path

Optional manual verification:

- one explicit local command to fetch live data for smoke checks (for example `uv run python -m scripts.data_sync_operations market-refresh-yfinance` or `just market-refresh-yfinance`)
- one explicit combined local sync smoke run (`uv run python -m scripts.data_sync_operations data-sync-local` or `just data-sync-local`)
- manual checks must not replace deterministic automated tests

## Security and Configuration

- read provider settings (timeouts, retries, optional tokens) from environment config
- do not hardcode credentials
- do not log secrets

## Secondary References (Context Only)

These links are useful for quick orientation but are not authoritative:

- https://algotrading101.com/learn/yfinance-guide/
- https://www.geeksforgeeks.org/python/how-to-use-yfinance-api-with-python/
