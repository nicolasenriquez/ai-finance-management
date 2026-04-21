"""Fail-first contract tests for upcoming portfolio AI copilot chat endpoint."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _load_portfolio_ai_routes_module() -> ModuleType:
    """Load routes module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ai_copilot.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.routes. "
            "Implement tasks 2.1-3.2 before copilot route tests can pass.",
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


def _copilot_endpoint_path(*, suffix: str) -> str:
    """Build one copilot endpoint path from configured API prefix."""

    module = _load_portfolio_ai_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ai_copilot.routes.settings is missing. "
            "Task 2.1 should expose configured route settings for copilot endpoints.",
        )
    return f"{settings.api_prefix}/portfolio/{suffix}"


def _assert_endpoint_registered(*, path: str, guidance: str) -> None:
    """Fail fast when one required endpoint is not yet mounted."""

    if path not in _registered_paths():
        pytest.fail(
            "Fail-first baseline: required portfolio copilot endpoint "
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
            "Fail-first baseline: copilot routes module is missing callable "
            f"'{callable_name}'. {guidance}",
        )


def test_chat_endpoint_contract_returns_typed_ready_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Copilot chat endpoint should return typed ready payload fields."""

    routes_module = _load_portfolio_ai_routes_module()
    endpoint_path = _copilot_endpoint_path(suffix="copilot/chat")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 before enabling this contract test.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_copilot_chat_response",
        guidance="Task 2.1 should wire chat route to a typed service response.",
    )

    async def _fake_chat_ready_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "ready",
            "answer_text": "Portfolio drawdown widened over 30D while contribution concentration increased.",
            "evidence": [
                {
                    "tool_id": "portfolio_risk_evolution",
                    "metric_id": "drawdown_path_points",
                }
            ],
            "limitations": [
                "Read-only analytical copilot; no trade execution.",
                "Not financial advice.",
            ],
            "reason_code": None,
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_copilot_chat_response",
        _fake_chat_ready_response,
    )

    request_payload: dict[str, object] = {
        "operation": "chat",
        "messages": [
            {"role": "user", "content": "Explain portfolio movement over 30D."},
        ],
        "period": "30D",
        "scope": "portfolio",
    }

    with TestClient(app) as client:
        response = client.post(endpoint_path, json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "ready"
    assert isinstance(payload["answer_text"], str)
    assert payload["answer_text"]
    assert isinstance(payload["evidence"], list)
    assert isinstance(payload["limitations"], list)
    assert payload.get("reason_code") in {None, ""}


def test_chat_endpoint_rejects_request_history_above_v1_bound() -> None:
    """Copilot chat endpoint should reject history larger than frozen max prior turns."""

    endpoint_path = _copilot_endpoint_path(suffix="copilot/chat")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 request validation before this test can pass.",
    )

    excessive_messages = [
        {"role": "user", "content": f"Turn {turn_index}"} for turn_index in range(10)
    ]

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "operation": "chat",
                "messages": excessive_messages,
            },
        )

    assert response.status_code in {400, 422}
    assert "8" in str(response.json()).lower()


def test_chat_endpoint_contract_surfaces_blocked_state_with_reason_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blocked copilot responses should expose one machine-readable reason code."""

    routes_module = _load_portfolio_ai_routes_module()
    endpoint_path = _copilot_endpoint_path(suffix="copilot/chat")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 blocked-state contract before this test can pass.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_copilot_chat_response",
        guidance="Task 2.1 should keep blocked responses typed.",
    )

    async def _fake_chat_blocked_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "blocked",
            "answer_text": "",
            "evidence": [],
            "limitations": ["Request is outside v1 safety boundary."],
            "reason_code": "boundary_restricted",
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_copilot_chat_response",
        _fake_chat_blocked_response,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "operation": "chat",
                "messages": [
                    {"role": "user", "content": "Buy TSLA now and guarantee gains."}
                ],
            },
        )

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    assert payload.get("state") == "blocked"
    assert payload.get("reason_code") == "boundary_restricted"


def test_chat_endpoint_contract_surfaces_error_state_with_reason_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error copilot responses should expose one machine-readable reason code."""

    routes_module = _load_portfolio_ai_routes_module()
    endpoint_path = _copilot_endpoint_path(suffix="copilot/chat")
    _assert_endpoint_registered(
        path=endpoint_path,
        guidance="Implement task 2.1 error-state contract before this test can pass.",
    )
    _assert_routes_callable_exists(
        module=routes_module,
        callable_name="get_portfolio_copilot_chat_response",
        guidance="Task 2.1 should keep error responses typed.",
    )

    async def _fake_chat_error_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "error",
            "answer_text": "",
            "evidence": [],
            "limitations": ["Provider was unavailable for this request."],
            "reason_code": "provider_unavailable",
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_copilot_chat_response",
        _fake_chat_error_response,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "operation": "chat",
                "messages": [
                    {"role": "user", "content": "Summarize current risk posture."}
                ],
            },
        )

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    assert payload.get("state") == "error"
    assert payload.get("reason_code") == "provider_unavailable"
