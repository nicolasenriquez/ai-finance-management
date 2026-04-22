"""Fail-first tests for phase-i copilot ML contract extensions."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _load_routes_module() -> ModuleType:
    """Load portfolio copilot routes module with fail-first guidance."""

    try:
        return import_module("app.portfolio_ai_copilot.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.routes. "
            "Implement tasks 7.1-7.6 before ML contract extension tests can pass.",
        )
        raise AssertionError from exc


def _load_service_module() -> ModuleType:
    """Load portfolio copilot service module with fail-first guidance."""

    try:
        return import_module("app.portfolio_ai_copilot.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.service. "
            "Implement tasks 7.1-7.6 before ML contract extension tests can pass.",
        )
        raise AssertionError from exc


def _copilot_chat_path() -> str:
    """Build copilot chat endpoint path from configured API prefix."""

    routes_module = _load_routes_module()
    settings = getattr(routes_module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ai_copilot.routes.settings is missing. "
            "Task 7.1 should keep route-prefix settings available.",
        )
    return f"{settings.api_prefix}/portfolio/copilot/chat"


@pytest.mark.integration
def test_chat_endpoint_accepts_document_ids_and_returns_prompt_suggestions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Copilot chat contract should support bounded document references and suggestions."""

    routes_module = _load_routes_module()
    endpoint_path = _copilot_chat_path()

    captured_document_ids: list[list[int] | None] = []

    async def _fake_chat_response(**kwargs: Any) -> dict[str, Any]:
        request = kwargs.get("request")
        captured_document_ids.append(getattr(request, "document_ids", None))
        return {
            "state": "ready",
            "answer_text": "CAPM beta moved higher while forecast state stayed ready.",
            "evidence": [
                {
                    "tool_id": "portfolio_ml_forecasts",
                    "metric_id": "horizons",
                    "as_of_ledger_at": "2026-04-05T00:00:00Z",
                },
            ],
            "limitations": [
                "Read-only analytical copilot; no trade execution.",
                "Responses are informational only and not financial advice.",
            ],
            "reason_code": None,
            "prompt_suggestions": [
                "Show the latest portfolio ML registry state.",
                "Explain why the forecast could become stale.",
            ],
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_copilot_chat_response",
        _fake_chat_response,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "operation": "chat",
                "messages": [
                    {
                        "role": "user",
                        "content": "Use document references and summarize ML state.",
                    },
                ],
                "scope": "portfolio",
                "period": "90D",
                "document_ids": [101, 102],
            },
        )

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    assert captured_document_ids == [[101, 102]]
    assert payload.get("state") == "ready"
    evidence_obj = payload.get("evidence")
    assert isinstance(evidence_obj, list)
    evidence = cast(list[object], evidence_obj)

    def _is_portfolio_ml_evidence_row(row_obj: object) -> bool:
        if not isinstance(row_obj, dict):
            return False
        row = cast(dict[str, object], row_obj)
        tool_id = row.get("tool_id")
        if not isinstance(tool_id, str):
            return False
        return tool_id.startswith("portfolio_ml_")

    assert any(_is_portfolio_ml_evidence_row(row) for row in evidence)
    prompt_suggestions_obj = payload.get("prompt_suggestions")
    assert isinstance(prompt_suggestions_obj, list)
    prompt_suggestions = cast(list[object], prompt_suggestions_obj)
    assert len(prompt_suggestions) > 0


def test_allowlisted_tool_registry_includes_portfolio_ml_tools() -> None:
    """Tool registry should expose allowlisted phase-i portfolio_ml tool adapters."""

    service_module = _load_service_module()
    registry_builder = getattr(service_module, "_build_allowlisted_tool_registry", None)
    if registry_builder is None or not callable(registry_builder):
        pytest.fail(
            "Fail-first baseline: missing callable _build_allowlisted_tool_registry(). "
            "Implement task 7.2 before this test can pass.",
        )

    registry = cast(dict[str, object], registry_builder())
    assert "portfolio_ml_signals" in registry
    assert "portfolio_ml_capm" in registry
    assert "portfolio_ml_forecasts" in registry
    assert "portfolio_ml_registry" in registry


@pytest.mark.integration
def test_chat_rejects_unresolved_document_references_without_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unresolved document IDs should fail fast before any provider invocation."""

    service_module = _load_service_module()
    endpoint_path = _copilot_chat_path()
    provider_call_count = 0

    async def _fake_provider_call(**_: Any) -> str:
        nonlocal provider_call_count
        provider_call_count += 1
        return "This provider response should never be used."

    monkeypatch.setattr(
        service_module,
        "request_groq_chat_completion",
        _fake_provider_call,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "operation": "chat",
                "messages": [
                    {
                        "role": "user",
                        "content": "Summarize referenced documents and forecast risk.",
                    }
                ],
                "period": "90D",
                "scope": "portfolio",
                "document_ids": [999999],
            },
        )

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    assert payload.get("state") == "blocked"
    assert payload.get("reason_code") == "insufficient_context"
    assert provider_call_count == 0
