## 1. Scope and Contract Baseline

- [ ] 1.1 Reconcile current portfolio analytics and frontend route contracts against new workspace/risk specs and record any conflicts before coding.
- [ ] 1.2 Add fail-first backend contract tests for time-series and contribution endpoints, including provenance and insufficiency rejection paths.
- [ ] 1.3 Add fail-first frontend contract tests for new workspace route state handling (`Home`, `Analytics`, `Risk`, `Transactions`) and explicit error/empty behavior.
- [ ] 1.4 Add a quant-stack decision record in project docs/OpenSpec artifacts with explicit accepted vs rejected package matrix and rationale.
- [ ] 1.5 Pin approved quant packages for estimator computation in `pyproject.toml` and `uv.lock`, and record upgrade policy (PR-scoped upgrade + fixture-diff review).
- [ ] 1.6 Add dependency guard coverage (check or test) that fails if rejected packages (`zipline`, `zipline-reloaded`, `pyfolio`, `pyrisk`, `mibian`, `backtrader`, `QuantLib-Python`) are introduced into runtime estimator dependencies.
- [ ] 1.7 Define and document v1 estimator methodology contract (default windows `30/90/252`, return basis semantics, annualization basis, and required metadata fields) before endpoint implementation.
- [ ] 1.8 Lock chart foundation decision to `Recharts` in docs/OpenSpec artifacts, including explicit re-evaluation criteria tied to route-level performance evidence.
- [ ] 1.9 Lock `Transactions` route v1 scope to ledger events only and record market-refresh diagnostics as deferred follow-up scope.

## 2. Backend Analytics and Risk Endpoints

- [ ] 2.1 Implement read-only portfolio time-series endpoint with deterministic ordering and explicit as-of metadata.
- [ ] 2.2 Implement contribution-by-symbol endpoint for supported periods from persisted truth.
- [ ] 2.3 Implement risk-estimator endpoint(s) with explicit estimator/window metadata and fail-fast insufficient-history behavior.
- [ ] 2.4 Ensure analytics and risk endpoints remain read-only and do not trigger ledger rebuild or market-data mutation side effects.
- [ ] 2.5 Add/extend backend unit and integration tests for success, validation failure, and insufficiency scenarios.
- [ ] 2.6 Implement estimator math kernels using only approved quant stack modules (`numpy`, `pandas`, `scipy`) with deterministic output adaptation into contract-safe decimal fields.
- [ ] 2.7 Implement operations-first preprocessing guards in estimator services (sorted timezone-aware index checks, explicit missing-data handling, explicit frequency/calendar handling, deterministic event-time alignment where needed).
- [ ] 2.8 Implement baseline financial estimator kernels using approved pandas/NumPy/SciPy patterns (`pct_change`, `rolling/std`, `cummax` drawdown path, rolling `cov/var` beta, optional SciPy stats/optimize where estimator contract requires it).
- [ ] 2.9 Add estimator regression fixtures with tolerance-based assertions for default windows (`30/90/252`) and include non-convergence/invalid-domain failure-path tests for SciPy-backed routines.
- [ ] 2.10 Implement backend validation and normalization for supported chart period enum values (`30D`, `90D`, `252D`, `MAX`) and reject unsupported periods explicitly.

## 3. Frontend Workspace Architecture

- [ ] 3.1 Add analytics workspace navigation and route composition for `Home`, `Analytics`, `Risk`, and `Transactions` while preserving existing summary/lot routes.
- [ ] 3.2 Implement shared dashboard layout primitives and trust-context header elements (freshness/scope/provenance).
- [ ] 3.3 Introduce typed frontend API clients/schemas/hooks for new analytics and risk endpoints.
- [ ] 3.4 Implement explicit loading/empty/error/not-found states for each new workspace route.
- [ ] 3.5 Implement frontend period selector/query constraints aligned to backend-supported enum values (`30D`, `90D`, `252D`, `MAX`) and prevent unsupported filter submissions.

## 4. Chart and UX Module Delivery

- [ ] 4.1 Add `Recharts`-based chart foundation components and tokenized styling for trend, contribution, and risk visualizations.
- [ ] 4.2 Implement Home route KPI + trend modules with deterministic drill-down entry points.
- [ ] 4.3 Implement Analytics route performance and contribution modules from server-provided payloads.
- [ ] 4.4 Implement Risk route estimator cards/charts with explicit unsupported/insufficient-data messaging.
- [ ] 4.5 Implement Transactions route table/list view with deterministic sorting/filter behavior for ledger events only (no market-refresh diagnostics in v1).

## 5. Quality Gates, Documentation, and Closeout

- [ ] 5.1 Extend frontend tests for keyboard/navigation behavior and state mapping across new routes.
- [ ] 5.2 Capture accessibility and CWV evidence for portfolio + analytics workspace routes and record artifacts in docs.
- [ ] 5.3 Update product/guides/standards references to reflect new workspace behavior, backend contract additions, estimator methodology metadata, and deferred boundaries.
- [ ] 5.4 Run validation gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`, targeted backend/frontend tests, OpenSpec validation) and record results in `CHANGELOG.md`.
