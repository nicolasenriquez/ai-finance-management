"""Fail-first integration tests for portfolio_ml signal endpoint contracts."""

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
            "Implement tasks 3.1 and 3.5 before signal endpoint tests can pass.",
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


def _signal_endpoint_path() -> str:
    """Build one signal endpoint path from configured API prefix."""

    module = _load_portfolio_ml_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ml.routes.settings is missing. "
            "Task 3.1 should expose configured route settings.",
        )
    return f"{settings.api_prefix}/portfolio/ml/signals"


def _assert_endpoint_registered(*, path: str, guidance: str) -> None:
    """Fail fast when one required endpoint is not yet mounted."""

    if path not in _registered_paths():
        pytest.fail(
            "Fail-first baseline: required portfolio_ml endpoint "
            f"{path} is not registered in app.main. {guidance}",
        )


def _assert_routes_callable_exists(
    *,
    module: ModuleType,
    callable_name: str,
    guidance: str,
) -> None:
    """Fail if one expected routes-level callable is missing."""

    if not hasattr(module, callable_name):
        pytest.fail(
            "Fail-first baseline: portfolio_ml routes module is missing callable "
            f"'{callable_name}'. {guidance}",
        )


@pytest.mark.integration
def test_signal_endpoint_contract_for_portfolio_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Signal endpoint should return frozen lifecycle contract for portfolio scope."""

    routes_module = _load_portfolio_ml_routes_module()
    endpoint_path = _signal_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 3.5 endpoint wiring before enabling this contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_ml_signal_response",
        guidance="Task 3.5 should wire route to typed signal service output.",
    )

    async def _fake_portfolio_signal_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "ready",
            "state_reason_code": "ready",
            "state_reason_detail": "signals_ready",
            "scope": "portfolio",
            "instrument_symbol": None,
            "as_of_ledger_at": "2026-04-01T00:00:00Z",
            "as_of_market_at": "2026-04-01T00:00:00Z",
            "evaluated_at": "2026-04-01T00:00:01Z",
            "freshness_policy": {"max_age_hours": 24},
            "signals": [],
            "capm": {},
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_ml_signal_response",
        _fake_portfolio_signal_response,
    )

    with TestClient(app) as client:
        response = client.get(endpoint_path, params={"scope": "portfolio"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "ready"
    assert payload["scope"] == "portfolio"
    assert payload["instrument_symbol"] is None


@pytest.mark.integration
def test_signal_endpoint_contract_for_instrument_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Signal endpoint should return validated instrument scope metadata and symbol."""

    routes_module = _load_portfolio_ml_routes_module()
    endpoint_path = _signal_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement instrument-scoped signal contract before enabling this test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_ml_signal_response",
        guidance="Task 3.5 should dispatch instrument scope through typed service contract.",
    )

    async def _fake_instrument_signal_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "ready",
            "state_reason_code": "ready",
            "state_reason_detail": "signals_ready",
            "scope": "instrument_symbol",
            "instrument_symbol": "AAPL",
            "as_of_ledger_at": "2026-04-01T00:00:00Z",
            "as_of_market_at": "2026-04-01T00:00:00Z",
            "evaluated_at": "2026-04-01T00:00:01Z",
            "freshness_policy": {"max_age_hours": 24},
            "signals": [],
            "capm": {},
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_ml_signal_response",
        _fake_instrument_signal_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={"scope": "instrument_symbol", "instrument_symbol": "AAPL"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "instrument_symbol"
    assert payload["instrument_symbol"] == "AAPL"


@pytest.mark.integration
def test_signal_endpoint_rejects_instrument_scope_without_symbol() -> None:
    """Signal endpoint should reject instrument scope requests that omit instrument_symbol."""

    endpoint_path = _signal_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement explicit instrument-symbol validation for task 3.5.",
    )

    with TestClient(app) as client:
        response = client.get(endpoint_path, params={"scope": "instrument_symbol"})

    assert response.status_code in {400, 422}
    assert "instrument_symbol" in str(response.json()).lower()
