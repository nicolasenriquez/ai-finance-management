## 1. Investigation and contract freeze

- [x] 1.1 Confirm the current Phase 6 scope against roadmap, backlog, decisions, provider standard, and yfinance guide
Notes: Keep this change focused on `yfinance` operationalization, not broker-authenticated expansion or valuation/API scope growth.
Notes: Confirmed against `docs/product/roadmap.md` (Phase 6), `docs/product/backlog-sprints.md` (Sprint 5.2), `docs/product/decisions.md` (ADR-010/ADR-017), `docs/standards/market-data-provider-standard.md`, and `docs/guides/yfinance-integration-guide.md`.
Notes: Scope for this change is intentionally narrower than broker-auth expansion: operationalize the existing `yfinance` path first while preserving non-goals (no ledger mutation, no valuation/public API expansion).
- [x] 1.2 Freeze the full-refresh contract: supported-symbol source, operator invocation shape, and refresh outcome evidence
Notes: Decide the single supported-symbol source and the minimal operator-facing success/failure payload before implementation begins.
Notes: Contract frozen for implementation: one explicit supported-universe source, one manual operator-triggered full refresh wrapper, and explicit structured outcome evidence (requested scope, provider identity, success/failure, snapshot provenance).
Notes: Full-refresh behavior remains all-or-nothing to avoid partial snapshot persistence when one symbol fails normalization/fetch safety checks.
- [x] 1.3 Diagnose the current `app/market_data` seam and identify the minimal orchestration wrapper for full-universe refresh
Notes: Reuse `ingest_yfinance_daily_close_snapshot()` and existing market-data persistence rules rather than creating a second ingest path.
Notes: Existing seam verified in `app/market_data/service.py`: `_normalize_requested_symbols()` -> `ingest_yfinance_daily_close_snapshot()` -> `ingest_market_data_snapshot()` with duplicate rejection, deterministic snapshot key, and idempotent insert-or-update semantics.
Notes: Minimal wrapper strategy for task `2.x`: add a supported-universe operator flow on top of the existing seam, without bypassing current validation/idempotency/non-mutation guarantees.

## 2. YFinance market-data operations implementation

- [x] 2.1 Centralize the current supported-symbol universe for market-data operations and keep it aligned with the existing `dataset_1`-anchored support contract
Notes: Avoid duplicate symbol lists and avoid implicit scope widening from provider responses or ad hoc runtime discovery.
Notes: Added `list_supported_market_data_symbols()` in `app/market_data/service.py` to expose one stable, sorted supported-universe source backed by the existing dataset_1-anchored symbol contract.
Notes: Existing symbol validation remains anchored to the same internal support set through `_normalize_symbol`, preserving fail-fast unsupported-symbol rejection.
- [x] 2.2 Add one explicit operator-facing full-refresh workflow that requests the supported symbol universe through the existing `yfinance` adapter path
Notes: Keep the first slice manual and schedule-ready; do not introduce queue or scheduler infrastructure unless a minimal local invocation mechanism is clearly required.
Notes: Added `refresh_yfinance_supported_universe()` in `app/market_data/service.py` as the operator-facing full-refresh workflow; it resolves supported symbols, builds a deterministic refresh plan, and executes through existing `ingest_yfinance_daily_close_snapshot()` semantics.
Notes: Implementation remains schedule-ready without adding queue/cron infrastructure and does not bypass current ingestion idempotency/non-mutation contracts.
- [x] 2.3 Add structured refresh outcome reporting and logging so each run is auditable by requested scope, provider, and snapshot provenance
Notes: Preserve fail-fast behavior and all-or-nothing semantics for incomplete or unsafe refreshes.
Notes: Added typed refresh outcome schema `MarketDataRefreshRunResult` in `app/market_data/schemas.py` with explicit provider/source identity, requested scope, snapshot provenance, and insert/update counters.
Notes: Added structured lifecycle logs `market_data.refresh_started`, `market_data.refresh_failed`, and `market_data.refresh_completed` with deterministic scope and snapshot context.
Notes: Task-local proof: `uv run ruff check app/market_data/service.py app/market_data/schemas.py`, `uv run mypy app/market_data`, `uv run pyright app/market_data`, and `uv run pytest -v app/market_data/tests/test_service_unit.py` all pass.

## 3. Verification and safety

- [x] 3.1 Add unit tests for supported-universe resolution, operator workflow behavior, and explicit failure handling for incomplete full-refresh results
Notes: Use deterministic fixtures or mocked provider responses only.
Notes: Added unit coverage in `app/market_data/tests/test_service_unit.py`:
Notes: `test_list_supported_market_data_symbols_returns_stable_sorted_universe`, `test_refresh_supported_universe_returns_structured_result`, and `test_refresh_supported_universe_fails_fast_on_incomplete_provider_coverage`.
Notes: Unit tests remain deterministic and use monkeypatching (no live provider/network dependency).
- [x] 3.2 Add integration coverage proving the full-refresh workflow remains idempotent where applicable and does not mutate canonical, ledger, lot, dividend, or corporate-action truth
Notes: Safety proof matters more than broad runtime surface here.
Notes: Added integration test `test_supported_universe_refresh_is_idempotent_and_non_mutating` in `app/market_data/tests/test_service_integration.py` using mocked provider rows for the full supported-universe scope and asserting idempotent refresh + unchanged canonical/ledger truth counts.
- [x] 3.3 Run touched-scope validation and record any environment-specific blockers explicitly
Notes: Include targeted tests plus touched-scope lint/type/spec validation; do not claim scheduler/live-network evidence in CI.
Notes: Touched-scope validation passed: `uv run ruff check app/market_data/service.py app/market_data/schemas.py app/market_data/tests/test_service_unit.py app/market_data/tests/test_service_integration.py`, `uv run black ... --check --diff`, `uv run mypy app/market_data`, `uv run pyright app/market_data`, `uv run pytest -v app/market_data/tests/test_service_unit.py`, `uv run pytest -v app/market_data/tests/test_service_integration.py::test_supported_universe_refresh_is_idempotent_and_non_mutating -m integration`.
Notes: Environment note: integration DB required migration-state recovery before the targeted integration run; executed `uv run alembic stamp base && uv run alembic upgrade head` and reran the integration test successfully.

## 4. Documentation and closeout

- [x] 4.1 Update roadmap, backlog, decisions, validation baseline, and yfinance/provider docs to reflect `yfinance` as the current operational provider path
Notes: Replace any language that implies broker-authenticated expansion is the immediate next step for this phase.
Notes: Updated `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md}`, and `docs/standards/market-data-provider-standard.md` to align phase-6 wording with the implemented service-level supported-universe refresh seam and manual schedule-ready posture.
- [x] 4.2 Update `CHANGELOG.md` with delivered behavior, validation evidence, and explicit non-goals
Notes: Keep later multi-provider, valuation, and frontend work clearly deferred.
Notes: Added `docs(market-data-operations): align phase-6 posture around yfinance operational refresh workflow` in `CHANGELOG.md` with updated docs footprint, closeout validation references, and explicit non-goals.
- [x] 4.3 Run final OpenSpec validation for the completed change and record blockers explicitly if any remain
Notes: `openspec validate add-yfinance-market-data-operations --type change --strict --json` and `openspec validate --specs --all --json` should be part of closeout evidence.
Notes: Final OpenSpec validation passed (`change`: 1/1 passed; `specs`: 13/13 passed). PostHog telemetry DNS failures (`edge.openspec.dev`) occurred after command completion and did not affect validation outcomes.
Notes: Manual live-provider smoke run against `refresh_yfinance_supported_universe` rejected with `MarketDataClientError` (`YFinance returned unsupported trading-date key for symbol 'AMD'`), requiring a dedicated operational hardening follow-up before treating market-data refresh as fully production-ready.
