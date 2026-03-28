"""Unit tests for risk estimator preprocessing guards and quant kernels."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace
from typing import cast

import pytest

RiskCallable = Callable[..., object]

_EXPECTED_REGRESSION_FIXTURES: dict[int, dict[str, Decimal]] = {
    30: {
        "volatility_annualized": Decimal("0.0006566641982796493"),
        "max_drawdown": Decimal("0"),
        "beta": Decimal("1.0188184205704474"),
    },
    90: {
        "volatility_annualized": Decimal("0.0022452767628759044"),
        "max_drawdown": Decimal("0"),
        "beta": Decimal("1.0202124986659036"),
    },
    252: {
        "volatility_annualized": Decimal("0.010418102636546484"),
        "max_drawdown": Decimal("0"),
        "beta": Decimal("1.0268916600969644"),
    },
}
_REGRESSION_ABS_TOLERANCE = Decimal("0.000001")


def _load_portfolio_analytics_module() -> object:
    """Load portfolio analytics service module in fail-first mode."""

    try:
        return import_module("app.portfolio_analytics.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.service. "
            "Implement tasks 2.4-2.7 before risk kernel tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> RiskCallable:
    """Load named callable from portfolio analytics service module."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(RiskCallable, candidate)


def _load_client_error_type() -> type[Exception]:
    """Load portfolio analytics client error type for explicit-failure assertions."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, "PortfolioAnalyticsClientError", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioAnalyticsClientError. "
            "Implement tasks 2.4-2.7 before this test can pass.",
        )
    return cast(type[Exception], candidate)


def _build_aligned_inputs(
    *,
    points: int = 31,
) -> tuple[list[datetime], dict[str, dict[datetime, Decimal]], dict[str, Decimal]]:
    """Build deterministic aligned timestamps, symbol prices, and open quantities."""

    aligned_timestamps: list[datetime] = [
        datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=day_offset)
        for day_offset in range(points)
    ]
    price_series_by_symbol: dict[str, dict[datetime, Decimal]] = {
        "AAPL": {
            timestamp: Decimal("175.00") + Decimal(index)
            for index, timestamp in enumerate(aligned_timestamps)
        },
        "VOO": {
            timestamp: Decimal("95.00") + (Decimal(index) * Decimal("0.5"))
            for index, timestamp in enumerate(aligned_timestamps)
        },
    }
    open_quantity_by_symbol = {
        "AAPL": Decimal("3.000000000"),
        "VOO": Decimal("1.500000000"),
    }
    return aligned_timestamps, price_series_by_symbol, open_quantity_by_symbol


def test_risk_quant_kernels_return_deterministic_metrics_for_same_input() -> None:
    """Quant kernels should return deterministic metric outputs for repeated inputs."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.7",
    )
    compute_metrics = _load_callable(
        "_compute_risk_metrics_from_price_frame",
        task_hint="2.6",
    )

    aligned_timestamps, price_series_by_symbol, open_quantity_by_symbol = _build_aligned_inputs()
    price_frame = build_frame(
        aligned_timestamps=aligned_timestamps,
        price_series_by_symbol=price_series_by_symbol,
    )

    first_result_raw = compute_metrics(
        price_frame=price_frame,
        open_quantity_by_symbol=open_quantity_by_symbol,
        window_days=30,
    )
    second_result_raw = compute_metrics(
        price_frame=price_frame,
        open_quantity_by_symbol=open_quantity_by_symbol,
        window_days=30,
    )

    if not isinstance(first_result_raw, Mapping):
        pytest.fail("Risk kernel result must be a mapping payload.")
    if not isinstance(second_result_raw, Mapping):
        pytest.fail("Risk kernel result must be a mapping payload.")
    first_result = cast(Mapping[str, object], first_result_raw)
    second_result = cast(Mapping[str, object], second_result_raw)
    assert first_result == second_result

    volatility = Decimal(str(first_result["volatility_annualized"]))
    max_drawdown = Decimal(str(first_result["max_drawdown"]))
    beta = Decimal(str(first_result["beta"]))
    assert volatility > Decimal("0")
    assert max_drawdown <= Decimal("0")
    assert beta.is_finite()


def test_risk_preprocessing_rejects_non_utc_or_naive_timestamps() -> None:
    """Preprocessing should fail explicitly when timestamps are not UTC-aware."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.7",
    )
    client_error_type = _load_client_error_type()

    aligned_timestamps, price_series_by_symbol, _ = _build_aligned_inputs()
    naive_timestamps = list(aligned_timestamps)
    naive_timestamps[0] = naive_timestamps[0].replace(tzinfo=None)

    with pytest.raises(client_error_type) as exc_info:
        build_frame(
            aligned_timestamps=naive_timestamps,
            price_series_by_symbol=price_series_by_symbol,
        )

    assert "timezone" in str(exc_info.value).lower()


def test_risk_preprocessing_rejects_unsorted_timestamps() -> None:
    """Preprocessing should fail explicitly when aligned timestamps are not monotonic."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.7",
    )
    client_error_type = _load_client_error_type()
    aligned_timestamps, price_series_by_symbol, _ = _build_aligned_inputs()

    unsorted_timestamps = list(reversed(aligned_timestamps))
    with pytest.raises(client_error_type) as exc_info:
        build_frame(
            aligned_timestamps=unsorted_timestamps,
            price_series_by_symbol=price_series_by_symbol,
        )

    assert "sorted" in str(exc_info.value).lower() or "monotonic" in str(exc_info.value).lower()


def test_risk_preprocessing_rejects_missing_symbol_alignment_points() -> None:
    """Preprocessing should fail explicitly when symbol data misses aligned timestamps."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.7",
    )
    client_error_type = _load_client_error_type()
    aligned_timestamps, price_series_by_symbol, _ = _build_aligned_inputs()

    missing_timestamp = aligned_timestamps[-1]
    del price_series_by_symbol["VOO"][missing_timestamp]

    with pytest.raises(client_error_type) as exc_info:
        build_frame(
            aligned_timestamps=aligned_timestamps,
            price_series_by_symbol=price_series_by_symbol,
        )

    assert "missing" in str(exc_info.value).lower()


def test_risk_quant_kernels_reject_non_positive_price_history() -> None:
    """Risk kernels should fail explicitly when aligned price frame has non-positive values."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.7",
    )
    compute_metrics = _load_callable(
        "_compute_risk_metrics_from_price_frame",
        task_hint="2.6",
    )
    client_error_type = _load_client_error_type()
    aligned_timestamps, price_series_by_symbol, open_quantity_by_symbol = _build_aligned_inputs()

    price_series_by_symbol["AAPL"][aligned_timestamps[1]] = Decimal("0")
    price_frame = build_frame(
        aligned_timestamps=aligned_timestamps,
        price_series_by_symbol=price_series_by_symbol,
    )

    with pytest.raises(client_error_type) as exc_info:
        compute_metrics(
            price_frame=price_frame,
            open_quantity_by_symbol=open_quantity_by_symbol,
            window_days=30,
        )

    assert "positive" in str(exc_info.value).lower()


def test_risk_regression_fixtures_match_default_windows_with_tolerance() -> None:
    """Risk kernels should remain within fixed tolerance for v1 default windows."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.9",
    )
    compute_metrics = _load_callable(
        "_compute_risk_metrics_from_price_frame",
        task_hint="2.9",
    )

    aligned_timestamps, price_series_by_symbol, open_quantity_by_symbol = _build_aligned_inputs(
        points=300
    )
    price_frame = build_frame(
        aligned_timestamps=aligned_timestamps,
        price_series_by_symbol=price_series_by_symbol,
    )

    for window_days, expected_metrics in _EXPECTED_REGRESSION_FIXTURES.items():
        computed_raw = compute_metrics(
            price_frame=price_frame,
            open_quantity_by_symbol=open_quantity_by_symbol,
            window_days=window_days,
        )
        if not isinstance(computed_raw, Mapping):
            pytest.fail("Risk regression fixture result must be a mapping payload.")
        computed = cast(Mapping[str, object], computed_raw)

        for metric_name, expected_value in expected_metrics.items():
            metric_value = Decimal(str(computed[metric_name]))
            assert abs(metric_value - expected_value) <= _REGRESSION_ABS_TOLERANCE


def test_risk_quant_kernels_fail_explicitly_when_scipy_regression_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SciPy regression domain errors should return explicit client-facing failures."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.9",
    )
    compute_metrics = _load_callable(
        "_compute_risk_metrics_from_price_frame",
        task_hint="2.9",
    )
    client_error_type = _load_client_error_type()
    aligned_timestamps, price_series_by_symbol, open_quantity_by_symbol = _build_aligned_inputs(
        points=120
    )
    price_frame = build_frame(
        aligned_timestamps=aligned_timestamps,
        price_series_by_symbol=price_series_by_symbol,
    )

    def _raise_regression_error(*_args: object, **_kwargs: object) -> object:
        raise ValueError("mocked regression failure")

    monkeypatch.setattr(
        "app.portfolio_analytics.service.stats.linregress",
        _raise_regression_error,
    )

    with pytest.raises(client_error_type) as exc_info:
        compute_metrics(
            price_frame=price_frame,
            open_quantity_by_symbol=open_quantity_by_symbol,
            window_days=90,
        )

    assert "regression failed" in str(exc_info.value).lower()


def test_risk_quant_kernels_fail_explicitly_when_scipy_slope_is_non_finite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-finite SciPy regression slope should be rejected explicitly."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.9",
    )
    compute_metrics = _load_callable(
        "_compute_risk_metrics_from_price_frame",
        task_hint="2.9",
    )
    client_error_type = _load_client_error_type()
    aligned_timestamps, price_series_by_symbol, open_quantity_by_symbol = _build_aligned_inputs(
        points=120
    )
    price_frame = build_frame(
        aligned_timestamps=aligned_timestamps,
        price_series_by_symbol=price_series_by_symbol,
    )

    def _return_non_finite_slope(*_args: object, **_kwargs: object) -> object:
        return SimpleNamespace(slope=float("nan"))

    monkeypatch.setattr(
        "app.portfolio_analytics.service.stats.linregress",
        _return_non_finite_slope,
    )

    with pytest.raises(client_error_type) as exc_info:
        compute_metrics(
            price_frame=price_frame,
            open_quantity_by_symbol=open_quantity_by_symbol,
            window_days=90,
        )

    assert "non-finite beta slope" in str(exc_info.value).lower()


def test_risk_quant_kernels_fail_when_proxy_variance_is_zero() -> None:
    """Beta should fail explicitly when proxy returns have zero variance."""

    build_frame = _load_callable(
        "_build_aligned_price_frame",
        task_hint="2.9",
    )
    compute_metrics = _load_callable(
        "_compute_risk_metrics_from_price_frame",
        task_hint="2.9",
    )
    client_error_type = _load_client_error_type()
    aligned_timestamps = [
        datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=day_offset) for day_offset in range(120)
    ]
    price_series_by_symbol = {
        "ONLY": {timestamp: Decimal("100.00") for timestamp in aligned_timestamps}
    }
    open_quantity_by_symbol = {"ONLY": Decimal("2.000000000")}
    price_frame = build_frame(
        aligned_timestamps=aligned_timestamps,
        price_series_by_symbol=price_series_by_symbol,
    )

    with pytest.raises(client_error_type) as exc_info:
        compute_metrics(
            price_frame=price_frame,
            open_quantity_by_symbol=open_quantity_by_symbol,
            window_days=90,
        )

    assert "variance is zero" in str(exc_info.value).lower()
