# Market Data Staged Live Smoke Evidence - 2026-03-26

## Purpose

Capture one reproducible evidence record for the staged market-refresh smoke sequence (`core -> 100`) plus one follow-on `data-sync-local` run.

Blocked outcomes are valid evidence.

## Environment Snapshot

- Date: 2026-03-26
- Operator: Codex
- Branch: `feat/market-refresh-live-smoke-evidence-20260326`
- Commit: working tree (uncommitted)
- Host: local development machine
- Python version: project `.venv` Python (via `uv run`)
- Database backend: PostgreSQL (local runtime DB)
- Notes: proposal scope intentionally validates `core` and `100` only; `200` is deferred from this change.

## Preconditions

- `DATABASE_URL` and `TEST_DATABASE_URL` configured and distinct.
- Runtime DB migrated (`uv run alembic upgrade head` executed before smoke run).
- Operator command surfaces available (`uv run python -m scripts.data_sync_operations ...`).

## Command Log

### 1) Refresh `core`

- Command: `uv run python -m scripts.data_sync_operations market-refresh-yfinance --refresh-scope core`
- Started at (UTC): `2026-03-26T21:10:44Z`
- Finished at (UTC): `2026-03-26T21:13:02Z`
- Exit status: `1`
- Output payload:

```json
{"error": "YFinance market refresh failed: YFinance currency metadata access failed for symbol 'TSLA'.", "stage": "market_refresh", "status": "failed", "status_code": 502}
```

### 2) Refresh `100`

- Command: `uv run python -m scripts.data_sync_operations market-refresh-yfinance --refresh-scope 100`
- Operator guard: 360s timeout to avoid indefinite runtime.
- Started at (UTC): `2026-03-26T21:30:16Z`
- Finished at (UTC): `2026-03-26T21:36:18Z`
- Exit status: `143` (terminated by timeout guard)
- Output payload:

```json
{"status":"failed","stage":"market_refresh","status_code":408,"error":"Scope 100 refresh exceeded operator timeout (360s) before completion."}
```

- Additional observed provider warning before timeout:

```text
1 Failed download:
['GLDD']: TypeError("'NoneType' object is not subscriptable")
```

### 3) Combined `data-sync-local`

- Command: `uv run python -m scripts.data_sync_operations data-sync-local --refresh-scope core`
- Started at (UTC): `2026-03-27T00:08:51Z`
- Finished at (UTC): `2026-03-27T00:12:34Z`
- Exit status: `0`
- Output payload:

```json
{
  "bootstrap": {
    "dataset_pdf_path": "app/golden_sets/dataset_1/202602_stocks.pdf",
    "duplicate_records": 171,
    "import_job_id": 4,
    "inserted_records": 0,
    "normalized_records": 171,
    "rebuild": {
      "corporate_action_events": 1,
      "dividend_events": 34,
      "lot_dispositions": 17,
      "open_lots": 112,
      "portfolio_transactions": 136,
      "processed_records": 171,
      "source_document_id": 1
    },
    "source_document_id": 1,
    "status": "completed",
    "storage_key": "<redacted-storage-key>.pdf"
  },
  "market_refresh": {
    "currency_assumed_symbols": [],
    "failed_symbols": [],
    "failed_symbols_count": 0,
    "history_fallback_periods_by_symbol": {},
    "history_fallback_symbols": [],
    "inserted_prices": 0,
    "refresh_scope_mode": "core",
    "requested_symbols": [
      "AMD",
      "APLD",
      "BBAI",
      "BRK.B",
      "GLD",
      "GOOGL",
      "HOOD",
      "META",
      "NVDA",
      "PLTR",
      "QQQM",
      "SCHD",
      "SCHG",
      "SMH",
      "SOFI",
      "SPMO",
      "TSLA",
      "UUUU",
      "VOO"
    ],
    "requested_symbols_count": 19,
    "retry_attempted_symbols": [],
    "retry_attempted_symbols_count": 0,
    "snapshot_captured_at": "2026-03-27T00:09:03.900996Z",
    "snapshot_id": 6,
    "snapshot_key": "yf|d1|1d|5y|aa0rp0|2026-03-27|s19|a874c6a169e8",
    "source_provider": "yfinance",
    "source_type": "market_data_provider",
    "status": "completed",
    "updated_prices": 23491
  },
  "status": "completed"
}
```

- Superseded run note: the earlier combined run at `2026-03-26T21:25:19Z` was retained only as exploratory history and is not used for ordered staged evidence because it occurred before standalone `100`.

## Evidence Extraction

Refresh `core` blocker:
- `status`: `failed`
- `stage`: `market_refresh`
- `status_code`: `502`
- `error`: `YFinance market refresh failed: YFinance currency metadata access failed for symbol 'TSLA'.`

Refresh `100` blocker:
- `status`: `failed`
- `stage`: `market_refresh`
- `status_code`: `408`
- `error`: `Scope 100 refresh exceeded operator timeout (360s) before completion.`

Combined `data-sync-local` success:
- top-level `status`: `completed`
- nested `market_refresh.status`: `completed`
- nested `market_refresh.refresh_scope_mode`: `core`
- nested `market_refresh.source_provider`: `yfinance`
- nested `market_refresh.requested_symbols_count`: `19`
- nested `market_refresh.snapshot_key`: `yf|d1|1d|5y|aa0rp0|2026-03-27|s19|a874c6a169e8`
- nested `market_refresh.snapshot_id`: `6`
- nested `market_refresh.inserted_prices`: `0`
- nested `market_refresh.updated_prices`: `23491`
- nested `market_refresh.retry_attempted_symbols_count`: `0`
- nested `market_refresh.failed_symbols_count`: `0`

Deferred staged scopes:
- scope: `200`
- reason: explicitly deferred from this proposal scope (`core -> 100` evidence-only closeout)

## Readiness Decision

- Current staged refresh posture: `core` and `100` both produced blocker evidence in this run set.
- Evidence summary:
- `core` failed with provider currency metadata access failure for required symbol `TSLA`.
- `100` did not complete within a bounded 360s operator window and was terminated with explicit timeout blocker evidence.
- `data-sync-local` with `core` scope completed successfully and produced typed refresh evidence.
- Blocking issues:
- provider reliability for required symbol metadata (`core`)
- operational runtime pressure for `100` under current refresh behavior
- Deferred scopes:
- `200` remains deferred by proposal scope.
- Follow-up action:
- keep Phase 6 readiness posture conservative in docs (`core/100` not yet fully green in live smoke)
- carry forward deferred/optimization work in a separate follow-up change.
