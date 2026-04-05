"""Fail-first integration tests for portfolio_ml model-registry endpoint contracts."""

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
            "Implement tasks 3.1 and 5.4 before registry endpoint tests can pass.",
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


def _registry_endpoint_path() -> str:
    """Build one registry endpoint path from configured API prefix."""

    module = _load_portfolio_ml_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ml.routes.settings is missing. "
            "Task 3.1 should expose configured route settings.",
        )
    return f"{settings.api_prefix}/portfolio/ml/registry"


def _assert_endpoint_registered(*, path: str, guidance: str) -> None:
    """Fail fast when one required endpoint is not yet mounted."""

    if path not in _registered_paths():
        pytest.fail(
            "Fail-first baseline: required portfolio_ml endpoint "
            f"{path} is not registered in app.main. {guidance}",
        )


@pytest.mark.integration
def test_registry_endpoint_contract_returns_lineage_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registry endpoint should return typed lineage rows and lifecycle metadata."""

    routes_module = _load_portfolio_ml_routes_module()
    endpoint_path = _registry_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 5.4 endpoint wiring before enabling this contract test.",
    )

    async def _fake_registry_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "ready",
            "state_reason_code": "ready",
            "state_reason_detail": "registry_rows_available",
            "as_of_ledger_at": "2026-04-01T00:00:00Z",
            "as_of_market_at": "2026-04-01T00:00:00Z",
            "evaluated_at": "2026-04-01T00:00:01Z",
            "rows": [
                {
                    "snapshot_ref": "portfolio_ridge_20260401T000001Z",
                    "scope": "portfolio",
                    "instrument_symbol": None,
                    "model_family": "ridge_lag_regression",
                    "lifecycle_state": "ready",
                    "feature_set_hash": "feat_hash_v1",
                    "data_window_start": "2025-12-01T00:00:00Z",
                    "data_window_end": "2026-03-31T00:00:00Z",
                    "run_status": "completed",
                    "promoted_at": "2026-04-01T00:00:01Z",
                    "expires_at": "2026-04-08T00:00:01Z",
                    "replaced_snapshot_ref": None,
                    "policy_result": {"qualified": True},
                    "metric_vector": {"wmape": 0.09},
                    "baseline_comparator_metrics": {"naive_wmape": 0.10},
                }
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_ml_registry_response",
        _fake_registry_response,
    )

    with TestClient(app) as client:
        response = client.get(endpoint_path)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "ready"
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["model_family"] == "ridge_lag_regression"


@pytest.mark.integration
def test_registry_endpoint_contract_supports_filter_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registry endpoint should allow scope/model/lifecycle filters for audit queries."""

    routes_module = _load_portfolio_ml_routes_module()
    endpoint_path = _registry_endpoint_path()
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement filter-aware registry contract for task 5.2/5.4.",
    )

    captured_scope_values: list[str | None] = []
    captured_model_family_values: list[str | None] = []
    captured_lifecycle_state_values: list[str | None] = []

    async def _fake_registry_response(**kwargs: Any) -> dict[str, Any]:
        captured_scope_values.append(kwargs.get("scope"))
        captured_model_family_values.append(kwargs.get("model_family"))
        captured_lifecycle_state_values.append(kwargs.get("lifecycle_state"))
        return {
            "state": "ready",
            "state_reason_code": "ready",
            "state_reason_detail": "registry_rows_available",
            "as_of_ledger_at": "2026-04-01T00:00:00Z",
            "as_of_market_at": "2026-04-01T00:00:00Z",
            "evaluated_at": "2026-04-01T00:00:01Z",
            "rows": [],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_ml_registry_response",
        _fake_registry_response,
    )

    with TestClient(app) as client:
        response = client.get(
            endpoint_path,
            params={
                "scope": "portfolio",
                "model_family": "ridge_lag_regression",
                "lifecycle_state": "ready",
            },
        )

    assert response.status_code == 200
    assert captured_scope_values == ["portfolio"]
    assert captured_model_family_values == ["ridge_lag_regression"]
    assert captured_lifecycle_state_values == ["ready"]
