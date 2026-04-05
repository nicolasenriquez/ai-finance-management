"""Typed schemas for portfolio ML signal contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class PortfolioMLScope(StrEnum):
    """Supported scope values for portfolio_ml signal requests."""

    PORTFOLIO = "portfolio"
    INSTRUMENT_SYMBOL = "instrument_symbol"


class PortfolioMLState(StrEnum):
    """Lifecycle state values for portfolio_ml read-only contracts."""

    READY = "ready"
    UNAVAILABLE = "unavailable"
    STALE = "stale"
    ERROR = "error"


class PortfolioMLFreshnessPolicy(BaseModel):
    """Freshness policy metadata included in every signal response."""

    max_age_hours: int = Field(ge=1)


class PortfolioMLSignalRow(BaseModel):
    """One deterministic signal row."""

    signal_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    interpretation_band: str = Field(min_length=1)
    value: Decimal


class PortfolioMLCapmMetrics(BaseModel):
    """CAPM metric payload with provenance metadata."""

    beta: Decimal | None = None
    alpha: Decimal | None = None
    expected_return: Decimal | None = None
    market_premium: Decimal | None = None
    benchmark_symbol: str | None = None
    risk_free_source: str | None = None
    annualization_factor: int | None = None


class PortfolioMLSignalResponse(BaseModel):
    """Read-only signal response contract for portfolio and instrument scopes."""

    state: PortfolioMLState
    state_reason_code: str = Field(min_length=1)
    state_reason_detail: str = Field(min_length=1)
    scope: PortfolioMLScope
    instrument_symbol: str | None = None
    as_of_ledger_at: datetime
    as_of_market_at: datetime
    evaluated_at: datetime
    freshness_policy: PortfolioMLFreshnessPolicy
    signals: list[PortfolioMLSignalRow]
    capm: PortfolioMLCapmMetrics


class PortfolioMLForecastHorizonRow(BaseModel):
    """One probabilistic forecast horizon row."""

    horizon_id: str = Field(min_length=1)
    point_estimate: Decimal
    lower_bound: Decimal
    upper_bound: Decimal
    confidence_level: Decimal
    model_snapshot_ref: str = Field(min_length=1)


class PortfolioMLForecastResponse(BaseModel):
    """Read-only forecast response contract for portfolio and instrument scopes."""

    state: PortfolioMLState
    state_reason_code: str = Field(min_length=1)
    state_reason_detail: str = Field(min_length=1)
    scope: PortfolioMLScope
    instrument_symbol: str | None = None
    as_of_ledger_at: datetime
    as_of_market_at: datetime
    evaluated_at: datetime
    freshness_policy: PortfolioMLFreshnessPolicy
    model_snapshot_ref: str | None = None
    model_family: str | None = None
    training_window_start: datetime | None = None
    training_window_end: datetime | None = None
    horizons: list[PortfolioMLForecastHorizonRow]


class PortfolioMLRegistryRow(BaseModel):
    """One registry audit row for model snapshot lineage and promotion metadata."""

    snapshot_ref: str = Field(min_length=1)
    scope: PortfolioMLScope
    instrument_symbol: str | None = None
    model_family: str = Field(min_length=1)
    lifecycle_state: PortfolioMLState
    feature_set_hash: str = Field(min_length=1)
    data_window_start: datetime
    data_window_end: datetime
    run_status: str = Field(min_length=1)
    promoted_at: datetime | None = None
    expires_at: datetime | None = None
    replaced_snapshot_ref: str | None = None
    policy_result: dict[str, object]
    metric_vector: dict[str, object]
    baseline_comparator_metrics: dict[str, object]


class PortfolioMLRegistryResponse(BaseModel):
    """Read-only model-registry audit response for snapshot lineage queries."""

    state: PortfolioMLState
    state_reason_code: str = Field(min_length=1)
    state_reason_detail: str = Field(min_length=1)
    as_of_ledger_at: datetime
    as_of_market_at: datetime
    evaluated_at: datetime
    rows: list[PortfolioMLRegistryRow]
