## 0. Investigation

- [x] 0.1 Confirm the exact Phase 4 analytics boundary from the roadmap, PRD, ADRs, ledger guide, and current OpenSpec specs before coding
Notes: Keep this change inside analytics service plus API scope. Do not expand into market-data ingestion, pricing snapshots, or frontend implementation.
Notes: Confirm that KPI v1 stays ledger-only and explainable from `portfolio_transaction`, `dividend_event`, `lot`, and `lot_disposition`.
Notes: Confirmed boundary from `docs/product/roadmap.md` (Phase 4 analytics API vs later market-data/front-end phases), `docs/product/decisions.md` ADR-009/010/011 (ledger-first + market-data separation + explicit accounting assumptions), and `docs/guides/portfolio-ledger-and-analytics-guide.md` (analytics derived from ledger truth with clear market-data boundary).
Notes: `openspec/changes/add-portfolio-analytics-api-from-ledger/specs/portfolio-analytics/spec.md` and `design.md` intentionally freeze v1 to ledger-only KPIs plus `as_of_ledger_at`; price-dependent valuation fields remain deferred.
Notes: Current routing in `app/main.py` still includes only health plus PDF pipeline slices, so analytics remains a net-new read-only feature slice and route surface.
- [x] 0.2 Diagnose blast radius across router registration, query patterns, response schemas, validation docs, and future frontend dependencies
Notes: Explicitly map affected areas in `app/main.py`, the new `app/portfolio_analytics/` slice, validation expectations, and docs that describe Phase 4 boundaries.
Notes: Confirm whether any shared schemas are truly cross-slice or whether analytics should remain self-contained inside its feature slice.
Notes: Blast radius includes new files under `app/portfolio_analytics/` (`schemas.py`, `service.py`, `routes.py`, `tests/`), router import/registration in `app/main.py`, and read-only query coupling to `app/portfolio_ledger/models.py` plus async DB dependency wiring from `app/core/database.py`.
Notes: Contract surface for frontend Phase 5 is established by `GET /api/portfolio/summary` and `GET /api/portfolio/lots/{instrument_symbol}` with deterministic symbol normalization, explicit unknown-symbol failure, and shared `as_of_ledger_at` consistency metadata.
Notes: Keep analytics schemas self-contained in the feature slice for now; no shared-schema extraction is justified yet because this contract is currently single-slice and not reused by 3+ features.

## 1. Contract and failing tests

- [x] 1.1 Add failing unit tests for grouped summary analytics formulas from existing ledger truth
Notes: Cover grouped rows by `instrument_symbol` and assert ledger-only KPI fields such as `open_quantity`, `open_cost_basis_usd`, `realized_gain_usd`, and dividend totals.
Notes: Added fail-first unit coverage in `app/portfolio_analytics/tests/test_grouped_summary_formulas.py` for grouped summary KPI formulas derived from ledger truth (`lot`, `lot_disposition`, `portfolio_transaction`, `dividend_event`).
Notes: Test assertions lock ledger-only KPI fields per `instrument_symbol` (`open_quantity`, `open_cost_basis_usd`, `open_lot_count`, `realized_proceeds_usd`, `realized_cost_basis_usd`, `realized_gain_usd`, `dividend_gross_usd`, `dividend_taxes_usd`, `dividend_net_usd`) and include a dedicated sell-proceeds de-duplication case for one sell transaction mapped to multiple lot dispositions.
Notes: Task-local proof: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests/test_grouped_summary_formulas.py` fails as expected because `app.portfolio_analytics.service` and `build_grouped_portfolio_summary_from_ledger()` are not implemented yet (tasks 2.1-2.2).
- [x] 1.2 Add failing unit tests for lot-detail analytics output and unknown-symbol rejection
Notes: Verify explainable lot rows plus linked disposition detail for an existing symbol, deterministic symbol normalization (trim + case-insensitive), and explicit client-facing failure for a missing symbol.
Notes: Added fail-first lot-detail unit coverage in `app/portfolio_analytics/tests/test_lot_detail_formulas.py` for deterministic symbol normalization (`" voo "` -> `"VOO"`), explainable lot rows with linked disposition history, and explicit unknown-symbol rejection via `PortfolioAnalyticsClientError` not-found semantics.
Notes: Test coverage locks lot-level disposition explainability by asserting per-lot matched quantity, matched basis, and linked sell transaction identifiers in the response payload.
- [x] 1.3 Add failing route/integration tests for summary and lot-detail endpoints
Notes: Route tests should lock response shape, status codes, and `as_of_ledger_at` presence; integration tests should prove analytics are computed from persisted ledger state rather than PDF reprocessing.
Notes: Added fail-first route and integration coverage in `app/portfolio_analytics/tests/test_routes.py` for `GET /api/portfolio/summary` and `GET /api/portfolio/lots/{instrument_symbol}`, including response-shape/status assertions and required `as_of_ledger_at` timestamp presence.
Notes: Integration path seeds persisted ledger truth rows and guards against accidental PDF pipeline coupling by patching extraction/normalization/persistence/rebuild entrypoints to raise if called, proving analytics requests should consume persisted ledger state only.
Notes: Added `app/portfolio_analytics/tests/conftest.py` integration fixtures with explicit migrated-table checks for analytics-slice DB-backed tests.
Notes: Task-local proof: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests/test_lot_detail_formulas.py app/portfolio_analytics/tests/test_routes.py` fails as expected because `app.portfolio_analytics.service` and `app.portfolio_analytics.routes` are not implemented yet (tasks 2.1-3.2).

## 2. Analytics schemas and service

- [x] 2.1 Define typed analytics schemas for grouped summary, lot detail, and route responses
Notes: Keep response models explicit and stable for the future frontend; include `as_of_ledger_at` and do not add price-dependent fields in this change.
Notes: Added explicit analytics response schemas in `app/portfolio_analytics/schemas.py` (`PortfolioSummaryResponse`, `PortfolioLotDetailResponse`, row/detail models) including `as_of_ledger_at` and ledger-only KPI fields.
- [x] 2.2 Implement grouped summary query/service logic from ledger and lot tables
Notes: Compute only ledger-supported KPI fields, emit explicit `as_of_ledger_at`, and keep analytics read-only over persisted truth.
Notes: Implemented grouped summary service/builders in `app/portfolio_analytics/service.py` over persisted `lot`, `lot_disposition`, sell `portfolio_transaction`, and `dividend_event` rows with sell-proceeds de-duplication and max-ledger `as_of_ledger_at`.
- [x] 2.3 Implement lot-detail query/service logic with explainable disposition history
Notes: Reuse persisted lot and sell-side disposition data rather than re-deriving accounting logic inside analytics, with deterministic symbol normalization.
Notes: Implemented lot-detail service logic with deterministic symbol normalization (`trim + uppercase`), explicit unknown-symbol `404`, and explainable per-lot disposition linkage including sell gross amounts.

## 3. API routes and application wiring

- [x] 3.1 Add portfolio analytics FastAPI routes for grouped summary and lot detail
Notes: Use a portfolio-facing route surface and explicit client errors for unsupported symbol requests.
Notes: Added `app/portfolio_analytics/routes.py` with `GET /api/portfolio/summary` and `GET /api/portfolio/lots/{instrument_symbol}`, explicit `PortfolioAnalyticsClientError` -> `HTTPException` mapping, and structured route-level logs.
- [x] 3.2 Register the analytics router in the application entrypoint and align structured logging
Notes: Logging should follow the repo event naming standard and keep request-level context explicit; analytics routes must not invoke rebuild operations.
Notes: Registered `portfolio_analytics_router` in `app/main.py`; route integration tests validate read-only behavior by patching extraction/normalization/persistence/rebuild entrypoints to fail if invoked.

## 4. Validation and documentation

- [x] 4.1 Run targeted unit, route, and integration validation for the analytics slice
Notes: Expected checks include targeted `pytest`, `ruff`, `black --check --diff`, `bandit`, `mypy`, `pyright`, and `ty`; include DB-backed integration checks if analytics tests depend on real ledger rows.
Notes: Validation evidence: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests` (7 passed, includes DB-backed route integration), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics app/main.py`, `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_analytics app/main.py --check --diff`, `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_analytics --severity-level high --confidence-level high`, `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py`, `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py`, `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py` (all pass).
- [x] 4.2 Update roadmap-adjacent guides and validation references for the new analytics API boundary
Notes: Reflect that grouped and lot-detail analytics APIs are implemented while market-data-dependent valuation remains deferred.
Notes: Updated roadmap/guide references in `docs/product/roadmap.md`, `docs/guides/portfolio-ledger-and-analytics-guide.md`, and `docs/guides/validation-baseline.md` to record implemented Phase 4 analytics endpoints and explicit market-data valuation deferral.
- [x] 4.3 Update `CHANGELOG.md` and confirm OpenSpec artifacts are archive-ready after implementation
Notes: Record the analytics API as the prerequisite backend contract for the later frontend MVP.
Notes: Added changelog entry documenting analytics API delivery, files touched, and validation evidence; OpenSpec apply progress is now expected to be archive-ready once all tasks are checked complete.
