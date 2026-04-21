"""Fail-first tests for PDF verification behavior."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from app.pdf_verification.schemas import PdfVerificationResult

VerificationCallable = Callable[..., object]

_GOLDEN_PDF_PATH = Path("app/golden_sets/dataset_1/202602_stocks.pdf")


def _load_golden_pdf_bytes() -> bytes:
    """Load dataset 1 PDF bytes from repository fixtures."""

    return _GOLDEN_PDF_PATH.read_bytes()


def _seed_storage_key(tmp_path: Path) -> str:
    """Write dataset 1 PDF into a temporary storage root."""

    storage_key = "dataset_1.pdf"
    (tmp_path / storage_key).write_bytes(_load_golden_pdf_bytes())
    return storage_key


def _load_verification_module() -> object:
    """Load verification service module in fail-first mode."""

    try:
        return import_module("app.pdf_verification.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.pdf_verification.service. "
            "Implement tasks 3.1-3.2 before verification tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> VerificationCallable:
    """Load named callable from verification service module."""

    module = _load_verification_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(VerificationCallable, candidate)


def test_verify_pdf_from_storage_returns_successful_report(tmp_path: Path) -> None:
    """Verification should return a successful report for dataset 1."""

    verify_pdf_from_storage = _load_callable("verify_pdf_from_storage", task_hint="3.1")
    storage_key = _seed_storage_key(tmp_path)

    result = cast(
        PdfVerificationResult,
        verify_pdf_from_storage(storage_key=storage_key, storage_root=tmp_path),
    )

    assert result.storage_key == storage_key
    assert result.status == "passed"
    assert result.summary.mismatch_count == 0


def test_build_verification_report_includes_mismatch_evidence() -> None:
    """Verification report should include actionable mismatch evidence fields."""

    build_verification_report = _load_callable(
        "build_verification_report", task_hint="3.2"
    )

    expected_records = [
        {
            "table_name": "compra_venta_activos",
            "row_id": 1,
            "row_index": 1,
            "source_page": 1,
            "raw_values": {"aporte_dolares": "US $ 112,80"},
        }
    ]
    actual_records = [
        {
            "table_name": "compra_venta_activos",
            "row_id": 1,
            "row_index": 1,
            "source_page": 1,
            "raw_values": {"aporte_dolares": "US $ 999,99"},
        }
    ]

    report = cast(
        PdfVerificationResult,
        build_verification_report(
            storage_key="dataset_1.pdf",
            expected_records=expected_records,
            actual_records=actual_records,
        ),
    )

    assert report.status == "failed"
    assert report.summary.mismatch_count == 1
    mismatch = report.mismatches[0]
    assert mismatch.table_name == "compra_venta_activos"
    assert mismatch.row_id == 1
    assert mismatch.row_index == 1
    assert mismatch.source_page == 1
    assert mismatch.field == "aporte_dolares"
    assert mismatch.expected_raw == "US $ 112,80"
    assert mismatch.actual_raw == "US $ 999,99"
