## 1. Scope and Contract Baseline

- [x] 1.1 Reconcile current portfolio analytics and frontend route contracts against new workspace/risk specs and record any conflicts before coding.
  Notes:
  - Current backend exposes only `/api/portfolio/summary` and `/api/portfolio/lots/{instrument_symbol}`; new workspace endpoints are not yet implemented.
  - Baseline endpoint paths for fail-first contracts are fixed to `/api/portfolio/time-series` and `/api/portfolio/contribution` for tasks 2.1-2.2.
  - Baseline temporal/provenance metadata for chart responses is fixed to `as_of_ledger_at`, `period`, `frequency`, and `timezone`.
  - Baseline insufficiency contract for requested unsupported history coverage is fixed to explicit `409` client rejection with factual `detail`.
  - Baseline frontend workspace route paths are fixed to `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, and `/portfolio/transactions` while preserving `/portfolio` and `/portfolio/:symbol`.
- [x] 1.2 Add fail-first backend contract tests for time-series and contribution endpoints, including provenance and insufficiency rejection paths.
  Notes:
  - Added fail-first route contract tests in `app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py`.
  - Tests intentionally fail until tasks 2.1-2.2 add route registration and service callables for time-series/contribution.
- [x] 1.3 Add fail-first frontend contract tests for new workspace route state handling (`Home`, `Analytics`, `Risk`, `Transactions`) and explicit error/empty behavior.
  Notes:
  - Added fail-first workspace contract tests in `frontend/src/app/analytics-workspace.contract.test.ts`.
  - Tests intentionally fail until tasks 3.1-3.4 add route registrations plus explicit loading/empty/error state coverage modules/tests.
- [x] 1.4 Add a quant-stack decision record in project docs/OpenSpec artifacts with explicit accepted vs rejected package matrix and rationale.
  Notes:
  - Added ADR-018 in `docs/product/decisions.md` with accepted/conditional/rejected quant package matrix and explicit rationale.
  - Extended OpenSpec decision section in `design.md` with the same quant package matrix for implementation-time traceability.
- [x] 1.5 Pin approved quant packages for estimator computation in `pyproject.toml` and `uv.lock`, and record upgrade policy (PR-scoped upgrade + fixture-diff review).
  Notes:
  - Pinned runtime quant dependencies in `pyproject.toml` as exact versions: `numpy==2.4.3`, `pandas==3.0.1`, `scipy==1.17.1`.
  - Regenerated `uv.lock` so root `requires-dist` and resolved package versions match exact quant pins.
  - Recorded upgrade policy in ADR/OpenSpec: PR-scoped quant upgrades with required estimator fixture-diff review evidence.
- [x] 1.6 Add dependency guard coverage (check or test) that fails if rejected packages (`zipline`, `zipline-reloaded`, `pyfolio`, `pyrisk`, `mibian`, `backtrader`, `QuantLib-Python`) are introduced into runtime estimator dependencies.
  Notes:
  - Added guard tests in `app/portfolio_analytics/tests/test_quant_dependency_policy.py`.
  - Coverage enforces exact quant pins + lock sync and rejects banned package presence in runtime dependency closure derived from `uv.lock`.
- [x] 1.7 Define and document v1 estimator methodology contract (default windows `30/90/252`, return basis semantics, annualization basis, and required metadata fields) before endpoint implementation.
  Notes:
  - Extended risk-estimator OpenSpec contract with frozen v1 methodology defaults and required metadata field set in `specs/portfolio-risk-estimators/spec.md`.
  - Documented the same frozen methodology contract in project docs (`docs/product/frontend-ux-analytics-expansion-roadmap.md`, `docs/product/decisions.md` ADR-019).
- [x] 1.8 Lock chart foundation decision to `Recharts` in docs/OpenSpec artifacts, including explicit re-evaluation criteria tied to route-level performance evidence.
  Notes:
  - Added explicit `Recharts` lock and evidence-gated re-evaluation criteria in OpenSpec workspace spec and design decisions.
  - Documented route-level re-evaluation gates and required decision-evidence artifact in product roadmap and ADR-020.
- [x] 1.9 Lock `Transactions` route v1 scope to ledger events only and record market-refresh diagnostics as deferred follow-up scope.
  Notes:
  - Confirmed and expanded `Transactions` ledger-only v1 contract in workspace spec with explicit deferred diagnostics follow-up scenario.
  - Recorded the same boundary in OpenSpec design + product docs (`frontend-ux-analytics-expansion-roadmap.md`, ADR-021).

## 2. Backend Analytics and Risk Endpoints

- [x] 2.1 Implement read-only portfolio time-series endpoint with deterministic ordering and explicit as-of metadata.
  Notes:
  - Added `/api/portfolio/time-series` route + typed service path (`PortfolioTimeSeriesResponse`) with deterministic timestamp alignment across open-position symbols.
  - Contract coverage validates provenance fields and explicit insufficient-history `409` behavior in `test_workspace_endpoint_contracts_fail_first.py`.
- [x] 2.2 Implement contribution-by-symbol endpoint for supported periods from persisted truth.
  Notes:
  - Added `/api/portfolio/contribution` route + typed service path (`PortfolioContributionResponse`) using aligned start/end valuation deltas from persisted snapshot rows only.
  - Contract coverage validates per-period provenance and explicit insufficient-history `409` behavior in `test_workspace_endpoint_contracts_fail_first.py`.
- [x] 2.3 Implement risk-estimator endpoint(s) with explicit estimator/window metadata and fail-fast insufficient-history behavior.
  Notes:
  - Added `/api/portfolio/risk-estimators` route + typed service path (`PortfolioRiskEstimatorsResponse`) with v1 bounded windows (`30/90/252`), explicit methodology metadata, and unsupported-window `422` rejection.
  - Implemented baseline deterministic estimators (annualized volatility, max drawdown, beta) over aligned persisted history with explicit insufficient-history `409` failure path.
- [x] 2.4 Ensure analytics and risk endpoints remain read-only and do not trigger ledger rebuild or market-data mutation side effects.
  Notes:
  - Extended snapshot-consistency service tests to assert repeatable-read/read-only transaction setup and absence of mutating SQL statements for time-series, contribution, and risk-estimator flows.
  - Extended integration route tests to enforce forbidden side-effect boundaries (PDF extraction/normalization/persistence, ledger rebuild, market refresh mutation) across new workspace endpoints.
- [x] 2.5 Add/extend backend unit and integration tests for success, validation failure, and insufficiency scenarios.
  Notes:
  - Added integration coverage in `test_routes.py` for time-series/contribution/risk success paths plus explicit validation (`422` unsupported risk window) and insufficiency (`409`) failures.
  - Added unit coverage in `test_risk_preprocessing_kernels.py` for deterministic risk-kernel outputs and explicit preprocessing failure paths.
- [x] 2.6 Implement estimator math kernels using only approved quant stack modules (`numpy`, `pandas`, `scipy`) with deterministic output adaptation into contract-safe decimal fields.
  Notes:
  - Implemented risk-kernel computation over aligned price frames with `pandas`/`numpy` and SciPy regression validation, then normalized outputs into deterministic Decimal payloads before contract quantization.
  - Added `pandas-stubs` and `scipy-stubs` to dev dependencies to keep strict mypy/pyright gates green for quant-kernel code paths.
- [x] 2.7 Implement operations-first preprocessing guards in estimator services (sorted timezone-aware index checks, explicit missing-data handling, explicit frequency/calendar handling, deterministic event-time alignment where needed).
  Notes:
  - Added explicit preprocessing guards for UTC-aware sorted timestamps, deterministic aligned symbol coverage, and no implicit missing-data fills before estimator math.
  - Risk estimator path now fails fast with explicit client-facing errors when preprocessing invariants are violated.
- [x] 2.8 Implement baseline financial estimator kernels using approved pandas/NumPy/SciPy patterns (`pct_change`, `rolling/std`, `cummax` drawdown path, rolling `cov/var` beta, optional SciPy stats/optimize where estimator contract requires it).
  Notes:
  - Implemented estimator kernel flow in `app/portfolio_analytics/service.py` using `pct_change`, windowed `rolling(...).std`, `cummax` drawdown path, and rolling `cov/var` beta with SciPy `linregress` verification.
  - Kernel outputs are adapted through deterministic Decimal coercion before API contract serialization.
- [x] 2.9 Add estimator regression fixtures with tolerance-based assertions for default windows (`30/90/252`) and include non-convergence/invalid-domain failure-path tests for SciPy-backed routines.
  Notes:
  - Added regression fixtures with absolute tolerance checks for `30/90/252` windows in `app/portfolio_analytics/tests/test_risk_preprocessing_kernels.py`.
  - Added explicit SciPy failure-path coverage for invalid-domain regression exceptions and non-finite slope rejection.
- [x] 2.10 Implement backend validation and normalization for supported chart period enum values (`30D`, `90D`, `252D`, `MAX`) and reject unsupported periods explicitly.
  Notes:
  - Added `normalize_chart_period` in `app/portfolio_analytics/service.py` to normalize case/whitespace and enforce explicit `422` rejection for unsupported values.
  - Updated `time-series` and `contribution` routes to use explicit normalization path; added route and unit tests for unsupported period rejection and lowercase `max` normalization.

## 3. Frontend Workspace Architecture

- [x] 3.1 Add analytics workspace navigation and route composition for `Home`, `Analytics`, `Risk`, and `Transactions` while preserving existing summary/lot routes.
  Notes:
  - Added canonical workspace routes in `frontend/src/app/router.tsx`: `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/transactions` while keeping existing `/portfolio` summary and `/portfolio/:symbol` lot-detail routes unchanged.
  - Added concrete page modules/tests for each workspace route so route contracts are implementation-backed.
- [x] 3.2 Implement shared dashboard layout primitives and trust-context header elements (freshness/scope/provenance).
  Notes:
  - Added shared layout primitive `PortfolioWorkspaceLayout` in `frontend/src/components/workspace-layout/PortfolioWorkspaceLayout.tsx` with route-level navigation and trust-context header pills.
  - Trust context now surfaces explicit freshness/scope/provenance (plus optional period/frequency/timezone) per workspace route.
- [x] 3.3 Introduce typed frontend API clients/schemas/hooks for new analytics and risk endpoints.
  Notes:
  - Extended typed API schemas in `frontend/src/core/api/schemas.ts` for time-series, contribution, risk-estimators, and chart-period enum values.
  - Added typed clients in `frontend/src/features/portfolio-workspace/api.ts` and hooks in `frontend/src/features/portfolio-workspace/hooks.ts`.
- [x] 3.4 Implement explicit loading/empty/error/not-found states for each new workspace route.
  Notes:
  - Implemented Home/Analytics/Risk/Transactions route pages with explicit `isLoading`, empty-state, and error/not-found mappings (`ErrorBanner` + `EmptyState`) in `frontend/src/pages/portfolio-*-page/*`.
  - Added route-state tests per page validating loading/empty/error/not-found behavior.
- [x] 3.5 Implement frontend period selector/query constraints aligned to backend-supported enum values (`30D`, `90D`, `252D`, `MAX`) and prevent unsupported filter submissions.
  Notes:
  - Added constrained period utilities in `frontend/src/features/portfolio-workspace/period.ts` and period control UI in `PortfolioChartPeriodControl.tsx` with only supported enum values.
  - Routes normalize unsupported query-string period values before hook dispatch and never submit unsupported period values to backend chart endpoints.

## 4. Chart and UX Module Delivery

- [x] 4.1 Add `Recharts`-based chart foundation components and tokenized styling for trend, contribution, and risk visualizations.
  Notes:
  - Added `Recharts` dependency in frontend package manifests and introduced shared chart foundation components in `frontend/src/components/charts/` for trend, contribution, and risk visuals.
  - Added tokenized chart styling variables/classes in `frontend/src/app/styles.css` and chart foundation tests in `frontend/src/components/charts/PortfolioCharts.test.tsx`.
- [x] 4.2 Implement Home route KPI + trend modules with deterministic drill-down entry points.
  Notes:
  - Home route now renders KPI cards plus Recharts trend module from typed time-series payloads in `frontend/src/pages/portfolio-home-page/PortfolioHomePage.tsx`.
  - Added deterministic drill-down links to analytics/risk/transactions routes with period-preserving entry points.
- [x] 4.3 Implement Analytics route performance and contribution modules from server-provided payloads.
  Notes:
  - Analytics route now renders Recharts performance and contribution modules from backend responses plus supporting contribution list module.
  - Period selector remains backend-enum constrained and all modules read from typed API hooks.
- [x] 4.4 Implement Risk route estimator cards/charts with explicit unsupported/insufficient-data messaging.
  Notes:
  - Risk route now renders estimator cards alongside Recharts risk chart using backend metric payloads.
  - Added explicit unsupported/insufficient messaging mapping in risk error handling (`Risk scope unsupported`, `Risk data insufficient`).
- [x] 4.5 Implement Transactions route table/list view with deterministic sorting/filter behavior for ledger events only (no market-refresh diagnostics in v1).
  Notes:
  - Transactions route now uses deterministic sorting (`posted_at desc`, tie-break by `id`) and explicit symbol/type filters before rendering.
  - Implemented tabular ledger-event-only presentation (no market-refresh diagnostics surfaced) with route tests covering sort/filter behavior.

## 5. Quality Gates, Documentation, and Closeout

- [x] 5.1 Extend frontend tests for keyboard/navigation behavior and state mapping across new routes.
  Notes:
  - Added `frontend/src/components/workspace-layout/PortfolioWorkspaceLayout.test.tsx` covering active-link state mapping for all workspace routes and keyboard tab/enter navigation across workspace tabs.
  - Kept per-route loading/empty/error tests and workspace contract tests green (`analytics-workspace.contract` + page-level route-state suites).
- [x] 5.2 Capture accessibility and CWV evidence for portfolio + analytics workspace routes and record artifacts in docs.
  Notes:
  - Extended fixture/evidence scripts to include workspace endpoints/routes: `frontend/scripts/capture-frontend-evidence.mjs`, `frontend/scripts/measure-cwv.mjs`.
  - Captured fresh evidence artifacts for `2026-03-28`: accessibility, keyboard, screenshots, and CWV JSON/markdown under `docs/evidence/frontend/`.
- [x] 5.3 Update product/guides/standards references to reflect new workspace behavior, backend contract additions, estimator methodology metadata, and deferred boundaries.
  Notes:
  - Updated guides/standards/product docs for workspace IA, new backend contracts, period/window constraints, estimator methodology metadata, and transactions deferred boundary:
    - `docs/guides/frontend-api-and-ux-guide.md`
    - `docs/standards/frontend-standard.md`
    - `docs/product/frontend-ux-analytics-expansion-roadmap.md`
    - `docs/guides/frontend-delivery-checklist.md`
- [x] 5.4 Run validation gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`, targeted backend/frontend tests, OpenSpec validation) and record results in `CHANGELOG.md`.
  Notes:
  - Completed gates:
    - `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run black . --check --diff --workers 1`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app`
    - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_chart_period_validation.py app/portfolio_analytics/tests/test_risk_preprocessing_kernels.py app/portfolio_analytics/tests/test_quant_dependency_policy.py app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py`
    - `npm --prefix frontend run lint`
    - `npm --prefix frontend run test`
    - `npm --prefix frontend run build`
    - `OPENSPEC_TELEMETRY=0 openspec validate expand-frontend-ux-and-analytics-workspace --type change --strict --json`
    - `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json`
