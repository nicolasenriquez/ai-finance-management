"""Typed schemas for portfolio rebalancing strategy comparisons."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class PortfolioRebalancingState(StrEnum):
    """Lifecycle states for rebalancing response contracts."""

    READY = "ready"
    UNAVAILABLE = "unavailable"
    INFEASIBLE = "infeasible"


class PortfolioRebalancingFreshnessPolicy(BaseModel):
    """Freshness policy metadata for rebalancing strategies."""

    max_age_hours: int = Field(ge=1)


class PortfolioRebalancingStrategyId(StrEnum):
    """Strategy identifiers published by the rebalancing endpoint."""

    MVO = "mvo"
    HRP = "hrp"
    BLACK_LITTERMAN = "black_litterman"


class PortfolioRebalancingWeightRow(BaseModel):
    """One instrument weight comparison row."""

    instrument_symbol: str = Field(min_length=1)
    current_weight_pct: Decimal
    suggested_weight_pct: Decimal
    delta_weight_pct: Decimal


class PortfolioRebalancingStrategyRow(BaseModel):
    """One strategy candidate row with expected outcome metrics."""

    strategy_id: PortfolioRebalancingStrategyId
    strategy_label: str = Field(min_length=1)
    expected_return_annualized: Decimal
    expected_volatility_annualized: Decimal
    expected_sharpe: Decimal
    weights: list[PortfolioRebalancingWeightRow]


class PortfolioRebalancingStrategiesResponse(BaseModel):
    """Read-only strategy comparison payload for rebalancing studio."""

    state: PortfolioRebalancingState
    state_reason_code: str = Field(min_length=1)
    state_reason_detail: str = Field(min_length=1)
    as_of_ledger_at: datetime
    as_of_market_at: datetime | None = None
    evaluated_at: datetime
    freshness_policy: PortfolioRebalancingFreshnessPolicy
    strategies: list[PortfolioRebalancingStrategyRow]
    caveats: list[str] = Field(default_factory=list[str])


class PortfolioRebalancingScenarioConstraints(BaseModel):
    """Typed scenario constraints for constrained strategy diagnostics."""

    max_position_weight_pct: Decimal | None = Field(
        default=None, gt=Decimal("0"), le=Decimal("100")
    )
    max_turnover_pct: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    excluded_symbols: list[str] = Field(default_factory=list[str], max_length=25)

    @model_validator(mode="after")
    def normalize_symbols(self) -> PortfolioRebalancingScenarioConstraints:
        """Normalize and deduplicate excluded symbols deterministically."""

        normalized_symbols: list[str] = []
        for symbol in self.excluded_symbols:
            normalized_symbol = symbol.strip().upper()
            if normalized_symbol and normalized_symbol not in normalized_symbols:
                normalized_symbols.append(normalized_symbol)
        self.excluded_symbols = normalized_symbols
        return self


class PortfolioRebalancingScenarioRequest(BaseModel):
    """Scenario request envelope for constrained rebalancing diagnostics."""

    constraints: PortfolioRebalancingScenarioConstraints = Field(
        default_factory=PortfolioRebalancingScenarioConstraints
    )


class PortfolioRebalancingScenarioResponse(BaseModel):
    """Read-only constrained rebalancing response with infeasible-state semantics."""

    state: PortfolioRebalancingState
    state_reason_code: str = Field(min_length=1)
    state_reason_detail: str = Field(min_length=1)
    as_of_ledger_at: datetime
    as_of_market_at: datetime | None = None
    evaluated_at: datetime
    freshness_policy: PortfolioRebalancingFreshnessPolicy
    applied_constraints: PortfolioRebalancingScenarioConstraints
    binding_constraints: list[str] = Field(default_factory=list[str])
    baseline_strategies: list[PortfolioRebalancingStrategyRow] = Field(
        default_factory=list[PortfolioRebalancingStrategyRow]
    )
    constrained_strategies: list[PortfolioRebalancingStrategyRow] = Field(
        default_factory=list[PortfolioRebalancingStrategyRow]
    )
    infeasible_cause: str | None = None
    caveats: list[str] = Field(default_factory=list[str])
