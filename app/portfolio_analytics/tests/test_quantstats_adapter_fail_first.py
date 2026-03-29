"""Fail-first tests for QuantStats adapter compatibility and resilient metric behavior."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from types import ModuleType, SimpleNamespace
from typing import cast

import pandas as pd
import pytest

from app.portfolio_analytics.schemas import (
    PortfolioQuantBenchmarkContext,
    PortfolioQuantMetric,
)

RiskCallable = Callable[..., object]
CallQuantstatsMetricCallable = Callable[..., Decimal]
BuildQuantstatsMetricRowsCallable = Callable[
    ...,
    tuple[list[PortfolioQuantMetric], PortfolioQuantBenchmarkContext],
]
SingleSeriesMetricCallable = Callable[[pd.Series], float]


class _FakeQuantStatsStatsModule(ModuleType):
    """Typed fake QuantStats stats module for adapter contract tests."""

    comp: SingleSeriesMetricCallable
    cagr: SingleSeriesMetricCallable
    volatility: SingleSeriesMetricCallable
    max_drawdown: SingleSeriesMetricCallable
    best: SingleSeriesMetricCallable
    worst: SingleSeriesMetricCallable
    win_rate: SingleSeriesMetricCallable
    sharpe: SingleSeriesMetricCallable
    sortino: SingleSeriesMetricCallable
    calmar: SingleSeriesMetricCallable


def _load_portfolio_analytics_module() -> object:
    """Load portfolio analytics service module in fail-first mode."""

    try:
        return import_module("app.portfolio_analytics.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.service. "
            "Implement tasks 1.2/2.1 before QuantStats adapter tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> RiskCallable:
    """Load one named callable from portfolio analytics service module."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(RiskCallable, candidate)


def _load_client_error_type() -> type[Exception]:
    """Load portfolio analytics client error type for explicit-failure assertions."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, "PortfolioAnalyticsClientError", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioAnalyticsClientError. "
            "Implement tasks 1.2/2.1 before this test can pass.",
        )
    return cast(type[Exception], candidate)


def _build_returns_series() -> pd.Series:
    """Build deterministic UTC-indexed daily return series for adapter tests."""

    index = pd.DatetimeIndex(
        [datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=offset) for offset in range(6)]
    )
    return pd.Series(
        [0.01, -0.004, 0.006, 0.002, -0.001, 0.005],
        index=index,
        dtype="float64",
    )


def _build_fake_stats_module_without_alpha_beta() -> ModuleType:
    """Build one fake QuantStats stats module with baseline callables only."""

    fake_module = _FakeQuantStatsStatsModule("fake_quantstats_stats")
    fake_module.comp = lambda _: 0.02
    fake_module.cagr = lambda _: 0.08
    fake_module.volatility = lambda _: 0.15
    fake_module.max_drawdown = lambda _: -0.05
    fake_module.best = lambda _: 0.03
    fake_module.worst = lambda _: -0.02
    fake_module.win_rate = lambda _: 0.66
    fake_module.sharpe = lambda _: 1.12
    fake_module.sortino = lambda _: 1.28
    fake_module.calmar = lambda _: 1.07
    return fake_module


def test_quantstats_adapter_reproduces_current_alpha_beta_callable_mismatch() -> None:
    """Low-level QuantStats callable boundary should fail explicitly when callable is absent."""

    call_metric = cast(
        CallQuantstatsMetricCallable,
        _load_callable(
            "_call_quantstats_metric",
            task_hint="1.2",
        ),
    )
    client_error_type = _load_client_error_type()

    returns = _build_returns_series()
    benchmark_returns = _build_returns_series()
    stats_module = _build_fake_stats_module_without_alpha_beta()

    with pytest.raises(client_error_type) as exc_info:
        call_metric(
            stats_module=stats_module,
            metric_id="alpha",
            callable_name="alpha",
            returns_series=returns,
            benchmark_returns=benchmark_returns,
        )

    assert "callable 'alpha' is unavailable" in str(exc_info.value).lower()


def test_quantstats_adapter_should_keep_core_metrics_when_optional_benchmark_metrics_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-first: adapter should keep core metrics even if alpha/beta callables are absent."""

    build_metric_rows = cast(
        BuildQuantstatsMetricRowsCallable,
        _load_callable(
            "_build_quantstats_metric_rows",
            task_hint="2.1",
        ),
    )

    returns = _build_returns_series()
    benchmark_returns = _build_returns_series()

    fake_quantstats_module = SimpleNamespace(
        stats=_build_fake_stats_module_without_alpha_beta(),
    )
    monkeypatch.setattr(
        import_module("app.portfolio_analytics.service"),
        "_load_quantstats_module",
        lambda: fake_quantstats_module,
    )

    rows, benchmark_context = build_metric_rows(
        returns_series=returns,
        benchmark_returns=benchmark_returns,
        benchmark_symbol="SP500_PROXY",
    )
    metric_ids = {str(getattr(row, "metric_id", "")) for row in rows}
    assert "sharpe" in metric_ids
    assert "sortino" in metric_ids
    assert "alpha" not in metric_ids
    assert "beta" not in metric_ids
    omitted_metric_ids = benchmark_context.omitted_metric_ids
    assert omitted_metric_ids == ["alpha", "beta"]
