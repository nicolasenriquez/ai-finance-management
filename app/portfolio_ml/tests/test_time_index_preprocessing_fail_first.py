"""Fail-first tests for time-index normalization and missing-point handling."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

import pandas as pd
import pytest

NormalizeTimeIndexSeriesCallable = Callable[..., pd.Series]


def _load_portfolio_ml_service_module() -> object:
    """Load portfolio_ml service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 3.1-3.2 before preprocessing tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> Callable[..., Any]:
    """Load one named callable from portfolio_ml service module."""

    module = _load_portfolio_ml_service_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(Callable[..., Any], candidate)


def _load_client_error_type() -> type[Exception]:
    """Load one portfolio_ml client error type for explicit-failure assertions."""

    module = _load_portfolio_ml_service_module()
    candidate = getattr(module, "PortfolioMLClientError", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioMLClientError. "
            "Implement task 3.1 error contracts before this test can pass.",
        )
    return cast(type[Exception], candidate)


def test_normalize_time_index_resamples_and_preserves_missing_points() -> None:
    """Normalization should enforce UTC daily index and preserve missing points as gaps."""

    normalize_time_index_series = cast(
        NormalizeTimeIndexSeriesCallable,
        _load_callable("normalize_time_index_series", task_hint="3.2"),
    )

    raw_points: list[dict[str, str]] = [
        {"captured_at": "2026-01-04T00:00:00Z", "value": "101.5"},
        {"captured_at": "2026-01-01T00:00:00Z", "value": "100.0"},
        {"captured_at": "2026-01-02T00:00:00Z", "value": "100.4"},
    ]

    normalized = normalize_time_index_series(
        raw_points=raw_points,
        frequency="1D",
        timezone="UTC",
    )

    assert isinstance(normalized, pd.Series)
    assert isinstance(normalized.index, pd.DatetimeIndex)
    assert normalized.index.is_monotonic_increasing
    assert str(normalized.index.tz) == "UTC"
    assert normalized.index[0].isoformat() == "2026-01-01T00:00:00+00:00"
    assert normalized.index[-1].isoformat() == "2026-01-04T00:00:00+00:00"
    assert normalized.isna().sum() == 1


def test_normalize_time_index_rejects_duplicate_timestamps_explicitly() -> None:
    """Normalization should reject duplicate timestamps instead of silently collapsing them."""

    normalize_time_index_series = cast(
        NormalizeTimeIndexSeriesCallable,
        _load_callable("normalize_time_index_series", task_hint="3.2"),
    )
    client_error_type = _load_client_error_type()

    duplicate_points: list[dict[str, str]] = [
        {"captured_at": "2026-01-01T00:00:00Z", "value": "100.0"},
        {"captured_at": "2026-01-01T00:00:00Z", "value": "100.1"},
    ]

    with pytest.raises(client_error_type) as exc_info:
        normalize_time_index_series(
            raw_points=duplicate_points,
            frequency="1D",
            timezone="UTC",
        )

    assert "duplicate" in str(exc_info.value).lower()
