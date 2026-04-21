"""Schemas for PDF extraction contracts."""

from pydantic import BaseModel, Field


class PdfExtractionRequest(BaseModel):
    """Request schema for extracting from a stored PDF upload."""

    storage_key: str = Field(
        min_length=1,
        description="Relative key under the configured PDF upload storage root.",
    )


class PdfExtractedRow(BaseModel):
    """One extracted table row with provenance."""

    row_id: int = Field(
        ge=1, description="Deterministic row identifier in emission order."
    )
    source_page: int = Field(
        ge=1, description="Source PDF page where the row originated."
    )
    raw_cells: dict[str, str | None] = Field(
        description="Raw source values keyed by canonical extraction column names.",
    )


class PdfExtractedTable(BaseModel):
    """Extracted table payload."""

    table_name: str = Field(
        min_length=1, description="Logical extracted table identifier."
    )
    columns: list[str] = Field(
        min_length=1,
        description="Deterministic output column order for this extracted table.",
    )
    rows: list[PdfExtractedRow] = Field(
        description="Row-wise extracted payload for the table."
    )


class PdfExtractionResult(BaseModel):
    """Top-level extraction response."""

    engine: str = Field(min_length=1, description="Extraction engine name.")
    storage_key: str = Field(
        min_length=1, description="Storage key used for this extraction run."
    )
    source_pdf_pages: int | None = Field(
        default=None,
        ge=1,
        description="Source PDF page count when known safely.",
    )
    tables: list[PdfExtractedTable] = Field(
        min_length=1,
        description="Extracted table outputs in deterministic order.",
    )
