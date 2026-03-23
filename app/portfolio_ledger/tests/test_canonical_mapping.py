"""Fail-first tests for canonical-to-ledger mapping and lineage preservation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date
from importlib import import_module
from typing import cast

import pytest

LedgerEventMappingCallable = Callable[..., Mapping[str, object]]


def _load_portfolio_ledger_module() -> object:
    """Load portfolio-ledger service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ledger.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ledger.service. "
            "Implement tasks 2.1-3.1 before canonical-to-ledger mapping tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> LedgerEventMappingCallable:
    """Load named callable from portfolio-ledger service module."""

    module = _load_portfolio_ledger_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(LedgerEventMappingCallable, candidate)


def _build_persisted_canonical_record(
    *,
    record_id: int,
    source_document_id: int,
    import_job_id: int,
    fingerprint: str,
    event_type: str,
    event_date: date,
    instrument_symbol: str,
    trade_side: str | None,
    canonical_payload: Mapping[str, object],
) -> dict[str, object]:
    """Build persisted canonical-record input used by mapping tests."""

    return {
        "id": record_id,
        "source_document_id": source_document_id,
        "import_job_id": import_job_id,
        "fingerprint": fingerprint,
        "event_type": event_type,
        "event_date": event_date,
        "instrument_symbol": instrument_symbol,
        "trade_side": trade_side,
        "canonical_payload": dict(canonical_payload),
    }


def test_trade_mapping_preserves_lineage_from_persisted_canonical_record() -> None:
    """Trade records should map to portfolio transactions with lineage."""

    map_record = _load_callable("map_canonical_record_to_ledger_event", task_hint="3.1")
    record = _build_persisted_canonical_record(
        record_id=101,
        source_document_id=11,
        import_job_id=22,
        fingerprint="fp-trade-101",
        event_type="trade",
        event_date=date(2025, 1, 10),
        instrument_symbol="VOO",
        trade_side="buy",
        canonical_payload={
            "event_type": "trade",
            "trade_date": "2025-01-10",
            "instrument_symbol": "VOO",
            "trade_side": "buy",
            "aporte_usd": "100.00",
            "acciones_compradas_qty": "1.000000000",
        },
    )

    mapped_event = map_record(record=record)
    lineage = cast(Mapping[str, object], mapped_event["lineage"])

    assert mapped_event["target_table"] == "portfolio_transaction"
    assert mapped_event["event_type"] == "trade"
    assert mapped_event["event_date"] == date(2025, 1, 10)
    assert mapped_event["instrument_symbol"] == "VOO"
    assert lineage["source_document_id"] == 11
    assert lineage["import_job_id"] == 22
    assert lineage["canonical_record_id"] == 101
    assert lineage["canonical_fingerprint"] == "fp-trade-101"


def test_dividend_mapping_preserves_lineage_from_persisted_canonical_record() -> None:
    """Dividend records should map to dividend events with lineage."""

    map_record = _load_callable("map_canonical_record_to_ledger_event", task_hint="3.1")
    record = _build_persisted_canonical_record(
        record_id=102,
        source_document_id=12,
        import_job_id=23,
        fingerprint="fp-dividend-102",
        event_type="dividend",
        event_date=date(2025, 2, 3),
        instrument_symbol="VOO",
        trade_side=None,
        canonical_payload={
            "event_type": "dividend",
            "dividend_date": "2025-02-03",
            "instrument_symbol": "VOO",
            "gross_usd": "5.00",
            "taxes_usd": "0.50",
            "net_usd": "4.50",
        },
    )

    mapped_event = map_record(record=record)
    lineage = cast(Mapping[str, object], mapped_event["lineage"])

    assert mapped_event["target_table"] == "dividend_event"
    assert mapped_event["event_type"] == "dividend"
    assert mapped_event["event_date"] == date(2025, 2, 3)
    assert mapped_event["instrument_symbol"] == "VOO"
    assert lineage["source_document_id"] == 12
    assert lineage["import_job_id"] == 23
    assert lineage["canonical_record_id"] == 102
    assert lineage["canonical_fingerprint"] == "fp-dividend-102"


def test_split_mapping_preserves_lineage_from_persisted_canonical_record() -> None:
    """Split records should map to corporate-action events with lineage."""

    map_record = _load_callable("map_canonical_record_to_ledger_event", task_hint="3.1")
    record = _build_persisted_canonical_record(
        record_id=103,
        source_document_id=13,
        import_job_id=24,
        fingerprint="fp-split-103",
        event_type="split",
        event_date=date(2025, 2, 10),
        instrument_symbol="VOO",
        trade_side=None,
        canonical_payload={
            "event_type": "split",
            "split_date": "2025-02-10",
            "instrument_symbol": "VOO",
            "shares_before_qty": "1.000000000",
            "shares_after_qty": "2.000000000",
            "split_ratio_value": "2.00",
        },
    )

    mapped_event = map_record(record=record)
    lineage = cast(Mapping[str, object], mapped_event["lineage"])

    assert mapped_event["target_table"] == "corporate_action_event"
    assert mapped_event["event_type"] == "split"
    assert mapped_event["event_date"] == date(2025, 2, 10)
    assert mapped_event["instrument_symbol"] == "VOO"
    assert lineage["source_document_id"] == 13
    assert lineage["import_job_id"] == 24
    assert lineage["canonical_record_id"] == 103
    assert lineage["canonical_fingerprint"] == "fp-split-103"


def test_internal_decimal_coercion_rejects_non_finite_values() -> None:
    """Decimal coercion should reject non-finite canonical payload values."""

    module = _load_portfolio_ledger_module()
    candidate = getattr(module, "_coerce_decimal", None)
    if candidate is None:
        pytest.fail(
            "Fail-first baseline: missing helper _coerce_decimal(). "
            "Implement task 3.1 decimal validation before this test can pass.",
        )
    coerce_decimal = cast(Callable[..., object], candidate)

    invalid_values: tuple[str, ...] = ("NaN", "Infinity", "-Infinity")
    for invalid_value in invalid_values:
        with pytest.raises(ValueError, match="finite decimal"):
            coerce_decimal(
                value=invalid_value,
                field="aporte_usd",
                canonical_record_id=999,
            )
