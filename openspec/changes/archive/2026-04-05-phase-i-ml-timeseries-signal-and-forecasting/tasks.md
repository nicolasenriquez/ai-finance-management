## 1. Scope and Contract Freeze

- [x] 1.1 Audit ML/time-series references and freeze included versus deferred methods for v1.
  Notes:
  - Include deterministic signal extraction plus CAPM signal contract and baseline forecasting family (naive, seasonal-naive, EWMA or Holt, ARIMA, ridge lag-regression).
  - Defer LSTM or generic RNN, Prophet, customer segmentation, and execution workflows.
- [x] 1.2 Freeze promotion policy thresholds (baseline improvement and interval calibration requirements).
  Notes:
  - Frozen thresholds are now explicit in proposal/design/spec artifacts: `wMAPE >= 5.0%` improvement, `<= 2.0%` max horizon regression, 80% interval coverage in `[0.72, 0.88]`, champion expiry `168` hours.
- [x] 1.3 Freeze API contracts for signals, CAPM metrics, forecasts, and registry with explicit `ready|unavailable|stale|error` state semantics.
  Notes:
  - Shared lifecycle envelope (`state`, reason code/detail, as-of/evaluated timestamps, freshness policy) and route paths are frozen in change artifacts before implementation.

## 2. Fail-First Data and Feature Tests

- [x] 2.1 Add fail-first unit tests for time-index normalization, resampling, and missing-point handling.
  Notes:
  - Added `app/portfolio_ml/tests/test_time_index_preprocessing_fail_first.py`.
- [x] 2.2 Add fail-first tests proving deterministic signal outputs for equivalent snapshot inputs.
  Notes:
  - Added `app/portfolio_ml/tests/test_deterministic_signal_payload_fail_first.py`.
- [x] 2.3 Add fail-first tests for freshness policy (`stale`) and insufficient-history (`unavailable`) behavior.
  Notes:
  - Added `app/portfolio_ml/tests/test_signal_lifecycle_policy_fail_first.py`.
- [x] 2.4 Add fail-first integration tests for portfolio and instrument scope signal contracts.
  Notes:
  - Added `app/portfolio_ml/tests/test_signal_endpoint_contracts_fail_first.py`.
- [x] 2.5 Add fail-first tests for CAPM metric computation and missing benchmark/risk-free input rejection.
  Notes:
  - Added `app/portfolio_ml/tests/test_capm_signal_metrics_fail_first.py`.

## 3. Time-Series Signal Implementation

- [x] 3.1 Create backend `portfolio_ml` vertical slice structure with typed schemas, services, routes, and tests.
  Notes:
  - Added `app/portfolio_ml/{schemas.py,service.py,routes.py}` and wired router in `app/main.py`.
- [x] 3.2 Implement deterministic signal builder service over approved read-only portfolio and market snapshots.
  Notes:
  - Added `build_deterministic_signal_payload` and `normalize_time_index_series` in `app/portfolio_ml/service.py`.
- [x] 3.3 Implement CAPM signal computation module (`beta`, `alpha`, `expected_return`, `market_premium`) with benchmark/risk-free provenance.
  Notes:
  - Added `compute_capm_signal_metrics` with explicit missing benchmark/risk-free rejection semantics.
- [x] 3.4 Implement provenance and freshness resolver producing explicit lifecycle states.
  Notes:
  - Added `resolve_signal_lifecycle_state` returning `ready|unavailable|stale` with reason code/detail metadata.
- [x] 3.5 Implement read-only signal endpoint contract for portfolio and instrument scopes.
  Notes:
  - Added `GET /api/portfolio/ml/signals` with scope validation and typed response normalization.
- [x] 3.6 Add structured logging taxonomy for signal generation start, success, stale, unavailable, and failure outcomes.
  Notes:
  - Added portfolio ML request/service logs including `portfolio_ml.signal_generation_started|completed|stale|unavailable|failed`.

## 4. Baseline Forecasting Engine

- [x] 4.1 Add fail-first tests for walk-forward split correctness and temporal leakage rejection.
  Notes:
  - Added `app/portfolio_ml/tests/test_walk_forward_policy_fail_first.py` with split-boundary and leakage-rejection assertions.
- [x] 4.2 Implement baseline candidate models and shared feature pipeline.
  Notes:
  - Candidate family MUST match frozen policy list from task 1.1.
  - Implemented `run_baseline_candidate_forecasts` + `build_shared_lag_feature_matrix` for `naive`, `seasonal_naive`, `ewma_holt`, `arima_baseline`, `ridge_lag_regression`.
- [x] 4.3 Implement evaluation metrics and naive-baseline comparison logic.
  Notes:
  - Added `evaluate_forecast_promotion_policy` and forecasting policy tests in `app/portfolio_ml/tests/test_forecast_policy_gates_fail_first.py`.
- [x] 4.4 Implement champion promotion and expiry handling policy.
  Notes:
  - Added `select_champion_forecast_snapshot` and `resolve_forecast_lifecycle_state` with 168-hour expiry semantics.
- [x] 4.5 Implement read-only probabilistic forecast endpoint with horizon-level interval metadata.
  Notes:
  - Added `GET /api/portfolio/ml/forecasts` plus typed forecast schemas and endpoint contract tests in `app/portfolio_ml/tests/test_forecast_endpoint_contracts_fail_first.py`.

## 5. Model Governance and Registry

- [x] 5.1 Add persistence schema/migration for model snapshot metadata and lifecycle fields.
  Notes:
  - Added `app/portfolio_ml/models.py` with `PortfolioMLModelSnapshot` including lifecycle, provenance, metrics, and audit metadata fields.
  - Added Alembic migration `alembic/versions/e1a9c4d2b6f1_add_portfolio_ml_model_registry_snapshot_.py`.
  - Updated `alembic/env.py` model imports for migration autoload.
- [x] 5.2 Implement registry service for snapshot lineage, promotion history, and filtering.
  Notes:
  - Added snapshot persistence/upsert path (`_upsert_model_snapshot`) and typed registry query service (`get_portfolio_ml_registry_response`) in `app/portfolio_ml/service.py`.
  - Added filter support for `scope`, `model_family`, and `lifecycle_state`.
- [x] 5.3 Implement explicit unsupported-model rejection path for deferred families (LSTM/RNN/Prophet/segmentation).
  Notes:
  - Added `enforce_supported_model_policy` with explicit `unsupported_model_policy` rejection semantics for deferred/disallowed families.
  - Added fail-first coverage in `app/portfolio_ml/tests/test_unsupported_model_policy_fail_first.py`.
- [x] 5.4 Implement read-only registry audit endpoint contract.
  Notes:
  - Added `GET /api/portfolio/ml/registry` in `app/portfolio_ml/routes.py` with typed response and query filters.
  - Added endpoint contract coverage in `app/portfolio_ml/tests/test_model_registry_contracts_fail_first.py`.

## 6. Documentation and Validation

- [x] 6.1 Update product/docs artifacts with included methods, deferred methods, and non-advice posture.
  Notes:
  - Added phase-i portfolio ML method policy and non-advice posture updates in `docs/product/roadmap.md`.
  - Updated copilot operations guide with phase-i ML extension policy in `docs/guides/portfolio-ai-copilot-guide.md`.
- [x] 6.2 Add implementation guide for offline training/evaluation command workflow and promotion policy interpretation.
  Notes:
  - Added `docs/guides/portfolio-ml-phase-i-guide.md` with included/deferred methods, command workflow, and promotion-policy interpretation.
  - Added offline workflow command script `scripts/portfolio_ml/run_offline_training_eval.py`.
  - Updated docs navigation in `docs/README.md`.
- [x] 6.3 Add `CHANGELOG.md` entry with delivered scope and metric-validation evidence.
- [x] 6.4 Run backend validation gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`) and targeted `portfolio_ml` plus affected `portfolio_analytics` tests.
  Notes:
  - Passed: `rtk uv run ruff check .`
  - Passed: `rtk uv run black . --check --diff`
  - Passed: `rtk uv run mypy app/`
  - Passed: `rtk uv run pyright app/`
  - Passed: `rtk uv run ty check app`
  - Passed: `rtk env ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -v app/portfolio_ml/tests app/portfolio_ai_copilot/tests app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py`
- [x] 6.5 Run OpenSpec change/spec validations and prepare implementation handoff.
  Notes:
  - Passed: `rtk openspec validate --changes "phase-i-ml-timeseries-signal-and-forecasting" --strict`
  - Passed: `rtk openspec validate --specs --all`

## 7. Copilot Grounding Bridge and Guarded Query Contracts

- [x] 7.1 Add fail-first backend tests for copilot contract extensions covering `portfolio_ml` tool evidence, `document_id` attachment references, and prompt-suggestion metadata.
  Notes:
  - Added `app/portfolio_ai_copilot/tests/test_ml_contract_extensions_fail_first.py`.
- [x] 7.2 Implement allowlisted copilot tools that expose phase-i signal, CAPM, forecast, and model-governance outputs without bypassing approved read-only contracts.
  Notes:
  - Extended copilot allowlisted tool registry with `portfolio_ml_signals`, `portfolio_ml_capm`, `portfolio_ml_forecasts`, and `portfolio_ml_registry`.
  - Added tool selection keyword mapping and typed tool adapters in `app/portfolio_ai_copilot/service.py`.
- [x] 7.3 Add fail-first tests for governed SQL template execution (template allowlist, parameter schema validation, max rows, timeout handling, and explicit rejection semantics).
  Notes:
  - Added `app/portfolio_ai_copilot/tests/test_governed_sql_template_policy_fail_first.py`.
- [x] 7.4 Implement one governed read-only SQL tool path for copilot based on template IDs and auditable execution metadata; prohibit free-form SQL input.
  Notes:
  - Added `execute_governed_sql_template` allowlisted workflow with parameter schema validation, bounded row limits, timeout, and audit metadata.
  - Added `portfolio_sql_template` tool adapter path in `app/portfolio_ai_copilot/service.py`.
- [x] 7.5 Implement chat request validation for bounded document references (`document_id` list) backed by existing ingestion records; reject unresolved references explicitly.
  Notes:
  - Extended request contract with bounded `document_ids` in `app/portfolio_ai_copilot/schemas.py`.
  - Added persisted-reference validation and prompt-context assembly in `app/portfolio_ai_copilot/service.py`.
- [x] 7.6 Extend copilot response schema and service output with optional prompt suggestions derived from active route/scope/tool context and lifecycle state.
  Notes:
  - Extended response contract with `prompt_suggestions` in `app/portfolio_ai_copilot/schemas.py`.
  - Added suggestion generation and safe fallback path in `app/portfolio_ai_copilot/service.py`.
