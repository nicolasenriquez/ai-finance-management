"""Contract tests for dataset-1 v1 deterministic finance golden cases."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import cast

_FINANCE_CASES_PATH = (
    Path(__file__).parent / "fixtures" / "dataset_1_v1_finance_cases.json"
)
_REQUIRED_CASES = {"fifo_sell", "dividend_income", "split_adjustment"}


def _load_finance_cases() -> dict[str, object]:
    """Load checked-in deterministic finance golden cases."""

    payload = cast(dict[str, object], json.loads(_FINANCE_CASES_PATH.read_text()))
    return payload


def _sum_total_basis(open_lots: list[dict[str, object]]) -> Decimal:
    """Return total basis from deterministic lot payload values."""

    return sum(
        (Decimal(str(lot["total_cost_basis_usd"])) for lot in open_lots),
        start=Decimal("0"),
    )


def test_dataset_1_v1_finance_fixture_includes_fifo_dividend_split_cases() -> None:
    """Task 2.3 must lock FIFO, dividend, and split golden-case coverage."""

    cases = _load_finance_cases()
    assert _REQUIRED_CASES.issubset(cases.keys())

    for case_name in _REQUIRED_CASES:
        case = cast(dict[str, object], cases[case_name])
        assert case["policy_version"] == "dataset_1_v1_fifo"


def test_dividend_case_keeps_lot_basis_unchanged_and_income_explicit() -> None:
    """Dividend golden case should lock no-lot-mutation policy behavior."""

    cases = _load_finance_cases()
    case = cast(dict[str, object], cases["dividend_income"])

    open_lots_before = cast(list[dict[str, object]], case["open_lots_before"])
    expected = cast(dict[str, object], case["expected"])
    open_lots_after = cast(list[dict[str, object]], expected["open_lots_after"])
    income_breakdown = cast(dict[str, object], expected["income_breakdown"])

    assert open_lots_after == open_lots_before
    assert _sum_total_basis(open_lots_after) == _sum_total_basis(open_lots_before)

    gross_usd = Decimal(str(income_breakdown["gross_usd"]))
    taxes_usd = Decimal(str(income_breakdown["taxes_usd"]))
    net_usd = Decimal(str(income_breakdown["net_usd"]))
    assert gross_usd - taxes_usd == net_usd
