"""Fail-first tests for walk-forward split correctness and leakage rejection."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

import pytest

BuildWalkForwardSplitsCallable = Callable[..., list[dict[str, int]]]
EnforceNoTemporalLeakageCallable = Callable[..., None]


def _load_portfolio_ml_service_module() -> object:
    """Load portfolio_ml service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 4.1-4.2 before walk-forward tests can pass.",
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
            "Implement task 3.1/4.1 before this test can pass.",
        )
    return cast(type[Exception], candidate)


def test_walk_forward_split_preserves_chronological_boundaries() -> None:
    """Walk-forward splits should always keep train_end <= test_start <= test_end."""

    build_walk_forward_splits = cast(
        BuildWalkForwardSplitsCallable,
        _load_callable("build_walk_forward_splits", task_hint="4.1"),
    )

    splits = build_walk_forward_splits(
        total_points=18,
        min_train_size=10,
        horizon=2,
        step=2,
    )

    assert len(splits) > 0
    for split in splits:
        assert split["train_start"] == 0
        assert split["train_end"] <= split["test_start"]
        assert split["test_start"] < split["test_end"]
        assert split["test_end"] <= 18


def test_walk_forward_leakage_rejection_is_explicit() -> None:
    """Leakage guard should fail fast when test windows overlap training windows."""

    enforce_no_temporal_leakage = cast(
        EnforceNoTemporalLeakageCallable,
        _load_callable("enforce_no_temporal_leakage", task_hint="4.1"),
    )
    client_error_type = _load_client_error_type()

    with pytest.raises(client_error_type) as exc_info:
        enforce_no_temporal_leakage(
            splits=[
                {
                    "train_start": 0,
                    "train_end": 10,
                    "test_start": 9,
                    "test_end": 11,
                }
            ]
        )

    assert "leakage" in str(exc_info.value).lower()
