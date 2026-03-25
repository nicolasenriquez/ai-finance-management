## 1. Investigation and scope contract freeze

- [x] 1.1 Confirm current roadmap/backlog/guides alignment for Sprint 5.2 and freeze the incremental refresh contract (`core`, `100`, `200`) with `core` as default.
Notes: Confirmed current phase alignment from `docs/product/{roadmap.md,backlog-sprints.md}` and operator guidance in `docs/guides/yfinance-integration-guide.md`; scope expansion remains inside Sprint 5.2 operational hardening.
Notes: Existing implementation already ships versioned universe sets (`core_refresh_symbols`, `starter_100_symbols`, `starter_200_symbols`) and this change freezes runtime selection to those three modes only.
- [x] 1.2 Define the typed refresh-scope value set and the minimum structured evidence fields required for stage-aware runs.
Notes: Typed selector contract frozen in design/spec artifacts as `refresh_scope_mode: Literal["core", "100", "200"]` with explicit rejection for unsupported values.
Notes: Minimum evidence contract frozen for success (`refresh_scope_mode`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, `updated_prices`) and refresh-stage failure (`status`, `stage`, `status_code`, `error`, `refresh_scope_mode`).

## 2. Market-data orchestration updates

- [x] 2.1 Add scope-aware symbol resolution in `app/market_data/service.py` so refresh can resolve `core_refresh_symbols`, `starter_100_symbols`, or `starter_200_symbols` deterministically.
Notes: Added typed refresh-scope normalization (`core|100|200`) and deterministic resolver mapping (`core -> list_supported_market_data_symbols`, `100/200 -> list_market_data_library_symbols`).
- [x] 2.2 Update `refresh_yfinance_supported_universe` orchestration to accept optional scope mode, default to `core`, and preserve fail-fast all-or-nothing behavior.
Notes: `refresh_yfinance_supported_universe` now accepts optional `refresh_scope_mode`, rejects unsupported values before provider ingest, and defaults to `core`.
- [x] 2.3 Extend market-data refresh run evidence/log context to include selected scope mode and requested symbol count.
Notes: Extended `MarketDataRefreshRunResult` with `refresh_scope_mode` and `requested_symbols_count`; propagated both fields to refresh logs and structured outcomes.
- [x] 2.4 Add/adjust unit and integration tests for scope resolution, default behavior, and non-mutation/idempotency guarantees.
Notes: Added/updated unit coverage for invalid scope rejection, default `core` behavior, and explicit `100` resolution; added integration coverage for scope-100 idempotency and core evidence assertions.
Notes: Integration DB drift was repaired via `uv run alembic stamp base && uv run alembic upgrade head`; scoped integration suite now passes.

## 3. Data-sync and operator command propagation

- [x] 3.1 Propagate refresh scope through `app/data_sync/service.py` for both `run_market_refresh_yfinance` and `run_data_sync_local`.
Notes: Added optional `refresh_scope_mode` propagation and normalization (`core` default) across data-sync market refresh and combined local sync seams; logs now include selected scope mode.
- [x] 3.2 Add CLI support for refresh scope in `scripts/data_sync_operations.py` and preserve backward-compatible defaults.
Notes: Added `--refresh-scope` (choices: `core`, `100`, `200`) for `market-refresh-yfinance` and `data-sync-local`; omission keeps existing default path (`core` via service normalization).
- [x] 3.3 Extend `justfile` recipes (`market-refresh-yfinance`, `data-sync-local`) with optional scope arguments.
Notes: Added optional `refresh_scope` parameter to both recipes and switched to argument-array assembly to preserve all previous combinations while supporting scope propagation.
- [x] 3.4 Add/update CLI and data-sync tests to verify scope propagation, defaulting, and fail-fast behavior.
Notes: Updated CLI tests for default scope pass-through, explicit scope propagation (`100`/`200`), and parser rejection for unsupported scope values.
Notes: Validation evidence: `PYTHONPATH=. uv run pytest -q app/data_sync/tests/test_data_sync_operations_cli.py` -> `7 passed`; `uv run ruff check app/data_sync/service.py scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py` -> clean; `uv run mypy app/` -> clean; `uv run pyright app/data_sync/service.py scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py` -> clean.

## 4. Documentation and validation closeout

- [x] 4.1 Update operational/docs contracts (`docs/guides/yfinance-integration-guide.md`, `docs/guides/local-workflow-justfile.md`, `docs/guides/validation-baseline.md`) with staged onboarding guidance (`core -> 100 -> 200`).
Notes: Updated runbook guidance and evidence contracts to include staged scope selector usage and scope-aware success evidence fields (`refresh_scope_mode`, `requested_symbols_count`).
- [x] 4.2 Update planning/docs state (`docs/product/roadmap.md`, `docs/product/backlog-sprints.md`, `docs/product/decisions.md`) and record delivery evidence in `CHANGELOG.md`.
Notes: Updated Sprint 5.2 roadmap/backlog/decision posture for explicit staged scope contract and recorded implementation + validation + smoke outcomes in `CHANGELOG.md`.
- [x] 4.3 Run touched-scope validation gates (lint, typing, tests) and capture one manual smoke evidence sequence for `core`, then `100`, then `200` (or explicit blocker evidence per stage).
Notes: Validation gates run green for touched scope (`ruff`, `mypy app/`, `pyright`, unit/integration/CLI tests including `pytest -v -m integration`).
Notes: Staged manual smoke evidence captured (2026-03-26 UTC snapshots): `core` failed at `stage=market_refresh` with `status_code=502` (`empty history` for `QQQM`); `100` failed with `status_code=502` (`missing currency metadata` for `AMD`); `200` failed with `status_code=502` (`missing currency metadata` for `XLF`).
