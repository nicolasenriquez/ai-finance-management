"""Fail-first tests for phase-m clustering, anomaly, and quantile forecast contracts."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _load_portfolio_ml_service_module() -> ModuleType:
    """Load portfolio_ml service module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 4.1-4.4 before phase-m ML extension tests can pass.",
        )
        raise AssertionError from exc


def _load_portfolio_ml_routes_module() -> ModuleType:
    """Load portfolio_ml routes module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ml.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.routes. "
            "Task 4.x should keep ML route contracts mounted for phase-m endpoints.",
        )
        raise AssertionError from exc


def _registered_paths() -> set[str]:
    """Return currently registered route paths."""

    return {
        route_path
        for route in app.routes
        for route_path in [getattr(route, "path", None)]
        if isinstance(route_path, str)
    }


def _assert_endpoint_registered(*, path: str, guidance: str) -> None:
    """Fail fast when one required endpoint is not mounted."""

    if path not in _registered_paths():
        pytest.fail(
            "Fail-first baseline: required portfolio_ml endpoint "
            f"{path} is not registered in app.main. {guidance}",
        )


def test_service_exposes_phase_m_clustering_and_anomaly_builders() -> None:
    """Service layer should expose deterministic clustering and anomaly builders."""

    service_module = _load_portfolio_ml_service_module()

    cluster_builder = getattr(service_module, "build_deterministic_cluster_payload", None)
    if cluster_builder is None or not callable(cluster_builder):
        pytest.fail(
            "Fail-first baseline: missing callable build_deterministic_cluster_payload(). "
            "Implement task 4.1 before this test can pass.",
        )

    anomaly_builder = getattr(service_module, "build_deterministic_anomaly_payload", None)
    if anomaly_builder is None or not callable(anomaly_builder):
        pytest.fail(
            "Fail-first baseline: missing callable build_deterministic_anomaly_payload(). "
            "Implement task 4.2 before this test can pass.",
        )


def test_clustering_and_anomaly_payloads_are_deterministic_for_equivalent_snapshot_input() -> None:
    """Equivalent snapshot inputs should produce equivalent cluster and anomaly outputs."""

    service_module = _load_portfolio_ml_service_module()

    cluster_builder_obj = getattr(service_module, "build_deterministic_cluster_payload", None)
    anomaly_builder_obj = getattr(service_module, "build_deterministic_anomaly_payload", None)
    if (
        cluster_builder_obj is None
        or anomaly_builder_obj is None
        or not callable(cluster_builder_obj)
        or not callable(anomaly_builder_obj)
    ):
        pytest.fail(
            "Fail-first baseline: clustering/anomaly deterministic builders are missing. "
            "Implement tasks 4.1 and 4.2 before enabling this test.",
        )

    cluster_builder = cast(Any, cluster_builder_obj)
    anomaly_builder = cast(Any, anomaly_builder_obj)

    snapshot_input = {
        "scope": "portfolio",
        "as_of_ledger_at": "2026-04-06T00:00:00Z",
        "as_of_market_at": "2026-04-06T00:00:00Z",
        "rows": [
            {"instrument_symbol": "AAPL", "return_30d": "0.042", "volatility_30d": "0.021"},
            {"instrument_symbol": "MSFT", "return_30d": "0.038", "volatility_30d": "0.019"},
        ],
    }

    first_cluster_payload = cluster_builder(snapshot_input=snapshot_input)
    second_cluster_payload = cluster_builder(snapshot_input=snapshot_input)
    assert first_cluster_payload == second_cluster_payload

    first_anomaly_payload = anomaly_builder(snapshot_input=snapshot_input)
    second_anomaly_payload = anomaly_builder(snapshot_input=snapshot_input)
    assert first_anomaly_payload == second_anomaly_payload


@pytest.mark.integration
def test_phase_m_ml_endpoints_are_registered() -> None:
    """Phase-m ML extension endpoints should be registered with app router."""

    routes_module = _load_portfolio_ml_routes_module()
    settings = getattr(routes_module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ml.routes.settings is missing. "
            "Task 4.x should keep route-prefix settings available.",
        )

    _assert_endpoint_registered(
        path=f"{settings.api_prefix}/portfolio/ml/clusters",
        guidance="Implement task 4.1 cluster endpoint routing before enabling this test.",
    )
    _assert_endpoint_registered(
        path=f"{settings.api_prefix}/portfolio/ml/anomalies",
        guidance="Implement task 4.2 anomaly endpoint routing before enabling this test.",
    )


@pytest.mark.integration
def test_forecast_endpoint_contract_includes_quantile_percentile_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forecast horizon rows should expose percentile quantile fields for fan rendering."""

    routes_module = _load_portfolio_ml_routes_module()
    settings = getattr(routes_module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ml.routes.settings is missing. "
            "Task 4.4 should keep route-prefix settings available.",
        )
    endpoint_path = f"{settings.api_prefix}/portfolio/ml/forecasts"
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Forecast endpoint must stay mounted while adding quantile fields.",
    )

    async def _fake_quantile_forecast_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "ready",
            "state_reason_code": "ready",
            "state_reason_detail": "forecast_ready",
            "scope": "portfolio",
            "instrument_symbol": None,
            "as_of_ledger_at": "2026-04-06T00:00:00Z",
            "as_of_market_at": "2026-04-06T00:00:00Z",
            "evaluated_at": "2026-04-06T00:00:01Z",
            "freshness_policy": {"max_age_hours": 24},
            "model_snapshot_ref": "portfolio_quantile_boosting_20260406",
            "model_family": "quantile_boosting",
            "training_window_start": "2026-01-01T00:00:00Z",
            "training_window_end": "2026-04-05T00:00:00Z",
            "horizons": [
                {
                    "horizon_id": "h+1",
                    "point_estimate": "0.004200",
                    "lower_bound": "-0.012000",
                    "upper_bound": "0.015000",
                    "confidence_level": "0.80",
                    "model_snapshot_ref": "portfolio_quantile_boosting_20260406",
                    "p10": "-0.012000",
                    "p50": "0.004200",
                    "p90": "0.015000",
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_ml_forecast_response",
        _fake_quantile_forecast_response,
    )

    with TestClient(app) as client:
        response = client.get(endpoint_path, params={"scope": "portfolio"})

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    horizons_obj = payload.get("horizons")
    assert isinstance(horizons_obj, list)
    horizons = cast(list[object], horizons_obj)
    assert len(horizons) == 1
    first_horizon_obj = horizons[0]
    assert isinstance(first_horizon_obj, dict)
    first_horizon = cast(dict[str, object], first_horizon_obj)
    assert "p10" in first_horizon
    assert "p50" in first_horizon
    assert "p90" in first_horizon
