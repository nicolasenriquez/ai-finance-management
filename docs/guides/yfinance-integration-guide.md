# YFinance Integration Guide

## Purpose

This guide defines how to use `yfinance` as the first external market-data provider in a way that fits current repository boundaries.

Use this guide for planning and implementation of Sprint `5.2` provider integration.

## Current Implementation Status (2026-03-26)

Implemented now:

- Adapter module: `app/market_data/providers/yfinance_adapter.py`
- Service orchestration entrypoint: `app/market_data/service.py::ingest_yfinance_daily_close_snapshot`
- Service-level full-refresh workflow: `app/market_data/service.py::refresh_yfinance_supported_universe`
- Supported-universe resolver: `app/market_data/service.py::list_supported_market_data_symbols`
- Starter-library resolver: `app/market_data/service.py::list_market_data_library_symbols` (sizes `100` / `200`)
- Refresh-scope selector contract: `core` (default), `100`, `200` propagated through market-data service, data-sync service, CLI, and just recipes
- Local operator CLI entrypoints: `scripts/data_sync_operations.py` (`data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local`)
- Symbol-universe generator: `scripts/build_market_symbol_universe.py`
- Local operator just recipes: `just data-bootstrap-dataset1`, `just market-refresh-yfinance`, `just data-sync-local`
- Local symbol-universe build recipe: `just market-symbol-universe-build`
- Settings surface: `market_data_yfinance_period`, `market_data_yfinance_interval`, `market_data_yfinance_timeout_seconds`, `market_data_yfinance_max_retries`, `market_data_yfinance_retry_backoff_seconds`, `market_data_yfinance_request_spacing_seconds`, `market_data_yfinance_history_fallback_periods`, `market_data_yfinance_default_currency`, `market_data_yfinance_auto_adjust`, `market_data_yfinance_repair`, `market_data_symbol_universe_path`

First-slice semantics frozen in code:

- `interval` must be `1d`
- `price_value` is provider `Close`
- time key is `trading_date` (not `market_timestamp`)
- `auto_adjust` must be `False`
- `repair` must be `False`
- requested symbol coverage is all-or-nothing
- semantic recovery is bounded and explicit:
  - empty-history fallback ladder: `5y -> 3y -> 1y -> 6mo` by default
  - missing currency metadata fallback: configured default currency (`USD` by default)
  - explicit invalid currency metadata remains fail-fast
- close-payload normalization supports both series and tabular runtime shapes; unsupported shapes fail fast
- approved day-level temporal-key variants are explicit and bounded: `date`/`datetime`, values with `to_pydatetime()` returning `date`/`datetime`, and scalar values exposing `item()` that resolve to `date`/`datetime`

Automated coverage is deterministic:

- unit and integration tests use mocks/monkeypatching for provider behavior
- CI validation does not depend on live yfinance network calls

Operational posture in this slice:

- refresh orchestration is implemented at the service boundary and exposed through local command entrypoints
- refresh orchestration supports staged onboarding scopes (`core`, `100`, `200`) with explicit selector validation; current smoke closeout scope is `core -> 100` and records `200` as deferred follow-up in this cycle
- combined local sync is deterministic and fail-fast (`bootstrap -> refresh`; refresh is skipped if bootstrap fails)
- scheduler/queue infrastructure is intentionally deferred
- public market-data route surface remains deferred in this change
- operator smoke evidence is explicit:
  - success paths use typed refresh/sync result models
  - blocked paths use structured fail-fast payload (`status`, `stage`, `status_code`, `error`)
- symbol-universe scope is explicit and versioned in `app/market_data/symbol_universe.v1.json`:
  - `core_refresh_symbols`: current fail-fast refresh scope (must include all portfolio symbols)
  - `starter_100_symbols` / `starter_200_symbols`: reusable library for expansion planning and controlled onboarding

Current live smoke evidence snapshot (2026-03-26):

- artifact: `docs/evidence/market-data/staged-live-smoke-2026-03-26.md`
- standalone `core`: blocked (`502`, TSLA currency metadata access failure)
- standalone `100`: blocked (`408`, bounded operator timeout at 360s)
- combined `data-sync-local --refresh-scope core`: completed with typed evidence payload
- `200`: deferred from this smoke closeout scope and tracked as follow-up

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
- explicit timeout and bounded retry/backoff (`market_data_yfinance_max_retries` defaults to `1`)
- explicit ordered history fallback ladder (`market_data_yfinance_history_fallback_periods`)
- explicit default-currency fallback for missing metadata (`market_data_yfinance_default_currency`)
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

When one or more symbols recover through shorter fallback periods, `snapshot_key` remains anchored to the originally requested contract. Effective fallback periods are recorded in metadata/evidence (`history_fallback_periods_by_symbol`) instead of changing snapshot identity.

## Error Handling and Retries

- Missing/invalid provider response shape: fail fast with explicit client error.
- Network/provider transient failures: bounded retries with explicit logging.
- Semantic empty-history failures: try configured ordered fallback periods before final symbol failure.
- Missing currency metadata after approved reads: apply configured default currency and record `currency_assumed_symbols`.
- Explicit unsupported currency values: fail fast; do not replace with default currency.
- Hard provider failures: fail request explicitly; do not ingest partial rows silently.
- Unexpected provider exceptions are surfaced with compact error reason text in 502 responses to improve blocker evidence quality.

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

- run staged refresh smoke sequence with explicit scope:
  - `uv run python -m scripts.data_sync_operations market-refresh-yfinance --refresh-scope core`
  - `uv run python -m scripts.data_sync_operations market-refresh-yfinance --refresh-scope 100`
  - equivalent just commands: `just market-refresh-yfinance "" core`, `just market-refresh-yfinance "" 100`
- run one explicit combined local sync smoke run with scope when needed (`uv run python -m scripts.data_sync_operations data-sync-local --refresh-scope core` or `just data-sync-local "" "" core`)
- for successful smoke runs, capture typed evidence (`refresh_scope_mode`, `source_provider`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, `updated_prices`, `retry_attempted_symbols`, `failed_symbols`, `history_fallback_symbols`, `history_fallback_periods_by_symbol`, `currency_assumed_symbols`)
- for blocked smoke runs, capture structured fail-fast payload (`status`, `stage`, `status_code`, `error`) plus selected scope and treat it as blocker evidence instead of partial success
- for deferred scopes, record explicit deferral reason and follow-up target instead of implying readiness
- manual checks must not replace deterministic automated tests

## Security and Configuration

- read provider settings (timeouts, retries, optional tokens) from environment config
- do not hardcode credentials
- do not log secrets

## Secondary References (Context Only)

These links are useful for quick orientation but are not authoritative:

- https://algotrading101.com/learn/yfinance-guide/
- https://www.geeksforgeeks.org/python/how-to-use-yfinance-api-with-python/
