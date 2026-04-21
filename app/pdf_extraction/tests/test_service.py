"""Fail-first tests for PDF extraction service behavior."""

from __future__ import annotations

import json
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from app.pdf_extraction.schemas import PdfExtractedTable, PdfExtractionResult

ExtractionCallable = Callable[..., PdfExtractionResult]

_GOLDEN_PDF_PATH = Path("app/golden_sets/dataset_1/202602_stocks.pdf")
_GOLDEN_JSON_PATH = Path("app/golden_sets/dataset_1/202602_stocks.json")


def _load_golden_pdf_bytes() -> bytes:
    """Load dataset 1 PDF bytes from repository fixtures."""

    return _GOLDEN_PDF_PATH.read_bytes()


def _load_golden_json() -> dict[str, object]:
    """Load dataset 1 JSON contract fixture."""

    return cast(
        dict[str, object], json.loads(_GOLDEN_JSON_PATH.read_text(encoding="utf-8"))
    )


def _seed_storage_key(tmp_path: Path) -> str:
    """Write dataset 1 PDF into a temporary storage root."""

    storage_key = "dataset_1.pdf"
    (tmp_path / storage_key).write_bytes(_load_golden_pdf_bytes())
    return storage_key


def _load_extractor() -> ExtractionCallable:
    """Load extraction entrypoint expected from the service module.

    This helper intentionally fails the test run when the entrypoint is
    missing. That preserves fail-first behavior until task 2.x implements
    the real service.
    """

    try:
        module = import_module("app.pdf_extraction.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.pdf_extraction.service. "
            "Implement task 2.1 to make extraction tests executable.",
        )
        raise AssertionError from exc

    extractor = getattr(module, "extract_pdf_from_storage", None)
    if extractor is None:
        pytest.fail(
            "Fail-first baseline: missing callable extract_pdf_from_storage(). "
            "Implement task 2.1 before these assertions can pass.",
        )

    return cast(ExtractionCallable, extractor)


def _table_by_name(result: PdfExtractionResult, table_name: str) -> PdfExtractedTable:
    """Return extracted table by logical table name."""

    for table in result.tables:
        if table.table_name == table_name:
            return table
    pytest.fail(f"Expected table '{table_name}' missing from extraction result.")
    raise AssertionError


def test_extract_dataset1_matches_expected_summary_contract(tmp_path: Path) -> None:
    """Extraction should match dataset 1 table-level summary counts."""

    extractor = _load_extractor()
    storage_key = _seed_storage_key(tmp_path)

    result = extractor(storage_key=storage_key, storage_root=tmp_path)

    assert result.engine == "pdfplumber"
    assert result.storage_key == storage_key
    assert result.source_pdf_pages == 9

    table_names = [table.table_name for table in result.tables]
    assert table_names == ["compra_venta_activos", "dividendos_recibidos", "splits"]

    counts_by_table = {table.table_name: len(table.rows) for table in result.tables}
    assert counts_by_table == {
        "compra_venta_activos": 136,
        "dividendos_recibidos": 34,
        "splits": 1,
    }


def test_extract_dataset1_filters_repeated_headers_and_footer_rows(
    tmp_path: Path,
) -> None:
    """Extraction should not emit known header/footer artifacts as rows."""

    extractor = _load_extractor()
    storage_key = _seed_storage_key(tmp_path)

    result = extractor(storage_key=storage_key, storage_root=tmp_path)
    transaction_table = _table_by_name(result, "compra_venta_activos")

    header_markers = {"fecha", "nombre_activo", "simbolo_activo", "categoria_activo"}
    footer_markers = {"certificado", "fintual", "exchange traded funds"}

    for row in transaction_table.rows:
        normalized_values = {
            value.strip().lower()
            for value in row.raw_cells.values()
            if isinstance(value, str) and value.strip()
        }
        joined_values = " ".join(sorted(normalized_values))
        assert not normalized_values.intersection(header_markers)
        for marker in footer_markers:
            assert marker not in joined_values


def test_extract_dataset1_preserves_row_id_and_source_page_provenance(
    tmp_path: Path,
) -> None:
    """Extraction should preserve deterministic row order and source-page provenance."""

    extractor = _load_extractor()
    storage_key = _seed_storage_key(tmp_path)
    expected_contract = _load_golden_json()

    result = extractor(storage_key=storage_key, storage_root=tmp_path)
    transaction_table = _table_by_name(result, "compra_venta_activos")

    observed_row_ids = [row.row_id for row in transaction_table.rows]
    assert observed_row_ids == list(range(1, len(transaction_table.rows) + 1))

    observed_pages = [row.source_page for row in transaction_table.rows]
    assert min(observed_pages) == 1
    assert max(observed_pages) <= 9
    assert max(observed_pages) > 1

    summary = expected_contract["summary"]
    assert isinstance(summary, dict)
    assert len(transaction_table.rows) == summary["transaction_rows"]
