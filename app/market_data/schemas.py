"""Typed schemas for market-data ingestion and read-boundary contracts."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class MarketDataPriceWrite(BaseModel):
    """One price payload row for market-data ingestion."""

    instrument_symbol: str = Field(min_length=1)
    market_timestamp: datetime | None = None
    trading_date: date | None = None
    price_value: Decimal
    currency_code: str = Field(default="USD", min_length=1, max_length=8)
    source_payload: dict[str, object] | None = None

    @model_validator(mode="after")
    def validate_market_time_context(self) -> Self:
        """Require exactly one market-time key for deterministic persistence."""

        if self.market_timestamp is None and self.trading_date is None:
            raise ValueError("Either market_timestamp or trading_date must be provided.")
        if self.market_timestamp is not None and self.trading_date is not None:
            raise ValueError("Provide only one of market_timestamp or trading_date.")
        return self


class MarketDataSnapshotWriteRequest(BaseModel):
    """Request schema for writing one market-data snapshot."""

    source_type: str = Field(min_length=1)
    source_provider: str = Field(min_length=1)
    snapshot_key: str = Field(min_length=1)
    snapshot_captured_at: datetime
    snapshot_metadata: dict[str, object] | None = None
    prices: list[MarketDataPriceWrite] = Field(min_length=1)


class MarketDataSnapshotWriteResult(BaseModel):
    """Write-result summary for one persisted market-data snapshot."""

    snapshot_id: int = Field(ge=1)
    inserted_prices: int = Field(ge=0)
    updated_prices: int = Field(ge=0)


class MarketDataPriceRow(BaseModel):
    """Read-boundary row for one persisted market-data value."""

    instrument_symbol: str = Field(min_length=1)
    market_timestamp: datetime | None = None
    trading_date: date | None = None
    price_value: Decimal
    currency_code: str = Field(min_length=1, max_length=8)
    snapshot_id: int = Field(ge=1)
    source_type: str = Field(min_length=1)
    source_provider: str = Field(min_length=1)
    snapshot_key: str = Field(min_length=1)
    snapshot_captured_at: datetime


class MarketDataRefreshRunResult(BaseModel):
    """Structured result for one operator-triggered market-data refresh run."""

    status: Literal["completed"] = "completed"
    source_type: str = Field(min_length=1)
    source_provider: str = Field(min_length=1)
    requested_symbols: list[str] = Field(min_length=1)
    snapshot_key: str = Field(min_length=1)
    snapshot_captured_at: datetime
    snapshot_id: int = Field(ge=1)
    inserted_prices: int = Field(ge=0)
    updated_prices: int = Field(ge=0)
