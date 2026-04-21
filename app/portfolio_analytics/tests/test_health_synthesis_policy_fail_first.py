"""Fail-first policy tests for deterministic portfolio-health synthesis scoring."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from types import ModuleType
from typing import cast

import pytest

from app.portfolio_analytics.schemas import (
    PortfolioHealthLabel,
    PortfolioHealthProfilePosture,
)


def _load_service_module() -> ModuleType:
    """Load portfolio analytics service module with actionable fail-first guidance."""

    try:
        return import_module("app.portfolio_analytics.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.service. "
            "Implement tasks 8.2-8.4 before health policy tests can pass.",
        )
        raise AssertionError from exc


def test_health_score_weighting_is_deterministic_and_profile_sensitive() -> None:
    """Different profile postures should produce deterministic but distinct scores."""

    service_module = _load_service_module()
    compute_score = getattr(
        service_module, "_compute_health_score_from_pillar_scores", None
    )
    if compute_score is None or not callable(compute_score):
        pytest.fail(
            "Fail-first baseline: missing _compute_health_score_from_pillar_scores helper. "
            "Task 8.3 should expose deterministic profile-weighted scoring.",
        )
    compute_score_fn = cast(Callable[..., int], compute_score)

    pillar_scores = {
        "growth": 88,
        "risk": 42,
        "risk_adjusted_quality": 79,
        "resilience": 68,
    }

    conservative_score = compute_score_fn(
        pillar_scores=pillar_scores,
        profile_posture=PortfolioHealthProfilePosture.CONSERVATIVE,
    )
    balanced_score = compute_score_fn(
        pillar_scores=pillar_scores,
        profile_posture=PortfolioHealthProfilePosture.BALANCED,
    )
    aggressive_score = compute_score_fn(
        pillar_scores=pillar_scores,
        profile_posture=PortfolioHealthProfilePosture.AGGRESSIVE,
    )

    assert conservative_score == compute_score_fn(
        pillar_scores=pillar_scores,
        profile_posture=PortfolioHealthProfilePosture.CONSERVATIVE,
    )
    assert aggressive_score > conservative_score
    assert balanced_score >= conservative_score


def test_health_label_policy_applies_critical_override_guardrails() -> None:
    """Critical override counts should constrain aggregate health labels."""

    service_module = _load_service_module()
    resolve_label = getattr(service_module, "_resolve_health_label_from_score", None)
    if resolve_label is None or not callable(resolve_label):
        pytest.fail(
            "Fail-first baseline: missing _resolve_health_label_from_score helper. "
            "Task 8.3 should enforce critical override guardrails.",
        )

    assert (
        resolve_label(health_score=80, critical_override_count=0)
        == PortfolioHealthLabel.HEALTHY
    )
    assert (
        resolve_label(health_score=80, critical_override_count=1)
        == PortfolioHealthLabel.WATCHLIST
    )
    assert (
        resolve_label(health_score=80, critical_override_count=2)
        == PortfolioHealthLabel.STRESSED
    )
    assert (
        resolve_label(health_score=40, critical_override_count=0)
        == PortfolioHealthLabel.STRESSED
    )
