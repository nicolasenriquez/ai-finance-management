"""Fail-first tests for deterministic opportunity scanner contracts."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, cast

import pytest


def _load_portfolio_ai_service_module() -> ModuleType:
    """Load service module and fail with actionable guidance if missing."""

    try:
        return import_module("app.portfolio_ai_copilot.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ai_copilot.service. "
            "Implement tasks 2.3-3.5 before opportunity scanner tests can pass.",
        )
        raise AssertionError from exc


def _load_service_symbol(
    *,
    symbol_name: str,
    guidance: str,
) -> object:
    """Load one service symbol and fail with clear guidance when missing."""

    module = _load_portfolio_ai_service_module()
    candidate = getattr(module, symbol_name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing symbol {symbol_name} in app.portfolio_ai_copilot.service. "
            f"{guidance}",
        )
    return candidate


def _load_client_error_type() -> type[Exception]:
    """Load typed client error class for explicit-failure assertions."""

    candidate = _load_service_symbol(
        symbol_name="PortfolioAiCopilotClientError",
        guidance=(
            "Task 2.3 should expose a typed opportunity-scanner insufficiency/boundary error."
        ),
    )
    if not isinstance(candidate, type) or not issubclass(candidate, Exception):
        pytest.fail(
            "Fail-first baseline: PortfolioAiCopilotClientError must be one Exception subclass.",
        )
    return candidate


def test_opportunity_scanner_ranking_is_deterministic_for_identical_inputs() -> None:
    """Deterministic scanner should return identical ranking for identical inputs."""

    compute_candidate = _load_service_symbol(
        symbol_name="compute_deterministic_opportunity_candidates",
        guidance=(
            "Task 2.3 should expose one deterministic opportunity ranking callable."
        ),
    )
    if not callable(compute_candidate):
        pytest.fail(
            "Fail-first baseline: compute_deterministic_opportunity_candidates must be callable.",
        )
    compute_deterministic_opportunity_candidates = cast(Any, compute_candidate)

    candidate_inputs: list[dict[str, object]] = [
        {
            "symbol": "AAA",
            "latest_close_price_usd": "95.00",
            "rolling_90d_high_price_usd": "120.00",
            "return_30d": "0.04",
            "volatility_30d": "0.18",
            "history_points_count": 120,
            "currently_held": False,
        },
        {
            "symbol": "BBB",
            "latest_close_price_usd": "60.00",
            "rolling_90d_high_price_usd": "75.00",
            "return_30d": "0.03",
            "volatility_30d": "0.17",
            "history_points_count": 120,
            "currently_held": False,
        },
        {
            "symbol": "CCC",
            "latest_close_price_usd": "40.00",
            "rolling_90d_high_price_usd": "42.00",
            "return_30d": "-0.02",
            "volatility_30d": "0.30",
            "history_points_count": 120,
            "currently_held": False,
        },
    ]

    first_result = compute_deterministic_opportunity_candidates(
        candidate_inputs=candidate_inputs,
        minimum_eligible_count=3,
    )
    second_result = compute_deterministic_opportunity_candidates(
        candidate_inputs=candidate_inputs,
        minimum_eligible_count=3,
    )

    assert first_result == second_result


def test_opportunity_scanner_rejects_insufficient_eligible_universe_explicitly() -> (
    None
):
    """Scanner should reject when insufficient eligible candidates are available."""

    compute_candidate = _load_service_symbol(
        symbol_name="compute_deterministic_opportunity_candidates",
        guidance=(
            "Task 2.3 should expose one deterministic opportunity ranking callable."
        ),
    )
    if not callable(compute_candidate):
        pytest.fail(
            "Fail-first baseline: compute_deterministic_opportunity_candidates must be callable.",
        )
    compute_deterministic_opportunity_candidates = cast(Any, compute_candidate)
    client_error_type = _load_client_error_type()

    insufficient_inputs: list[dict[str, object]] = [
        {
            "symbol": "AAA",
            "latest_close_price_usd": "95.00",
            "rolling_90d_high_price_usd": "120.00",
            "return_30d": "0.04",
            "volatility_30d": "0.18",
            "history_points_count": 20,
            "currently_held": False,
        },
        {
            "symbol": "BBB",
            "latest_close_price_usd": "60.00",
            "rolling_90d_high_price_usd": "75.00",
            "return_30d": "0.03",
            "volatility_30d": "0.17",
            "history_points_count": 45,
            "currently_held": True,
        },
    ]

    with pytest.raises(client_error_type) as exc_info:
        compute_deterministic_opportunity_candidates(
            candidate_inputs=insufficient_inputs,
            minimum_eligible_count=20,
        )

    assert "insufficient" in str(exc_info.value).lower()


def test_opportunity_scanner_classifies_held_symbol_as_double_down_when_rules_pass() -> (
    None
):
    """Held symbol should classify as double_down_candidate when threshold and proxy pass."""

    compute_candidate = _load_service_symbol(
        symbol_name="compute_deterministic_opportunity_candidates",
        guidance=(
            "Task 2.3 should expose one deterministic opportunity ranking callable."
        ),
    )
    if not callable(compute_candidate):
        pytest.fail(
            "Fail-first baseline: compute_deterministic_opportunity_candidates must be callable.",
        )
    compute_deterministic_opportunity_candidates = cast(Any, compute_candidate)

    candidate_inputs: list[dict[str, object]] = [
        {
            "symbol": "AAA",
            "latest_close_price_usd": "80.00",
            "rolling_90d_high_price_usd": "100.00",
            "rolling_52w_high_price_usd": "100.00",
            "drawdown_from_52w_high_pct": "0.20",
            "return_30d": "-0.05",
            "return_90d": "-0.10",
            "return_252d": "0.08",
            "volatility_30d": "0.03",
            "history_points_count": 260,
            "currently_held": True,
        },
        {
            "symbol": "BBB",
            "latest_close_price_usd": "90.00",
            "rolling_90d_high_price_usd": "100.00",
            "rolling_52w_high_price_usd": "110.00",
            "drawdown_from_52w_high_pct": "0.181818",
            "return_30d": "0.02",
            "return_90d": "0.04",
            "return_252d": "0.12",
            "volatility_30d": "0.02",
            "history_points_count": 260,
            "currently_held": False,
        },
        {
            "symbol": "CCC",
            "latest_close_price_usd": "50.00",
            "rolling_90d_high_price_usd": "60.00",
            "rolling_52w_high_price_usd": "70.00",
            "drawdown_from_52w_high_pct": "0.285714",
            "return_30d": "-0.04",
            "return_90d": "-0.08",
            "return_252d": "-0.02",
            "volatility_30d": "0.04",
            "history_points_count": 260,
            "currently_held": False,
        },
    ]

    ranked = compute_deterministic_opportunity_candidates(
        candidate_inputs=candidate_inputs,
        minimum_eligible_count=3,
    )
    aaa_row = next(row for row in ranked if str(row.get("symbol")) == "AAA")
    assert aaa_row.get("action_state") == "double_down_candidate"
    assert str(aaa_row.get("action_multiplier")) == "2.000000"


def test_opportunity_scanner_marks_failed_proxy_candidates_as_hold_off() -> None:
    """Candidates with failed fundamentals proxy should classify as hold_off."""

    compute_candidate = _load_service_symbol(
        symbol_name="compute_deterministic_opportunity_candidates",
        guidance=(
            "Task 2.3 should expose one deterministic opportunity ranking callable."
        ),
    )
    if not callable(compute_candidate):
        pytest.fail(
            "Fail-first baseline: compute_deterministic_opportunity_candidates must be callable.",
        )
    compute_deterministic_opportunity_candidates = cast(Any, compute_candidate)

    candidate_inputs: list[dict[str, object]] = [
        {
            "symbol": "AAA",
            "latest_close_price_usd": "50.00",
            "rolling_90d_high_price_usd": "100.00",
            "rolling_52w_high_price_usd": "120.00",
            "drawdown_from_52w_high_pct": "0.583333",
            "return_30d": "-0.40",
            "return_90d": "-0.50",
            "return_252d": "-0.65",
            "volatility_30d": "0.18",
            "history_points_count": 300,
            "currently_held": False,
        },
        {
            "symbol": "BBB",
            "latest_close_price_usd": "88.00",
            "rolling_90d_high_price_usd": "102.00",
            "rolling_52w_high_price_usd": "118.00",
            "drawdown_from_52w_high_pct": "0.254237",
            "return_30d": "-0.02",
            "return_90d": "0.01",
            "return_252d": "0.04",
            "volatility_30d": "0.03",
            "history_points_count": 300,
            "currently_held": True,
        },
        {
            "symbol": "CCC",
            "latest_close_price_usd": "70.00",
            "rolling_90d_high_price_usd": "80.00",
            "rolling_52w_high_price_usd": "95.00",
            "drawdown_from_52w_high_pct": "0.263157",
            "return_30d": "0.01",
            "return_90d": "0.03",
            "return_252d": "0.07",
            "volatility_30d": "0.02",
            "history_points_count": 300,
            "currently_held": False,
        },
    ]

    ranked = compute_deterministic_opportunity_candidates(
        candidate_inputs=candidate_inputs,
        minimum_eligible_count=3,
    )
    aaa_row = next(row for row in ranked if str(row.get("symbol")) == "AAA")
    assert aaa_row.get("action_state") == "hold_off"
    assert aaa_row.get("fundamentals_proxy_state") == "failed"


def test_opportunity_scanner_does_not_double_down_without_full_52w_history() -> None:
    """Held symbols with less than 252 points should not classify as double_down_candidate."""

    compute_candidate = _load_service_symbol(
        symbol_name="compute_deterministic_opportunity_candidates",
        guidance=(
            "Task 2.3 should expose one deterministic opportunity ranking callable."
        ),
    )
    if not callable(compute_candidate):
        pytest.fail(
            "Fail-first baseline: compute_deterministic_opportunity_candidates must be callable.",
        )
    compute_deterministic_opportunity_candidates = cast(Any, compute_candidate)

    candidate_inputs: list[dict[str, object]] = [
        {
            "symbol": "AAA",
            "latest_close_price_usd": "80.00",
            "rolling_90d_high_price_usd": "100.00",
            "rolling_52w_high_price_usd": "100.00",
            "drawdown_from_52w_high_pct": "0.20",
            "return_30d": "-0.05",
            "return_90d": "-0.10",
            "return_252d": "0.08",
            "volatility_30d": "0.03",
            "history_points_count": 120,
            "currently_held": True,
        },
        {
            "symbol": "BBB",
            "latest_close_price_usd": "90.00",
            "rolling_90d_high_price_usd": "100.00",
            "rolling_52w_high_price_usd": "110.00",
            "drawdown_from_52w_high_pct": "0.181818",
            "return_30d": "0.02",
            "return_90d": "0.04",
            "return_252d": "0.12",
            "volatility_30d": "0.02",
            "history_points_count": 260,
            "currently_held": False,
        },
        {
            "symbol": "CCC",
            "latest_close_price_usd": "50.00",
            "rolling_90d_high_price_usd": "60.00",
            "rolling_52w_high_price_usd": "70.00",
            "drawdown_from_52w_high_pct": "0.285714",
            "return_30d": "-0.04",
            "return_90d": "-0.08",
            "return_252d": "-0.02",
            "volatility_30d": "0.04",
            "history_points_count": 260,
            "currently_held": False,
        },
    ]

    ranked = compute_deterministic_opportunity_candidates(
        candidate_inputs=candidate_inputs,
        minimum_eligible_count=3,
    )
    aaa_row = next(row for row in ranked if str(row.get("symbol")) == "AAA")
    assert aaa_row.get("action_state") == "baseline_dca"
    assert "insufficient_52w_history" in list(aaa_row.get("action_reason_codes", []))
