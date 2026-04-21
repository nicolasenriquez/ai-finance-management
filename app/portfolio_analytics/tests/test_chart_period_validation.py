"""Unit tests for chart period normalization and validation behavior."""

from __future__ import annotations

from importlib import import_module
from typing import Any, cast

import pytest

from app.portfolio_analytics.schemas import PortfolioChartPeriod


def _load_portfolio_analytics_module() -> object:
    """Load portfolio analytics service module in fail-first mode."""

    try:
        return import_module("app.portfolio_analytics.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.service. "
            "Implement task 2.10 before chart-period validation tests can pass.",
        )
        raise AssertionError from exc


def _load_normalizer() -> Any:
    """Load chart-period normalizer callable from service module."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, "normalize_chart_period", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing normalize_chart_period(). "
            "Implement task 2.10 before chart-period validation tests can pass.",
        )
    return candidate


def _load_client_error_type() -> type[Exception]:
    """Load portfolio analytics client error type for explicit-failure assertions."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, "PortfolioAnalyticsClientError", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioAnalyticsClientError. "
            "Implement task 2.10 before chart-period validation tests can pass.",
        )
    return cast(type[Exception], candidate)


def test_normalize_chart_period_supports_case_and_whitespace_variants() -> None:
    """Normalizer should accept supported periods with case/whitespace normalization."""

    normalize_chart_period = _load_normalizer()

    assert normalize_chart_period(period_value=" 30d ") == PortfolioChartPeriod.D30
    assert normalize_chart_period(period_value="90D") == PortfolioChartPeriod.D90
    assert normalize_chart_period(period_value="6m") == PortfolioChartPeriod.D6M
    assert normalize_chart_period(period_value="252d") == PortfolioChartPeriod.D252
    assert normalize_chart_period(period_value=" ytd ") == PortfolioChartPeriod.YTD
    assert normalize_chart_period(period_value=" max ") == PortfolioChartPeriod.MAX


def test_normalize_chart_period_passthrough_for_enum_values() -> None:
    """Normalizer should preserve already-normalized enum values."""

    normalize_chart_period = _load_normalizer()

    assert (
        normalize_chart_period(period_value=PortfolioChartPeriod.D30)
        == PortfolioChartPeriod.D30
    )
    assert (
        normalize_chart_period(period_value=PortfolioChartPeriod.MAX)
        == PortfolioChartPeriod.MAX
    )


def test_normalize_chart_period_rejects_unsupported_values_explicitly() -> None:
    """Unsupported period values should fail explicitly with supported enum detail."""

    normalize_chart_period = _load_normalizer()
    client_error_type = _load_client_error_type()

    with pytest.raises(client_error_type) as exc_info:
        normalize_chart_period(period_value="45D")

    error = exc_info.value
    assert "supported periods" in str(error).lower()
    status_code = getattr(error, "status_code", None)
    assert status_code == 422
