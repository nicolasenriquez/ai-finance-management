"""Service layer for PDF normalization."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import NoReturn

from app.core.logging import get_logger
from app.pdf_extraction.schemas import PdfExtractedRow
from app.pdf_extraction.service import (
    PdfExtractionClientError,
    extract_pdf_from_storage,
)
from app.pdf_normalization.schemas import (
    CanonicalDividendRecord,
    CanonicalRecord,
    CanonicalSplitRecord,
    CanonicalTradeRecord,
    NormalizationErrorCode,
    NormalizationValidationError,
    PdfNormalizationResult,
    PdfNormalizationSummary,
    RowProvenance,
    TradeSide,
)

logger = get_logger(__name__)


class PdfNormalizationClientError(ValueError):
    """Raised when normalization input cannot be processed deterministically."""

    status_code: int
    validation_errors: tuple[NormalizationValidationError, ...]

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        validation_errors: tuple[NormalizationValidationError, ...] | None = None,
    ) -> None:
        """Initialize client-facing normalization error."""

        super().__init__(message)
        self.status_code = status_code
        self.validation_errors = validation_errors or ()


def normalize_blank_cell(value: str | None) -> str | None:
    """Normalize whitespace and convert empty source cells to `None`."""

    if value is None:
        return None

    cleaned_value = " ".join(value.split())
    return cleaned_value or None


def parse_date_value(
    raw_value: str,
    *,
    field: str | None = None,
    provenance: RowProvenance | None = None,
) -> date:
    """Parse deterministic ISO-like date values."""

    normalized_value = normalize_blank_cell(raw_value)
    if normalized_value is None:
        _raise_validation_error(
            code=NormalizationErrorCode.MISSING_REQUIRED_FIELD,
            message="Date value is required.",
            field=field or "date",
            raw_value=raw_value,
            provenance=provenance,
        )

    sanitized_value = normalized_value.replace(" ", "")

    try:
        return date.fromisoformat(sanitized_value)
    except ValueError as exc:
        _raise_validation_error(
            code=NormalizationErrorCode.INVALID_DATE,
            message="Date must use YYYY-MM-DD format.",
            field=field or "date",
            raw_value=normalized_value,
            provenance=provenance,
        )
        raise AssertionError from exc


def parse_decimal_comma_value(
    raw_value: str,
    *,
    field: str | None = None,
    provenance: RowProvenance | None = None,
) -> Decimal:
    """Parse locale-specific decimal-comma values into `Decimal`."""

    normalized_value = normalize_blank_cell(raw_value)
    if normalized_value is None:
        _raise_validation_error(
            code=NormalizationErrorCode.MISSING_REQUIRED_FIELD,
            message="Numeric value is required.",
            field=field or "value",
            raw_value=raw_value,
            provenance=provenance,
        )

    ascii_value = (
        normalized_value.replace("US $", "")
        .replace("US$", "")
        .replace("$", "")
        .replace(" ", "")
    )
    integer_part, comma, decimal_part = ascii_value.partition(",")
    normalized_numeric = integer_part.replace(".", "")
    if comma:
        normalized_numeric = f"{normalized_numeric}.{decimal_part}"

    if not normalized_numeric or normalized_numeric in {"+", "-", "."}:
        _raise_validation_error(
            code=NormalizationErrorCode.INVALID_NUMBER,
            message="Numeric value is invalid.",
            field=field or "value",
            raw_value=normalized_value,
            provenance=provenance,
        )

    try:
        return Decimal(normalized_numeric)
    except (InvalidOperation, ValueError) as exc:
        _raise_validation_error(
            code=NormalizationErrorCode.INVALID_NUMBER,
            message="Numeric value is invalid.",
            field=field or "value",
            raw_value=normalized_value,
            provenance=provenance,
        )
        raise AssertionError from exc


def derive_trade_side(
    *,
    aporte_usd: Decimal | None,
    acciones_compradas_qty: Decimal | None,
    rescate_usd: Decimal | None,
    acciones_vendidas_qty: Decimal | None,
) -> TradeSide:
    """Derive deterministic trade direction from mutually exclusive value pairs."""

    is_buy = (
        aporte_usd is not None
        and acciones_compradas_qty is not None
        and rescate_usd is None
        and acciones_vendidas_qty is None
    )
    is_sell = (
        aporte_usd is None
        and acciones_compradas_qty is None
        and rescate_usd is not None
        and acciones_vendidas_qty is not None
    )

    if is_buy:
        return TradeSide.BUY
    if is_sell:
        return TradeSide.SELL

    _raise_validation_error(
        code=NormalizationErrorCode.AMBIGUOUS_TRADE_SIDE,
        message="Trade side cannot be derived deterministically from provided values.",
    )


def normalize_trade_row(
    *,
    raw_cells: dict[str, str | None],
    row_id: int | None,
    row_index: int,
    source_page: int,
    table_name: str,
) -> CanonicalTradeRecord:
    """Normalize one extracted trade row into a canonical trade event."""

    provenance = _build_provenance(
        table_name=table_name,
        row_id=row_id,
        row_index=row_index,
        source_page=source_page,
    )
    canonical_raw_values = _canonicalize_raw_cells(raw_cells)

    trade_date = parse_date_value(
        _require_text_field(canonical_raw_values, "fecha", provenance=provenance),
        field="fecha",
        provenance=provenance,
    )
    aporte_usd = _parse_optional_decimal_field(
        canonical_raw_values,
        "aporte_dolares",
        provenance=provenance,
    )
    acciones_compradas_qty = _parse_optional_decimal_field(
        canonical_raw_values,
        "acciones_compradas",
        provenance=provenance,
    )
    rescate_usd = _parse_optional_decimal_field(
        canonical_raw_values,
        "rescate_dolares",
        provenance=provenance,
    )
    acciones_vendidas_qty = _parse_optional_decimal_field(
        canonical_raw_values,
        "acciones_vendidas",
        provenance=provenance,
    )
    trade_side = derive_trade_side(
        aporte_usd=aporte_usd,
        acciones_compradas_qty=acciones_compradas_qty,
        rescate_usd=rescate_usd,
        acciones_vendidas_qty=acciones_vendidas_qty,
    )

    return CanonicalTradeRecord(
        trade_side=trade_side,
        trade_date=trade_date,
        instrument_name=_require_text_field(
            canonical_raw_values, "nombre_activo", provenance=provenance
        ),
        instrument_symbol=_require_text_field(
            canonical_raw_values, "simbolo_activo", provenance=provenance
        ),
        instrument_category=_require_text_field(
            canonical_raw_values, "categoria_activo", provenance=provenance
        ),
        aporte_usd=aporte_usd,
        acciones_compradas_qty=acciones_compradas_qty,
        rescate_usd=rescate_usd,
        acciones_vendidas_qty=acciones_vendidas_qty,
        raw_values=canonical_raw_values,
        provenance=provenance,
    )


def normalize_dividend_row(
    *,
    raw_cells: dict[str, str | None],
    row_id: int | None,
    row_index: int,
    source_page: int,
    table_name: str,
) -> CanonicalDividendRecord:
    """Normalize one extracted dividend row into a canonical dividend event."""

    provenance = _build_provenance(
        table_name=table_name,
        row_id=row_id,
        row_index=row_index,
        source_page=source_page,
    )
    canonical_raw_values = _canonicalize_raw_cells(raw_cells)

    return CanonicalDividendRecord(
        dividend_date=parse_date_value(
            _require_text_field(canonical_raw_values, "fecha", provenance=provenance),
            field="fecha",
            provenance=provenance,
        ),
        instrument_name=_require_text_field(
            canonical_raw_values, "nombre_activo", provenance=provenance
        ),
        instrument_symbol=_require_text_field(
            canonical_raw_values, "simbolo_activo", provenance=provenance
        ),
        instrument_category=_require_text_field(
            canonical_raw_values, "categoria_activo", provenance=provenance
        ),
        gross_usd=_parse_required_decimal_field(
            canonical_raw_values,
            "monto_bruto",
            provenance=provenance,
        ),
        taxes_usd=_parse_required_decimal_field(
            canonical_raw_values,
            "monto_impuestos",
            provenance=provenance,
        ),
        net_usd=_parse_required_decimal_field(
            canonical_raw_values,
            "monto_neto",
            provenance=provenance,
        ),
        raw_values=canonical_raw_values,
        provenance=provenance,
    )


def normalize_split_row(
    *,
    raw_cells: dict[str, str | None],
    row_id: int | None,
    row_index: int,
    source_page: int,
    table_name: str,
) -> CanonicalSplitRecord:
    """Normalize one extracted split row into a canonical split event."""

    provenance = _build_provenance(
        table_name=table_name,
        row_id=row_id,
        row_index=row_index,
        source_page=source_page,
    )
    canonical_raw_values = _canonicalize_raw_cells(raw_cells)

    return CanonicalSplitRecord(
        split_date=parse_date_value(
            _require_text_field(canonical_raw_values, "fecha", provenance=provenance),
            field="fecha",
            provenance=provenance,
        ),
        instrument_name=_require_text_field(
            canonical_raw_values, "nombre_activo", provenance=provenance
        ),
        instrument_symbol=_require_text_field(
            canonical_raw_values, "simbolo_activo", provenance=provenance
        ),
        instrument_category=_require_text_field(
            canonical_raw_values, "categoria_activo", provenance=provenance
        ),
        shares_before_qty=_parse_required_decimal_field(
            canonical_raw_values,
            "acciones_iniciales",
            provenance=provenance,
        ),
        shares_after_qty=_parse_required_decimal_field(
            canonical_raw_values,
            "acciones_finales",
            provenance=provenance,
        ),
        split_ratio_value=_parse_required_decimal_field(
            canonical_raw_values,
            "ratio",
            provenance=provenance,
        ),
        raw_values=canonical_raw_values,
        provenance=provenance,
    )


def normalize_pdf_from_storage(
    *, storage_key: str, storage_root: Path
) -> PdfNormalizationResult:
    """Normalize extracted dataset 1 rows into canonical records."""

    logger.info("pdf_normalization.execution_started", storage_key=storage_key)
    try:
        extraction_result = extract_pdf_from_storage(
            storage_key=storage_key, storage_root=storage_root
        )
    except PdfExtractionClientError as exc:
        logger.info(
            "pdf_normalization.execution_rejected",
            storage_key=storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise PdfNormalizationClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc

    records: list[CanonicalRecord] = []
    trade_count = 0
    dividend_count = 0
    split_count = 0

    for table in extraction_result.tables:
        for row_index, row in enumerate(table.rows, start=1):
            record = _normalize_row_for_table(
                table_name=table.table_name,
                row=row,
                row_index=row_index,
            )
            records.append(record)
            if isinstance(record, CanonicalTradeRecord):
                trade_count += 1
            elif isinstance(record, CanonicalDividendRecord):
                dividend_count += 1
            else:
                split_count += 1

    result = PdfNormalizationResult(
        storage_key=storage_key,
        source_pdf_pages=extraction_result.source_pdf_pages,
        records=records,
        summary=PdfNormalizationSummary(
            trade_records=trade_count,
            dividend_records=dividend_count,
            split_records=split_count,
        ),
    )
    logger.info(
        "pdf_normalization.execution_completed",
        storage_key=storage_key,
        source_pdf_pages=result.source_pdf_pages,
        trade_records=trade_count,
        dividend_records=dividend_count,
        split_records=split_count,
    )
    return result


def _normalize_row_for_table(
    *,
    table_name: str,
    row: PdfExtractedRow,
    row_index: int,
) -> CanonicalRecord:
    """Dispatch one extracted row to its table-specific normalizer."""

    if table_name == "compra_venta_activos":
        return normalize_trade_row(
            raw_cells=row.raw_cells,
            row_id=row.row_id,
            row_index=row_index,
            source_page=row.source_page,
            table_name=table_name,
        )
    if table_name == "dividendos_recibidos":
        return normalize_dividend_row(
            raw_cells=row.raw_cells,
            row_id=row.row_id,
            row_index=row_index,
            source_page=row.source_page,
            table_name=table_name,
        )
    if table_name == "splits":
        return normalize_split_row(
            raw_cells=row.raw_cells,
            row_id=row.row_id,
            row_index=row_index,
            source_page=row.source_page,
            table_name=table_name,
        )

    _raise_validation_error(
        code=NormalizationErrorCode.UNSUPPORTED_TABLE_ROW,
        message=f"Unsupported extracted table for normalization: {table_name}.",
        field="table_name",
        raw_value=table_name,
    )


def _build_provenance(
    *,
    table_name: str,
    row_id: int | None,
    row_index: int,
    source_page: int,
) -> RowProvenance:
    """Create deterministic provenance for normalized records."""

    return RowProvenance(
        table_name=table_name,
        row_id=row_id,
        row_index=row_index,
        source_page=source_page,
    )


def _canonicalize_raw_cells(raw_cells: dict[str, str | None]) -> dict[str, str | None]:
    """Normalize raw cell values while preserving source keys."""

    return {field: normalize_blank_cell(value) for field, value in raw_cells.items()}


def _require_text_field(
    raw_cells: dict[str, str | None],
    field: str,
    *,
    provenance: RowProvenance,
) -> str:
    """Read a required non-empty text field from normalized raw values."""

    value = normalize_blank_cell(raw_cells.get(field))
    if value is None:
        _raise_validation_error(
            code=NormalizationErrorCode.MISSING_REQUIRED_FIELD,
            message=f"Field '{field}' is required.",
            field=field,
            raw_value=raw_cells.get(field),
            provenance=provenance,
        )
    return value


def _parse_optional_decimal_field(
    raw_cells: dict[str, str | None],
    field: str,
    *,
    provenance: RowProvenance,
) -> Decimal | None:
    """Parse optional decimal-comma field from normalized raw values."""

    raw_value = normalize_blank_cell(raw_cells.get(field))
    if raw_value is None:
        return None
    return parse_decimal_comma_value(
        raw_value,
        field=field,
        provenance=provenance,
    )


def _parse_required_decimal_field(
    raw_cells: dict[str, str | None],
    field: str,
    *,
    provenance: RowProvenance,
) -> Decimal:
    """Parse required decimal-comma field from normalized raw values."""

    raw_value = normalize_blank_cell(raw_cells.get(field))
    if raw_value is None:
        _raise_validation_error(
            code=NormalizationErrorCode.MISSING_REQUIRED_FIELD,
            message=f"Field '{field}' is required.",
            field=field,
            raw_value=raw_cells.get(field),
            provenance=provenance,
        )

    return parse_decimal_comma_value(
        raw_value,
        field=field,
        provenance=provenance,
    )


def _raise_validation_error(
    *,
    code: NormalizationErrorCode,
    message: str,
    field: str | None = None,
    raw_value: str | None = None,
    provenance: RowProvenance | None = None,
) -> NoReturn:
    """Raise a normalized validation failure with structured context."""

    validation_error = NormalizationValidationError(
        code=code,
        message=message,
        field=field,
        raw_value=raw_value,
        provenance=provenance,
    )
    raise PdfNormalizationClientError(
        message,
        status_code=422,
        validation_errors=(validation_error,),
    )
