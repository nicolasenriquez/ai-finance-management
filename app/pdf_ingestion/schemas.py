"""Schemas for PDF ingestion responses."""

from pydantic import BaseModel, Field

from app.pdf_preflight.schemas import PdfPreflightResult


class PdfIngestionResult(BaseModel):
    """Response schema for PDF ingestion."""

    document_id: str = Field(
        min_length=1,
        description="Generated identifier for the uploaded document.",
    )
    original_filename: str = Field(
        min_length=1,
        description="Original file name from the client upload.",
    )
    content_type: str = Field(
        min_length=1,
        description="MIME type declared for the uploaded file.",
    )
    file_size_bytes: int = Field(
        ge=0,
        description="Total uploaded file size in bytes.",
    )
    sha256: str = Field(
        min_length=64,
        max_length=64,
        description="SHA-256 digest of the uploaded PDF bytes.",
    )
    page_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of PDF pages when it can be determined safely.",
    )
    storage_key: str = Field(
        min_length=1,
        description="Relative storage key under the configured upload root.",
    )
    preflight: PdfPreflightResult
