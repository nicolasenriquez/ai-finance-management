"""Schemas for PDF preflight analysis."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ExtractabilityStatus(StrEnum):
    """Machine-readable extractability statuses for PDF preflight."""

    EXTRACTABLE = "extractable"
    ENCRYPTED = "encrypted"
    OCR_REQUIRED = "ocr_required"


class PdfPreflightResult(BaseModel):
    """Response schema for PDF preflight analysis."""

    status: ExtractabilityStatus
    message: str
    encrypted: bool
    page_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of pages when it can be determined safely.",
    )
    extracted_text_char_count: int = Field(
        ge=0,
        description="Count of extracted non-whitespace text characters.",
    )
    min_text_chars_required: int = Field(
        ge=0,
        description="Configured minimum non-whitespace character threshold.",
    )
    ocr_supported: bool = Field(
        default=False,
        description="Whether the current pipeline can fall back to OCR.",
    )
