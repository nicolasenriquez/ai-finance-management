"""Fail-first tests for CAPM metric computation and input rejection semantics."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib import import_module
from typing import Any, cast

import pytest

ComputeCapmSignalMetricsCallable = Callable[..., Mapping[str, object]]


def _load_portfolio_ml_service_module() -> object:
    """Load portfolio_ml service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 3.1-3.3 before CAPM tests can pass.",
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
            "Implement task 3.1 error contracts before CAPM tests can pass.",
        )
    return cast(type[Exception], candidate)


def test_capm_metrics_include_required_fields_and_provenance() -> None:
    """CAPM computation should return required metric and provenance fields."""

    compute_capm_signal_metrics = cast(
        ComputeCapmSignalMetricsCallable,
        _load_callable("compute_capm_signal_metrics", task_hint="3.3"),
    )

    payload = compute_capm_signal_metrics(
        portfolio_returns=[0.01, -0.005, 0.007, 0.002, -0.001, 0.004],
        benchmark_returns=[0.008, -0.004, 0.006, 0.001, -0.001, 0.003],
        risk_free_rate_annual=0.03,
        benchmark_symbol="SPY",
        risk_free_source="UST_3M",
        annualization_factor=252,
    )

    assert payload.get("beta") is not None
    assert payload.get("alpha") is not None
    assert payload.get("expected_return") is not None
    assert payload.get("market_premium") is not None
    assert payload.get("benchmark_symbol") == "SPY"
    assert payload.get("risk_free_source") == "UST_3M"


def test_capm_metrics_reject_missing_benchmark_inputs_explicitly() -> None:
    """CAPM computation should fail fast when benchmark series is missing."""

    compute_capm_signal_metrics = cast(
        ComputeCapmSignalMetricsCallable,
        _load_callable("compute_capm_signal_metrics", task_hint="3.3"),
    )
    client_error_type = _load_client_error_type()

    with pytest.raises(client_error_type) as exc_info:
        compute_capm_signal_metrics(
            portfolio_returns=[0.01, -0.005, 0.007],
            benchmark_returns=[],
            risk_free_rate_annual=0.03,
            benchmark_symbol="SPY",
            risk_free_source="UST_3M",
            annualization_factor=252,
        )

    assert "benchmark" in str(exc_info.value).lower()


def test_capm_metrics_reject_missing_risk_free_inputs_explicitly() -> None:
    """CAPM computation should fail fast when risk-free inputs are absent."""

    compute_capm_signal_metrics = cast(
        ComputeCapmSignalMetricsCallable,
        _load_callable("compute_capm_signal_metrics", task_hint="3.3"),
    )
    client_error_type = _load_client_error_type()

    with pytest.raises(client_error_type) as exc_info:
        compute_capm_signal_metrics(
            portfolio_returns=[0.01, -0.005, 0.007],
            benchmark_returns=[0.008, -0.004, 0.006],
            risk_free_rate_annual=None,
            benchmark_symbol="SPY",
            risk_free_source=None,
            annualization_factor=252,
        )

    exception_text = str(exc_info.value).lower()
    assert "risk" in exception_text
    assert "free" in exception_text
