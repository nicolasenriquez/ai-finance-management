"""Typed schemas for portfolio analytics summary and lot-detail responses."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

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
    latest_close_price_usd: Decimal | None = None
    market_value_usd: Decimal | None = None
    unrealized_gain_usd: Decimal | None = None
    unrealized_gain_pct: Decimal | None = None


class PortfolioSummaryResponse(BaseModel):
    """Portfolio grouped-summary API response."""

    as_of_ledger_at: datetime
    pricing_snapshot_key: str | None = None
    pricing_snapshot_captured_at: datetime | None = None
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


class PortfolioChartPeriod(StrEnum):
    """Supported period values for chart-oriented analytics endpoints."""

    D30 = "30D"
    D90 = "90D"
    D252 = "252D"
    MAX = "MAX"


class PortfolioTimeSeriesPoint(BaseModel):
    """One chartable portfolio point for time-series responses."""

    captured_at: datetime
    portfolio_value_usd: Decimal
    pnl_usd: Decimal


class PortfolioTimeSeriesResponse(BaseModel):
    """Time-series response payload for portfolio value trend views."""

    as_of_ledger_at: datetime
    period: PortfolioChartPeriod
    frequency: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    points: list[PortfolioTimeSeriesPoint]


class PortfolioContributionRow(BaseModel):
    """One per-symbol contribution aggregate row for selected period."""

    instrument_symbol: str = Field(min_length=1)
    contribution_pnl_usd: Decimal
    contribution_pct: Decimal


class PortfolioContributionResponse(BaseModel):
    """Contribution breakdown response for one selected chart period."""

    as_of_ledger_at: datetime
    period: PortfolioChartPeriod
    rows: list[PortfolioContributionRow]


class PortfolioTransactionEvent(BaseModel):
    """One persisted ledger event row for transactions route rendering."""

    id: str = Field(min_length=1)
    posted_at: datetime
    instrument_symbol: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    quantity: Decimal
    cash_amount_usd: Decimal


class PortfolioTransactionsResponse(BaseModel):
    """Transactions response payload for persisted ledger-event history."""

    as_of_ledger_at: datetime
    events: list[PortfolioTransactionEvent]


class PortfolioAnnualizationBasis(BaseModel):
    """Annualization basis metadata carried by risk metrics."""

    kind: Literal["trading_days"]
    value: int = Field(ge=1)


class PortfolioRiskEstimatorMetric(BaseModel):
    """One computed portfolio risk metric with methodology context."""

    estimator_id: str = Field(min_length=1)
    value: Decimal
    window_days: int = Field(ge=1)
    return_basis: Literal["simple", "log"]
    annualization_basis: PortfolioAnnualizationBasis
    as_of_timestamp: datetime


class PortfolioRiskEstimatorsResponse(BaseModel):
    """Risk-estimators response payload for portfolio analytics routes."""

    as_of_ledger_at: datetime
    window_days: int = Field(ge=1)
    metrics: list[PortfolioRiskEstimatorMetric]
