"""Fail-first tests for FIFO lot accounting and split-adjusted open lots."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

AccountingCallable = Callable[..., object]

_FINANCE_CASES_PATH = Path(__file__).parent / "fixtures" / "dataset_1_v1_finance_cases.json"


def _load_accounting_module() -> object:
    """Load portfolio-ledger accounting module in fail-first mode."""

    try:
        return import_module("app.portfolio_ledger.accounting")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ledger.accounting. "
            "Implement tasks 2.1-3.2 before FIFO accounting tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> AccountingCallable:
    """Load named callable from portfolio-ledger accounting module."""

    module = _load_accounting_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(AccountingCallable, candidate)


def _load_finance_case(case_name: str) -> dict[str, object]:
    """Load one deterministic finance case by key."""

    case_payload = cast(dict[str, object], json.loads(_FINANCE_CASES_PATH.read_text()))
    case = case_payload.get(case_name)
    if case is None:
        pytest.fail(
            f"Finance test fixture is missing case '{case_name}' in {_FINANCE_CASES_PATH}.",
        )
    return cast(dict[str, object], case)


def _sum_total_basis(open_lots: Sequence[Mapping[str, object]]) -> Decimal:
    """Return total lot basis from deterministic string values."""

    return sum(
        (Decimal(str(lot["total_cost_basis_usd"])) for lot in open_lots),
        start=Decimal("0"),
    )


def test_fifo_matching_consumes_oldest_open_lots_first() -> None:
    """Sell matching should consume open lots in FIFO order."""

    match_fifo = _load_callable("match_sell_trade_fifo", task_hint="3.2")
    case = _load_finance_case("fifo_sell")

    open_lots = cast(list[Mapping[str, object]], case["open_lots"])
    sell_trade = cast(Mapping[str, object], case["sell_trade"])
    expected = cast(Mapping[str, object], case["expected"])
    expected_dispositions = cast(list[Mapping[str, object]], expected["dispositions"])

    result = cast(Mapping[str, object], match_fifo(open_lots=open_lots, sell_trade=sell_trade))
    dispositions = cast(list[Mapping[str, object]], result["dispositions"])

    assert [item["lot_id"] for item in dispositions] == [
        item["lot_id"] for item in expected_dispositions
    ]
    assert [item["matched_qty"] for item in dispositions] == [
        item["matched_qty"] for item in expected_dispositions
    ]
    assert [item["matched_cost_basis_usd"] for item in dispositions] == [
        item["matched_cost_basis_usd"] for item in expected_dispositions
    ]
    assert Decimal(str(result["total_matched_basis_usd"])) == Decimal(
        str(expected["total_matched_basis_usd"])
    )


def test_realized_gain_uses_fifo_matched_basis() -> None:
    """Realized gain should use sell proceeds minus FIFO-matched basis."""

    calculate_realized_gain = _load_callable("calculate_realized_gain_from_fifo", task_hint="3.2")
    case = _load_finance_case("fifo_sell")

    sell_trade = cast(Mapping[str, object], case["sell_trade"])
    expected = cast(Mapping[str, object], case["expected"])
    dispositions = cast(list[Mapping[str, object]], expected["dispositions"])

    realized_gain_usd = cast(
        Decimal,
        calculate_realized_gain(dispositions=dispositions, sell_trade=sell_trade),
    )

    assert realized_gain_usd == Decimal(str(expected["realized_gain_usd"]))


def test_split_adjustment_preserves_total_basis_and_updates_unit_basis() -> None:
    """Split handling should preserve total lot basis while adjusting quantities."""

    apply_split = _load_callable("apply_split_to_open_lots", task_hint="3.2")
    case = _load_finance_case("split_adjustment")

    open_lots = cast(list[Mapping[str, object]], case["open_lots"])
    split_event = cast(Mapping[str, object], case["split_event"])
    expected = cast(Mapping[str, object], case["expected"])
    expected_open_lots = cast(list[Mapping[str, object]], expected["open_lots"])

    adjusted_lots = cast(
        list[Mapping[str, object]],
        apply_split(open_lots=open_lots, split_event=split_event),
    )

    assert adjusted_lots == expected_open_lots
    assert _sum_total_basis(adjusted_lots) == _sum_total_basis(open_lots)
