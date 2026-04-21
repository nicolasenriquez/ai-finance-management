"""Unit tests for optional benchmark overlays in portfolio time-series points."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from app.portfolio_analytics import service as portfolio_analytics_service
from app.portfolio_analytics.service import build_portfolio_time_series_points

ResolveBenchmarkSeriesCallable = Callable[
    ...,
    dict[str, dict[datetime, Decimal]],
]
_RESOLVER_ATTRIBUTE_NAME = "_resolve_benchmark_price_series_by_id"


def test_time_series_points_include_benchmark_overlay_when_series_is_available() -> (
    None
):
    """Time-series points should expose normalized benchmark overlays when available."""

    first_timestamp = datetime(2025, 1, 1, tzinfo=UTC)
    second_timestamp = datetime(2025, 1, 2, tzinfo=UTC)
    aligned_timestamps = [first_timestamp, second_timestamp]

    points = build_portfolio_time_series_points(
        aligned_timestamps=aligned_timestamps,
        open_quantity_by_symbol={"AAPL": Decimal("1.000000000")},
        price_series_by_symbol={
            "AAPL": {
                first_timestamp: Decimal("100.00"),
                second_timestamp: Decimal("120.00"),
            }
        },
        total_open_cost_basis_usd=Decimal("100.00"),
        benchmark_price_series_by_id={
            "benchmark_sp500_value_usd": {
                first_timestamp: Decimal("50.00"),
                second_timestamp: Decimal("55.00"),
            }
        },
    )

    assert len(points) == 2
    assert points[0]["portfolio_value_usd"] == Decimal("100.00")
    assert points[1]["portfolio_value_usd"] == Decimal("120.00")
    assert points[0]["benchmark_sp500_value_usd"] == Decimal("100.00")
    assert points[1]["benchmark_sp500_value_usd"] == Decimal("110.00")
    assert points[0]["benchmark_nasdaq100_value_usd"] is None
    assert points[1]["benchmark_nasdaq100_value_usd"] is None


def test_resolve_benchmark_price_series_prefers_first_full_coverage_candidate() -> None:
    """Benchmark resolver should pick deterministic first candidate with full coverage."""

    first_timestamp = datetime(2025, 1, 1, tzinfo=UTC)
    second_timestamp = datetime(2025, 1, 2, tzinfo=UTC)
    aligned_timestamps = [first_timestamp, second_timestamp]

    resolve_benchmark_price_series_by_id = cast(
        ResolveBenchmarkSeriesCallable,
        getattr(portfolio_analytics_service, _RESOLVER_ATTRIBUTE_NAME),
    )
    resolved = resolve_benchmark_price_series_by_id(
        aligned_timestamps=aligned_timestamps,
        candidate_price_series_by_symbol={
            "VOO": {
                first_timestamp: Decimal("100.00"),
                second_timestamp: Decimal("101.00"),
            },
            "SPY": {
                first_timestamp: Decimal("99.00"),
            },
            "QQQ": {
                first_timestamp: Decimal("200.00"),
                second_timestamp: Decimal("210.00"),
            },
        },
    )

    assert set(resolved) == {
        "benchmark_sp500_value_usd",
        "benchmark_nasdaq100_value_usd",
    }
    assert resolved["benchmark_sp500_value_usd"][first_timestamp] == Decimal("100.00")
    assert resolved["benchmark_sp500_value_usd"][second_timestamp] == Decimal("101.00")
    assert resolved["benchmark_nasdaq100_value_usd"][first_timestamp] == Decimal(
        "200.00"
    )
    assert resolved["benchmark_nasdaq100_value_usd"][second_timestamp] == Decimal(
        "210.00"
    )
