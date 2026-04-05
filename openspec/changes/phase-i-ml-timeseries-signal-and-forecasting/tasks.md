## 1. Scope and Contract Freeze

- [ ] 1.1 Audit ML/time-series references and freeze included versus deferred methods for v1.
  Notes:
  - Include deterministic signal extraction plus CAPM signal contract and baseline forecasting family (naive, seasonal-naive, EWMA or Holt, ARIMA, ridge lag-regression).
  - Defer LSTM or generic RNN, Prophet, customer segmentation, and execution workflows.
- [ ] 1.2 Freeze promotion policy thresholds (baseline improvement and interval calibration requirements).
- [ ] 1.3 Freeze API contracts for signals, CAPM metrics, forecasts, and registry with explicit `ready|unavailable|stale|error` state semantics.

## 2. Fail-First Data and Feature Tests

- [ ] 2.1 Add fail-first unit tests for time-index normalization, resampling, and missing-point handling.
- [ ] 2.2 Add fail-first tests proving deterministic signal outputs for equivalent snapshot inputs.
- [ ] 2.3 Add fail-first tests for freshness policy (`stale`) and insufficient-history (`unavailable`) behavior.
- [ ] 2.4 Add fail-first integration tests for portfolio and instrument scope signal contracts.
- [ ] 2.5 Add fail-first tests for CAPM metric computation and missing benchmark/risk-free input rejection.

## 3. Time-Series Signal Implementation

- [ ] 3.1 Create backend `portfolio_ml` vertical slice structure with typed schemas, services, routes, and tests.
- [ ] 3.2 Implement deterministic signal builder service over approved read-only portfolio and market snapshots.
- [ ] 3.3 Implement CAPM signal computation module (`beta`, `alpha`, `expected_return`, `market_premium`) with benchmark/risk-free provenance.
- [ ] 3.4 Implement provenance and freshness resolver producing explicit lifecycle states.
- [ ] 3.5 Implement read-only signal endpoint contract for portfolio and instrument scopes.
- [ ] 3.6 Add structured logging taxonomy for signal generation start, success, stale, unavailable, and failure outcomes.

## 4. Baseline Forecasting Engine

- [ ] 4.1 Add fail-first tests for walk-forward split correctness and temporal leakage rejection.
- [ ] 4.2 Implement baseline candidate models and shared feature pipeline.
  Notes:
  - Candidate family MUST match frozen policy list from task 1.1.
- [ ] 4.3 Implement evaluation metrics and naive-baseline comparison logic.
- [ ] 4.4 Implement champion promotion and expiry handling policy.
- [ ] 4.5 Implement read-only probabilistic forecast endpoint with horizon-level interval metadata.

## 5. Model Governance and Registry

- [ ] 5.1 Add persistence schema/migration for model snapshot metadata and lifecycle fields.
- [ ] 5.2 Implement registry service for snapshot lineage, promotion history, and filtering.
- [ ] 5.3 Implement explicit unsupported-model rejection path for deferred families (LSTM/RNN/Prophet/segmentation).
- [ ] 5.4 Implement read-only registry audit endpoint contract.

## 6. Documentation and Validation

- [ ] 6.1 Update product/docs artifacts with included methods, deferred methods, and non-advice posture.
- [ ] 6.2 Add implementation guide for offline training/evaluation command workflow and promotion policy interpretation.
- [ ] 6.3 Add `CHANGELOG.md` entry with delivered scope and metric-validation evidence.
- [ ] 6.4 Run backend validation gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`) and targeted `portfolio_ml` plus affected `portfolio_analytics` tests.
- [ ] 6.5 Run OpenSpec change/spec validations and prepare implementation handoff.

## 7. Copilot Grounding Bridge and Guarded Query Contracts

- [ ] 7.1 Add fail-first backend tests for copilot contract extensions covering `portfolio_ml` tool evidence, `document_id` attachment references, and prompt-suggestion metadata.
- [ ] 7.2 Implement allowlisted copilot tools that expose phase-i signal, CAPM, forecast, and model-governance outputs without bypassing approved read-only contracts.
- [ ] 7.3 Add fail-first tests for governed SQL template execution (template allowlist, parameter schema validation, max rows, timeout handling, and explicit rejection semantics).
- [ ] 7.4 Implement one governed read-only SQL tool path for copilot based on template IDs and auditable execution metadata; prohibit free-form SQL input.
- [ ] 7.5 Implement chat request validation for bounded document references (`document_id` list) backed by existing ingestion records; reject unresolved references explicitly.
- [ ] 7.6 Extend copilot response schema and service output with optional prompt suggestions derived from active route/scope/tool context and lifecycle state.
