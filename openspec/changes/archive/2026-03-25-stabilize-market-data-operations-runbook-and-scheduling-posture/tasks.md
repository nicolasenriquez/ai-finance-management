## 1. Investigation and contract freeze

- [x] 1.1 Confirm the remaining Phase 6 scope against roadmap, backlog, decisions, validation baseline, and yfinance guide
Notes: Confirmed against `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/validation-baseline.md`, and `docs/guides/yfinance-integration-guide.md`.
Notes: Remaining Sprint 5.2 scope is explicitly operational: stabilize live-provider smoke/runbook evidence and formalize schedule-ready invocation posture on top of existing local commands.
Notes: Scope freeze for this change remains strict: no public market-data router, no scheduler/queue infrastructure, no ledger/canonical mutation, and no valuation/API/frontend expansion.
- [x] 1.2 Investigate the current live smoke blocker and freeze the approved runbook/evidence contract for `market-refresh-yfinance` and `data-sync-local`
Notes: Prior closeout evidence (archived `add-yfinance-data-sync-operations`) recorded a fail-fast live smoke blocker at `stage=market_refresh` with `status_code=502`, while bootstrap succeeded in the same `data-sync-local` run.
Notes: Contract freeze for blocked runs: preserve structured failure payload (`status`, `stage`, `status_code`, `error`) from `scripts/data_sync_operations.py` and treat that output as first-class blocker evidence, not partial success.
Notes: Contract freeze for successful runs: preserve typed evidence from `MarketDataRefreshRunResult` and `DataSyncLocalRunResult` (`source_provider`, `requested_symbols`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, insert/update counters) so operator runbooks and closeout remain deterministic.
- [x] 1.3 Diagnose the minimal provider/date-key hardening needed to support approved live day-level refresh variants without weakening fail-fast rules
Notes: Current adapter already handles approved series and symbol-keyed tabular `Close` shapes via `_extract_close_items` / `_extract_tabular_close_items`, with fail-fast rejection for unsupported tabular payloads.
Notes: `trading_date` coercion currently accepts `datetime`, `date`, and values exposing `to_pydatetime()`; unsupported keys still raise explicit `YFinanceAdapterError` and stop persistence.
Notes: Minimal hardening target for `2.x`: keep all-or-nothing ingest and fail-fast behavior, focus only on approved day-level temporal variants observed in live smoke runs, and avoid broad payload coercion or silent row skipping.

## 2. Operational stabilization implementation

- [x] 2.1 Implement the minimal `app/market_data` and/or `app/data_sync` changes required to accept the approved live temporal variants for current operational refreshes
Notes: Hardened temporal-key coercion in `app/market_data/providers/yfinance_adapter.py` via `_coerce_day_level_temporal_key`, keeping day-level semantics while accepting bounded live variants (`date`/`datetime`, `to_pydatetime()` yielding `date`/`datetime`, and scalar `item()` conversions).
Notes: Unsupported temporal keys still fail explicitly with `YFinanceAdapterError` before persistence; all-or-nothing ingest behavior is unchanged.
- [x] 2.2 Preserve explicit blocker reporting and structured outcome evidence for successful and blocked operator runs
Notes: Preserved structured blocker contract (`status`, `stage`, `status_code`, `error`) and success contract (`MarketDataRefreshRunResult`/`DataSyncLocalRunResult`) while improving provider blocker detail by surfacing compact exception reason text in adapter 502 errors.
Notes: Existing service/CLI stage boundaries remain unchanged (`market_refresh` in `app/data_sync/service.py`; structured stderr failure payload in `scripts/data_sync_operations.py`).
- [x] 2.3 Keep the existing command surfaces schedule-ready and document any invocation prerequisites without adding scheduler infrastructure
Notes: Command surfaces remain unchanged (`data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local` via `scripts.data_sync_operations.py` and corresponding `just` recipes), preserving scheduler-ready invocation seams.
Notes: Added explicit CLI prerequisite guidance (DB URL + migrations + preferred `just` invocation surfaces) in parser epilog without introducing queue/cron/worker infrastructure.

## 3. Verification and safety

- [x] 3.1 Add deterministic unit tests for the approved live temporal variants and explicit blocker evidence behavior
Notes: Added deterministic adapter unit coverage in `app/market_data/tests/test_yfinance_adapter_unit.py` for approved temporal-key variants (`test_fetch_symbol_rows_supports_temporal_scalar_item_keys`, `test_fetch_symbol_rows_supports_to_pydatetime_returning_date`) and explicit blocker reason propagation (`test_fetch_surfaces_unexpected_provider_reason_for_blocker_evidence`).
Notes: Red-first proof executed before adapter patch: new temporal-variant tests failed with `unsupported trading-date key`, then passed after implementation.
- [x] 3.2 Add or update integration coverage proving the stabilized refresh path still preserves idempotency and canonical/ledger non-mutation guarantees
Notes: Added adapter-path integration regression `test_supported_universe_refresh_adapter_item_keys_are_idempotent_and_non_mutating` in `app/market_data/tests/test_service_integration.py`, exercising `refresh_yfinance_supported_universe` through the real adapter path with `item()` temporal keys.
Notes: Integration evidence confirms both stabilized and baseline supported-universe refresh paths remain idempotent and canonical/ledger non-mutating.
- [x] 3.3 Run touched-scope validation and one explicit manual smoke workflow, recording success evidence or blocker evidence honestly
Notes: Touched-scope validation passed: `ruff`, `black --check --diff`, `mypy`, `pyright`, `ty`, targeted unit/CLI suites (`28 passed`), and targeted integration suites (`2 passed`) after applying migration prerequisite (`uv run alembic stamp base && uv run alembic upgrade head`).
Notes: Manual smoke outcomes were captured honestly in sequence: initial run blocked at `stage=market_refresh` (`status_code=502`, `KeyError: 'currency'`), then post-fix rerun succeeded with `{"status":"completed","market_refresh":{"status":"completed","requested_symbols_count":19,"inserted_prices":23505}}`.

## 4. Documentation and closeout

- [x] 4.1 Update roadmap, backlog, decisions, validation baseline, runbook/operator docs, and provider standard for the stabilized operational posture
Notes: Updated product docs `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}` to mark runbook/schedule-ready stabilization delivered, freeze bounded temporal-key acceptance, and keep remaining scope focused on unresolved live-provider blockers plus deferred expansion non-goals.
Notes: Updated operator/runbook and provider references `docs/guides/{validation-baseline.md,yfinance-integration-guide.md,local-workflow-justfile.md}` and `docs/standards/market-data-provider-standard.md` with explicit success/blocker evidence contract (`status`, `stage`, `status_code`, `error`) and approved temporal-key variant set.
- [x] 4.2 Update `CHANGELOG.md` with delivered behavior, evidence, and explicit remaining non-goals
Notes: Added `2026-03-25` entry `fix(market-data-operations): stabilize yfinance temporal-key handling and formalize operator blocker evidence` with touched files, validation commands, manual smoke blocker evidence, and explicit non-goal posture.
- [x] 4.3 Run final OpenSpec validation for the change and record any environment-dependent blockers explicitly
Notes: Final OpenSpec validations passed: `openspec validate stabilize-market-data-operations-runbook-and-scheduling-posture --type change --strict --json` (1/1 pass) and `openspec validate --specs --all --json` (15/15 pass).
Notes: Environment-dependent provider blocker observed earlier (`stage=market_refresh`, `status_code=502`, `KeyError: 'currency'`) was resolved by canonical/provider symbol handling (`BRK.B` -> `BRK-B`) plus safe currency fallback; latest manual smoke completed successfully.
Notes: OpenSpec CLI emitted PostHog DNS flush warnings (`edge.openspec.dev`) after validation completion; command exit and validation outcomes were unaffected.
