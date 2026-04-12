"""Fail-first tests for phase-m structured copilot response and question-pack contracts."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _load_routes_module() -> ModuleType:
    """Load routes module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ai_copilot.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.routes. "
            "Implement task 5.1 before phase-m copilot contract tests can pass.",
        )
        raise AssertionError from exc


def _load_schemas_module() -> ModuleType:
    """Load schemas module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ai_copilot.schemas")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.schemas. "
            "Task 5.1 should introduce structured phase-m response contracts.",
        )
        raise AssertionError from exc


def _load_service_module() -> ModuleType:
    """Load service module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ai_copilot.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.service. "
            "Task 5.2 should expose guided question-pack orchestration.",
        )
        raise AssertionError from exc


def _copilot_chat_path() -> str:
    """Build copilot chat endpoint path from configured API prefix."""

    routes_module = _load_routes_module()
    settings = getattr(routes_module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_ai_copilot.routes.settings is missing. "
            "Task 5.1 should preserve route-prefix settings availability.",
        )
    return f"{settings.api_prefix}/portfolio/copilot/chat"


def test_response_schema_exposes_structured_phase_m_fields() -> None:
    """Copilot response schema should expose structured narrative envelope fields."""

    schemas_module = _load_schemas_module()
    response_model = getattr(schemas_module, "PortfolioCopilotChatResponse", None)
    if response_model is None or not hasattr(response_model, "model_fields"):
        pytest.fail(
            "Fail-first baseline: missing PortfolioCopilotChatResponse model_fields metadata. "
            "Task 5.1 should keep typed response schema available.",
        )

    model_fields = cast(dict[str, object], response_model.model_fields)
    expected_fields = {
        "answer",
        "evidence",
        "assumptions",
        "caveats",
        "suggested_follow_ups",
    }
    for expected_field in expected_fields:
        assert (
            expected_field in model_fields
        ), f"Fail-first baseline: missing structured copilot response field '{expected_field}'."

    assert "answer_text" not in model_fields, (
        "Fail-first baseline: legacy answer_text should be replaced by structured 'answer' "
        "field in phase-m response contracts."
    )


def test_service_exposes_phase_m_question_pack_resolver() -> None:
    """Copilot service should expose one guided question-pack resolver callable."""

    service_module = _load_service_module()
    question_pack_resolver = getattr(service_module, "resolve_phase_m_question_pack", None)
    if question_pack_resolver is None or not callable(question_pack_resolver):
        pytest.fail(
            "Fail-first baseline: missing callable resolve_phase_m_question_pack(). "
            "Implement task 5.2 before this test can pass.",
        )


@pytest.mark.integration
def test_chat_endpoint_returns_structured_sections_for_ready_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ready chat responses should include structured narrative sections."""

    routes_module = _load_routes_module()
    endpoint_path = _copilot_chat_path()

    async def _fake_phase_m_chat_response(**_: Any) -> dict[str, Any]:
        return {
            "state": "ready",
            "answer_text": "Temporary compatibility answer text.",
            "answer": "Portfolio drawdown was driven by BTC and NVDA concentration.",
            "evidence": [
                {
                    "tool_id": "portfolio_risk_estimators",
                    "metric_id": "drawdown",
                    "as_of_ledger_at": "2026-04-06T00:00:00Z",
                }
            ],
            "assumptions": ["Benchmark uses SPY daily close alignment."],
            "caveats": ["News context is delayed for one symbol."],
            "suggested_follow_ups": [
                "Show concentration-to-risk breakdown for top five holdings.",
            ],
            "reason_code": None,
        }

    monkeypatch.setattr(
        routes_module,
        "get_portfolio_copilot_chat_response",
        _fake_phase_m_chat_response,
    )

    with TestClient(app) as client:
        response = client.post(
            endpoint_path,
            json={
                "operation": "chat",
                "messages": [
                    {
                        "role": "user",
                        "content": "Why is my portfolio down today?",
                    },
                ],
                "scope": "portfolio",
                "period": "90D",
            },
        )

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    assert "answer" in payload
    assert "assumptions" in payload
    assert "caveats" in payload
    assert "suggested_follow_ups" in payload
