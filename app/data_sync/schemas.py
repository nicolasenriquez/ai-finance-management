"""Typed schemas for local data-sync operational workflows."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.market_data.schemas import MarketDataRefreshRunResult


class PortfolioLedgerRebuildRunResult(BaseModel):
    """Structured ledger-rebuild evidence for one source document."""

    source_document_id: int = Field(ge=1)
    processed_records: int = Field(ge=0)
    portfolio_transactions: int = Field(ge=0)
    dividend_events: int = Field(ge=0)
    corporate_action_events: int = Field(ge=0)
    open_lots: int = Field(ge=0)
    lot_dispositions: int = Field(ge=0)


class DatasetBootstrapRunResult(BaseModel):
    """Structured result for one dataset_1 bootstrap workflow run."""

    status: Literal["completed"] = "completed"
    dataset_pdf_path: str = Field(min_length=1)
    storage_key: str = Field(min_length=1)
    source_document_id: int = Field(ge=1)
    import_job_id: int = Field(ge=1)
    normalized_records: int = Field(ge=0)
    inserted_records: int = Field(ge=0)
    duplicate_records: int = Field(ge=0)
    rebuild: PortfolioLedgerRebuildRunResult


class DataSyncLocalRunResult(BaseModel):
    """Structured result for one combined local data-sync run.

    The `market_refresh` payload includes typed retry and recovery diagnostics
    from market-data operations.
    """

    status: Literal["completed"] = "completed"
    bootstrap: DatasetBootstrapRunResult
    market_refresh: MarketDataRefreshRunResult
