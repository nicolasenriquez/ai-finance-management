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


@pytest.mark.integration
def test_hierarchy_endpoint_contract_includes_grouping_and_provenance_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hierarchy endpoint should expose group metadata and pricing provenance fields."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="hierarchy")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement hierarchy route wiring before enabling this contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_hierarchy_response",
        guidance="Hierarchy route should dispatch to typed service response callable.",
    )

    async def _fake_hierarchy_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "group_by": "sector",
            "pricing_snapshot_key": "snapshot-key",
            "pricing_snapshot_captured_at": "2026-03-28T00:00:00Z",
            "groups": [
                {
                    "group_key": "Technology",
                    "group_label": "Technology",
                    "asset_count": 1,
                    "total_market_value_usd": "120.00",
                    "total_profit_loss_usd": "20.00",
                    "total_change_pct": "20.00",
                    "assets": [
                        {
                            "instrument_symbol": "AAPL",
                            "sector_label": "Technology",
                            "open_quantity": "1.000000000",
                            "open_cost_basis_usd": "100.00",
                            "avg_price_usd": "100.00",
                            "current_price_usd": "120.00",
                            "market_value_usd": "120.00",
                            "profit_loss_usd": "20.00",
                            "change_pct": "20.00",
                            "lot_count": 1,
                            "lots": [
                                {
                                    "lot_id": 1,
                                    "opened_on": "2026-03-20",
                                    "original_qty": "1.000000000",
                                    "remaining_qty": "1.000000000",
                                    "unit_cost_basis_usd": "100.00",
                                    "total_cost_basis_usd": "100.00",
                                    "market_value_usd": "120.00",
                                    "profit_loss_usd": "20.00",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_hierarchy_response",
        _fake_hierarchy_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"group_by": "sector"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["as_of_ledger_at"]
    assert payload["group_by"] == "sector"
    assert payload["pricing_snapshot_key"] == "snapshot-key"
    assert payload["pricing_snapshot_captured_at"]
    assert isinstance(payload["groups"], list)
    assert payload["groups"][0]["group_key"] == "Technology"


@pytest.mark.integration
def test_hierarchy_endpoint_rejects_unsupported_group_by_values() -> None:
    """Hierarchy endpoint should reject unsupported grouping values with 422."""

    endpoint_path = _workspace_endpoint_path(suffix="hierarchy")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement hierarchy route registration before enabling this test.",
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"group_by": "country"},
        )

    assert response.status_code == 422


@pytest.mark.integration
def test_hierarchy_endpoint_rejects_missing_open_positions_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hierarchy endpoint should surface insufficient-data failures as explicit 409 responses."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="hierarchy")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement hierarchy route before enabling this insufficiency contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_hierarchy_response",
        guidance="Hierarchy route should dispatch explicit insufficiency failures.",
    )

    async def _raise_no_positions(**_: Any) -> dict[str, Any]:
        raise PortfolioAnalyticsClientError(
            "No open positions are available for hierarchy rendering.",
            status_code=409,
        )

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_hierarchy_response",
        _raise_no_positions,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"group_by": "sector"},
        )

    assert response.status_code == 409
    assert "No open positions" in str(response.json().get("detail", ""))


@pytest.mark.integration
def test_quant_metrics_endpoint_contract_includes_period_benchmark_and_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quant-metrics endpoint should expose period, benchmark symbol, and metric list."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="quant-metrics")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement QuantStats route wiring before enabling this contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_quant_metrics_response",
        guidance="Quant metrics route should dispatch to typed service response callable.",
    )

    async def _fake_quant_metrics_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "period": "90D",
            "benchmark_symbol": "SP500_PROXY",
            "benchmark_context": {
                "benchmark_symbol": "SP500_PROXY",
                "omitted_metric_ids": [],
                "omission_reason": None,
            },
            "metrics": [
                {
                    "metric_id": "sharpe",
                    "label": "Sharpe Ratio",
                    "description": "Risk-adjusted return ratio.",
                    "value": "1.100000",
                    "display_as": "number",
                },
                {
                    "metric_id": "volatility",
                    "label": "Volatility",
                    "description": "Annualized return volatility estimate.",
                    "value": "0.180000",
                    "display_as": "percent",
                },
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_quant_metrics_response",
        _fake_quant_metrics_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "90D"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["as_of_ledger_at"]
    assert payload["period"] == "90D"
    assert payload["benchmark_symbol"] == "SP500_PROXY"
    assert payload["benchmark_context"]["benchmark_symbol"] == "SP500_PROXY"
    assert payload["benchmark_context"]["omitted_metric_ids"] == []
    assert payload["benchmark_context"]["omission_reason"] is None
    assert isinstance(payload["metrics"], list)
    assert payload["metrics"][0]["metric_id"] == "sharpe"
    assert payload["metrics"][0]["display_as"] == "number"


@pytest.mark.integration
def test_quant_metrics_endpoint_rejects_insufficient_history_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quant-metrics endpoint should reject insufficient history with explicit 409 response."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="quant-metrics")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement QuantStats route before enabling this insufficiency contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_quant_metrics_response",
        guidance="Quant metrics route should dispatch explicit insufficiency failures.",
    )

    async def _raise_insufficient_history(**_: Any) -> dict[str, Any]:
        raise PortfolioAnalyticsClientError(
            "Insufficient persisted history for quant metrics period 90D.",
            status_code=409,
        )

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_quant_metrics_response",
        _raise_insufficient_history,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "90D"},
        )

    assert response.status_code == 409
    assert "Insufficient persisted history" in str(response.json().get("detail", ""))


@pytest.mark.integration
def test_quant_metrics_endpoint_rejects_unsupported_period_values() -> None:
    """Quant-metrics endpoint should reject unsupported chart period values with 422."""

    endpoint_path = _workspace_endpoint_path(suffix="quant-metrics")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement QuantStats period normalization before enabling this test.",
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "13D"},
        )

    assert response.status_code == 422
    assert "supported periods" in str(response.json()).lower()
