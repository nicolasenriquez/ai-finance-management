"""Fail-first tests for governed SQL template contracts in portfolio copilot."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from importlib import import_module
from types import ModuleType
from typing import cast

import pytest

ExecuteGovernedSqlTemplateCallable = Callable[..., Awaitable[dict[str, object]]]


def _load_service_module() -> ModuleType:
    """Load portfolio copilot service module with fail-first guidance."""

    try:
        return import_module("app.portfolio_ai_copilot.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.service. "
            "Implement tasks 7.3-7.4 before governed SQL tests can pass.",
        )
        raise AssertionError from exc


def _load_service_error_type() -> type[Exception]:
    """Load one typed copilot client error class."""

    module = _load_service_module()
    candidate = getattr(module, "PortfolioAiCopilotClientError", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioAiCopilotClientError. "
            "Implement task 7.4 explicit rejection semantics.",
        )
    if not isinstance(candidate, type) or not issubclass(candidate, Exception):
        pytest.fail(
            "Fail-first baseline: PortfolioAiCopilotClientError must be an Exception subclass.",
        )
    return candidate


def _load_execute_governed_sql_callable() -> ExecuteGovernedSqlTemplateCallable:
    """Load governed SQL template executor callable with fail-first guidance."""

    module = _load_service_module()
    candidate = getattr(module, "execute_governed_sql_template", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing callable execute_governed_sql_template(). "
            "Implement tasks 7.3-7.4 before this test can pass.",
        )
    if not callable(candidate):
        pytest.fail(
            "Fail-first baseline: execute_governed_sql_template must be callable."
        )
    return cast(ExecuteGovernedSqlTemplateCallable, candidate)


@pytest.mark.asyncio
async def test_governed_sql_rejects_unapproved_template_id() -> None:
    """Unapproved SQL template IDs should fail fast with explicit policy semantics."""

    execute_governed_sql_template = _load_execute_governed_sql_callable()
    client_error_type = _load_service_error_type()

    with pytest.raises(client_error_type) as exc_info:
        await execute_governed_sql_template(
            db=None,
            template_id="unknown_template",
            template_params={},
        )

    error_text = str(exc_info.value).lower()
    assert "governed_sql_template_not_allowlisted" in error_text


@pytest.mark.asyncio
async def test_governed_sql_rejects_free_form_sql_text_input() -> None:
    """Free-form SQL text must be rejected by governed template policy."""

    execute_governed_sql_template = _load_execute_governed_sql_callable()
    client_error_type = _load_service_error_type()

    with pytest.raises(client_error_type) as exc_info:
        await execute_governed_sql_template(
            db=None,
            template_id="portfolio_ml_latest_forecast_states",
            template_params={},
            raw_sql="SELECT * FROM source_document",
        )

    error_text = str(exc_info.value).lower()
    assert "governed_sql_policy" in error_text


@pytest.mark.asyncio
async def test_governed_sql_rejects_invalid_parameter_shapes() -> None:
    """Template parameter schema violations should fail with explicit semantics."""

    execute_governed_sql_template = _load_execute_governed_sql_callable()
    client_error_type = _load_service_error_type()

    with pytest.raises(client_error_type) as exc_info:
        await execute_governed_sql_template(
            db=None,
            template_id="portfolio_ml_latest_forecast_states",
            template_params={"max_rows": "9999"},
        )

    error_text = str(exc_info.value).lower()
    assert "governed_sql_invalid_parameters" in error_text
