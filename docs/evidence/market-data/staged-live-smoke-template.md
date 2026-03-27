# Market Data Staged Live Smoke Evidence Template

## Purpose

Capture one reproducible evidence record for the staged market-refresh smoke sequence (`core -> 100`) plus one follow-on `data-sync-local` run.

Blocked outcomes are valid evidence. Do not rewrite blocked outcomes as success.

## Environment Snapshot

- Date:
- Operator:
- Branch:
- Commit:
- Host:
- Python version:
- Database backend:
- Notes:

## Preconditions

- `DATABASE_URL` and `TEST_DATABASE_URL` are both configured and distinct.
- Runtime database is migrated (`uv run alembic upgrade head` or equivalent).
- Operator command surfaces are available:
- `just market-refresh-yfinance`
- `just data-sync-local`
- `uv run python -m scripts.data_sync_operations market-refresh-yfinance`
- `uv run python -m scripts.data_sync_operations data-sync-local`

## Command Log

### 1) Refresh `core`

- Command:
- Started at (UTC):
- Finished at (UTC):
- Exit status:
- Output payload:

### 2) Refresh `100`

- Command:
- Started at (UTC):
- Finished at (UTC):
- Exit status:
- Output payload:

### 3) Combined `data-sync-local`

- Command:
- Started at (UTC):
- Finished at (UTC):
- Exit status:
- Output payload:

## Evidence Extraction

For each successful refresh/sync payload, capture:

- `status`
- `refresh_scope_mode`
- `source_provider`
- `requested_symbols`
- `requested_symbols_count`
- `snapshot_key`
- `snapshot_captured_at`
- `snapshot_id`
- `inserted_prices`
- `updated_prices`
- `retry_attempted_symbols`
- `failed_symbols`
- `history_fallback_symbols`
- `history_fallback_periods_by_symbol`
- `currency_assumed_symbols`

For each blocked payload, capture:

- `status`
- `stage`
- `status_code`
- `error`
- attempted command and attempted scope

For deferred staged scopes, capture:

- deferred scope name
- deferral reason
- follow-up owner or target proposal (if available)

## Readiness Decision

- Current staged refresh posture:
- Evidence summary:
- Blocking issues:
- Deferred scopes:
- Follow-up action:
