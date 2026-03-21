"""Tests for PDF persistence schemas."""

import pytest
from pydantic import ValidationError

from app.pdf_persistence.schemas import (
    PdfPersistenceErrorCode,
    PdfPersistenceErrorDetail,
    PdfPersistenceErrorResponse,
    PdfPersistenceRequest,
    PdfPersistenceResult,
    PdfPersistenceSummary,
    SourceDocumentPersistenceStatus,
)


def test_persistence_request_requires_storage_key() -> None:
    """Persistence request should reject blank storage keys."""

    with pytest.raises(ValidationError):
        PdfPersistenceRequest(storage_key="")


def test_persistence_summary_requires_accounted_record_totals() -> None:
    """Summary counts should enforce inserted + duplicate = normalized."""

    valid_summary = PdfPersistenceSummary(
        normalized_records=5,
        inserted_records=2,
        duplicate_records=3,
    )
    assert valid_summary.accounted_records == 5

    with pytest.raises(ValidationError):
        PdfPersistenceSummary(
            normalized_records=5,
            inserted_records=2,
            duplicate_records=2,
        )


def test_persistence_result_is_typed_for_document_and_import_job_outcomes() -> None:
    """Result schema should capture document reuse and successful import job identity."""

    result = PdfPersistenceResult(
        storage_key="doc-123.pdf",
        source_document_id=10,
        source_document_status=SourceDocumentPersistenceStatus.REUSED,
        import_job_id=55,
        summary=PdfPersistenceSummary(
            normalized_records=3,
            inserted_records=1,
            duplicate_records=2,
        ),
        source_type="pdf_statement",
        source_system="broker_pdf_dataset_1",
        fingerprint_version="v1",
        canonical_schema_version="dataset_1_v1",
    )

    assert result.source_document_status == SourceDocumentPersistenceStatus.REUSED
    assert result.import_job_id == 55
    assert result.summary.inserted_records == 1
    assert result.summary.duplicate_records == 2


def test_persistence_error_contract_is_typed() -> None:
    """Error contract should expose machine-readable codes with contextual metadata."""

    response = PdfPersistenceErrorResponse(
        error=PdfPersistenceErrorDetail(
            code=PdfPersistenceErrorCode.DATABASE_WRITE_FAILED,
            message="Failed to persist canonical records.",
            field="database",
        ),
        storage_key="doc-123.pdf",
    )

    assert response.error.code == PdfPersistenceErrorCode.DATABASE_WRITE_FAILED
    assert response.storage_key == "doc-123.pdf"
    assert response.import_job_id is None
