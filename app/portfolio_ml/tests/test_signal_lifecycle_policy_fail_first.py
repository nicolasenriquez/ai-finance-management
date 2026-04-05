"""Fail-first tests for signal lifecycle state resolution."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib import import_module
from typing import Any, cast

import pytest

ResolveSignalLifecycleStateCallable = Callable[..., Mapping[str, object]]


def _load_portfolio_ml_service_module() -> object:
    """Load portfolio_ml service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 3.1-3.4 before lifecycle policy tests can pass.",
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


def test_lifecycle_resolver_returns_stale_when_source_data_exceeds_freshness_policy() -> None:
    """Lifecycle resolver should return stale with explicit reason when source data is old."""

    resolve_signal_lifecycle_state = cast(
        ResolveSignalLifecycleStateCallable,
        _load_callable("resolve_signal_lifecycle_state", task_hint="3.4"),
    )

    state_payload = resolve_signal_lifecycle_state(
        as_of_ledger_at="2026-04-01T00:00:00Z",
        as_of_market_at="2026-04-01T00:00:00Z",
        evaluated_at="2026-04-03T00:00:00Z",
        freshness_policy_hours=24,
        missing_history_windows=[],
    )

    assert state_payload.get("state") == "stale"
    assert state_payload.get("state_reason_code") == "source_data_stale"


def test_lifecycle_resolver_returns_unavailable_for_insufficient_history() -> None:
    """Lifecycle resolver should return unavailable with factual missing-history metadata."""

    resolve_signal_lifecycle_state = cast(
        ResolveSignalLifecycleStateCallable,
        _load_callable("resolve_signal_lifecycle_state", task_hint="3.4"),
    )

    state_payload = resolve_signal_lifecycle_state(
        as_of_ledger_at="2026-04-01T00:00:00Z",
        as_of_market_at="2026-04-01T00:00:00Z",
        evaluated_at="2026-04-01T00:00:10Z",
        freshness_policy_hours=24,
        missing_history_windows=["90D", "252D"],
    )

    assert state_payload.get("state") == "unavailable"
    assert state_payload.get("state_reason_code") == "insufficient_history"
    reason_detail = state_payload.get("state_reason_detail")
    assert isinstance(reason_detail, str)
    assert "90D" in reason_detail
    assert "252D" in reason_detail
