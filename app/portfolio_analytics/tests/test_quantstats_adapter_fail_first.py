"""Fail-first tests for QuantStats adapter compatibility and resilient metric behavior."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from app.portfolio_analytics.schemas import (
    PortfolioChartPeriod,
    PortfolioMonteCarloCalibrationBasis,
    PortfolioMonteCarloCalibrationContext,
    PortfolioMonteCarloProfileId,
    PortfolioMonteCarloProfileScenario,
    PortfolioMonteCarloRequest,
    PortfolioQuantBenchmarkContext,
    PortfolioQuantMetric,
    PortfolioQuantReportScope,
)

RiskCallable = Callable[..., object]
CallQuantstatsMetricCallable = Callable[..., Decimal]
BuildQuantstatsMetricRowsCallable = Callable[
    ...,
    tuple[list[PortfolioQuantMetric], PortfolioQuantBenchmarkContext],
]
SingleSeriesMetricCallable = Callable[[pd.Series], float]
ComputeRiskMetricsCallable = Callable[..., dict[str, Decimal]]
GetRiskEstimatorsResponseCallable = Callable[..., Coroutine[Any, Any, object]]


class _FakeMonteCarloResult:
    """Typed Monte Carlo result stub used by adapter compatibility tests."""

    data: pd.DataFrame
    stats: dict[str, float]
    maxdd: dict[str, float]
    bust_probability: float | None
    goal_probability: float | None

    def __init__(self) -> None:
        self.data = pd.DataFrame(
            {
                "sim_0": [0.01, 0.03, 0.05],
                "sim_1": [-0.01, 0.01, 0.04],
            }
        )
        self.stats = {
            "min": -0.02,
            "max": 0.08,
            "mean": 0.04,
            "median": 0.045,
            "std": 0.02,
            "percentile_5": -0.01,
            "percentile_25": 0.01,
            "percentile_75": 0.06,
            "percentile_95": 0.075,
        }
        self.maxdd = {
            "min": -0.12,
            "max": -0.03,
            "mean": -0.07,
            "median": -0.06,
            "std": 0.02,
            "percentile_5": -0.11,
            "percentile_95": -0.04,
        }
        self.bust_probability = 0.12
        self.goal_probability = 0.37


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


def test_quantstats_monte_carlo_adapter_calls_pinned_runtime_with_explicit_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-first: Monte Carlo adapter should call QuantStats runtime with explicit envelope."""

    run_monte_carlo = _load_callable(
        "_run_quantstats_monte_carlo",
        task_hint="2.6",
    )

    captured_calls: list[dict[str, object]] = []

    def _fake_montecarlo(
        returns: pd.Series,
        sims: int = 1000,
        bust: float | None = None,
        goal: float | None = None,
        seed: int | None = None,
    ) -> _FakeMonteCarloResult:
        captured_calls.append(
            {
                "returns_len": len(returns),
                "sims": sims,
                "bust": bust,
                "goal": goal,
                "seed": seed,
            }
        )
        return _FakeMonteCarloResult()

    fake_quantstats_module = SimpleNamespace(
        stats=SimpleNamespace(montecarlo=_fake_montecarlo),
    )
    monkeypatch.setattr(
        import_module("app.portfolio_analytics.service"),
        "_load_quantstats_module",
        lambda: fake_quantstats_module,
    )

    returns = _build_returns_series()
    result = run_monte_carlo(
        returns_series=returns,
        sims=1000,
        bust_threshold=-0.2,
        goal_threshold=0.3,
        seed=20260330,
    )

    assert captured_calls == [
        {
            "returns_len": len(returns),
            "sims": 1000,
            "bust": -0.2,
            "goal": 0.3,
            "seed": 20260330,
        }
    ]
    assert hasattr(result, "stats")
    assert hasattr(result, "maxdd")
    assert hasattr(result, "bust_probability")
    assert hasattr(result, "goal_probability")


def test_quantstats_monte_carlo_adapter_fails_explicitly_when_callable_missing() -> None:
    """Fail-first: Monte Carlo adapter should fail explicitly when runtime callable is absent."""

    run_monte_carlo = _load_callable(
        "_run_quantstats_monte_carlo",
        task_hint="2.6",
    )
    client_error_type = _load_client_error_type()

    returns = _build_returns_series()
    with pytest.raises(client_error_type) as exc_info:
        run_monte_carlo(
            returns_series=returns,
            sims=1000,
            bust_threshold=-0.2,
            goal_threshold=0.3,
            seed=20260330,
            quantstats_module=SimpleNamespace(stats=SimpleNamespace()),
        )

    assert "montecarlo" in str(exc_info.value).lower()


def test_monte_carlo_request_accepts_short_horizon_and_rejects_sub_minimum() -> None:
    """Monte Carlo request contract should accept 5-day horizon and reject horizon below 5."""

    accepted = PortfolioMonteCarloRequest(
        scope=PortfolioQuantReportScope.PORTFOLIO,
        period=PortfolioChartPeriod.D30,
        sims=1000,
        horizon_days=5,
    )
    assert accepted.horizon_days == 5

    with pytest.raises(ValidationError):
        PortfolioMonteCarloRequest(
            scope=PortfolioQuantReportScope.PORTFOLIO,
            period=PortfolioChartPeriod.D30,
            sims=1000,
            horizon_days=4,
        )


def test_monte_carlo_profile_thresholds_fallback_explicitly_when_sample_is_insufficient() -> None:
    """Calibration helper should emit explicit fallback metadata when sample size is insufficient."""

    resolve_thresholds = _load_callable(
        "_resolve_monte_carlo_profile_thresholds",
        task_hint="7.2",
    )

    sparse_returns = pd.Series(
        [0.01, -0.02, 0.015, 0.005],
        index=pd.DatetimeIndex(
            [
                datetime(2026, 1, 2, tzinfo=UTC),
                datetime(2026, 1, 3, tzinfo=UTC),
                datetime(2026, 1, 4, tzinfo=UTC),
                datetime(2026, 1, 5, tzinfo=UTC),
            ]
        ),
        dtype="float64",
    )

    thresholds_by_profile, calibration_context = cast(
        tuple[
            dict[PortfolioMonteCarloProfileId, tuple[Decimal, Decimal]],
            PortfolioMonteCarloCalibrationContext,
        ],
        resolve_thresholds(
            returns_series=sparse_returns,
            calibration_basis=PortfolioMonteCarloCalibrationBasis.ANNUAL,
            manual_bust_threshold=None,
            manual_goal_threshold=None,
        ),
    )

    assert PortfolioMonteCarloProfileId.CONSERVATIVE in thresholds_by_profile
    assert PortfolioMonteCarloProfileId.BALANCED in thresholds_by_profile
    assert PortfolioMonteCarloProfileId.GROWTH in thresholds_by_profile
    assert calibration_context.requested_basis == PortfolioMonteCarloCalibrationBasis.ANNUAL
    assert calibration_context.used_fallback is True
    assert "insufficient historical sample" in str(calibration_context.fallback_reason).lower()


def test_monte_carlo_profile_scenarios_keep_fixed_order_for_panoramic_comparison() -> None:
    """Profile scenario rows should stay in conservative/balanced/growth order for stable reading."""

    build_scenarios = _load_callable(
        "_build_monte_carlo_profile_scenarios",
        task_hint="7.1",
    )

    terminal_series = pd.Series(
        [-0.32, -0.21, -0.11, -0.03, 0.02, 0.08, 0.15, 0.26, 0.39],
        dtype="float64",
    )
    scenario_rows = cast(
        list[PortfolioMonteCarloProfileScenario],
        build_scenarios(
            terminal_series=terminal_series,
            profile_thresholds_by_id={
                PortfolioMonteCarloProfileId.CONSERVATIVE: (
                    Decimal("-0.10"),
                    Decimal("0.12"),
                ),
                PortfolioMonteCarloProfileId.BALANCED: (
                    Decimal("-0.20"),
                    Decimal("0.27"),
                ),
                PortfolioMonteCarloProfileId.GROWTH: (
                    Decimal("-0.30"),
                    Decimal("0.45"),
                ),
            },
        ),
    )

    profile_ids = [row.profile_id.value for row in scenario_rows]
    assert profile_ids == ["conservative", "balanced", "growth"]


def test_risk_metric_computation_uses_external_proxy_override_for_single_symbol_beta() -> None:
    """Single-symbol beta should use provided proxy returns rather than self-regression."""

    compute_risk_metrics = cast(
        ComputeRiskMetricsCallable,
        _load_callable(
            "_compute_risk_metrics_from_price_frame",
            task_hint="3.2",
        ),
    )

    aligned_timestamps = pd.DatetimeIndex(
        [datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index) for index in range(6)]
    )
    benchmark_returns = [0.01, -0.005, 0.008, -0.004, 0.006]
    symbol_returns = [return_value * 2.0 for return_value in benchmark_returns]

    symbol_prices = [100.0]
    for return_value in symbol_returns:
        symbol_prices.append(symbol_prices[-1] * (1.0 + return_value))
    price_frame = pd.DataFrame(
        {"AAPL": symbol_prices},
        index=aligned_timestamps,
        dtype=np.float64,
    )
    proxy_returns_override = pd.Series(
        benchmark_returns,
        index=aligned_timestamps[1:],
        dtype=np.float64,
        name="proxy",
    )

    metrics = compute_risk_metrics(
        price_frame=price_frame,
        open_quantity_by_symbol={"AAPL": Decimal("1")},
        window_days=5,
        proxy_returns_override=proxy_returns_override,
    )

    beta_value = float(metrics["beta"])
    assert 1.8 <= beta_value <= 2.2


def test_instrument_scope_risk_estimators_fail_explicitly_when_benchmark_proxy_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Instrument-scope risk estimators should fail-fast when no benchmark proxy is available."""

    get_risk_estimators_response = cast(
        GetRiskEstimatorsResponseCallable,
        _load_callable(
            "get_portfolio_risk_estimators_response",
            task_hint="3.4",
        ),
    )
    client_error_type = _load_client_error_type()
    service_module = import_module("app.portfolio_analytics.service")

    aligned_timestamps = [
        datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index) for index in range(31)
    ]
    symbol_prices = {
        timestamp: Decimal("100") + Decimal(index)
        for index, timestamp in enumerate(aligned_timestamps)
    }

    class _FakeTransactionContext:
        async def __aenter__(self) -> None:
            return None

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

    class _FakeSession:
        def begin(self) -> _FakeTransactionContext:
            return _FakeTransactionContext()

    async def _fake_set_repeatable_read_snapshot(*, db: object) -> None:
        _ = db
        return None

    async def _fake_load_open_position_price_inputs(
        *,
        db: object,
    ) -> tuple[
        dict[str, Decimal],
        Decimal,
        dict[str, dict[datetime, Decimal]],
        dict[str, dict[datetime, Decimal]],
    ]:
        _ = db
        return (
            {"AAPL": Decimal("1")},
            Decimal("100"),
            {"AAPL": symbol_prices},
            {},
        )

    monkeypatch.setattr(
        service_module,
        "_set_repeatable_read_snapshot",
        _fake_set_repeatable_read_snapshot,
    )
    monkeypatch.setattr(
        service_module,
        "_load_open_position_price_inputs",
        _fake_load_open_position_price_inputs,
    )

    with pytest.raises(client_error_type) as exc_info:
        asyncio.run(
            get_risk_estimators_response(
                db=_FakeSession(),
                window_days=30,
                scope=PortfolioQuantReportScope.INSTRUMENT_SYMBOL,
                instrument_symbol="AAPL",
            )
        )

    assert "benchmark return series" in str(exc_info.value).lower()
