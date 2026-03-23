"""Typed schemas for portfolio-ledger canonical inputs and derived event seeds."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class LedgerEventType(StrEnum):
    """Dataset-1 canonical event types supported by the portfolio ledger."""

    TRADE = "trade"
    DIVIDEND = "dividend"
    SPLIT = "split"


class LedgerTargetTable(StrEnum):
    """Target ledger-domain tables used by canonical-to-ledger mapping."""

    PORTFOLIO_TRANSACTION = "portfolio_transaction"
    DIVIDEND_EVENT = "dividend_event"
    CORPORATE_ACTION_EVENT = "corporate_action_event"


class LedgerLineage(BaseModel):
    """Queryable lineage metadata for derived ledger rows."""

    source_document_id: int = Field(ge=1)
    import_job_id: int = Field(ge=1)
    canonical_record_id: int = Field(ge=1)
    canonical_fingerprint: str = Field(min_length=1)


class PersistedCanonicalRecord(BaseModel):
    """Typed surface for persisted canonical records used by rebuild flows."""

    canonical_record_id: int = Field(ge=1)
    source_document_id: int = Field(ge=1)
    import_job_id: int = Field(ge=1)
    fingerprint: str = Field(min_length=1)
    event_type: LedgerEventType
    event_date: date
    instrument_symbol: str = Field(min_length=1)
    trade_side: str | None = None
    canonical_payload: dict[str, object]


class LedgerEventSeed(BaseModel):
    """Typed seed object for writing one derived ledger-domain event."""

    target_table: LedgerTargetTable
    event_type: LedgerEventType
    event_date: date
    instrument_symbol: str = Field(min_length=1)
    lineage: LedgerLineage
    canonical_payload: dict[str, object]
