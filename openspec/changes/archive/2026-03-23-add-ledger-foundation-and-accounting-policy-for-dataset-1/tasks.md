## 0. Investigation

- [x] 0.1 Confirm the exact Phase 3 boundary from the roadmap, ADRs, ledger guide, and current persistence design before coding
Notes: Keep this change inside ledger foundation plus accounting-policy freeze. Do not expand into analytics endpoints, market data, or frontend work.
Notes: Confirmed from `docs/product/roadmap.md` (Phase 3 vs Phase 4 boundary), `docs/product/decisions.md` ADR-009/010/011/012, and `docs/guides/portfolio-ledger-and-analytics-guide.md` ledger/market-data/analytics separation.
Notes: Current application routing in `app/main.py` includes PDF pipeline slices only; no portfolio analytics endpoints exist yet, so this slice remains internal domain foundation work.
- [x] 0.2 Confirm which dataset 1 event types and fields are actually available from `canonical_pdf_record` before freezing accounting rules
Notes: Ground the policy in existing `trade`, `dividend`, and `split` records only, and document unsupported fee or FX handling explicitly.
Notes: `CanonicalEventType` in `app/pdf_normalization/schemas.py` is constrained to `trade`, `dividend`, and `split`; persistence fingerprint contract in `app/pdf_persistence/service.py` matches the same three families.
Notes: `canonical_pdf_record` in `app/pdf_persistence/models.py` persists event surface fields (`event_type`, `event_date`, `instrument_symbol`, `trade_side`) plus `canonical_payload`, `raw_values`, and `provenance`; no explicit fee/FX fields are currently present.
- [x] 0.3 Diagnose blast radius across migrations, persistence coupling, lot derivation, validation assets, and later analytics dependencies
Notes: Explicitly decide whether `canonical_pdf_record` remains immutable upstream audit truth and whether ledger rebuild stays internal to services in this phase.
Notes: Blast radius covers new portfolio-ledger slice files, new SQLAlchemy models, Alembic migration(s), targeted/integration tests, finance golden cases, and docs/changelog updates; existing PDF ETL route contracts stay unchanged.
Notes: Decision recorded for this phase: keep `canonical_pdf_record` immutable as upstream audit truth and implement ledger rebuild internally as canonical-to-ledger derivation services before any analytics API expansion.

## 1. Contract and failing tests

- [x] 1.1 Add failing unit tests for canonical-to-ledger event mapping and lineage preservation
Notes: Cover trades, dividends, and splits deriving from persisted canonical records without reparsing source PDFs.
Notes: Added fail-first tests in `app/portfolio_ledger/tests/test_canonical_mapping.py` for trade/dividend/split canonical-to-ledger mapping plus lineage assertions (`source_document_id`, `import_job_id`, `canonical_record_id`, `canonical_fingerprint`).
Notes: Task-local proof: `uv run pytest -v app/portfolio_ledger/tests/test_canonical_mapping.py` fails as expected because `app.portfolio_ledger.service` and `map_canonical_record_to_ledger_event()` are not implemented yet (tasks 2.1-3.1).
- [x] 1.2 Add failing unit tests for FIFO lot matching, realized-basis accounting, and split-adjusted open lots using deterministic finance cases
Notes: Finance tests should be independent of PDF parsing and easy to audit by reading the fixtures.
Notes: Added deterministic finance fixtures in `app/portfolio_ledger/tests/fixtures/dataset_1_v1_finance_cases.json` and fail-first tests in `app/portfolio_ledger/tests/test_fifo_accounting.py`.
Notes: Test coverage includes FIFO lot-order matching, realized gain from FIFO-matched basis, and split-driven open-lot quantity/unit-basis adjustments with total-basis preservation.
Notes: Task-local proof: `uv run pytest -v app/portfolio_ledger/tests/test_fifo_accounting.py` fails as expected because `app.portfolio_ledger.accounting` plus `match_sell_trade_fifo()`, `calculate_realized_gain_from_fifo()`, and `apply_split_to_open_lots()` are not implemented yet (tasks 2.1-3.2).
- [x] 1.3 Add failing integration tests for duplicate-safe ledger rebuilds from existing persisted canonical input
Notes: Rebuilding from the same source data must not create duplicate ledger, lot, or lot-disposition truth.
Notes: Added deterministic persisted-canonical seed fixture in `app/portfolio_ledger/tests/fixtures/dataset_1_v1_canonical_seed.json` and integration fail-first coverage in `app/portfolio_ledger/tests/test_rebuild_integration.py`.
Notes: Integration scenarios now cover (1) sequential rerun duplicate-safety and (2) concurrent rebuild duplicate-safety for the same persisted canonical source input, with assertions targeted at ledger and lot table row counts.
Notes: Added `app/portfolio_ledger/tests/conftest.py` to provide local async DB fixtures so integration tests execute in this feature-slice test package.
Notes: Task-local proof: `uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` fails as expected because `app.portfolio_ledger.service` and `rebuild_portfolio_ledger_from_canonical_records()` are not implemented yet (tasks 2.2-3.3).

## 2. Ledger schema and policy foundation

- [x] 2.1 Define typed ledger and accounting-policy schemas/constants for dataset 1 v1
Notes: Freeze one explicit policy version and keep unsupported fee/FX behavior explicit rather than implied.
Notes: Added typed ledger contracts in `app/portfolio_ledger/schemas.py` (`LedgerEventType`, `LedgerTargetTable`, `LedgerLineage`, `PersistedCanonicalRecord`, `LedgerEventSeed`).
Notes: Added explicit dataset-1 v1 policy constants in `app/portfolio_ledger/accounting.py` (`AccountingPolicyVersion`, `LotMatchingMethod`, `UnsupportedAccountingConcern`, `DATASET_1_V1_ACCOUNTING_POLICY`) with FIFO + unsupported fee/FX handling.
Notes: Added task-local contract tests in `app/portfolio_ledger/tests/test_policy_schemas.py` and verified green with `uv run pytest -v app/portfolio_ledger/tests/test_policy_schemas.py`.
Notes: Follow-up fail-first behavior remains intact for later tasks (`uv run pytest -v app/portfolio_ledger/tests/test_fifo_accounting.py` still fails on missing 3.2 callables).
- [x] 2.2 Add SQLAlchemy models and Alembic migration(s) for the minimal ledger and lot tables
Notes: Keep market-data and analytics-cache entities out of scope in this phase.
Notes: Added minimal SQLAlchemy models in `app/portfolio_ledger/models.py` for `portfolio_transaction`, `dividend_event`, `corporate_action_event`, `lot`, and `lot_disposition` with explicit lineage foreign keys and deterministic uniqueness constraints to support idempotent rebuild foundations.
Notes: Added Alembic migration `alembic/versions/12ecb9689094_add_portfolio_ledger_foundation_tables.py` (upgrade/downgrade + indexes) and registered `app.portfolio_ledger.models` in `alembic/env.py` metadata imports.
Notes: Added fail-first contract coverage in `app/portfolio_ledger/tests/test_models_schema.py`; task-local proof is green with `uv run pytest -v app/portfolio_ledger/tests/test_models_schema.py` and migration sanity check `uv run alembic upgrade head`.
- [x] 2.3 Add checked-in finance golden cases that lock FIFO, dividend, and split behavior for dataset 1
Notes: Golden cases are part of the contract, not optional test convenience.
Notes: Extended `app/portfolio_ledger/tests/fixtures/dataset_1_v1_finance_cases.json` with deterministic `dividend_income` coverage while preserving FIFO (`fifo_sell`) and split (`split_adjustment`) golden cases under one explicit `dataset_1_v1_fifo` policy version.
Notes: Added fixture-contract tests in `app/portfolio_ledger/tests/test_finance_golden_cases.py` to lock required case presence (FIFO/dividend/split) and dividend behavior (`gross - taxes = net`, open-lot basis unchanged).
Notes: Task-local proof is green with `uv run pytest -v app/portfolio_ledger/tests/test_finance_golden_cases.py` and companion policy alignment check `uv run pytest -v app/portfolio_ledger/tests/test_policy_schemas.py app/portfolio_ledger/tests/test_finance_golden_cases.py`.

## 3. Ledger derivation implementation

- [x] 3.1 Create a dedicated portfolio-ledger service that derives ledger events from persisted canonical records transactionally
Notes: Reuse persisted canonical input and preserve lineage back to source documents, import jobs, and canonical fingerprints.
Notes: Added `app/portfolio_ledger/service.py` with `map_canonical_record_to_ledger_event()` and `rebuild_portfolio_ledger_from_canonical_records()` as the dedicated derivation boundary consuming persisted `canonical_pdf_record` input.
Notes: Derivation now maps canonical `trade`/`dividend`/`split` records to ledger event seeds and persists `portfolio_transaction`, `dividend_event`, and `corporate_action_event` rows with explicit lineage (`source_document_id`, `import_job_id`, `canonical_record_id`, `canonical_fingerprint`) inside a transactional rebuild flow.
Notes: Service is fail-fast for unsupported/malformed canonical payload values via explicit `PortfolioLedgerClientError`; lot derivation and duplicate-safe rerun/concurrency behavior remain scoped to tasks 3.2-3.3.
Notes: Task-local proof is green with `uv run pytest -v app/portfolio_ledger/tests/test_canonical_mapping.py`.
- [x] 3.2 Implement FIFO lot derivation and lot-disposition logic for buy, sell, and split flows
Notes: Dividends remain separate income events and must not mutate lot basis.
Notes: Implemented FIFO accounting callables in `app/portfolio_ledger/accounting.py`: `match_sell_trade_fifo()`, `calculate_realized_gain_from_fifo()`, and `apply_split_to_open_lots()`.
Notes: FIFO sell matching now consumes open lots in order, emits deterministic lot-disposition payloads, and computes matched basis for realized-gain evaluation; split handling adjusts open-lot quantities by split ratio while preserving total lot basis and recomputing unit basis.
Notes: Added strict fail-fast numeric/string coercion guards for accounting inputs to prevent silent inference on malformed payloads.
Notes: Task-local proof is green with `uv run pytest -v app/portfolio_ledger/tests/test_fifo_accounting.py`; companion contract alignment is green with `uv run pytest -v app/portfolio_ledger/tests/test_policy_schemas.py app/portfolio_ledger/tests/test_finance_golden_cases.py app/portfolio_ledger/tests/test_fifo_accounting.py`.
- [x] 3.3 Enforce idempotent and duplicate-safe ledger rebuild behavior for reruns and concurrent rebuilds
Notes: Database uniqueness remains the final arbiter for duplicate races in this slice.
Notes: Rebuild flow in `app/portfolio_ledger/service.py` now performs conflict-safe upserts (`ON CONFLICT`) for derived `portfolio_transaction`, `dividend_event`, and `corporate_action_event` rows keyed by canonical-record uniqueness constraints.
Notes: Added deterministic lot and lot-disposition rebuild logic driven from ledger events, with upsert semantics for `lot` (`uq_lot_opening_tx`) and `lot_disposition` (`uq_lot_disposition_lot_sell_tx`) so reruns and concurrent runs reconcile instead of duplicating.
Notes: Duplicate-safe behavior is validated with `uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (rerun + concurrent scenarios both green).
Notes: Focused ledger-slice regression is also green with `uv run pytest -v app/portfolio_ledger/tests/test_canonical_mapping.py app/portfolio_ledger/tests/test_fifo_accounting.py app/portfolio_ledger/tests/test_finance_golden_cases.py -m "not integration"` and integration rerun.

## 4. Validation and documentation

- [x] 4.1 Run targeted and integration validation for the ledger foundation slice
Notes: Expected checks include targeted `pytest`, integration/database validation, `ruff`, `black --check --diff`, `bandit`, `mypy`, `pyright`, and `ty`.
Notes: Ledger-slice validation is green with `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 3 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (3 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger`, `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger --check --diff`, `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_ledger --severity-level high --confidence-level high`, `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger`, `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger`, and `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger`.
- [x] 4.2 Update affected product and guide documents to record the frozen accounting policy and ledger boundary
Notes: Reflect the new contract in roadmap-adjacent guidance without claiming analytics or market-data support yet.
Notes: Updated `docs/product/roadmap.md` Phase 3 bullets to capture implemented ledger entities, frozen `dataset_1_v1` policy scope, explicit unsupported fee/FX behavior, and Phase 3 boundary from analytics/market-data work.
Notes: Updated `docs/guides/portfolio-ledger-and-analytics-guide.md` with a concrete “Current Repository Contract (Phase 3)” section that records implemented ledger chain, event support, policy freeze, and deferred analytics boundary.
- [x] 4.3 Update `CHANGELOG.md` and any affected OpenSpec or validation references after implementation
Notes: Record the ledger foundation as the prerequisite phase before analytics APIs and frontend work.
Notes: Added 2026-03-22 changelog entry describing completed ledger-foundation closeout, frozen accounting policy boundary, documentation updates, and validation evidence.
Notes: Updated `docs/guides/validation-baseline.md` to reflect implemented portfolio-ledger foundation status and required duplicate-safe ledger rebuild validation expectations.
Notes: `openspec validate --specs --all` confirms `change/add-ledger-foundation-and-accounting-policy-for-dataset-1` passes; pre-existing failures remain in `spec/pdf-ingestion` and `spec/pdf-preflight-analysis`.
