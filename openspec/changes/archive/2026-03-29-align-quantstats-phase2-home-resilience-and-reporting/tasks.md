## 1. Investigation and Contract Baseline

- [x] 1.1 Reconcile QuantStats official API surface (`stats`, `reports`, Monte Carlo) against current adapter implementation and record required compatibility mappings before code changes.
  Notes:
  - Confirmed pinned runtime callable mismatch: `quantstats.stats.alpha`/`beta` are unavailable in `quantstats==0.0.81`; benchmark-relative metrics must map via `quantstats.stats.greeks`.
  - Recorded explicit compatibility mapping in `docs/standards/quantstats-standard.md` (`Pinned-version compatibility mapping` section).
- [x] 1.2 Add fail-first backend tests that reproduce current QuantStats compatibility failure and define expected resilient behavior for optional benchmark metrics.
  Notes:
  - Added fail-first backend adapter tests in `app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py`.
  - Added one reproduction test for current mismatch failure and one future-state resilience expectation test for optional benchmark metrics.
- [x] 1.3 Add fail-first frontend tests for Home section-scoped failure boundaries (core context success with quant/report section error).
  Notes:
  - Added fail-first Home test in `frontend/src/pages/portfolio-home-page/PortfolioHomePage.test.tsx` expecting core modules to remain visible when quant section fails.
- [x] 1.4 Confirm metric placement matrix (Home preview vs Risk context vs Quant/report route) and capture it in docs/OpenSpec artifacts before implementation.
  Notes:
  - Captured explicit placement matrix in `docs/standards/quantstats-standard.md` (`Metric Placement Matrix` section).
  - Design and proposal already align with this matrix via section-scoped Home resilience and risk-context metric interpretation boundaries.

## 2. Backend Quant Adapter and Reporting

- [x] 2.1 Refactor QuantStats adapter in `app/portfolio_analytics/service.py` to use version-compatible metric call paths and explicit optional benchmark metric handling.
  Notes:
  - Refactored optional benchmark-relative metrics (`alpha`, `beta`) to use `quantstats.stats.greeks` compatibility path; core metrics remain strict-call fail-fast.
  - Added explicit benchmark omission behavior so missing/incompatible optional benchmark outputs do not block core quant metric rows.
- [x] 2.2 Extend quant metrics response contract/schema to represent optional benchmark-relative metrics and explicit omission metadata.
  Notes:
  - Added `PortfolioQuantBenchmarkContext` and attached it to `PortfolioQuantMetricsResponse` as `benchmark_context`.
  - Contract now carries `omitted_metric_ids` and `omission_reason` for optional benchmark-relative metrics.
- [x] 2.3 Implement bounded HTML tearsheet generation API flow (`portfolio` and `instrument_symbol` scope) with deterministic validation and retrieval contracts.
  Notes:
  - Added report-generation service/route flow: `POST /api/portfolio/quant-reports` with typed request/response models.
  - Added report retrieval route: `GET /api/portfolio/quant-reports/{report_id}` returning HTML artifact content.
- [x] 2.4 Enforce report artifact lifecycle controls (deterministic naming, retention, and explicit unavailable-state failures).
  Notes:
  - Added deterministic report id/path strategy plus bounded in-memory artifact registry with TTL purge.
  - Retrieval now fails explicitly with unavailable/expired semantics (`404`/`410`) and cleanup behavior.
- [x] 2.5 Add backend tests for successful report generation, invalid-scope rejection, unavailable-artifact retrieval, and read-only side-effect boundaries.
  Notes:
  - Added integration tests in `app/portfolio_analytics/tests/test_routes.py` for report success, invalid scope rejection, unavailable artifact retrieval, and read-only guardrails.
  - Updated adapter/contract tests to validate resilient benchmark omission context and updated QuantStats compatibility behavior.

## 3. Frontend Resilience and UX Alignment

- [x] 3.1 Update Home route composition to isolate optional quant/report failures from core summary/trend/hierarchy rendering with section-scoped loading/empty/error boundaries.
  Notes:
  - Refactored `frontend/src/pages/portfolio-home-page/PortfolioHomePage.tsx` to keep summary/trend/hierarchy rendering available even when quant/report modules fail.
  - Added section-scoped quant/report loading/error/empty behavior and retry-safe state mapping.
- [x] 3.2 Add/update quant and risk route labels to preserve explicit interpretation boundaries for preview vs risk-context metrics, including explicit benchmark-omission context messaging.
  Notes:
  - Updated workspace labels and page copy: `Analytics (Preview)` and `Risk (Interpretation)` with explicit scope framing.
  - Home quant/report module now renders benchmark omission context from `benchmark_context` metadata.
- [x] 3.3 Integrate report-generation UI controls and result handling with explicit loading/error/ready states, including typed generation and artifact-retrieval contracts.
  Notes:
  - Added typed report generate/retrieve contracts in frontend API schemas/client/hooks.
  - Added report action controls for `portfolio` and `instrument_symbol` scope, generation lifecycle states, metadata display, retrieval link, and HTML preview handling.
- [x] 3.4 Apply hierarchy table visual refinements aligned to target design while preserving deterministic controls, explicit control labeling, and keyboard accessibility behavior.
  Notes:
  - Updated hierarchy interactions with explicit control labels and deterministic expansion semantics for groups/assets.
  - Added toolbar and row-control accessibility labeling (`aria-label`/`aria-controls`) while preserving keyboard operability.
- [x] 3.5 Extend frontend tests for section-scoped errors, report action flows, benchmark-context rendering, and hierarchy interaction determinism.
  Notes:
  - Extended Home tests for section-scoped error boundaries, report action flow, and benchmark-omission rendering.
  - Added `frontend/src/features/portfolio-hierarchy/PortfolioHierarchyTable.test.tsx` for deterministic, explicit control behavior.
  - Updated analytics/risk/workspace layout tests to verify interpretation-boundary labels.

## 4. Standards and Documentation

- [x] 4.1 Add `docs/standards/quantstats-standard.md` using official QuantStats documentation references and repository fail-fast rules.
  Notes:
  - Added `docs/standards/quantstats-standard.md` with pinned-version compatibility mapping (`quantstats==0.0.81`), adapter safety rules, Monte Carlo interpretation guidance, and official QuantStats links.
- [x] 4.2 Update docs navigation and product references to include QuantStats standard, report capability scope, and placement matrix decisions.
  Notes:
  - Added QuantStats standard to `docs/README.md` navigation.
  - Updated frontend UX/API and roadmap docs with quant report endpoint scope and Home/Risk/Quant placement boundary guidance.
- [x] 4.3 Add changelog entry documenting quant adapter resilience changes, report contracts, and validation evidence.
  Notes:
  - Added `2026-03-29` changelog entry covering backend adapter/report contracts, frontend resilience UX, hierarchy controls, docs updates, and validation commands/outcomes.

## 5. Validation and Closeout

- [x] 5.1 Run backend gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`) and targeted pytest suites for portfolio analytics quant/report paths.
  Notes:
  - Backend gates passed:
    - `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics app/core/config.py`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_analytics app/core/config.py --check --diff`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app`
  - Targeted quant/report pytest evidence passed:
    - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests/test_quant_dependency_policy.py app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py app/portfolio_analytics/tests/test_quant_report_artifact_lifecycle.py app/portfolio_analytics/tests/test_time_series_benchmark_overlays.py`
    - `ALLOW_INTEGRATION_DB_MUTATION=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests/test_quant_dependency_policy.py app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py app/portfolio_analytics/tests/test_quant_report_artifact_lifecycle.py app/portfolio_analytics/tests/test_time_series_benchmark_overlays.py app/portfolio_analytics/tests/test_routes.py -k "quant_report_generation or quant_report_artifact_retrieval or quant_report_retrieval or quant_metrics"`
- [x] 5.2 Run frontend gates (`lint`, `test`, `build`) including updated workspace route tests.
  Notes:
  - Frontend gates passed:
    - `npm --prefix frontend run lint`
    - `npm --prefix frontend run test`
    - `npm --prefix frontend run build`
- [x] 5.3 Run OpenSpec validation for this change and specs, then record command outcomes in change artifacts/changelog.
  Notes:
  - OpenSpec validation passed:
    - `OPENSPEC_TELEMETRY=0 openspec validate align-quantstats-phase2-home-resilience-and-reporting --type change --strict --json`
    - `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json`
