"""Schemas for PDF verification contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def _empty_mismatch_list() -> list[VerificationMismatch]:
    """Create typed empty mismatch list for strict type checkers."""

    return []


class VerificationStatus(StrEnum):
    """Top-level verification status."""

    PASSED = "passed"
    FAILED = "failed"


class PdfVerificationRequest(BaseModel):
    """Request schema for verifying a stored PDF upload."""

    storage_key: str = Field(
        min_length=1,
        description="Relative key under the configured PDF upload storage root.",
    )


class VerificationMismatch(BaseModel):
    """Field-level mismatch evidence."""

    table_name: str = Field(min_length=1)
    row_id: int | None = Field(default=None, ge=1)
    row_index: int = Field(ge=1)
    source_page: int | None = Field(default=None, ge=1)
    field: str = Field(min_length=1)
    expected_raw: str | None = None
    actual_raw: str | None = None


class VerificationSummary(BaseModel):
    """Verification summary counts."""

    expected_records: int = Field(ge=0)
    actual_records: int = Field(ge=0)
    mismatch_count: int = Field(ge=0)


class PdfVerificationResult(BaseModel):
    """Top-level verification response."""

    storage_key: str = Field(min_length=1)
    status: VerificationStatus
    source_pdf_pages: int | None = Field(default=None, ge=1)
    summary: VerificationSummary
    mismatches: list[VerificationMismatch] = Field(default_factory=_empty_mismatch_list)
    verified_at_utc: datetime | None = None
