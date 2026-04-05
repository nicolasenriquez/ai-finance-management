"""Fail-first tests for baseline comparison and champion promotion policy gates."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from importlib import import_module
from typing import Any, cast

import pytest

EvaluateForecastPromotionPolicyCallable = Callable[..., dict[str, object]]
SelectChampionForecastSnapshotCallable = Callable[..., dict[str, object]]
ResolveForecastLifecycleStateCallable = Callable[..., dict[str, object]]


def _load_portfolio_ml_service_module() -> object:
    """Load portfolio_ml service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 4.2-4.4 before forecast policy tests can pass.",
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


def test_forecast_policy_accepts_candidate_that_beats_naive_and_calibrates() -> None:
    """Promotion policy should pass when candidate improves wMAPE and coverage is calibrated."""

    evaluate_forecast_promotion_policy = cast(
        EvaluateForecastPromotionPolicyCallable,
        _load_callable("evaluate_forecast_promotion_policy", task_hint="4.3"),
    )

    policy_result = evaluate_forecast_promotion_policy(
        candidate_wmape_by_horizon=[0.090, 0.095, 0.100],
        naive_wmape_by_horizon=[0.100, 0.105, 0.110],
        interval_coverage=0.80,
    )

    assert policy_result["qualified"] is True
    assert policy_result["reason_code"] == "qualified"


def test_forecast_policy_rejects_candidate_with_interval_miscalibration() -> None:
    """Promotion policy should reject candidates outside interval coverage bounds."""

    evaluate_forecast_promotion_policy = cast(
        EvaluateForecastPromotionPolicyCallable,
        _load_callable("evaluate_forecast_promotion_policy", task_hint="4.3"),
    )

    policy_result = evaluate_forecast_promotion_policy(
        candidate_wmape_by_horizon=[0.090, 0.095, 0.100],
        naive_wmape_by_horizon=[0.100, 0.105, 0.110],
        interval_coverage=0.65,
    )

    assert policy_result["qualified"] is False
    assert policy_result["reason_code"] == "interval_calibration_failed"


def test_champion_expiry_returns_stale_lifecycle_state() -> None:
    """Expired champion snapshots should resolve to stale forecast lifecycle state."""

    select_champion_forecast_snapshot = cast(
        SelectChampionForecastSnapshotCallable,
        _load_callable("select_champion_forecast_snapshot", task_hint="4.4"),
    )
    resolve_forecast_lifecycle_state = cast(
        ResolveForecastLifecycleStateCallable,
        _load_callable("resolve_forecast_lifecycle_state", task_hint="4.4"),
    )

    evaluated_at = datetime(2026, 4, 5, 0, 0, tzinfo=UTC)
    policy_result = {
        "qualified": True,
        "reason_code": "qualified",
        "reason_detail": "candidate_meets_policy",
        "improvement_pct": 6.0,
    }
    horizons = [
        {
            "horizon_id": "h+1",
            "point_estimate": "101.00",
            "lower_bound": "99.00",
            "upper_bound": "103.00",
            "confidence_level": "0.80",
        }
    ]

    champion = select_champion_forecast_snapshot(
        scope="portfolio",
        instrument_symbol=None,
        model_family="ridge_lag_regression",
        horizons=horizons,
        policy_result=policy_result,
        evaluated_at=evaluated_at,
    )
    lifecycle = resolve_forecast_lifecycle_state(
        champion_snapshot=champion,
        evaluated_at=evaluated_at + timedelta(hours=169),
    )

    assert lifecycle["state"] == "stale"
    assert lifecycle["state_reason_code"] == "champion_expired"
