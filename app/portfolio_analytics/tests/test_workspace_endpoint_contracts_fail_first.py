"""Fail-first contract tests for upcoming analytics workspace endpoints."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.portfolio_analytics.schemas import PortfolioQuantReportGenerateResponse
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
def test_time_series_endpoint_normalizes_instrument_scope_inputs_before_service_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Time-series endpoint should normalize scope/symbol query inputs before service dispatch."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="time-series")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement instrument-scoped time-series support before enabling this test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_time_series_response",
        guidance="Instrument-scoped time-series contract should dispatch through typed service.",
    )

    captured_scope_values: list[str] = []
    captured_symbol_values: list[str | None] = []

    async def _fake_time_series_response(**kwargs: Any) -> dict[str, Any]:
        scope = kwargs.get("scope")
        if scope is None or not hasattr(scope, "value"):
            raise AssertionError("Normalized scope enum value was not passed to service callable.")
        captured_scope_values.append(str(scope.value))
        captured_symbol_values.append(cast(str | None, kwargs.get("instrument_symbol")))
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "period": "MAX",
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
            params={
                "period": "max",
                "scope": "instrument_symbol",
                "instrument_symbol": " voo ",
            },
        )

    assert response.status_code == 200
    assert captured_scope_values == ["instrument_symbol"]
    assert captured_symbol_values == ["VOO"]


@pytest.mark.integration
def test_time_series_endpoint_rejects_instrument_scope_without_symbol_explicitly() -> None:
    """Instrument-scoped time-series requests should fail fast when symbol is missing."""

    endpoint_path = _workspace_endpoint_path(suffix="time-series")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement explicit instrument scope validation for time-series endpoint.",
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={
                "period": "MAX",
                "scope": "instrument_symbol",
            },
        )

    assert response.status_code == 422
    assert "instrument_symbol is required" in str(response.json()).lower()


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
def test_risk_estimators_endpoint_infers_period_from_window_when_period_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Risk-estimators endpoint should infer period metadata from window when period query is omitted."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="risk-estimators")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Risk-estimators route must remain registered for period/window inference.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_risk_estimators_response",
        guidance="Risk-estimators route should dispatch to typed service response callable.",
    )

    captured_period_values: list[str] = []

    async def _fake_risk_response(**kwargs: Any) -> dict[str, Any]:
        normalized_period = kwargs.get("period")
        if normalized_period is None or not hasattr(normalized_period, "value"):
            raise AssertionError(
                "Normalized period enum should be passed when period query parameter is omitted."
            )
        captured_period_values.append(str(normalized_period.value))
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "window_days": int(kwargs.get("window_days", 30)),
            "metrics": [
                {
                    "estimator_id": "beta",
                    "value": "0.920000",
                    "window_days": int(kwargs.get("window_days", 30)),
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
        response_90 = client.get(endpoint_path, params={"window_days": 90})
        response_126 = client.get(endpoint_path, params={"window_days": 126})
        response_default = client.get(endpoint_path)

    assert response_90.status_code == 200
    assert response_126.status_code == 200
    assert response_default.status_code == 200
    assert captured_period_values == ["90D", "6M", "30D"]


@pytest.mark.integration
def test_efficient_frontier_endpoint_contract_exposes_frontier_points_and_weights(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Efficient-frontier endpoint should expose points, diagnostics, and weight vectors."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="efficient-frontier")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement Markowitz efficient-frontier route wiring before enabling this contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_efficient_frontier_response",
        guidance="Efficient-frontier route should dispatch to typed service response callable.",
    )

    async def _fake_efficient_frontier_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "scope": "portfolio",
            "instrument_symbol": None,
            "period": "90D",
            "risk_free_rate_annual": "0.030000",
            "methodology": {
                "optimization_model": "mean_variance_long_only",
                "sampling_method": "dirichlet_mc",
                "annualization_basis": "trading_days_252",
            },
            "frontier_points": [
                {
                    "point_id": "p01",
                    "expected_return": "0.080000",
                    "volatility": "0.140000",
                    "sharpe_ratio": "0.357143",
                    "is_max_sharpe": False,
                    "is_min_volatility": True,
                },
                {
                    "point_id": "p12",
                    "expected_return": "0.120000",
                    "volatility": "0.180000",
                    "sharpe_ratio": "0.500000",
                    "is_max_sharpe": True,
                    "is_min_volatility": False,
                },
            ],
            "asset_points": [
                {
                    "instrument_symbol": "AAPL",
                    "expected_return": "0.130000",
                    "volatility": "0.240000",
                },
                {
                    "instrument_symbol": "VOO",
                    "expected_return": "0.090000",
                    "volatility": "0.160000",
                },
            ],
            "max_sharpe_weights": [
                {"instrument_symbol": "AAPL", "weight": "0.350000"},
                {"instrument_symbol": "VOO", "weight": "0.650000"},
            ],
            "min_volatility_weights": [
                {"instrument_symbol": "AAPL", "weight": "0.120000"},
                {"instrument_symbol": "VOO", "weight": "0.880000"},
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_efficient_frontier_response",
        _fake_efficient_frontier_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "90D"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["as_of_ledger_at"]
    assert payload["scope"] == "portfolio"
    assert payload["period"] == "90D"
    assert payload["methodology"]["optimization_model"] == "mean_variance_long_only"
    assert isinstance(payload["frontier_points"], list)
    assert payload["frontier_points"][0]["point_id"] == "p01"
    assert isinstance(payload["asset_points"], list)
    assert isinstance(payload["max_sharpe_weights"], list)
    assert isinstance(payload["min_volatility_weights"], list)


@pytest.mark.integration
def test_efficient_frontier_endpoint_normalizes_scope_and_symbol_before_service_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Efficient-frontier endpoint should normalize scope and symbol query values."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="efficient-frontier")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement efficient-frontier route registration before enabling this normalization test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_efficient_frontier_response",
        guidance="Efficient-frontier route should dispatch to typed service response callable.",
    )

    captured_scope_values: list[str] = []
    captured_symbol_values: list[str | None] = []
    captured_period_values: list[str] = []

    async def _fake_efficient_frontier_response(**kwargs: Any) -> dict[str, Any]:
        normalized_scope = kwargs.get("scope")
        normalized_period = kwargs.get("period")
        if normalized_scope is None or not hasattr(normalized_scope, "value"):
            raise AssertionError("Normalized scope enum value was not passed to service callable.")
        if normalized_period is None or not hasattr(normalized_period, "value"):
            raise AssertionError("Normalized period enum value was not passed to service callable.")
        captured_scope_values.append(str(normalized_scope.value))
        captured_symbol_values.append(cast(str | None, kwargs.get("instrument_symbol")))
        captured_period_values.append(str(normalized_period.value))
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "scope": str(normalized_scope.value),
            "instrument_symbol": cast(str | None, kwargs.get("instrument_symbol")),
            "period": str(normalized_period.value),
            "risk_free_rate_annual": "0.030000",
            "methodology": {
                "optimization_model": "mean_variance_long_only",
                "sampling_method": "dirichlet_mc",
                "annualization_basis": "trading_days_252",
            },
            "frontier_points": [],
            "asset_points": [],
            "max_sharpe_weights": [],
            "min_volatility_weights": [],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_efficient_frontier_response",
        _fake_efficient_frontier_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={
                "period": "max",
                "scope": "instrument_symbol",
                "instrument_symbol": " voo ",
            },
        )

    assert response.status_code == 200
    assert captured_period_values == ["MAX"]
    assert captured_scope_values == ["instrument_symbol"]
    assert captured_symbol_values == ["VOO"]


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


@pytest.mark.integration
def test_quant_report_generation_rejects_home_route_context_fields_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quant-report generation should reject Home-route context fields not in typed contract."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="quant-reports")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.3 before enabling this route-agnostic contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="generate_portfolio_quant_report_response",
        guidance="Task 2.3 should keep report generation route-agnostic and typed.",
    )

    async def _fake_generate_response(**_: Any) -> PortfolioQuantReportGenerateResponse:
        return PortfolioQuantReportGenerateResponse.model_validate(
            {
                "report_id": "report-001",
                "report_url_path": "/api/portfolio/quant-reports/report-001",
                "scope": "portfolio",
                "instrument_symbol": None,
                "period": "30D",
                "benchmark_symbol": "SP500_PROXY",
                "generated_at": "2026-03-28T00:00:00Z",
                "expires_at": "2026-03-28T01:00:00Z",
            }
        )

    monkeypatch.setattr(
        routes_module,
        "generate_portfolio_quant_report_response",
        _fake_generate_response,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "scope": "portfolio",
                "period": "30D",
                "home_route_context": "workspace-home",
            },
        )

    assert response.status_code == 422
    assert "home_route_context" in str(response.json()).lower()


@pytest.mark.integration
def test_quant_report_generation_exposes_explicit_lifecycle_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quant-report generation should expose explicit lifecycle metadata for promoted UX."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="quant-reports")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.3 before enabling lifecycle metadata contract checks.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="generate_portfolio_quant_report_response",
        guidance="Task 2.3 should expose explicit lifecycle metadata for promoted Quant/Reports UX.",
    )

    async def _fake_generate_response(**_: Any) -> PortfolioQuantReportGenerateResponse:
        return PortfolioQuantReportGenerateResponse.model_validate(
            {
                "report_id": "report-001",
                "report_url_path": "/api/portfolio/quant-reports/report-001",
                "scope": "portfolio",
                "instrument_symbol": None,
                "period": "30D",
                "benchmark_symbol": "SP500_PROXY",
                "generated_at": "2026-03-28T00:00:00Z",
                "expires_at": "2026-03-28T01:00:00Z",
                "lifecycle_status": "ready",
            }
        )

    monkeypatch.setattr(
        routes_module,
        "generate_portfolio_quant_report_response",
        _fake_generate_response,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "scope": "portfolio",
                "period": "30D",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["lifecycle_status"] == "ready"


@pytest.mark.integration
def test_risk_evolution_endpoint_contract_includes_drawdown_and_rolling_series(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Risk-evolution endpoint should expose chart-ready drawdown and rolling series."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="risk-evolution")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.2 before enabling risk-evolution contracts.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_risk_evolution_response",
        guidance="Task 2.2 should wire risk-evolution route to typed service response.",
    )

    async def _fake_risk_evolution_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "scope": "instrument_symbol",
            "instrument_symbol": "VOO",
            "period": "252D",
            "rolling_window_days": 30,
            "methodology": {
                "drawdown_method": "running_peak_relative_decline",
                "rolling_volatility_method": "rolling_std_x_sqrt_252",
                "rolling_beta_method": "rolling_covariance_div_variance",
            },
            "drawdown_path_points": [
                {"captured_at": "2026-03-20T00:00:00Z", "drawdown": "-0.020000"},
                {"captured_at": "2026-03-21T00:00:00Z", "drawdown": "-0.018000"},
            ],
            "rolling_points": [
                {
                    "captured_at": "2026-03-20T00:00:00Z",
                    "volatility_annualized": "0.210000",
                    "beta": "0.920000",
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_risk_evolution_response",
        _fake_risk_evolution_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={
                "period": "252D",
                "scope": "instrument_symbol",
                "instrument_symbol": " voo ",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "instrument_symbol"
    assert payload["instrument_symbol"] == "VOO"
    assert payload["period"] == "252D"
    assert payload["rolling_window_days"] == 30
    assert isinstance(payload["drawdown_path_points"], list)
    assert isinstance(payload["rolling_points"], list)
    assert payload["methodology"]["drawdown_method"]


@pytest.mark.integration
def test_return_distribution_endpoint_contract_exposes_bucket_policy_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return-distribution endpoint should expose deterministic bucket policy metadata."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="return-distribution")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.2 before enabling return-distribution contracts.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_return_distribution_response",
        guidance="Task 2.2 should wire return-distribution route to typed service response.",
    )

    async def _fake_distribution_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "scope": "portfolio",
            "instrument_symbol": None,
            "period": "90D",
            "sample_size": 89,
            "bucket_policy": {
                "method": "equal_width",
                "bin_count": 12,
                "min_return": "-0.061200",
                "max_return": "0.047300",
            },
            "buckets": [
                {
                    "bucket_index": 0,
                    "lower_bound": "-0.061200",
                    "upper_bound": "-0.052000",
                    "count": 2,
                    "frequency": "0.022472",
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_return_distribution_response",
        _fake_distribution_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "90D"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "portfolio"
    assert payload["instrument_symbol"] is None
    assert payload["bucket_policy"]["method"] == "equal_width"
    assert payload["bucket_policy"]["bin_count"] == 12
    assert isinstance(payload["buckets"], list)


@pytest.mark.integration
def test_monte_carlo_endpoint_contract_exposes_effective_parameters_and_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monte Carlo endpoint should expose effective envelope and summary payload shape."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="monte-carlo")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 before enabling Monte Carlo endpoint contracts.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="generate_portfolio_monte_carlo_response",
        guidance="Task 2.1 should wire Monte Carlo route to typed service response.",
    )

    async def _fake_monte_carlo_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "scope": "portfolio",
            "instrument_symbol": None,
            "period": "90D",
            "simulation": {
                "sims": 1000,
                "horizon_days": 90,
                "seed": 20260330,
                "bust_threshold": "-0.200000",
                "goal_threshold": "0.300000",
            },
            "assumptions": {
                "model": "quantstats_shuffled_returns",
                "notes": [
                    "Simulation shuffles historical simple returns.",
                    "Monte Carlo output is scenario-based and not predictive.",
                ],
            },
            "summary": {
                "start_value_usd": "12668.08",
                "median_ending_value_usd": "13214.90",
                "mean_ending_return": "0.042100",
                "bust_probability": "0.083000",
                "goal_probability": "0.312000",
                "interpretation_signal": "balanced",
            },
            "ending_return_percentiles": [
                {"percentile": 5, "value": "-0.190000"},
                {"percentile": 50, "value": "0.040000"},
                {"percentile": 95, "value": "0.280000"},
            ],
            "profile_comparison_enabled": True,
            "calibration_context": {
                "requested_basis": "monthly",
                "effective_basis": "monthly",
                "sample_size": 30,
                "lookback_start": "2023-01-31T00:00:00Z",
                "lookback_end": "2025-06-30T00:00:00Z",
                "used_fallback": False,
                "fallback_reason": None,
            },
            "profile_scenarios": [
                {
                    "profile_id": "conservative",
                    "label": "Conservative",
                    "bust_threshold": "-0.100000",
                    "goal_threshold": "0.120000",
                    "bust_probability": "0.120000",
                    "goal_probability": "0.420000",
                    "interpretation_signal": "balanced",
                },
                {
                    "profile_id": "balanced",
                    "label": "Balanced",
                    "bust_threshold": "-0.200000",
                    "goal_threshold": "0.270000",
                    "bust_probability": "0.083000",
                    "goal_probability": "0.312000",
                    "interpretation_signal": "balanced",
                },
                {
                    "profile_id": "growth",
                    "label": "Growth",
                    "bust_threshold": "-0.300000",
                    "goal_threshold": "0.450000",
                    "bust_probability": "0.041000",
                    "goal_probability": "0.210000",
                    "interpretation_signal": "balanced",
                },
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "generate_portfolio_monte_carlo_response",
        _fake_monte_carlo_response,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "scope": "portfolio",
                "period": "90D",
                "sims": 1000,
                "horizon_days": 90,
                "bust_threshold": -0.2,
                "goal_threshold": 0.3,
                "seed": 20260330,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "portfolio"
    assert payload["simulation"]["sims"] == 1000
    assert payload["simulation"]["horizon_days"] == 90
    assert payload["simulation"]["seed"] == 20260330
    assert payload["summary"]["median_ending_value_usd"]
    assert isinstance(payload["ending_return_percentiles"], list)
    assert payload["profile_comparison_enabled"] is True
    assert payload["calibration_context"]["effective_basis"] == "monthly"
    assert [row["profile_id"] for row in payload["profile_scenarios"]] == [
        "conservative",
        "balanced",
        "growth",
    ]


@pytest.mark.integration
def test_monte_carlo_endpoint_rejects_out_of_bounds_simulation_count() -> None:
    """Monte Carlo endpoint should reject requests outside bounded sims envelope."""

    endpoint_path = _workspace_endpoint_path(suffix="monte-carlo")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 parameter-envelope validation before this test can pass.",
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "scope": "portfolio",
                "period": "90D",
                "sims": 100,
            },
        )

    assert response.status_code == 422
    assert "sims" in str(response.json()).lower()


@pytest.mark.integration
def test_monte_carlo_endpoint_rejects_unsupported_calibration_basis() -> None:
    """Monte Carlo endpoint should reject calibration basis values outside approved enum."""

    endpoint_path = _workspace_endpoint_path(suffix="monte-carlo")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 7.2 validation contract for calibration basis.",
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "scope": "portfolio",
                "period": "90D",
                "sims": 1000,
                "calibration_basis": "weekly",
            },
        )

    assert response.status_code == 422
    assert "calibration_basis" in str(response.json()).lower()


@pytest.mark.integration
def test_monte_carlo_endpoint_is_deterministic_for_equivalent_seed_and_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Equivalent seed + input should produce deterministic payload output."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="monte-carlo")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.3 deterministic-seed contract before this test can pass.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="generate_portfolio_monte_carlo_response",
        guidance="Task 2.3 should route deterministic Monte Carlo seed handling through service.",
    )

    async def _fake_monte_carlo_response(**kwargs: Any) -> dict[str, Any]:
        request = kwargs.get("request")
        seed = getattr(request, "seed", None)
        if seed is None:
            raise AssertionError("Monte Carlo request seed should be available in typed request.")
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "scope": "portfolio",
            "instrument_symbol": None,
            "period": "90D",
            "simulation": {
                "sims": 1000,
                "horizon_days": 90,
                "seed": seed,
                "bust_threshold": None,
                "goal_threshold": None,
            },
            "assumptions": {
                "model": "quantstats_shuffled_returns",
                "notes": ["Deterministic seed-enabled simulation."],
            },
            "summary": {
                "start_value_usd": "100.00",
                "median_ending_value_usd": "103.00",
                "mean_ending_return": "0.030000",
                "bust_probability": None,
                "goal_probability": None,
                "interpretation_signal": "monitor",
            },
            "ending_return_percentiles": [
                {"percentile": 50, "value": "0.030000"},
            ],
            "profile_comparison_enabled": True,
            "calibration_context": {
                "requested_basis": "manual",
                "effective_basis": "manual",
                "sample_size": 90,
                "lookback_start": "2026-01-01T00:00:00Z",
                "lookback_end": "2026-03-28T00:00:00Z",
                "used_fallback": False,
                "fallback_reason": None,
            },
            "profile_scenarios": [
                {
                    "profile_id": "conservative",
                    "label": "Conservative",
                    "bust_threshold": "-0.120000",
                    "goal_threshold": "0.100000",
                    "bust_probability": "0.200000",
                    "goal_probability": "0.450000",
                    "interpretation_signal": "balanced",
                },
                {
                    "profile_id": "balanced",
                    "label": "Balanced",
                    "bust_threshold": "-0.200000",
                    "goal_threshold": "0.180000",
                    "bust_probability": "0.140000",
                    "goal_probability": "0.390000",
                    "interpretation_signal": "balanced",
                },
                {
                    "profile_id": "growth",
                    "label": "Growth",
                    "bust_threshold": "-0.300000",
                    "goal_threshold": "0.330000",
                    "bust_probability": "0.080000",
                    "goal_probability": "0.290000",
                    "interpretation_signal": "balanced",
                },
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "generate_portfolio_monte_carlo_response",
        _fake_monte_carlo_response,
    )

    request_payload = {
        "scope": "portfolio",
        "period": "90D",
        "sims": 1000,
        "horizon_days": 90,
        "seed": 20260330,
    }

    with TestClient(app) as client:
        first_response = client.post(endpoint_path, json=request_payload)
        second_response = client.post(endpoint_path, json=request_payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()


@pytest.mark.integration
def test_monte_carlo_endpoint_surfaces_insufficient_history_as_explicit_409(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monte Carlo endpoint should surface insufficient-history failures explicitly."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="monte-carlo")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.3 insufficiency contract before enabling this test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="generate_portfolio_monte_carlo_response",
        guidance="Task 2.3 should expose explicit insufficiency failures from service layer.",
    )

    async def _raise_insufficient_history(**_: Any) -> dict[str, Any]:
        raise PortfolioAnalyticsClientError(
            "Insufficient persisted history for Monte Carlo horizon 252 days.",
            status_code=409,
        )

    monkeypatch.setattr(
        routes_module,
        "generate_portfolio_monte_carlo_response",
        _raise_insufficient_history,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={"scope": "portfolio", "period": "252D", "horizon_days": 252},
        )

    assert response.status_code == 409
    assert "insufficient persisted history" in str(response.json()).lower()


@pytest.mark.integration
def test_health_synthesis_endpoint_contract_returns_required_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Health synthesis endpoint should expose deterministic summary payload shape."""

    routes_module = _load_portfolio_analytics_routes_module()
    endpoint_path = _workspace_endpoint_path(suffix="health-synthesis")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 8.2 before enabling this health contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_health_synthesis_response",
        guidance="Task 8.2 should wire health synthesis route to typed service contract.",
    )

    async def _fake_health_response(**_: Any) -> dict[str, Any]:
        return {
            "as_of_ledger_at": "2026-03-28T00:00:00Z",
            "scope": "portfolio",
            "instrument_symbol": None,
            "period": "90D",
            "profile_posture": "balanced",
            "health_score": 74,
            "health_label": "healthy",
            "threshold_policy_version": "health_v1_20260330",
            "pillars": [
                {
                    "pillar_id": "growth",
                    "label": "Growth",
                    "score": 80,
                    "status": "favorable",
                    "metrics": [
                        {
                            "metric_id": "cagr",
                            "label": "CAGR",
                            "value_display": "+14.00%",
                            "score": 80,
                            "contribution": "supporting",
                        }
                    ],
                }
            ],
            "key_drivers": [
                {
                    "metric_id": "cagr",
                    "label": "CAGR",
                    "direction": "supporting",
                    "impact_points": 60,
                    "rationale": "Growth output is strong versus long-term target bands.",
                    "value_display": "+14.00%",
                }
            ],
            "health_caveats": [
                "Health synthesis supports interpretation and is not financial advice."
            ],
            "core_metric_ids": ["cagr", "max_drawdown", "sharpe_ratio"],
            "advanced_metric_ids": ["value_at_risk_95"],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_health_synthesis_response",
        _fake_health_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={
                "period": "90D",
                "scope": "portfolio",
                "profile_posture": "balanced",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["health_score"] == 74
    assert payload["health_label"] == "healthy"
    assert payload["profile_posture"] == "balanced"
    assert isinstance(payload["pillars"], list)
    assert isinstance(payload["key_drivers"], list)
    assert isinstance(payload["health_caveats"], list)


@pytest.mark.integration
def test_health_synthesis_endpoint_rejects_instrument_scope_without_symbol() -> None:
    """Instrument-scoped health synthesis requests should fail fast without symbol."""

    endpoint_path = _workspace_endpoint_path(suffix="health-synthesis")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 8.2 explicit scope validation before enabling this test.",
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"period": "90D", "scope": "instrument_symbol"},
        )

    assert response.status_code == 422
    assert "instrument_symbol is required" in str(response.json()).lower()
