"""Typed schemas for portfolio analytics summary and lot-detail responses."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    D6M = "6M"
    D252 = "252D"
    YTD = "YTD"
    MAX = "MAX"


class PortfolioHierarchyGroupBy(StrEnum):
    """Supported grouping values for portfolio hierarchy responses."""

    SECTOR = "sector"
    SYMBOL = "symbol"


class PortfolioTimeSeriesPoint(BaseModel):
    """One chartable portfolio point for time-series responses."""

    captured_at: datetime
    portfolio_value_usd: Decimal
    pnl_usd: Decimal
    benchmark_sp500_value_usd: Decimal | None = None
    benchmark_nasdaq100_value_usd: Decimal | None = None


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


class PortfolioHierarchyLotRow(BaseModel):
    """One lot-level row nested under a hierarchy asset row."""

    lot_id: int = Field(ge=1)
    opened_on: date
    original_qty: Decimal
    remaining_qty: Decimal
    unit_cost_basis_usd: Decimal
    total_cost_basis_usd: Decimal
    market_value_usd: Decimal
    profit_loss_usd: Decimal


class PortfolioHierarchyAssetRow(BaseModel):
    """One asset row inside portfolio hierarchy groups."""

    instrument_symbol: str = Field(min_length=1)
    sector_label: str = Field(min_length=1)
    open_quantity: Decimal
    open_cost_basis_usd: Decimal
    avg_price_usd: Decimal
    current_price_usd: Decimal
    market_value_usd: Decimal
    profit_loss_usd: Decimal
    change_pct: Decimal | None = None
    lot_count: int = Field(ge=0)
    lots: list[PortfolioHierarchyLotRow]


class PortfolioHierarchyGroupRow(BaseModel):
    """One top-level hierarchy group row (sector or symbol)."""

    group_key: str = Field(min_length=1)
    group_label: str = Field(min_length=1)
    asset_count: int = Field(ge=0)
    total_market_value_usd: Decimal
    total_profit_loss_usd: Decimal
    total_change_pct: Decimal | None = None
    assets: list[PortfolioHierarchyAssetRow]


class PortfolioHierarchyResponse(BaseModel):
    """Hierarchy response payload for home workspace pivot table."""

    as_of_ledger_at: datetime
    group_by: PortfolioHierarchyGroupBy
    pricing_snapshot_key: str | None = None
    pricing_snapshot_captured_at: datetime | None = None
    groups: list[PortfolioHierarchyGroupRow]


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
    unit: Literal["percent", "ratio", "unitless"] = "unitless"
    interpretation_band: Literal["favorable", "caution", "elevated_risk"] = "caution"
    timeline_series_id: str | None = None
    health_contribution_direction: Literal["supporting", "neutral", "penalizing"] = "neutral"
    health_contribution_severity: Literal["low", "moderate", "high"] = "moderate"


class PortfolioRiskTimelineContext(BaseModel):
    """Timeline linkage metadata for risk-estimator interpretation contracts."""

    available: bool
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod


class PortfolioRiskRenderGuardrails(BaseModel):
    """Mixed-unit rendering guardrails for risk interpretation views."""

    mixed_units: bool
    unit_groups: list[str] = Field(default_factory=list)
    guidance: str = Field(min_length=1)


class PortfolioRiskEstimatorsResponse(BaseModel):
    """Risk-estimators response payload for portfolio analytics routes."""

    as_of_ledger_at: datetime
    window_days: int = Field(ge=1)
    metrics: list[PortfolioRiskEstimatorMetric]
    timeline_context: PortfolioRiskTimelineContext | None = None
    guardrails: PortfolioRiskRenderGuardrails | None = None


class PortfolioRiskEvolutionMethodology(BaseModel):
    """Methodology metadata for charted risk-evolution datasets."""

    drawdown_method: str = Field(min_length=1)
    rolling_volatility_method: str = Field(min_length=1)
    rolling_beta_method: str = Field(min_length=1)


class PortfolioRiskDrawdownPoint(BaseModel):
    """One drawdown-path point for risk evolution rendering."""

    captured_at: datetime
    drawdown: Decimal


class PortfolioRiskRollingPoint(BaseModel):
    """One rolling-estimator point for risk evolution rendering."""

    captured_at: datetime
    volatility_annualized: Decimal | None = None
    beta: Decimal | None = None


class PortfolioRiskEvolutionResponse(BaseModel):
    """Risk-evolution response payload for timeline chart modules."""

    as_of_ledger_at: datetime
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod
    rolling_window_days: int = Field(ge=2)
    methodology: PortfolioRiskEvolutionMethodology
    drawdown_path_points: list[PortfolioRiskDrawdownPoint]
    rolling_points: list[PortfolioRiskRollingPoint]


class PortfolioReturnDistributionBucketPolicy(BaseModel):
    """Bucket policy metadata used for deterministic return histograms."""

    method: Literal["equal_width"]
    bin_count: int = Field(ge=2)
    min_return: Decimal
    max_return: Decimal


class PortfolioReturnDistributionBucket(BaseModel):
    """One deterministic return-distribution bucket."""

    bucket_index: int = Field(ge=0)
    lower_bound: Decimal
    upper_bound: Decimal
    count: int = Field(ge=0)
    frequency: Decimal


class PortfolioReturnDistributionResponse(BaseModel):
    """Return-distribution response payload for risk interpretation modules."""

    as_of_ledger_at: datetime
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod
    sample_size: int = Field(ge=0)
    bucket_policy: PortfolioReturnDistributionBucketPolicy
    buckets: list[PortfolioReturnDistributionBucket]


class PortfolioQuantMetric(BaseModel):
    """One QuantStats-derived metric with display guidance for frontend rendering."""

    metric_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    value: Decimal
    display_as: Literal["percent", "number"]


class PortfolioQuantBenchmarkContext(BaseModel):
    """Optional benchmark-relative metric context for QuantStats responses."""

    benchmark_symbol: str | None = None
    omitted_metric_ids: list[str] = Field(default_factory=list)
    omission_reason: str | None = None


class PortfolioQuantMetricsResponse(BaseModel):
    """QuantStats metrics response payload for portfolio analytics routes."""

    as_of_ledger_at: datetime
    period: PortfolioChartPeriod
    benchmark_symbol: str | None = None
    benchmark_context: PortfolioQuantBenchmarkContext = Field(
        default_factory=PortfolioQuantBenchmarkContext
    )
    metrics: list[PortfolioQuantMetric]


class PortfolioQuantReportScope(StrEnum):
    """Supported report scope values for QuantStats tearsheet generation."""

    PORTFOLIO = "portfolio"
    INSTRUMENT_SYMBOL = "instrument_symbol"


class PortfolioEfficientFrontierMethodology(BaseModel):
    """Methodology metadata for efficient-frontier response interpretation."""

    optimization_model: str = Field(min_length=1)
    sampling_method: str = Field(min_length=1)
    annualization_basis: str = Field(min_length=1)


class PortfolioEfficientFrontierPoint(BaseModel):
    """One point along the efficient-frontier approximation curve."""

    point_id: str = Field(min_length=1)
    expected_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    is_max_sharpe: bool = False
    is_min_volatility: bool = False


class PortfolioEfficientFrontierAssetPoint(BaseModel):
    """One single-asset point shown alongside the efficient frontier."""

    instrument_symbol: str = Field(min_length=1)
    expected_return: Decimal
    volatility: Decimal


class PortfolioEfficientFrontierWeight(BaseModel):
    """One symbol weight row for selected frontier allocations."""

    instrument_symbol: str = Field(min_length=1)
    weight: Decimal


class PortfolioEfficientFrontierResponse(BaseModel):
    """Efficient-frontier response payload for Markowitz diagnostics modules."""

    as_of_ledger_at: datetime
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod
    risk_free_rate_annual: Decimal
    methodology: PortfolioEfficientFrontierMethodology
    frontier_points: list[PortfolioEfficientFrontierPoint]
    asset_points: list[PortfolioEfficientFrontierAssetPoint]
    max_sharpe_weights: list[PortfolioEfficientFrontierWeight]
    min_volatility_weights: list[PortfolioEfficientFrontierWeight]


class PortfolioQuantReportLifecycleStatus(StrEnum):
    """Lifecycle statuses exposed by quant report generation contract."""

    READY = "ready"
    EXPIRED = "expired"
    UNAVAILABLE = "unavailable"


class PortfolioQuantReportGenerateRequest(BaseModel):
    """Request payload for bounded QuantStats tearsheet generation."""

    model_config = ConfigDict(extra="forbid")

    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod = PortfolioChartPeriod.D90
    include_simulation_context: bool = False


class PortfolioMonteCarloCalibrationBasis(StrEnum):
    """Supported calibration basis values for profile-scenario threshold derivation."""

    MONTHLY = "monthly"
    ANNUAL = "annual"
    MANUAL = "manual"


class PortfolioMonteCarloProfileId(StrEnum):
    """Stable profile identifiers for scenario matrix rendering."""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    GROWTH = "growth"


class PortfolioMonteCarloSignal(StrEnum):
    """Interpretation signal labels for Monte Carlo summary and profile rows."""

    MONITOR = "monitor"
    BALANCED = "balanced"
    DOWNSIDE_CAUTION = "downside_caution"
    UPSIDE_FAVORABLE = "upside_favorable"


class PortfolioMonteCarloRequest(BaseModel):
    """Request payload for bounded Monte Carlo simulation diagnostics."""

    model_config = ConfigDict(extra="forbid")

    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod = PortfolioChartPeriod.D90
    sims: int = Field(default=1000, ge=250, le=5000)
    horizon_days: int | None = Field(default=None, ge=5, le=756)
    bust_threshold: Decimal | None = Field(default=None, ge=Decimal("-0.95"), le=Decimal("0"))
    goal_threshold: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("3"))
    seed: int | None = Field(default=None, ge=0, le=2_147_483_647)
    enable_profile_comparison: bool = True
    calibration_basis: PortfolioMonteCarloCalibrationBasis = (
        PortfolioMonteCarloCalibrationBasis.MONTHLY
    )

    @model_validator(mode="after")
    def validate_scope_and_thresholds(self) -> PortfolioMonteCarloRequest:
        """Validate explicit scope symmetry and threshold ordering."""

        if self.scope == PortfolioQuantReportScope.PORTFOLIO:
            if self.instrument_symbol is not None and self.instrument_symbol.strip():
                raise ValueError(
                    "instrument_symbol must be omitted when chart scope is 'portfolio'."
                )
        elif self.scope == PortfolioQuantReportScope.INSTRUMENT_SYMBOL:
            if self.instrument_symbol is None or not self.instrument_symbol.strip():
                raise ValueError(
                    "instrument_symbol is required when chart scope is 'instrument_symbol'."
                )

        if (
            self.bust_threshold is not None
            and self.goal_threshold is not None
            and self.bust_threshold >= self.goal_threshold
        ):
            raise ValueError("bust_threshold must be less than goal_threshold.")
        return self


class PortfolioMonteCarloSimulationParameters(BaseModel):
    """Effective simulation envelope used for one Monte Carlo execution."""

    sims: int = Field(ge=250, le=5000)
    horizon_days: int = Field(ge=5, le=756)
    seed: int = Field(ge=0, le=2_147_483_647)
    bust_threshold: Decimal | None = None
    goal_threshold: Decimal | None = None


class PortfolioMonteCarloAssumptions(BaseModel):
    """Interpretation assumptions for Monte Carlo diagnostics."""

    model: Literal["quantstats_shuffled_returns"]
    notes: list[str] = Field(default_factory=list)


class PortfolioMonteCarloSummary(BaseModel):
    """Simulation summary outputs for chart cards and diagnostics."""

    start_value_usd: Decimal
    median_ending_value_usd: Decimal
    mean_ending_return: Decimal
    bust_probability: Decimal | None = None
    goal_probability: Decimal | None = None
    interpretation_signal: PortfolioMonteCarloSignal = PortfolioMonteCarloSignal.MONITOR


class PortfolioMonteCarloPercentilePoint(BaseModel):
    """One percentile output point for simulation ending-return distributions."""

    percentile: int = Field(ge=0, le=100)
    value: Decimal


class PortfolioMonteCarloProfileScenario(BaseModel):
    """One profile row in the Monte Carlo side-by-side comparison matrix."""

    profile_id: PortfolioMonteCarloProfileId
    label: str = Field(min_length=1)
    bust_threshold: Decimal
    goal_threshold: Decimal
    bust_probability: Decimal | None = None
    goal_probability: Decimal | None = None
    interpretation_signal: PortfolioMonteCarloSignal = PortfolioMonteCarloSignal.MONITOR


class PortfolioMonteCarloCalibrationContext(BaseModel):
    """Calibration metadata for deterministic profile-threshold derivation."""

    requested_basis: PortfolioMonteCarloCalibrationBasis
    effective_basis: PortfolioMonteCarloCalibrationBasis
    sample_size: int = Field(ge=0)
    lookback_start: datetime | None = None
    lookback_end: datetime | None = None
    used_fallback: bool = False
    fallback_reason: str | None = None


class PortfolioSimulationContextStatus(StrEnum):
    """Simulation context lifecycle statuses for quant-report contracts."""

    READY = "ready"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


def _default_profile_scenarios() -> list[PortfolioMonteCarloProfileScenario]:
    """Return default empty profile scenario collection for response schema."""

    return []


class PortfolioMonteCarloResponse(BaseModel):
    """Monte Carlo simulation response payload with explicit assumptions metadata."""

    as_of_ledger_at: datetime
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod
    simulation: PortfolioMonteCarloSimulationParameters
    assumptions: PortfolioMonteCarloAssumptions
    summary: PortfolioMonteCarloSummary
    ending_return_percentiles: list[PortfolioMonteCarloPercentilePoint]
    profile_comparison_enabled: bool = True
    calibration_context: PortfolioMonteCarloCalibrationContext
    profile_scenarios: list[PortfolioMonteCarloProfileScenario] = Field(
        default_factory=_default_profile_scenarios
    )


class PortfolioHealthProfilePosture(StrEnum):
    """Supported profile postures for deterministic health-weighting policy."""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class PortfolioHealthLabel(StrEnum):
    """Aggregate portfolio-health interpretation labels."""

    HEALTHY = "healthy"
    WATCHLIST = "watchlist"
    STRESSED = "stressed"


class PortfolioHealthPillarStatus(StrEnum):
    """Status bands for one health pillar score."""

    FAVORABLE = "favorable"
    CAUTION = "caution"
    ELEVATED_RISK = "elevated_risk"


class PortfolioHealthDriver(BaseModel):
    """One deterministic driver row used in health interpretation summaries."""

    metric_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    direction: Literal["supporting", "penalizing"]
    impact_points: int = Field(ge=0, le=100)
    rationale: str = Field(min_length=1)
    value_display: str = Field(min_length=1)


class PortfolioHealthPillarMetric(BaseModel):
    """One metric included inside one health pillar summary."""

    metric_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value_display: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    contribution: Literal["supporting", "neutral", "penalizing"]


class PortfolioHealthPillar(BaseModel):
    """One health pillar with deterministic score and supporting metric context."""

    pillar_id: Literal["growth", "risk", "risk_adjusted_quality", "resilience"]
    label: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    status: PortfolioHealthPillarStatus
    metrics: list[PortfolioHealthPillarMetric] = Field(
        default_factory=list[PortfolioHealthPillarMetric]
    )


class PortfolioHealthSynthesisResponse(BaseModel):
    """Deterministic portfolio-health synthesis payload for executive interpretation."""

    as_of_ledger_at: datetime
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod
    profile_posture: PortfolioHealthProfilePosture
    health_score: int = Field(ge=0, le=100)
    health_label: PortfolioHealthLabel
    threshold_policy_version: str = Field(min_length=1)
    pillars: list[PortfolioHealthPillar]
    key_drivers: list[PortfolioHealthDriver] = Field(default_factory=list[PortfolioHealthDriver])
    health_caveats: list[str] = Field(default_factory=list)
    core_metric_ids: list[str] = Field(default_factory=list)
    advanced_metric_ids: list[str] = Field(default_factory=list)


class PortfolioQuantReportGenerateResponse(BaseModel):
    """Report-generation metadata response with deterministic retrieval contract."""

    report_id: str = Field(min_length=1)
    report_url_path: str = Field(min_length=1)
    lifecycle_status: PortfolioQuantReportLifecycleStatus
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None = None
    period: PortfolioChartPeriod
    benchmark_symbol: str | None = None
    generated_at: datetime
    expires_at: datetime
    simulation_context_status: PortfolioSimulationContextStatus = (
        PortfolioSimulationContextStatus.UNAVAILABLE
    )
    simulation_context_reason: str | None = None
    health_summary: PortfolioHealthSynthesisResponse | None = None
