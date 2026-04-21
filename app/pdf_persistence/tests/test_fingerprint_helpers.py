"""Fail-first tests for PDF persistence fingerprint helper behavior."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import cast

import pytest
from pydantic import ValidationError

from app.pdf_persistence.schemas import PdfPersistenceSummary

PersistenceCallable = Callable[..., object]


def _load_persistence_module() -> object:
    """Load persistence service module in fail-first mode."""

    try:
        return import_module("app.pdf_persistence.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.pdf_persistence.service. "
            "Implement tasks 2.3 and 3.1 before persistence helper tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> PersistenceCallable:
    """Load named callable from persistence service module."""

    module = _load_persistence_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(PersistenceCallable, candidate)


def test_build_canonical_record_fingerprint_is_deterministic() -> None:
    """Fingerprint generation should be deterministic for equal canonical input."""

    build_fingerprint = _load_callable(
        "build_canonical_record_fingerprint", task_hint="2.3"
    )

    canonical_record = {
        "event_type": "trade",
        "trade_side": "buy",
        "trade_date": "2025-01-10",
        "instrument_symbol": "VOO",
        "aporte_usd": "10.00",
        "rescate_usd": None,
        "acciones_compradas_qty": "0.010000000",
        "acciones_vendidas_qty": None,
        "provenance": {
            "table_name": "compra_venta_activos",
            "row_index": 1,
            "source_page": 1,
        },
    }

    first_fingerprint = cast(
        str,
        build_fingerprint(
            record=canonical_record,
            source_type="pdf_statement",
            source_system="broker_pdf_dataset_1",
            fingerprint_version="v1",
        ),
    )
    second_fingerprint = cast(
        str,
        build_fingerprint(
            record=canonical_record,
            source_type="pdf_statement",
            source_system="broker_pdf_dataset_1",
            fingerprint_version="v1",
        ),
    )

    assert first_fingerprint == second_fingerprint
    assert first_fingerprint


def test_build_canonical_record_fingerprint_is_source_scoped() -> None:
    """Fingerprint should change when source-scoping fields differ."""

    build_fingerprint = _load_callable(
        "build_canonical_record_fingerprint", task_hint="2.3"
    )

    canonical_record = {
        "event_type": "dividend",
        "dividend_date": "2025-01-10",
        "instrument_symbol": "VOO",
        "gross_usd": "5.00",
        "taxes_usd": "0.50",
        "net_usd": "4.50",
        "provenance": {
            "table_name": "dividendos_recibidos",
            "row_index": 3,
            "source_page": 2,
        },
    }

    dataset_1_fingerprint = cast(
        str,
        build_fingerprint(
            record=canonical_record,
            source_type="pdf_statement",
            source_system="broker_pdf_dataset_1",
            fingerprint_version="v1",
        ),
    )
    dataset_2_fingerprint = cast(
        str,
        build_fingerprint(
            record=canonical_record,
            source_type="pdf_statement",
            source_system="broker_pdf_dataset_2",
            fingerprint_version="v1",
        ),
    )

    assert dataset_1_fingerprint != dataset_2_fingerprint


def test_calculate_persistence_counts_handles_duplicates() -> None:
    """Duplicate detection should classify inserted versus duplicate fingerprints."""

    calculate_counts = _load_callable("calculate_persistence_counts", task_hint="2.3")

    inserted_records, duplicate_records = cast(
        tuple[int, int],
        calculate_counts(
            candidate_fingerprints=("fp-a", "fp-b", "fp-b", "fp-c"),
            existing_fingerprints={"fp-b", "fp-z"},
        ),
    )

    assert inserted_records == 2
    assert duplicate_records == 2


def test_build_persistence_summary_enforces_accounting() -> None:
    """Persistence summary helper should reject invalid record accounting."""

    build_summary = _load_callable("build_persistence_summary", task_hint="2.3")

    valid_summary = cast(
        PdfPersistenceSummary,
        build_summary(
            normalized_records=4,
            inserted_records=1,
            duplicate_records=3,
        ),
    )
    assert valid_summary.normalized_records == 4
    assert valid_summary.inserted_records == 1
    assert valid_summary.duplicate_records == 3

    with pytest.raises((ValidationError, ValueError)):
        build_summary(
            normalized_records=4,
            inserted_records=1,
            duplicate_records=1,
        )
