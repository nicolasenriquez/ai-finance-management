"""Typed schemas for portfolio analytics summary and lot-detail responses."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PortfolioSummaryRow(BaseModel):
    """One grouped portfolio analytics row for an instrument symbol."""

    instrument_symbol: str = Field(min_length=1)
    open_quantity: Decimal
    open_cost_basis_usd: Decimal
    open_lot_count: int = Field(ge=0)
    realized_proceeds_usd: Decimal
    realized_cost_basis_usd: Decimal
    realized_gain_usd: Decimal
    dividend_gross_usd: Decimal
    dividend_taxes_usd: Decimal
    dividend_net_usd: Decimal


class PortfolioSummaryResponse(BaseModel):
    """Portfolio grouped-summary API response."""

    as_of_ledger_at: datetime
    rows: list[PortfolioSummaryRow]


class LotDispositionDetail(BaseModel):
    """One sell-side disposition row linked to a lot."""

    sell_transaction_id: int = Field(ge=1)
    disposition_date: date
    matched_qty: Decimal
    matched_cost_basis_usd: Decimal
    sell_gross_amount_usd: Decimal


class PortfolioLotDetailRow(BaseModel):
    """One lot row in a lot-detail response."""

    lot_id: int = Field(ge=1)
    opened_on: date
    original_qty: Decimal
    remaining_qty: Decimal
    total_cost_basis_usd: Decimal
    unit_cost_basis_usd: Decimal
    dispositions: list[LotDispositionDetail]


class PortfolioLotDetailResponse(BaseModel):
    """Portfolio lot-detail API response for one instrument symbol."""

    as_of_ledger_at: datetime
    instrument_symbol: str = Field(min_length=1)
    lots: list[PortfolioLotDetailRow]
