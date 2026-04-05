"""Fail-first tests for unsupported-model policy enforcement."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

import pytest

EnforceSupportedModelPolicyCallable = Callable[..., str]


def _load_portfolio_ml_service_module() -> object:
    """Load portfolio_ml service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 4.x-5.3 before unsupported-model tests can pass.",
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
            "Implement tasks 3.1/5.3 before this test can pass.",
        )
    return cast(type[Exception], candidate)


def test_supported_model_family_passes_policy_check() -> None:
    """Supported model family values should pass policy check unchanged."""

    enforce_supported_model_policy = cast(
        EnforceSupportedModelPolicyCallable,
        _load_callable("enforce_supported_model_policy", task_hint="5.3"),
    )

    normalized = enforce_supported_model_policy(model_family="ridge_lag_regression")
    assert normalized == "ridge_lag_regression"


def test_unsupported_model_family_rejected_with_explicit_policy_reason() -> None:
    """Unsupported model family values should fail fast with policy reason semantics."""

    enforce_supported_model_policy = cast(
        EnforceSupportedModelPolicyCallable,
        _load_callable("enforce_supported_model_policy", task_hint="5.3"),
    )
    client_error_type = _load_client_error_type()

    with pytest.raises(client_error_type) as exc_info:
        enforce_supported_model_policy(model_family="LSTM")

    exception_text = str(exc_info.value).lower()
    assert "unsupported_model_policy" in exception_text
    assert "lstm" in exception_text
