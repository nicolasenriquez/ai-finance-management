# Portfolio ML Phase-I Guide

## Purpose

This guide documents the shipped phase-i `portfolio_ml` scope, including:

- included vs deferred methods
- read-only and non-advice posture
- offline training/evaluation command workflow
- promotion-policy interpretation for champion governance

## Included Methods (v1)

- Deterministic time-series signals:
  - trend slope
  - momentum
  - volatility regime
  - drawdown state
- CAPM signal metrics:
  - `beta`
  - `alpha`
  - `expected_return`
  - `market_premium`
- Baseline forecast family:
  - `naive`
  - `seasonal_naive`
  - `ewma_holt`
  - `arima_baseline`
  - `ridge_lag_regression`
- Governance/registry:
  - champion snapshot persistence
  - registry lineage retrieval
  - lifecycle filtering (`ready|unavailable|stale|error`)

## Deferred Methods (explicitly out of phase-i)

- LSTM / generic RNN
- Prophet
- customer segmentation
- execution or rebalancing workflows

Unsupported/deferred families are rejected with explicit `unsupported_model_policy`
semantics.

## Read-Only and Non-Advice Posture

- Endpoints are read-only:
  - `GET /api/portfolio/ml/signals`
  - `GET /api/portfolio/ml/forecasts`
  - `GET /api/portfolio/ml/registry`
- Copilot integration is read-only and allowlisted.
- Output is informational and not financial advice.
- No trade execution instructions or guaranteed-return claims are produced.

## Offline Training/Evaluation Workflow

Use the command workflow to run forecast evaluation and registry inspection from
the backend environment.

### 1) Run portfolio-scope offline forecast evaluation

```bash
uv run python scripts/portfolio_ml/run_offline_training_eval.py --scope portfolio
```

### 2) Run instrument-scope evaluation and inspect registry

```bash
uv run python scripts/portfolio_ml/run_offline_training_eval.py \
  --scope instrument_symbol \
  --instrument-symbol NVDA \
  --include-registry
```

### 3) Filter registry inspection by lifecycle state

```bash
uv run python scripts/portfolio_ml/run_offline_training_eval.py \
  --scope portfolio \
  --include-registry \
  --registry-lifecycle-state ready
```

### 4) Run focused policy tests before promotion decisions

```bash
uv run pytest -v app/portfolio_ml/tests/test_forecast_policy_gates_fail_first.py
uv run pytest -v app/portfolio_ml/tests/test_model_registry_contracts_fail_first.py
```

## Promotion Policy Interpretation

Frozen thresholds:

- `wmape_improvement_min_pct = 5.0`
- `max_horizon_regression_pct = 2.0`
- `prediction_interval_nominal = 0.80`
- `prediction_interval_coverage_floor = 0.72`
- `prediction_interval_coverage_ceiling = 0.88`
- `champion_ttl_hours = 168`

Interpretation:

- `qualified=true`: candidate can be promoted to champion.
- `baseline_improvement_failed`: candidate did not beat naive baseline enough.
- `horizon_regression_exceeded`: at least one horizon degraded beyond tolerance.
- `interval_calibration_failed`: interval coverage is out of accepted bounds.
- `champion_expired`: previously promoted champion exceeded TTL and is stale.

## Validation Commands

```bash
uv run ruff check app/portfolio_ml app/portfolio_ai_copilot
uv run mypy app/portfolio_ml app/portfolio_ai_copilot
uv run pyright app/portfolio_ml app/portfolio_ai_copilot
uv run ty check app
uv run pytest -v app/portfolio_ml/tests app/portfolio_ai_copilot/tests
```
