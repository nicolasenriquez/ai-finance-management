"""Fail-first unit tests for grouped portfolio summary analytics formulas."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from importlib import import_module
from typing import cast

import pytest

SummaryCallable = Callable[..., Sequence[Mapping[str, object]]]


def _load_portfolio_analytics_module() -> object:
    """Load portfolio analytics service module in fail-first mode."""

    try:
        return import_module("app.portfolio_analytics.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.service. "
            "Implement tasks 2.1-2.2 before grouped summary formula tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> SummaryCallable:
    """Load named callable from portfolio analytics service module."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(SummaryCallable, candidate)


def _index_rows_by_symbol(
    summary_rows: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    """Return summary rows indexed by instrument symbol."""

    rows_by_symbol: dict[str, Mapping[str, object]] = {}
    for row in summary_rows:
        symbol = row.get("instrument_symbol")
        if not isinstance(symbol, str):
            pytest.fail("Grouped summary rows must include string instrument_symbol values.")
        rows_by_symbol[symbol] = row
    return rows_by_symbol


def _assert_decimal_field(row: Mapping[str, object], field: str, expected: str) -> None:
    """Assert one numeric KPI field using stable Decimal comparison."""

    if field not in row:
        pytest.fail(f"Grouped summary row is missing KPI field '{field}'.")
    actual = Decimal(str(row[field]))
    assert actual == Decimal(expected)


def test_grouped_summary_computes_ledger_only_kpis_per_instrument() -> None:
    """Grouped summary should emit one ledger-only KPI row per instrument symbol."""

    build_summary = _load_callable(
        "build_grouped_portfolio_summary_from_ledger",
        task_hint="2.2",
    )

    summary_rows = build_summary(
        lots=[
            {
                "id": 101,
                "instrument_symbol": "VOO",
                "remaining_qty": "2.000000000",
                "total_cost_basis_usd": "200.00",
            },
            {
                "id": 102,
                "instrument_symbol": "VOO",
                "remaining_qty": "1.000000000",
                "total_cost_basis_usd": "130.00",
            },
            {
                "id": 103,
                "instrument_symbol": "AAPL",
                "remaining_qty": "3.000000000",
                "total_cost_basis_usd": "450.00",
            },
            {
                "id": 104,
                "instrument_symbol": "NVDA",
                "remaining_qty": "0.000000000",
                "total_cost_basis_usd": "350.00",
            },
        ],
        lot_dispositions=[
            {
                "lot_id": 101,
                "sell_transaction_id": 9001,
                "instrument_symbol": "VOO",
                "matched_cost_basis_usd": "80.00",
            },
            {
                "lot_id": 102,
                "sell_transaction_id": 9001,
                "instrument_symbol": "VOO",
                "matched_cost_basis_usd": "40.00",
            },
            {
                "lot_id": 104,
                "sell_transaction_id": 9002,
                "instrument_symbol": "NVDA",
                "matched_cost_basis_usd": "350.00",
            },
        ],
        portfolio_transactions=[
            {
                "id": 9001,
                "instrument_symbol": "VOO",
                "trade_side": "sell",
                "gross_amount_usd": "250.00",
            },
            {
                "id": 9002,
                "instrument_symbol": "NVDA",
                "trade_side": "sell",
                "gross_amount_usd": "500.00",
            },
        ],
        dividend_events=[
            {
                "instrument_symbol": "VOO",
                "gross_amount_usd": "7.00",
                "taxes_withheld_usd": "1.00",
                "net_amount_usd": "6.00",
            },
            {
                "instrument_symbol": "AAPL",
                "gross_amount_usd": "2.00",
                "taxes_withheld_usd": "0.00",
                "net_amount_usd": "2.00",
            },
        ],
    )

    rows_by_symbol = _index_rows_by_symbol(summary_rows)

    assert set(rows_by_symbol) == {"AAPL", "NVDA", "VOO"}

    voo_row = rows_by_symbol["VOO"]
    _assert_decimal_field(voo_row, "open_quantity", "3.000000000")
    _assert_decimal_field(voo_row, "open_cost_basis_usd", "330.00")
    assert int(voo_row["open_lot_count"]) == 2
    _assert_decimal_field(voo_row, "realized_proceeds_usd", "250.00")
    _assert_decimal_field(voo_row, "realized_cost_basis_usd", "120.00")
    _assert_decimal_field(voo_row, "realized_gain_usd", "130.00")
    _assert_decimal_field(voo_row, "dividend_gross_usd", "7.00")
    _assert_decimal_field(voo_row, "dividend_taxes_usd", "1.00")
    _assert_decimal_field(voo_row, "dividend_net_usd", "6.00")

    aapl_row = rows_by_symbol["AAPL"]
    _assert_decimal_field(aapl_row, "open_quantity", "3.000000000")
    _assert_decimal_field(aapl_row, "open_cost_basis_usd", "450.00")
    assert int(aapl_row["open_lot_count"]) == 1
    _assert_decimal_field(aapl_row, "realized_proceeds_usd", "0.00")
    _assert_decimal_field(aapl_row, "realized_cost_basis_usd", "0.00")
    _assert_decimal_field(aapl_row, "realized_gain_usd", "0.00")
    _assert_decimal_field(aapl_row, "dividend_gross_usd", "2.00")
    _assert_decimal_field(aapl_row, "dividend_taxes_usd", "0.00")
    _assert_decimal_field(aapl_row, "dividend_net_usd", "2.00")

    nvda_row = rows_by_symbol["NVDA"]
    _assert_decimal_field(nvda_row, "open_quantity", "0.000000000")
    _assert_decimal_field(nvda_row, "open_cost_basis_usd", "0.00")
    assert int(nvda_row["open_lot_count"]) == 0
    _assert_decimal_field(nvda_row, "realized_proceeds_usd", "500.00")
    _assert_decimal_field(nvda_row, "realized_cost_basis_usd", "350.00")
    _assert_decimal_field(nvda_row, "realized_gain_usd", "150.00")
    _assert_decimal_field(nvda_row, "dividend_gross_usd", "0.00")
    _assert_decimal_field(nvda_row, "dividend_taxes_usd", "0.00")
    _assert_decimal_field(nvda_row, "dividend_net_usd", "0.00")


def test_grouped_summary_deduplicates_sell_proceeds_per_sell_transaction() -> None:
    """Realized proceeds should count each sell transaction once per instrument."""

    build_summary = _load_callable(
        "build_grouped_portfolio_summary_from_ledger",
        task_hint="2.2",
    )

    summary_rows = build_summary(
        lots=[
            {
                "id": 301,
                "instrument_symbol": "VOO",
                "remaining_qty": "0.000000000",
                "total_cost_basis_usd": "0.00",
            },
            {
                "id": 302,
                "instrument_symbol": "VOO",
                "remaining_qty": "0.000000000",
                "total_cost_basis_usd": "0.00",
            },
        ],
        lot_dispositions=[
            {
                "lot_id": 301,
                "sell_transaction_id": 9101,
                "instrument_symbol": "VOO",
                "matched_cost_basis_usd": "100.00",
            },
            {
                "lot_id": 302,
                "sell_transaction_id": 9101,
                "instrument_symbol": "VOO",
                "matched_cost_basis_usd": "90.00",
            },
        ],
        portfolio_transactions=[
            {
                "id": 9101,
                "instrument_symbol": "VOO",
                "trade_side": "sell",
                "gross_amount_usd": "250.00",
            },
        ],
        dividend_events=[],
    )

    rows_by_symbol = _index_rows_by_symbol(summary_rows)
    assert set(rows_by_symbol) == {"VOO"}

    voo_row = rows_by_symbol["VOO"]
    _assert_decimal_field(voo_row, "realized_proceeds_usd", "250.00")
    _assert_decimal_field(voo_row, "realized_cost_basis_usd", "190.00")
    _assert_decimal_field(voo_row, "realized_gain_usd", "60.00")
