"""Fail-first contract tests for upcoming analytics workspace endpoints."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.portfolio_analytics.service import PortfolioAnalyticsClientError


def _load_portfolio_analytics_routes_module() -> ModuleType:
    """Load routes module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_analytics.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.routes. "
            "Implement tasks 2.1-3.2 before workspace endpoint tests can pass.",
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


def _workspace_endpoint_path(*, suffix: str) -> str:
    """Build one workspace endpoint path from configured API prefix."""

    module = _load_portfolio_analytics_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_analytics.routes.settings is missing. "
            "Task 2.1 should expose configured route settings for workspace endpoints.",
        )
    return f"{settings.api_prefix}/portfolio/{suffix}"


def _assert_endpoint_registered(*, path: str, guidance: str) -> None:
    """Fail fast when one required endpoint is not yet mounted."""

    if path not in _registered_paths():
        pytest.fail(
            "Fail-first baseline: required portfolio analytics endpoint "
            f"{path} is not registered in app.main. {guidance}",
        )


def _assert_routes_callable_exists(
    *,
    module: ModuleType,
    callable_name: str,
    guidance: str,
) -> None:
    """Fail if one expected routes-level service callable is missing."""

    if not hasattr(module, callable_name):
        pytest.fail(
            "Fail-first baseline: routes module is missing callable "
            f"'{callable_name}'. {guidance}",
        )


@pytest.mark.integration
def test_time_series_endpoint_contract_includes_provenance_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Time-series endpoint should expose temporal provenance in successful responses."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="time-series")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 before enabling this test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_time_series_response",
        guidance="Task 2.1 should wire the route to a typed service response.",
    )

    async def _fake_time_series_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "period": "30D",
            "frequency": "1D",
            "timezone": "UTC",
            "points": [
                {
                    "captured_at": "2026-03-27T00:00:00Z",
                    "portfolio_value_usd": "1000.00",
                    "pnl_usd": "0.00",
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_time_series_response",
        _fake_time_series_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "30D"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["as_of_ledger_at"]
    assert payload["period"] == "30D"
    assert payload["frequency"] == "1D"
    assert payload["timezone"] == "UTC"
    assert isinstance(payload["points"], list)


@pytest.mark.integration
def test_time_series_endpoint_rejects_insufficient_history_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Time-series endpoint should reject insufficient history with explicit 409 response."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="time-series")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 before enabling this insufficiency contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_time_series_response",
        guidance="Task 2.1 should wire explicit insufficiency failures.",
    )

    async def _raise_insufficient_history(**_: Any) -> dict[str, Any]:
        raise PortfolioAnalyticsClientError(
            "Insufficient persisted history for requested period 252D.",
            status_code=409,
        )

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_time_series_response",
        _raise_insufficient_history,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "252D"},
        )

    assert response.status_code == 409
    assert "Insufficient persisted history" in str(response.json().get("detail", ""))


@pytest.mark.integration
def test_time_series_endpoint_rejects_unsupported_period_explicitly() -> None:
    """Time-series endpoint should reject unsupported period values with explicit detail."""

    endpoint_path = _workspace_endpoint_path(suffix="time-series")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.10 explicit period validation before enabling this test.",
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "45D"},
        )

    assert response.status_code == 422
    assert "supported periods" in str(response.json()).lower()


@pytest.mark.integration
def test_contribution_endpoint_contract_includes_provenance_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contribution endpoint should expose period/as-of provenance in successful responses."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="contribution")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.2 before enabling this test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_contribution_response",
        guidance="Task 2.2 should wire the route to a typed service response.",
    )

    async def _fake_contribution_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "period": "30D",
            "rows": [
                {
                    "instrument_symbol": "AAPL",
                    "contribution_pnl_usd": "12.00",
                    "contribution_pct": "1.20",
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_contribution_response",
        _fake_contribution_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "30D"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["as_of_ledger_at"]
    assert payload["period"] == "30D"
    assert isinstance(payload["rows"], list)
    first_row = payload["rows"][0]
    assert first_row["instrument_symbol"] == "AAPL"
    assert first_row["contribution_pnl_usd"] == "12.00"
    assert first_row["contribution_pct"] == "1.20"


@pytest.mark.integration
def test_contribution_endpoint_normalizes_supported_period_values_before_service_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contribution endpoint should normalize supported period values before dispatch."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="contribution")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.10 before enabling this normalization contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_contribution_response",
        guidance="Task 2.10 should normalize period inputs before service dispatch.",
    )

    captured_period_values: list[str] = []

    async def _fake_contribution_response(**kwargs: Any) -> dict[str, Any]:
        period = kwargs.get("period")
        if period is None or not hasattr(period, "value"):
            raise AssertionError("Normalized period enum value was not passed to service callable.")
        captured_period_values.append(str(period.value))
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "period": str(period.value),
            "rows": [],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_contribution_response",
        _fake_contribution_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "max"},
        )

    assert response.status_code == 200
    assert captured_period_values == ["MAX"]


@pytest.mark.integration
def test_contribution_endpoint_rejects_insufficient_history_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contribution endpoint should reject insufficient history with explicit 409 response."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="contribution")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.2 before enabling this insufficiency contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_contribution_response",
        guidance="Task 2.2 should wire explicit insufficiency failures.",
    )

    async def _raise_insufficient_history(**_: Any) -> dict[str, Any]:
        raise PortfolioAnalyticsClientError(
            "Insufficient persisted history for contribution period 252D.",
            status_code=409,
        )

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_contribution_response",
        _raise_insufficient_history,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "252D"},
        )

    assert response.status_code == 409
    assert "Insufficient persisted history" in str(response.json().get("detail", ""))


@pytest.mark.integration
def test_risk_estimators_endpoint_contract_includes_methodology_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Risk-estimators endpoint should expose explicit methodology metadata fields."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="risk-estimators")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.3 before enabling this risk contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_risk_estimators_response",
        guidance="Task 2.3 should wire the route to a typed risk service response.",
    )

    async def _fake_risk_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "window_days": 30,
            "metrics": [
                {
                    "estimator_id": "volatility_annualized",
                    "value": "0.18",
                    "window_days": 30,
                    "return_basis": "simple",
                    "annualization_basis": {
                        "kind": "trading_days",
                        "value": 252,
                    },
                    "as_of_timestamp": "2026-03-28T00:00:00Z",
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_risk_estimators_response",
        _fake_risk_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"window_days": 30},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["as_of_ledger_at"]
    assert payload["window_days"] == 30
    assert isinstance(payload["metrics"], list)
    first_metric = payload["metrics"][0]
    assert first_metric["estimator_id"] == "volatility_annualized"
    assert first_metric["window_days"] == 30
    assert first_metric["return_basis"] == "simple"
    assert first_metric["annualization_basis"]["kind"] == "trading_days"
    assert first_metric["annualization_basis"]["value"] == 252
    assert first_metric["as_of_timestamp"]


@pytest.mark.integration
def test_risk_estimators_endpoint_rejects_insufficient_history_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Risk-estimators endpoint should reject insufficient history with explicit 409 response."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="risk-estimators")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.3 before enabling this insufficiency contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_risk_estimators_response",
        guidance="Task 2.3 should wire explicit insufficiency failures.",
    )

    async def _raise_insufficient_history(**_: Any) -> dict[str, Any]:
        raise PortfolioAnalyticsClientError(
            "Insufficient persisted history for risk window 252.",
            status_code=409,
        )

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_risk_estimators_response",
        _raise_insufficient_history,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"window_days": 252},
        )

    assert response.status_code == 409
    assert "Insufficient persisted history" in str(response.json().get("detail", ""))
