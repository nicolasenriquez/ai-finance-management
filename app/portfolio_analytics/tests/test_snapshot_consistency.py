"""Regression tests for analytics snapshot consistency behavior."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.portfolio_analytics.schemas import PortfolioChartPeriod
from app.portfolio_analytics.service import (
    get_portfolio_contribution_response,
    get_portfolio_lot_detail_response,
    get_portfolio_risk_estimators_response,
    get_portfolio_summary_response,
    get_portfolio_time_series_response,
)


class _FakeScalarResult:
    """Minimal scalar-result wrapper used by fake execute responses."""

    def __init__(self, rows: Sequence[object]) -> None:
        self._rows = list(rows)

    def all(self) -> list[object]:
        """Return all fake scalar rows."""

        return list(self._rows)


class _FakeExecuteResult:
    """Minimal SQLAlchemy-like result used by analytics service tests."""

    def __init__(
        self,
        *,
        rows: Sequence[object] | None = None,
        scalar_value: object | None = None,
    ) -> None:
        self._rows = list(rows or [])
        self._scalar_value = scalar_value

    def scalars(self) -> _FakeScalarResult:
        """Return fake scalar rows."""

        return _FakeScalarResult(self._rows)

    def scalar_one_or_none(self) -> object | None:
        """Return one scalar value or None."""

        return self._scalar_value


class _FakeBeginContext:
    """Async context manager used to emulate AsyncSession.begin()."""

    async def __aenter__(self) -> None:
        """Enter fake transaction context."""

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: object | None,
    ) -> bool:
        """Exit fake transaction context."""

        return False


class _FakeSession:
    """Minimal fake AsyncSession recording execute statements in order."""

    def __init__(self, responses: Sequence[_FakeExecuteResult]) -> None:
        self._responses: Iterator[_FakeExecuteResult] = iter(responses)
        self.executed_sql: list[str] = []

    def begin(self) -> _FakeBeginContext:
        """Return a fake transaction context manager."""

        return _FakeBeginContext()

    async def execute(self, statement: object) -> _FakeExecuteResult:
        """Record SQL text and return queued fake result."""

        self.executed_sql.append(str(statement))
        try:
            return next(self._responses)
        except StopIteration as exc:
            pytest.fail("Unexpected extra execute() call in analytics service.")
            raise AssertionError from exc


def _assert_no_mutation_sql(executed_sql: Sequence[str]) -> None:
    """Assert recorded SQL statements do not contain mutation keywords."""

    mutating_keywords = (" INSERT ", " UPDATE ", " DELETE ", " MERGE ")
    for statement in executed_sql:
        normalized_statement = f" {statement.upper()} "
        assert not any(keyword in normalized_statement for keyword in mutating_keywords)


def _build_fake_price_rows(*, points: int) -> list[SimpleNamespace]:
    """Build deterministic fake USD price-history rows for two symbols."""

    rows: list[SimpleNamespace] = []
    for day_offset in range(points):
        trading_day = date.fromordinal(date(2025, 1, 1).toordinal() + day_offset)
        rows.append(
            SimpleNamespace(
                instrument_symbol="AAPL",
                market_timestamp=None,
                trading_date=trading_day,
                price_value=Decimal("175.00") + Decimal(day_offset),
            )
        )
        rows.append(
            SimpleNamespace(
                instrument_symbol="VOO",
                market_timestamp=None,
                trading_date=trading_day,
                price_value=Decimal("95.00") + (Decimal(day_offset) * Decimal("0.5")),
            )
        )
    return rows


async def _fake_snapshot_coverage(**_kwargs: object) -> SimpleNamespace:
    """Return deterministic snapshot coverage for fake service executions."""

    return SimpleNamespace(
        snapshot_id=99,
        snapshot_key="test-snapshot",
        snapshot_captured_at=datetime(2025, 2, 20, 0, 0, 0, tzinfo=UTC),
        latest_close_price_usd_by_symbol={
            "AAPL": Decimal("190.00"),
            "VOO": Decimal("105.00"),
        },
    )


@pytest.mark.asyncio
async def test_summary_response_sets_repeatable_read_transaction_before_queries() -> (
    None
):
    """Summary service must set repeatable-read/read-only transaction semantics first."""

    fake_session = _FakeSession(
        responses=(
            _FakeExecuteResult(),
            _FakeExecuteResult(rows=[]),
            _FakeExecuteResult(rows=[]),
            _FakeExecuteResult(rows=[]),
            _FakeExecuteResult(rows=[]),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
        )
    )

    response = await get_portfolio_summary_response(
        db=cast(AsyncSession, fake_session),
    )

    assert response.rows == []
    assert fake_session.executed_sql
    assert fake_session.executed_sql[0].strip().upper() == (
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    )


@pytest.mark.asyncio
async def test_time_series_response_remains_read_only_and_no_mutation_sql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Time-series service must stay read-only and avoid mutating SQL statements."""

    fake_lot = SimpleNamespace(
        instrument_symbol="VOO",
        remaining_qty=Decimal("1.500000000"),
        total_cost_basis_usd=Decimal("160.00"),
    )
    fake_session = _FakeSession(
        responses=(
            _FakeExecuteResult(),
            _FakeExecuteResult(rows=[fake_lot]),
            _FakeExecuteResult(rows=_build_fake_price_rows(points=35)),
            _FakeExecuteResult(scalar_value=datetime(2025, 2, 20, 0, 0, 0, tzinfo=UTC)),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
        )
    )
    monkeypatch.setattr(
        "app.portfolio_analytics.service.resolve_latest_consistent_snapshot_coverage_for_symbols",
        _fake_snapshot_coverage,
    )

    response = await get_portfolio_time_series_response(
        db=cast(AsyncSession, fake_session),
        period=PortfolioChartPeriod.MAX,
    )

    assert len(response.points) == 35
    assert fake_session.executed_sql
    assert fake_session.executed_sql[0].strip().upper() == (
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    )
    _assert_no_mutation_sql(fake_session.executed_sql[1:])


@pytest.mark.asyncio
async def test_contribution_response_remains_read_only_and_no_mutation_sql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contribution service must stay read-only and avoid mutating SQL statements."""

    fake_lot = SimpleNamespace(
        instrument_symbol="VOO",
        remaining_qty=Decimal("1.500000000"),
        total_cost_basis_usd=Decimal("160.00"),
    )
    fake_session = _FakeSession(
        responses=(
            _FakeExecuteResult(),
            _FakeExecuteResult(rows=[fake_lot]),
            _FakeExecuteResult(rows=_build_fake_price_rows(points=35)),
            _FakeExecuteResult(scalar_value=datetime(2025, 2, 20, 0, 0, 0, tzinfo=UTC)),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
        )
    )
    monkeypatch.setattr(
        "app.portfolio_analytics.service.resolve_latest_consistent_snapshot_coverage_for_symbols",
        _fake_snapshot_coverage,
    )

    response = await get_portfolio_contribution_response(
        db=cast(AsyncSession, fake_session),
        period=PortfolioChartPeriod.MAX,
    )

    assert len(response.rows) == 1
    assert fake_session.executed_sql
    assert fake_session.executed_sql[0].strip().upper() == (
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    )
    _assert_no_mutation_sql(fake_session.executed_sql[1:])


@pytest.mark.asyncio
async def test_risk_estimator_response_remains_read_only_and_no_mutation_sql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Risk-estimator service must stay read-only and avoid mutating SQL statements."""

    fake_lot = SimpleNamespace(
        instrument_symbol="VOO",
        remaining_qty=Decimal("1.500000000"),
        total_cost_basis_usd=Decimal("160.00"),
    )
    fake_session = _FakeSession(
        responses=(
            _FakeExecuteResult(),
            _FakeExecuteResult(rows=[fake_lot]),
            _FakeExecuteResult(rows=_build_fake_price_rows(points=35)),
            _FakeExecuteResult(scalar_value=datetime(2025, 2, 20, 0, 0, 0, tzinfo=UTC)),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
        )
    )
    monkeypatch.setattr(
        "app.portfolio_analytics.service.resolve_latest_consistent_snapshot_coverage_for_symbols",
        _fake_snapshot_coverage,
    )

    response = await get_portfolio_risk_estimators_response(
        db=cast(AsyncSession, fake_session),
        window_days=30,
    )

    assert len(response.metrics) == 6
    assert {metric.estimator_id for metric in response.metrics} == {
        "volatility_annualized",
        "max_drawdown",
        "beta",
        "downside_deviation_annualized",
        "value_at_risk_95",
        "expected_shortfall_95",
    }
    assert fake_session.executed_sql
    assert fake_session.executed_sql[0].strip().upper() == (
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    )
    _assert_no_mutation_sql(fake_session.executed_sql[1:])


@pytest.mark.asyncio
async def test_lot_detail_response_sets_repeatable_read_transaction_before_queries() -> (
    None
):
    """Lot-detail service must set repeatable-read/read-only transaction semantics first."""

    fake_lot = SimpleNamespace(
        id=101,
        instrument_symbol="VOO",
        opened_on=date(2025, 1, 10),
        original_qty=Decimal("2.000000000"),
        remaining_qty=Decimal("1.000000000"),
        total_cost_basis_usd=Decimal("100.00"),
        unit_cost_basis_usd=Decimal("50.000000000"),
    )
    fake_session = _FakeSession(
        responses=(
            _FakeExecuteResult(),
            _FakeExecuteResult(rows=[fake_lot]),
            _FakeExecuteResult(rows=[]),
            _FakeExecuteResult(
                scalar_value=datetime(2025, 2, 20, 0, 0, 0, tzinfo=UTC),
            ),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
            _FakeExecuteResult(scalar_value=None),
        )
    )

    response = await get_portfolio_lot_detail_response(
        instrument_symbol=" voo ",
        db=cast(AsyncSession, fake_session),
    )

    assert response.instrument_symbol == "VOO"
    assert len(response.lots) == 1
    assert fake_session.executed_sql
    assert fake_session.executed_sql[0].strip().upper() == (
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    )
