"""Schemas for PDF persistence contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class PdfPersistenceRequest(BaseModel):
    """Request schema for persisting a stored PDF upload."""

    storage_key: str = Field(
        min_length=1,
        description="Relative key under the configured PDF upload storage root.",
    )


class SourceDocumentPersistenceStatus(StrEnum):
    """Document persistence outcome for a request."""

    CREATED = "created"
    REUSED = "reused"


class PdfPersistenceSummary(BaseModel):
    """Persistence result summary counts."""

    normalized_records: int = Field(
        ge=0,
        description="Total canonical records produced by normalization for this request.",
    )
    inserted_records: int = Field(
        ge=0,
        description="Canonical records inserted as new rows in this request.",
    )
    duplicate_records: int = Field(
        ge=0,
        description="Canonical records skipped as duplicates in this request.",
    )

    @property
    def accounted_records(self) -> int:
        """Return inserted plus duplicate records for accounting checks."""

        return self.inserted_records + self.duplicate_records

    @model_validator(mode="after")
    def validate_record_accounting(self) -> Self:
        """Ensure inserted plus duplicate counts match normalized records."""

        if self.accounted_records != self.normalized_records:
            raise ValueError(
                "Persistence summary is invalid: inserted_records + duplicate_records "
                "must equal normalized_records."
            )
        return self


class PdfPersistenceResult(BaseModel):
    """Top-level persistence response."""

    storage_key: str = Field(min_length=1)
    source_document_id: int = Field(
        ge=1,
        description="Database identifier of the deduplicated source document.",
    )
    source_document_status: SourceDocumentPersistenceStatus = Field(
        description="Whether source-document persistence created or reused the row.",
    )
    import_job_id: int = Field(
        ge=1,
        description="Database identifier for the successful import job.",
    )
    summary: PdfPersistenceSummary
    source_type: str = Field(
        min_length=1,
        description="Source type used by the persistence fingerprint contract.",
    )
    source_system: str = Field(
        min_length=1,
        description="Source system used by the persistence fingerprint contract.",
    )
    fingerprint_version: str = Field(
        min_length=1,
        description="Version string of the deterministic fingerprint contract.",
    )
    canonical_schema_version: str = Field(
        min_length=1,
        description="Version string of the canonical record schema contract.",
    )


class PdfPersistenceErrorCode(StrEnum):
    """Machine-readable persistence error categories."""

    INVALID_STORAGE_KEY = "invalid_storage_key"
    STORAGE_KEY_NOT_FOUND = "storage_key_not_found"
    INGESTION_METADATA_NOT_FOUND = "ingestion_metadata_not_found"
    INGESTION_METADATA_INVALID = "ingestion_metadata_invalid"
    NORMALIZATION_FAILED = "normalization_failed"
    DATABASE_WRITE_FAILED = "database_write_failed"
    PERSISTENCE_ROLLED_BACK = "persistence_rolled_back"


class PdfPersistenceErrorDetail(BaseModel):
    """Typed persistence error payload."""

    code: PdfPersistenceErrorCode
    message: str = Field(min_length=1)
    field: str | None = None


class PdfPersistenceErrorResponse(BaseModel):
    """Error response schema for persistence endpoints."""

    error: PdfPersistenceErrorDetail
    storage_key: str | None = Field(
        default=None,
        min_length=1,
        description="Storage key associated with the failed persistence request.",
    )
    import_job_id: int | None = Field(
        default=None,
        ge=1,
        description="Import-job identifier when a failure occurs after job creation.",
    )
