"""Fail-first tests for portfolio copilot schema validation edge cases."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

import pytest
from pydantic import ValidationError


def _load_schemas_module() -> ModuleType:
    """Load portfolio copilot schemas module with fail-first guidance."""

    try:
        return import_module("app.portfolio_ai_copilot.schemas")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.schemas. "
            "Implement typed request contracts before schema validation tests can pass.",
        )
        raise AssertionError from exc


def test_chat_request_rejects_blank_sql_template_id_after_trimming() -> None:
    """Whitespace-only sql_template_id should fail request validation."""

    schemas_module = _load_schemas_module()
    request_model = getattr(schemas_module, "PortfolioCopilotChatRequest", None)
    if request_model is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioCopilotChatRequest in "
            "app.portfolio_ai_copilot.schemas.",
        )

    payload: dict[str, object] = {
        "operation": "chat",
        "messages": [{"role": "user", "content": "Summarize forecast state."}],
        "scope": "portfolio",
        "sql_template_id": "   ",
    }

    with pytest.raises(ValidationError) as exc_info:
        request_model.model_validate(payload)

    assert "sql_template_id must be non-empty when provided." in str(exc_info.value)
