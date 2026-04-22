"""Fail-first tests for provider/runtime error to copilot reason mapping."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest


def _load_portfolio_ai_service_module() -> ModuleType:
    """Load service module and fail with actionable guidance when missing."""

    try:
        return import_module("app.portfolio_ai_copilot.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.service. "
            "Implement tasks 2.6-3.6 before provider mapping tests can pass.",
        )
        raise AssertionError from exc


def _load_mapping_callable() -> Any:
    """Load provider failure mapping callable and fail with clear guidance."""

    module = _load_portfolio_ai_service_module()
    candidate = getattr(module, "map_provider_failure_to_copilot_state", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing map_provider_failure_to_copilot_state() in "
            "app.portfolio_ai_copilot.service. Task 2.6 should freeze provider failure "
            "normalization before implementation.",
        )
    if not callable(candidate):
        pytest.fail("Fail-first baseline: map_provider_failure_to_copilot_state must be callable.")
    return cast(Any, candidate)


def _assert_mapping(
    *,
    mapping_result: object,
    expected_state: str,
    expected_reason_code: str,
) -> None:
    """Assert one normalized state/reason mapping from permissive result shapes."""

    if isinstance(mapping_result, tuple):
        mapping_tuple = cast(tuple[object, ...], mapping_result)
        if len(mapping_tuple) == 2:
            actual_state = str(mapping_tuple[0])
            actual_reason_code = str(mapping_tuple[1])
        else:
            actual_state = "None"
            actual_reason_code = "None"
    elif isinstance(mapping_result, dict):
        mapping_dict = cast(dict[str, object], mapping_result)
        actual_state = str(mapping_dict.get("state"))
        actual_reason_code = str(mapping_dict.get("reason_code"))
    else:
        actual_state = str(getattr(mapping_result, "state", None))
        actual_reason_code = str(getattr(mapping_result, "reason_code", None))

    assert actual_state == expected_state
    assert actual_reason_code == expected_reason_code


def test_provider_failure_mapping_contract_for_rate_limit() -> None:
    """Provider 429 should map to error/rate_limited contract semantics."""

    mapper = _load_mapping_callable()
    mapping_result = mapper(
        status_code=429,
        provider_error_code="rate_limit_exceeded",
        error_type="RateLimitError",
    )
    _assert_mapping(
        mapping_result=mapping_result,
        expected_state="error",
        expected_reason_code="rate_limited",
    )


def test_provider_failure_mapping_contract_for_policy_block() -> None:
    """Provider 403 policy/permission blocks should map to blocked/policy reason."""

    mapper = _load_mapping_callable()
    mapping_result = mapper(
        status_code=403,
        provider_error_code="blocked_api_access",
        error_type="PermissionDeniedError",
    )
    _assert_mapping(
        mapping_result=mapping_result,
        expected_state="blocked",
        expected_reason_code="provider_blocked_policy",
    )


def test_provider_failure_mapping_contract_for_misconfiguration() -> None:
    """Invalid credentials or model config should map to provider_misconfigured."""

    mapper = _load_mapping_callable()
    mapping_result = mapper(
        status_code=401,
        provider_error_code="invalid_api_key",
        error_type="AuthenticationError",
    )
    _assert_mapping(
        mapping_result=mapping_result,
        expected_state="error",
        expected_reason_code="provider_misconfigured",
    )


def test_provider_failure_mapping_contract_for_unavailability() -> None:
    """Timeouts/5xx should map to provider_unavailable."""

    mapper = _load_mapping_callable()
    mapping_result = mapper(
        status_code=503,
        provider_error_code="service_unavailable",
        error_type="APITimeoutError",
    )
    _assert_mapping(
        mapping_result=mapping_result,
        expected_state="error",
        expected_reason_code="provider_unavailable",
    )
