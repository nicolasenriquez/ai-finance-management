"""Typed schemas for holdings-grounded portfolio news context."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class PortfolioNewsContextState(StrEnum):
    """Lifecycle states for news-context response contracts."""

    READY = "ready"
    UNAVAILABLE = "unavailable"


class PortfolioNewsFreshnessPolicy(BaseModel):
    """Freshness metadata for news-context payloads."""

    max_age_hours: int = Field(ge=1)


class PortfolioNewsSourceRow(BaseModel):
    """One source-provenance row for a generated symbol headline."""

    source_id: str = Field(min_length=1)
    source_label: str = Field(min_length=1)
    published_at: datetime
    url: str = Field(min_length=1)


class PortfolioNewsContextRow(BaseModel):
    """One holdings-grounded symbol context row."""

    instrument_symbol: str = Field(min_length=1)
    market_value_weight_pct: Decimal
    summary: str = Field(min_length=1)
    impact_bias: str = Field(min_length=1)
    caveats: list[str] = Field(default_factory=list[str])
    sources: list[PortfolioNewsSourceRow]


class PortfolioNewsContextResponse(BaseModel):
    """Read-only news-context payload tied to holdings scope."""

    state: PortfolioNewsContextState
    state_reason_code: str = Field(min_length=1)
    state_reason_detail: str = Field(min_length=1)
    as_of_ledger_at: datetime
    as_of_market_at: datetime | None = None
    evaluated_at: datetime
    freshness_policy: PortfolioNewsFreshnessPolicy
    rows: list[PortfolioNewsContextRow]
