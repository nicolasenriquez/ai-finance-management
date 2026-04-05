"""Fail-first integration tests for portfolio_ml forecast endpoint contracts."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _load_portfolio_ml_routes_module() -> ModuleType:
    """Load portfolio_ml routes module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ml.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.routes. "
            "Implement tasks 3.1 and 4.5 before forecast endpoint tests can pass.",
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


def _forecast_endpoint_path() -> str:
    """Build one forecast endpoint path from configured API prefix."""

    module = _load_portfolio_ml_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ml.routes.settings is missing. "
            "Task 3.1 should expose configured route settings.",
        )
    return f"{settings.api_prefix}/portfolio/ml/forecasts"


def _assert_endpoint_registered(*, path: str, guidance: str) -> None:
    """Fail fast when one required endpoint is not yet mounted."""

    if path not in _registered_paths():
        pytest.fail(
            "Fail-first baseline: required portfolio_ml endpoint "
            f"{path} is not registered in app.main. {guidance}",
        )


@pytest.mark.integration
def test_forecast_endpoint_contract_returns_probabilistic_horizon_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forecast endpoint should include horizon point/interval metadata in ready state."""

    routes_module = _load_portfolio_ml_routes_module()
    endpoint_path = _forecast_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 4.5 endpoint wiring before enabling this contract test.",
    )

    async def _fake_forecast_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "ready",
            "state_reason_code": "ready",
            "state_reason_detail": "forecast_ready",
            "scope": "portfolio",
            "instrument_symbol": None,
            "as_of_ledger_at": "2026-04-01T00:00:00Z",
            "as_of_market_at": "2026-04-01T00:00:00Z",
            "evaluated_at": "2026-04-01T00:00:01Z",
            "freshness_policy": {"max_age_hours": 24},
            "model_snapshot_ref": "portfolio_ridge_20260401T000001Z",
            "model_family": "ridge_lag_regression",
            "training_window_start": "2025-12-01T00:00:00Z",
            "training_window_end": "2026-03-31T00:00:00Z",
            "horizons": [
                {
                    "horizon_id": "h+1",
                    "point_estimate": "101.50",
                    "lower_bound": "99.50",
                    "upper_bound": "103.50",
                    "confidence_level": "0.80",
                    "model_snapshot_ref": "portfolio_ridge_20260401T000001Z",
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_ml_forecast_response",
        _fake_forecast_response,
    )

    with TestClient(app) as client:
        response = client.get(endpoint_path, params={"scope": "portfolio"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "ready"
    assert len(payload["horizons"]) == 1
    assert payload["horizons"][0]["horizon_id"] == "h+1"
    assert payload["horizons"][0]["confidence_level"] == "0.80"


@pytest.mark.integration
def test_forecast_endpoint_contract_exposes_stale_state_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forecast endpoint should expose stale state with explicit reason metadata."""

    routes_module = _load_portfolio_ml_routes_module()
    endpoint_path = _forecast_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement stale-state contract semantics for task 4.5.",
    )

    async def _fake_stale_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "stale",
            "state_reason_code": "champion_expired",
            "state_reason_detail": "Champion snapshot exceeded 168-hour TTL.",
            "scope": "portfolio",
            "instrument_symbol": None,
            "as_of_ledger_at": "2026-04-01T00:00:00Z",
            "as_of_market_at": "2026-04-01T00:00:00Z",
            "evaluated_at": "2026-04-09T01:00:00Z",
            "freshness_policy": {"max_age_hours": 24},
            "model_snapshot_ref": "portfolio_ridge_20260401T000001Z",
            "model_family": "ridge_lag_regression",
            "training_window_start": "2025-12-01T00:00:00Z",
            "training_window_end": "2026-03-31T00:00:00Z",
            "horizons": [],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_ml_forecast_response",
        _fake_stale_response,
    )

    with TestClient(app) as client:
        response = client.get(endpoint_path, params={"scope": "portfolio"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "stale"
    assert payload["state_reason_code"] == "champion_expired"


@pytest.mark.integration
def test_forecast_endpoint_rejects_instrument_scope_without_symbol() -> None:
    """Forecast endpoint should reject instrument scope requests missing instrument symbol."""

    endpoint_path = _forecast_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement explicit instrument-symbol validation for task 4.5.",
    )

    with TestClient(app) as client:
        response = client.get(endpoint_path, params={"scope": "instrument_symbol"})

    assert response.status_code in {400, 422}
    assert "instrument_symbol" in str(response.json()).lower()
