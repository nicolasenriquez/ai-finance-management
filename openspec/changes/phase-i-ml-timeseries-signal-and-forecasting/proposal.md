## Why

The ML and time-series references include many useful techniques, but the current repository does not yet have a production contract for deterministic signal generation or validated forecasting. We need a narrow, high-value phase that upgrades portfolio insight while preserving strict fail-fast, read-only, and non-advice boundaries.

## What Changes

- Add a deterministic time-series signal capability over existing ledger and market snapshots (trend, momentum, volatility regime, drawdown state, and data-freshness markers).
- Add explicit CAPM signal contracts for portfolio and instrument scopes (`beta`, `alpha`, `expected_return`, `market_premium`) with benchmark and risk-free provenance metadata.
- Add a baseline forecasting capability with walk-forward validation across a constrained model family (naive, seasonal-naive, EWMA/Holt, ARIMA, and ridge lag regression).
- Add champion-model promotion rules that require measurable improvement over naive baselines and return explicit `ready`, `unavailable`, `stale`, or `error` states.
- Add model-governance metadata contracts for provenance, feature hashes, training windows, horizon coverage, quality metrics, and expiry.
- Add read-only API contracts for signals, forecasts, and model-registry audit output for downstream analytics and future copilot grounding.
- Add one backend copilot-grounding bridge so `portfolio_ml` outputs are available through allowlisted read-only copilot tools, including typed evidence metadata.
- Add one governed SQL analytics tool contract for copilot that supports only allowlisted read-only query templates with strict parameter, row-budget, and timeout controls (no free-form SQL execution).
- Add one chat attachment-reference contract where copilot accepts validated `document_id` references from prior ingestion flows rather than raw file bytes in chat requests.
- Add optional prompt-suggestion metadata in copilot responses so frontend chips can guide high-value follow-up questions without changing read-only boundaries.
- Explicitly defer high-complexity reference techniques (LSTM/RNN, Prophet, customer segmentation, and any trade-execution or autonomous advice workflows).

## Capabilities

### New Capabilities
- `portfolio-timeseries-signals`: Deterministic signal extraction, CAPM metrics, and freshness/provenance semantics for portfolio and instrument scopes.
- `portfolio-forecasting-baselines`: Baseline forecast training, walk-forward evaluation, champion selection, and probabilistic forecast output.
- `portfolio-ml-model-governance`: Registry/audit contracts for model snapshots, promotion decisions, expiry handling, and allowed-model policy.

### Modified Capabilities
- `portfolio-ai-copilot`: Extend read-only copilot contract for `portfolio_ml` tool grounding, governed SQL template access, attachment references, and prompt-suggestion metadata.

## Impact

- Backend: new vertical slice under `app/portfolio_ml/` for schemas, services, routes, and tests; no direct SQL agent access and no mutation of ledger/canonical truth tables.
- Data contracts: new read-only endpoints for signal/CAPM/forecast/registry outputs; explicit stale or unavailable states instead of silent fallback.
- Copilot contracts: backend-only copilot integration updates for ML tool grounding, governed SQL template execution, document-reference attachments, and prompt-suggestion metadata.
- Dependencies: add conservative statistical/ML dependencies suitable for strict typed backend usage (`statsmodels`, `scikit-learn`) while excluding TensorFlow class dependencies in this phase.
- Operations: training/evaluation remains offline or command-triggered in v1 (no scheduler required), with deterministic run metadata persisted for audit.
- Security/governance: SQL access remains policy-bound and read-only through allowlisted templates, with explicit audit trail fields for every copilot SQL tool execution.
- Governance/docs: roadmap/backlog, model policy, and changelog updates required for rollout.
