"""Regression tests for analytics snapshot consistency behavior."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.portfolio_analytics.service import (
    get_portfolio_lot_detail_response,
    get_portfolio_summary_response,
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


@pytest.mark.asyncio
async def test_summary_response_sets_repeatable_read_transaction_before_queries() -> None:
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
async def test_lot_detail_response_sets_repeatable_read_transaction_before_queries() -> None:
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
