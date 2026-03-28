## 1. Investigation and contract freeze

- [x] 1.1 Confirm the exact `dataset_1` bootstrap seam to orchestrate (ingest -> persist -> rebuild) and document required inputs/outputs
Notes: Reuse existing service and route contracts; avoid introducing parallel persistence paths.
Notes: Confirmed canonical bootstrap seam for this change is:
Notes: `POST /api/pdf/ingest` (`app/pdf_ingestion/routes.py`) -> `POST /api/pdf/persist` (`app/pdf_persistence/routes.py`) -> `rebuild_portfolio_ledger_from_canonical_records` (`app/portfolio_ledger/service.py`).
Notes: `persist_pdf_from_storage` already chains normalization and extraction internally (`normalize_pdf_from_storage` -> `extract_pdf_from_storage`), so bootstrap should not invoke separate extract/normalize routes in parallel.
Notes: Required handoff is `PdfPersistenceResult.source_document_id` into ledger rebuild; persistence and rebuild return deterministic counters needed for command evidence (`import_job_id`, inserted/duplicate summary, processed/derived ledger and lot counts).
- [x] 1.2 Reproduce the live `yfinance` trading-date-key failure and freeze expected adapter behavior for supported runtime close payload shapes
Notes: Capture the failing payload-shape pattern in tests before implementation.
Notes: Reproduced locally with a deterministic pandas close-table fixture via adapter internals: `_extract_series_items` yields `('AMD', Series)` and `_coerce_trading_date` raises `YFinance returned unsupported trading-date key for symbol 'AMD'.` (`status_code=502`), matching live blocker behavior.
Notes: Root-cause freeze: current `_extract_series_items` treats tabular `Close` payloads as `(column_name, series)` tuples; symbol labels are incorrectly fed into trading-date coercion.
Notes: Expected behavior freeze for implementation phase: support series-like and tabular close payloads by deriving `trading_date` only from temporal index values, preserve requested symbol attribution, and fail fast on unsupported shapes without partial ingest.
- [x] 1.3 Freeze operator command contracts (`data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local`) including fail-fast semantics and evidence format
Notes: Keep command scope local/manual and schedule-ready; no public router required in this slice.
Notes: `data-bootstrap-dataset1`: local fail-fast workflow `ingest -> persist -> rebuild`; output evidence must include `storage_key`, `source_document_id`, `import_job_id`, persistence summary counts, and rebuild summary counts.
Notes: `market-refresh-yfinance`: local wrapper over `refresh_yfinance_supported_universe`; output evidence must include provider/source identity, requested scope count, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, and insert/update counters.
Notes: `data-sync-local`: deterministic sequence `data-bootstrap-dataset1` then `market-refresh-yfinance`; refresh must not run when bootstrap fails; command exits non-zero on first failing stage with explicit stage-specific error context.
Notes: Scope freeze for this change: command-level operational entrypoints only (no new public market-data route, no scheduler/queue infrastructure).

## 2. YFinance adapter hardening

- [x] 2.1 Add failing unit coverage for tabular close-payload normalization where symbol labels can be misread as time keys
Notes: Added adapter unit regressions in `app/market_data/tests/test_yfinance_adapter_unit.py`:
Notes: `test_fetch_symbol_rows_supports_tabular_close_payload_for_requested_symbol` and `test_fetch_symbol_rows_rejects_tabular_close_payload_with_ambiguous_symbol_columns`.
Notes: Confirmed red-first behavior before adapter patch (`raw_market_key='AMD'` -> unsupported trading-date key), then reran green after implementation.
- [x] 2.2 Implement minimal adapter changes so trading-date keys are derived safely across approved close payload shapes
Notes: Updated `app/market_data/providers/yfinance_adapter.py` to route close payload handling through `_extract_close_items` with explicit tabular-shape resolution.
Notes: Added safe tabular extraction helpers (`_extract_tabular_close_items`, `_is_tabular_close_payload`, `_close_column_matches_symbol`) to map requested symbol columns before trading-date coercion.
Notes: Behavior remains fail-fast for ambiguous or unsupported tabular shapes (`unsupported tabular Close payload`) and does not introduce partial-row coercion.
- [x] 2.3 Add/adjust service-level regression coverage so supported-universe refresh fails explicitly on unsupported shapes and succeeds on valid tabular payloads
Notes: Added service-level unit regressions in `app/market_data/tests/test_service_unit.py`:
Notes: `test_refresh_supported_universe_surfaces_adapter_shape_error` and `test_refresh_supported_universe_succeeds_through_provider_ingest_path`.
Notes: Refresh now has explicit regression coverage for adapter shape failures and full-scope provider-ingest success path through `refresh_yfinance_supported_universe`.
Notes: Task-local proof: `uv run pytest -v app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py` and targeted lint/type checks on touched files (`ruff`, `mypy`, `pyright`) pass.

## 3. Local operator data-sync entrypoints

- [x] 3.1 Implement `dataset_1` bootstrap command entrypoint that orchestrates ingest -> persist -> rebuild through existing seams
Notes: Added orchestration service `run_dataset1_bootstrap` in `app/data_sync/service.py` with explicit stage boundaries (`input`, `ingest`, `persist`, `rebuild`) and typed run evidence via `DatasetBootstrapRunResult`.
Notes: Added CLI entrypoint command `data-bootstrap-dataset1` in `scripts/data_sync_operations.py` with deterministic JSON output and structured failure payloads.
- [x] 3.2 Implement `yfinance` market-refresh command entrypoint using `refresh_yfinance_supported_universe`
Notes: Added orchestration service `run_market_refresh_yfinance` in `app/data_sync/service.py` wrapping `refresh_yfinance_supported_universe` with fail-fast `DataSyncClientError(stage="market_refresh")`.
Notes: Added CLI entrypoint command `market-refresh-yfinance` in `scripts/data_sync_operations.py`.
- [x] 3.3 Implement combined local sync entrypoint that executes bootstrap then refresh with strict fail-fast behavior
Notes: Added `run_data_sync_local` in `app/data_sync/service.py` enforcing strict sequence `bootstrap -> refresh` with immediate stop on first failing stage.
Notes: Added CLI entrypoint command `data-sync-local` in `scripts/data_sync_operations.py` returning combined typed evidence (`DataSyncLocalRunResult`) on success.
- [x] 3.4 Add `just` recipes for `data-bootstrap-dataset1`, `market-refresh-yfinance`, and `data-sync-local`
Notes: Added `justfile` recipes `data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local` with `db-check` + `db-upgrade` prerequisites and optional argument overrides.
Notes: Fixed recipe execution boundary to module mode (`uv run python -m scripts.data_sync_operations ...`) so project imports resolve correctly from repo root.

## 4. Verification and safety

- [x] 4.1 Add deterministic tests for new command entrypoints (unit first; integration where contract risk is meaningful)
Notes: Added `app/data_sync/tests/test_data_sync_operations_cli.py` with deterministic unit coverage for parser behavior, bootstrap success output, refresh fail-fast output, and combined sync argument wiring.
- [x] 4.2 Run touched-scope validation (`ruff`, `black --check`, `mypy`, `pyright`, `ty`, targeted `pytest`) and record blockers explicitly
Notes: Validation evidence:
Notes: `uv run ruff check app/data_sync scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py` (pass)
Notes: `uv run black app/data_sync scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py --check --diff` (pass)
Notes: `uv run mypy app/data_sync app/market_data/providers/yfinance_adapter.py app/market_data/service.py` (pass)
Notes: `uv run pyright app/data_sync app/market_data/providers/yfinance_adapter.py app/market_data/service.py` (0 errors)
Notes: `uv run ty check app` (pass)
Notes: `uv run pytest -v app/data_sync/tests/test_data_sync_operations_cli.py app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py` (24 passed)
- [x] 4.3 Run one local smoke execution of the new operator workflows and record environment-specific blockers without masking failures
Notes: Executed smoke run:
Notes: `uv run python -m scripts.data_sync_operations data-sync-local --snapshot-captured-at 2026-03-25T00:00:00Z`
Notes: Bootstrap stage completed successfully (`ingest -> persist -> rebuild`) with deterministic counters; refresh stage failed fast with structured error payload:
Notes: `{"status":"failed","stage":"market_refresh","status_code":502,"error":"YFinance market refresh failed: YFinance provider fetch failed with an unexpected error."}`
Notes: This is recorded as environment/provider blocker evidence, not masked as partial success.

## 5. Documentation and closeout

- [x] 5.1 Update roadmap/backlog/guides to reflect the new local data-sync operational workflow and yfinance hardening status
Notes: Updated docs to reflect delivered command-level operations + hardening status:
Notes: `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`
Notes: `docs/guides/{local-workflow-justfile.md,validation-baseline.md,yfinance-integration-guide.md,portfolio-ledger-and-analytics-guide.md}`
Notes: `docs/standards/yfance-standard.md`
- [x] 5.2 Update `CHANGELOG.md` with delivered behavior, validation evidence, and deferred non-goals
Notes: Added `2026-03-25` changelog entry `feat(data-sync-operations): add local dataset bootstrap and yfinance refresh command workflows` with validation evidence and explicit deferred non-goals.
- [x] 5.3 Run final OpenSpec validation for the change and record outcome evidence in task notes
Notes: `openspec validate add-yfinance-data-sync-operations --type change --strict --json` -> `valid: true`, `failed: 0` for this change.
Notes: CLI exited successfully; PostHog telemetry flush produced network warnings (`edge.openspec.dev` DNS) without affecting validation result.
