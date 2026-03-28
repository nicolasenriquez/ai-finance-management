## 0. Investigation

- [x] 0.1 Confirm the exact Phase 6 KPI boundary from the roadmap, PRD, ADRs, current analytics spec, and existing market-data contracts before coding
Notes: Keep this change inside grouped summary market-enrichment only. Do not expand into lot-detail valuation, public market-data routes, FX conversion, or scheduler work.
Notes: Confirm the enriched summary must expose explicit pricing provenance and remain read-only over ledger plus persisted market-data truth.
Notes: Confirmed boundary from `docs/product/roadmap.md` Phase 6 contract (`market_data_snapshot`/`price_history` internal read boundary, no public market-data router, no scheduler expansion), plus current deferred valuation posture that this change is intended to advance.
Notes: Confirmed from `docs/product/prd.md` and ADR implications in `docs/product/decisions.md` that valuation metrics must include explicit pricing provenance and must not mutate ledger truth.
Notes: Confirmed from `openspec/specs/portfolio-analytics/spec.md` that existing API behavior is ledger-only v1 today (`open_*`, `realized_*`, `dividend_*`, `as_of_ledger_at`), so this change is a spec-level contract extension rather than implementation-only refactor.

- [x] 0.2 Diagnose blast radius across analytics schemas, market-data read helpers, frontend summary contract, and validation/docs
Notes: Explicitly map affected areas in `app/portfolio_analytics/`, `app/market_data/`, `frontend/src/`, `docs/product/`, `docs/guides/`, and `CHANGELOG.md`.
Notes: Confirm whether current market-data read helpers are sufficient or whether one focused snapshot-selection helper is needed for coherent summary valuation.
Notes: Backend blast radius confirmed in `app/portfolio_analytics/{service.py,schemas.py,routes.py}` plus existing test surface `app/portfolio_analytics/tests/{test_grouped_summary_formulas.py,test_snapshot_consistency.py,test_routes.py}` for fail-first coverage and response/behavior updates.
Notes: `app/market_data/service.py::list_price_history_for_symbol` is currently symbol-scoped; coherent summary valuation across multiple open symbols likely requires one focused internal snapshot-selection helper rather than ad hoc per-symbol latest-row reads.
Notes: Frontend blast radius confirmed in `frontend/src/core/api/schemas.ts`, `frontend/src/features/portfolio-summary/{api.ts,overview.ts,PortfolioSummaryHeader.tsx,PortfolioSummaryTable.tsx}`, and `frontend/src/pages/portfolio-summary-page/{PortfolioSummaryPage.tsx,PortfolioSummaryPage.test.tsx}`.
Notes: Documentation blast radius confirmed in `docs/product/{roadmap.md,decisions.md,frontend-mvp-prd-addendum.md}`, `docs/guides/{validation-baseline.md,portfolio-ledger-and-analytics-guide.md,frontend-api-and-ux-guide.md}`, and `CHANGELOG.md`.

## 1. Contract and failing tests

- [x] 1.1 Add failing backend tests for enriched grouped summary formulas, snapshot provenance, and missing-coverage rejection
Notes: Lock the expected valuation fields, selected snapshot metadata, and explicit failure when an open-position symbol lacks safe pricing coverage in the chosen snapshot.
Notes: Cover closed-position rows so valuation fields do not require pricing when `open_quantity == 0`.
Notes: Added fail-first backend contract tests in `app/portfolio_analytics/tests/test_market_enriched_contract.py` requiring row-level market fields (`latest_close_price_usd`, `market_value_usd`, `unrealized_gain_usd`, `unrealized_gain_pct`) and response-level pricing provenance (`pricing_snapshot_key`, `pricing_snapshot_captured_at`).
Notes: Added fail-first service tests in `app/portfolio_analytics/tests/test_grouped_summary_formulas.py` for open-position market-field presence plus explicit missing-coverage rejection via a required `validate_open_position_price_coverage()` contract.
Notes: Task-local proof (expected fail-first): `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_market_enriched_contract.py app/portfolio_analytics/tests/test_grouped_summary_formulas.py::test_grouped_summary_open_rows_require_market_enriched_valuation_fields app/portfolio_analytics/tests/test_grouped_summary_formulas.py::test_missing_open_position_price_coverage_is_rejected_explicitly` -> 4 failed with missing schema fields and missing coverage-validation callable.

- [x] 1.2 Add failing frontend/API contract tests for the expanded summary payload and updated ledger-vs-market copy
Notes: Update typed API schemas/tests first so the frontend contract is explicit before implementation.
Notes: Keep summary messaging aligned with the new bounded valuation contract and explicit pricing provenance.
Notes: Added fail-first frontend API contract tests in `frontend/src/core/api/schemas.market-enriched.test.ts` requiring market-enriched row fields and explicit pricing snapshot provenance in summary responses.
Notes: Added fail-first UI copy assertion in `frontend/src/pages/portfolio-summary-page/PortfolioSummaryPage.test.tsx` requiring market-enriched plus pricing-provenance messaging on summary success state.
Notes: Task-local proof (expected fail-first): `cd frontend && npm run test -- src/core/api/schemas.market-enriched.test.ts src/pages/portfolio-summary-page/PortfolioSummaryPage.test.tsx` -> 3 failed (schema contract still accepts legacy payload and new market-enriched copy is not rendered yet).

## 2. Backend implementation

- [x] 2.1 Implement or extend internal market-data read helpers to resolve one consistent persisted snapshot for required open-position symbols
Notes: Keep snapshot-selection logic internal to backend services. Do not add public market-data routes in this change.
Notes: The selected snapshot must be coherent for all open-position symbols used in the summary response.
Notes: Added `resolve_latest_consistent_snapshot_coverage_for_symbols()` in `app/market_data/service.py` with `MarketDataConsistentSnapshotCoverage` to select one latest persisted snapshot (`snapshot_captured_at` desc) that has USD pricing coverage for every required symbol.
Notes: Snapshot coverage helper remains internal to backend services; no public market-data router changes were introduced.

- [x] 2.2 Expand portfolio analytics summary schemas and service logic with pricing provenance and bounded valuation fields
Notes: Preserve existing ledger-only KPI fields and add only the approved market-enriched fields for this slice.
Notes: Keep the summary path read-only and fail fast when required pricing coverage is incomplete.
Notes: Expanded `PortfolioSummaryRow` with bounded valuation fields (`latest_close_price_usd`, `market_value_usd`, `unrealized_gain_usd`, `unrealized_gain_pct`) and `PortfolioSummaryResponse` with explicit provenance (`pricing_snapshot_key`, `pricing_snapshot_captured_at`) in `app/portfolio_analytics/schemas.py`.
Notes: Updated `get_portfolio_summary_response()` and `build_grouped_portfolio_summary_from_ledger()` in `app/portfolio_analytics/service.py` to enrich open rows from one selected snapshot, keep closed-row valuation nullable, and enforce fail-fast coverage with `validate_open_position_price_coverage()`.
Notes: Task-local proof: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_market_enriched_contract.py app/portfolio_analytics/tests/test_grouped_summary_formulas.py app/portfolio_analytics/tests/test_snapshot_consistency.py` (8 passed).

- [x] 2.3 Update the summary route integration surface without changing lot-detail behavior
Notes: Route behavior should expose explicit client-facing failure for unsafe valuation coverage while leaving lot-detail contract unchanged.
Notes: Updated integration seed surface in `app/portfolio_analytics/tests/test_routes.py` to include deterministic `market_data_snapshot` + `price_history` rows for summary success-path assertions, including pricing provenance and valuation fields.
Notes: Added explicit integration rejection coverage `test_summary_endpoint_rejects_missing_open_position_price_coverage` asserting `409` when open-position pricing coverage is unavailable; lot-detail tests and lot-detail service contract remain unchanged.
Notes: Task-local proof: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_routes.py -k "summary_endpoint_returns_grouped_rows_with_as_of_ledger_at or summary_endpoint_rejects_missing_open_position_price_coverage" -m integration` (2 passed, 2 deselected).

## 3. Frontend, docs, and validation

- [x] 3.1 Update frontend summary rendering, API types, and tests for market-enriched KPI fields and explicit pricing provenance
Notes: Keep the UI clear about ledger-state vs pricing-state freshness and avoid implying unsupported FX-sensitive precision.
Notes: Expanded frontend summary API schemas in `frontend/src/core/api/schemas.ts` with required market-enriched row fields and required response provenance (`pricing_snapshot_key`, `pricing_snapshot_captured_at`) using nullable semantics where closed rows/no-open-position summary responses are valid.
Notes: Updated summary rendering in `frontend/src/features/portfolio-summary/{PortfolioSummaryHeader.tsx,PortfolioSummaryTable.tsx,overview.ts}` and `frontend/src/pages/portfolio-summary-page/PortfolioSummaryPage.tsx` to surface pricing provenance and bounded valuation fields while keeping lot drill-down behavior unchanged.
Notes: Updated frontend tests in `frontend/src/core/api/schemas.market-enriched.test.ts`, `frontend/src/pages/portfolio-summary-page/PortfolioSummaryPage.test.tsx`, `frontend/src/features/portfolio-summary/{overview.test.ts,PortfolioSummaryTable.keyboard.test.tsx}` for enriched payload contract and copy assertions.
Notes: Task-local proof: `cd frontend && npm run test -- src/core/api/schemas.market-enriched.test.ts src/pages/portfolio-summary-page/PortfolioSummaryPage.test.tsx src/features/portfolio-summary/overview.test.ts src/features/portfolio-summary/PortfolioSummaryTable.keyboard.test.tsx` (10 passed).

- [x] 3.2 Update product/guides/OpenSpec-adjacent docs for the new analytics boundary
Notes: Reflect that grouped summary is now market-enriched while public market-data routes, lot-detail valuation, and FX-sensitive analytics remain deferred.
Notes: Updated product docs in `docs/product/{roadmap.md,decisions.md,frontend-mvp-prd-addendum.md}` to reflect market-enriched summary delivery in Phase 6 with explicit provenance and unchanged non-goals.
Notes: Updated implementation guides in `docs/guides/{portfolio-ledger-and-analytics-guide.md,frontend-api-and-ux-guide.md,validation-baseline.md}` so current contracts/state models/validation gates match summary enrichment behavior and deferred boundaries.

- [x] 3.3 Run targeted backend/frontend validation and record the change in `CHANGELOG.md`
Notes: Expected checks include targeted backend/frontend tests plus `ruff`, `black --check --diff`, `mypy`, `pyright`, `ty`, relevant integration coverage, and `openspec validate --specs --all`.
Notes: Added delivery record in `CHANGELOG.md` (`feat(portfolio-analytics): deliver market-enriched summary KPIs with snapshot provenance across API, frontend, and docs`) including scope, rationale, touched areas, and validation evidence.
Notes: Validation evidence: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_market_enriched_contract.py app/portfolio_analytics/tests/test_grouped_summary_formulas.py app/portfolio_analytics/tests/test_snapshot_consistency.py` (8 passed); `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_routes.py -k "summary_endpoint_returns_grouped_rows_with_as_of_ledger_at or summary_endpoint_rejects_missing_open_position_price_coverage" -m integration` (2 passed, 2 deselected); `cd frontend && npm run lint` (pass); `cd frontend && npm run test` (26 passed); `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/market_data/service.py app/portfolio_analytics/schemas.py app/portfolio_analytics/service.py app/portfolio_analytics/tests/test_routes.py` (pass); `UV_CACHE_DIR=/tmp/uv-cache uv run black app/market_data/service.py app/portfolio_analytics/schemas.py app/portfolio_analytics/service.py app/portfolio_analytics/tests/test_routes.py --check --diff` (pass); `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass); `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (0 errors); `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app` (pass); `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (16/16 passed).
