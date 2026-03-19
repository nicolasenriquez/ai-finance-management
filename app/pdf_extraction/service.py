"""Service layer for PDF extraction from stored uploads."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pdfplumber

from app.core.logging import get_logger
from app.pdf_extraction.schemas import (
    PdfExtractedRow,
    PdfExtractedTable,
    PdfExtractionResult,
)

logger = get_logger(__name__)

_TABLE_ORDER: tuple[str, ...] = (
    "compra_venta_activos",
    "dividendos_recibidos",
    "splits",
)

_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "compra_venta_activos": (
        "fecha",
        "nombre_activo",
        "simbolo_activo",
        "categoria_activo",
        "aporte_dolares",
        "acciones_compradas",
        "rescate_dolares",
        "acciones_vendidas",
    ),
    "dividendos_recibidos": (
        "fecha",
        "nombre_activo",
        "simbolo_activo",
        "categoria_activo",
        "monto_bruto",
        "monto_impuestos",
        "monto_neto",
    ),
    "splits": (
        "fecha",
        "nombre_activo",
        "simbolo_activo",
        "categoria_activo",
        "acciones_iniciales",
        "acciones_finales",
        "ratio",
    ),
}

_HEADER_TO_TABLE: dict[tuple[str, ...], str] = {
    (
        "fecha",
        "nombre activo",
        "simbolo activo",
        "categoria activo",
        "aporte de dolares",
        "acciones compradas",
        "rescate de dolares",
        "acciones vendidas",
    ): "compra_venta_activos",
    (
        "fecha",
        "nombre activo",
        "simbolo activo",
        "categoria activo",
        "monto bruto",
        "monto impuestos",
        "monto neto",
    ): "dividendos_recibidos",
    (
        "fecha",
        "nombre activo",
        "simbolo activo",
        "categoria activo",
        "acciones iniciales",
        "acciones finales",
        "ratio",
    ): "splits",
}

_HEADER_MARKERS: frozenset[str] = frozenset(
    {"fecha", "nombre activo", "simbolo activo", "categoria activo"}
)

_FOOTER_MARKERS: tuple[str, ...] = (
    "certificado",
    "fintual administradora",
    "exchange traded funds",
    "www.fintual.cl",
    "rut",
)


class PdfExtractionClientError(ValueError):
    """Raised when client-provided extraction input is invalid."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize client-facing extraction error."""

        super().__init__(message)
        self.status_code = status_code


def _normalize_for_match(value: str) -> str:
    """Normalize text for deterministic header/footer matching."""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_only.lower().split())


def _clean_cell(value: object | None) -> str | None:
    """Normalize cell whitespace and convert empty values to None."""

    if value is None:
        return None

    cleaned = " ".join(str(value).replace("\n", " ").split())
    return cleaned or None


def _normalize_row_for_header(cells: list[str | None]) -> tuple[str, ...]:
    """Build normalized row tuple used for header detection."""

    normalized: list[str] = []
    for cell in cells:
        normalized.append("" if cell is None else _normalize_for_match(cell))
    return tuple(normalized)


def _is_repeated_header(raw_cells: dict[str, str | None]) -> bool:
    """Detect repeated header rows accidentally parsed as data rows."""

    normalized_values = {
        _normalize_for_match(value)
        for value in raw_cells.values()
        if isinstance(value, str) and value.strip()
    }
    return _HEADER_MARKERS.issubset(normalized_values)


def _is_footer_artifact(raw_cells: dict[str, str | None]) -> bool:
    """Detect known footer/non-data artifact rows."""

    normalized_joined = " ".join(
        _normalize_for_match(value)
        for value in raw_cells.values()
        if isinstance(value, str) and value.strip()
    )
    return any(marker in normalized_joined for marker in _FOOTER_MARKERS)


def _resolve_storage_path(*, storage_key: str, storage_root: Path) -> Path:
    """Resolve and validate a storage key inside the configured storage root."""

    normalized_key = storage_key.strip()
    if not normalized_key:
        raise PdfExtractionClientError(
            "Storage key is required for extraction.",
            status_code=400,
        )

    key_path = Path(normalized_key)
    if key_path.is_absolute():
        raise PdfExtractionClientError(
            "Storage key must be a relative path.",
            status_code=400,
        )

    root_resolved = storage_root.resolve()
    candidate = (root_resolved / key_path).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise PdfExtractionClientError(
            "Storage key must remain inside the configured upload root.",
            status_code=400,
        )

    if candidate.suffix.lower() != ".pdf":
        raise PdfExtractionClientError(
            "Storage key must point to a PDF file.",
            status_code=400,
        )

    if not candidate.is_file():
        raise PdfExtractionClientError(
            "Stored PDF was not found for the provided storage key.",
            status_code=404,
        )

    return candidate


def extract_pdf_from_storage(*, storage_key: str, storage_root: Path) -> PdfExtractionResult:
    """Extract deterministic raw rows from a stored PDF using pdfplumber."""

    storage_path = _resolve_storage_path(storage_key=storage_key, storage_root=storage_root)
    logger.info(
        "pdf_extraction.execution_started",
        storage_key=storage_key,
        storage_path=str(storage_path),
    )

    table_rows: dict[str, list[PdfExtractedRow]] = {name: [] for name in _TABLE_ORDER}

    try:
        with pdfplumber.open(storage_path) as pdf:
            source_pdf_pages = len(pdf.pages)
            current_table_name: str | None = None

            for page_number, page in enumerate(pdf.pages, start=1):
                for extracted_table in page.extract_tables() or []:
                    for raw_row in extracted_table:
                        cells = [_clean_cell(value) for value in raw_row]
                        if not any(cells):
                            continue

                        header_key = _normalize_row_for_header(cells)
                        matched_table = _HEADER_TO_TABLE.get(header_key)
                        if matched_table is not None:
                            current_table_name = matched_table
                            continue

                        if current_table_name is None:
                            continue

                        columns = _TABLE_COLUMNS[current_table_name]
                        padded_cells = (cells + [None] * len(columns))[: len(columns)]
                        raw_cells = dict(zip(columns, padded_cells, strict=True))

                        if _is_repeated_header(raw_cells):
                            continue
                        if _is_footer_artifact(raw_cells):
                            continue

                        next_row_id = len(table_rows[current_table_name]) + 1
                        table_rows[current_table_name].append(
                            PdfExtractedRow(
                                row_id=next_row_id,
                                source_page=page_number,
                                raw_cells=raw_cells,
                            )
                        )
    except PdfExtractionClientError:
        raise
    except Exception as exc:  # pragma: no cover - defensive fail-fast guard
        logger.error(
            "pdf_extraction.execution_failed",
            storage_key=storage_key,
            error=str(exc),
            exc_info=True,
        )
        raise PdfExtractionClientError(
            "Extraction failed for the provided PDF.",
            status_code=422,
        ) from exc

    if not any(table_rows.values()):
        raise PdfExtractionClientError(
            "No supported table data found in the provided PDF.",
            status_code=422,
        )

    missing_tables = [name for name in _TABLE_ORDER if not table_rows[name]]
    if missing_tables:
        raise PdfExtractionClientError(
            f"No supported table data found for: {', '.join(missing_tables)}.",
            status_code=422,
        )

    tables = [
        PdfExtractedTable(
            table_name=table_name,
            columns=list(_TABLE_COLUMNS[table_name]),
            rows=table_rows[table_name],
        )
        for table_name in _TABLE_ORDER
    ]

    result = PdfExtractionResult(
        engine="pdfplumber",
        storage_key=storage_key,
        source_pdf_pages=source_pdf_pages,
        tables=tables,
    )

    logger.info(
        "pdf_extraction.execution_completed",
        storage_key=storage_key,
        source_pdf_pages=source_pdf_pages,
        table_counts={name: len(rows) for name, rows in table_rows.items()},
    )
    return result
