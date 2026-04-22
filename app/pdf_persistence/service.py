"""Service helpers for PDF persistence."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence, Set
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import cast

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.pdf_ingestion.schemas import PdfIngestionResult
from app.pdf_ingestion.service import (
    PdfIngestionClientError,
    load_ingestion_result_from_storage,
)
from app.pdf_normalization.schemas import (
    CanonicalDividendRecord,
    CanonicalRecord,
    CanonicalTradeRecord,
    PdfNormalizationResult,
)
from app.pdf_normalization.service import (
    PdfNormalizationClientError,
    normalize_pdf_from_storage,
)
from app.pdf_persistence.models import CanonicalPdfRecord, ImportJob, SourceDocument
from app.pdf_persistence.schemas import (
    PdfPersistenceResult,
    PdfPersistenceSummary,
    SourceDocumentPersistenceStatus,
)

logger = get_logger(__name__)

DEFAULT_SOURCE_TYPE = "pdf_statement"
DEFAULT_SOURCE_SYSTEM = "broker_pdf_dataset_1"
DEFAULT_FINGERPRINT_VERSION = "v1"
DEFAULT_CANONICAL_SCHEMA_VERSION = "dataset_1_v1"

_TRADE_EVENT_TYPE = "trade"
_DIVIDEND_EVENT_TYPE = "dividend"
_SPLIT_EVENT_TYPE = "split"

_PROVENANCE_FINGERPRINT_FIELDS: tuple[str, ...] = (
    "table_name",
    "row_index",
    "source_page",
)
_EVENT_FINGERPRINT_FIELDS: dict[str, tuple[str, ...]] = {
    _TRADE_EVENT_TYPE: (
        "trade_date",
        "instrument_symbol",
        "trade_side",
        "aporte_usd",
        "rescate_usd",
        "acciones_compradas_qty",
        "acciones_vendidas_qty",
    ),
    _DIVIDEND_EVENT_TYPE: (
        "dividend_date",
        "instrument_symbol",
        "gross_usd",
        "taxes_usd",
        "net_usd",
    ),
    _SPLIT_EVENT_TYPE: (
        "split_date",
        "instrument_symbol",
        "shares_before_qty",
        "shares_after_qty",
        "split_ratio_value",
    ),
}


class PdfPersistenceClientError(ValueError):
    """Raised when persistence helper input cannot be processed deterministically."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize client-facing persistence helper error."""

        super().__init__(message)
        self.status_code = status_code


async def persist_pdf_from_storage(
    *,
    storage_key: str,
    storage_root: Path,
    db: AsyncSession,
) -> PdfPersistenceResult:
    """Persist deduplicated source metadata and canonical records transactionally."""

    normalized_storage_key = _normalize_required_text(storage_key, field="storage_key")
    logger.info(
        "pdf_persistence.execution_started",
        storage_key=normalized_storage_key,
    )

    ingestion_result = _load_ingestion_result(
        storage_key=normalized_storage_key,
        storage_root=storage_root,
    )
    normalization_result = _load_normalization_result(
        storage_key=normalized_storage_key,
        storage_root=storage_root,
    )

    try:
        result = await _persist_normalization_result(
            storage_key=normalized_storage_key,
            ingestion_result=ingestion_result,
            normalization_result=normalization_result,
            db=db,
        )
    except PdfPersistenceClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "pdf_persistence.execution_failed",
            storage_key=normalized_storage_key,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PdfPersistenceClientError(
            "Failed to persist canonical records due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "pdf_persistence.execution_completed",
        storage_key=result.storage_key,
        source_document_id=result.source_document_id,
        source_document_status=result.source_document_status.value,
        import_job_id=result.import_job_id,
        inserted_records=result.summary.inserted_records,
        duplicate_records=result.summary.duplicate_records,
    )
    return result


def _load_ingestion_result(*, storage_key: str, storage_root: Path) -> PdfIngestionResult:
    """Load durable ingestion metadata for persistence."""

    try:
        return load_ingestion_result_from_storage(
            storage_key=storage_key,
            storage_root=storage_root,
        )
    except PdfIngestionClientError as exc:
        logger.info(
            "pdf_persistence.ingestion_metadata_rejected",
            storage_key=storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise PdfPersistenceClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc


def _load_normalization_result(*, storage_key: str, storage_root: Path) -> PdfNormalizationResult:
    """Normalize a stored PDF into canonical records for persistence."""

    try:
        return normalize_pdf_from_storage(
            storage_key=storage_key,
            storage_root=storage_root,
        )
    except PdfNormalizationClientError as exc:
        logger.info(
            "pdf_persistence.normalization_rejected",
            storage_key=storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise PdfPersistenceClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc


async def _persist_normalization_result(
    *,
    storage_key: str,
    ingestion_result: PdfIngestionResult,
    normalization_result: PdfNormalizationResult,
    db: AsyncSession,
) -> PdfPersistenceResult:
    """Persist source document, import job, and canonical records in one transaction."""

    async with db.begin():
        source_document, source_document_status = await _resolve_or_create_source_document(
            ingestion_result=ingestion_result,
            db=db,
        )

        import_job = ImportJob(
            source_document_id=source_document.id,
            storage_key=storage_key,
            normalized_records=0,
            inserted_records=0,
            duplicate_records=0,
        )
        db.add(import_job)
        await db.flush()

        import_job_id = import_job.id

        inserted_records, duplicate_records = await _insert_canonical_records(
            source_document_id=source_document.id,
            import_job_id=import_job_id,
            records=normalization_result.records,
            db=db,
        )

        summary = build_persistence_summary(
            normalized_records=len(normalization_result.records),
            inserted_records=inserted_records,
            duplicate_records=duplicate_records,
        )

        import_job.normalized_records = summary.normalized_records
        import_job.inserted_records = summary.inserted_records
        import_job.duplicate_records = summary.duplicate_records

        return PdfPersistenceResult(
            storage_key=storage_key,
            source_document_id=source_document.id,
            source_document_status=source_document_status,
            import_job_id=import_job_id,
            summary=summary,
            source_type=DEFAULT_SOURCE_TYPE,
            source_system=DEFAULT_SOURCE_SYSTEM,
            fingerprint_version=DEFAULT_FINGERPRINT_VERSION,
            canonical_schema_version=DEFAULT_CANONICAL_SCHEMA_VERSION,
        )


async def _resolve_or_create_source_document(
    *,
    ingestion_result: PdfIngestionResult,
    db: AsyncSession,
) -> tuple[SourceDocument, SourceDocumentPersistenceStatus]:
    """Resolve deduplicated source document by SHA-256 with conflict-safe insert."""

    insert_statement = (
        postgresql_insert(SourceDocument)
        .values(
            sha256=ingestion_result.sha256,
            storage_key=ingestion_result.storage_key,
            original_filename=ingestion_result.original_filename,
            content_type=ingestion_result.content_type,
            file_size_bytes=ingestion_result.file_size_bytes,
            page_count=ingestion_result.page_count,
        )
        .on_conflict_do_nothing(index_elements=[SourceDocument.sha256])
        .returning(SourceDocument.id)
    )
    insert_result = await db.execute(insert_statement)
    inserted_source_document_id = insert_result.scalar_one_or_none()

    if inserted_source_document_id is None:
        source_document = await _fetch_source_document_by_sha256(
            sha256=ingestion_result.sha256,
            db=db,
        )
        return source_document, SourceDocumentPersistenceStatus.REUSED

    created_source_document = await db.get(SourceDocument, inserted_source_document_id)
    if created_source_document is None:
        raise PdfPersistenceClientError(
            "Created source document could not be loaded from database.",
            status_code=500,
        )
    return created_source_document, SourceDocumentPersistenceStatus.CREATED


async def _fetch_source_document_by_sha256(
    *,
    sha256: str,
    db: AsyncSession,
) -> SourceDocument:
    """Fetch existing source document row by deterministic hash."""

    query = select(SourceDocument).where(SourceDocument.sha256 == sha256)
    query_result = await db.execute(query)
    source_document = query_result.scalar_one_or_none()
    if not isinstance(source_document, SourceDocument):
        raise PdfPersistenceClientError(
            "Existing source document was not found after duplicate detection.",
            status_code=500,
        )
    return source_document


async def _insert_canonical_records(
    *,
    source_document_id: int,
    import_job_id: int,
    records: Sequence[CanonicalRecord],
    db: AsyncSession,
) -> tuple[int, int]:
    """Insert canonical records and skip duplicates via unique fingerprint conflicts."""

    inserted_records = 0
    duplicate_records = 0

    for record in records:
        fingerprint = build_canonical_record_fingerprint(
            record=record,
            source_type=DEFAULT_SOURCE_TYPE,
            source_system=DEFAULT_SOURCE_SYSTEM,
            fingerprint_version=DEFAULT_FINGERPRINT_VERSION,
        )
        event_date, trade_side = _extract_record_surface(record)
        canonical_payload = _build_canonical_payload(record)
        provenance_payload = _coerce_record_mapping(
            record.provenance.model_dump(mode="json"),
            context="record.provenance",
        )

        insert_statement = (
            postgresql_insert(CanonicalPdfRecord)
            .values(
                source_document_id=source_document_id,
                import_job_id=import_job_id,
                event_type=record.event_type.value,
                event_date=event_date,
                instrument_symbol=record.instrument_symbol,
                trade_side=trade_side,
                fingerprint=fingerprint,
                fingerprint_version=DEFAULT_FINGERPRINT_VERSION,
                canonical_schema_version=DEFAULT_CANONICAL_SCHEMA_VERSION,
                canonical_payload=canonical_payload,
                raw_values=dict(record.raw_values),
                provenance=dict(provenance_payload),
            )
            .on_conflict_do_nothing(index_elements=[CanonicalPdfRecord.fingerprint])
            .returning(CanonicalPdfRecord.id)
        )
        insert_result = await db.execute(insert_statement)
        inserted_record_id = insert_result.scalar_one_or_none()
        if inserted_record_id is None:
            duplicate_records += 1
            continue

        inserted_records += 1

    return inserted_records, duplicate_records


def _extract_record_surface(record: CanonicalRecord) -> tuple[date, str | None]:
    """Extract typed structured columns from one canonical record."""

    if isinstance(record, CanonicalTradeRecord):
        return record.trade_date, record.trade_side.value
    if isinstance(record, CanonicalDividendRecord):
        return record.dividend_date, None
    return record.split_date, None


def _build_canonical_payload(record: CanonicalRecord) -> dict[str, object]:
    """Build JSON-safe canonical payload excluding raw values and provenance."""

    payload_mapping = _coerce_record_mapping(
        record.model_dump(mode="json", exclude={"raw_values", "provenance"}),
        context="canonical_payload",
    )
    return dict(payload_mapping)


def build_canonical_record_fingerprint(
    *,
    record: Mapping[str, object] | BaseModel,
    source_type: str,
    source_system: str,
    fingerprint_version: str,
) -> str:
    """Build deterministic SHA-256 fingerprint for one canonical record.

    The payload includes source-scope fields, event-specific business fields,
    and stable provenance fallback fields required by the spec.
    """

    normalized_source_type = _normalize_required_text(source_type, field="source_type")
    normalized_source_system = _normalize_required_text(source_system, field="source_system")
    normalized_fingerprint_version = _normalize_required_text(
        fingerprint_version,
        field="fingerprint_version",
    )

    record_payload = _coerce_record_mapping(record, context="record")
    event_type = _normalize_required_text(
        _read_required_field(record_payload, "event_type", context="record"),
        field="event_type",
    )
    event_fields = _EVENT_FINGERPRINT_FIELDS.get(event_type)
    if event_fields is None:
        raise PdfPersistenceClientError(
            f"Unsupported canonical event_type '{event_type}' for fingerprint generation.",
            status_code=422,
        )

    provenance_payload = _coerce_record_mapping(
        _read_required_field(record_payload, "provenance", context="record"),
        context="record.provenance",
    )

    fingerprint_payload: dict[str, object] = {
        "source_type": normalized_source_type,
        "source_system": normalized_source_system,
        "event_type": event_type,
        "fingerprint_version": normalized_fingerprint_version,
    }

    for field_name in event_fields:
        fingerprint_payload[field_name] = _normalize_fingerprint_value(
            _read_required_field(record_payload, field_name, context="record")
        )
    for field_name in _PROVENANCE_FINGERPRINT_FIELDS:
        fingerprint_payload[field_name] = _normalize_fingerprint_value(
            _read_required_field(
                provenance_payload,
                field_name,
                context="record.provenance",
            )
        )

    serialized_payload = json.dumps(
        fingerprint_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(serialized_payload.encode("utf-8")).hexdigest()


def calculate_persistence_counts(
    *,
    candidate_fingerprints: Sequence[str],
    existing_fingerprints: Set[str],
) -> tuple[int, int]:
    """Return inserted and duplicate counts for candidate fingerprints.

    This helper is advisory for request accounting; database uniqueness
    constraints remain the final arbiter for concurrent duplicate races.
    """

    seen_in_request: set[str] = set()
    inserted_records = 0
    duplicate_records = 0

    for fingerprint in candidate_fingerprints:
        normalized_fingerprint = _normalize_required_text(
            fingerprint,
            field="fingerprint",
        )
        if (
            normalized_fingerprint in existing_fingerprints
            or normalized_fingerprint in seen_in_request
        ):
            duplicate_records += 1
            continue

        inserted_records += 1
        seen_in_request.add(normalized_fingerprint)

    return inserted_records, duplicate_records


def build_persistence_summary(
    *,
    normalized_records: int,
    inserted_records: int,
    duplicate_records: int,
) -> PdfPersistenceSummary:
    """Build typed persistence summary with strict record accounting checks."""

    return PdfPersistenceSummary(
        normalized_records=normalized_records,
        inserted_records=inserted_records,
        duplicate_records=duplicate_records,
    )


def _coerce_record_mapping(
    value: Mapping[str, object] | BaseModel | object,
    *,
    context: str,
) -> Mapping[str, object]:
    """Convert a record-like input into a mapping."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    if isinstance(value, Mapping):
        mapping_value = cast(Mapping[object, object], value)
        payload: dict[str, object] = {}
        for raw_key, raw_value in mapping_value.items():
            if not isinstance(raw_key, str):
                raise PdfPersistenceClientError(
                    f"{context} keys must be strings.",
                    status_code=422,
                )
            payload[raw_key] = raw_value
        return payload

    raise PdfPersistenceClientError(
        f"{context} must be an object-like mapping.",
        status_code=422,
    )


def _read_required_field(
    payload: Mapping[str, object],
    field_name: str,
    *,
    context: str,
) -> object:
    """Read a required field from mapping payload."""

    if field_name not in payload:
        raise PdfPersistenceClientError(
            f"Missing required field '{field_name}' in {context}.",
            status_code=422,
        )
    return payload[field_name]


def _normalize_required_text(value: object, *, field: str) -> str:
    """Normalize required non-empty string fields."""

    if not isinstance(value, str):
        raise PdfPersistenceClientError(
            f"Field '{field}' must be a string.",
            status_code=422,
        )
    normalized = value.strip()
    if not normalized:
        raise PdfPersistenceClientError(
            f"Field '{field}' must be a non-empty string.",
            status_code=422,
        )
    return normalized


def _normalize_fingerprint_value(value: object) -> object:
    """Normalize values into deterministic JSON-safe primitives."""

    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return _normalize_fingerprint_value(value.value)
    if isinstance(value, BaseModel):
        return _normalize_fingerprint_value(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        mapping_value = cast(Mapping[object, object], value)
        normalized_items: dict[str, object] = {}
        for raw_key, raw_nested_value in mapping_value.items():
            key = str(raw_key)
            normalized_items[key] = _normalize_fingerprint_value(raw_nested_value)
        return normalized_items
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        sequence_value = cast(Sequence[object], value)
        normalized_sequence: list[object] = []
        for item in sequence_value:
            normalized_sequence.append(_normalize_fingerprint_value(item))
        return normalized_sequence

    raise PdfPersistenceClientError(
        f"Unsupported fingerprint value type: {type(value).__name__}.",
        status_code=422,
    )
