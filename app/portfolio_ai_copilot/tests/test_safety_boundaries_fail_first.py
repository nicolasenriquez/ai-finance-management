"""Fail-first safety tests for copilot context privacy and boundary enforcement."""

from __future__ import annotations

import json
from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest


def _load_portfolio_ai_service_module() -> ModuleType:
    """Load service module with actionable fail-first guidance if missing."""

    try:
        return import_module("app.portfolio_ai_copilot.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.service. "
            "Implement tasks 2.2-3.4 before copilot safety tests can pass.",
        )
        raise AssertionError from exc


def _load_service_symbol(
    *,
    symbol_name: str,
    guidance: str,
) -> object:
    """Load one named symbol from service module and fail with clear guidance."""

    module = _load_portfolio_ai_service_module()
    candidate = getattr(module, symbol_name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing symbol {symbol_name} in app.portfolio_ai_copilot.service. "
            f"{guidance}",
        )
    return candidate


def _load_service_error_type(
    *,
    symbol_name: str = "PortfolioAiCopilotClientError",
    guidance: str,
) -> type[Exception]:
    """Load one exception type from service module and fail with guidance."""

    candidate = _load_service_symbol(symbol_name=symbol_name, guidance=guidance)
    if not isinstance(candidate, type) or not issubclass(candidate, Exception):
        pytest.fail(
            f"Fail-first baseline: symbol {symbol_name} must be one Exception subclass.",
        )
    return candidate


def test_model_context_excluded_fields_contract_includes_private_payload_markers() -> (
    None
):
    """Model-context exclusion contract should include private/raw payload markers."""

    excluded_fields_candidate = _load_service_symbol(
        symbol_name="MODEL_CONTEXT_EXCLUDED_FIELDS",
        guidance=(
            "Task 2.2 should freeze explicit exclusion markers for raw canonical/private fields."
        ),
    )

    if not isinstance(excluded_fields_candidate, (list, tuple, set, frozenset)):
        pytest.fail(
            "Fail-first baseline: MODEL_CONTEXT_EXCLUDED_FIELDS must be one iterable."
        )
    typed_excluded_fields_candidate = cast(
        list[object] | tuple[object, ...] | set[object] | frozenset[object],
        excluded_fields_candidate,
    )
    excluded_fields = {str(item) for item in typed_excluded_fields_candidate}

    required_markers = {
        "raw_payload",
        "source_payload",
        "canonical_payload",
        "transaction_events",
    }
    missing_markers = sorted(required_markers.difference(excluded_fields))
    assert missing_markers == []


def test_sanitize_model_context_payload_removes_raw_and_private_fields() -> None:
    """Sanitization helper should remove raw/private payload keys before model visibility."""

    sanitize_candidate = _load_service_symbol(
        symbol_name="sanitize_model_context_payload",
        guidance="Task 2.2 should expose one explicit model-context sanitization helper.",
    )
    if not callable(sanitize_candidate):
        pytest.fail(
            "Fail-first baseline: sanitize_model_context_payload must be callable."
        )
    sanitize_model_context_payload = cast(Any, sanitize_candidate)

    unsafe_context_payload: dict[str, object] = {
        "portfolio_summary": {"rows": [{"instrument_symbol": "VOO"}]},
        "raw_payload": {"sensitive": True},
        "source_payload": {"provider_secret": "never-send"},
        "transaction_events": [{"id": "evt-001", "cash_amount_usd": "1800.00"}],
    }

    sanitized_payload = sanitize_model_context_payload(
        context_payload=unsafe_context_payload
    )
    serialized_payload = json.dumps(sanitized_payload, default=str, sort_keys=True)

    assert "raw_payload" not in serialized_payload
    assert "source_payload" not in serialized_payload
    assert "transaction_events" not in serialized_payload
    assert "portfolio_summary" in serialized_payload


def test_boundary_classifier_rejects_execution_and_guarantee_requests_explicitly() -> (
    None
):
    """Boundary classifier should block execution and guaranteed-return asks."""

    classify_candidate = _load_service_symbol(
        symbol_name="classify_copilot_boundary_violation_reason",
        guidance="Task 2.2 should expose one explicit unsafe-request boundary classifier.",
    )
    if not callable(classify_candidate):
        pytest.fail(
            "Fail-first baseline: classify_copilot_boundary_violation_reason must be callable.",
        )
    classify_boundary_violation = cast(Any, classify_candidate)

    violation_reason = classify_boundary_violation(
        user_message="Buy NVDA automatically and guarantee 20% return next month.",
    )
    assert violation_reason == "boundary_restricted"


def test_boundary_classifier_returns_none_for_safe_read_only_analysis_requests() -> (
    None
):
    """Boundary classifier should allow scoped read-only analytical requests."""

    classify_candidate = _load_service_symbol(
        symbol_name="classify_copilot_boundary_violation_reason",
        guidance="Task 2.2 should expose one explicit unsafe-request boundary classifier.",
    )
    if not callable(classify_candidate):
        pytest.fail(
            "Fail-first baseline: classify_copilot_boundary_violation_reason must be callable.",
        )
    classify_boundary_violation = cast(Any, classify_candidate)

    violation_reason = classify_boundary_violation(
        user_message="Explain contribution concentration over 90D for my portfolio.",
    )
    assert violation_reason is None


def test_boundary_enforcer_raises_typed_client_error_for_unsafe_execution_requests() -> (
    None
):
    """Boundary enforcement should raise typed client errors for unsafe asks."""

    enforce_candidate = _load_service_symbol(
        symbol_name="enforce_copilot_request_boundary",
        guidance="Task 2.2 should expose one explicit request-boundary enforcement callable.",
    )
    if not callable(enforce_candidate):
        pytest.fail(
            "Fail-first baseline: enforce_copilot_request_boundary must be callable."
        )
    enforce_copilot_request_boundary = cast(Any, enforce_candidate)

    client_error_type = _load_service_error_type(
        guidance="Task 2.2 should raise one typed client-facing copilot boundary error.",
    )

    with pytest.raises(client_error_type):
        enforce_copilot_request_boundary(
            user_message="Sell AAPL now and rebalance my holdings automatically.",
        )
