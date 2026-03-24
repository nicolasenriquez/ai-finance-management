## 1. Investigation and baseline alignment

- [x] 1.1 Confirm market-data scope against roadmap, PRD, decisions, ledger guide, and PostgreSQL standards
Notes: Validate that the proposed slice stays storage-focused, preserves ledger-first portfolio truth, does not expand current KPI or frontend valuation scope, and is anchored to the current `dataset_1` instrument universe.
Notes: Scope confirmed against `docs/product/roadmap.md`, `docs/product/prd.md`, `docs/product/decisions.md` (ADR-010), `docs/guides/portfolio-ledger-and-analytics-guide.md`, and `docs/standards/postgres-standard.md`; all sources align on market-data separation from ledger truth and explicit snapshot/provenance requirements.
- [x] 1.2 Diagnose current storage and query boundaries and define the minimal schema shape required for quotes and price history
Notes: Keep the first iteration intentionally small: provider/source identity, canonical instrument identifier, market timestamp or trading-date context, numeric price payload, and ingestion provenance.
Notes: Current persisted truth boundary remains `source_document` -> `import_job` -> `canonical_pdf_record` -> `portfolio_transaction` / `dividend_event` / `corporate_action_event` -> `lot` / `lot_disposition`, and current analytics reads stay ledger-only (`app/portfolio_analytics/service.py`) with no `price_history` dependency.
- [x] 1.2.1 Confirm current symbol inventory and normalization edge cases from persisted `dataset_1` ledger truth
Notes: Treat the existing MVP symbol set as the first supported universe and make edge cases such as `BRK.B` explicit before uniqueness or schema rules are finalized.
Notes: Confirmed `dataset_1` symbol universe from `app/golden_sets/dataset_1/202602_stocks.json`: `AMD`, `APLD`, `BBAI`, `BRK.B`, `GLD`, `GOOGL`, `HOOD`, `META`, `NVDA`, `PLTR`, `QQQM`, `SCHD`, `SCHG`, `SMH`, `SOFI`, `SPMO`, `TSLA`, `UUUU`, `VOO`.
Notes: Existing symbol normalization contract is `trim + uppercase` (lot-detail path), which preserves punctuation and keeps dotted ticker shapes viable for canonical matching.
- [x] 1.3 Repair OpenSpec spec-format baseline for `pdf-ingestion` and `pdf-preflight-analysis` without changing their intended behavior
Notes: Restore `## Purpose` and `## Requirements` structure so `openspec validate --specs --all` can become a reliable repo-level gate again.
Notes: Updated `openspec/specs/pdf-ingestion/spec.md` and `openspec/specs/pdf-preflight-analysis/spec.md` to valid main-spec structure (`# ... Specification`, `## Purpose`, `## Requirements`) without changing requirement/scenario semantics.
Notes: Task-local proof: `openspec validate --specs --all --json` now passes (`11/11` items valid, including `pdf-ingestion` and `pdf-preflight-analysis`).

## 2. Market-data persistence boundary

- [x] 2.1 Create the `app/market_data/` feature slice with typed models, schemas, service boundary, and migration scaffolding
Notes: Follow the repository vertical-slice pattern and keep shared abstractions out unless they are already justified by reuse.
Notes: Added `app/market_data/` scaffold with typed package files: `models.py` (`MarketDataSnapshot`, `PriceHistory`), `schemas.py` (write/read contracts), and `service.py` (explicit write/read boundary stubs for tasks `2.2` and `2.3`).
Notes: Added migration scaffold `alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py` creating `market_data_snapshot` and `price_history` tables with FK/index/check-constraint baseline, and wired Alembic model discovery via `alembic/env.py`.
Notes: Task-local proof passed: `uv run ruff check app/market_data alembic/env.py alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py`, `uv run black --check ...`, `uv run mypy app/market_data`, and `openspec validate add-market-data-ingestion-boundary --type change --strict --json`.
- [x] 2.2 Implement idempotent market-data write semantics with explicit provider/source provenance and deterministic uniqueness rules
Notes: Fail fast on missing provenance, incomplete time keys, or unsafe symbol remapping; do not add silent defaults that could blur source-of-truth boundaries.
Notes: Implemented `ingest_market_data_snapshot` in `app/market_data/service.py` with explicit normalization/validation: source identity normalization, timezone-aware timestamp enforcement, canonical symbol validation (dataset_1 universe including dotted tickers), and duplicate symbol/time-key rejection inside one request payload.
Notes: Idempotency semantics now use deterministic snapshot + symbol/time key matching with insert-or-update behavior, explicit `inserted_prices`/`updated_prices` result counts, and `updated_at` refresh on updates.
Notes: Strengthened DB-backed uniqueness contract in `app/market_data/models.py` and `alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py` with exact-one-time-key constraint and partial unique indexes for `(snapshot_id, instrument_symbol, market_timestamp)` / `(snapshot_id, instrument_symbol, trading_date)`.
- [x] 2.3 Expose a minimal internal read boundary for persisted market-data snapshots without expanding current portfolio analytics contracts
Notes: This slice should make later valuation work possible, not sneak it in early.
Notes: Implemented internal read boundary `list_price_history_for_symbol` in `app/market_data/service.py` that loads persisted `price_history` rows joined to `market_data_snapshot` provenance and returns typed `MarketDataPriceRow` payloads ordered by most recent market context.
Notes: Read boundary remains internal-only (no new API routes); current `/api/portfolio/*` contract is unchanged and ledger-only.
Notes: Task-local proof passed after implementation: `uv run ruff check app/market_data alembic/env.py alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py`, `uv run black --check ...`, `uv run mypy app/market_data`, and `openspec validate add-market-data-ingestion-boundary --type change --strict --json`.

## 3. Verification and safety

- [x] 3.1 Add unit tests for provenance validation, fail-fast rejection, and deterministic idempotency behavior
Notes: Start with failing tests and lock down duplicate-ingestion, missing-metadata, and canonical symbol-shape cases before implementation broadens.
Notes: Added unit suite `app/market_data/tests/test_service_unit.py` covering fail-fast validation before DB access for timezone-aware snapshot provenance, unsupported-symbol rejection, duplicate symbol/time-key payload rejection, and unsafe-symbol-shape rejection in read boundary.
Notes: Unit proof: `uv run pytest -v app/market_data/tests/test_service_unit.py` -> `4 passed`.
- [x] 3.2 Add integration coverage proving market-data refresh does not mutate canonical, ledger, lot, dividend, or corporate-action truth
Notes: Safety proof matters more than API surface here; the main regression risk is cross-boundary mutation or lossy symbol storage that breaks later joins to ledger truth.
Notes: Added integration suite `app/market_data/tests/test_service_integration.py` with deterministic idempotency verification (`inserted_prices` then `updated_prices` with one persisted row) and explicit non-mutation checks for successful and rejected refresh paths against `canonical_pdf_record`, `portfolio_transaction`, `dividend_event`, `corporate_action_event`, `lot`, and `lot_disposition`.
Notes: Integration proof: `uv run pytest -v app/market_data/tests/test_service_integration.py -m integration` -> `4 passed`.
- [x] 3.3 Validate migration behavior and confirm native PostgreSQL remains sufficient for the first market-data slice
Notes: Document why TimescaleDB or background scheduling remains deferred rather than implied.
Notes: Migration behavior validated by applying current head (`uv run alembic upgrade head`) and asserting presence of market-data tables/indexes/constraints (`market_data_snapshot`, `price_history`, partial unique indexes, and constraint names) in integration test `test_market_data_migration_schema_contract_is_present`.
Notes: Current slice remains native-PostgreSQL sufficient: no TimescaleDB-specific objects or extension requirements were needed to ingest/read idempotent market-data snapshots in the validated integration flow.

## 4. Documentation and closeout

- [x] 4.1 Update roadmap, backlog, validation baseline, and ledger/analytics guidance for the new market-data boundary
Notes: Close the loop between product planning, engineering constraints, and execution workflow so future changes inherit the correct boundary.
Notes: Updated `docs/product/roadmap.md`, `docs/product/backlog-sprints.md`, `docs/guides/validation-baseline.md`, and `docs/guides/portfolio-ledger-and-analytics-guide.md` to reflect the implemented market-data boundary, explicit non-mutation guarantees, and remaining deferred valuation scope.
Notes: Task-local doc-proof: `openspec validate add-market-data-ingestion-boundary --type change --strict --json` passes after documentation updates.
- [x] 4.2 Update changelog with delivered behavior, validation evidence, and explicit non-goals
Notes: Keep the delivery record grep-friendly and explicit about what still remains out of scope.
Notes: Added 2026-03-24 changelog entry `feat(market-data): add isolated ingestion boundary with idempotent snapshot persistence` in `CHANGELOG.md` covering delivered behavior, validation evidence, and explicit non-goals.
- [x] 4.3 Run final validation (`openspec validate --specs --all`, targeted tests, and touched-scope quality gates) and record blockers explicitly if any remain
Notes: If a repo-wide gate still fails, the blocker must be named directly rather than hidden behind partial success language.
Notes: Final validation passed for touched scope: `openspec validate --specs --all --json` (`11/11` valid), `uv run ruff check app/market_data alembic/env.py alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py`, `uv run black app/market_data alembic/env.py alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py --check --diff`, `uv run bandit -c pyproject.toml -r app/market_data --severity-level high --confidence-level high`, `uv run mypy app/market_data`, `uv run pyright app/market_data`, `uv run ty check app/market_data`, `uv run pytest -v app/market_data/tests/test_service_unit.py`, `uv run alembic upgrade head`, and `uv run pytest -v app/market_data/tests/test_service_integration.py -m integration`.
Notes: No blocking validation failures remain for this change; non-fatal OpenSpec telemetry DNS errors (`edge.openspec.dev`) appeared after successful validation output in this network-restricted environment.
