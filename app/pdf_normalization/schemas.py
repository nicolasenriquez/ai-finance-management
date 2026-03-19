"""Schemas for PDF normalization contracts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class CanonicalEventType(StrEnum):
    """Canonical event types emitted by normalization."""

    TRADE = "trade"
    DIVIDEND = "dividend"
    SPLIT = "split"


class TradeSide(StrEnum):
    """Canonical trade direction."""

    BUY = "buy"
    SELL = "sell"


class PdfNormalizationRequest(BaseModel):
    """Request schema for normalizing a stored PDF upload."""

    storage_key: str = Field(
        min_length=1,
        description="Relative key under the configured PDF upload storage root.",
    )


class RowProvenance(BaseModel):
    """Source provenance carried by canonical records."""

    table_name: str = Field(min_length=1, description="Logical source table name.")
    row_id: int | None = Field(
        default=None, ge=1, description="Source row identifier when available."
    )
    row_index: int = Field(
        ge=1,
        description="Deterministic 1-based row index fallback inside the source table.",
    )
    source_page: int = Field(ge=1, description="Source PDF page for the record.")


class CanonicalTradeRecord(BaseModel):
    """Canonical trade event."""

    event_type: Literal[CanonicalEventType.TRADE] = CanonicalEventType.TRADE
    trade_side: TradeSide
    trade_date: date
    instrument_name: str = Field(min_length=1)
    instrument_symbol: str = Field(min_length=1)
    instrument_category: str = Field(min_length=1)
    aporte_usd: Decimal | None = None
    acciones_compradas_qty: Decimal | None = None
    rescate_usd: Decimal | None = None
    acciones_vendidas_qty: Decimal | None = None
    raw_values: dict[str, str | None] = Field(
        description="Source raw values preserved as audit truth.",
    )
    provenance: RowProvenance


class CanonicalDividendRecord(BaseModel):
    """Canonical dividend event."""

    event_type: Literal[CanonicalEventType.DIVIDEND] = CanonicalEventType.DIVIDEND
    dividend_date: date
    instrument_name: str = Field(min_length=1)
    instrument_symbol: str = Field(min_length=1)
    instrument_category: str = Field(min_length=1)
    gross_usd: Decimal
    taxes_usd: Decimal
    net_usd: Decimal
    raw_values: dict[str, str | None] = Field(
        description="Source raw values preserved as audit truth.",
    )
    provenance: RowProvenance


class CanonicalSplitRecord(BaseModel):
    """Canonical split event."""

    event_type: Literal[CanonicalEventType.SPLIT] = CanonicalEventType.SPLIT
    split_date: date
    instrument_name: str = Field(min_length=1)
    instrument_symbol: str = Field(min_length=1)
    instrument_category: str = Field(min_length=1)
    shares_before_qty: Decimal
    shares_after_qty: Decimal
    split_ratio_value: Decimal
    raw_values: dict[str, str | None] = Field(
        description="Source raw values preserved as audit truth.",
    )
    provenance: RowProvenance


CanonicalRecord = CanonicalTradeRecord | CanonicalDividendRecord | CanonicalSplitRecord


class PdfNormalizationSummary(BaseModel):
    """Normalization result summary."""

    trade_records: int = Field(ge=0)
    dividend_records: int = Field(ge=0)
    split_records: int = Field(ge=0)


class PdfNormalizationResult(BaseModel):
    """Top-level normalization response."""

    storage_key: str = Field(min_length=1)
    source_pdf_pages: int | None = Field(default=None, ge=1)
    records: list[CanonicalRecord]
    summary: PdfNormalizationSummary


class NormalizationErrorCode(StrEnum):
    """Machine-readable normalization error categories."""

    INVALID_DATE = "invalid_date"
    INVALID_NUMBER = "invalid_number"
    INVALID_MONEY = "invalid_money"
    AMBIGUOUS_TRADE_SIDE = "ambiguous_trade_side"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNSUPPORTED_TABLE_ROW = "unsupported_table_row"


class NormalizationValidationError(BaseModel):
    """Structured normalization validation failure."""

    code: NormalizationErrorCode
    message: str = Field(min_length=1)
    field: str | None = None
    raw_value: str | None = None
    provenance: RowProvenance | None = None
