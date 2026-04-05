"""Service helpers for read-only portfolio ML signal contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Final, cast

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.portfolio_ml.models import PortfolioMLModelSnapshot
from app.portfolio_ml.schemas import (
    PortfolioMLCapmMetrics,
    PortfolioMLForecastHorizonRow,
    PortfolioMLForecastResponse,
    PortfolioMLFreshnessPolicy,
    PortfolioMLRegistryResponse,
    PortfolioMLRegistryRow,
    PortfolioMLScope,
    PortfolioMLSignalResponse,
    PortfolioMLSignalRow,
    PortfolioMLState,
)
from app.shared.models import utcnow

logger = get_logger(__name__)

_SIGNAL_VALUE_SCALE: Final[Decimal] = Decimal("0.000001")
_CAPM_VALUE_SCALE: Final[Decimal] = Decimal("0.000001")
_FORECAST_VALUE_SCALE: Final[Decimal] = Decimal("0.01")
_DEFAULT_FRESHNESS_HOURS: Final[int] = 24
_TRADING_DAYS_ANNUALIZATION: Final[int] = 252
_FORECAST_HORIZON_COUNT: Final[int] = 3
_FORECAST_CONFIDENCE_LEVEL: Final[Decimal] = Decimal("0.80")
_PROMOTION_IMPROVEMENT_MIN_PCT: Final[float] = 5.0
_MAX_HORIZON_REGRESSION_PCT: Final[float] = 2.0
_COVERAGE_FLOOR: Final[float] = 0.72
_COVERAGE_CEILING: Final[float] = 0.88
_CHAMPION_TTL_HOURS: Final[int] = 168
_DEFAULT_RIDGE_LAG_COUNT: Final[int] = 5
_SUPPORTED_FORECAST_MODEL_FAMILIES: Final[frozenset[str]] = frozenset(
    {"naive", "seasonal_naive", "ewma_holt", "arima_baseline", "ridge_lag_regression"}
)
_DEFERRED_MODEL_FAMILIES: Final[frozenset[str]] = frozenset(
    {"lstm", "rnn", "prophet", "segmentation", "customer_segmentation"}
)

_FORECAST_CHAMPION_BY_SCOPE: dict[tuple[str, str], dict[str, object]] = {}


class PortfolioMLClientError(ValueError):
    """Raised when portfolio_ml requests are invalid or unsafe to process."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize one client-facing portfolio ML error."""

        super().__init__(message)
        self.status_code = status_code


def _normalize_model_family_token(*, model_family: str) -> str:
    """Normalize one model-family token to canonical snake_case value."""

    normalized = model_family.strip().lower().replace("-", "_")
    if normalized == "arima":
        return "arima_baseline"
    if normalized in {"ewma", "holt", "holt_family"}:
        return "ewma_holt"
    if normalized in {"ridge", "ridge_lag"}:
        return "ridge_lag_regression"
    return normalized


def enforce_supported_model_policy(*, model_family: str) -> str:
    """Reject deferred or unsupported model families with explicit policy semantics."""

    normalized = _normalize_model_family_token(model_family=model_family)
    if normalized in _DEFERRED_MODEL_FAMILIES:
        raise PortfolioMLClientError(
            "unsupported_model_policy: model family " f"'{model_family}' is deferred for v1.",
            status_code=422,
        )
    if normalized not in _SUPPORTED_FORECAST_MODEL_FAMILIES:
        raise PortfolioMLClientError(
            "unsupported_model_policy: model family "
            f"'{model_family}' is not allowlisted for v1.",
            status_code=422,
        )
    return normalized


def _coerce_json_mapping(value: object) -> dict[str, object]:
    """Normalize one JSON-like mapping value into a string-keyed dictionary."""

    if not isinstance(value, Mapping):
        return {}
    mapping_value = cast(Mapping[object, object], value)
    normalized: dict[str, object] = {}
    for key, item in mapping_value.items():
        normalized[str(key)] = item
    return normalized


def _parse_decimal(value: object, *, field_name: str) -> Decimal:
    """Parse one numeric value into Decimal with explicit error semantics."""

    if isinstance(value, Decimal):
        return value

    if isinstance(value, int | float):
        return Decimal(str(value))

    if isinstance(value, str):
        normalized = value.strip()
        if normalized == "":
            raise PortfolioMLClientError(
                f"Field '{field_name}' must not be empty.",
                status_code=422,
            )
        try:
            return Decimal(normalized)
        except InvalidOperation as exc:
            raise PortfolioMLClientError(
                f"Field '{field_name}' must be numeric.",
                status_code=422,
            ) from exc

    raise PortfolioMLClientError(
        f"Field '{field_name}' must be numeric.",
        status_code=422,
    )


def _to_utc_datetime(value: object, *, field_name: str) -> datetime:
    """Convert one timestamp-like object to timezone-aware UTC datetime."""

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    if isinstance(value, str):
        normalized = value.strip()
        if normalized == "":
            raise PortfolioMLClientError(
                f"Field '{field_name}' must not be empty.",
                status_code=422,
            )
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise PortfolioMLClientError(
                f"Field '{field_name}' must be an ISO-8601 timestamp.",
                status_code=422,
            ) from exc
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    raise PortfolioMLClientError(
        f"Field '{field_name}' must be a timestamp.",
        status_code=422,
    )


def _quantize_decimal(value: Decimal, *, scale: Decimal) -> Decimal:
    """Quantize one Decimal to deterministic scale."""

    return value.quantize(scale)


def normalize_time_index_series(
    *,
    raw_points: Sequence[Mapping[str, object]],
    frequency: str,
    timezone: str,
) -> pd.Series:
    """Normalize one point series into deterministic UTC-indexed frequency-aligned data."""

    if frequency.strip() == "":
        raise PortfolioMLClientError("Frequency must not be empty.", status_code=422)

    if timezone.upper() != "UTC":
        raise PortfolioMLClientError(
            "Only UTC timezone is supported for deterministic signal normalization.",
            status_code=422,
        )

    indexed_points: list[tuple[datetime, float]] = []
    for point in raw_points:
        captured_at = _to_utc_datetime(point.get("captured_at"), field_name="captured_at")
        value_decimal = _parse_decimal(point.get("value"), field_name="value")
        indexed_points.append((captured_at, float(value_decimal)))

    if len(indexed_points) == 0:
        raise PortfolioMLClientError(
            "At least one series point is required.",
            status_code=409,
        )

    indexed_points.sort(key=lambda item: item[0])
    index = pd.DatetimeIndex([item[0] for item in indexed_points])

    if index.has_duplicates:
        raise PortfolioMLClientError(
            "Duplicate captured_at timestamps are not allowed.",
            status_code=409,
        )

    series = pd.Series(
        [item[1] for item in indexed_points],
        index=index,
        dtype="float64",
    )
    normalized = series.asfreq(frequency)
    return normalized


def _calculate_trend(series: pd.Series) -> Decimal:
    """Compute one deterministic trend slope signal over the trailing 30 points."""

    cleaned = series.dropna()
    if len(cleaned) < 2:
        return Decimal("0")

    trailing = cleaned.iloc[-min(len(cleaned), 30) :]
    x_axis = np.arange(len(trailing), dtype="float64")
    y_axis = trailing.to_numpy(dtype="float64")
    slope = float(np.polyfit(x_axis, y_axis, deg=1)[0])
    return _quantize_decimal(Decimal(str(slope)), scale=_SIGNAL_VALUE_SCALE)


def _calculate_momentum(series: pd.Series) -> Decimal:
    """Compute one deterministic trailing momentum ratio over up to 90 points."""

    cleaned = series.dropna()
    if len(cleaned) < 2:
        return Decimal("0")

    trailing = cleaned.iloc[-min(len(cleaned), 90) :]
    start_value = float(trailing.iloc[0])
    end_value = float(trailing.iloc[-1])
    if math.isclose(start_value, 0.0):
        return Decimal("0")

    momentum_ratio = (end_value / start_value) - 1.0
    return _quantize_decimal(Decimal(str(momentum_ratio)), scale=_SIGNAL_VALUE_SCALE)


def _calculate_volatility_regime(series: pd.Series) -> Decimal:
    """Compute one annualized realized-volatility ratio from normalized returns."""

    cleaned = series.dropna()
    if len(cleaned) < 3:
        return Decimal("0")

    returns = cleaned.pct_change().dropna()
    if len(returns) < 2:
        return Decimal("0")

    volatility = float(returns.std(ddof=1) * math.sqrt(_TRADING_DAYS_ANNUALIZATION))
    return _quantize_decimal(Decimal(str(volatility)), scale=_SIGNAL_VALUE_SCALE)


def _calculate_drawdown_state(series: pd.Series) -> Decimal:
    """Compute one latest drawdown ratio from trailing cumulative max."""

    cleaned = series.dropna()
    if len(cleaned) == 0:
        return Decimal("0")

    cumulative_max = cleaned.cummax()
    latest_value = float(cleaned.iloc[-1])
    latest_peak = float(cumulative_max.iloc[-1])
    if math.isclose(latest_peak, 0.0):
        return Decimal("0")

    drawdown_ratio = (latest_value / latest_peak) - 1.0
    return _quantize_decimal(Decimal(str(drawdown_ratio)), scale=_SIGNAL_VALUE_SCALE)


def _volatility_band(volatility: Decimal) -> str:
    """Map one volatility value to deterministic interpretation band."""

    if volatility < Decimal("0.15"):
        return "favorable"
    if volatility < Decimal("0.30"):
        return "caution"
    return "elevated_risk"


def _drawdown_band(drawdown: Decimal) -> str:
    """Map one drawdown value to deterministic interpretation band."""

    if drawdown > Decimal("-0.05"):
        return "favorable"
    if drawdown > Decimal("-0.15"):
        return "caution"
    return "elevated_risk"


def build_deterministic_signal_payload(
    *,
    snapshot_input: Mapping[str, object],
) -> Mapping[str, object]:
    """Build deterministic signal rows from one normalized snapshot input mapping."""

    raw_points_value_obj = snapshot_input.get("series_points")
    if not isinstance(raw_points_value_obj, list):
        raise PortfolioMLClientError(
            "Snapshot input must include a 'series_points' list.",
            status_code=422,
        )
    raw_points_value = cast(list[object], raw_points_value_obj)
    raw_points: list[Mapping[str, object]] = []
    for row in raw_points_value:
        if not isinstance(row, Mapping):
            raise PortfolioMLClientError(
                "Each series point must be a mapping.",
                status_code=422,
            )
        raw_points.append(cast(Mapping[str, object], row))

    normalized_series = normalize_time_index_series(
        raw_points=raw_points,
        frequency="1D",
        timezone="UTC",
    )

    trend_value = _calculate_trend(normalized_series)
    momentum_value = _calculate_momentum(normalized_series)
    volatility_value = _calculate_volatility_regime(normalized_series)
    drawdown_value = _calculate_drawdown_state(normalized_series)

    scope_value = snapshot_input.get("scope")
    scope = scope_value if isinstance(scope_value, str) else PortfolioMLScope.PORTFOLIO.value

    signal_rows: list[dict[str, object]] = [
        {
            "signal_id": "trend_30d",
            "label": "Trend (30D)",
            "unit": "slope_per_day",
            "interpretation_band": "favorable" if trend_value >= Decimal("0") else "caution",
            "value": trend_value,
        },
        {
            "signal_id": "momentum_90d",
            "label": "Momentum (90D)",
            "unit": "ratio",
            "interpretation_band": "favorable" if momentum_value >= Decimal("0") else "caution",
            "value": momentum_value,
        },
        {
            "signal_id": "volatility_regime",
            "label": "Volatility Regime",
            "unit": "annualized_ratio",
            "interpretation_band": _volatility_band(volatility_value),
            "value": volatility_value,
        },
        {
            "signal_id": "drawdown_state",
            "label": "Drawdown State",
            "unit": "ratio",
            "interpretation_band": _drawdown_band(drawdown_value),
            "value": drawdown_value,
        },
    ]

    return {
        "scope": scope,
        "instrument_symbol": snapshot_input.get("instrument_symbol"),
        "signals": signal_rows,
    }


def resolve_signal_lifecycle_state(
    *,
    as_of_ledger_at: str | datetime,
    as_of_market_at: str | datetime,
    evaluated_at: str | datetime,
    freshness_policy_hours: int,
    missing_history_windows: Sequence[str],
) -> Mapping[str, object]:
    """Resolve lifecycle state for one signal response from freshness/history policy."""

    ledger_at = _to_utc_datetime(as_of_ledger_at, field_name="as_of_ledger_at")
    market_at = _to_utc_datetime(as_of_market_at, field_name="as_of_market_at")
    evaluated = _to_utc_datetime(evaluated_at, field_name="evaluated_at")

    if freshness_policy_hours <= 0:
        raise PortfolioMLClientError(
            "Freshness policy hours must be positive.",
            status_code=422,
        )

    if len(missing_history_windows) > 0:
        missing_window_labels = ", ".join(sorted(set(missing_history_windows)))
        return {
            "state": PortfolioMLState.UNAVAILABLE.value,
            "state_reason_code": "insufficient_history",
            "state_reason_detail": (
                "Missing required history windows for deterministic signal generation: "
                f"{missing_window_labels}."
            ),
        }

    oldest_source_timestamp = ledger_at if ledger_at <= market_at else market_at
    age_hours = (evaluated - oldest_source_timestamp).total_seconds() / 3600
    if age_hours > freshness_policy_hours:
        return {
            "state": PortfolioMLState.STALE.value,
            "state_reason_code": "source_data_stale",
            "state_reason_detail": ("Source snapshot age exceeds freshness policy threshold."),
        }

    return {
        "state": PortfolioMLState.READY.value,
        "state_reason_code": "ready",
        "state_reason_detail": "signals_ready",
    }


def compute_capm_signal_metrics(
    *,
    portfolio_returns: Sequence[float | int | Decimal],
    benchmark_returns: Sequence[float | int | Decimal],
    risk_free_rate_annual: float | int | Decimal | None,
    benchmark_symbol: str | None,
    risk_free_source: str | None,
    annualization_factor: int,
) -> Mapping[str, object]:
    """Compute deterministic CAPM metrics with explicit benchmark/risk-free provenance."""

    if len(benchmark_returns) == 0:
        raise PortfolioMLClientError(
            "CAPM requires benchmark return history.",
            status_code=409,
        )
    if len(portfolio_returns) == 0:
        raise PortfolioMLClientError(
            "CAPM requires portfolio return history.",
            status_code=409,
        )
    if len(portfolio_returns) != len(benchmark_returns):
        raise PortfolioMLClientError(
            "Portfolio and benchmark return histories must have equal length.",
            status_code=409,
        )
    if len(portfolio_returns) < 2:
        raise PortfolioMLClientError(
            "CAPM requires at least two aligned return observations.",
            status_code=409,
        )
    if annualization_factor <= 0:
        raise PortfolioMLClientError(
            "Annualization factor must be positive.",
            status_code=422,
        )
    if risk_free_rate_annual is None:
        raise PortfolioMLClientError(
            "CAPM requires risk-free input.",
            status_code=409,
        )
    if risk_free_source is None or risk_free_source.strip() == "":
        raise PortfolioMLClientError(
            "CAPM requires risk-free source provenance.",
            status_code=409,
        )
    if benchmark_symbol is None or benchmark_symbol.strip() == "":
        raise PortfolioMLClientError(
            "CAPM requires benchmark symbol provenance.",
            status_code=409,
        )

    portfolio_array = np.asarray([float(item) for item in portfolio_returns], dtype="float64")
    benchmark_array = np.asarray([float(item) for item in benchmark_returns], dtype="float64")
    risk_free_annual = float(
        _parse_decimal(risk_free_rate_annual, field_name="risk_free_rate_annual")
    )
    risk_free_per_period = risk_free_annual / annualization_factor

    benchmark_variance = float(np.var(benchmark_array, ddof=1))
    if math.isclose(benchmark_variance, 0.0):
        raise PortfolioMLClientError(
            "CAPM benchmark variance is zero.",
            status_code=409,
        )

    covariance_matrix = np.cov(portfolio_array, benchmark_array, ddof=1)
    covariance = float(covariance_matrix[0, 1])
    beta = covariance / benchmark_variance

    portfolio_excess_mean = float(np.mean(portfolio_array - risk_free_per_period))
    benchmark_excess_mean = float(np.mean(benchmark_array - risk_free_per_period))
    alpha_annual = (portfolio_excess_mean - (beta * benchmark_excess_mean)) * annualization_factor
    market_premium = benchmark_excess_mean * annualization_factor
    expected_return = risk_free_annual + (beta * market_premium)

    return {
        "beta": _quantize_decimal(Decimal(str(beta)), scale=_CAPM_VALUE_SCALE),
        "alpha": _quantize_decimal(Decimal(str(alpha_annual)), scale=_CAPM_VALUE_SCALE),
        "expected_return": _quantize_decimal(
            Decimal(str(expected_return)),
            scale=_CAPM_VALUE_SCALE,
        ),
        "market_premium": _quantize_decimal(
            Decimal(str(market_premium)),
            scale=_CAPM_VALUE_SCALE,
        ),
        "benchmark_symbol": benchmark_symbol.strip().upper(),
        "risk_free_source": risk_free_source.strip(),
        "annualization_factor": annualization_factor,
    }


def _default_snapshot_points(*, evaluated_at: datetime) -> list[dict[str, object]]:
    """Build one deterministic synthetic daily series for v1 signal endpoint fallback."""

    day_3 = evaluated_at - timedelta(days=3)
    day_2 = evaluated_at - timedelta(days=2)
    day_1 = evaluated_at - timedelta(days=1)
    day_0 = evaluated_at
    return [
        {"captured_at": day_3.isoformat(), "value": "100.0"},
        {"captured_at": day_2.isoformat(), "value": "101.2"},
        {"captured_at": day_1.isoformat(), "value": "100.9"},
        {"captured_at": day_0.isoformat(), "value": "102.1"},
    ]


async def get_portfolio_ml_signal_response(
    *,
    scope: PortfolioMLScope,
    instrument_symbol: str | None = None,
) -> PortfolioMLSignalResponse:
    """Return one read-only portfolio_ml signal response for selected scope."""

    normalized_symbol = instrument_symbol.strip().upper() if instrument_symbol is not None else None
    if normalized_symbol == "":
        normalized_symbol = None
    logger.info(
        "portfolio_ml.signal_generation_started",
        scope=scope.value,
        instrument_symbol=normalized_symbol,
    )

    try:
        if scope is PortfolioMLScope.INSTRUMENT_SYMBOL and normalized_symbol is None:
            raise PortfolioMLClientError(
                "instrument_symbol is required when scope=instrument_symbol.",
                status_code=422,
            )

        evaluated_at = utcnow()
        as_of_ledger_at = evaluated_at - timedelta(hours=1)
        as_of_market_at = evaluated_at - timedelta(hours=1)

        deterministic_payload = build_deterministic_signal_payload(
            snapshot_input={
                "scope": scope.value,
                "instrument_symbol": normalized_symbol,
                "series_points": _default_snapshot_points(evaluated_at=evaluated_at),
            },
        )
        lifecycle = resolve_signal_lifecycle_state(
            as_of_ledger_at=as_of_ledger_at,
            as_of_market_at=as_of_market_at,
            evaluated_at=evaluated_at,
            freshness_policy_hours=_DEFAULT_FRESHNESS_HOURS,
            missing_history_windows=[],
        )
        capm_payload = compute_capm_signal_metrics(
            portfolio_returns=[0.010, -0.005, 0.007, 0.002, -0.001, 0.004],
            benchmark_returns=[0.008, -0.004, 0.006, 0.001, -0.001, 0.003],
            risk_free_rate_annual=0.03,
            benchmark_symbol="SPY",
            risk_free_source="UST_3M",
            annualization_factor=_TRADING_DAYS_ANNUALIZATION,
        )

        lifecycle_state = PortfolioMLState(cast(str, lifecycle["state"]))
        signal_rows: list[PortfolioMLSignalRow] = []
        signal_rows_payload_obj = deterministic_payload.get("signals")
        if isinstance(signal_rows_payload_obj, list):
            signal_rows_payload = cast(list[object], signal_rows_payload_obj)
            for signal_row_payload in signal_rows_payload:
                if isinstance(signal_row_payload, Mapping):
                    signal_rows.append(PortfolioMLSignalRow.model_validate(signal_row_payload))

        response = PortfolioMLSignalResponse(
            state=lifecycle_state,
            state_reason_code=cast(str, lifecycle["state_reason_code"]),
            state_reason_detail=cast(str, lifecycle["state_reason_detail"]),
            scope=scope,
            instrument_symbol=normalized_symbol,
            as_of_ledger_at=as_of_ledger_at,
            as_of_market_at=as_of_market_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioMLFreshnessPolicy(max_age_hours=_DEFAULT_FRESHNESS_HOURS),
            signals=signal_rows,
            capm=PortfolioMLCapmMetrics.model_validate(capm_payload),
        )

        if response.state is PortfolioMLState.STALE:
            logger.info(
                "portfolio_ml.signal_generation_stale",
                scope=scope.value,
                instrument_symbol=normalized_symbol,
                reason_code=response.state_reason_code,
            )
        elif response.state is PortfolioMLState.UNAVAILABLE:
            logger.info(
                "portfolio_ml.signal_generation_unavailable",
                scope=scope.value,
                instrument_symbol=normalized_symbol,
                reason_code=response.state_reason_code,
            )
        else:
            logger.info(
                "portfolio_ml.signal_generation_completed",
                scope=scope.value,
                instrument_symbol=normalized_symbol,
                signal_count=len(response.signals),
            )

        return response
    except PortfolioMLClientError:
        logger.error(
            "portfolio_ml.signal_generation_failed",
            scope=scope.value,
            instrument_symbol=normalized_symbol,
            exc_info=True,
        )
        raise
    except Exception:
        logger.error(
            "portfolio_ml.signal_generation_failed",
            scope=scope.value,
            instrument_symbol=normalized_symbol,
            exc_info=True,
        )
        raise PortfolioMLClientError(
            "Unexpected portfolio_ml signal generation error.",
            status_code=500,
        ) from None


def build_walk_forward_splits(
    *,
    total_points: int,
    min_train_size: int,
    horizon: int,
    step: int = 1,
) -> list[dict[str, int]]:
    """Build deterministic walk-forward splits with chronological train/test windows."""

    if total_points <= 0 or min_train_size <= 0 or horizon <= 0 or step <= 0:
        raise PortfolioMLClientError(
            "Walk-forward parameters must be positive integers.",
            status_code=422,
        )
    if total_points < (min_train_size + horizon):
        raise PortfolioMLClientError(
            "Insufficient points for requested walk-forward split parameters.",
            status_code=409,
        )

    splits: list[dict[str, int]] = []
    split_anchor = min_train_size
    while split_anchor + horizon <= total_points:
        splits.append(
            {
                "train_start": 0,
                "train_end": split_anchor,
                "test_start": split_anchor,
                "test_end": split_anchor + horizon,
            }
        )
        split_anchor += step

    enforce_no_temporal_leakage(splits=splits)
    return splits


def enforce_no_temporal_leakage(*, splits: Sequence[Mapping[str, int]]) -> None:
    """Reject walk-forward split definitions that violate temporal boundaries."""

    for split in splits:
        train_start = split.get("train_start")
        train_end = split.get("train_end")
        test_start = split.get("test_start")
        test_end = split.get("test_end")
        if train_start is None or train_end is None or test_start is None or test_end is None:
            raise PortfolioMLClientError(
                "Walk-forward split is missing required boundary fields.",
                status_code=422,
            )
        if train_start < 0 or train_end <= train_start:
            raise PortfolioMLClientError(
                "Walk-forward training boundaries are invalid.",
                status_code=422,
            )
        if test_start < 0 or test_end <= test_start:
            raise PortfolioMLClientError(
                "Walk-forward test boundaries are invalid.",
                status_code=422,
            )
        if train_end > test_start:
            raise PortfolioMLClientError(
                "Temporal leakage detected: train_end exceeds test_start.",
                status_code=409,
            )


def _to_float_series(values: Sequence[float | int | Decimal]) -> np.ndarray:
    """Convert numeric sequence into deterministic float64 numpy array."""

    if len(values) == 0:
        raise PortfolioMLClientError(
            "Forecast series must not be empty.",
            status_code=409,
        )
    return np.asarray([float(value) for value in values], dtype="float64")


def build_shared_lag_feature_matrix(
    *,
    series_values: Sequence[float | int | Decimal],
    lag_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Build lag-feature matrix shared by baseline forecast candidates."""

    if lag_count <= 0:
        raise PortfolioMLClientError(
            "Lag count must be positive.",
            status_code=422,
        )
    series_array = _to_float_series(series_values)
    if len(series_array) <= lag_count:
        raise PortfolioMLClientError(
            "Insufficient history for lag feature matrix.",
            status_code=409,
        )

    feature_rows: list[list[float]] = []
    targets: list[float] = []
    for idx in range(lag_count, len(series_array)):
        lag_window = series_array[idx - lag_count : idx]
        feature_rows.append(lag_window.tolist())
        targets.append(float(series_array[idx]))

    return np.asarray(feature_rows, dtype="float64"), np.asarray(targets, dtype="float64")


def _forecast_naive(series_array: np.ndarray, *, horizon_count: int) -> np.ndarray:
    """Generate naive baseline forecast from last observed value."""

    return np.full(shape=(horizon_count,), fill_value=float(series_array[-1]), dtype="float64")


def _forecast_seasonal_naive(
    series_array: np.ndarray,
    *,
    horizon_count: int,
    seasonal_period: int,
) -> np.ndarray:
    """Generate seasonal-naive baseline forecast."""

    if seasonal_period <= 0:
        raise PortfolioMLClientError(
            "Seasonal period must be positive.",
            status_code=422,
        )
    if len(series_array) < seasonal_period:
        return _forecast_naive(series_array, horizon_count=horizon_count)

    seasonal_values = series_array[-seasonal_period:]
    forecast_values: list[float] = []
    for horizon_offset in range(horizon_count):
        forecast_values.append(float(seasonal_values[horizon_offset % seasonal_period]))
    return np.asarray(forecast_values, dtype="float64")


def _forecast_ewma_holt(series_array: np.ndarray, *, horizon_count: int) -> np.ndarray:
    """Generate Holt-style EWMA baseline forecast."""

    if len(series_array) < 2:
        return _forecast_naive(series_array, horizon_count=horizon_count)

    alpha = 0.4
    beta = 0.2
    level = float(series_array[0])
    trend = float(series_array[1] - series_array[0])
    for observed_value in series_array[1:]:
        previous_level = level
        level = alpha * float(observed_value) + (1.0 - alpha) * (level + trend)
        trend = beta * (level - previous_level) + (1.0 - beta) * trend

    return np.asarray(
        [level + ((horizon_index + 1) * trend) for horizon_index in range(horizon_count)],
        dtype="float64",
    )


def _forecast_arima_baseline(series_array: np.ndarray, *, horizon_count: int) -> np.ndarray:
    """Generate AR(1)-style baseline forecast using least-squares fit."""

    if len(series_array) < 3:
        return _forecast_naive(series_array, horizon_count=horizon_count)

    x_axis = series_array[:-1]
    y_axis = series_array[1:]
    design_matrix = np.column_stack((np.ones(len(x_axis), dtype="float64"), x_axis))
    coefficients, *_ = np.linalg.lstsq(design_matrix, y_axis, rcond=None)
    intercept = float(coefficients[0])
    phi = float(coefficients[1])

    forecast_values: list[float] = []
    current_value = float(series_array[-1])
    for _ in range(horizon_count):
        current_value = intercept + (phi * current_value)
        forecast_values.append(current_value)
    return np.asarray(forecast_values, dtype="float64")


def _forecast_ridge_lag_regression(
    series_array: np.ndarray,
    *,
    horizon_count: int,
    lag_count: int,
    ridge_lambda: float = 1.0,
) -> np.ndarray:
    """Generate ridge lag-regression baseline forecast from shared lag features."""

    if len(series_array) <= lag_count:
        return _forecast_naive(series_array, horizon_count=horizon_count)

    x_matrix, y_vector = build_shared_lag_feature_matrix(
        series_values=series_array.tolist(),
        lag_count=lag_count,
    )
    intercept_column = np.ones((x_matrix.shape[0], 1), dtype="float64")
    x_with_intercept = np.hstack((intercept_column, x_matrix))

    ridge_identity = np.eye(x_with_intercept.shape[1], dtype="float64")
    ridge_identity[0, 0] = 0.0
    weights = (
        np.linalg.pinv((x_with_intercept.T @ x_with_intercept) + (ridge_lambda * ridge_identity))
        @ x_with_intercept.T
        @ y_vector
    )

    lag_window = list(series_array[-lag_count:])
    forecast_values: list[float] = []
    for _ in range(horizon_count):
        feature_vector = np.asarray([1.0, *lag_window], dtype="float64")
        next_value = float(feature_vector @ weights)
        forecast_values.append(next_value)
        lag_window = [*lag_window[1:], next_value]

    return np.asarray(forecast_values, dtype="float64")


def run_baseline_candidate_forecasts(
    *,
    series_values: Sequence[float | int | Decimal],
    horizon_count: int,
    seasonal_period: int = 5,
) -> dict[str, list[Decimal]]:
    """Run approved baseline forecast candidate family over one input series."""

    if horizon_count <= 0:
        raise PortfolioMLClientError(
            "Forecast horizon count must be positive.",
            status_code=422,
        )

    series_array = _to_float_series(series_values)
    if len(series_array) < 2:
        raise PortfolioMLClientError(
            "Forecast generation requires at least two observations.",
            status_code=409,
        )

    candidates: dict[str, np.ndarray] = {
        "naive": _forecast_naive(series_array, horizon_count=horizon_count),
        "seasonal_naive": _forecast_seasonal_naive(
            series_array,
            horizon_count=horizon_count,
            seasonal_period=seasonal_period,
        ),
        "ewma_holt": _forecast_ewma_holt(series_array, horizon_count=horizon_count),
        "arima_baseline": _forecast_arima_baseline(series_array, horizon_count=horizon_count),
        "ridge_lag_regression": _forecast_ridge_lag_regression(
            series_array,
            horizon_count=horizon_count,
            lag_count=_DEFAULT_RIDGE_LAG_COUNT,
        ),
    }

    quantized: dict[str, list[Decimal]] = {}
    for model_family, forecast_values in candidates.items():
        quantized[model_family] = [
            _quantize_decimal(Decimal(str(value)), scale=_FORECAST_VALUE_SCALE)
            for value in forecast_values
        ]
    return quantized


def _wmape(*, actual: Sequence[float], predicted: Sequence[float]) -> float:
    """Compute weighted mean absolute percentage error."""

    actual_array = np.asarray(actual, dtype="float64")
    predicted_array = np.asarray(predicted, dtype="float64")
    denominator = float(np.sum(np.abs(actual_array)))
    if math.isclose(denominator, 0.0):
        return 0.0
    numerator = float(np.sum(np.abs(actual_array - predicted_array)))
    return numerator / denominator


def evaluate_forecast_promotion_policy(
    *,
    candidate_wmape_by_horizon: Sequence[float],
    naive_wmape_by_horizon: Sequence[float],
    interval_coverage: float,
) -> dict[str, object]:
    """Evaluate frozen forecast promotion policy gates against naive baseline."""

    if len(candidate_wmape_by_horizon) == 0 or len(naive_wmape_by_horizon) == 0:
        raise PortfolioMLClientError(
            "Policy evaluation requires non-empty horizon metrics.",
            status_code=422,
        )
    if len(candidate_wmape_by_horizon) != len(naive_wmape_by_horizon):
        raise PortfolioMLClientError(
            "Candidate and naive horizon metric counts must match.",
            status_code=422,
        )

    candidate_mean = float(np.mean(np.asarray(candidate_wmape_by_horizon, dtype="float64")))
    naive_mean = float(np.mean(np.asarray(naive_wmape_by_horizon, dtype="float64")))

    if math.isclose(naive_mean, 0.0):
        improvement_pct = 0.0
    else:
        improvement_pct = ((naive_mean - candidate_mean) / naive_mean) * 100.0

    horizon_regressions: list[float] = []
    for candidate_metric, naive_metric in zip(
        candidate_wmape_by_horizon,
        naive_wmape_by_horizon,
        strict=True,
    ):
        if math.isclose(naive_metric, 0.0):
            horizon_regressions.append(0.0)
        else:
            horizon_regressions.append(((candidate_metric - naive_metric) / naive_metric) * 100.0)
    max_horizon_regression_pct = max(horizon_regressions)

    if interval_coverage < _COVERAGE_FLOOR or interval_coverage > _COVERAGE_CEILING:
        return {
            "qualified": False,
            "reason_code": "interval_calibration_failed",
            "reason_detail": "Prediction interval coverage is outside policy bounds.",
            "improvement_pct": improvement_pct,
            "max_horizon_regression_pct": max_horizon_regression_pct,
            "interval_coverage": interval_coverage,
        }
    if improvement_pct < _PROMOTION_IMPROVEMENT_MIN_PCT:
        return {
            "qualified": False,
            "reason_code": "baseline_improvement_failed",
            "reason_detail": "Candidate did not beat naive baseline by required threshold.",
            "improvement_pct": improvement_pct,
            "max_horizon_regression_pct": max_horizon_regression_pct,
            "interval_coverage": interval_coverage,
        }
    if max_horizon_regression_pct > _MAX_HORIZON_REGRESSION_PCT:
        return {
            "qualified": False,
            "reason_code": "horizon_regression_exceeded",
            "reason_detail": "Candidate exceeds allowed horizon-level regression.",
            "improvement_pct": improvement_pct,
            "max_horizon_regression_pct": max_horizon_regression_pct,
            "interval_coverage": interval_coverage,
        }

    return {
        "qualified": True,
        "reason_code": "qualified",
        "reason_detail": "Candidate satisfies promotion policy gates.",
        "improvement_pct": improvement_pct,
        "max_horizon_regression_pct": max_horizon_regression_pct,
        "interval_coverage": interval_coverage,
    }


def select_champion_forecast_snapshot(
    *,
    scope: str,
    instrument_symbol: str | None,
    model_family: str,
    horizons: Sequence[Mapping[str, object]],
    policy_result: Mapping[str, object],
    evaluated_at: datetime,
    metric_vector: Mapping[str, object] | None = None,
    baseline_comparator_metrics: Mapping[str, object] | None = None,
    feature_set_hash: str = "portfolio_ml_features_v1",
) -> dict[str, object]:
    """Create one deterministic champion snapshot payload from promoted candidate."""

    if policy_result.get("qualified") is not True:
        raise PortfolioMLClientError(
            "Cannot select champion snapshot for non-qualified candidate.",
            status_code=409,
        )

    normalized_symbol = instrument_symbol.strip().upper() if instrument_symbol is not None else None
    if normalized_symbol == "":
        normalized_symbol = None
    snapshot_ref = (
        f"{scope}_{normalized_symbol or 'portfolio'}_{model_family}_{evaluated_at:%Y%m%dT%H%M%SZ}"
    )
    expires_at = evaluated_at + timedelta(hours=_CHAMPION_TTL_HOURS)
    training_window_end = evaluated_at - timedelta(days=1)
    training_window_start = training_window_end - timedelta(days=120)

    normalized_horizons: list[dict[str, object]] = []
    for horizon in horizons:
        normalized_horizons.append(
            {
                "horizon_id": str(horizon["horizon_id"]),
                "point_estimate": _quantize_decimal(
                    _parse_decimal(horizon["point_estimate"], field_name="point_estimate"),
                    scale=_FORECAST_VALUE_SCALE,
                ),
                "lower_bound": _quantize_decimal(
                    _parse_decimal(horizon["lower_bound"], field_name="lower_bound"),
                    scale=_FORECAST_VALUE_SCALE,
                ),
                "upper_bound": _quantize_decimal(
                    _parse_decimal(horizon["upper_bound"], field_name="upper_bound"),
                    scale=_FORECAST_VALUE_SCALE,
                ),
                "confidence_level": _parse_decimal(
                    horizon["confidence_level"],
                    field_name="confidence_level",
                ),
                "model_snapshot_ref": snapshot_ref,
            }
        )

    return {
        "scope": scope,
        "instrument_symbol": normalized_symbol,
        "model_family": model_family,
        "model_snapshot_ref": snapshot_ref,
        "evaluated_at": evaluated_at,
        "expires_at": expires_at,
        "training_window_start": training_window_start,
        "training_window_end": training_window_end,
        "policy_result": dict(policy_result),
        "metric_vector": dict(metric_vector) if metric_vector is not None else {},
        "baseline_comparator_metrics": (
            dict(baseline_comparator_metrics) if baseline_comparator_metrics is not None else {}
        ),
        "feature_set_hash": feature_set_hash,
        "run_status": "completed",
        "horizons": normalized_horizons,
    }


def resolve_forecast_lifecycle_state(
    *,
    champion_snapshot: Mapping[str, object] | None,
    evaluated_at: datetime,
) -> dict[str, str]:
    """Resolve lifecycle state for one forecast response from champion snapshot state."""

    if champion_snapshot is None:
        return {
            "state": PortfolioMLState.UNAVAILABLE.value,
            "state_reason_code": "no_qualified_champion",
            "state_reason_detail": "No promoted forecast champion is available.",
        }

    expires_at_value = champion_snapshot.get("expires_at")
    expires_at = _to_utc_datetime(expires_at_value, field_name="expires_at")
    if evaluated_at > expires_at:
        return {
            "state": PortfolioMLState.STALE.value,
            "state_reason_code": "champion_expired",
            "state_reason_detail": "Champion snapshot exceeded policy TTL.",
        }

    return {
        "state": PortfolioMLState.READY.value,
        "state_reason_code": "ready",
        "state_reason_detail": "forecast_ready",
    }


def _build_default_forecast_history(*, points: int) -> list[Decimal]:
    """Build one deterministic synthetic history series for forecast baseline execution."""

    if points < 20:
        raise PortfolioMLClientError(
            "Forecast history generation requires at least 20 points.",
            status_code=422,
        )
    history: list[Decimal] = []
    for idx in range(points):
        baseline = 100.0 + (idx * 0.35)
        seasonal = math.sin(idx / 3.0) * 1.2
        value = baseline + seasonal
        history.append(_quantize_decimal(Decimal(str(value)), scale=_FORECAST_VALUE_SCALE))
    return history


def _build_default_actual_horizon(
    *,
    history: Sequence[Decimal],
    horizon_count: int,
) -> list[float]:
    """Build deterministic synthetic future values for baseline candidate evaluation."""

    if len(history) == 0:
        raise PortfolioMLClientError(
            "History is required to build deterministic forecast evaluation targets.",
            status_code=409,
        )
    last_value = float(history[-1])
    return [last_value + ((offset + 1) * 0.30) for offset in range(horizon_count)]


def _build_interval_bounds(
    *,
    point_forecast: Sequence[Decimal],
    residual_scale: float,
) -> tuple[list[Decimal], list[Decimal]]:
    """Build deterministic interval bounds for one point-forecast vector."""

    z_score_for_80 = 1.2815515655446004
    interval_radius = max(0.01, residual_scale * z_score_for_80)
    lower: list[Decimal] = []
    upper: list[Decimal] = []
    for point_value in point_forecast:
        lower.append(
            _quantize_decimal(
                point_value - Decimal(str(interval_radius)),
                scale=_FORECAST_VALUE_SCALE,
            )
        )
        upper.append(
            _quantize_decimal(
                point_value + Decimal(str(interval_radius)),
                scale=_FORECAST_VALUE_SCALE,
            )
        )
    return lower, upper


def _interval_coverage(
    *,
    actual: Sequence[float],
    lower_bounds: Sequence[Decimal],
    upper_bounds: Sequence[Decimal],
) -> float:
    """Compute empirical interval coverage for one horizon vector."""

    covered = 0
    for actual_value, lower_value, upper_value in zip(
        actual, lower_bounds, upper_bounds, strict=True
    ):
        lower_float = float(lower_value)
        upper_float = float(upper_value)
        if lower_float <= actual_value <= upper_float:
            covered += 1
    return covered / len(actual) if len(actual) > 0 else 0.0


async def _upsert_model_snapshot(
    *,
    db: AsyncSession,
    snapshot_payload: Mapping[str, object],
    lifecycle_state: PortfolioMLState,
) -> PortfolioMLModelSnapshot:
    """Persist one model snapshot metadata row for registry audit retrieval."""

    snapshot_ref_value = snapshot_payload.get("model_snapshot_ref")
    if not isinstance(snapshot_ref_value, str) or snapshot_ref_value.strip() == "":
        raise PortfolioMLClientError(
            "Model snapshot payload is missing model_snapshot_ref.",
            status_code=422,
        )
    snapshot_ref = snapshot_ref_value.strip()

    scope_value = snapshot_payload.get("scope")
    if not isinstance(scope_value, str):
        raise PortfolioMLClientError(
            "Model snapshot payload is missing scope.",
            status_code=422,
        )
    try:
        normalized_scope = PortfolioMLScope(scope_value)
    except ValueError as exc:
        raise PortfolioMLClientError(
            "Unsupported registry scope filter value.",
            status_code=422,
        ) from exc

    instrument_symbol_value = snapshot_payload.get("instrument_symbol")
    normalized_symbol = (
        instrument_symbol_value.strip().upper()
        if isinstance(instrument_symbol_value, str) and instrument_symbol_value.strip() != ""
        else None
    )

    model_family_value = snapshot_payload.get("model_family")
    if not isinstance(model_family_value, str):
        raise PortfolioMLClientError(
            "Model snapshot payload is missing model_family.",
            status_code=422,
        )
    normalized_model_family = enforce_supported_model_policy(model_family=model_family_value)

    training_window_start_value = snapshot_payload.get("training_window_start")
    training_window_end_value = snapshot_payload.get("training_window_end")
    evaluated_at_value = snapshot_payload.get("evaluated_at")
    expires_at_value = snapshot_payload.get("expires_at")

    training_window_start = _to_utc_datetime(
        training_window_start_value,
        field_name="training_window_start",
    )
    training_window_end = _to_utc_datetime(
        training_window_end_value,
        field_name="training_window_end",
    )
    promoted_at = _to_utc_datetime(
        evaluated_at_value,
        field_name="evaluated_at",
    )
    expires_at = _to_utc_datetime(expires_at_value, field_name="expires_at")

    policy_result = _coerce_json_mapping(snapshot_payload.get("policy_result"))
    metric_vector = _coerce_json_mapping(snapshot_payload.get("metric_vector"))
    baseline_metrics = _coerce_json_mapping(snapshot_payload.get("baseline_comparator_metrics"))

    feature_set_hash_value = snapshot_payload.get("feature_set_hash")
    if not isinstance(feature_set_hash_value, str) or feature_set_hash_value.strip() == "":
        feature_set_hash = "portfolio_ml_features_v1"
    else:
        feature_set_hash = feature_set_hash_value.strip()

    run_status_value = snapshot_payload.get("run_status")
    run_status = run_status_value.strip() if isinstance(run_status_value, str) else "completed"
    if run_status == "":
        run_status = "completed"

    replaced_snapshot_ref_value = snapshot_payload.get("replaced_snapshot_ref")
    replaced_snapshot_ref = (
        replaced_snapshot_ref_value.strip()
        if isinstance(replaced_snapshot_ref_value, str)
        and replaced_snapshot_ref_value.strip() != ""
        else None
    )

    existing = await db.execute(
        select(PortfolioMLModelSnapshot).where(
            PortfolioMLModelSnapshot.snapshot_ref == snapshot_ref
        )
    )
    snapshot_row = existing.scalar_one_or_none()
    if snapshot_row is None:
        snapshot_row = PortfolioMLModelSnapshot(
            snapshot_ref=snapshot_ref,
            scope=normalized_scope.value,
            instrument_symbol=normalized_symbol,
            model_family=normalized_model_family,
            lifecycle_state=lifecycle_state.value,
            feature_set_hash=feature_set_hash,
            data_window_start=training_window_start,
            data_window_end=training_window_end,
            run_status=run_status,
            promoted_at=promoted_at,
            expires_at=expires_at,
            replaced_snapshot_ref=replaced_snapshot_ref,
            policy_result=policy_result,
            metric_vector=metric_vector,
            baseline_comparator_metrics=baseline_metrics,
            failure_reason_code=None,
            failure_reason_detail=None,
            snapshot_metadata={
                "policy_thresholds": {
                    "wmape_improvement_min_pct": _PROMOTION_IMPROVEMENT_MIN_PCT,
                    "max_horizon_regression_pct": _MAX_HORIZON_REGRESSION_PCT,
                    "interval_coverage_floor": _COVERAGE_FLOOR,
                    "interval_coverage_ceiling": _COVERAGE_CEILING,
                    "champion_ttl_hours": _CHAMPION_TTL_HOURS,
                }
            },
        )
        db.add(snapshot_row)
    else:
        snapshot_row.scope = normalized_scope.value
        snapshot_row.instrument_symbol = normalized_symbol
        snapshot_row.model_family = normalized_model_family
        snapshot_row.lifecycle_state = lifecycle_state.value
        snapshot_row.feature_set_hash = feature_set_hash
        snapshot_row.data_window_start = training_window_start
        snapshot_row.data_window_end = training_window_end
        snapshot_row.run_status = run_status
        snapshot_row.promoted_at = promoted_at
        snapshot_row.expires_at = expires_at
        snapshot_row.replaced_snapshot_ref = replaced_snapshot_ref
        snapshot_row.policy_result = policy_result
        snapshot_row.metric_vector = metric_vector
        snapshot_row.baseline_comparator_metrics = baseline_metrics
        snapshot_row.failure_reason_code = None
        snapshot_row.failure_reason_detail = None

    await db.flush()
    await db.commit()
    await db.refresh(snapshot_row)
    return snapshot_row


def _to_registry_row(snapshot: PortfolioMLModelSnapshot) -> PortfolioMLRegistryRow:
    """Map one model snapshot row to typed registry response row."""

    try:
        scope = PortfolioMLScope(snapshot.scope)
    except ValueError:
        scope = PortfolioMLScope.PORTFOLIO
    try:
        lifecycle_state = PortfolioMLState(snapshot.lifecycle_state)
    except ValueError:
        lifecycle_state = PortfolioMLState.ERROR

    return PortfolioMLRegistryRow(
        snapshot_ref=snapshot.snapshot_ref,
        scope=scope,
        instrument_symbol=snapshot.instrument_symbol,
        model_family=snapshot.model_family,
        lifecycle_state=lifecycle_state,
        feature_set_hash=snapshot.feature_set_hash,
        data_window_start=snapshot.data_window_start,
        data_window_end=snapshot.data_window_end,
        run_status=snapshot.run_status,
        promoted_at=snapshot.promoted_at,
        expires_at=snapshot.expires_at,
        replaced_snapshot_ref=snapshot.replaced_snapshot_ref,
        policy_result=snapshot.policy_result,
        metric_vector=snapshot.metric_vector,
        baseline_comparator_metrics=snapshot.baseline_comparator_metrics,
    )


async def get_portfolio_ml_registry_response(
    *,
    db: AsyncSession,
    scope: str | None = None,
    model_family: str | None = None,
    lifecycle_state: str | None = None,
) -> PortfolioMLRegistryResponse:
    """Return one read-only registry response for model snapshot audit queries."""

    statement = select(PortfolioMLModelSnapshot)

    if scope is not None and scope.strip() != "":
        try:
            normalized_scope = PortfolioMLScope(scope.strip())
        except ValueError as exc:
            raise PortfolioMLClientError(
                "Unsupported registry scope filter value.",
                status_code=422,
            ) from exc
        statement = statement.where(PortfolioMLModelSnapshot.scope == normalized_scope.value)

    if model_family is not None and model_family.strip() != "":
        normalized_model_family = enforce_supported_model_policy(model_family=model_family)
        statement = statement.where(
            PortfolioMLModelSnapshot.model_family == normalized_model_family
        )

    if lifecycle_state is not None and lifecycle_state.strip() != "":
        try:
            normalized_lifecycle_state = PortfolioMLState(lifecycle_state.strip().lower())
        except ValueError as exc:
            raise PortfolioMLClientError(
                "Unsupported registry lifecycle_state filter value.",
                status_code=422,
            ) from exc
        statement = statement.where(
            PortfolioMLModelSnapshot.lifecycle_state == normalized_lifecycle_state.value
        )

    statement = statement.order_by(
        PortfolioMLModelSnapshot.promoted_at.desc(),
        PortfolioMLModelSnapshot.id.desc(),
    )
    rows_result = await db.execute(statement)
    snapshot_rows = rows_result.scalars().all()

    evaluated_at = utcnow()
    as_of_ledger_at = evaluated_at - timedelta(hours=1)
    as_of_market_at = evaluated_at - timedelta(hours=1)

    if len(snapshot_rows) == 0:
        return PortfolioMLRegistryResponse(
            state=PortfolioMLState.UNAVAILABLE,
            state_reason_code="no_registry_rows",
            state_reason_detail="No model registry snapshots match the requested filters.",
            as_of_ledger_at=as_of_ledger_at,
            as_of_market_at=as_of_market_at,
            evaluated_at=evaluated_at,
            rows=[],
        )

    registry_rows = [_to_registry_row(snapshot) for snapshot in snapshot_rows]
    return PortfolioMLRegistryResponse(
        state=PortfolioMLState.READY,
        state_reason_code="ready",
        state_reason_detail="registry_rows_available",
        as_of_ledger_at=as_of_ledger_at,
        as_of_market_at=as_of_market_at,
        evaluated_at=evaluated_at,
        rows=registry_rows,
    )


async def get_portfolio_ml_forecast_response(
    *,
    scope: PortfolioMLScope,
    instrument_symbol: str | None = None,
    db: AsyncSession | None = None,
) -> PortfolioMLForecastResponse:
    """Return one read-only probabilistic forecast response for selected scope."""

    normalized_symbol = instrument_symbol.strip().upper() if instrument_symbol is not None else None
    if normalized_symbol == "":
        normalized_symbol = None
    logger.info(
        "portfolio_ml.forecast_generation_started",
        scope=scope.value,
        instrument_symbol=normalized_symbol,
    )

    try:
        if scope is PortfolioMLScope.INSTRUMENT_SYMBOL and normalized_symbol is None:
            raise PortfolioMLClientError(
                "instrument_symbol is required when scope=instrument_symbol.",
                status_code=422,
            )

        evaluated_at = utcnow()
        as_of_ledger_at = evaluated_at - timedelta(hours=1)
        as_of_market_at = evaluated_at - timedelta(hours=1)

        forecast_history = _build_default_forecast_history(points=140)
        actual_horizon = _build_default_actual_horizon(
            history=forecast_history,
            horizon_count=_FORECAST_HORIZON_COUNT,
        )

        # Build a simple walk-forward split set for leakage-safe validation contracts.
        walk_forward_splits = build_walk_forward_splits(
            total_points=len(forecast_history),
            min_train_size=90,
            horizon=_FORECAST_HORIZON_COUNT,
            step=5,
        )
        enforce_no_temporal_leakage(splits=walk_forward_splits)

        candidate_forecasts = run_baseline_candidate_forecasts(
            series_values=forecast_history,
            horizon_count=_FORECAST_HORIZON_COUNT,
            seasonal_period=5,
        )
        naive_forecast = [float(value) for value in candidate_forecasts["naive"]]
        naive_wmape_by_horizon = [
            (
                0.0
                if math.isclose(actual_value, 0.0)
                else abs(actual_value - naive_value) / abs(actual_value)
            )
            for actual_value, naive_value in zip(actual_horizon, naive_forecast, strict=True)
        ]

        training_residual_scale = float(
            np.std(
                np.diff(np.asarray([float(value) for value in forecast_history], dtype="float64")),
                ddof=1,
            )
        )
        if math.isnan(training_residual_scale):
            training_residual_scale = 0.01

        best_snapshot: dict[str, object] | None = None
        best_improvement = float("-inf")
        for model_family, point_forecast in candidate_forecasts.items():
            if model_family == "naive":
                continue
            normalized_model_family = enforce_supported_model_policy(model_family=model_family)

            point_forecast_float = [float(value) for value in point_forecast]
            candidate_wmape_by_horizon = [
                (
                    0.0
                    if math.isclose(actual_value, 0.0)
                    else abs(actual_value - predicted_value) / abs(actual_value)
                )
                for actual_value, predicted_value in zip(
                    actual_horizon,
                    point_forecast_float,
                    strict=True,
                )
            ]
            lower_bounds, upper_bounds = _build_interval_bounds(
                point_forecast=point_forecast,
                residual_scale=training_residual_scale,
            )
            coverage = _interval_coverage(
                actual=actual_horizon,
                lower_bounds=lower_bounds,
                upper_bounds=upper_bounds,
            )
            policy_result = evaluate_forecast_promotion_policy(
                candidate_wmape_by_horizon=candidate_wmape_by_horizon,
                naive_wmape_by_horizon=naive_wmape_by_horizon,
                interval_coverage=coverage,
            )
            if policy_result["qualified"] is not True:
                continue

            candidate_horizons: list[dict[str, object]] = []
            for horizon_index, point_value in enumerate(point_forecast):
                candidate_horizons.append(
                    {
                        "horizon_id": f"h+{horizon_index + 1}",
                        "point_estimate": point_value,
                        "lower_bound": lower_bounds[horizon_index],
                        "upper_bound": upper_bounds[horizon_index],
                        "confidence_level": _FORECAST_CONFIDENCE_LEVEL,
                    }
                )

            candidate_snapshot = select_champion_forecast_snapshot(
                scope=scope.value,
                instrument_symbol=normalized_symbol,
                model_family=normalized_model_family,
                horizons=candidate_horizons,
                policy_result=policy_result,
                evaluated_at=evaluated_at,
                metric_vector={
                    "candidate_wmape_by_horizon": candidate_wmape_by_horizon,
                    "candidate_wmape_mean": float(
                        np.mean(np.asarray(candidate_wmape_by_horizon, dtype="float64"))
                    ),
                    "interval_coverage": coverage,
                },
                baseline_comparator_metrics={
                    "naive_wmape_by_horizon": naive_wmape_by_horizon,
                    "naive_wmape_mean": float(
                        np.mean(np.asarray(naive_wmape_by_horizon, dtype="float64"))
                    ),
                },
            )
            candidate_improvement = float(cast(float, policy_result["improvement_pct"]))
            if candidate_improvement > best_improvement:
                best_improvement = candidate_improvement
                best_snapshot = candidate_snapshot

        scope_key = (scope.value, normalized_symbol or "")
        if best_snapshot is not None:
            _FORECAST_CHAMPION_BY_SCOPE[scope_key] = best_snapshot

        champion_snapshot = _FORECAST_CHAMPION_BY_SCOPE.get(scope_key)
        lifecycle = resolve_forecast_lifecycle_state(
            champion_snapshot=champion_snapshot,
            evaluated_at=evaluated_at,
        )
        lifecycle_state = PortfolioMLState(lifecycle["state"])
        if db is not None and champion_snapshot is not None:
            await _upsert_model_snapshot(
                db=db,
                snapshot_payload=champion_snapshot,
                lifecycle_state=lifecycle_state,
            )

        horizons: list[PortfolioMLForecastHorizonRow] = []
        model_snapshot_ref: str | None = None
        selected_model_family: str | None = None
        training_window_start: datetime | None = None
        training_window_end: datetime | None = None
        if champion_snapshot is not None:
            snapshot_ref_value = champion_snapshot.get("model_snapshot_ref")
            if isinstance(snapshot_ref_value, str):
                model_snapshot_ref = snapshot_ref_value
            selected_family_value = champion_snapshot.get("model_family")
            if isinstance(selected_family_value, str):
                selected_model_family = selected_family_value
            training_window_start_value = champion_snapshot.get("training_window_start")
            training_window_end_value = champion_snapshot.get("training_window_end")
            if training_window_start_value is not None:
                training_window_start = _to_utc_datetime(
                    training_window_start_value,
                    field_name="training_window_start",
                )
            if training_window_end_value is not None:
                training_window_end = _to_utc_datetime(
                    training_window_end_value,
                    field_name="training_window_end",
                )

            horizon_rows_payload_obj = champion_snapshot.get("horizons")
            if isinstance(horizon_rows_payload_obj, list):
                horizon_rows_payload = cast(list[object], horizon_rows_payload_obj)
                for horizon_payload in horizon_rows_payload:
                    if isinstance(horizon_payload, Mapping):
                        horizons.append(
                            PortfolioMLForecastHorizonRow.model_validate(horizon_payload)
                        )

        response = PortfolioMLForecastResponse(
            state=lifecycle_state,
            state_reason_code=lifecycle["state_reason_code"],
            state_reason_detail=lifecycle["state_reason_detail"],
            scope=scope,
            instrument_symbol=normalized_symbol,
            as_of_ledger_at=as_of_ledger_at,
            as_of_market_at=as_of_market_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioMLFreshnessPolicy(max_age_hours=_DEFAULT_FRESHNESS_HOURS),
            model_snapshot_ref=model_snapshot_ref,
            model_family=selected_model_family,
            training_window_start=training_window_start,
            training_window_end=training_window_end,
            horizons=horizons if lifecycle_state is PortfolioMLState.READY else [],
        )

        if response.state is PortfolioMLState.STALE:
            logger.info(
                "portfolio_ml.forecast_generation_stale",
                scope=scope.value,
                instrument_symbol=normalized_symbol,
                reason_code=response.state_reason_code,
            )
        elif response.state is PortfolioMLState.UNAVAILABLE:
            logger.info(
                "portfolio_ml.forecast_generation_unavailable",
                scope=scope.value,
                instrument_symbol=normalized_symbol,
                reason_code=response.state_reason_code,
            )
        else:
            logger.info(
                "portfolio_ml.forecast_generation_completed",
                scope=scope.value,
                instrument_symbol=normalized_symbol,
                model_family=response.model_family,
                horizon_count=len(response.horizons),
            )

        return response
    except PortfolioMLClientError:
        logger.error(
            "portfolio_ml.forecast_generation_failed",
            scope=scope.value,
            instrument_symbol=normalized_symbol,
            exc_info=True,
        )
        raise
    except Exception:
        logger.error(
            "portfolio_ml.forecast_generation_failed",
            scope=scope.value,
            instrument_symbol=normalized_symbol,
            exc_info=True,
        )
        raise PortfolioMLClientError(
            "Unexpected portfolio_ml forecast generation error.",
            status_code=500,
        ) from None
