"""Fail-first contract tests for phase-m decision-layer endpoint coverage."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

import pytest

from app.core.config import get_settings
from app.main import app


def _registered_paths() -> set[str]:
    """Return currently registered route paths."""

    return {
        route_path
        for route in app.routes
        for route_path in [getattr(route, "path", None)]
        if isinstance(route_path, str)
    }


def _load_module_or_fail(*, module_name: str, guidance: str) -> ModuleType:
    """Load one module and fail with actionable guidance if missing."""

    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"Fail-first baseline: missing module {module_name}. {guidance}",
        )
        raise AssertionError from exc


def _assert_endpoint_registered(*, path: str, guidance: str) -> None:
    """Fail fast when one required endpoint is not mounted."""

    if path not in _registered_paths():
        pytest.fail(
            "Fail-first baseline: required phase-m endpoint "
            f"{path} is not registered in app.main. {guidance}",
        )


def _assert_callable_exists(
    *, module: ModuleType, callable_name: str, guidance: str
) -> None:
    """Fail when one expected module callable is missing."""

    if not hasattr(module, callable_name):
        pytest.fail(
            "Fail-first baseline: expected callable "
            f"'{callable_name}' is missing in {module.__name__}. {guidance}",
        )


def test_phase_m_decision_layer_endpoints_are_registered() -> None:
    """Phase-m decision/rebalancing/news route contracts should be mounted."""

    settings = get_settings()
    expected_paths = [
        f"{settings.api_prefix}/portfolio/command-center",
        f"{settings.api_prefix}/portfolio/exposure",
        f"{settings.api_prefix}/portfolio/contribution-to-risk",
        f"{settings.api_prefix}/portfolio/correlation",
        f"{settings.api_prefix}/portfolio/rebalancing/strategies",
        f"{settings.api_prefix}/portfolio/news/context",
    ]

    for expected_path in expected_paths:
        _assert_endpoint_registered(
            path=expected_path,
            guidance=(
                "Implement tasks 2.1-2.4 and 3.1-3.4 before phase-m "
                "decision-layer endpoint tests can pass."
            ),
        )


def test_phase_m_routes_expose_typed_service_callables() -> None:
    """Phase-m route modules should expose expected typed service callables."""

    analytics_routes = _load_module_or_fail(
        module_name="app.portfolio_analytics.routes",
        guidance="Task 2.x should extend portfolio_analytics routes with decision-layer callables.",
    )
    _assert_callable_exists(
        module=analytics_routes,
        callable_name="get_portfolio_command_center_response",
        guidance="Task 2.1 should wire command-center service into analytics routes.",
    )
    _assert_callable_exists(
        module=analytics_routes,
        callable_name="get_portfolio_exposure_response",
        guidance="Task 2.2 should wire exposure decomposition service into analytics routes.",
    )
    _assert_callable_exists(
        module=analytics_routes,
        callable_name="get_portfolio_contribution_to_risk_response",
        guidance="Task 2.3 should wire contribution-to-risk service into analytics routes.",
    )
    _assert_callable_exists(
        module=analytics_routes,
        callable_name="get_portfolio_correlation_response",
        guidance="Task 2.4 should wire correlation matrix service into analytics routes.",
    )

    rebalancing_routes = _load_module_or_fail(
        module_name="app.portfolio_rebalancing.routes",
        guidance="Task 3.1 should introduce a dedicated rebalancing slice with route module.",
    )
    _assert_callable_exists(
        module=rebalancing_routes,
        callable_name="get_portfolio_rebalancing_strategies_response",
        guidance="Task 3.1 should expose strategy-comparison route callable.",
    )

    news_routes = _load_module_or_fail(
        module_name="app.portfolio_news_context.routes",
        guidance="Task 3.3 should introduce a dedicated news-context slice with route module.",
    )
    _assert_callable_exists(
        module=news_routes,
        callable_name="get_portfolio_news_context_response",
        guidance="Task 3.3 should expose holdings-grounded news-context route callable.",
    )
