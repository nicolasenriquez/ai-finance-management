"""Service layer for PDF verification."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from app.core.logging import get_logger
from app.pdf_normalization.service import (
    PdfNormalizationClientError,
    normalize_blank_cell,
    normalize_pdf_from_storage,
)
from app.pdf_verification.schemas import (
    PdfVerificationResult,
    VerificationMismatch,
    VerificationStatus,
    VerificationSummary,
)

logger = get_logger(__name__)

_DATASET_1_GOLDEN_JSON_PATH = (
    Path(__file__).resolve().parent.parent / "golden_sets" / "dataset_1" / "202602_stocks.json"
)
_DATASET_1_TABLE_ORDER: tuple[str, ...] = (
    "compra_venta_activos",
    "dividendos_recibidos",
    "splits",
)
_RECORD_PRESENCE_FIELD = "__record_presence__"
_RECORD_PRESENT_VALUE = "present"


@dataclass(frozen=True)
class VerifiableRecord:
    """Comparable verification record preserving row identity and raw values."""

    table_name: str
    row_id: int | None
    row_index: int
    source_page: int | None
    raw_values: dict[str, str | None]


class PdfVerificationClientError(ValueError):
    """Raised when verification input cannot be processed deterministically."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize client-facing verification error."""

        super().__init__(message)
        self.status_code = status_code


def verify_pdf_from_storage(*, storage_key: str, storage_root: Path) -> PdfVerificationResult:
    """Verify normalized dataset 1 records against the checked-in golden set."""

    logger.info("pdf_verification.execution_started", storage_key=storage_key)
    try:
        normalization_result = normalize_pdf_from_storage(
            storage_key=storage_key,
            storage_root=storage_root,
        )
    except PdfNormalizationClientError as exc:
        logger.info(
            "pdf_verification.execution_rejected",
            storage_key=storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise PdfVerificationClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc

    expected_records = _load_expected_records_from_golden_set()
    actual_records = _build_actual_records(normalization_result.records)
    report = build_verification_report(
        storage_key=storage_key,
        expected_records=expected_records,
        actual_records=actual_records,
        source_pdf_pages=normalization_result.source_pdf_pages,
    )

    logger.info(
        "pdf_verification.execution_completed",
        storage_key=storage_key,
        status=report.status,
        expected_records=report.summary.expected_records,
        actual_records=report.summary.actual_records,
        mismatch_count=report.summary.mismatch_count,
    )
    return report


def build_verification_report(
    *,
    storage_key: str,
    expected_records: Sequence[object],
    actual_records: Sequence[object],
    source_pdf_pages: int | None = None,
) -> PdfVerificationResult:
    """Build deterministic verification report with field-level mismatch evidence."""

    expected = _coerce_records(expected_records, context="expected_records")
    actual = _coerce_records(actual_records, context="actual_records")

    _build_identity_index(expected, context="expected_records")
    actual_index = _build_identity_index(actual, context="actual_records")

    mismatches: list[VerificationMismatch] = []
    matched_keys: set[tuple[str, int, int | None]] = set()

    for expected_record in expected:
        identity_key = _record_identity_key(expected_record)
        actual_record = actual_index.get(identity_key)
        if actual_record is None:
            mismatches.append(
                VerificationMismatch(
                    table_name=expected_record.table_name,
                    row_id=expected_record.row_id,
                    row_index=expected_record.row_index,
                    source_page=expected_record.source_page,
                    field=_RECORD_PRESENCE_FIELD,
                    expected_raw=_RECORD_PRESENT_VALUE,
                    actual_raw=None,
                )
            )
            continue

        matched_keys.add(identity_key)
        mismatches.extend(_compare_record_fields(expected_record, actual_record))

    for actual_record in actual:
        identity_key = _record_identity_key(actual_record)
        if identity_key in matched_keys:
            continue

        mismatches.append(
            VerificationMismatch(
                table_name=actual_record.table_name,
                row_id=actual_record.row_id,
                row_index=actual_record.row_index,
                source_page=actual_record.source_page,
                field=_RECORD_PRESENCE_FIELD,
                expected_raw=None,
                actual_raw=_RECORD_PRESENT_VALUE,
            )
        )

    status = VerificationStatus.PASSED if not mismatches else VerificationStatus.FAILED
    return PdfVerificationResult(
        storage_key=storage_key,
        status=status,
        source_pdf_pages=source_pdf_pages,
        summary=VerificationSummary(
            expected_records=len(expected),
            actual_records=len(actual),
            mismatch_count=len(mismatches),
        ),
        mismatches=mismatches,
        verified_at_utc=datetime.now(UTC),
    )


def _load_expected_records_from_golden_set() -> list[VerifiableRecord]:
    """Load dataset 1 expected records from checked-in golden JSON contract."""

    contract = _load_dataset_1_contract()
    tables = _expect_mapping(contract.get("tables"), context="tables")
    records: list[VerifiableRecord] = []

    for table_name in _DATASET_1_TABLE_ORDER:
        table_payload = _expect_mapping(
            tables.get(table_name),
            context=f"tables.{table_name}",
        )
        columns = _expect_string_list(
            table_payload.get("columns"),
            context=f"tables.{table_name}.columns",
        )
        rows = _expect_list(
            table_payload.get("rows"),
            context=f"tables.{table_name}.rows",
        )

        for row_index, row_value in enumerate(rows, start=1):
            row_payload = _expect_mapping(
                row_value,
                context=f"tables.{table_name}.rows[{row_index}]",
            )
            raw_values: dict[str, str | None] = {}
            for column_name in columns:
                raw_values[column_name] = _extract_expected_raw_value(
                    row_payload.get(column_name),
                    context=f"tables.{table_name}.rows[{row_index}].{column_name}",
                )

            records.append(
                VerifiableRecord(
                    table_name=table_name,
                    row_id=_optional_positive_int(
                        row_payload.get("row_id"),
                        context=f"tables.{table_name}.rows[{row_index}].row_id",
                    ),
                    row_index=row_index,
                    source_page=_optional_positive_int(
                        row_payload.get("source_page"),
                        context=f"tables.{table_name}.rows[{row_index}].source_page",
                    ),
                    raw_values=raw_values,
                )
            )

    return records


def _build_actual_records(normalized_records: Sequence[object]) -> list[VerifiableRecord]:
    """Build verifiable records from canonical normalization output."""

    records: list[VerifiableRecord] = []
    for index, normalized_record in enumerate(normalized_records, start=1):
        provenance = getattr(normalized_record, "provenance", None)
        raw_values = getattr(normalized_record, "raw_values", None)
        if provenance is None or raw_values is None:
            raise PdfVerificationClientError(
                f"Normalization output record at index {index} is missing provenance/raw values.",
                status_code=422,
            )

        table_name = getattr(provenance, "table_name", None)
        row_id = getattr(provenance, "row_id", None)
        row_index = getattr(provenance, "row_index", None)
        source_page = getattr(provenance, "source_page", None)
        if not isinstance(table_name, str) or not table_name:
            raise PdfVerificationClientError(
                f"Normalization output record at index {index} has invalid table_name provenance.",
                status_code=422,
            )
        if isinstance(row_id, bool) or (row_id is not None and not isinstance(row_id, int)):
            raise PdfVerificationClientError(
                f"Normalization output record at index {index} has invalid row_id provenance.",
                status_code=422,
            )
        if isinstance(row_index, bool) or not isinstance(row_index, int) or row_index < 1:
            raise PdfVerificationClientError(
                f"Normalization output record at index {index} has invalid row_index provenance.",
                status_code=422,
            )
        if isinstance(source_page, bool) or not isinstance(source_page, int) or source_page < 1:
            raise PdfVerificationClientError(
                f"Normalization output record at index {index} has invalid source_page provenance.",
                status_code=422,
            )

        records.append(
            VerifiableRecord(
                table_name=table_name,
                row_id=row_id,
                row_index=row_index,
                source_page=source_page,
                raw_values=_coerce_raw_values(
                    raw_values,
                    context=f"normalized_records[{index}].raw_values",
                ),
            )
        )

    return records


def _coerce_records(records: Sequence[object], *, context: str) -> list[VerifiableRecord]:
    """Coerce arbitrary record-like inputs into verifiable records."""

    coerced: list[VerifiableRecord] = []
    for index, record in enumerate(records, start=1):
        if isinstance(record, VerifiableRecord):
            coerced.append(record)
            continue

        payload = _expect_mapping(record, context=f"{context}[{index}]")
        table_name = _required_non_empty_string(
            payload.get("table_name"),
            context=f"{context}[{index}].table_name",
        )
        row_index = _required_positive_int(
            payload.get("row_index"),
            context=f"{context}[{index}].row_index",
        )
        row_id = _optional_positive_int(
            payload.get("row_id"),
            context=f"{context}[{index}].row_id",
        )
        source_page = _optional_positive_int(
            payload.get("source_page"),
            context=f"{context}[{index}].source_page",
        )
        raw_values = _coerce_raw_values(
            payload.get("raw_values"),
            context=f"{context}[{index}].raw_values",
        )
        coerced.append(
            VerifiableRecord(
                table_name=table_name,
                row_id=row_id,
                row_index=row_index,
                source_page=source_page,
                raw_values=raw_values,
            )
        )
    return coerced


def _compare_record_fields(
    expected_record: VerifiableRecord,
    actual_record: VerifiableRecord,
) -> list[VerificationMismatch]:
    """Compare raw values for two matched records and emit field-level mismatches."""

    expected_fields = list(expected_record.raw_values.keys())
    actual_extra_fields = [
        field_name
        for field_name in actual_record.raw_values
        if field_name not in expected_record.raw_values
    ]
    field_names = [*expected_fields, *sorted(actual_extra_fields)]

    mismatches: list[VerificationMismatch] = []
    for field_name in field_names:
        expected_raw = expected_record.raw_values.get(field_name)
        actual_raw = actual_record.raw_values.get(field_name)
        if _normalize_for_comparison(field_name, expected_raw) == _normalize_for_comparison(
            field_name,
            actual_raw,
        ):
            continue

        mismatches.append(
            VerificationMismatch(
                table_name=expected_record.table_name,
                row_id=(
                    expected_record.row_id
                    if expected_record.row_id is not None
                    else actual_record.row_id
                ),
                row_index=expected_record.row_index,
                source_page=(
                    expected_record.source_page
                    if expected_record.source_page is not None
                    else actual_record.source_page
                ),
                field=field_name,
                expected_raw=expected_raw,
                actual_raw=actual_raw,
            )
        )

    return mismatches


def _build_identity_index(
    records: Sequence[VerifiableRecord],
    *,
    context: str,
) -> dict[tuple[str, int, int | None], VerifiableRecord]:
    """Build deterministic identity index and reject duplicate record identities."""

    index: dict[tuple[str, int, int | None], VerifiableRecord] = {}
    for record in records:
        identity_key = _record_identity_key(record)
        if identity_key in index:
            table_name, row_index, source_page = identity_key
            raise PdfVerificationClientError(
                "Verification cannot continue with duplicated record identity "
                f"in {context}: table={table_name}, row_index={row_index}, "
                f"source_page={source_page}.",
                status_code=422,
            )
        index[identity_key] = record
    return index


def _record_identity_key(record: VerifiableRecord) -> tuple[str, int, int | None]:
    """Return deterministic row identity used for expected/actual pairing."""

    return (record.table_name, record.row_index, record.source_page)


def _normalize_for_comparison(field_name: str, value: str | None) -> str | None:
    """Normalize comparison values while preserving raw mismatch evidence."""

    normalized = normalize_blank_cell(value)
    if normalized is None:
        return None
    if field_name == "fecha":
        return normalized.replace(" ", "")
    return normalized


def _coerce_raw_values(value: object, *, context: str) -> dict[str, str | None]:
    """Validate and normalize record raw-value mapping."""

    payload = _expect_mapping(value, context=context)
    raw_values: dict[str, str | None] = {}
    for field_name, field_value in payload.items():
        if not field_name:
            raise PdfVerificationClientError(
                f"{context} contains an empty field name.",
                status_code=422,
            )
        raw_values[field_name] = _optional_string(
            field_value,
            context=f"{context}.{field_name}",
        )
    return raw_values


def _extract_expected_raw_value(value: object, *, context: str) -> str | None:
    """Extract raw source value from dataset 1 golden row field."""

    if value is None:
        return None
    if isinstance(value, str):
        return normalize_blank_cell(value)
    if isinstance(value, dict):
        typed_value = _expect_mapping(cast(object, value), context=context)
        raw_candidate = typed_value.get("raw")
        return _optional_string(raw_candidate, context=f"{context}.raw")
    raise PdfVerificationClientError(
        f"{context} must be either string, null, or object with raw field.",
        status_code=422,
    )


def _load_dataset_1_contract() -> dict[str, object]:
    """Read and parse the dataset 1 golden JSON contract from disk."""

    try:
        raw_text = _DATASET_1_GOLDEN_JSON_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Unable to read golden dataset contract at {_DATASET_1_GOLDEN_JSON_PATH}.",
        ) from exc

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Golden dataset contract is not valid JSON.",
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("Golden dataset contract must be a top-level object.")

    return cast(dict[str, object], parsed)


def _expect_mapping(value: object, *, context: str) -> dict[str, object]:
    """Assert value is a string-keyed object mapping."""

    if isinstance(value, dict):
        return cast(dict[str, object], value)
    raise PdfVerificationClientError(f"{context} must be an object.", status_code=422)


def _expect_list(value: object, *, context: str) -> list[object]:
    """Assert value is a list."""

    if isinstance(value, list):
        return cast(list[object], value)
    raise PdfVerificationClientError(f"{context} must be a list.", status_code=422)


def _expect_string_list(value: object, *, context: str) -> list[str]:
    """Assert value is a non-empty list of non-empty strings."""

    values = _expect_list(value, context=context)
    strings: list[str] = []
    for index, item in enumerate(values, start=1):
        if not isinstance(item, str) or not item:
            raise PdfVerificationClientError(
                f"{context}[{index}] must be a non-empty string.",
                status_code=422,
            )
        strings.append(item)
    return strings


def _required_non_empty_string(value: object, *, context: str) -> str:
    """Assert value is a required non-empty string."""

    if not isinstance(value, str):
        raise PdfVerificationClientError(f"{context} must be a string.", status_code=422)
    normalized = normalize_blank_cell(value)
    if normalized is None:
        raise PdfVerificationClientError(
            f"{context} cannot be blank.",
            status_code=422,
        )
    return normalized


def _optional_string(value: object, *, context: str) -> str | None:
    """Assert value is either null or string and normalize whitespace."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise PdfVerificationClientError(f"{context} must be a string or null.", status_code=422)
    return normalize_blank_cell(value)


def _required_positive_int(value: object, *, context: str) -> int:
    """Assert value is a required positive integer."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise PdfVerificationClientError(
            f"{context} must be a positive integer.",
            status_code=422,
        )
    return value


def _optional_positive_int(value: object, *, context: str) -> int | None:
    """Assert value is optional positive integer."""

    if value is None:
        return None
    return _required_positive_int(value, context=context)
