# Portfolio ML Technical Strategy Guide

## Purpose

This guide documents the deterministic technical strategy implemented in
`app/portfolio_ml/service.py` for `GET /api/portfolio/ml/signals`.

It translates the ETF notebook exploration into production-safe, read-only
signals that work with the current repository standards (typed contracts,
deterministic outputs, fail-fast behavior, and no execution advice).

## Data Contract and Scope

- Input contract: `series_points[]` with `captured_at` (ISO-8601 UTC) and
  `value` (close-like level).
- Normalization: UTC daily frequency (`1D`) via `normalize_time_index_series()`.
- External calls: none in signal generation path.
- Output contract: `PortfolioMLSignalResponse.signals[]` with stable `signal_id`,
  `label`, `unit`, `interpretation_band`, and `value`.

## Implemented Signal Set

Legacy v1 signals kept intact:

- `trend_30d`
- `momentum_90d`
- `volatility_regime`
- `drawdown_state`

Strategy extension signals:

- `daily_return_1d`
- `price_vs_sma_50`
- `sma_50_vs_200`
- `price_vs_ema_50`
- `ema_50_vs_200`
- `bollinger_percent_b_20d`
- `ichimoku_bias_proxy`
- `monthly_return_1m`
- `monthly_return_avg_3m`
- `trailing_return_12m`

## Formula Definitions

Let `P_t` be the latest normalized close-like level.

- `daily_return_1d = (P_t / P_{t-1}) - 1`
- `trend_30d`: slope from `np.polyfit` on trailing 30 points
- `momentum_90d = (P_t / P_{t-90_or_first}) - 1`
- `price_vs_sma_50 = (P_t / SMA_50_t) - 1`
- `sma_50_vs_200 = (SMA_50_t / SMA_200_t) - 1`
- `price_vs_ema_50 = (P_t / EMA_50_t) - 1`
- `ema_50_vs_200 = (EMA_50_t / EMA_200_t) - 1`
- `bollinger_percent_b_20d`:
  - `middle = rolling_mean_20`
  - `upper = middle + 1.96 * rolling_std_20`
  - `lower = middle - 1.96 * rolling_std_20`
  - `%B = (P_t - lower) / (upper - lower)`
- `ichimoku_bias_proxy` (close-only proxy):
  - conversion line from 9-period rolling max/min over close
  - baseline line from 26-period rolling max/min over close
  - leading spans A/B with 26-period shift
  - final bias = average of available components:
    - `(conversion / baseline) - 1`
    - `(price / cloud_midpoint) - 1`
- `monthly_return_1m`: month-end close return `(M_t / M_{t-1}) - 1`
- `monthly_return_avg_3m`: mean of trailing 3 month-over-month returns
- `trailing_return_12m = (P_t / P_{t-252_or_first}) - 1`

All values are quantized to `0.000001` precision for deterministic contract
stability.

## Interpretation Bands

Each signal emits one of:

- `favorable`
- `caution`
- `elevated_risk`

Band rules are deterministic and encoded in `service.py`:

- volatility/drawdown keep existing policy thresholds
- return and distance-type metrics use bounded absolute-magnitude thresholds
- trend-spread and Ichimoku proxy metrics use signed trend-bias thresholds
- Bollinger `%B` uses channel-position thresholds (`[0.2, 0.8]` favorable)

## DCA Strategy Usage (Read-Only)

Use these signals as context for pacing monthly DCA, not for trade automation.

- Favor baseline DCA when trend and regime signals remain favorable.
- Reduce increment size when stretch/volatility bands move to caution or elevated risk.
- Increase analytical review when multiple signals degrade together.

This module does not emit buy/sell orders and does not provide financial advice.

## Important Modeling Notes

- The original notebook cumulative-return bug (`cumprod(1 + price_level)`) is not
  used. Trailing return is computed from return ratios.
- Ichimoku is implemented as a close-only proxy because the current
  `series_points` contract does not include OHLC high/low fields.
- To move to canonical Ichimoku, extend the snapshot input contract with explicit
  daily `high` and `low` and keep deterministic tests for parity.

## Validation Commands

```bash
rtk uv run pytest -v app/portfolio_ml/tests/test_deterministic_signal_payload_fail_first.py
rtk uv run mypy app/portfolio_ml/service.py
rtk uv run pyright app/portfolio_ml/service.py
```
