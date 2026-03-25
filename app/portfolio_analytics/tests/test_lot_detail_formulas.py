"""Fail-first unit tests for lot-detail analytics formulas and symbol handling."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from importlib import import_module
from typing import cast

import pytest

LotDetailCallable = Callable[..., Mapping[str, object]]


def _load_portfolio_analytics_module() -> object:
    """Load portfolio analytics service module in fail-first mode."""

    try:
        return import_module("app.portfolio_analytics.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.service. "
            "Implement tasks 2.1-2.3 before lot-detail formula tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> LotDetailCallable:
    """Load named callable from portfolio analytics service module."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(LotDetailCallable, candidate)


def _load_error_type(name: str, *, task_hint: str) -> type[Exception]:
    """Load named exception class from portfolio analytics service module."""

    module = _load_portfolio_analytics_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing error type {name}. "
            f"Implement task {task_hint} before this test can pass.",
        )
    if not isinstance(candidate, type) or not issubclass(candidate, Exception):
        pytest.fail(f"Expected {name} to be an Exception subclass.")
    return candidate


def _assert_decimal_field(row: Mapping[str, object], field: str, expected: str) -> None:
    """Assert one numeric field in lot-detail payload using Decimal comparison."""

    if field not in row:
        pytest.fail(f"Lot-detail payload is missing '{field}'.")
    assert Decimal(str(row[field])) == Decimal(expected)


def _get_lot_row(result: Mapping[str, object], *, lot_id: int) -> Mapping[str, object]:
    """Return one lot-detail row by lot identifier."""

    raw_lots = result.get("lots")
    if not isinstance(raw_lots, list):
        pytest.fail("Lot-detail result must include a 'lots' list.")
    lots = cast(list[object], raw_lots)
    for lot_candidate in lots:
        if not isinstance(lot_candidate, Mapping):
            continue
        lot = cast(Mapping[str, object], lot_candidate)
        raw_lot_id = lot.get("lot_id")
        if not isinstance(raw_lot_id, int):
            continue
        if raw_lot_id == lot_id:
            return lot
    pytest.fail(f"Lot-detail result is missing lot_id={lot_id}.")


def test_lot_detail_returns_explainable_lot_rows_for_symbol_variants() -> None:
    """Lot detail should normalize symbol input and include linked dispositions."""

    build_lot_detail = _load_callable("build_lot_detail_from_ledger", task_hint="2.3")

    result = build_lot_detail(
        instrument_symbol=" voo ",
        lots=[
            {
                "id": 501,
                "instrument_symbol": "VOO",
                "opened_on": "2025-01-10",
                "original_qty": "2.000000000",
                "remaining_qty": "1.000000000",
                "total_cost_basis_usd": "100.00",
                "unit_cost_basis_usd": "50.000000000",
            },
            {
                "id": 502,
                "instrument_symbol": "VOO",
                "opened_on": "2025-01-12",
                "original_qty": "1.000000000",
                "remaining_qty": "0.500000000",
                "total_cost_basis_usd": "60.00",
                "unit_cost_basis_usd": "120.000000000",
            },
            {
                "id": 503,
                "instrument_symbol": "AAPL",
                "opened_on": "2025-01-14",
                "original_qty": "3.000000000",
                "remaining_qty": "3.000000000",
                "total_cost_basis_usd": "450.00",
                "unit_cost_basis_usd": "150.000000000",
            },
        ],
        lot_dispositions=[
            {
                "lot_id": 501,
                "sell_transaction_id": 9101,
                "disposition_date": "2025-02-01",
                "matched_qty": "1.000000000",
                "matched_cost_basis_usd": "50.00",
            },
            {
                "lot_id": 502,
                "sell_transaction_id": 9101,
                "disposition_date": "2025-02-01",
                "matched_qty": "0.500000000",
                "matched_cost_basis_usd": "60.00",
            },
        ],
        portfolio_transactions=[
            {
                "id": 9101,
                "instrument_symbol": "VOO",
                "event_date": "2025-02-01",
                "trade_side": "sell",
                "gross_amount_usd": "210.00",
            },
        ],
    )

    assert result.get("instrument_symbol") == "VOO"
    assert isinstance(result.get("lots"), Sequence)

    first_lot = _get_lot_row(result, lot_id=501)
    _assert_decimal_field(first_lot, "remaining_qty", "1.000000000")
    _assert_decimal_field(first_lot, "total_cost_basis_usd", "100.00")

    first_lot_dispositions = first_lot.get("dispositions")
    if not isinstance(first_lot_dispositions, list):
        pytest.fail("Each lot row must include a 'dispositions' list.")
    dispositions = cast(list[object], first_lot_dispositions)
    assert len(dispositions) == 1
    first_disposition = dispositions[0]
    if not isinstance(first_disposition, Mapping):
        pytest.fail("Lot disposition entries must be JSON objects.")
    disposition = cast(Mapping[str, object], first_disposition)
    sell_transaction_id = disposition.get("sell_transaction_id")
    if not isinstance(sell_transaction_id, int):
        pytest.fail("Lot disposition must include integer sell_transaction_id values.")
    assert sell_transaction_id == 9101
    _assert_decimal_field(disposition, "matched_qty", "1.000000000")
    _assert_decimal_field(disposition, "matched_cost_basis_usd", "50.00")


def test_lot_detail_rejects_unknown_instrument_symbol_explicitly() -> None:
    """Unknown symbols should raise explicit client-facing not-found failures."""

    build_lot_detail = _load_callable("build_lot_detail_from_ledger", task_hint="2.3")
    client_error = _load_error_type("PortfolioAnalyticsClientError", task_hint="2.3")

    with pytest.raises(client_error) as exc_info:
        build_lot_detail(
            instrument_symbol="msft",
            lots=[
                {
                    "id": 601,
                    "instrument_symbol": "VOO",
                    "opened_on": "2025-01-10",
                    "original_qty": "2.000000000",
                    "remaining_qty": "2.000000000",
                    "total_cost_basis_usd": "200.00",
                    "unit_cost_basis_usd": "100.000000000",
                }
            ],
            lot_dispositions=[],
            portfolio_transactions=[],
        )

    error = exc_info.value
    assert "not found" in str(error).lower()
    status_code = vars(error).get("status_code")
    if status_code is not None:
        assert int(status_code) == 404
