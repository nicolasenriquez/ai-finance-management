"""Service helpers for read-only portfolio analytics from ledger truth."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from importlib import import_module
from itertools import pairwise
from pathlib import Path
from types import ModuleType
from typing import Literal, cast

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.market_data.models import PriceHistory
from app.market_data.service import (
    MarketDataClientError,
    resolve_latest_consistent_snapshot_coverage_for_symbols,
)
from app.portfolio_analytics.schemas import (
    PortfolioAnnualizationBasis,
    PortfolioChartPeriod,
    PortfolioCommandCenterInsight,
    PortfolioCommandCenterResponse,
    PortfolioContributionResponse,
    PortfolioContributionRow,
    PortfolioContributionToRiskMethodology,
    PortfolioContributionToRiskResponse,
    PortfolioContributionToRiskRow,
    PortfolioCorrelationMatrixRow,
    PortfolioCorrelationResponse,
    PortfolioDecisionFreshnessPolicy,
    PortfolioDecisionState,
    PortfolioEfficientFrontierAssetPoint,
    PortfolioEfficientFrontierMethodology,
    PortfolioEfficientFrontierPoint,
    PortfolioEfficientFrontierResponse,
    PortfolioEfficientFrontierWeight,
    PortfolioExposureResponse,
    PortfolioExposureRow,
    PortfolioHealthDriver,
    PortfolioHealthLabel,
    PortfolioHealthPillar,
    PortfolioHealthPillarMetric,
    PortfolioHealthPillarStatus,
    PortfolioHealthProfilePosture,
    PortfolioHealthSynthesisResponse,
    PortfolioHierarchyAssetRow,
    PortfolioHierarchyGroupBy,
    PortfolioHierarchyGroupRow,
    PortfolioHierarchyLotRow,
    PortfolioHierarchyResponse,
    PortfolioLotDetailResponse,
    PortfolioLotDetailRow,
    PortfolioMonteCarloAssumptions,
    PortfolioMonteCarloCalibrationBasis,
    PortfolioMonteCarloCalibrationContext,
    PortfolioMonteCarloPercentilePoint,
    PortfolioMonteCarloProfileId,
    PortfolioMonteCarloProfileScenario,
    PortfolioMonteCarloRequest,
    PortfolioMonteCarloResponse,
    PortfolioMonteCarloSignal,
    PortfolioMonteCarloSimulationParameters,
    PortfolioMonteCarloSummary,
    PortfolioQuantBenchmarkContext,
    PortfolioQuantMetric,
    PortfolioQuantMetricsResponse,
    PortfolioQuantReportGenerateRequest,
    PortfolioQuantReportGenerateResponse,
    PortfolioQuantReportLifecycleStatus,
    PortfolioQuantReportScope,
    PortfolioReturnDistributionBucket,
    PortfolioReturnDistributionBucketPolicy,
    PortfolioReturnDistributionResponse,
    PortfolioRiskDrawdownPoint,
    PortfolioRiskEstimatorMetric,
    PortfolioRiskEstimatorsResponse,
    PortfolioRiskEvolutionMethodology,
    PortfolioRiskEvolutionResponse,
    PortfolioRiskRenderGuardrails,
    PortfolioRiskRollingPoint,
    PortfolioRiskTimelineContext,
    PortfolioSimulationContextStatus,
    PortfolioSummaryResponse,
    PortfolioSummaryRow,
    PortfolioTimeSeriesPoint,
    PortfolioTimeSeriesResponse,
    PortfolioTransactionEvent,
    PortfolioTransactionsResponse,
)
from app.portfolio_ledger.models import (
    DividendEvent,
    Lot,
    LotDisposition,
    PortfolioTransaction,
)
from app.shared.models import utcnow

logger = get_logger(__name__)
settings = get_settings()

_QTY_SCALE = Decimal("0.000000001")
_MONEY_SCALE = Decimal("0.01")
_PCT_SCALE = Decimal("0.01")
_RATIO_SCALE = Decimal("0.000001")
_PERIOD_TO_REQUIRED_POINTS: dict[PortfolioChartPeriod, int | None] = {
    PortfolioChartPeriod.D30: 30,
    PortfolioChartPeriod.D90: 90,
    PortfolioChartPeriod.D6M: 126,
    PortfolioChartPeriod.D252: 252,
    PortfolioChartPeriod.YTD: None,
    PortfolioChartPeriod.MAX: None,
}
_SUPPORTED_RISK_WINDOWS: set[int] = {30, 90, 126, 252}
_DEFAULT_ROLLING_WINDOW_BY_PERIOD: dict[PortfolioChartPeriod, int] = {
    PortfolioChartPeriod.D30: 10,
    PortfolioChartPeriod.D90: 30,
    PortfolioChartPeriod.D6M: 30,
    PortfolioChartPeriod.D252: 30,
    PortfolioChartPeriod.YTD: 30,
    PortfolioChartPeriod.MAX: 30,
}
_DEFAULT_MONTE_CARLO_HORIZON_BY_PERIOD: dict[PortfolioChartPeriod, int] = {
    PortfolioChartPeriod.D30: 20,
    PortfolioChartPeriod.D90: 60,
    PortfolioChartPeriod.D6M: 84,
    PortfolioChartPeriod.D252: 126,
    PortfolioChartPeriod.YTD: 60,
    PortfolioChartPeriod.MAX: 252,
}
_MIN_MONTE_CARLO_HORIZON_DAYS = 5
_MONTE_CARLO_DEFAULT_SEED = 20260330
_MONTE_CARLO_MONTHLY_CALIBRATION_MIN_SAMPLE = 24
_MONTE_CARLO_ANNUAL_CALIBRATION_MIN_SAMPLE = 5
_EFFICIENT_FRONTIER_DEFAULT_POINTS = 24
_EFFICIENT_FRONTIER_MIN_POINTS = 8
_EFFICIENT_FRONTIER_MAX_POINTS = 60
_EFFICIENT_FRONTIER_MIN_SAMPLE_COUNT = 3000
_EFFICIENT_FRONTIER_POINT_SAMPLE_MULTIPLIER = 280
_EFFICIENT_FRONTIER_RANDOM_SEED = 20260405
_EFFICIENT_FRONTIER_RISK_FREE_RATE_ANNUAL = Decimal("0.03")
_SUPPORTED_CHART_PERIOD_VALUES: tuple[str, ...] = tuple(
    period.value for period in PortfolioChartPeriod
)
_SUPPORTED_CHART_SCOPE_VALUES: tuple[str, ...] = tuple(
    scope.value for scope in PortfolioQuantReportScope
)
_OPTIONAL_BENCHMARK_CANDIDATE_SYMBOLS: tuple[str, ...] = (
    "VOO",
    "SPY",
    "IVV",
    "QQQM",
    "QQQ",
)
_BENCHMARK_CANDIDATE_SYMBOLS_BY_ID: dict[str, tuple[str, ...]] = {
    "benchmark_sp500_value_usd": ("VOO", "SPY", "IVV"),
    "benchmark_nasdaq100_value_usd": ("QQQM", "QQQ"),
}
_BENCHMARK_LABEL_BY_FIELD: dict[str, str] = {
    "benchmark_sp500_value_usd": "SP500_PROXY",
    "benchmark_nasdaq100_value_usd": "NASDAQ100_PROXY",
}
_QUANT_REPORT_RETENTION = timedelta(minutes=settings.quant_report_retention_minutes)
_MONTE_CARLO_PROFILE_LABELS: dict[PortfolioMonteCarloProfileId, str] = {
    PortfolioMonteCarloProfileId.CONSERVATIVE: "Conservative",
    PortfolioMonteCarloProfileId.BALANCED: "Balanced",
    PortfolioMonteCarloProfileId.GROWTH: "Growth",
}
_MONTE_CARLO_FALLBACK_PROFILE_THRESHOLDS: dict[
    PortfolioMonteCarloProfileId, tuple[Decimal, Decimal]
] = {
    PortfolioMonteCarloProfileId.CONSERVATIVE: (
        Decimal("-0.10"),
        Decimal("0.12"),
    ),
    PortfolioMonteCarloProfileId.BALANCED: (
        Decimal("-0.20"),
        Decimal("0.27"),
    ),
    PortfolioMonteCarloProfileId.GROWTH: (
        Decimal("-0.30"),
        Decimal("0.45"),
    ),
}
_HEALTH_POLICY_VERSION = "health_v1_20260330"
_HEALTH_PROFILE_WEIGHTS: dict[
    PortfolioHealthProfilePosture, tuple[Decimal, Decimal, Decimal, Decimal]
] = {
    PortfolioHealthProfilePosture.CONSERVATIVE: (
        Decimal("0.20"),
        Decimal("0.40"),
        Decimal("0.25"),
        Decimal("0.15"),
    ),
    PortfolioHealthProfilePosture.BALANCED: (
        Decimal("0.30"),
        Decimal("0.30"),
        Decimal("0.25"),
        Decimal("0.15"),
    ),
    PortfolioHealthProfilePosture.AGGRESSIVE: (
        Decimal("0.35"),
        Decimal("0.20"),
        Decimal("0.30"),
        Decimal("0.15"),
    ),
}
_HEALTH_CORE_METRIC_IDS: tuple[str, ...] = (
    "cagr",
    "cumulative_return",
    "sharpe_ratio",
    "sortino_ratio",
    "calmar_ratio",
    "volatility_annualized",
    "max_drawdown",
    "expected_shortfall_95",
    "recovery_factor",
    "win_month",
)
_HEALTH_ADVANCED_METRIC_IDS: tuple[str, ...] = (
    "one_year_return",
    "three_year_annualized_return",
    "value_at_risk_95",
    "longest_drawdown_days",
)
_SECTOR_BY_SYMBOL: dict[str, str] = {
    "AAPL": "Technology",
    "AMD": "Technology",
    "APLD": "Technology",
    "BBAI": "Technology",
    "BRK.B": "Financials",
    "GLD": "Commodities",
    "GOOGL": "Communication Services",
    "HOOD": "Financials",
    "META": "Communication Services",
    "NVDA": "Technology",
    "PLTR": "Technology",
    "QQQM": "ETF",
    "SCHD": "ETF",
    "SCHG": "ETF",
    "SMH": "ETF",
    "SOFI": "Financials",
    "SPMO": "ETF",
    "TSLA": "Consumer Cyclical",
    "UUUU": "Energy",
    "VOO": "ETF",
}
_DECISION_FRESHNESS_HOURS = 24
_CORRELATION_MAX_SYMBOLS = 12


@dataclass(frozen=True)
class _QuantReportArtifact:
    """One generated QuantStats report artifact with lifecycle metadata."""

    report_id: str
    scope: PortfolioQuantReportScope
    instrument_symbol: str | None
    period: PortfolioChartPeriod
    benchmark_symbol: str | None
    generated_at: datetime
    expires_at: datetime
    output_path: Path


@dataclass(frozen=True)
class _ScopedValueSeriesResult:
    """Deterministic scope-selected value/return series bundle for analytics contracts."""

    scope: PortfolioQuantReportScope
    instrument_symbol: str | None
    aligned_timestamps: list[datetime]
    value_series: pd.Series
    returns_series: pd.Series
    candidate_price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]]


@dataclass(frozen=True)
class _HealthMetricEvaluation:
    """Deterministic metric evaluation used by portfolio-health synthesis logic."""

    metric_id: str
    label: str
    raw_value: float
    score: int
    value_display: str
    contribution: Literal["supporting", "neutral", "penalizing"]
    rationale: str


_QUANT_REPORT_ARTIFACTS_BY_ID: dict[str, _QuantReportArtifact] = {}


class PortfolioAnalyticsClientError(ValueError):
    """Raised when analytics requests are invalid or unsafe to process."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize a client-facing analytics error."""

        super().__init__(message)
        self.status_code = status_code


def normalize_chart_period(*, period_value: object) -> PortfolioChartPeriod:
    """Normalize one chart period input into the approved v1 enum values."""

    if isinstance(period_value, PortfolioChartPeriod):
        return period_value

    if not isinstance(period_value, str):
        raise PortfolioAnalyticsClientError(
            "Unsupported chart period value. "
            f"Supported periods are: {', '.join(_SUPPORTED_CHART_PERIOD_VALUES)}.",
            status_code=422,
        )

    normalized_period_value = period_value.strip().upper()
    for period in PortfolioChartPeriod:
        if normalized_period_value == period.value:
            return period

    raise PortfolioAnalyticsClientError(
        "Unsupported chart period value. "
        f"Supported periods are: {', '.join(_SUPPORTED_CHART_PERIOD_VALUES)}.",
        status_code=422,
    )


def _resolve_period_minimum_timestamp(*, period: PortfolioChartPeriod) -> datetime | None:
    """Return optional period floor timestamp used for aligned-series selection."""

    if period != PortfolioChartPeriod.YTD:
        return None
    now_utc = utcnow()
    return datetime(year=now_utc.year, month=1, day=1, tzinfo=UTC)


def normalize_chart_scope(
    *,
    scope_value: object,
    instrument_symbol_value: object,
) -> tuple[PortfolioQuantReportScope, str | None]:
    """Normalize one chart scope request into supported scope/symbol values."""

    normalized_scope: PortfolioQuantReportScope
    if isinstance(scope_value, PortfolioQuantReportScope):
        normalized_scope = scope_value
    elif isinstance(scope_value, str):
        normalized_scope_text = scope_value.strip().lower()
        matched_scope: PortfolioQuantReportScope | None = next(
            (scope for scope in PortfolioQuantReportScope if normalized_scope_text == scope.value),
            None,
        )
        if matched_scope is None:
            raise PortfolioAnalyticsClientError(
                "Unsupported chart scope value. "
                f"Supported scopes are: {', '.join(_SUPPORTED_CHART_SCOPE_VALUES)}.",
                status_code=422,
            )
        normalized_scope = matched_scope
    else:
        raise PortfolioAnalyticsClientError(
            "Unsupported chart scope value. "
            f"Supported scopes are: {', '.join(_SUPPORTED_CHART_SCOPE_VALUES)}.",
            status_code=422,
        )

    if normalized_scope == PortfolioQuantReportScope.PORTFOLIO:
        if isinstance(instrument_symbol_value, str) and instrument_symbol_value.strip():
            raise PortfolioAnalyticsClientError(
                "instrument_symbol must be omitted when chart scope is 'portfolio'.",
                status_code=422,
            )
        return normalized_scope, None

    if (
        instrument_symbol_value is None
        or not isinstance(instrument_symbol_value, str)
        or not instrument_symbol_value.strip()
    ):
        raise PortfolioAnalyticsClientError(
            "instrument_symbol is required when chart scope is 'instrument_symbol'.",
            status_code=422,
        )

    normalized_instrument_symbol = _normalize_symbol(
        symbol_value=instrument_symbol_value,
        field="instrument_symbol",
    )
    return normalized_scope, normalized_instrument_symbol


async def get_portfolio_summary_response(*, db: AsyncSession) -> PortfolioSummaryResponse:
    """Return grouped portfolio summary computed from persisted ledger truth."""

    logger.info("portfolio_analytics.summary_started")
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            lots_result = await db.execute(select(Lot))
            lot_dispositions_result = await db.execute(select(LotDisposition))
            sell_transactions_result = await db.execute(
                select(PortfolioTransaction).where(
                    func.lower(PortfolioTransaction.trade_side) == "sell",
                )
            )
            dividend_events_result = await db.execute(select(DividendEvent))

            serialized_lots = [_serialize_lot_row(row) for row in lots_result.scalars().all()]
            serialized_lot_dispositions = [
                _serialize_lot_disposition_row(row)
                for row in lot_dispositions_result.scalars().all()
            ]
            serialized_sell_transactions = [
                _serialize_portfolio_transaction_row(row)
                for row in sell_transactions_result.scalars().all()
            ]
            serialized_dividends = [
                _serialize_dividend_event_row(row) for row in dividend_events_result.scalars().all()
            ]

            open_position_symbols = collect_open_position_symbols_from_lots(lots=serialized_lots)
            latest_close_price_usd_by_symbol: dict[str, Decimal] = {}
            pricing_snapshot_key: str | None = None
            pricing_snapshot_captured_at: datetime | None = None
            if open_position_symbols:
                snapshot_coverage = await resolve_latest_consistent_snapshot_coverage_for_symbols(
                    db=db,
                    required_symbols=open_position_symbols,
                )
                if snapshot_coverage is None:
                    missing_symbols_csv = ", ".join(sorted(open_position_symbols))
                    raise PortfolioAnalyticsClientError(
                        "No consistent persisted market-data snapshot provides complete USD "
                        "pricing coverage for open position symbol(s): "
                        f"{missing_symbols_csv}.",
                        status_code=409,
                    )

                validate_open_position_price_coverage(
                    open_position_symbols=open_position_symbols,
                    priced_symbols=set(snapshot_coverage.latest_close_price_usd_by_symbol),
                    snapshot_key=snapshot_coverage.snapshot_key,
                )
                latest_close_price_usd_by_symbol = (
                    snapshot_coverage.latest_close_price_usd_by_symbol
                )
                pricing_snapshot_key = snapshot_coverage.snapshot_key
                pricing_snapshot_captured_at = snapshot_coverage.snapshot_captured_at

            rows_payload = build_grouped_portfolio_summary_from_ledger(
                lots=serialized_lots,
                lot_dispositions=serialized_lot_dispositions,
                portfolio_transactions=serialized_sell_transactions,
                dividend_events=serialized_dividends,
                latest_close_price_usd_by_symbol=latest_close_price_usd_by_symbol,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            summary_response = PortfolioSummaryResponse(
                as_of_ledger_at=as_of_ledger_at,
                pricing_snapshot_key=pricing_snapshot_key,
                pricing_snapshot_captured_at=pricing_snapshot_captured_at,
                rows=[
                    PortfolioSummaryRow.model_validate(row_payload) for row_payload in rows_payload
                ],
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.summary_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.summary_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build portfolio summary from ledger due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.summary_completed",
        as_of_ledger_at=summary_response.as_of_ledger_at.isoformat(),
        pricing_snapshot_key=summary_response.pricing_snapshot_key,
        row_count=len(summary_response.rows),
    )
    return summary_response


async def get_portfolio_lot_detail_response(
    *,
    instrument_symbol: str,
    db: AsyncSession,
) -> PortfolioLotDetailResponse:
    """Return lot-detail analytics for one instrument symbol from persisted ledger truth."""

    normalized_symbol = _normalize_symbol(symbol_value=instrument_symbol, field="instrument_symbol")
    logger.info("portfolio_analytics.lot_detail_started", instrument_symbol=normalized_symbol)

    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            lots_result = await db.execute(
                select(Lot).where(func.upper(Lot.instrument_symbol) == normalized_symbol),
            )
            lots = lots_result.scalars().all()
            lot_ids = [lot.id for lot in lots]

            if not lot_ids:
                logger.info(
                    "portfolio_analytics.lot_detail_rejected",
                    instrument_symbol=normalized_symbol,
                    status_code=404,
                    error="Instrument symbol not found in portfolio ledger.",
                )
                raise PortfolioAnalyticsClientError(
                    f"Instrument symbol '{normalized_symbol}' was not found in the portfolio ledger.",
                    status_code=404,
                )

            lot_dispositions_result = await db.execute(
                select(LotDisposition).where(LotDisposition.lot_id.in_(lot_ids)),
            )
            lot_dispositions = lot_dispositions_result.scalars().all()
            sell_transaction_ids = sorted(
                {disposition.sell_transaction_id for disposition in lot_dispositions}
            )
            sell_transactions: list[PortfolioTransaction] = []
            if sell_transaction_ids:
                sell_transactions_result = await db.execute(
                    select(PortfolioTransaction).where(
                        PortfolioTransaction.id.in_(sell_transaction_ids)
                    ),
                )
                sell_transactions = list(sell_transactions_result.scalars().all())

            detail_payload = build_lot_detail_from_ledger(
                instrument_symbol=normalized_symbol,
                lots=[_serialize_lot_row(row) for row in lots],
                lot_dispositions=[_serialize_lot_disposition_row(row) for row in lot_dispositions],
                portfolio_transactions=[
                    _serialize_portfolio_transaction_row(row) for row in sell_transactions
                ],
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            lot_detail_response = PortfolioLotDetailResponse(
                as_of_ledger_at=as_of_ledger_at,
                instrument_symbol=cast(str, detail_payload["instrument_symbol"]),
                lots=[
                    PortfolioLotDetailRow.model_validate(lot_payload)
                    for lot_payload in cast(list[dict[str, object]], detail_payload["lots"])
                ],
            )
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.lot_detail_failed",
            instrument_symbol=normalized_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build lot detail from ledger due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.lot_detail_completed",
        instrument_symbol=lot_detail_response.instrument_symbol,
        as_of_ledger_at=lot_detail_response.as_of_ledger_at.isoformat(),
        lot_count=len(lot_detail_response.lots),
    )
    return lot_detail_response


async def get_portfolio_time_series_response(
    *,
    db: AsyncSession,
    period: PortfolioChartPeriod,
    scope: PortfolioQuantReportScope = PortfolioQuantReportScope.PORTFOLIO,
    instrument_symbol: str | None = None,
) -> PortfolioTimeSeriesResponse:
    """Return chart-ready portfolio time-series for one supported period."""

    normalized_scope, normalized_instrument_symbol = normalize_chart_scope(
        scope_value=scope,
        instrument_symbol_value=instrument_symbol,
    )
    logger.info(
        "portfolio_analytics.time_series_started",
        period=period.value,
        scope=normalized_scope.value,
        instrument_symbol=normalized_instrument_symbol,
    )
    required_points = _PERIOD_TO_REQUIRED_POINTS[period]
    minimum_timestamp = _resolve_period_minimum_timestamp(period=period)
    insufficient_history_detail = (
        f"Insufficient persisted history for requested period {period.value}."
    )
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(
                db=db,
                instrument_symbol=normalized_instrument_symbol,
            )

            aligned_timestamps = _select_aligned_timestamps(
                price_series_by_symbol=price_series_by_symbol,
                required_points=required_points,
                minimum_points=1,
                minimum_timestamp=minimum_timestamp,
                insufficient_history_detail=insufficient_history_detail,
            )
            points_payload = build_portfolio_time_series_points(
                aligned_timestamps=aligned_timestamps,
                open_quantity_by_symbol=open_quantity_by_symbol,
                price_series_by_symbol=price_series_by_symbol,
                total_open_cost_basis_usd=total_open_cost_basis_usd,
                benchmark_price_series_by_id=_resolve_benchmark_price_series_by_id(
                    aligned_timestamps=aligned_timestamps,
                    candidate_price_series_by_symbol={
                        **optional_price_series_by_symbol,
                        **price_series_by_symbol,
                    },
                ),
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioTimeSeriesResponse(
                as_of_ledger_at=as_of_ledger_at,
                period=period,
                frequency="1D",
                timezone="UTC",
                points=[
                    PortfolioTimeSeriesPoint.model_validate(point_payload)
                    for point_payload in points_payload
                ],
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.time_series_failed",
            period=period.value,
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.time_series_failed",
            period=period.value,
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build portfolio time-series due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.time_series_completed",
        period=response.period.value,
        scope=normalized_scope.value,
        instrument_symbol=normalized_instrument_symbol,
        point_count=len(response.points),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def get_portfolio_contribution_response(
    *,
    db: AsyncSession,
    period: PortfolioChartPeriod,
) -> PortfolioContributionResponse:
    """Return per-symbol contribution aggregates for one supported period."""

    logger.info(
        "portfolio_analytics.contribution_started",
        period=period.value,
    )
    required_points = _PERIOD_TO_REQUIRED_POINTS[period]
    minimum_timestamp = _resolve_period_minimum_timestamp(period=period)
    insufficient_history_detail = (
        f"Insufficient persisted history for contribution period {period.value}."
    )
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                _optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)

            aligned_timestamps = _select_aligned_timestamps(
                price_series_by_symbol=price_series_by_symbol,
                required_points=required_points,
                minimum_points=2,
                minimum_timestamp=minimum_timestamp,
                insufficient_history_detail=insufficient_history_detail,
            )
            contribution_rows_payload = build_portfolio_contribution_rows(
                aligned_timestamps=aligned_timestamps,
                open_quantity_by_symbol=open_quantity_by_symbol,
                price_series_by_symbol=price_series_by_symbol,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioContributionResponse(
                as_of_ledger_at=as_of_ledger_at,
                period=period,
                rows=[
                    PortfolioContributionRow.model_validate(row_payload)
                    for row_payload in contribution_rows_payload
                ],
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.contribution_failed",
            period=period.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.contribution_failed",
            period=period.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build portfolio contribution due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.contribution_completed",
        period=response.period.value,
        row_count=len(response.rows),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def get_portfolio_risk_estimators_response(
    *,
    db: AsyncSession,
    window_days: int,
    scope: PortfolioQuantReportScope = PortfolioQuantReportScope.PORTFOLIO,
    instrument_symbol: str | None = None,
    period: PortfolioChartPeriod = PortfolioChartPeriod.D252,
) -> PortfolioRiskEstimatorsResponse:
    """Return bounded v1 risk estimators with explicit methodology metadata."""

    if window_days not in _SUPPORTED_RISK_WINDOWS:
        supported_windows_csv = ", ".join(str(window) for window in sorted(_SUPPORTED_RISK_WINDOWS))
        raise PortfolioAnalyticsClientError(
            "Unsupported risk window value. " f"Supported windows are: {supported_windows_csv}.",
            status_code=422,
        )

    logger.info(
        "portfolio_analytics.risk_estimators_started",
        window_days=window_days,
        scope=scope.value,
        instrument_symbol=instrument_symbol,
    )
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)
            candidate_price_series_by_symbol: dict[str, Mapping[datetime, Decimal]] = {
                **optional_price_series_by_symbol,
                **price_series_by_symbol,
            }
            insufficient_history_detail = (
                f"Insufficient persisted history for risk window {window_days}."
            )
            proxy_returns_override: pd.Series | None = None
            if scope == PortfolioQuantReportScope.PORTFOLIO:
                aligned_timestamps = _select_aligned_timestamps(
                    price_series_by_symbol=price_series_by_symbol,
                    required_points=window_days + 1,
                    minimum_points=window_days + 1,
                    insufficient_history_detail=insufficient_history_detail,
                )
                price_frame = _build_aligned_price_frame(
                    aligned_timestamps=aligned_timestamps,
                    price_series_by_symbol=price_series_by_symbol,
                )
                risk_quantity_by_symbol = open_quantity_by_symbol
            else:
                if instrument_symbol is None:
                    raise PortfolioAnalyticsClientError(
                        "instrument_symbol is required when chart scope is 'instrument_symbol'.",
                        status_code=422,
                    )
                scoped_series = candidate_price_series_by_symbol.get(instrument_symbol)
                if scoped_series is None:
                    raise PortfolioAnalyticsClientError(
                        "No persisted market-data history is available for requested risk symbol "
                        f"'{instrument_symbol}'.",
                        status_code=409,
                    )
                aligned_timestamps = _select_aligned_timestamps(
                    price_series_by_symbol={instrument_symbol: scoped_series},
                    required_points=window_days + 1,
                    minimum_points=window_days + 1,
                    insufficient_history_detail=insufficient_history_detail,
                )
                price_frame = _build_aligned_price_frame(
                    aligned_timestamps=aligned_timestamps,
                    price_series_by_symbol={instrument_symbol: scoped_series},
                )
                risk_quantity_by_symbol = {instrument_symbol: Decimal("1")}
                _benchmark_symbol, benchmark_returns = _select_quantstats_benchmark_returns(
                    aligned_timestamps=aligned_timestamps,
                    benchmark_price_series_by_id=_resolve_benchmark_price_series_by_id(
                        aligned_timestamps=aligned_timestamps,
                        candidate_price_series_by_symbol=candidate_price_series_by_symbol,
                    ),
                )
                if benchmark_returns is None:
                    raise PortfolioAnalyticsClientError(
                        "No compatible benchmark return series is available for instrument-scoped "
                        "beta estimation.",
                        status_code=409,
                    )
                proxy_returns_override = benchmark_returns
            computed_metrics = _compute_risk_metrics_from_price_frame(
                price_frame=price_frame,
                open_quantity_by_symbol=risk_quantity_by_symbol,
                window_days=window_days,
                proxy_returns_override=proxy_returns_override,
            )

            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            latest_timestamp = price_frame.index[-1].to_pydatetime(warn=False)
            if latest_timestamp.tzinfo is None:
                latest_timestamp = latest_timestamp.replace(tzinfo=UTC)
            else:
                latest_timestamp = latest_timestamp.astimezone(UTC)
            annualization_basis = PortfolioAnnualizationBasis(
                kind="trading_days",
                value=252,
            )
            raw_metrics = [
                PortfolioRiskEstimatorMetric(
                    estimator_id="volatility_annualized",
                    value=_quantize_ratio(computed_metrics["volatility_annualized"]),
                    window_days=window_days,
                    return_basis="simple",
                    annualization_basis=annualization_basis,
                    as_of_timestamp=latest_timestamp,
                ),
                PortfolioRiskEstimatorMetric(
                    estimator_id="max_drawdown",
                    value=_quantize_ratio(computed_metrics["max_drawdown"]),
                    window_days=window_days,
                    return_basis="simple",
                    annualization_basis=annualization_basis,
                    as_of_timestamp=latest_timestamp,
                ),
                PortfolioRiskEstimatorMetric(
                    estimator_id="beta",
                    value=_quantize_ratio(computed_metrics["beta"]),
                    window_days=window_days,
                    return_basis="simple",
                    annualization_basis=annualization_basis,
                    as_of_timestamp=latest_timestamp,
                ),
                PortfolioRiskEstimatorMetric(
                    estimator_id="downside_deviation_annualized",
                    value=_quantize_ratio(computed_metrics["downside_deviation_annualized"]),
                    window_days=window_days,
                    return_basis="simple",
                    annualization_basis=annualization_basis,
                    as_of_timestamp=latest_timestamp,
                ),
                PortfolioRiskEstimatorMetric(
                    estimator_id="value_at_risk_95",
                    value=_quantize_ratio(computed_metrics["value_at_risk_95"]),
                    window_days=window_days,
                    return_basis="simple",
                    annualization_basis=annualization_basis,
                    as_of_timestamp=latest_timestamp,
                ),
                PortfolioRiskEstimatorMetric(
                    estimator_id="expected_shortfall_95",
                    value=_quantize_ratio(computed_metrics["expected_shortfall_95"]),
                    window_days=window_days,
                    return_basis="simple",
                    annualization_basis=annualization_basis,
                    as_of_timestamp=latest_timestamp,
                ),
            ]
            metrics: list[PortfolioRiskEstimatorMetric] = []
            for metric in raw_metrics:
                interpretation_band = _resolve_risk_interpretation_band(
                    estimator_id=metric.estimator_id,
                    value=metric.value,
                )
                (
                    health_contribution_direction,
                    health_contribution_severity,
                ) = _resolve_risk_band_health_contribution(interpretation_band=interpretation_band)
                metrics.append(
                    metric.model_copy(
                        update={
                            "unit": _resolve_risk_metric_unit(estimator_id=metric.estimator_id),
                            "interpretation_band": interpretation_band,
                            "timeline_series_id": metric.estimator_id,
                            "health_contribution_direction": health_contribution_direction,
                            "health_contribution_severity": health_contribution_severity,
                        }
                    )
                )
            unit_groups: list[str] = sorted({str(metric.unit) for metric in metrics})
            mixed_units = len(unit_groups) > 1
            response = PortfolioRiskEstimatorsResponse(
                as_of_ledger_at=as_of_ledger_at,
                window_days=window_days,
                metrics=metrics,
                timeline_context=PortfolioRiskTimelineContext(
                    available=True,
                    scope=scope,
                    instrument_symbol=instrument_symbol,
                    period=period,
                ),
                guardrails=PortfolioRiskRenderGuardrails(
                    mixed_units=mixed_units,
                    unit_groups=unit_groups,
                    guidance=(
                        "Estimator units are mixed; render percent and ratio estimators in "
                        "separate groups to avoid invalid one-axis comparisons."
                        if mixed_units
                        else "Estimator units are comparable for shared-axis interpretation."
                    ),
                ),
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.risk_estimators_failed",
            window_days=window_days,
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.risk_estimators_failed",
            window_days=window_days,
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build portfolio risk estimators due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.risk_estimators_completed",
        window_days=response.window_days,
        scope=scope.value,
        instrument_symbol=instrument_symbol,
        metric_count=len(response.metrics),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def get_portfolio_risk_evolution_response(
    *,
    db: AsyncSession,
    period: PortfolioChartPeriod,
    scope: PortfolioQuantReportScope,
    instrument_symbol: str | None,
) -> PortfolioRiskEvolutionResponse:
    """Return drawdown and rolling estimator timelines for risk interpretation modules."""

    logger.info(
        "portfolio_analytics.risk_evolution_started",
        period=period.value,
        scope=scope.value,
        instrument_symbol=instrument_symbol,
    )
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)
            scoped_series = _build_scope_value_series_result(
                scope=scope,
                period=period,
                instrument_symbol=instrument_symbol,
                open_quantity_by_symbol=open_quantity_by_symbol,
                price_series_by_symbol=price_series_by_symbol,
                optional_price_series_by_symbol=optional_price_series_by_symbol,
                context_label="risk evolution",
            )
            rolling_window_days = min(
                _DEFAULT_ROLLING_WINDOW_BY_PERIOD[period],
                len(scoped_series.returns_series),
            )
            rolling_window_days = max(2, rolling_window_days)
            drawdown_series = (
                scoped_series.value_series / scoped_series.value_series.cummax()
            ) - 1.0
            rolling_volatility_series = scoped_series.returns_series.rolling(
                window=rolling_window_days,
                min_periods=rolling_window_days,
            ).std(ddof=1) * np.sqrt(252.0)
            proxy_returns = _build_scope_proxy_returns_series_for_beta(
                scope=scope,
                instrument_symbol=instrument_symbol,
                aligned_timestamps=scoped_series.aligned_timestamps,
                open_price_series_by_symbol=price_series_by_symbol,
                candidate_price_series_by_symbol=scoped_series.candidate_price_series_by_symbol,
                primary_returns_series=scoped_series.returns_series,
            )
            rolling_beta_series = _build_rolling_beta_series(
                returns_series=scoped_series.returns_series,
                proxy_returns_series=proxy_returns,
                window_days=rolling_window_days,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)

            drawdown_points: list[PortfolioRiskDrawdownPoint] = []
            for timestamp, drawdown_value in drawdown_series.items():
                drawdown_points.append(
                    PortfolioRiskDrawdownPoint(
                        captured_at=_normalize_series_timestamp_to_utc(timestamp),
                        drawdown=_quantize_ratio(
                            _decimal_from_float(
                                value=float(drawdown_value),
                                field="drawdown_path",
                            )
                        ),
                    )
                )

            rolling_points: list[PortfolioRiskRollingPoint] = []
            for timestamp in scoped_series.returns_series.index:
                volatility_value = rolling_volatility_series.get(timestamp)
                beta_value = rolling_beta_series.get(timestamp)
                rolling_points.append(
                    PortfolioRiskRollingPoint(
                        captured_at=_normalize_series_timestamp_to_utc(timestamp),
                        volatility_annualized=_to_optional_quantized_ratio(
                            value=volatility_value,
                            field="rolling_volatility_annualized",
                        ),
                        beta=_to_optional_quantized_ratio(
                            value=beta_value,
                            field="rolling_beta",
                        ),
                    )
                )

            response = PortfolioRiskEvolutionResponse(
                as_of_ledger_at=as_of_ledger_at,
                scope=scope,
                instrument_symbol=instrument_symbol,
                period=period,
                rolling_window_days=rolling_window_days,
                methodology=PortfolioRiskEvolutionMethodology(
                    drawdown_method="running_peak_relative_decline",
                    rolling_volatility_method="rolling_std_x_sqrt_252",
                    rolling_beta_method="rolling_covariance_div_variance",
                ),
                drawdown_path_points=drawdown_points,
                rolling_points=rolling_points,
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.risk_evolution_failed",
            period=period.value,
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.risk_evolution_failed",
            period=period.value,
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build risk evolution due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.risk_evolution_completed",
        period=response.period.value,
        scope=response.scope.value,
        instrument_symbol=response.instrument_symbol,
        drawdown_points=len(response.drawdown_path_points),
        rolling_points=len(response.rolling_points),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def get_portfolio_return_distribution_response(
    *,
    db: AsyncSession,
    period: PortfolioChartPeriod,
    scope: PortfolioQuantReportScope,
    instrument_symbol: str | None,
    bin_count: int = 12,
) -> PortfolioReturnDistributionResponse:
    """Return deterministic return-distribution buckets for chart rendering."""

    logger.info(
        "portfolio_analytics.return_distribution_started",
        period=period.value,
        scope=scope.value,
        instrument_symbol=instrument_symbol,
        bin_count=bin_count,
    )
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)
            scoped_series = _build_scope_value_series_result(
                scope=scope,
                period=period,
                instrument_symbol=instrument_symbol,
                open_quantity_by_symbol=open_quantity_by_symbol,
                price_series_by_symbol=price_series_by_symbol,
                optional_price_series_by_symbol=optional_price_series_by_symbol,
                context_label="return distribution",
            )
            returns_values = scoped_series.returns_series.to_numpy(dtype=np.float64)
            if not np.isfinite(returns_values).all():
                raise PortfolioAnalyticsClientError(
                    "Return distribution requires finite aligned return values.",
                    status_code=422,
                )
            sample_size = len(returns_values)
            if sample_size < 2:
                raise PortfolioAnalyticsClientError(
                    f"Insufficient persisted history for return distribution period {period.value}.",
                    status_code=409,
                )

            lower_bound = float(np.min(returns_values))
            upper_bound = float(np.max(returns_values))
            if lower_bound == upper_bound:
                lower_bound -= 1e-9
                upper_bound += 1e-9

            histogram_counts, histogram_edges = np.histogram(
                returns_values,
                bins=bin_count,
                range=(lower_bound, upper_bound),
            )
            buckets = [
                PortfolioReturnDistributionBucket(
                    bucket_index=bucket_index,
                    lower_bound=_quantize_ratio(
                        _decimal_from_float(
                            value=float(histogram_edges[bucket_index]),
                            field="distribution_lower_bound",
                        )
                    ),
                    upper_bound=_quantize_ratio(
                        _decimal_from_float(
                            value=float(histogram_edges[bucket_index + 1]),
                            field="distribution_upper_bound",
                        )
                    ),
                    count=int(histogram_counts[bucket_index]),
                    frequency=_quantize_ratio(
                        Decimal(int(histogram_counts[bucket_index])) / Decimal(sample_size)
                    ),
                )
                for bucket_index in range(bin_count)
            ]
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioReturnDistributionResponse(
                as_of_ledger_at=as_of_ledger_at,
                scope=scope,
                instrument_symbol=instrument_symbol,
                period=period,
                sample_size=sample_size,
                bucket_policy=PortfolioReturnDistributionBucketPolicy(
                    method="equal_width",
                    bin_count=bin_count,
                    min_return=_quantize_ratio(
                        _decimal_from_float(
                            value=float(np.min(returns_values)),
                            field="distribution_min_return",
                        )
                    ),
                    max_return=_quantize_ratio(
                        _decimal_from_float(
                            value=float(np.max(returns_values)),
                            field="distribution_max_return",
                        )
                    ),
                ),
                buckets=buckets,
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.return_distribution_failed",
            period=period.value,
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.return_distribution_failed",
            period=period.value,
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build return distribution due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.return_distribution_completed",
        period=response.period.value,
        scope=response.scope.value,
        instrument_symbol=response.instrument_symbol,
        sample_size=response.sample_size,
        bin_count=response.bucket_policy.bin_count,
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


def _build_efficient_frontier_weight_rows(
    *,
    ordered_symbols: Sequence[str],
    weight_vector: np.ndarray,
) -> list[PortfolioEfficientFrontierWeight]:
    """Build normalized symbol-weight rows from one sampled portfolio vector."""

    if len(ordered_symbols) != len(weight_vector):
        raise PortfolioAnalyticsClientError(
            "Efficient frontier weight vector dimensions do not match symbol set.",
            status_code=422,
        )
    if not np.isfinite(weight_vector).all():
        raise PortfolioAnalyticsClientError(
            "Efficient frontier weight vector contains non-finite values.",
            status_code=422,
        )

    clipped_weights = np.clip(weight_vector.astype(np.float64), a_min=0.0, a_max=None)
    total_weight = float(np.sum(clipped_weights))
    if total_weight <= 0:
        raise PortfolioAnalyticsClientError(
            "Efficient frontier weight vector normalization failed.",
            status_code=422,
        )
    normalized_weights = clipped_weights / total_weight
    return [
        PortfolioEfficientFrontierWeight(
            instrument_symbol=symbol,
            weight=_quantize_ratio(
                _decimal_from_float(
                    value=float(weight_value),
                    field=f"efficient_frontier_weight_{symbol}",
                )
            ),
        )
        for symbol, weight_value in zip(
            ordered_symbols,
            normalized_weights,
            strict=True,
        )
    ]


async def get_portfolio_efficient_frontier_response(
    *,
    db: AsyncSession,
    period: PortfolioChartPeriod,
    scope: PortfolioQuantReportScope,
    instrument_symbol: str | None,
    frontier_points: int = _EFFICIENT_FRONTIER_DEFAULT_POINTS,
) -> PortfolioEfficientFrontierResponse:
    """Return deterministic Markowitz efficient-frontier diagnostics for selected scope."""

    normalized_scope, normalized_instrument_symbol = normalize_chart_scope(
        scope_value=scope,
        instrument_symbol_value=instrument_symbol,
    )
    if (
        frontier_points < _EFFICIENT_FRONTIER_MIN_POINTS
        or frontier_points > _EFFICIENT_FRONTIER_MAX_POINTS
    ):
        raise PortfolioAnalyticsClientError(
            "frontier_points must be between 8 and 60.",
            status_code=422,
        )

    logger.info(
        "portfolio_analytics.efficient_frontier_started",
        period=period.value,
        scope=normalized_scope.value,
        instrument_symbol=normalized_instrument_symbol,
        frontier_points=frontier_points,
    )
    insufficient_history_detail = (
        f"Insufficient persisted history for efficient frontier period {period.value}."
    )
    required_points = _PERIOD_TO_REQUIRED_POINTS[period]
    minimum_timestamp = _resolve_period_minimum_timestamp(period=period)
    risk_free_rate_annual = float(_EFFICIENT_FRONTIER_RISK_FREE_RATE_ANNUAL)

    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                _optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(
                db=db,
                instrument_symbol=(
                    normalized_instrument_symbol
                    if normalized_scope == PortfolioQuantReportScope.INSTRUMENT_SYMBOL
                    else None
                ),
            )
            aligned_timestamps = _select_aligned_timestamps(
                price_series_by_symbol=price_series_by_symbol,
                required_points=required_points,
                minimum_points=2,
                minimum_timestamp=minimum_timestamp,
                insufficient_history_detail=insufficient_history_detail,
            )
            price_frame = _build_aligned_price_frame(
                aligned_timestamps=aligned_timestamps,
                price_series_by_symbol=price_series_by_symbol,
            )
            returns_frame = price_frame.pct_change().dropna()
            if returns_frame.empty or len(returns_frame.index) < 2:
                raise PortfolioAnalyticsClientError(
                    insufficient_history_detail,
                    status_code=409,
                )
            if not np.isfinite(returns_frame.to_numpy(dtype=np.float64)).all():
                raise PortfolioAnalyticsClientError(
                    "Efficient frontier requires finite aligned return values.",
                    status_code=422,
                )

            ordered_symbols = [str(column_name) for column_name in price_frame.columns]
            symbol_count = len(ordered_symbols)
            if symbol_count == 0:
                raise PortfolioAnalyticsClientError(
                    "Efficient frontier requires at least one open-position symbol.",
                    status_code=409,
                )
            expected_returns_by_symbol = returns_frame.mean().to_numpy(dtype=np.float64) * 252.0
            covariance_matrix = returns_frame.cov().to_numpy(dtype=np.float64) * 252.0
            if (
                not np.isfinite(expected_returns_by_symbol).all()
                or not np.isfinite(covariance_matrix).all()
            ):
                raise PortfolioAnalyticsClientError(
                    "Efficient frontier requires finite expected-return and covariance inputs.",
                    status_code=422,
                )
            if covariance_matrix.shape != (symbol_count, symbol_count):
                raise PortfolioAnalyticsClientError(
                    "Efficient frontier covariance matrix dimensions are invalid.",
                    status_code=422,
                )

            asset_volatility = np.sqrt(
                np.clip(
                    np.diag(covariance_matrix),
                    a_min=1e-12,
                    a_max=None,
                )
            )
            asset_points = [
                PortfolioEfficientFrontierAssetPoint(
                    instrument_symbol=symbol,
                    expected_return=_quantize_ratio(
                        _decimal_from_float(
                            value=float(expected_return_value),
                            field=f"efficient_frontier_asset_return_{symbol}",
                        )
                    ),
                    volatility=_quantize_ratio(
                        _decimal_from_float(
                            value=float(volatility_value),
                            field=f"efficient_frontier_asset_volatility_{symbol}",
                        )
                    ),
                )
                for symbol, expected_return_value, volatility_value in zip(
                    ordered_symbols,
                    expected_returns_by_symbol,
                    asset_volatility,
                    strict=True,
                )
            ]

            if symbol_count == 1:
                single_expected_return = float(expected_returns_by_symbol[0])
                single_volatility = float(asset_volatility[0])
                single_sharpe = (
                    (single_expected_return - risk_free_rate_annual) / single_volatility
                    if single_volatility > 0
                    else 0.0
                )
                single_weight_rows = [
                    PortfolioEfficientFrontierWeight(
                        instrument_symbol=ordered_symbols[0],
                        weight=Decimal("1.000000"),
                    )
                ]
                as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
                response = PortfolioEfficientFrontierResponse(
                    as_of_ledger_at=as_of_ledger_at,
                    scope=normalized_scope,
                    instrument_symbol=normalized_instrument_symbol,
                    period=period,
                    risk_free_rate_annual=_quantize_ratio(
                        _EFFICIENT_FRONTIER_RISK_FREE_RATE_ANNUAL
                    ),
                    methodology=PortfolioEfficientFrontierMethodology(
                        optimization_model="mean_variance_long_only",
                        sampling_method="single_asset_degenerate_case",
                        annualization_basis="trading_days_252",
                    ),
                    frontier_points=[
                        PortfolioEfficientFrontierPoint(
                            point_id="p01",
                            expected_return=_quantize_ratio(
                                _decimal_from_float(
                                    value=single_expected_return,
                                    field="efficient_frontier_single_expected_return",
                                )
                            ),
                            volatility=_quantize_ratio(
                                _decimal_from_float(
                                    value=single_volatility,
                                    field="efficient_frontier_single_volatility",
                                )
                            ),
                            sharpe_ratio=_quantize_ratio(
                                _decimal_from_float(
                                    value=single_sharpe,
                                    field="efficient_frontier_single_sharpe_ratio",
                                )
                            ),
                            is_max_sharpe=True,
                            is_min_volatility=True,
                        )
                    ],
                    asset_points=asset_points,
                    max_sharpe_weights=single_weight_rows,
                    min_volatility_weights=single_weight_rows,
                )
                logger.info(
                    "portfolio_analytics.efficient_frontier_completed",
                    period=response.period.value,
                    scope=response.scope.value,
                    instrument_symbol=response.instrument_symbol,
                    symbol_count=symbol_count,
                    frontier_points=len(response.frontier_points),
                    as_of_ledger_at=response.as_of_ledger_at.isoformat(),
                )
                return response

            sample_count = max(
                _EFFICIENT_FRONTIER_MIN_SAMPLE_COUNT,
                frontier_points * _EFFICIENT_FRONTIER_POINT_SAMPLE_MULTIPLIER,
            )
            random_generator = np.random.default_rng(_EFFICIENT_FRONTIER_RANDOM_SEED)
            sampled_weights = random_generator.dirichlet(
                alpha=np.ones(symbol_count, dtype=np.float64),
                size=sample_count,
            )
            sampled_expected_returns = sampled_weights @ expected_returns_by_symbol
            sampled_variances = np.einsum(
                "ij,jk,ik->i",
                sampled_weights,
                covariance_matrix,
                sampled_weights,
            )
            sampled_variances = np.clip(sampled_variances, a_min=1e-12, a_max=None)
            sampled_volatility = np.sqrt(sampled_variances)
            sampled_sharpe = (sampled_expected_returns - risk_free_rate_annual) / sampled_volatility
            finite_mask = (
                np.isfinite(sampled_expected_returns)
                & np.isfinite(sampled_volatility)
                & np.isfinite(sampled_sharpe)
            )
            if not finite_mask.any():
                raise PortfolioAnalyticsClientError(
                    "Efficient frontier sampling produced no finite candidate portfolios.",
                    status_code=409,
                )
            sampled_weights = sampled_weights[finite_mask]
            sampled_expected_returns = sampled_expected_returns[finite_mask]
            sampled_volatility = sampled_volatility[finite_mask]
            sampled_sharpe = sampled_sharpe[finite_mask]
            if len(sampled_expected_returns) == 0:
                raise PortfolioAnalyticsClientError(
                    "Efficient frontier sampling produced no candidate portfolios.",
                    status_code=409,
                )

            min_volatility_index = int(np.argmin(sampled_volatility))
            max_sharpe_index = int(np.argmax(sampled_sharpe))
            sorted_indices = np.argsort(sampled_expected_returns)
            frontier_candidate_indices: list[int] = []
            for index_bucket in np.array_split(sorted_indices, frontier_points):
                if len(index_bucket) == 0:
                    continue
                bucket_volatility = sampled_volatility[index_bucket]
                bucket_choice = int(index_bucket[int(np.argmin(bucket_volatility))])
                frontier_candidate_indices.append(bucket_choice)
            frontier_candidate_indices.append(min_volatility_index)
            frontier_candidate_indices.append(max_sharpe_index)
            unique_frontier_indices = sorted(
                set(frontier_candidate_indices),
                key=lambda index_value: float(sampled_expected_returns[index_value]),
            )

            frontier_rows = [
                PortfolioEfficientFrontierPoint(
                    point_id=f"p{row_index + 1:02d}",
                    expected_return=_quantize_ratio(
                        _decimal_from_float(
                            value=float(sampled_expected_returns[frontier_index]),
                            field=f"efficient_frontier_expected_return_{row_index}",
                        )
                    ),
                    volatility=_quantize_ratio(
                        _decimal_from_float(
                            value=float(sampled_volatility[frontier_index]),
                            field=f"efficient_frontier_volatility_{row_index}",
                        )
                    ),
                    sharpe_ratio=_quantize_ratio(
                        _decimal_from_float(
                            value=float(sampled_sharpe[frontier_index]),
                            field=f"efficient_frontier_sharpe_ratio_{row_index}",
                        )
                    ),
                    is_max_sharpe=frontier_index == max_sharpe_index,
                    is_min_volatility=frontier_index == min_volatility_index,
                )
                for row_index, frontier_index in enumerate(unique_frontier_indices)
            ]

            max_sharpe_weights = _build_efficient_frontier_weight_rows(
                ordered_symbols=ordered_symbols,
                weight_vector=sampled_weights[max_sharpe_index],
            )
            min_volatility_weights = _build_efficient_frontier_weight_rows(
                ordered_symbols=ordered_symbols,
                weight_vector=sampled_weights[min_volatility_index],
            )

            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioEfficientFrontierResponse(
                as_of_ledger_at=as_of_ledger_at,
                scope=normalized_scope,
                instrument_symbol=normalized_instrument_symbol,
                period=period,
                risk_free_rate_annual=_quantize_ratio(_EFFICIENT_FRONTIER_RISK_FREE_RATE_ANNUAL),
                methodology=PortfolioEfficientFrontierMethodology(
                    optimization_model="mean_variance_long_only",
                    sampling_method="dirichlet_mc",
                    annualization_basis="trading_days_252",
                ),
                frontier_points=frontier_rows,
                asset_points=asset_points,
                max_sharpe_weights=max_sharpe_weights,
                min_volatility_weights=min_volatility_weights,
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.efficient_frontier_failed",
            period=period.value,
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            frontier_points=frontier_points,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.efficient_frontier_failed",
            period=period.value,
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            frontier_points=frontier_points,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build efficient frontier due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.efficient_frontier_completed",
        period=response.period.value,
        scope=response.scope.value,
        instrument_symbol=response.instrument_symbol,
        symbol_count=len(open_quantity_by_symbol),
        frontier_points=len(response.frontier_points),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def get_portfolio_health_synthesis_response(
    *,
    db: AsyncSession,
    period: PortfolioChartPeriod,
    scope: PortfolioQuantReportScope = PortfolioQuantReportScope.PORTFOLIO,
    instrument_symbol: str | None = None,
    profile_posture: PortfolioHealthProfilePosture = PortfolioHealthProfilePosture.BALANCED,
) -> PortfolioHealthSynthesisResponse:
    """Return deterministic portfolio-health synthesis for selected scope and period."""

    normalized_scope, normalized_instrument_symbol = normalize_chart_scope(
        scope_value=scope,
        instrument_symbol_value=instrument_symbol,
    )
    logger.info(
        "portfolio_analytics.health_synthesis_started",
        period=period.value,
        scope=normalized_scope.value,
        instrument_symbol=normalized_instrument_symbol,
        profile_posture=profile_posture.value,
    )

    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)
            scoped_series = _build_scope_value_series_result(
                scope=normalized_scope,
                period=period,
                instrument_symbol=normalized_instrument_symbol,
                open_quantity_by_symbol=open_quantity_by_symbol,
                price_series_by_symbol=price_series_by_symbol,
                optional_price_series_by_symbol=optional_price_series_by_symbol,
                context_label="health synthesis",
            )
            (
                pillars,
                key_drivers,
                health_caveats,
                critical_override_count,
            ) = _build_health_pillars_and_drivers(
                value_series=scoped_series.value_series,
                returns_series=scoped_series.returns_series,
            )
            pillar_scores = {pillar.pillar_id: pillar.score for pillar in pillars}
            health_score = _compute_health_score_from_pillar_scores(
                pillar_scores=pillar_scores,
                profile_posture=profile_posture,
            )
            health_label = _resolve_health_label_from_score(
                health_score=health_score,
                critical_override_count=critical_override_count,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioHealthSynthesisResponse(
                as_of_ledger_at=as_of_ledger_at,
                scope=normalized_scope,
                instrument_symbol=normalized_instrument_symbol,
                period=period,
                profile_posture=profile_posture,
                health_score=health_score,
                health_label=health_label,
                threshold_policy_version=_HEALTH_POLICY_VERSION,
                pillars=pillars,
                key_drivers=key_drivers,
                health_caveats=health_caveats,
                core_metric_ids=list(_HEALTH_CORE_METRIC_IDS),
                advanced_metric_ids=list(_HEALTH_ADVANCED_METRIC_IDS),
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.health_synthesis_failed",
            period=period.value,
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            profile_posture=profile_posture.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.health_synthesis_failed",
            period=period.value,
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            profile_posture=profile_posture.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build portfolio health synthesis due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.health_synthesis_completed",
        period=response.period.value,
        scope=response.scope.value,
        instrument_symbol=response.instrument_symbol,
        profile_posture=response.profile_posture.value,
        health_score=response.health_score,
        health_label=response.health_label.value,
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def generate_portfolio_monte_carlo_response(
    *,
    db: AsyncSession,
    request: PortfolioMonteCarloRequest,
) -> PortfolioMonteCarloResponse:
    """Return deterministic Monte Carlo diagnostics for approved scope and period inputs."""

    normalized_scope, normalized_instrument_symbol = normalize_chart_scope(
        scope_value=request.scope,
        instrument_symbol_value=request.instrument_symbol,
    )
    requested_horizon_days = request.horizon_days
    default_horizon_days = _DEFAULT_MONTE_CARLO_HORIZON_BY_PERIOD[request.period]
    effective_horizon_days = (
        requested_horizon_days if requested_horizon_days is not None else default_horizon_days
    )
    effective_seed = request.seed if request.seed is not None else _MONTE_CARLO_DEFAULT_SEED
    logger.info(
        "portfolio_analytics.monte_carlo_started",
        scope=normalized_scope.value,
        instrument_symbol=normalized_instrument_symbol,
        period=request.period.value,
        sims=request.sims,
        horizon_days=effective_horizon_days,
        seed=effective_seed,
    )

    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)
            scoped_series = _build_scope_value_series_result(
                scope=normalized_scope,
                period=request.period,
                instrument_symbol=normalized_instrument_symbol,
                open_quantity_by_symbol=open_quantity_by_symbol,
                price_series_by_symbol=price_series_by_symbol,
                optional_price_series_by_symbol=optional_price_series_by_symbol,
                context_label="monte carlo",
            )
            available_return_days = len(scoped_series.returns_series)
            if available_return_days < _MIN_MONTE_CARLO_HORIZON_DAYS:
                raise PortfolioAnalyticsClientError(
                    "Insufficient persisted history for Monte Carlo simulation. "
                    f"Available return days: {available_return_days}. "
                    f"Minimum required: {_MIN_MONTE_CARLO_HORIZON_DAYS}.",
                    status_code=409,
                )
            if requested_horizon_days is None:
                effective_horizon_days = min(default_horizon_days, available_return_days)
            if effective_horizon_days > available_return_days:
                raise PortfolioAnalyticsClientError(
                    "Insufficient persisted history for Monte Carlo horizon "
                    f"{effective_horizon_days} days. "
                    f"Available return days for scope/period: {available_return_days}.",
                    status_code=409,
                )
            simulation_returns = scoped_series.returns_series.tail(effective_horizon_days)
            start_value = _quantize_money(
                _decimal_from_float(
                    value=float(scoped_series.value_series.iloc[-1]),
                    field="monte_carlo_start_value",
                )
            )
            monte_carlo_result = _run_quantstats_monte_carlo(
                returns_series=simulation_returns,
                sims=request.sims,
                bust_threshold=request.bust_threshold,
                goal_threshold=request.goal_threshold,
                seed=effective_seed,
            )

            terminal_series = _extract_monte_carlo_terminal_series(
                monte_carlo_result=monte_carlo_result
            )
            percentile_values = _extract_monte_carlo_percentile_values(
                terminal_series=terminal_series
            )
            median_return = percentile_values[50]
            mean_return = float(terminal_series.mean())
            bust_probability = _extract_optional_probability(
                monte_carlo_result=monte_carlo_result,
                field_name="bust_probability",
            )
            goal_probability = _extract_optional_probability(
                monte_carlo_result=monte_carlo_result,
                field_name="goal_probability",
            )
            profile_thresholds_by_id, calibration_context = _resolve_monte_carlo_profile_thresholds(
                returns_series=scoped_series.returns_series,
                calibration_basis=request.calibration_basis,
                manual_bust_threshold=request.bust_threshold,
                manual_goal_threshold=request.goal_threshold,
            )
            profile_scenarios = (
                _build_monte_carlo_profile_scenarios(
                    terminal_series=terminal_series,
                    profile_thresholds_by_id=profile_thresholds_by_id,
                )
                if request.enable_profile_comparison
                else []
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioMonteCarloResponse(
                as_of_ledger_at=as_of_ledger_at,
                scope=normalized_scope,
                instrument_symbol=normalized_instrument_symbol,
                period=request.period,
                simulation=PortfolioMonteCarloSimulationParameters(
                    sims=request.sims,
                    horizon_days=effective_horizon_days,
                    seed=effective_seed,
                    bust_threshold=request.bust_threshold,
                    goal_threshold=request.goal_threshold,
                ),
                assumptions=PortfolioMonteCarloAssumptions(
                    model="quantstats_shuffled_returns",
                    notes=[
                        "Simulation shuffles historical simple returns from persisted data.",
                        "Results are scenario-based diagnostics and not predictive forecasts.",
                    ],
                ),
                summary=PortfolioMonteCarloSummary(
                    start_value_usd=start_value,
                    median_ending_value_usd=_quantize_money(
                        start_value
                        * (
                            Decimal("1")
                            + _decimal_from_float(
                                value=median_return,
                                field="monte_carlo_median_return",
                            )
                        )
                    ),
                    mean_ending_return=_quantize_ratio(
                        _decimal_from_float(
                            value=mean_return,
                            field="monte_carlo_mean_return",
                        )
                    ),
                    bust_probability=bust_probability,
                    goal_probability=goal_probability,
                    interpretation_signal=_resolve_monte_carlo_signal_label(
                        bust_probability=bust_probability,
                        goal_probability=goal_probability,
                    ),
                ),
                ending_return_percentiles=[
                    PortfolioMonteCarloPercentilePoint(
                        percentile=percentile,
                        value=_quantize_ratio(
                            _decimal_from_float(
                                value=percentile_value,
                                field=f"monte_carlo_percentile_{percentile}",
                            )
                        ),
                    )
                    for percentile, percentile_value in sorted(percentile_values.items())
                ],
                profile_comparison_enabled=request.enable_profile_comparison,
                calibration_context=calibration_context,
                profile_scenarios=profile_scenarios,
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.monte_carlo_failed",
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            period=request.period.value,
            sims=request.sims,
            horizon_days=effective_horizon_days,
            seed=effective_seed,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.monte_carlo_failed",
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
            period=request.period.value,
            sims=request.sims,
            horizon_days=effective_horizon_days,
            seed=effective_seed,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to generate Monte Carlo diagnostics due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.monte_carlo_completed",
        scope=response.scope.value,
        instrument_symbol=response.instrument_symbol,
        period=response.period.value,
        sims=response.simulation.sims,
        horizon_days=response.simulation.horizon_days,
        seed=response.simulation.seed,
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def get_portfolio_quant_metrics_response(
    *,
    db: AsyncSession,
    period: PortfolioChartPeriod,
) -> PortfolioQuantMetricsResponse:
    """Return QuantStats-derived portfolio metrics for one supported chart period."""

    logger.info(
        "portfolio_analytics.quant_metrics_started",
        period=period.value,
    )
    required_points = _PERIOD_TO_REQUIRED_POINTS[period]
    minimum_timestamp = _resolve_period_minimum_timestamp(period=period)
    insufficient_history_detail = (
        f"Insufficient persisted history for quant metrics period {period.value}."
    )
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)
            aligned_timestamps = _select_aligned_timestamps(
                price_series_by_symbol=price_series_by_symbol,
                required_points=required_points,
                minimum_points=2,
                minimum_timestamp=minimum_timestamp,
                insufficient_history_detail=insufficient_history_detail,
            )
            returns_series = _build_portfolio_returns_series(
                aligned_timestamps=aligned_timestamps,
                price_series_by_symbol=price_series_by_symbol,
                open_quantity_by_symbol=open_quantity_by_symbol,
                insufficient_history_detail=insufficient_history_detail,
            )

            benchmark_symbol, benchmark_returns = _select_quantstats_benchmark_returns(
                aligned_timestamps=aligned_timestamps,
                benchmark_price_series_by_id=_resolve_benchmark_price_series_by_id(
                    aligned_timestamps=aligned_timestamps,
                    candidate_price_series_by_symbol={
                        **optional_price_series_by_symbol,
                        **price_series_by_symbol,
                    },
                ),
            )
            if benchmark_returns is not None:
                shared_index = returns_series.index.intersection(benchmark_returns.index)
                if len(shared_index) >= 2:
                    returns_series = returns_series.loc[shared_index]
                    benchmark_returns = benchmark_returns.loc[shared_index]
                else:
                    benchmark_symbol = None
                    benchmark_returns = None

            metrics, benchmark_context = _build_quantstats_metric_rows(
                returns_series=returns_series,
                benchmark_returns=benchmark_returns,
                benchmark_symbol=benchmark_symbol,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioQuantMetricsResponse(
                as_of_ledger_at=as_of_ledger_at,
                period=period,
                benchmark_symbol=benchmark_symbol,
                benchmark_context=benchmark_context,
                metrics=metrics,
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.quant_metrics_failed",
            period=period.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.quant_metrics_failed",
            period=period.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build quant metrics due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.quant_metrics_completed",
        period=response.period.value,
        metric_count=len(response.metrics),
        benchmark_symbol=response.benchmark_symbol,
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def generate_portfolio_quant_report_response(
    *,
    db: AsyncSession,
    request: PortfolioQuantReportGenerateRequest,
    api_prefix: str,
) -> PortfolioQuantReportGenerateResponse:
    """Generate one bounded QuantStats HTML report and return retrieval metadata."""

    normalized_scope, normalized_instrument_symbol = _normalize_quant_report_request(
        request=request
    )
    logger.info(
        "portfolio_analytics.quant_report_generation_started",
        scope=normalized_scope.value,
        period=request.period.value,
        instrument_symbol=normalized_instrument_symbol,
    )
    _purge_expired_quant_report_artifacts()

    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            (
                open_quantity_by_symbol,
                _total_open_cost_basis_usd,
                price_series_by_symbol,
                optional_price_series_by_symbol,
            ) = await _load_open_position_price_inputs(db=db)
            (
                returns_series,
                benchmark_symbol,
                benchmark_returns,
            ) = _build_quant_report_returns_series(
                scope=normalized_scope,
                period=request.period,
                instrument_symbol=normalized_instrument_symbol,
                open_quantity_by_symbol=open_quantity_by_symbol,
                price_series_by_symbol=price_series_by_symbol,
                optional_price_series_by_symbol=optional_price_series_by_symbol,
            )
            (
                report_returns_series,
                report_benchmark_returns,
            ) = _normalize_quantstats_report_inputs(
                returns_series=returns_series,
                benchmark_returns=benchmark_returns,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            synthetic_value_series = returns_series.add(1.0).cumprod()
            (
                health_pillars,
                health_key_drivers,
                health_caveats,
                health_critical_override_count,
            ) = _build_health_pillars_and_drivers(
                value_series=synthetic_value_series,
                returns_series=returns_series,
            )
            health_pillar_scores = {pillar.pillar_id: pillar.score for pillar in health_pillars}
            health_profile_posture = PortfolioHealthProfilePosture.BALANCED
            health_score = _compute_health_score_from_pillar_scores(
                pillar_scores=health_pillar_scores,
                profile_posture=health_profile_posture,
            )
            health_summary = PortfolioHealthSynthesisResponse(
                as_of_ledger_at=as_of_ledger_at,
                scope=normalized_scope,
                instrument_symbol=normalized_instrument_symbol,
                period=request.period,
                profile_posture=health_profile_posture,
                health_score=health_score,
                health_label=_resolve_health_label_from_score(
                    health_score=health_score,
                    critical_override_count=health_critical_override_count,
                ),
                threshold_policy_version=_HEALTH_POLICY_VERSION,
                pillars=health_pillars,
                key_drivers=health_key_drivers,
                health_caveats=health_caveats,
                core_metric_ids=list(_HEALTH_CORE_METRIC_IDS),
                advanced_metric_ids=list(_HEALTH_ADVANCED_METRIC_IDS),
            )

        quantstats_module = _load_quantstats_module()
        reports_module_raw = getattr(quantstats_module, "reports", None)
        if reports_module_raw is None or not isinstance(reports_module_raw, ModuleType):
            raise PortfolioAnalyticsClientError(
                "QuantStats reports module is unavailable in runtime dependency.",
                status_code=500,
            )
        raw_html_callable = getattr(reports_module_raw, "html", None)
        if raw_html_callable is None or not callable(raw_html_callable):
            raise PortfolioAnalyticsClientError(
                "QuantStats reports.html callable is unavailable in runtime dependency.",
                status_code=500,
            )
        html_callable: Callable[..., object] = raw_html_callable

        generated_at = utcnow().astimezone(UTC)
        expires_at = generated_at + _QUANT_REPORT_RETENTION
        report_id = _build_quant_report_id(
            scope=normalized_scope,
            instrument_symbol=normalized_instrument_symbol,
            period=request.period,
            as_of_ledger_at=as_of_ledger_at,
            generated_at=generated_at,
        )
        output_path = _resolve_quant_report_output_path(report_id=report_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_title = _build_quant_report_title(
            scope=normalized_scope,
            instrument_symbol=normalized_instrument_symbol,
            period=request.period,
        )

        try:
            html_callable(
                report_returns_series,
                benchmark=report_benchmark_returns,
                title=report_title,
                output=str(output_path),
                compounded=True,
                periods_per_year=252,
                match_dates=True,
            )
        except Exception as exc:
            raise PortfolioAnalyticsClientError(
                "Quant report generation failed for the selected scope and period.",
                status_code=422,
            ) from exc

        if (not output_path.exists()) or output_path.stat().st_size <= 0:
            raise PortfolioAnalyticsClientError(
                "Quant report artifact generation did not produce a readable HTML output.",
                status_code=500,
            )

        artifact = _QuantReportArtifact(
            report_id=report_id,
            scope=normalized_scope,
            instrument_symbol=normalized_instrument_symbol,
            period=request.period,
            benchmark_symbol=benchmark_symbol,
            generated_at=generated_at,
            expires_at=expires_at,
            output_path=output_path,
        )
        _QUANT_REPORT_ARTIFACTS_BY_ID[report_id] = artifact
        response = PortfolioQuantReportGenerateResponse(
            report_id=report_id,
            report_url_path=f"{api_prefix}/portfolio/quant-reports/{report_id}",
            lifecycle_status=PortfolioQuantReportLifecycleStatus.READY,
            scope=normalized_scope,
            instrument_symbol=normalized_instrument_symbol,
            period=request.period,
            benchmark_symbol=benchmark_symbol,
            generated_at=generated_at,
            expires_at=expires_at,
            simulation_context_status=PortfolioSimulationContextStatus.UNAVAILABLE,
            simulation_context_reason=(
                "Simulation context is available through the dedicated Monte Carlo endpoint."
                if request.include_simulation_context
                else "Simulation context was not requested in quant report generation."
            ),
            health_summary=health_summary,
        )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.quant_report_generation_failed",
            scope=normalized_scope.value,
            period=request.period.value,
            instrument_symbol=normalized_instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.quant_report_generation_failed",
            scope=normalized_scope.value,
            period=request.period.value,
            instrument_symbol=normalized_instrument_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to generate quant report due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.quant_report_generation_completed",
        report_id=response.report_id,
        scope=response.scope.value,
        period=response.period.value,
        instrument_symbol=response.instrument_symbol,
        benchmark_symbol=response.benchmark_symbol,
        lifecycle_status=response.lifecycle_status.value,
        generated_at=response.generated_at.isoformat(),
        expires_at=response.expires_at.isoformat(),
    )
    return response


def get_portfolio_quant_report_html_content(
    *,
    report_id: str,
) -> str:
    """Return one generated QuantStats HTML report artifact by deterministic report ID."""

    normalized_report_id = report_id.strip()
    if not normalized_report_id:
        raise PortfolioAnalyticsClientError(
            "Report id must be a non-empty string.",
            status_code=422,
        )

    artifact = _QUANT_REPORT_ARTIFACTS_BY_ID.get(normalized_report_id)
    if artifact is None:
        _purge_expired_quant_report_artifacts()
        raise PortfolioAnalyticsClientError(
            f"Quant report artifact '{normalized_report_id}' is unavailable.",
            status_code=404,
        )

    if artifact.expires_at <= utcnow().astimezone(UTC):
        _remove_quant_report_artifact(artifact=artifact)
        raise PortfolioAnalyticsClientError(
            f"Quant report artifact '{normalized_report_id}' has expired.",
            status_code=410,
        )
    if not artifact.output_path.exists():
        _remove_quant_report_artifact(artifact=artifact)
        raise PortfolioAnalyticsClientError(
            f"Quant report artifact '{normalized_report_id}' is unavailable.",
            status_code=404,
        )

    try:
        html_content = artifact.output_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PortfolioAnalyticsClientError(
            f"Quant report artifact '{normalized_report_id}' cannot be read.",
            status_code=500,
        ) from exc

    if not html_content.strip():
        _remove_quant_report_artifact(artifact=artifact)
        raise PortfolioAnalyticsClientError(
            f"Quant report artifact '{normalized_report_id}' is unavailable.",
            status_code=404,
        )
    return html_content


async def get_portfolio_transactions_response(
    *,
    db: AsyncSession,
) -> PortfolioTransactionsResponse:
    """Return persisted ledger-event history for transactions workspace route."""

    logger.info("portfolio_analytics.transactions_started")
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            trade_rows_result = await db.execute(select(PortfolioTransaction))
            dividend_rows_result = await db.execute(select(DividendEvent))

            event_rows: list[PortfolioTransactionEvent] = []
            for trade_row in trade_rows_result.scalars().all():
                normalized_trade_side = (
                    trade_row.trade_side.strip().lower() if trade_row.trade_side else "trade"
                )
                posted_at = datetime.combine(trade_row.event_date, time.min, tzinfo=UTC)
                event_rows.append(
                    PortfolioTransactionEvent(
                        id=f"trade:{trade_row.id}",
                        posted_at=posted_at,
                        instrument_symbol=_normalize_symbol(
                            symbol_value=trade_row.instrument_symbol,
                            field="instrument_symbol",
                        ),
                        event_type=normalized_trade_side,
                        quantity=_quantize_qty(
                            _coerce_decimal(
                                value=trade_row.quantity,
                                field="quantity",
                                context="portfolio_transaction",
                            )
                        ),
                        cash_amount_usd=_quantize_money(
                            _coerce_decimal(
                                value=trade_row.gross_amount_usd,
                                field="gross_amount_usd",
                                context="portfolio_transaction",
                            )
                        ),
                    )
                )

            for dividend_row in dividend_rows_result.scalars().all():
                posted_at = datetime.combine(dividend_row.event_date, time.min, tzinfo=UTC)
                event_rows.append(
                    PortfolioTransactionEvent(
                        id=f"dividend:{dividend_row.id}",
                        posted_at=posted_at,
                        instrument_symbol=_normalize_symbol(
                            symbol_value=dividend_row.instrument_symbol,
                            field="instrument_symbol",
                        ),
                        event_type="dividend",
                        quantity=Decimal("0").quantize(_QTY_SCALE),
                        cash_amount_usd=_quantize_money(
                            _coerce_decimal(
                                value=dividend_row.net_amount_usd,
                                field="net_amount_usd",
                                context="dividend_event",
                            )
                        ),
                    )
                )

            event_rows.sort(
                key=lambda event_row: (
                    event_row.posted_at,
                    event_row.id,
                ),
                reverse=True,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioTransactionsResponse(
                as_of_ledger_at=as_of_ledger_at,
                events=event_rows,
            )
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.transactions_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to load portfolio transactions due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.transactions_completed",
        event_count=len(response.events),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


async def get_portfolio_hierarchy_response(
    *,
    db: AsyncSession,
    group_by: PortfolioHierarchyGroupBy,
) -> PortfolioHierarchyResponse:
    """Return hierarchy-ready open-position rows for home workspace pivot table."""

    logger.info(
        "portfolio_analytics.hierarchy_started",
        group_by=group_by.value,
    )
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            open_lots_result = await db.execute(
                select(Lot).where(Lot.remaining_qty > Decimal("0")),
            )
            open_lots = cast(list[Lot], open_lots_result.scalars().all())
            if not open_lots:
                raise PortfolioAnalyticsClientError(
                    "No open positions are available for hierarchy rendering.",
                    status_code=409,
                )

            serialized_open_lots = [_serialize_lot_row(row) for row in open_lots]
            open_position_symbols = collect_open_position_symbols_from_lots(
                lots=serialized_open_lots
            )
            snapshot_coverage = await resolve_latest_consistent_snapshot_coverage_for_symbols(
                db=db,
                required_symbols=open_position_symbols,
            )
            if snapshot_coverage is None:
                missing_symbols_csv = ", ".join(sorted(open_position_symbols))
                raise PortfolioAnalyticsClientError(
                    "No consistent persisted market-data snapshot provides complete USD "
                    "pricing coverage for open position symbol(s): "
                    f"{missing_symbols_csv}.",
                    status_code=409,
                )

            validate_open_position_price_coverage(
                open_position_symbols=open_position_symbols,
                priced_symbols=set(snapshot_coverage.latest_close_price_usd_by_symbol),
                snapshot_key=snapshot_coverage.snapshot_key,
            )
            groups = build_portfolio_hierarchy_groups(
                open_lots=serialized_open_lots,
                latest_close_price_usd_by_symbol=snapshot_coverage.latest_close_price_usd_by_symbol,
                group_by=group_by,
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            response = PortfolioHierarchyResponse(
                as_of_ledger_at=as_of_ledger_at,
                group_by=group_by,
                pricing_snapshot_key=snapshot_coverage.snapshot_key,
                pricing_snapshot_captured_at=snapshot_coverage.snapshot_captured_at,
                groups=groups,
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.hierarchy_failed",
            group_by=group_by.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            str(exc),
            status_code=exc.status_code,
        ) from exc
    except PortfolioAnalyticsClientError:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.hierarchy_failed",
            group_by=group_by.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build portfolio hierarchy due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.hierarchy_completed",
        group_by=response.group_by.value,
        group_count=len(response.groups),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


def build_portfolio_hierarchy_groups(
    *,
    open_lots: Sequence[Mapping[str, object]],
    latest_close_price_usd_by_symbol: Mapping[str, Decimal],
    group_by: PortfolioHierarchyGroupBy,
) -> list[PortfolioHierarchyGroupRow]:
    """Build hierarchy group rows from open lots and one pricing snapshot."""

    asset_builder_by_symbol: dict[str, dict[str, object]] = {}
    normalized_latest_close_price_usd_by_symbol: dict[str, Decimal] = {}
    for raw_symbol, raw_price in latest_close_price_usd_by_symbol.items():
        normalized_symbol = _normalize_symbol(
            symbol_value=raw_symbol,
            field="latest_close_price_usd_by_symbol",
        )
        normalized_latest_close_price_usd_by_symbol[normalized_symbol] = _coerce_decimal(
            value=raw_price,
            field="latest_close_price_usd_by_symbol",
            context="market_data_price",
        )

    for lot in open_lots:
        lot_context = "lot"
        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=lot,
                field="instrument_symbol",
                context=lot_context,
            ),
            field="instrument_symbol",
        )
        lot_id = _coerce_positive_int(
            value=_read_required_field(record=lot, field="id", context=lot_context),
            field="id",
            context=lot_context,
        )
        opened_on = _coerce_date(
            value=_read_required_field(record=lot, field="opened_on", context=lot_context),
            field="opened_on",
            context=lot_context,
        )
        original_qty = _coerce_decimal(
            value=_read_required_field(record=lot, field="original_qty", context=lot_context),
            field="original_qty",
            context=lot_context,
        )
        remaining_qty = _coerce_decimal(
            value=_read_required_field(record=lot, field="remaining_qty", context=lot_context),
            field="remaining_qty",
            context=lot_context,
        )
        total_cost_basis_usd = _coerce_decimal(
            value=_read_required_field(
                record=lot, field="total_cost_basis_usd", context=lot_context
            ),
            field="total_cost_basis_usd",
            context=lot_context,
        )
        unit_cost_basis_usd = _coerce_decimal(
            value=_read_required_field(
                record=lot, field="unit_cost_basis_usd", context=lot_context
            ),
            field="unit_cost_basis_usd",
            context=lot_context,
        )
        if remaining_qty <= Decimal("0"):
            continue

        latest_close_price_usd = normalized_latest_close_price_usd_by_symbol.get(symbol)
        if latest_close_price_usd is None:
            raise PortfolioAnalyticsClientError(
                "Hierarchy rendering found missing latest close coverage for open symbol "
                f"'{symbol}'.",
                status_code=422,
            )

        lot_market_value_usd = remaining_qty * latest_close_price_usd
        lot_profit_loss_usd = lot_market_value_usd - total_cost_basis_usd

        if symbol not in asset_builder_by_symbol:
            asset_builder_by_symbol[symbol] = {
                "open_quantity_raw": Decimal("0"),
                "open_cost_basis_raw": Decimal("0"),
                "sector_label": _resolve_sector_label(symbol=symbol),
                "current_price_raw": latest_close_price_usd,
                "lots": [],
            }

        asset_builder = asset_builder_by_symbol[symbol]
        asset_builder["open_quantity_raw"] = cast(Decimal, asset_builder["open_quantity_raw"]) + (
            remaining_qty
        )
        asset_builder["open_cost_basis_raw"] = (
            cast(Decimal, asset_builder["open_cost_basis_raw"]) + total_cost_basis_usd
        )
        cast(list[PortfolioHierarchyLotRow], asset_builder["lots"]).append(
            PortfolioHierarchyLotRow(
                lot_id=lot_id,
                opened_on=opened_on,
                original_qty=_quantize_qty(original_qty),
                remaining_qty=_quantize_qty(remaining_qty),
                unit_cost_basis_usd=_quantize_money(unit_cost_basis_usd),
                total_cost_basis_usd=_quantize_money(total_cost_basis_usd),
                market_value_usd=_quantize_money(lot_market_value_usd),
                profit_loss_usd=_quantize_money(lot_profit_loss_usd),
            )
        )

    if not asset_builder_by_symbol:
        raise PortfolioAnalyticsClientError(
            "No open positions are available for hierarchy rendering.",
            status_code=409,
        )

    asset_rows: list[PortfolioHierarchyAssetRow] = []
    for symbol in sorted(asset_builder_by_symbol):
        asset_builder = asset_builder_by_symbol[symbol]
        open_quantity_raw = cast(Decimal, asset_builder["open_quantity_raw"])
        open_cost_basis_raw = cast(Decimal, asset_builder["open_cost_basis_raw"])
        current_price_raw = cast(Decimal, asset_builder["current_price_raw"])
        lots = cast(list[PortfolioHierarchyLotRow], asset_builder["lots"])
        lots.sort(
            key=lambda lot_row: (
                lot_row.opened_on.isoformat(),
                lot_row.lot_id,
            )
        )

        market_value_raw = open_quantity_raw * current_price_raw
        profit_loss_raw = market_value_raw - open_cost_basis_raw
        avg_price_raw = (
            (open_cost_basis_raw / open_quantity_raw)
            if open_quantity_raw > Decimal("0")
            else Decimal("0")
        )
        change_pct = _compute_unrealized_gain_pct(
            unrealized_gain_usd=profit_loss_raw,
            open_cost_basis_usd=open_cost_basis_raw,
        )

        asset_rows.append(
            PortfolioHierarchyAssetRow(
                instrument_symbol=symbol,
                sector_label=cast(str, asset_builder["sector_label"]),
                open_quantity=_quantize_qty(open_quantity_raw),
                open_cost_basis_usd=_quantize_money(open_cost_basis_raw),
                avg_price_usd=_quantize_money(avg_price_raw),
                current_price_usd=_quantize_money(current_price_raw),
                market_value_usd=_quantize_money(market_value_raw),
                profit_loss_usd=_quantize_money(profit_loss_raw),
                change_pct=change_pct,
                lot_count=len(lots),
                lots=lots,
            )
        )

    grouped_assets: dict[str, list[PortfolioHierarchyAssetRow]] = defaultdict(list)
    if group_by == PortfolioHierarchyGroupBy.SYMBOL:
        for asset_row in asset_rows:
            grouped_assets[asset_row.instrument_symbol].append(asset_row)
    else:
        for asset_row in asset_rows:
            grouped_assets[asset_row.sector_label].append(asset_row)

    groups: list[PortfolioHierarchyGroupRow] = []
    for group_key in sorted(grouped_assets):
        grouped_asset_rows = sorted(
            grouped_assets[group_key],
            key=lambda row: row.instrument_symbol,
        )
        total_market_value_raw = sum(
            (asset_row.market_value_usd for asset_row in grouped_asset_rows),
            start=Decimal("0"),
        )
        total_profit_loss_raw = sum(
            (asset_row.profit_loss_usd for asset_row in grouped_asset_rows),
            start=Decimal("0"),
        )
        total_open_cost_basis_raw = sum(
            (asset_row.open_cost_basis_usd for asset_row in grouped_asset_rows),
            start=Decimal("0"),
        )
        total_change_pct = _compute_unrealized_gain_pct(
            unrealized_gain_usd=total_profit_loss_raw,
            open_cost_basis_usd=total_open_cost_basis_raw,
        )

        groups.append(
            PortfolioHierarchyGroupRow(
                group_key=group_key,
                group_label=group_key,
                asset_count=len(grouped_asset_rows),
                total_market_value_usd=_quantize_money(total_market_value_raw),
                total_profit_loss_usd=_quantize_money(total_profit_loss_raw),
                total_change_pct=total_change_pct,
                assets=grouped_asset_rows,
            )
        )

    return groups


def build_grouped_portfolio_summary_from_ledger(
    *,
    lots: Sequence[Mapping[str, object]],
    lot_dispositions: Sequence[Mapping[str, object]],
    portfolio_transactions: Sequence[Mapping[str, object]],
    dividend_events: Sequence[Mapping[str, object]],
    latest_close_price_usd_by_symbol: Mapping[str, Decimal] | None = None,
) -> list[dict[str, object]]:
    """Compute grouped KPI rows by instrument symbol from ledger and optional pricing."""

    normalized_latest_close_price_usd_by_symbol: dict[str, Decimal] = {}
    if latest_close_price_usd_by_symbol is not None:
        for raw_symbol, raw_price in latest_close_price_usd_by_symbol.items():
            normalized_symbol = _normalize_symbol(
                symbol_value=raw_symbol,
                field="latest_close_price_usd_by_symbol",
            )
            normalized_latest_close_price_usd_by_symbol[normalized_symbol] = _coerce_decimal(
                value=raw_price,
                field="latest_close_price_usd_by_symbol",
                context="market_data_price",
            )

    open_quantity_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    open_cost_basis_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    open_lot_count_by_symbol: dict[str, int] = defaultdict(int)
    lot_id_to_symbol: dict[int, str] = {}

    for lot in lots:
        lot_context = "lot"
        lot_id = _coerce_positive_int(
            value=_read_required_field(record=lot, field="id", context=lot_context),
            field="id",
            context=lot_context,
        )
        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=lot,
                field="instrument_symbol",
                context=lot_context,
            ),
            field="instrument_symbol",
        )
        lot_id_to_symbol[lot_id] = symbol
        remaining_qty = _coerce_decimal(
            value=_read_required_field(record=lot, field="remaining_qty", context=lot_context),
            field="remaining_qty",
            context=lot_context,
        )
        total_cost_basis_usd = _coerce_decimal(
            value=_read_required_field(
                record=lot, field="total_cost_basis_usd", context=lot_context
            ),
            field="total_cost_basis_usd",
            context=lot_context,
        )

        if remaining_qty > Decimal("0"):
            open_quantity_by_symbol[symbol] += remaining_qty
            open_cost_basis_by_symbol[symbol] += total_cost_basis_usd
            open_lot_count_by_symbol[symbol] += 1

    realized_cost_basis_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    disposition_sell_ids_by_symbol: dict[str, set[int]] = defaultdict(set)

    for disposition in lot_dispositions:
        disposition_context = "lot_disposition"
        lot_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition, field="lot_id", context=disposition_context
            ),
            field="lot_id",
            context=disposition_context,
        )
        symbol_from_lot = lot_id_to_symbol.get(lot_id)
        if symbol_from_lot is None:
            raw_disposition_symbol = disposition.get("instrument_symbol")
            if raw_disposition_symbol is None:
                raise PortfolioAnalyticsClientError(
                    "Disposition row cannot be resolved to an instrument symbol.",
                    status_code=422,
                )
            symbol = _normalize_symbol(
                symbol_value=raw_disposition_symbol,
                field="instrument_symbol",
            )
        else:
            symbol = symbol_from_lot

        matched_cost_basis_usd = _coerce_decimal(
            value=_read_required_field(
                record=disposition,
                field="matched_cost_basis_usd",
                context=disposition_context,
            ),
            field="matched_cost_basis_usd",
            context=disposition_context,
        )
        sell_transaction_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition,
                field="sell_transaction_id",
                context=disposition_context,
            ),
            field="sell_transaction_id",
            context=disposition_context,
        )

        realized_cost_basis_by_symbol[symbol] += matched_cost_basis_usd
        disposition_sell_ids_by_symbol[symbol].add(sell_transaction_id)

    sell_proceeds_by_symbol_and_tx: dict[tuple[str, int], Decimal] = {}
    sell_transaction_ids_by_symbol: dict[str, set[int]] = defaultdict(set)

    for transaction in portfolio_transactions:
        transaction_context = "portfolio_transaction"
        trade_side_raw = _read_required_field(
            record=transaction,
            field="trade_side",
            context=transaction_context,
        )
        if not isinstance(trade_side_raw, str):
            raise PortfolioAnalyticsClientError(
                "Portfolio transaction trade_side must be a string.",
                status_code=422,
            )
        if trade_side_raw.strip().lower() != "sell":
            continue

        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=transaction,
                field="instrument_symbol",
                context=transaction_context,
            ),
            field="instrument_symbol",
        )
        transaction_id = _coerce_positive_int(
            value=_read_required_field(record=transaction, field="id", context=transaction_context),
            field="id",
            context=transaction_context,
        )
        gross_amount_usd = _coerce_decimal(
            value=_read_required_field(
                record=transaction,
                field="gross_amount_usd",
                context=transaction_context,
            ),
            field="gross_amount_usd",
            context=transaction_context,
        )

        key = (symbol, transaction_id)
        previous_amount = sell_proceeds_by_symbol_and_tx.get(key)
        if previous_amount is not None and previous_amount != gross_amount_usd:
            raise PortfolioAnalyticsClientError(
                "Sell transaction gross amount is inconsistent for the same transaction id.",
                status_code=422,
            )
        sell_proceeds_by_symbol_and_tx[key] = gross_amount_usd
        sell_transaction_ids_by_symbol[symbol].add(transaction_id)

    dividend_gross_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    dividend_taxes_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    dividend_net_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for dividend in dividend_events:
        dividend_context = "dividend_event"
        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=dividend,
                field="instrument_symbol",
                context=dividend_context,
            ),
            field="instrument_symbol",
        )
        gross_amount_usd = _coerce_decimal(
            value=_read_required_field(
                record=dividend,
                field="gross_amount_usd",
                context=dividend_context,
            ),
            field="gross_amount_usd",
            context=dividend_context,
        )
        taxes_withheld_usd = _coerce_decimal(
            value=_read_required_field(
                record=dividend,
                field="taxes_withheld_usd",
                context=dividend_context,
            ),
            field="taxes_withheld_usd",
            context=dividend_context,
        )
        net_amount_usd = _coerce_decimal(
            value=_read_required_field(
                record=dividend, field="net_amount_usd", context=dividend_context
            ),
            field="net_amount_usd",
            context=dividend_context,
        )

        dividend_gross_by_symbol[symbol] += gross_amount_usd
        dividend_taxes_by_symbol[symbol] += taxes_withheld_usd
        dividend_net_by_symbol[symbol] += net_amount_usd

    active_symbols = sorted(
        {
            *open_quantity_by_symbol.keys(),
            *realized_cost_basis_by_symbol.keys(),
            *sell_transaction_ids_by_symbol.keys(),
            *dividend_gross_by_symbol.keys(),
            *dividend_taxes_by_symbol.keys(),
            *dividend_net_by_symbol.keys(),
        }
    )

    summary_rows: list[dict[str, object]] = []
    for symbol in active_symbols:
        open_quantity = _quantize_qty(open_quantity_by_symbol.get(symbol, Decimal("0")))
        open_cost_basis_usd = _quantize_money(open_cost_basis_by_symbol.get(symbol, Decimal("0")))
        open_lot_count = open_lot_count_by_symbol.get(symbol, 0)

        realized_proceeds_usd = _quantize_money(
            sum(
                (
                    sell_proceeds_by_symbol_and_tx[(symbol, sell_transaction_id)]
                    for sell_transaction_id in sell_transaction_ids_by_symbol.get(symbol, set())
                    if (symbol, sell_transaction_id) in sell_proceeds_by_symbol_and_tx
                ),
                start=Decimal("0"),
            )
        )
        realized_cost_basis_usd = _quantize_money(
            realized_cost_basis_by_symbol.get(symbol, Decimal("0")),
        )
        realized_gain_usd = _quantize_money(realized_proceeds_usd - realized_cost_basis_usd)

        dividend_gross_usd = _quantize_money(dividend_gross_by_symbol.get(symbol, Decimal("0")))
        dividend_taxes_usd = _quantize_money(dividend_taxes_by_symbol.get(symbol, Decimal("0")))
        dividend_net_usd = _quantize_money(dividend_net_by_symbol.get(symbol, Decimal("0")))
        latest_close_price_usd: Decimal | None = None
        market_value_usd: Decimal | None = None
        unrealized_gain_usd: Decimal | None = None
        unrealized_gain_pct: Decimal | None = None
        if open_quantity > Decimal("0"):
            latest_close_candidate = normalized_latest_close_price_usd_by_symbol.get(symbol)
            if latest_close_candidate is not None:
                latest_close_price_usd = _quantize_money(latest_close_candidate)
                raw_market_value_usd = open_quantity * latest_close_candidate
                raw_unrealized_gain_usd = raw_market_value_usd - open_cost_basis_usd
                market_value_usd = _quantize_money(raw_market_value_usd)
                unrealized_gain_usd = _quantize_money(raw_unrealized_gain_usd)
                unrealized_gain_pct = _compute_unrealized_gain_pct(
                    unrealized_gain_usd=raw_unrealized_gain_usd,
                    open_cost_basis_usd=open_cost_basis_usd,
                )

        has_activity = any(
            (
                open_quantity > Decimal("0"),
                realized_proceeds_usd > Decimal("0"),
                realized_cost_basis_usd > Decimal("0"),
                dividend_gross_usd > Decimal("0"),
                dividend_taxes_usd > Decimal("0"),
                dividend_net_usd > Decimal("0"),
            )
        )
        if not has_activity:
            continue

        summary_rows.append(
            {
                "instrument_symbol": symbol,
                "open_quantity": open_quantity,
                "open_cost_basis_usd": open_cost_basis_usd,
                "open_lot_count": open_lot_count,
                "realized_proceeds_usd": realized_proceeds_usd,
                "realized_cost_basis_usd": realized_cost_basis_usd,
                "realized_gain_usd": realized_gain_usd,
                "dividend_gross_usd": dividend_gross_usd,
                "dividend_taxes_usd": dividend_taxes_usd,
                "dividend_net_usd": dividend_net_usd,
                "latest_close_price_usd": latest_close_price_usd,
                "market_value_usd": market_value_usd,
                "unrealized_gain_usd": unrealized_gain_usd,
                "unrealized_gain_pct": unrealized_gain_pct,
            }
        )

    return summary_rows


def collect_open_position_symbols_from_lots(*, lots: Sequence[Mapping[str, object]]) -> set[str]:
    """Return normalized symbols with positive remaining quantity from lot rows."""

    open_position_symbols: set[str] = set()
    for lot in lots:
        lot_context = "lot"
        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=lot,
                field="instrument_symbol",
                context=lot_context,
            ),
            field="instrument_symbol",
        )
        remaining_qty = _coerce_decimal(
            value=_read_required_field(record=lot, field="remaining_qty", context=lot_context),
            field="remaining_qty",
            context=lot_context,
        )
        if remaining_qty > Decimal("0"):
            open_position_symbols.add(symbol)
    return open_position_symbols


def validate_open_position_price_coverage(
    *,
    open_position_symbols: set[str],
    priced_symbols: set[str],
    snapshot_key: str,
) -> None:
    """Fail fast when selected snapshot does not cover all open-position symbols."""

    missing_symbols = sorted(open_position_symbols - priced_symbols)
    if not missing_symbols:
        return

    missing_symbols_csv = ", ".join(missing_symbols)
    raise PortfolioAnalyticsClientError(
        f"Selected pricing snapshot '{snapshot_key}' is missing required open-position coverage "
        f"for symbol(s): {missing_symbols_csv}.",
        status_code=409,
    )


async def _load_open_position_price_inputs(
    *,
    db: AsyncSession,
    instrument_symbol: str | None = None,
) -> tuple[
    dict[str, Decimal],
    Decimal,
    dict[str, dict[datetime, Decimal]],
    dict[str, dict[datetime, Decimal]],
]:
    """Load open-position quantities and aligned snapshot price history inputs."""

    lots_result = await db.execute(
        select(Lot).where(Lot.remaining_qty > Decimal("0")),
    )
    open_lots = cast(list[Lot], lots_result.scalars().all())
    if not open_lots:
        raise PortfolioAnalyticsClientError(
            "No open positions are available for analytics computation.",
            status_code=409,
        )

    open_quantity_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    total_open_cost_basis_usd = Decimal("0")
    for lot in open_lots:
        normalized_symbol = _normalize_symbol(
            symbol_value=lot.instrument_symbol,
            field="instrument_symbol",
        )
        if instrument_symbol is not None and normalized_symbol != instrument_symbol:
            continue
        remaining_qty = _coerce_decimal(
            value=lot.remaining_qty,
            field="remaining_qty",
            context="lot",
        )
        total_cost_basis_usd = _coerce_decimal(
            value=lot.total_cost_basis_usd,
            field="total_cost_basis_usd",
            context="lot",
        )
        open_quantity_by_symbol[normalized_symbol] += remaining_qty
        total_open_cost_basis_usd += total_cost_basis_usd

    if not open_quantity_by_symbol:
        if instrument_symbol is None:
            raise PortfolioAnalyticsClientError(
                "No open positions are available for analytics computation.",
                status_code=409,
            )
        raise PortfolioAnalyticsClientError(
            "No open positions are available for requested symbol " f"'{instrument_symbol}'.",
            status_code=409,
        )

    required_symbols = set(open_quantity_by_symbol)
    optional_symbols = set(_OPTIONAL_BENCHMARK_CANDIDATE_SYMBOLS)
    query_symbols = required_symbols | optional_symbols
    snapshot_coverage = await resolve_latest_consistent_snapshot_coverage_for_symbols(
        db=db,
        required_symbols=required_symbols,
    )
    if snapshot_coverage is None:
        missing_symbols_csv = ", ".join(sorted(required_symbols))
        raise PortfolioAnalyticsClientError(
            "No consistent persisted market-data snapshot provides complete USD pricing "
            f"coverage for open position symbol(s): {missing_symbols_csv}.",
            status_code=409,
        )

    price_rows = await _load_snapshot_price_rows(
        db=db,
        snapshot_id=snapshot_coverage.snapshot_id,
        query_symbols=query_symbols,
    )
    price_series_by_symbol = _build_price_series_by_symbol(
        price_rows=price_rows,
        required_symbols=required_symbols,
    )
    optional_price_series_by_symbol = _build_optional_price_series_by_symbol(
        price_rows=price_rows,
        optional_symbols=optional_symbols,
    )
    return (
        dict(open_quantity_by_symbol),
        total_open_cost_basis_usd,
        price_series_by_symbol,
        optional_price_series_by_symbol,
    )


async def _load_snapshot_price_rows(
    *,
    db: AsyncSession,
    snapshot_id: int,
    query_symbols: set[str],
) -> list[PriceHistory]:
    """Load deterministic USD price rows for one snapshot and symbol set."""

    query = (
        select(PriceHistory)
        .where(
            PriceHistory.snapshot_id == snapshot_id,
            PriceHistory.instrument_symbol.in_(query_symbols),
            PriceHistory.currency_code == "USD",
        )
        .order_by(
            PriceHistory.instrument_symbol.asc(),
            PriceHistory.market_timestamp.asc().nullslast(),
            PriceHistory.trading_date.asc().nullslast(),
            PriceHistory.id.asc(),
        )
    )
    result = await db.execute(query)
    return cast(list[PriceHistory], result.scalars().all())


def _build_price_series_by_symbol(
    *,
    price_rows: Sequence[PriceHistory],
    required_symbols: set[str],
) -> dict[str, dict[datetime, Decimal]]:
    """Build timestamp-indexed price series for each required symbol."""

    series_by_symbol: dict[str, dict[datetime, Decimal]] = {
        symbol: {} for symbol in sorted(required_symbols)
    }
    for price_row in price_rows:
        normalized_symbol = _normalize_symbol(
            symbol_value=price_row.instrument_symbol,
            field="instrument_symbol",
        )
        if normalized_symbol not in series_by_symbol:
            continue

        captured_at = _coerce_price_row_timestamp(price_row=price_row)
        price_value = _coerce_decimal(
            value=price_row.price_value,
            field="price_value",
            context="price_history",
        )
        series_by_symbol[normalized_symbol][captured_at] = price_value

    missing_symbols = [
        symbol for symbol, symbol_series in series_by_symbol.items() if not symbol_series
    ]
    if missing_symbols:
        missing_symbols_csv = ", ".join(sorted(missing_symbols))
        raise PortfolioAnalyticsClientError(
            "Insufficient persisted history: selected snapshot is missing price rows for "
            f"open position symbol(s): {missing_symbols_csv}.",
            status_code=409,
        )

    return series_by_symbol


def _build_optional_price_series_by_symbol(
    *,
    price_rows: Sequence[PriceHistory],
    optional_symbols: set[str],
) -> dict[str, dict[datetime, Decimal]]:
    """Build timestamp-indexed price series for optional benchmark candidates."""

    series_by_symbol: dict[str, dict[datetime, Decimal]] = {
        symbol: {} for symbol in sorted(optional_symbols)
    }
    for price_row in price_rows:
        normalized_symbol = _normalize_symbol(
            symbol_value=price_row.instrument_symbol,
            field="instrument_symbol",
        )
        if normalized_symbol not in series_by_symbol:
            continue

        captured_at = _coerce_price_row_timestamp(price_row=price_row)
        price_value = _coerce_decimal(
            value=price_row.price_value,
            field="price_value",
            context="price_history",
        )
        series_by_symbol[normalized_symbol][captured_at] = price_value

    return {
        symbol: symbol_series for symbol, symbol_series in series_by_symbol.items() if symbol_series
    }


def _coerce_price_row_timestamp(*, price_row: PriceHistory) -> datetime:
    """Return one timezone-aware timestamp for a price-history row."""

    if price_row.market_timestamp is not None:
        timestamp = price_row.market_timestamp
    elif price_row.trading_date is not None:
        timestamp = datetime.combine(price_row.trading_date, time.min, tzinfo=UTC)
    else:
        raise PortfolioAnalyticsClientError(
            "Price-history row is missing market time context.",
            status_code=422,
        )

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def _select_aligned_timestamps(
    *,
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    required_points: int | None,
    minimum_points: int,
    minimum_timestamp: datetime | None = None,
    insufficient_history_detail: str,
) -> list[datetime]:
    """Select deterministic aligned timestamps across all required symbols."""

    symbol_timestamp_sets: list[set[datetime]] = [
        set(symbol_series.keys()) for symbol_series in price_series_by_symbol.values()
    ]
    if not symbol_timestamp_sets:
        raise PortfolioAnalyticsClientError(
            insufficient_history_detail,
            status_code=409,
        )

    common_timestamps: set[datetime] = set(symbol_timestamp_sets[0])
    for symbol_timestamps in symbol_timestamp_sets[1:]:
        common_timestamps &= symbol_timestamps

    ordered_timestamps: list[datetime] = sorted(common_timestamps)
    if minimum_timestamp is not None:
        ordered_timestamps = [
            timestamp for timestamp in ordered_timestamps if timestamp >= minimum_timestamp
        ]

    if required_points is not None:
        if len(ordered_timestamps) < required_points:
            raise PortfolioAnalyticsClientError(
                insufficient_history_detail,
                status_code=409,
            )
        ordered_timestamps = ordered_timestamps[-required_points:]

    if len(ordered_timestamps) < minimum_points:
        raise PortfolioAnalyticsClientError(
            insufficient_history_detail,
            status_code=409,
        )
    return ordered_timestamps


def _build_aligned_price_frame(
    *,
    aligned_timestamps: Sequence[datetime],
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
) -> pd.DataFrame:
    """Build one deterministic, UTC-aware aligned price frame for estimator kernels."""

    _validate_aligned_timestamp_index(aligned_timestamps=aligned_timestamps)
    ordered_symbols = sorted(price_series_by_symbol)
    if not ordered_symbols:
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing requires at least one symbol series.",
            status_code=422,
        )

    price_columns: dict[str, list[float]] = {}
    for symbol in ordered_symbols:
        symbol_series = price_series_by_symbol.get(symbol)
        if symbol_series is None:
            raise PortfolioAnalyticsClientError(
                "Risk estimator preprocessing found missing symbol series mapping.",
                status_code=422,
            )

        symbol_prices: list[float] = []
        for timestamp in aligned_timestamps:
            raw_price = symbol_series.get(timestamp)
            if raw_price is None:
                raise PortfolioAnalyticsClientError(
                    "Risk estimator preprocessing found missing aligned symbol price point.",
                    status_code=422,
                )
            normalized_price = _coerce_decimal(
                value=raw_price,
                field="price_value",
                context="risk_estimator_preprocessing",
            )
            symbol_prices.append(float(normalized_price))
        price_columns[symbol] = symbol_prices

    datetime_index = pd.DatetimeIndex(list(aligned_timestamps))
    if datetime_index.tz is None:
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing requires timezone-aware UTC timestamps.",
            status_code=422,
        )

    price_frame = pd.DataFrame(
        price_columns,
        index=datetime_index,
        dtype=np.float64,
    )
    if price_frame.empty:
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing produced an empty aligned price frame.",
            status_code=422,
        )
    if price_frame.isna().to_numpy(dtype=bool).any():
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing does not allow missing aligned values.",
            status_code=422,
        )
    if not np.isfinite(price_frame.to_numpy(dtype=np.float64)).all():
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing requires finite aligned price values.",
            status_code=422,
        )
    return price_frame


def _compute_risk_metrics_from_price_frame(
    *,
    price_frame: pd.DataFrame,
    open_quantity_by_symbol: Mapping[str, Decimal],
    window_days: int,
    proxy_returns_override: pd.Series | None = None,
) -> dict[str, Decimal]:
    """Compute baseline v1 risk metrics from aligned prices using pandas/NumPy/SciPy."""

    if window_days <= 1:
        raise PortfolioAnalyticsClientError(
            "Risk estimator window must be greater than one day.",
            status_code=422,
        )
    if price_frame.shape[0] < window_days + 1:
        raise PortfolioAnalyticsClientError(
            f"Insufficient persisted history for risk window {window_days}.",
            status_code=409,
        )

    ordered_symbols = [str(column_name) for column_name in price_frame.columns]
    if not ordered_symbols:
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing requires at least one symbol column.",
            status_code=422,
        )

    quantity_vector_values: list[float] = []
    for symbol in ordered_symbols:
        if symbol not in open_quantity_by_symbol:
            raise PortfolioAnalyticsClientError(
                "Risk estimator preprocessing found symbol alignment mismatch.",
                status_code=422,
            )
        normalized_quantity = _coerce_decimal(
            value=open_quantity_by_symbol[symbol],
            field="open_quantity",
            context="risk_estimator_preprocessing",
        )
        if normalized_quantity <= Decimal("0"):
            raise PortfolioAnalyticsClientError(
                "Risk estimator preprocessing requires positive open quantities.",
                status_code=422,
            )
        quantity_vector_values.append(float(normalized_quantity))

    quantity_vector = np.array(quantity_vector_values, dtype=np.float64)
    price_matrix = price_frame.to_numpy(dtype=np.float64)
    if not np.isfinite(price_matrix).all():
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing requires finite aligned symbol prices.",
            status_code=422,
        )
    if np.any(price_matrix <= 0):
        raise PortfolioAnalyticsClientError(
            "Risk estimators require positive historical symbol prices.",
            status_code=409,
        )

    portfolio_values = np.matmul(price_matrix, quantity_vector)
    if not np.isfinite(portfolio_values).all():
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing produced non-finite portfolio values.",
            status_code=422,
        )
    if np.any(portfolio_values <= 0):
        raise PortfolioAnalyticsClientError(
            "Risk estimators require positive historical portfolio values to compute returns.",
            status_code=409,
        )

    portfolio_value_series = pd.Series(
        portfolio_values,
        index=price_frame.index,
        name="portfolio_value",
    )
    portfolio_returns = portfolio_value_series.pct_change().dropna()
    symbol_returns = price_frame.pct_change().dropna(how="all")
    if symbol_returns.isna().to_numpy(dtype=bool).any():
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing does not allow implicit missing-data fills.",
            status_code=422,
        )
    if proxy_returns_override is not None:
        proxy_returns = proxy_returns_override.astype(np.float64)
        if proxy_returns.empty:
            raise PortfolioAnalyticsClientError(
                f"Insufficient persisted history for risk window {window_days}.",
                status_code=409,
            )
        if not np.isfinite(proxy_returns.to_numpy(dtype=np.float64)).all():
            raise PortfolioAnalyticsClientError(
                "Risk estimator preprocessing requires finite benchmark proxy return values.",
                status_code=422,
            )
    else:
        proxy_returns = symbol_returns.mean(axis=1)

    risk_window_frame = pd.concat(
        (
            portfolio_returns.rename("portfolio"),
            proxy_returns.rename("proxy"),
        ),
        axis=1,
        join="inner",
    ).tail(window_days)
    if len(risk_window_frame) < window_days:
        raise PortfolioAnalyticsClientError(
            f"Insufficient persisted history for risk window {window_days}.",
            status_code=409,
        )
    if risk_window_frame.isna().to_numpy(dtype=bool).any():
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing found missing aligned return values.",
            status_code=422,
        )

    portfolio_window = risk_window_frame["portfolio"]
    proxy_window = risk_window_frame["proxy"]
    rolling_std = portfolio_window.rolling(
        window=window_days,
        min_periods=window_days,
    ).std(ddof=1)
    volatility_annualized = float(rolling_std.iloc[-1]) * float(np.sqrt(252.0))

    cumulative_peaks = portfolio_value_series.cummax()
    drawdown_series = (portfolio_value_series / cumulative_peaks) - 1.0
    max_drawdown = float(drawdown_series.min())

    rolling_covariance = portfolio_window.rolling(
        window=window_days,
        min_periods=window_days,
    ).cov(proxy_window)
    rolling_variance = proxy_window.rolling(
        window=window_days,
        min_periods=window_days,
    ).var(ddof=1)
    covariance_value = float(rolling_covariance.iloc[-1])
    variance_value = float(rolling_variance.iloc[-1])

    if not np.isfinite(variance_value):
        raise PortfolioAnalyticsClientError(
            "Risk estimator variance computation produced non-finite values.",
            status_code=422,
        )

    if variance_value == 0.0:
        raise PortfolioAnalyticsClientError(
            "Risk estimator regression failed because proxy return variance is zero.",
            status_code=422,
        )

    try:
        regression_result = stats.linregress(
            proxy_window.to_numpy(dtype=np.float64),
            portfolio_window.to_numpy(dtype=np.float64),
        )
    except ValueError as exc:
        raise PortfolioAnalyticsClientError(
            "Risk estimator regression failed due to invalid input domain.",
            status_code=422,
        ) from exc
    if not np.isfinite(regression_result.slope):
        raise PortfolioAnalyticsClientError(
            "Risk estimator regression produced a non-finite beta slope.",
            status_code=422,
        )
    beta_from_covariance = covariance_value / variance_value
    beta = float(regression_result.slope)
    if np.isfinite(beta_from_covariance):
        beta = float((beta + beta_from_covariance) / 2.0)

    downside_returns = portfolio_window[portfolio_window < 0]
    if len(downside_returns) >= 2:
        downside_std = float(downside_returns.std(ddof=1))
    else:
        downside_std = 0.0
    downside_deviation_annualized = downside_std * float(np.sqrt(252.0))

    value_at_risk_95 = float(portfolio_window.quantile(0.05))
    tail_returns = portfolio_window[portfolio_window <= value_at_risk_95]
    expected_shortfall_95 = (
        float(tail_returns.mean()) if len(tail_returns) > 0 else value_at_risk_95
    )

    for metric_value, metric_field in (
        (downside_deviation_annualized, "downside_deviation_annualized"),
        (value_at_risk_95, "value_at_risk_95"),
        (expected_shortfall_95, "expected_shortfall_95"),
    ):
        if not np.isfinite(metric_value):
            raise PortfolioAnalyticsClientError(
                f"Risk estimator {metric_field} produced a non-finite value.",
                status_code=422,
            )

    return {
        "volatility_annualized": _decimal_from_float(
            value=volatility_annualized,
            field="volatility_annualized",
        ),
        "max_drawdown": _decimal_from_float(
            value=max_drawdown,
            field="max_drawdown",
        ),
        "beta": _decimal_from_float(
            value=beta,
            field="beta",
        ),
        "downside_deviation_annualized": _decimal_from_float(
            value=downside_deviation_annualized,
            field="downside_deviation_annualized",
        ),
        "value_at_risk_95": _decimal_from_float(
            value=value_at_risk_95,
            field="value_at_risk_95",
        ),
        "expected_shortfall_95": _decimal_from_float(
            value=expected_shortfall_95,
            field="expected_shortfall_95",
        ),
    }


def _validate_aligned_timestamp_index(*, aligned_timestamps: Sequence[datetime]) -> None:
    """Validate UTC-aware monotonic event-time index without implicit calendar coercion."""

    if not aligned_timestamps:
        raise PortfolioAnalyticsClientError(
            "Risk estimator preprocessing requires non-empty aligned timestamps.",
            status_code=422,
        )

    normalized_timestamps: list[datetime] = []
    for timestamp in aligned_timestamps:
        if timestamp.tzinfo is None:
            raise PortfolioAnalyticsClientError(
                "Risk estimator preprocessing requires timezone-aware timestamps.",
                status_code=422,
            )
        if timestamp.utcoffset() != timedelta(0):
            raise PortfolioAnalyticsClientError(
                "Risk estimator preprocessing requires UTC-aligned timestamps.",
                status_code=422,
            )
        normalized_timestamps.append(timestamp.astimezone(UTC))

    for previous_timestamp, current_timestamp in pairwise(normalized_timestamps):
        if current_timestamp <= previous_timestamp:
            raise PortfolioAnalyticsClientError(
                "Risk estimator preprocessing requires strictly sorted timestamps.",
                status_code=422,
            )


def _resolve_benchmark_price_series_by_id(
    *,
    aligned_timestamps: Sequence[datetime],
    candidate_price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
) -> dict[str, dict[datetime, Decimal]]:
    """Resolve optional benchmark series with full aligned timestamp coverage."""

    resolved_series_by_id: dict[str, dict[datetime, Decimal]] = {}
    if not aligned_timestamps:
        return resolved_series_by_id

    for (
        benchmark_field,
        candidate_symbols,
    ) in _BENCHMARK_CANDIDATE_SYMBOLS_BY_ID.items():
        for candidate_symbol in candidate_symbols:
            symbol_series = candidate_price_series_by_symbol.get(candidate_symbol)
            if symbol_series is None:
                continue

            if any(timestamp not in symbol_series for timestamp in aligned_timestamps):
                continue

            resolved_series_by_id[benchmark_field] = {
                timestamp: symbol_series[timestamp] for timestamp in aligned_timestamps
            }
            break

    return resolved_series_by_id


def build_portfolio_time_series_points(
    *,
    aligned_timestamps: Sequence[datetime],
    open_quantity_by_symbol: Mapping[str, Decimal],
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    total_open_cost_basis_usd: Decimal,
    benchmark_price_series_by_id: Mapping[str, Mapping[datetime, Decimal]],
) -> list[dict[str, object]]:
    """Build deterministic time-series points from open-position pricing history."""

    points: list[dict[str, object]] = []
    portfolio_values_by_timestamp: dict[datetime, Decimal] = {}
    ordered_symbols = sorted(open_quantity_by_symbol)
    for captured_at in aligned_timestamps:
        portfolio_value_usd = Decimal("0")
        for symbol in ordered_symbols:
            symbol_price_series = price_series_by_symbol.get(symbol)
            if symbol_price_series is None or captured_at not in symbol_price_series:
                raise PortfolioAnalyticsClientError(
                    "Aligned time-series computation found missing symbol coverage.",
                    status_code=422,
                )
            portfolio_value_usd += (
                open_quantity_by_symbol[symbol] * symbol_price_series[captured_at]
            )

        portfolio_values_by_timestamp[captured_at] = portfolio_value_usd

    if not aligned_timestamps:
        return points

    first_timestamp = aligned_timestamps[0]
    portfolio_start_value_usd = portfolio_values_by_timestamp[first_timestamp]

    benchmark_value_series_by_id: dict[str, dict[datetime, Decimal]] = {}
    for benchmark_field, benchmark_price_series in benchmark_price_series_by_id.items():
        start_price = benchmark_price_series.get(first_timestamp)
        if start_price is None or start_price <= Decimal("0"):
            continue

        normalized_series: dict[datetime, Decimal] = {}
        for timestamp in aligned_timestamps:
            benchmark_price = benchmark_price_series.get(timestamp)
            if benchmark_price is None:
                normalized_series = {}
                break
            normalized_series[timestamp] = portfolio_start_value_usd * (
                benchmark_price / start_price
            )
        if normalized_series:
            benchmark_value_series_by_id[benchmark_field] = normalized_series

    for captured_at in aligned_timestamps:
        portfolio_value_usd = portfolio_values_by_timestamp[captured_at]
        pnl_usd = portfolio_value_usd - total_open_cost_basis_usd

        point_payload: dict[str, object] = {
            "captured_at": captured_at,
            "portfolio_value_usd": _quantize_money(portfolio_value_usd),
            "pnl_usd": _quantize_money(pnl_usd),
            "benchmark_sp500_value_usd": None,
            "benchmark_nasdaq100_value_usd": None,
        }

        for benchmark_field, normalized_series in benchmark_value_series_by_id.items():
            point_payload[benchmark_field] = _quantize_money(normalized_series[captured_at])

        points.append(point_payload)
    return points


def build_portfolio_contribution_rows(
    *,
    aligned_timestamps: Sequence[datetime],
    open_quantity_by_symbol: Mapping[str, Decimal],
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
) -> list[dict[str, object]]:
    """Build deterministic contribution rows from period start/end valuations."""

    start_timestamp = aligned_timestamps[0]
    end_timestamp = aligned_timestamps[-1]
    contribution_pnl_usd_by_symbol: dict[str, Decimal] = {}
    for symbol in sorted(open_quantity_by_symbol):
        symbol_series = price_series_by_symbol.get(symbol)
        if symbol_series is None:
            raise PortfolioAnalyticsClientError(
                "Contribution computation found missing symbol price series.",
                status_code=422,
            )
        start_price = symbol_series.get(start_timestamp)
        end_price = symbol_series.get(end_timestamp)
        if start_price is None or end_price is None:
            raise PortfolioAnalyticsClientError(
                "Contribution computation found missing aligned symbol price point.",
                status_code=422,
            )
        contribution_pnl_usd_by_symbol[symbol] = open_quantity_by_symbol[symbol] * (
            end_price - start_price
        )

    total_contribution_pnl = sum(
        contribution_pnl_usd_by_symbol.values(),
        start=Decimal("0"),
    )
    rows: list[dict[str, object]] = []
    for symbol in sorted(contribution_pnl_usd_by_symbol):
        contribution_pnl_usd = contribution_pnl_usd_by_symbol[symbol]
        contribution_pct = Decimal("0")
        if total_contribution_pnl != Decimal("0"):
            contribution_pct = (contribution_pnl_usd / total_contribution_pnl) * Decimal("100")
        rows.append(
            {
                "instrument_symbol": symbol,
                "contribution_pnl_usd": _quantize_money(contribution_pnl_usd),
                "contribution_pct": contribution_pct.quantize(_PCT_SCALE),
            }
        )
    return rows


def _build_portfolio_returns_series(
    *,
    aligned_timestamps: Sequence[datetime],
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    open_quantity_by_symbol: Mapping[str, Decimal],
    insufficient_history_detail: str,
) -> pd.Series:
    """Build one portfolio returns series from aligned symbol prices and open quantities."""

    price_frame = _build_aligned_price_frame(
        aligned_timestamps=aligned_timestamps,
        price_series_by_symbol=price_series_by_symbol,
    )
    ordered_symbols = [str(column_name) for column_name in price_frame.columns]
    quantity_vector_values = [
        float(
            _coerce_decimal(
                value=open_quantity_by_symbol[symbol],
                field="open_quantity",
                context="quant_metrics_preprocessing",
            )
        )
        for symbol in ordered_symbols
    ]
    quantity_vector = np.array(
        quantity_vector_values,
        dtype=np.float64,
    )
    portfolio_values = np.matmul(
        price_frame.to_numpy(dtype=np.float64),
        quantity_vector,
    )
    return _build_returns_series_from_values(
        values=portfolio_values,
        timestamps=list(price_frame.index),
        series_name="portfolio_value",
        insufficient_history_detail=insufficient_history_detail,
        positive_values_error_detail=(
            "Quant metrics require positive historical portfolio values to compute returns."
        ),
        non_finite_values_error_detail=("Quant metrics require finite aligned return values."),
    )


def _build_returns_series_from_values(
    *,
    values: Sequence[float],
    timestamps: Sequence[datetime],
    series_name: str,
    insufficient_history_detail: str,
    positive_values_error_detail: str,
    non_finite_values_error_detail: str,
) -> pd.Series:
    """Build one finite returns series from timestamp-aligned positive value points."""

    if len(values) != len(timestamps):
        raise PortfolioAnalyticsClientError(
            "Return-series preprocessing requires aligned values and timestamps.",
            status_code=422,
        )
    if len(values) < 2:
        raise PortfolioAnalyticsClientError(
            insufficient_history_detail,
            status_code=409,
        )
    value_array = np.array(values, dtype=np.float64)
    if np.any(value_array <= 0):
        raise PortfolioAnalyticsClientError(
            positive_values_error_detail,
            status_code=409,
        )
    value_series = pd.Series(
        value_array,
        index=pd.DatetimeIndex(list(timestamps)),
        name=series_name,
        dtype=np.float64,
    )
    returns_series = value_series.pct_change().dropna()
    if returns_series.empty:
        raise PortfolioAnalyticsClientError(
            insufficient_history_detail,
            status_code=409,
        )
    if not np.isfinite(returns_series.to_numpy(dtype=np.float64)).all():
        raise PortfolioAnalyticsClientError(
            non_finite_values_error_detail,
            status_code=422,
        )
    return returns_series


def _build_scope_value_series_result(
    *,
    scope: PortfolioQuantReportScope,
    period: PortfolioChartPeriod,
    instrument_symbol: str | None,
    open_quantity_by_symbol: Mapping[str, Decimal],
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    optional_price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    context_label: str,
) -> _ScopedValueSeriesResult:
    """Build deterministic value/return series for portfolio or instrument scope."""

    required_points = _PERIOD_TO_REQUIRED_POINTS[period]
    minimum_timestamp = _resolve_period_minimum_timestamp(period=period)
    insufficient_history_detail = (
        f"Insufficient persisted history for {context_label} period {period.value}."
    )
    candidate_price_series_by_symbol: dict[str, Mapping[datetime, Decimal]] = {
        **optional_price_series_by_symbol,
        **price_series_by_symbol,
    }

    if scope == PortfolioQuantReportScope.PORTFOLIO:
        aligned_timestamps = _select_aligned_timestamps(
            price_series_by_symbol=price_series_by_symbol,
            required_points=required_points,
            minimum_points=2,
            minimum_timestamp=minimum_timestamp,
            insufficient_history_detail=insufficient_history_detail,
        )
        price_frame = _build_aligned_price_frame(
            aligned_timestamps=aligned_timestamps,
            price_series_by_symbol=price_series_by_symbol,
        )
        ordered_symbols = [str(column_name) for column_name in price_frame.columns]
        quantity_vector_values: list[float] = []
        for symbol in ordered_symbols:
            if symbol not in open_quantity_by_symbol:
                raise PortfolioAnalyticsClientError(
                    "Scope-series preprocessing found symbol alignment mismatch.",
                    status_code=422,
                )
            normalized_quantity = _coerce_decimal(
                value=open_quantity_by_symbol[symbol],
                field="open_quantity",
                context="scope_series_preprocessing",
            )
            if normalized_quantity <= Decimal("0"):
                raise PortfolioAnalyticsClientError(
                    "Scope-series preprocessing requires positive open quantities.",
                    status_code=422,
                )
            quantity_vector_values.append(float(normalized_quantity))
        quantity_vector = np.array(quantity_vector_values, dtype=np.float64)
        portfolio_values = np.matmul(
            price_frame.to_numpy(dtype=np.float64),
            quantity_vector,
        )
        value_series = pd.Series(
            portfolio_values,
            index=price_frame.index,
            name="portfolio_value",
            dtype=np.float64,
        )
        returns_series = _build_returns_series_from_values(
            values=portfolio_values,
            timestamps=list(price_frame.index),
            series_name="portfolio_value",
            insufficient_history_detail=insufficient_history_detail,
            positive_values_error_detail=(
                f"{context_label.title()} requires positive historical portfolio values "
                "to compute returns."
            ),
            non_finite_values_error_detail=(
                f"{context_label.title()} requires finite aligned return values."
            ),
        )
        return _ScopedValueSeriesResult(
            scope=scope,
            instrument_symbol=None,
            aligned_timestamps=list(aligned_timestamps),
            value_series=value_series,
            returns_series=returns_series,
            candidate_price_series_by_symbol=candidate_price_series_by_symbol,
        )

    if instrument_symbol is None:
        raise PortfolioAnalyticsClientError(
            "instrument_symbol is required when chart scope is 'instrument_symbol'.",
            status_code=422,
        )

    symbol_series = candidate_price_series_by_symbol.get(instrument_symbol)
    if symbol_series is None:
        raise PortfolioAnalyticsClientError(
            "No persisted market-data history is available for requested symbol "
            f"'{instrument_symbol}'.",
            status_code=409,
        )
    aligned_timestamps = _select_aligned_timestamps(
        price_series_by_symbol={instrument_symbol: symbol_series},
        required_points=required_points,
        minimum_points=2,
        minimum_timestamp=minimum_timestamp,
        insufficient_history_detail=insufficient_history_detail,
    )
    symbol_values = [
        float(
            _coerce_decimal(
                value=symbol_series[timestamp],
                field="price_value",
                context="scope_symbol_preprocessing",
            )
        )
        for timestamp in aligned_timestamps
    ]
    value_series = pd.Series(
        symbol_values,
        index=pd.DatetimeIndex(list(aligned_timestamps)),
        name=instrument_symbol,
        dtype=np.float64,
    )
    returns_series = _build_returns_series_from_values(
        values=symbol_values,
        timestamps=aligned_timestamps,
        series_name=instrument_symbol,
        insufficient_history_detail=insufficient_history_detail,
        positive_values_error_detail=(
            f"{context_label.title()} requires positive historical symbol values to compute "
            "returns."
        ),
        non_finite_values_error_detail=(
            f"{context_label.title()} requires finite aligned return values."
        ),
    )
    return _ScopedValueSeriesResult(
        scope=scope,
        instrument_symbol=instrument_symbol,
        aligned_timestamps=list(aligned_timestamps),
        value_series=value_series,
        returns_series=returns_series,
        candidate_price_series_by_symbol=candidate_price_series_by_symbol,
    )


def _build_scope_proxy_returns_series_for_beta(
    *,
    scope: PortfolioQuantReportScope,
    instrument_symbol: str | None,
    aligned_timestamps: Sequence[datetime],
    open_price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    candidate_price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    primary_returns_series: pd.Series,
) -> pd.Series | None:
    """Build one proxy return series compatible with rolling beta computation."""

    if scope == PortfolioQuantReportScope.PORTFOLIO:
        proxy_returns = _build_equal_weight_proxy_returns(
            aligned_timestamps=aligned_timestamps,
            price_series_by_symbol=open_price_series_by_symbol,
        )
        if not proxy_returns:
            return None
        proxy_series = pd.Series(
            [float(return_value) for return_value in proxy_returns],
            index=pd.DatetimeIndex(list(aligned_timestamps)[1:]),
            dtype=np.float64,
            name="proxy",
        )
    else:
        if instrument_symbol is None:
            return None
        benchmark_symbol, benchmark_returns = _select_quantstats_benchmark_returns(
            aligned_timestamps=aligned_timestamps,
            benchmark_price_series_by_id=_resolve_benchmark_price_series_by_id(
                aligned_timestamps=aligned_timestamps,
                candidate_price_series_by_symbol=candidate_price_series_by_symbol,
            ),
        )
        _ = benchmark_symbol
        if benchmark_returns is None:
            return None
        proxy_series = benchmark_returns

    shared_index = primary_returns_series.index.intersection(proxy_series.index)
    if len(shared_index) < 2:
        return None
    aligned_proxy = proxy_series.loc[shared_index]
    if not np.isfinite(aligned_proxy.to_numpy(dtype=np.float64)).all():
        return None
    return aligned_proxy


def _build_rolling_beta_series(
    *,
    returns_series: pd.Series,
    proxy_returns_series: pd.Series | None,
    window_days: int,
) -> pd.Series:
    """Build rolling beta series with explicit zero-variance and NaN handling."""

    if proxy_returns_series is None:
        return pd.Series(np.nan, index=returns_series.index, dtype=np.float64)

    aligned_frame = pd.concat(
        [
            returns_series.rename("portfolio"),
            proxy_returns_series.rename("proxy"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    if len(aligned_frame) < window_days:
        return pd.Series(np.nan, index=returns_series.index, dtype=np.float64)

    rolling_covariance = (
        aligned_frame["portfolio"]
        .rolling(
            window=window_days,
            min_periods=window_days,
        )
        .cov(aligned_frame["proxy"])
    )
    rolling_variance = (
        aligned_frame["proxy"]
        .rolling(
            window=window_days,
            min_periods=window_days,
        )
        .var(ddof=1)
    )
    rolling_beta = rolling_covariance / rolling_variance.replace(0.0, np.nan)
    rolling_beta = rolling_beta.replace([np.inf, -np.inf], np.nan)
    return rolling_beta.reindex(returns_series.index)


def _resolve_risk_metric_unit(
    *,
    estimator_id: str,
) -> Literal["percent", "ratio", "unitless"]:
    """Resolve one risk metric display unit from estimator identifier."""

    normalized_estimator_id = estimator_id.lower()
    if (
        "volatility" in normalized_estimator_id
        or "drawdown" in normalized_estimator_id
        or "downside_deviation" in normalized_estimator_id
        or "value_at_risk" in normalized_estimator_id
        or "shortfall" in normalized_estimator_id
    ):
        return "percent"
    if "beta" in normalized_estimator_id:
        return "ratio"
    return "unitless"


def _resolve_risk_interpretation_band(
    *,
    estimator_id: str,
    value: Decimal,
) -> Literal["favorable", "caution", "elevated_risk"]:
    """Resolve threshold-aware interpretation band for one risk metric value."""

    normalized_estimator_id = estimator_id.lower()
    numeric_value = float(value)
    absolute_value = abs(numeric_value)

    if "max_drawdown" in normalized_estimator_id:
        if absolute_value <= 0.10:
            return "favorable"
        if absolute_value <= 0.20:
            return "caution"
        return "elevated_risk"
    if "volatility_annualized" in normalized_estimator_id:
        if absolute_value <= 0.15:
            return "favorable"
        if absolute_value <= 0.25:
            return "caution"
        return "elevated_risk"
    if "beta" in normalized_estimator_id:
        if 0.8 <= numeric_value <= 1.2:
            return "favorable"
        if 0.6 <= numeric_value < 0.8 or 1.2 < numeric_value <= 1.4:
            return "caution"
        return "elevated_risk"
    if "value_at_risk_95" in normalized_estimator_id:
        if absolute_value <= 0.02:
            return "favorable"
        if absolute_value <= 0.05:
            return "caution"
        return "elevated_risk"
    if "expected_shortfall_95" in normalized_estimator_id:
        if absolute_value <= 0.03:
            return "favorable"
        if absolute_value <= 0.06:
            return "caution"
        return "elevated_risk"
    if "downside_deviation_annualized" in normalized_estimator_id:
        if absolute_value <= 0.10:
            return "favorable"
        if absolute_value <= 0.20:
            return "caution"
        return "elevated_risk"

    return "caution"


def _resolve_risk_band_health_contribution(
    *,
    interpretation_band: Literal["favorable", "caution", "elevated_risk"],
) -> tuple[Literal["supporting", "neutral", "penalizing"], Literal["low", "moderate", "high"]]:
    """Map one risk interpretation band into health-contribution metadata."""

    if interpretation_band == "favorable":
        return ("supporting", "low")
    if interpretation_band == "elevated_risk":
        return ("penalizing", "high")
    return ("neutral", "moderate")


def _score_positive_metric(value: float, thresholds: tuple[float, float, float, float]) -> int:
    """Score one higher-is-better metric into bounded 0..100 band."""

    high, medium_high, medium_low, low = thresholds
    if value >= high:
        return 100
    if value >= medium_high:
        return 80
    if value >= medium_low:
        return 60
    if value >= low:
        return 45
    if value >= 0.0:
        return 35
    return 20


def _score_negative_metric(
    absolute_value: float,
    thresholds: tuple[float, float, float, float],
) -> int:
    """Score one lower-is-better metric into bounded 0..100 band."""

    low, medium_low, medium_high, high = thresholds
    if absolute_value <= low:
        return 100
    if absolute_value <= medium_low:
        return 80
    if absolute_value <= medium_high:
        return 60
    if absolute_value <= high:
        return 40
    return 20


def _resolve_health_pillar_status(*, score: int) -> PortfolioHealthPillarStatus:
    """Resolve one health-pillar status from integer pillar score."""

    if score >= 70:
        return PortfolioHealthPillarStatus.FAVORABLE
    if score >= 45:
        return PortfolioHealthPillarStatus.CAUTION
    return PortfolioHealthPillarStatus.ELEVATED_RISK


def _resolve_health_metric_contribution(
    *, score: int
) -> Literal["supporting", "neutral", "penalizing"]:
    """Resolve one metric contribution direction from normalized score."""

    if score >= 60:
        return "supporting"
    if score <= 40:
        return "penalizing"
    return "neutral"


def _resolve_health_label_from_score(
    *,
    health_score: int,
    critical_override_count: int,
) -> PortfolioHealthLabel:
    """Resolve aggregate health label from score and critical override policy."""

    if critical_override_count >= 2:
        return PortfolioHealthLabel.STRESSED
    if health_score < 45:
        return PortfolioHealthLabel.STRESSED
    if critical_override_count == 1:
        return PortfolioHealthLabel.WATCHLIST
    if health_score <= 69:
        return PortfolioHealthLabel.WATCHLIST
    return PortfolioHealthLabel.HEALTHY


def _compute_health_score_from_pillar_scores(
    *,
    pillar_scores: (
        Mapping[str, int]
        | Mapping[Literal["growth", "risk", "risk_adjusted_quality", "resilience"], int]
    ),
    profile_posture: PortfolioHealthProfilePosture,
) -> int:
    """Compute deterministic aggregate health score from profile-weighted pillars."""

    weights = _HEALTH_PROFILE_WEIGHTS[profile_posture]
    weighted_score = (
        Decimal(str(pillar_scores.get("growth", 0))) * weights[0]
        + Decimal(str(pillar_scores.get("risk", 0))) * weights[1]
        + Decimal(str(pillar_scores.get("risk_adjusted_quality", 0))) * weights[2]
        + Decimal(str(pillar_scores.get("resilience", 0))) * weights[3]
    )
    return max(0, min(100, round(float(weighted_score))))


def _format_health_value_display(
    *,
    value: float,
    display_as: Literal["percent", "number", "days"],
    signed_percent: bool = True,
) -> str:
    """Format one health metric value for deterministic UI consumption."""

    if display_as == "percent":
        percent_value = value * 100.0
        sign_prefix = "+" if signed_percent and percent_value > 0 else ""
        return f"{sign_prefix}{percent_value:.2f}%"
    if display_as == "days":
        return f"{round(value)} days"
    return f"{value:.3f}"


def _resolve_health_rationale(
    *,
    metric_id: str,
    value: float,
    contribution: Literal["supporting", "neutral", "penalizing"],
) -> str:
    """Resolve concise deterministic rationale for one health metric driver."""

    if metric_id == "max_drawdown":
        if contribution == "penalizing":
            return "Drawdown depth is materially above conservative tolerance."
        if contribution == "supporting":
            return "Drawdown depth remains contained versus common risk bands."
        return "Drawdown depth is moderate for this period."
    if metric_id == "volatility_annualized":
        if contribution == "penalizing":
            return "Annualized volatility indicates elevated dispersion risk."
        if contribution == "supporting":
            return "Annualized volatility remains within a controlled band."
        return "Annualized volatility is neither clearly low nor clearly elevated."
    if metric_id in {"sharpe_ratio", "sortino_ratio", "calmar_ratio"}:
        if contribution == "penalizing":
            return "Risk-adjusted efficiency is weak for this observation window."
        if contribution == "supporting":
            return "Risk-adjusted efficiency supports the current return profile."
        return "Risk-adjusted efficiency is moderate for this period."
    if metric_id in {"cagr", "cumulative_return"}:
        if contribution == "penalizing":
            return "Growth output is below healthy long-term targets."
        if contribution == "supporting":
            return "Growth output is strong versus long-term target bands."
        return "Growth output is stable but not dominant in this window."
    if metric_id == "expected_shortfall_95":
        if contribution == "penalizing":
            return "Tail-loss severity is elevated in adverse scenarios."
        if contribution == "supporting":
            return "Tail-loss severity remains controlled in adverse scenarios."
        return "Tail-loss severity is moderate for this period."
    if metric_id == "recovery_factor":
        if contribution == "penalizing":
            return "Recovery efficiency after drawdowns is limited."
        if contribution == "supporting":
            return "Recovery efficiency after drawdowns is healthy."
        return "Recovery efficiency is neutral for this period."
    if metric_id == "longest_drawdown_days":
        if contribution == "penalizing":
            return "Capital spent extended time below prior peaks."
        if contribution == "supporting":
            return "Recovery windows are relatively short."
        return "Recovery duration is moderate for this period."
    if metric_id == "win_month":
        if contribution == "penalizing":
            return "Monthly consistency is weak in the selected lookback."
        if contribution == "supporting":
            return "Monthly consistency is supportive of portfolio resilience."
        return "Monthly consistency is balanced in this period."
    _ = value
    return "Metric contributes neutral signal under current threshold policy."


def _calculate_longest_drawdown_days(*, drawdown_series: pd.Series) -> int:
    """Calculate longest consecutive drawdown duration in days."""

    if drawdown_series.empty:
        return 0

    longest_span = 0
    current_span = 0
    for drawdown_value in drawdown_series.to_numpy(dtype=np.float64):
        if drawdown_value < 0:
            current_span += 1
            longest_span = max(longest_span, current_span)
        else:
            current_span = 0
    return longest_span


def _build_health_pillars_and_drivers(
    *,
    value_series: pd.Series,
    returns_series: pd.Series,
) -> tuple[list[PortfolioHealthPillar], list[PortfolioHealthDriver], list[str], int]:
    """Build deterministic health pillars, key drivers, caveats, and override counts."""

    returns_values = returns_series.to_numpy(dtype=np.float64)
    if not np.isfinite(returns_values).all():
        raise PortfolioAnalyticsClientError(
            "Health synthesis requires finite return values.",
            status_code=422,
        )
    if len(returns_values) < 2:
        raise PortfolioAnalyticsClientError(
            "Health synthesis requires at least two return observations.",
            status_code=409,
        )

    start_value = float(value_series.iloc[0])
    end_value = float(value_series.iloc[-1])
    if start_value <= 0 or end_value <= 0:
        raise PortfolioAnalyticsClientError(
            "Health synthesis requires positive portfolio values.",
            status_code=409,
        )

    caveats: list[str] = [
        "Health synthesis supports interpretation and is not financial advice.",
    ]
    cumulative_return = (end_value / start_value) - 1.0
    years = max(len(returns_values) / 252.0, 1.0 / 252.0)
    cagr = (1.0 + cumulative_return) ** (1.0 / years) - 1.0
    one_year_return: float | None = None
    if len(returns_values) >= 252:
        one_year_return = float(np.prod(1.0 + returns_values[-252:]) - 1.0)
    else:
        caveats.append(
            "One-year return is omitted because fewer than 252 return days are available."
        )

    three_year_annualized_return: float | None = None
    if len(returns_values) >= 756:
        compounded_three_year = float(np.prod(1.0 + returns_values[-756:]) - 1.0)
        three_year_annualized_return = (1.0 + compounded_three_year) ** (252.0 / 756.0) - 1.0
    else:
        caveats.append(
            "Three-year annualized return is omitted because fewer than 756 return days are available."
        )

    volatility_annualized = float(np.std(returns_values, ddof=1) * np.sqrt(252.0))
    drawdown_series = (value_series / value_series.cummax()) - 1.0
    max_drawdown = float(drawdown_series.min())
    value_at_risk_95 = float(np.quantile(returns_values, 0.05))
    expected_shortfall_values = returns_values[returns_values <= value_at_risk_95]
    if expected_shortfall_values.size == 0:
        expected_shortfall_values = np.array([value_at_risk_95], dtype=np.float64)
    expected_shortfall_95 = float(np.mean(expected_shortfall_values))

    mean_return = float(np.mean(returns_values))
    volatility_daily = float(np.std(returns_values, ddof=1))
    sharpe_ratio = (
        0.0 if volatility_daily <= 0 else (mean_return / volatility_daily) * np.sqrt(252.0)
    )
    downside_values = returns_values[returns_values < 0.0]
    downside_deviation = float(np.std(downside_values, ddof=1)) if downside_values.size > 1 else 0.0
    sortino_ratio = (
        0.0 if downside_deviation <= 0.0 else (mean_return / downside_deviation) * np.sqrt(252.0)
    )
    calmar_ratio = 0.0 if max_drawdown == 0 else cagr / abs(max_drawdown)

    recovery_factor = 0.0 if max_drawdown == 0 else cumulative_return / abs(max_drawdown)
    longest_drawdown_days = _calculate_longest_drawdown_days(drawdown_series=drawdown_series)
    monthly_returns = returns_series.add(1.0).resample("ME").prod().sub(1.0).dropna()
    if len(monthly_returns) == 0:
        win_month = float(np.mean(returns_values > 0.0))
        caveats.append("Monthly win rate used daily fallback due to sparse month-end observations.")
    else:
        win_month = float(np.mean(monthly_returns.to_numpy(dtype=np.float64) > 0.0))

    def _metric(
        *,
        metric_id: str,
        label: str,
        raw_value: float,
        score: int,
        display_as: Literal["percent", "number", "days"],
    ) -> _HealthMetricEvaluation:
        contribution = _resolve_health_metric_contribution(score=score)
        return _HealthMetricEvaluation(
            metric_id=metric_id,
            label=label,
            raw_value=raw_value,
            score=score,
            value_display=_format_health_value_display(
                value=raw_value,
                display_as=display_as,
                signed_percent=(display_as == "percent"),
            ),
            contribution=contribution,
            rationale=_resolve_health_rationale(
                metric_id=metric_id,
                value=raw_value,
                contribution=contribution,
            ),
        )

    growth_metrics: list[_HealthMetricEvaluation] = [
        _metric(
            metric_id="cagr",
            label="CAGR",
            raw_value=cagr,
            score=_score_positive_metric(cagr, (0.15, 0.12, 0.08, 0.05)),
            display_as="percent",
        ),
        _metric(
            metric_id="cumulative_return",
            label="Cumulative Return",
            raw_value=cumulative_return,
            score=_score_positive_metric(cumulative_return, (0.60, 0.30, 0.10, 0.00)),
            display_as="percent",
        ),
    ]
    if one_year_return is not None:
        growth_metrics.append(
            _metric(
                metric_id="one_year_return",
                label="1Y Return",
                raw_value=one_year_return,
                score=_score_positive_metric(one_year_return, (0.20, 0.12, 0.05, 0.00)),
                display_as="percent",
            )
        )
    if three_year_annualized_return is not None:
        growth_metrics.append(
            _metric(
                metric_id="three_year_annualized_return",
                label="3Y Annualized Return",
                raw_value=three_year_annualized_return,
                score=_score_positive_metric(
                    three_year_annualized_return,
                    (0.15, 0.10, 0.06, 0.00),
                ),
                display_as="percent",
            )
        )

    risk_metrics: list[_HealthMetricEvaluation] = [
        _metric(
            metric_id="max_drawdown",
            label="Max Drawdown",
            raw_value=max_drawdown,
            score=_score_negative_metric(abs(max_drawdown), (0.10, 0.20, 0.30, 0.45)),
            display_as="percent",
        ),
        _metric(
            metric_id="volatility_annualized",
            label="Volatility (Ann.)",
            raw_value=volatility_annualized,
            score=_score_negative_metric(volatility_annualized, (0.15, 0.25, 0.35, 0.50)),
            display_as="percent",
        ),
        _metric(
            metric_id="expected_shortfall_95",
            label="Expected Shortfall (95%)",
            raw_value=expected_shortfall_95,
            score=_score_negative_metric(abs(expected_shortfall_95), (0.03, 0.06, 0.10, 0.15)),
            display_as="percent",
        ),
        _metric(
            metric_id="value_at_risk_95",
            label="Value at Risk (95%)",
            raw_value=value_at_risk_95,
            score=_score_negative_metric(abs(value_at_risk_95), (0.02, 0.05, 0.08, 0.12)),
            display_as="percent",
        ),
    ]

    quality_metrics: list[_HealthMetricEvaluation] = [
        _metric(
            metric_id="sharpe_ratio",
            label="Sharpe Ratio",
            raw_value=sharpe_ratio,
            score=_score_positive_metric(sharpe_ratio, (1.20, 0.70, 0.30, 0.00)),
            display_as="number",
        ),
        _metric(
            metric_id="sortino_ratio",
            label="Sortino Ratio",
            raw_value=sortino_ratio,
            score=_score_positive_metric(sortino_ratio, (1.50, 1.00, 0.50, 0.00)),
            display_as="number",
        ),
        _metric(
            metric_id="calmar_ratio",
            label="Calmar Ratio",
            raw_value=calmar_ratio,
            score=_score_positive_metric(calmar_ratio, (1.00, 0.70, 0.30, 0.00)),
            display_as="number",
        ),
    ]

    resilience_metrics: list[_HealthMetricEvaluation] = [
        _metric(
            metric_id="recovery_factor",
            label="Recovery Factor",
            raw_value=recovery_factor,
            score=_score_positive_metric(recovery_factor, (3.00, 2.00, 1.00, 0.50)),
            display_as="number",
        ),
        _metric(
            metric_id="longest_drawdown_days",
            label="Longest Drawdown Days",
            raw_value=float(longest_drawdown_days),
            score=_score_negative_metric(
                float(longest_drawdown_days),
                (60.0, 180.0, 365.0, 540.0),
            ),
            display_as="days",
        ),
        _metric(
            metric_id="win_month",
            label="Win Month",
            raw_value=win_month,
            score=_score_positive_metric(win_month, (0.65, 0.55, 0.45, 0.35)),
            display_as="percent",
        ),
    ]

    def _pillar_score(metrics: Sequence[_HealthMetricEvaluation]) -> int:
        if not metrics:
            return 0
        score_value = float(sum(metric.score for metric in metrics)) / float(len(metrics))
        return max(0, min(100, round(score_value)))

    pillars_input: list[tuple[str, str, list[_HealthMetricEvaluation]]] = [
        ("growth", "Growth", growth_metrics),
        ("risk", "Risk", risk_metrics),
        ("risk_adjusted_quality", "Risk-adjusted quality", quality_metrics),
        ("resilience", "Resilience", resilience_metrics),
    ]
    pillars: list[PortfolioHealthPillar] = []
    all_metrics: list[_HealthMetricEvaluation] = []
    for pillar_id, label, metric_evaluations in pillars_input:
        all_metrics.extend(metric_evaluations)
        pillar_score = _pillar_score(metric_evaluations)
        pillars.append(
            PortfolioHealthPillar(
                pillar_id=cast(
                    Literal["growth", "risk", "risk_adjusted_quality", "resilience"],
                    pillar_id,
                ),
                label=label,
                score=pillar_score,
                status=_resolve_health_pillar_status(score=pillar_score),
                metrics=[
                    PortfolioHealthPillarMetric(
                        metric_id=metric.metric_id,
                        label=metric.label,
                        value_display=metric.value_display,
                        score=metric.score,
                        contribution=metric.contribution,
                    )
                    for metric in metric_evaluations
                ],
            )
        )

    critical_override_count = 0
    if abs(max_drawdown) > 0.30:
        critical_override_count += 1
    if abs(expected_shortfall_95) > 0.06:
        critical_override_count += 1
    if calmar_ratio < 0.3 and len(returns_values) >= 252:
        critical_override_count += 1
    if critical_override_count > 0:
        caveats.append(
            f"Critical risk override count: {critical_override_count}. Aggregate health label is constrained by risk guardrails."
        )

    sorted_metrics = sorted(
        all_metrics,
        key=lambda metric: (
            abs(metric.score - 50),
            metric.metric_id,
        ),
        reverse=True,
    )
    supporting_metrics = [
        metric for metric in sorted_metrics if metric.contribution == "supporting"
    ][:2]
    penalizing_metrics = [
        metric for metric in sorted_metrics if metric.contribution == "penalizing"
    ][:2]
    driver_rows: list[PortfolioHealthDriver] = []
    for metric in supporting_metrics:
        driver_rows.append(
            PortfolioHealthDriver(
                metric_id=metric.metric_id,
                label=metric.label,
                direction="supporting",
                impact_points=min(100, abs(metric.score - 50) * 2),
                rationale=metric.rationale,
                value_display=metric.value_display,
            )
        )
    for metric in penalizing_metrics:
        driver_rows.append(
            PortfolioHealthDriver(
                metric_id=metric.metric_id,
                label=metric.label,
                direction="penalizing",
                impact_points=min(100, abs(metric.score - 50) * 2),
                rationale=metric.rationale,
                value_display=metric.value_display,
            )
        )

    if not driver_rows:
        caveats.append(
            "No dominant health drivers were detected; review full metric ledger for nuance."
        )

    return (pillars, driver_rows, caveats, critical_override_count)


def _normalize_series_timestamp_to_utc(timestamp: object) -> datetime:
    """Normalize pandas/datetime timestamps to timezone-aware UTC datetimes."""

    if isinstance(timestamp, pd.Timestamp):
        normalized_timestamp = timestamp.to_pydatetime(warn=False)
    elif isinstance(timestamp, datetime):
        normalized_timestamp = timestamp
    else:
        raise PortfolioAnalyticsClientError(
            "Series timestamp normalization requires datetime-compatible index values.",
            status_code=422,
        )

    if normalized_timestamp.tzinfo is None:
        return normalized_timestamp.replace(tzinfo=UTC)
    return normalized_timestamp.astimezone(UTC)


def _to_optional_quantized_ratio(*, value: object, field: str) -> Decimal | None:
    """Convert optional scalar values into quantized ratios with finite validation."""

    if value is None:
        return None
    if isinstance(value, Decimal):
        numeric_value = float(value)
    elif isinstance(value, float):
        numeric_value = value
    elif isinstance(value, np.floating):
        numeric_value = float(value.item())
    else:
        return None
    if not np.isfinite(numeric_value):
        return None
    return _quantize_ratio(_decimal_from_float(value=numeric_value, field=field))


def _run_quantstats_monte_carlo(
    *,
    returns_series: pd.Series,
    sims: int,
    bust_threshold: Decimal | None,
    goal_threshold: Decimal | None,
    seed: int,
    quantstats_module: object | None = None,
) -> object:
    """Run QuantStats Monte Carlo simulation with explicit callable compatibility checks."""

    if not isinstance(returns_series.index, pd.DatetimeIndex):
        raise PortfolioAnalyticsClientError(
            "Monte Carlo simulation requires DatetimeIndex return series.",
            status_code=422,
        )
    if returns_series.empty:
        raise PortfolioAnalyticsClientError(
            "Monte Carlo simulation requires non-empty return history.",
            status_code=409,
        )
    if not np.isfinite(returns_series.to_numpy(dtype=np.float64)).all():
        raise PortfolioAnalyticsClientError(
            "Monte Carlo simulation requires finite aligned return values.",
            status_code=422,
        )

    runtime_module = (
        quantstats_module if quantstats_module is not None else _load_quantstats_module()
    )
    stats_module = getattr(runtime_module, "stats", None)
    if stats_module is None:
        raise PortfolioAnalyticsClientError(
            "QuantStats stats module is unavailable in runtime dependency.",
            status_code=500,
        )
    raw_callable = getattr(stats_module, "montecarlo", None)
    if raw_callable is None or not callable(raw_callable):
        raise PortfolioAnalyticsClientError(
            "QuantStats Monte Carlo callable 'montecarlo' is unavailable in runtime dependency.",
            status_code=500,
        )

    monte_carlo_callable: Callable[..., object] = raw_callable
    try:
        return monte_carlo_callable(
            returns_series,
            sims=sims,
            bust=float(bust_threshold) if bust_threshold is not None else None,
            goal=float(goal_threshold) if goal_threshold is not None else None,
            seed=seed,
        )
    except Exception as exc:
        raise PortfolioAnalyticsClientError(
            "Monte Carlo simulation failed for selected scope and period.",
            status_code=422,
        ) from exc


def _extract_monte_carlo_terminal_series(*, monte_carlo_result: object) -> pd.Series:
    """Extract terminal return distribution from QuantStats Monte Carlo result object."""

    raw_data = getattr(monte_carlo_result, "data", None)
    if not isinstance(raw_data, pd.DataFrame) or raw_data.empty:
        raise PortfolioAnalyticsClientError(
            "Monte Carlo result data is unavailable or invalid.",
            status_code=422,
        )
    terminal_series = raw_data.iloc[-1]
    if not np.isfinite(terminal_series.to_numpy(dtype=np.float64)).all():
        raise PortfolioAnalyticsClientError(
            "Monte Carlo terminal distribution contains non-finite values.",
            status_code=422,
        )
    return terminal_series.astype(np.float64)


def _extract_monte_carlo_percentile_values(
    *,
    terminal_series: pd.Series,
) -> dict[int, float]:
    """Extract deterministic percentile values from Monte Carlo terminal distribution."""

    return {
        5: float(terminal_series.quantile(0.05)),
        25: float(terminal_series.quantile(0.25)),
        50: float(terminal_series.quantile(0.50)),
        75: float(terminal_series.quantile(0.75)),
        95: float(terminal_series.quantile(0.95)),
    }


def _extract_optional_probability(
    *,
    monte_carlo_result: object,
    field_name: str,
) -> Decimal | None:
    """Extract optional probability fields from Monte Carlo result with finite checks."""

    raw_probability = getattr(monte_carlo_result, field_name, None)
    if raw_probability is None:
        return None
    if isinstance(raw_probability, Decimal):
        numeric_probability = float(raw_probability)
    elif isinstance(raw_probability, np.floating):
        numeric_probability = float(raw_probability.item())
    elif isinstance(raw_probability, (int, float)):
        numeric_probability = float(raw_probability)
    else:
        raise PortfolioAnalyticsClientError(
            f"Monte Carlo field '{field_name}' returned unsupported value type.",
            status_code=422,
        )
    if not np.isfinite(numeric_probability):
        raise PortfolioAnalyticsClientError(
            f"Monte Carlo field '{field_name}' returned non-finite value.",
            status_code=422,
        )
    if numeric_probability < 0.0 or numeric_probability > 1.0:
        raise PortfolioAnalyticsClientError(
            f"Monte Carlo field '{field_name}' must be in [0, 1].",
            status_code=422,
        )
    return _quantize_ratio(
        _decimal_from_float(
            value=numeric_probability,
            field=f"monte_carlo_{field_name}",
        )
    )


def _resolve_monte_carlo_signal_label(
    *,
    bust_probability: Decimal | None,
    goal_probability: Decimal | None,
) -> PortfolioMonteCarloSignal:
    """Resolve deterministic interpretation signal from bust/goal probabilities."""

    if bust_probability is None and goal_probability is None:
        return PortfolioMonteCarloSignal.MONITOR
    if bust_probability is not None and bust_probability >= Decimal("0.25"):
        return PortfolioMonteCarloSignal.DOWNSIDE_CAUTION
    if goal_probability is not None and goal_probability >= Decimal("0.50"):
        return PortfolioMonteCarloSignal.UPSIDE_FAVORABLE
    return PortfolioMonteCarloSignal.BALANCED


def _to_utc_datetime_or_none(timestamp: object) -> datetime | None:
    """Normalize optional pandas timestamps to timezone-aware UTC datetime."""

    if timestamp is None or not isinstance(timestamp, pd.Timestamp) or pd.isna(timestamp):
        return None
    normalized = timestamp.to_pydatetime()
    if normalized.tzinfo is None:
        return normalized.replace(tzinfo=UTC)
    return normalized.astimezone(UTC)


def _aggregate_returns_for_calibration(
    *,
    returns_series: pd.Series,
    calibration_basis: PortfolioMonteCarloCalibrationBasis,
) -> pd.Series:
    """Aggregate return series for calibration basis in a deterministic way."""

    if calibration_basis == PortfolioMonteCarloCalibrationBasis.MONTHLY:
        frequency = "ME"
    elif calibration_basis == PortfolioMonteCarloCalibrationBasis.ANNUAL:
        frequency = "YE"
    else:
        return pd.Series(dtype=np.float64)

    compounded_returns = returns_series.add(1.0).resample(frequency).prod().sub(1.0).dropna()
    if compounded_returns.empty:
        return pd.Series(dtype=np.float64)
    if not np.isfinite(compounded_returns.to_numpy(dtype=np.float64)).all():
        raise PortfolioAnalyticsClientError(
            "Monte Carlo profile calibration requires finite historical return values.",
            status_code=422,
        )
    return compounded_returns.astype(np.float64)


def _coerce_threshold_pair(
    *,
    bust_threshold: Decimal,
    goal_threshold: Decimal,
) -> tuple[Decimal, Decimal]:
    """Clamp bust/goal thresholds to envelope bounds and preserve strict ordering."""

    bounded_bust = min(Decimal("0"), max(Decimal("-0.95"), bust_threshold))
    bounded_goal = min(Decimal("3"), max(Decimal("0"), goal_threshold))
    if bounded_bust >= bounded_goal:
        bounded_goal = min(Decimal("3"), bounded_bust + Decimal("0.05"))
    if bounded_bust >= bounded_goal:
        bounded_bust = max(Decimal("-0.95"), bounded_goal - Decimal("0.05"))
    if bounded_bust >= bounded_goal:
        raise PortfolioAnalyticsClientError(
            "Monte Carlo profile thresholds must satisfy bust < goal after envelope bounds.",
            status_code=422,
        )
    return _quantize_ratio(bounded_bust), _quantize_ratio(bounded_goal)


def _resolve_monte_carlo_profile_thresholds(
    *,
    returns_series: pd.Series,
    calibration_basis: PortfolioMonteCarloCalibrationBasis,
    manual_bust_threshold: Decimal | None,
    manual_goal_threshold: Decimal | None,
) -> tuple[
    dict[PortfolioMonteCarloProfileId, tuple[Decimal, Decimal]],
    PortfolioMonteCarloCalibrationContext,
]:
    """Resolve profile threshold matrix and calibration metadata for Monte Carlo diagnostics."""

    if calibration_basis == PortfolioMonteCarloCalibrationBasis.MANUAL:
        balanced_defaults = _MONTE_CARLO_FALLBACK_PROFILE_THRESHOLDS[
            PortfolioMonteCarloProfileId.BALANCED
        ]
        base_bust = (
            manual_bust_threshold if manual_bust_threshold is not None else balanced_defaults[0]
        )
        base_goal = (
            manual_goal_threshold if manual_goal_threshold is not None else balanced_defaults[1]
        )
        profile_thresholds = {
            PortfolioMonteCarloProfileId.CONSERVATIVE: _coerce_threshold_pair(
                bust_threshold=base_bust + Decimal("0.08"),
                goal_threshold=base_goal - Decimal("0.08"),
            ),
            PortfolioMonteCarloProfileId.BALANCED: _coerce_threshold_pair(
                bust_threshold=base_bust,
                goal_threshold=base_goal,
            ),
            PortfolioMonteCarloProfileId.GROWTH: _coerce_threshold_pair(
                bust_threshold=base_bust - Decimal("0.10"),
                goal_threshold=base_goal + Decimal("0.15"),
            ),
        }
        lookback_start = _to_utc_datetime_or_none(returns_series.index.min())
        lookback_end = _to_utc_datetime_or_none(returns_series.index.max())
        return (
            profile_thresholds,
            PortfolioMonteCarloCalibrationContext(
                requested_basis=calibration_basis,
                effective_basis=PortfolioMonteCarloCalibrationBasis.MANUAL,
                sample_size=len(returns_series),
                lookback_start=lookback_start,
                lookback_end=lookback_end,
                used_fallback=False,
                fallback_reason=None,
            ),
        )

    aggregated_returns = _aggregate_returns_for_calibration(
        returns_series=returns_series,
        calibration_basis=calibration_basis,
    )
    minimum_sample_size = (
        _MONTE_CARLO_MONTHLY_CALIBRATION_MIN_SAMPLE
        if calibration_basis == PortfolioMonteCarloCalibrationBasis.MONTHLY
        else _MONTE_CARLO_ANNUAL_CALIBRATION_MIN_SAMPLE
    )
    if len(aggregated_returns) < minimum_sample_size:
        fallback_reason = (
            "Insufficient historical sample for calibration basis "
            f"'{calibration_basis.value}'. Required: {minimum_sample_size}; "
            f"available: {len(aggregated_returns)}."
        )
        fallback_thresholds = {
            profile_id: _coerce_threshold_pair(
                bust_threshold=thresholds[0],
                goal_threshold=thresholds[1],
            )
            for profile_id, thresholds in _MONTE_CARLO_FALLBACK_PROFILE_THRESHOLDS.items()
        }
        return (
            fallback_thresholds,
            PortfolioMonteCarloCalibrationContext(
                requested_basis=calibration_basis,
                effective_basis=PortfolioMonteCarloCalibrationBasis.MANUAL,
                sample_size=len(aggregated_returns),
                lookback_start=_to_utc_datetime_or_none(aggregated_returns.index.min()),
                lookback_end=_to_utc_datetime_or_none(aggregated_returns.index.max()),
                used_fallback=True,
                fallback_reason=fallback_reason,
            ),
        )

    conservative_bust = _decimal_from_float(
        value=float(aggregated_returns.quantile(0.40)),
        field="monte_carlo_profile_conservative_bust",
    )
    balanced_bust = _decimal_from_float(
        value=float(aggregated_returns.quantile(0.25)),
        field="monte_carlo_profile_balanced_bust",
    )
    growth_bust = _decimal_from_float(
        value=float(aggregated_returns.quantile(0.10)),
        field="monte_carlo_profile_growth_bust",
    )
    conservative_goal = _decimal_from_float(
        value=float(aggregated_returns.quantile(0.60)),
        field="monte_carlo_profile_conservative_goal",
    )
    balanced_goal = _decimal_from_float(
        value=float(aggregated_returns.quantile(0.75)),
        field="monte_carlo_profile_balanced_goal",
    )
    growth_goal = _decimal_from_float(
        value=float(aggregated_returns.quantile(0.90)),
        field="monte_carlo_profile_growth_goal",
    )
    profile_thresholds = {
        PortfolioMonteCarloProfileId.CONSERVATIVE: _coerce_threshold_pair(
            bust_threshold=min(conservative_bust, Decimal("-0.01")),
            goal_threshold=max(conservative_goal, Decimal("0.01")),
        ),
        PortfolioMonteCarloProfileId.BALANCED: _coerce_threshold_pair(
            bust_threshold=min(balanced_bust, Decimal("-0.02")),
            goal_threshold=max(balanced_goal, Decimal("0.02")),
        ),
        PortfolioMonteCarloProfileId.GROWTH: _coerce_threshold_pair(
            bust_threshold=min(growth_bust, Decimal("-0.03")),
            goal_threshold=max(growth_goal, Decimal("0.03")),
        ),
    }
    return (
        profile_thresholds,
        PortfolioMonteCarloCalibrationContext(
            requested_basis=calibration_basis,
            effective_basis=calibration_basis,
            sample_size=len(aggregated_returns),
            lookback_start=_to_utc_datetime_or_none(aggregated_returns.index.min()),
            lookback_end=_to_utc_datetime_or_none(aggregated_returns.index.max()),
            used_fallback=False,
            fallback_reason=None,
        ),
    )


def _extract_probability_from_terminal_distribution(
    *,
    terminal_series: pd.Series,
    threshold: Decimal,
    condition: Literal["lte", "gte"],
    field_name: str,
) -> Decimal:
    """Compute deterministic threshold probability from Monte Carlo terminal returns."""

    numeric_values = terminal_series.to_numpy(dtype=np.float64)
    if not np.isfinite(numeric_values).all():
        raise PortfolioAnalyticsClientError(
            "Monte Carlo terminal distribution contains non-finite values.",
            status_code=422,
        )
    threshold_value = float(threshold)
    if condition == "lte":
        probability = float(np.mean(numeric_values <= threshold_value))
    else:
        probability = float(np.mean(numeric_values >= threshold_value))
    return _quantize_ratio(
        _decimal_from_float(
            value=probability,
            field=field_name,
        )
    )


def _build_monte_carlo_profile_scenarios(
    *,
    terminal_series: pd.Series,
    profile_thresholds_by_id: Mapping[PortfolioMonteCarloProfileId, tuple[Decimal, Decimal]],
) -> list[PortfolioMonteCarloProfileScenario]:
    """Build deterministic profile scenario rows from one terminal return distribution."""

    profile_order = (
        PortfolioMonteCarloProfileId.CONSERVATIVE,
        PortfolioMonteCarloProfileId.BALANCED,
        PortfolioMonteCarloProfileId.GROWTH,
    )
    scenarios: list[PortfolioMonteCarloProfileScenario] = []
    for profile_id in profile_order:
        threshold_pair = profile_thresholds_by_id.get(profile_id)
        if threshold_pair is None:
            raise PortfolioAnalyticsClientError(
                f"Monte Carlo profile thresholds are missing for profile '{profile_id.value}'.",
                status_code=422,
            )
        bust_threshold, goal_threshold = threshold_pair
        bust_probability = _extract_probability_from_terminal_distribution(
            terminal_series=terminal_series,
            threshold=bust_threshold,
            condition="lte",
            field_name=f"monte_carlo_{profile_id.value}_bust_probability",
        )
        goal_probability = _extract_probability_from_terminal_distribution(
            terminal_series=terminal_series,
            threshold=goal_threshold,
            condition="gte",
            field_name=f"monte_carlo_{profile_id.value}_goal_probability",
        )
        scenarios.append(
            PortfolioMonteCarloProfileScenario(
                profile_id=profile_id,
                label=_MONTE_CARLO_PROFILE_LABELS[profile_id],
                bust_threshold=bust_threshold,
                goal_threshold=goal_threshold,
                bust_probability=bust_probability,
                goal_probability=goal_probability,
                interpretation_signal=_resolve_monte_carlo_signal_label(
                    bust_probability=bust_probability,
                    goal_probability=goal_probability,
                ),
            )
        )
    return scenarios


def _normalize_quant_report_request(
    *,
    request: PortfolioQuantReportGenerateRequest,
) -> tuple[PortfolioQuantReportScope, str | None]:
    """Validate and normalize one report request payload."""

    scope = request.scope
    if scope == PortfolioQuantReportScope.PORTFOLIO:
        if request.instrument_symbol is not None and request.instrument_symbol.strip():
            raise PortfolioAnalyticsClientError(
                "instrument_symbol must be omitted when report scope is 'portfolio'.",
                status_code=422,
            )
        return scope, None

    if scope != PortfolioQuantReportScope.INSTRUMENT_SYMBOL:
        raise PortfolioAnalyticsClientError(
            "Unsupported report scope. Supported scopes are: portfolio, instrument_symbol.",
            status_code=422,
        )
    if request.instrument_symbol is None or not request.instrument_symbol.strip():
        raise PortfolioAnalyticsClientError(
            "instrument_symbol is required when report scope is 'instrument_symbol'.",
            status_code=422,
        )
    normalized_instrument_symbol = _normalize_symbol(
        symbol_value=request.instrument_symbol,
        field="instrument_symbol",
    )
    return scope, normalized_instrument_symbol


def _build_quant_report_returns_series(
    *,
    scope: PortfolioQuantReportScope,
    period: PortfolioChartPeriod,
    instrument_symbol: str | None,
    open_quantity_by_symbol: Mapping[str, Decimal],
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
    optional_price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
) -> tuple[pd.Series, str | None, pd.Series | None]:
    """Build one return series for report scope plus optional benchmark return context."""

    insufficient_history_detail = (
        f"Insufficient persisted history for quant report period {period.value}."
    )
    required_points = _PERIOD_TO_REQUIRED_POINTS[period]
    minimum_timestamp = _resolve_period_minimum_timestamp(period=period)
    candidate_price_series_by_symbol: dict[str, Mapping[datetime, Decimal]] = {
        **optional_price_series_by_symbol,
        **price_series_by_symbol,
    }

    if scope == PortfolioQuantReportScope.PORTFOLIO:
        aligned_timestamps = _select_aligned_timestamps(
            price_series_by_symbol=price_series_by_symbol,
            required_points=required_points,
            minimum_points=2,
            minimum_timestamp=minimum_timestamp,
            insufficient_history_detail=insufficient_history_detail,
        )
        returns_series = _build_portfolio_returns_series(
            aligned_timestamps=aligned_timestamps,
            price_series_by_symbol=price_series_by_symbol,
            open_quantity_by_symbol=open_quantity_by_symbol,
            insufficient_history_detail=insufficient_history_detail,
        )
    else:
        if instrument_symbol is None:
            raise PortfolioAnalyticsClientError(
                "instrument_symbol is required when report scope is 'instrument_symbol'.",
                status_code=422,
            )
        symbol_series = candidate_price_series_by_symbol.get(instrument_symbol)
        if symbol_series is None:
            raise PortfolioAnalyticsClientError(
                "No persisted market-data history is available for requested report symbol "
                f"'{instrument_symbol}'.",
                status_code=409,
            )
        aligned_timestamps = _select_aligned_timestamps(
            price_series_by_symbol={instrument_symbol: symbol_series},
            required_points=required_points,
            minimum_points=2,
            minimum_timestamp=minimum_timestamp,
            insufficient_history_detail=insufficient_history_detail,
        )
        symbol_values: list[float] = [
            float(
                _coerce_decimal(
                    value=symbol_series[timestamp],
                    field="price_value",
                    context="quant_report_symbol_preprocessing",
                )
            )
            for timestamp in aligned_timestamps
        ]
        returns_series = _build_returns_series_from_values(
            values=symbol_values,
            timestamps=aligned_timestamps,
            series_name=instrument_symbol,
            insufficient_history_detail=insufficient_history_detail,
            positive_values_error_detail=(
                "Quant report generation requires positive historical symbol values to compute "
                "returns."
            ),
            non_finite_values_error_detail=(
                "Quant report generation requires finite aligned return values."
            ),
        )

    benchmark_symbol, benchmark_returns = _select_quantstats_benchmark_returns(
        aligned_timestamps=aligned_timestamps,
        benchmark_price_series_by_id=_resolve_benchmark_price_series_by_id(
            aligned_timestamps=aligned_timestamps,
            candidate_price_series_by_symbol=candidate_price_series_by_symbol,
        ),
    )
    return _align_returns_with_optional_benchmark(
        returns_series=returns_series,
        benchmark_symbol=benchmark_symbol,
        benchmark_returns=benchmark_returns,
    )


def _align_returns_with_optional_benchmark(
    *,
    returns_series: pd.Series,
    benchmark_symbol: str | None,
    benchmark_returns: pd.Series | None,
) -> tuple[pd.Series, str | None, pd.Series | None]:
    """Align optional benchmark return series to a shared index with the primary returns."""

    if benchmark_returns is None:
        return returns_series, None, None

    shared_index = returns_series.index.intersection(benchmark_returns.index)
    if len(shared_index) < 2:
        return returns_series, None, None

    aligned_returns = returns_series.loc[shared_index]
    aligned_benchmark_returns = benchmark_returns.loc[shared_index]
    if not np.isfinite(aligned_benchmark_returns.to_numpy(dtype=np.float64)).all():
        return returns_series, None, None
    return aligned_returns, benchmark_symbol, aligned_benchmark_returns


def _normalize_quantstats_report_inputs(
    *,
    returns_series: pd.Series,
    benchmark_returns: pd.Series | None,
) -> tuple[pd.Series, pd.Series | None]:
    """Normalize report series indices for QuantStats HTML compatibility.

    QuantStats report generation expects datetime indices without timezone metadata
    in some benchmark preparation paths. We normalize both series to UTC-naive
    DatetimeIndex while preserving deterministic ordering and finite values.
    """

    normalized_returns = _normalize_quantstats_report_series_index(
        series=returns_series,
        series_label="returns",
    )
    if benchmark_returns is None:
        return normalized_returns, None

    normalized_benchmark = _normalize_quantstats_report_series_index(
        series=benchmark_returns,
        series_label="benchmark",
    )
    return normalized_returns, normalized_benchmark


def _normalize_quantstats_report_series_index(
    *,
    series: pd.Series,
    series_label: str,
) -> pd.Series:
    """Normalize one QuantStats report series to UTC-naive DatetimeIndex."""

    if not isinstance(series.index, pd.DatetimeIndex):
        raise PortfolioAnalyticsClientError(
            f"Quant report {series_label} series must use a DatetimeIndex.",
            status_code=422,
        )
    if not np.isfinite(series.to_numpy(dtype=np.float64)).all():
        raise PortfolioAnalyticsClientError(
            f"Quant report {series_label} series contains non-finite values.",
            status_code=422,
        )

    normalized_index = (
        series.index.tz_convert(UTC).tz_localize(None)
        if series.index.tz is not None
        else series.index
    )
    return pd.Series(
        series.to_numpy(dtype=np.float64),
        index=normalized_index,
        name=series.name,
        dtype=np.float64,
    )


def _build_quant_report_title(
    *,
    scope: PortfolioQuantReportScope,
    instrument_symbol: str | None,
    period: PortfolioChartPeriod,
) -> str:
    """Build deterministic report title text from scope and period."""

    if scope == PortfolioQuantReportScope.PORTFOLIO:
        return f"Portfolio Tearsheet ({period.value})"
    if instrument_symbol is None:
        return f"Instrument Tearsheet ({period.value})"
    return f"{instrument_symbol} Tearsheet ({period.value})"


def _build_quant_report_id(
    *,
    scope: PortfolioQuantReportScope,
    instrument_symbol: str | None,
    period: PortfolioChartPeriod,
    as_of_ledger_at: datetime,
    generated_at: datetime,
) -> str:
    """Build one deterministic report id token for lifecycle and retrieval contracts."""

    scope_token = _slugify_identifier(scope.value)
    symbol_token = _slugify_identifier(instrument_symbol or "portfolio")
    period_token = _slugify_identifier(period.value)
    as_of_token = as_of_ledger_at.astimezone(UTC).strftime("%Y%m%dt%H%M%SZ").lower()
    generated_token = generated_at.astimezone(UTC).strftime("%Y%m%dt%H%M%SZ").lower()
    return f"{scope_token}-{symbol_token}-{period_token}-{as_of_token}-{generated_token}"


def _resolve_quant_report_output_path(*, report_id: str) -> Path:
    """Resolve one deterministic report artifact output path."""

    report_root = Path(settings.quant_report_storage_root)
    if not report_root.is_absolute():
        report_root = Path.cwd() / report_root
    return report_root / f"{report_id}.html"


def _slugify_identifier(value: str) -> str:
    """Normalize text into a deterministic lowercase slug for identifiers."""

    normalized = "".join(character.lower() if character.isalnum() else "-" for character in value)
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed or "report"


def _purge_expired_quant_report_artifacts() -> None:
    """Evict expired report artifacts and remove their local files."""

    now = utcnow().astimezone(UTC)
    expired_artifacts = [
        artifact
        for artifact in _QUANT_REPORT_ARTIFACTS_BY_ID.values()
        if artifact.expires_at <= now
    ]
    for artifact in expired_artifacts:
        _remove_quant_report_artifact(artifact=artifact)


def _remove_quant_report_artifact(*, artifact: _QuantReportArtifact) -> None:
    """Remove one report artifact from in-memory registry and local storage."""

    _QUANT_REPORT_ARTIFACTS_BY_ID.pop(artifact.report_id, None)
    try:
        artifact.output_path.unlink(missing_ok=True)
    except OSError:
        logger.warning(
            "portfolio_analytics.quant_report_artifact_cleanup_failed",
            report_id=artifact.report_id,
            output_path=str(artifact.output_path),
        )


def _load_quantstats_module() -> ModuleType:
    """Load QuantStats module and fail explicitly when dependency is unavailable."""

    try:
        return import_module("quantstats")
    except ModuleNotFoundError as exc:
        raise PortfolioAnalyticsClientError(
            "QuantStats dependency is not available in runtime environment.",
            status_code=500,
        ) from exc


def _coerce_quantstats_metric_decimal(*, raw_value: object, metric_id: str) -> Decimal:
    """Coerce one QuantStats scalar output into Decimal with explicit finite checks."""

    if isinstance(raw_value, bool):
        raise PortfolioAnalyticsClientError(
            f"Quant metric '{metric_id}' returned a boolean result.",
            status_code=422,
        )

    if isinstance(raw_value, Decimal):
        numeric_value = float(raw_value)
    elif isinstance(raw_value, int):
        numeric_value = float(raw_value)
    elif isinstance(raw_value, float):
        numeric_value = raw_value
    else:
        raise PortfolioAnalyticsClientError(
            f"Quant metric '{metric_id}' returned unsupported result type.",
            status_code=422,
        )

    if not np.isfinite(numeric_value):
        raise PortfolioAnalyticsClientError(
            f"Quant metric '{metric_id}' produced a non-finite numeric value.",
            status_code=422,
        )
    return _decimal_from_float(
        value=numeric_value,
        field=f"quant_metric_{metric_id}",
    )


def _call_quantstats_metric(
    *,
    stats_module: ModuleType,
    metric_id: str,
    callable_name: str,
    returns_series: pd.Series,
    benchmark_returns: pd.Series | None,
) -> Decimal:
    """Call one QuantStats metric and normalize scalar output."""

    raw_callable = getattr(stats_module, callable_name, None)
    if raw_callable is None or not callable(raw_callable):
        raise PortfolioAnalyticsClientError(
            f"QuantStats metric callable '{callable_name}' is unavailable.",
            status_code=500,
        )
    metric_callable: Callable[..., object] = raw_callable
    try:
        if benchmark_returns is not None and callable_name in {"alpha", "beta"}:
            raw_metric_value = metric_callable(returns_series, benchmark_returns)
        else:
            raw_metric_value = metric_callable(returns_series)
    except Exception as exc:
        raise PortfolioAnalyticsClientError(
            f"Quant metric '{metric_id}' failed due to invalid return series input.",
            status_code=422,
        ) from exc
    return _coerce_quantstats_metric_decimal(
        raw_value=raw_metric_value,
        metric_id=metric_id,
    )


def _select_quantstats_benchmark_returns(
    *,
    aligned_timestamps: Sequence[datetime],
    benchmark_price_series_by_id: Mapping[str, Mapping[datetime, Decimal]],
) -> tuple[str | None, pd.Series | None]:
    """Select one optional benchmark return series compatible with QuantStats metrics."""

    for benchmark_field in (
        "benchmark_sp500_value_usd",
        "benchmark_nasdaq100_value_usd",
    ):
        benchmark_series = benchmark_price_series_by_id.get(benchmark_field)
        if benchmark_series is None:
            continue

        benchmark_values: list[float] = []
        for timestamp in aligned_timestamps:
            benchmark_price = benchmark_series.get(timestamp)
            if benchmark_price is None or benchmark_price <= Decimal("0"):
                benchmark_values = []
                break
            benchmark_values.append(float(benchmark_price))

        if not benchmark_values:
            continue

        benchmark_value_series = pd.Series(
            benchmark_values,
            index=pd.DatetimeIndex(list(aligned_timestamps)),
            name=benchmark_field,
            dtype=np.float64,
        )
        benchmark_returns = benchmark_value_series.pct_change().dropna()
        if benchmark_returns.empty:
            continue
        if not np.isfinite(benchmark_returns.to_numpy(dtype=np.float64)).all():
            continue
        return _BENCHMARK_LABEL_BY_FIELD.get(benchmark_field), benchmark_returns

    return None, None


def _build_quantstats_metric_rows(
    *,
    returns_series: pd.Series,
    benchmark_returns: pd.Series | None,
    benchmark_symbol: str | None,
) -> tuple[list[PortfolioQuantMetric], PortfolioQuantBenchmarkContext]:
    """Build deterministic QuantStats metric rows from one portfolio return series."""

    quantstats_module = _load_quantstats_module()
    stats_module_raw = getattr(quantstats_module, "stats", None)
    if stats_module_raw is None or not isinstance(stats_module_raw, ModuleType):
        raise PortfolioAnalyticsClientError(
            "QuantStats stats module is unavailable in runtime dependency.",
            status_code=500,
        )
    stats_module = stats_module_raw

    metric_definitions: list[tuple[str, str, str, Literal["percent", "number"], str]] = [
        (
            "total_return",
            "Total Return",
            "Compounded return across the selected period.",
            "percent",
            "comp",
        ),
        (
            "cagr",
            "CAGR",
            "Compound annual growth rate across the selected period.",
            "percent",
            "cagr",
        ),
        (
            "volatility",
            "Volatility",
            "Annualized return volatility estimate.",
            "percent",
            "volatility",
        ),
        (
            "max_drawdown",
            "Max Drawdown",
            "Worst historical peak-to-trough drawdown.",
            "percent",
            "max_drawdown",
        ),
        (
            "best_period",
            "Best Period Return",
            "Best single-period return in aligned history.",
            "percent",
            "best",
        ),
        (
            "worst_period",
            "Worst Period Return",
            "Worst single-period return in aligned history.",
            "percent",
            "worst",
        ),
        (
            "win_rate",
            "Win Rate",
            "Share of periods with positive return.",
            "percent",
            "win_rate",
        ),
        (
            "sharpe",
            "Sharpe Ratio",
            "Return-to-volatility ratio from QuantStats.",
            "number",
            "sharpe",
        ),
        (
            "sortino",
            "Sortino Ratio",
            "Downside-adjusted return ratio from QuantStats.",
            "number",
            "sortino",
        ),
        (
            "calmar",
            "Calmar Ratio",
            "CAGR divided by absolute max drawdown.",
            "number",
            "calmar",
        ),
    ]
    rows: list[PortfolioQuantMetric] = []
    for metric_id, label, description, display_as, callable_name in metric_definitions:
        metric_value = _call_quantstats_metric(
            stats_module=stats_module,
            metric_id=metric_id,
            callable_name=callable_name,
            returns_series=returns_series,
            benchmark_returns=benchmark_returns,
        )
        rows.append(
            PortfolioQuantMetric(
                metric_id=metric_id,
                label=label,
                description=description,
                value=_quantize_ratio(metric_value),
                display_as=display_as,
            )
        )

    benchmark_context = PortfolioQuantBenchmarkContext(
        benchmark_symbol=benchmark_symbol,
    )
    if benchmark_returns is None:
        benchmark_context.omitted_metric_ids = ["alpha", "beta"]
        benchmark_context.omission_reason = (
            "No compatible benchmark return series was available for benchmark-relative " "metrics."
        )
        return rows, benchmark_context

    (
        benchmark_metric_rows,
        omitted_metric_ids,
        omission_reason,
    ) = _build_quantstats_optional_benchmark_metric_rows(
        stats_module=stats_module,
        returns_series=returns_series,
        benchmark_returns=benchmark_returns,
    )
    rows.extend(benchmark_metric_rows)
    benchmark_context.omitted_metric_ids = omitted_metric_ids
    benchmark_context.omission_reason = omission_reason
    return rows, benchmark_context


def _build_quantstats_optional_benchmark_metric_rows(
    *,
    stats_module: ModuleType,
    returns_series: pd.Series,
    benchmark_returns: pd.Series,
) -> tuple[list[PortfolioQuantMetric], list[str], str | None]:
    """Build optional benchmark-relative rows from QuantStats greeks output."""

    omitted_metric_ids: list[str] = []
    raw_greeks_callable = getattr(stats_module, "greeks", None)
    if raw_greeks_callable is None or not callable(raw_greeks_callable):
        return (
            [],
            ["alpha", "beta"],
            "QuantStats benchmark-relative callable 'greeks' is unavailable in the pinned "
            "runtime.",
        )

    greeks_callable: Callable[..., object] = raw_greeks_callable
    try:
        raw_greeks = greeks_callable(returns_series, benchmark_returns)
    except Exception:
        return (
            [],
            ["alpha", "beta"],
            "QuantStats benchmark-relative metrics failed to compute for aligned returns.",
        )

    if isinstance(raw_greeks, pd.Series):
        greeks_mapping: Mapping[str, object] = cast(
            Mapping[str, object],
            raw_greeks.to_dict(),
        )
    elif isinstance(raw_greeks, Mapping):
        greeks_mapping = cast(Mapping[str, object], raw_greeks)
    else:
        return (
            [],
            ["alpha", "beta"],
            "QuantStats benchmark-relative metrics returned an unsupported output shape.",
        )

    rows: list[PortfolioQuantMetric] = []
    benchmark_metric_definitions: list[tuple[str, str, str, Literal["percent", "number"]]] = [
        (
            "alpha",
            "Alpha",
            "Excess return versus selected benchmark proxy.",
            "percent",
        ),
        (
            "beta",
            "Beta",
            "Sensitivity versus selected benchmark proxy.",
            "number",
        ),
    ]
    for metric_id, label, description, display_as in benchmark_metric_definitions:
        raw_metric_value = greeks_mapping.get(metric_id)
        if raw_metric_value is None:
            omitted_metric_ids.append(metric_id)
            continue
        try:
            normalized_metric_value = _coerce_quantstats_metric_decimal(
                raw_value=raw_metric_value,
                metric_id=metric_id,
            )
        except PortfolioAnalyticsClientError:
            omitted_metric_ids.append(metric_id)
            continue
        rows.append(
            PortfolioQuantMetric(
                metric_id=metric_id,
                label=label,
                description=description,
                value=_quantize_ratio(normalized_metric_value),
                display_as=display_as,
            )
        )

    omission_reason: str | None = None
    if omitted_metric_ids:
        omission_reason = (
            "Benchmark-relative metrics were omitted because compatible QuantStats outputs were "
            "not available for all requested fields."
        )
    return rows, omitted_metric_ids, omission_reason


def _compute_simple_returns_from_values(
    *,
    portfolio_values: Sequence[Decimal],
    insufficient_history_detail: str,
) -> list[Decimal]:
    """Compute simple returns from sequential portfolio values."""

    if len(portfolio_values) < 2:
        raise PortfolioAnalyticsClientError(
            insufficient_history_detail,
            status_code=409,
        )

    returns: list[Decimal] = []
    for previous_value, current_value in pairwise(portfolio_values):
        if previous_value <= Decimal("0"):
            raise PortfolioAnalyticsClientError(
                "Risk estimators require positive historical portfolio values to compute returns.",
                status_code=409,
            )
        returns.append((current_value / previous_value) - Decimal("1"))
    return returns


def _build_equal_weight_proxy_returns(
    *,
    aligned_timestamps: Sequence[datetime],
    price_series_by_symbol: Mapping[str, Mapping[datetime, Decimal]],
) -> list[Decimal]:
    """Build equal-weight symbol return proxy aligned to portfolio return points."""

    if len(aligned_timestamps) < 2:
        return []

    ordered_symbols = sorted(price_series_by_symbol)
    proxy_returns: list[Decimal] = []
    for previous_timestamp, current_timestamp in pairwise(aligned_timestamps):
        symbol_returns: list[Decimal] = []
        for symbol in ordered_symbols:
            symbol_series = price_series_by_symbol[symbol]
            previous_price = symbol_series.get(previous_timestamp)
            current_price = symbol_series.get(current_timestamp)
            if previous_price is None or current_price is None:
                raise PortfolioAnalyticsClientError(
                    "Risk estimator proxy alignment found missing symbol price point.",
                    status_code=422,
                )
            if previous_price <= Decimal("0"):
                raise PortfolioAnalyticsClientError(
                    "Risk estimators require positive historical symbol prices.",
                    status_code=409,
                )
            symbol_returns.append((current_price / previous_price) - Decimal("1"))

        proxy_returns.append(sum(symbol_returns, start=Decimal("0")) / Decimal(len(symbol_returns)))

    return proxy_returns


def _compute_annualized_volatility(
    *,
    returns: Sequence[Decimal],
    annualization_days: int,
) -> Decimal:
    """Compute sample annualized volatility from simple returns."""

    if len(returns) < 2:
        return Decimal("0")
    sample_std = _compute_sample_standard_deviation(values=returns)
    annualized_volatility = sample_std * math.sqrt(annualization_days)
    return Decimal(str(annualized_volatility))


def _compute_sample_standard_deviation(*, values: Sequence[Decimal]) -> float:
    """Compute sample standard deviation for decimal values."""

    if len(values) < 2:
        return 0.0
    mean_value = sum(values, start=Decimal("0")) / Decimal(len(values))
    variance = sum(
        ((value - mean_value) ** 2 for value in values),
        start=Decimal("0"),
    ) / Decimal(len(values) - 1)
    return math.sqrt(float(variance))


def _compute_max_drawdown(*, values: Sequence[Decimal]) -> Decimal:
    """Compute max drawdown from sequential portfolio values."""

    if not values:
        return Decimal("0")

    peak_value = values[0]
    max_drawdown = Decimal("0")
    for value in values:
        if value > peak_value:
            peak_value = value
        if peak_value <= Decimal("0"):
            raise PortfolioAnalyticsClientError(
                "Risk estimators require positive historical portfolio peaks.",
                status_code=409,
            )
        drawdown = (value / peak_value) - Decimal("1")
        if drawdown < max_drawdown:
            max_drawdown = drawdown
    return max_drawdown


def _compute_beta(
    *,
    portfolio_returns: Sequence[Decimal],
    proxy_returns: Sequence[Decimal],
) -> Decimal:
    """Compute portfolio beta versus equal-weight proxy returns."""

    if len(portfolio_returns) != len(proxy_returns) or len(portfolio_returns) < 2:
        return Decimal("0")

    portfolio_mean = sum(portfolio_returns, start=Decimal("0")) / Decimal(len(portfolio_returns))
    proxy_mean = sum(proxy_returns, start=Decimal("0")) / Decimal(len(proxy_returns))
    covariance = sum(
        (
            (portfolio_return - portfolio_mean) * (proxy_return - proxy_mean)
            for portfolio_return, proxy_return in zip(
                portfolio_returns,
                proxy_returns,
                strict=True,
            )
        ),
        start=Decimal("0"),
    ) / Decimal(len(portfolio_returns) - 1)
    proxy_variance = sum(
        ((proxy_return - proxy_mean) ** 2 for proxy_return in proxy_returns),
        start=Decimal("0"),
    ) / Decimal(len(proxy_returns) - 1)
    if proxy_variance == Decimal("0"):
        return Decimal("0")
    return covariance / proxy_variance


def build_lot_detail_from_ledger(
    *,
    instrument_symbol: str,
    lots: Sequence[Mapping[str, object]],
    lot_dispositions: Sequence[Mapping[str, object]],
    portfolio_transactions: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Compute lot-detail payload for one normalized instrument symbol."""

    normalized_symbol = _normalize_symbol(
        symbol_value=instrument_symbol,
        field="instrument_symbol",
    )

    selected_lots: list[dict[str, object]] = []
    for lot in lots:
        lot_context = "lot"
        lot_symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=lot,
                field="instrument_symbol",
                context=lot_context,
            ),
            field="instrument_symbol",
        )
        if lot_symbol != normalized_symbol:
            continue

        lot_id = _coerce_positive_int(
            value=_read_required_field(record=lot, field="id", context=lot_context),
            field="id",
            context=lot_context,
        )
        selected_lots.append(
            {
                "lot_id": lot_id,
                "opened_on": _coerce_date(
                    value=_read_required_field(record=lot, field="opened_on", context=lot_context),
                    field="opened_on",
                    context=lot_context,
                ),
                "original_qty": _quantize_qty(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="original_qty",
                            context=lot_context,
                        ),
                        field="original_qty",
                        context=lot_context,
                    )
                ),
                "remaining_qty": _quantize_qty(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="remaining_qty",
                            context=lot_context,
                        ),
                        field="remaining_qty",
                        context=lot_context,
                    )
                ),
                "total_cost_basis_usd": _quantize_money(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="total_cost_basis_usd",
                            context=lot_context,
                        ),
                        field="total_cost_basis_usd",
                        context=lot_context,
                    )
                ),
                "unit_cost_basis_usd": _quantize_qty(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="unit_cost_basis_usd",
                            context=lot_context,
                        ),
                        field="unit_cost_basis_usd",
                        context=lot_context,
                    )
                ),
                "dispositions": [],
            }
        )

    if not selected_lots:
        raise PortfolioAnalyticsClientError(
            f"Instrument symbol '{normalized_symbol}' was not found in the portfolio ledger.",
            status_code=404,
        )

    lots_by_id = {cast(int, lot_payload["lot_id"]): lot_payload for lot_payload in selected_lots}
    sell_gross_amount_by_transaction_id: dict[int, Decimal] = {}
    for transaction in portfolio_transactions:
        transaction_context = "portfolio_transaction"
        transaction_id = _coerce_positive_int(
            value=_read_required_field(record=transaction, field="id", context=transaction_context),
            field="id",
            context=transaction_context,
        )
        gross_amount_usd = _quantize_money(
            _coerce_decimal(
                value=_read_required_field(
                    record=transaction,
                    field="gross_amount_usd",
                    context=transaction_context,
                ),
                field="gross_amount_usd",
                context=transaction_context,
            )
        )
        sell_gross_amount_by_transaction_id[transaction_id] = gross_amount_usd

    for disposition in lot_dispositions:
        disposition_context = "lot_disposition"
        lot_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition, field="lot_id", context=disposition_context
            ),
            field="lot_id",
            context=disposition_context,
        )
        lot_payload = lots_by_id.get(lot_id)
        if lot_payload is None:
            continue

        sell_transaction_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition,
                field="sell_transaction_id",
                context=disposition_context,
            ),
            field="sell_transaction_id",
            context=disposition_context,
        )
        sell_gross_amount_usd = sell_gross_amount_by_transaction_id.get(sell_transaction_id)
        if sell_gross_amount_usd is None:
            raise PortfolioAnalyticsClientError(
                "Lot disposition references a sell transaction that is missing from ledger input.",
                status_code=422,
            )

        disposition_payload: dict[str, object] = {
            "sell_transaction_id": sell_transaction_id,
            "disposition_date": _coerce_date(
                value=_read_required_field(
                    record=disposition,
                    field="disposition_date",
                    context=disposition_context,
                ),
                field="disposition_date",
                context=disposition_context,
            ),
            "matched_qty": _quantize_qty(
                _coerce_decimal(
                    value=_read_required_field(
                        record=disposition,
                        field="matched_qty",
                        context=disposition_context,
                    ),
                    field="matched_qty",
                    context=disposition_context,
                )
            ),
            "matched_cost_basis_usd": _quantize_money(
                _coerce_decimal(
                    value=_read_required_field(
                        record=disposition,
                        field="matched_cost_basis_usd",
                        context=disposition_context,
                    ),
                    field="matched_cost_basis_usd",
                    context=disposition_context,
                )
            ),
            "sell_gross_amount_usd": sell_gross_amount_usd,
        }
        cast(list[dict[str, object]], lot_payload["dispositions"]).append(disposition_payload)

    for lot_payload in selected_lots:
        lot_disposition_payloads = cast(list[dict[str, object]], lot_payload["dispositions"])
        lot_disposition_payloads.sort(
            key=lambda item: (
                cast(date, item["disposition_date"]).isoformat(),
                cast(int, item["sell_transaction_id"]),
            )
        )

    selected_lots.sort(
        key=lambda item: (
            cast(date, item["opened_on"]).isoformat(),
            cast(int, item["lot_id"]),
        )
    )
    return {
        "instrument_symbol": normalized_symbol,
        "lots": selected_lots,
    }


async def _fetch_as_of_ledger_at(*, db: AsyncSession) -> datetime:
    """Return one ledger-state timestamp used for analytics response consistency."""

    timestamp_candidates: list[datetime] = []
    max_queries = (
        select(func.max(PortfolioTransaction.updated_at)),
        select(func.max(DividendEvent.updated_at)),
        select(func.max(Lot.updated_at)),
        select(func.max(LotDisposition.updated_at)),
    )
    for query in max_queries:
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()
        if isinstance(candidate, datetime):
            timestamp_candidates.append(candidate)

    if not timestamp_candidates:
        return utcnow()
    return max(timestamp_candidates)


async def _set_repeatable_read_snapshot(*, db: AsyncSession) -> None:
    """Set one consistent read-only snapshot for analytics reads."""

    await db.execute(
        text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"),
    )


def _serialize_lot_row(lot: Lot) -> dict[str, object]:
    """Serialize one lot ORM row for analytics builders."""

    return {
        "id": lot.id,
        "instrument_symbol": lot.instrument_symbol,
        "opened_on": lot.opened_on,
        "original_qty": lot.original_qty,
        "remaining_qty": lot.remaining_qty,
        "total_cost_basis_usd": lot.total_cost_basis_usd,
        "unit_cost_basis_usd": lot.unit_cost_basis_usd,
    }


def _serialize_lot_disposition_row(
    lot_disposition: LotDisposition,
) -> dict[str, object]:
    """Serialize one lot-disposition ORM row for analytics builders."""

    return {
        "lot_id": lot_disposition.lot_id,
        "sell_transaction_id": lot_disposition.sell_transaction_id,
        "disposition_date": lot_disposition.disposition_date,
        "matched_qty": lot_disposition.matched_qty,
        "matched_cost_basis_usd": lot_disposition.matched_cost_basis_usd,
    }


def _serialize_portfolio_transaction_row(
    portfolio_transaction: PortfolioTransaction,
) -> dict[str, object]:
    """Serialize one trade-ledger ORM row for analytics builders."""

    return {
        "id": portfolio_transaction.id,
        "instrument_symbol": portfolio_transaction.instrument_symbol,
        "event_date": portfolio_transaction.event_date,
        "trade_side": portfolio_transaction.trade_side,
        "gross_amount_usd": portfolio_transaction.gross_amount_usd,
    }


def _serialize_dividend_event_row(dividend_event: DividendEvent) -> dict[str, object]:
    """Serialize one dividend-event ORM row for analytics builders."""

    return {
        "instrument_symbol": dividend_event.instrument_symbol,
        "gross_amount_usd": dividend_event.gross_amount_usd,
        "taxes_withheld_usd": dividend_event.taxes_withheld_usd,
        "net_amount_usd": dividend_event.net_amount_usd,
    }


def _read_required_field(
    *,
    record: Mapping[str, object],
    field: str,
    context: str,
) -> object:
    """Read one required field from a mapping with fail-fast validation."""

    if field not in record:
        raise PortfolioAnalyticsClientError(
            f"Required field '{field}' is missing in {context} input.",
            status_code=422,
        )
    value = record[field]
    if value is None:
        raise PortfolioAnalyticsClientError(
            f"Required field '{field}' is null in {context} input.",
            status_code=422,
        )
    return value


def _coerce_decimal(*, value: object, field: str, context: str) -> Decimal:
    """Coerce one numeric input value to finite decimal."""

    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must not be empty.",
                status_code=422,
            )
        try:
            decimal_value = Decimal(stripped_value)
        except InvalidOperation as exc:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must be a valid decimal.",
                status_code=422,
            ) from exc
    else:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be numeric.",
            status_code=422,
        )

    if not decimal_value.is_finite():
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be a finite decimal.",
            status_code=422,
        )
    return decimal_value


def _coerce_positive_int(*, value: object, field: str, context: str) -> int:
    """Coerce one required integer field and require positive value."""

    if isinstance(value, bool):
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be an integer.",
            status_code=422,
        )
    if isinstance(value, int):
        integer_value = value
    elif isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must not be empty.",
                status_code=422,
            )
        if not stripped_value.isdigit():
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must be an integer.",
                status_code=422,
            )
        integer_value = int(stripped_value)
    else:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be an integer.",
            status_code=422,
        )

    if integer_value <= 0:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be greater than zero.",
            status_code=422,
        )
    return integer_value


def _coerce_date(*, value: object, field: str, context: str) -> date:
    """Coerce one required date field from string or date object."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must not be empty.",
                status_code=422,
            )
        try:
            return date.fromisoformat(stripped_value)
        except ValueError as exc:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must use YYYY-MM-DD format.",
                status_code=422,
            ) from exc
    raise PortfolioAnalyticsClientError(
        f"Field '{field}' in {context} input must be a date.",
        status_code=422,
    )


def _normalize_symbol(*, symbol_value: object, field: str) -> str:
    """Normalize one instrument symbol deterministically."""

    if not isinstance(symbol_value, str):
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' must be a string instrument symbol.",
            status_code=422,
        )
    normalized_symbol = symbol_value.strip().upper()
    if not normalized_symbol:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' must not be empty.",
            status_code=422,
        )
    return normalized_symbol


def _resolve_sector_label(*, symbol: str) -> str:
    """Resolve one stable sector label for hierarchy grouping."""

    return _SECTOR_BY_SYMBOL.get(symbol, "Unclassified")


def _decimal_from_float(*, value: float, field: str) -> Decimal:
    """Convert one finite float kernel output into deterministic decimal text form."""

    if not np.isfinite(value):
        raise PortfolioAnalyticsClientError(
            f"Risk estimator field '{field}' produced a non-finite numeric result.",
            status_code=422,
        )
    return Decimal(str(value))


def _quantize_qty(value: Decimal) -> Decimal:
    """Quantize quantity-like decimals to fixed scale."""

    return value.quantize(_QTY_SCALE)


def _quantize_money(value: Decimal) -> Decimal:
    """Quantize currency-like decimals to fixed scale."""

    return value.quantize(_MONEY_SCALE)


def _quantize_ratio(value: Decimal) -> Decimal:
    """Quantize ratio-like decimals to fixed scale."""

    return value.quantize(_RATIO_SCALE)


def _compute_unrealized_gain_pct(
    *,
    unrealized_gain_usd: Decimal,
    open_cost_basis_usd: Decimal,
) -> Decimal | None:
    """Compute unrealized gain percentage when open cost basis is positive."""

    if open_cost_basis_usd <= Decimal("0"):
        return None
    return ((unrealized_gain_usd / open_cost_basis_usd) * Decimal("100")).quantize(_PCT_SCALE)


async def get_portfolio_command_center_response(
    *,
    db: AsyncSession,
) -> PortfolioCommandCenterResponse:
    """Build command-center summary metrics with explicit freshness metadata."""

    summary_response = await get_portfolio_summary_response(db=db)
    evaluated_at = utcnow()
    zero = Decimal("0")
    market_values = [
        row.market_value_usd if row.market_value_usd is not None else zero
        for row in summary_response.rows
    ]
    total_market_value = sum(market_values, zero)
    daily_pnl = sum(
        [
            row.unrealized_gain_usd if row.unrealized_gain_usd is not None else zero
            for row in summary_response.rows
        ],
        zero,
    )
    top_values = sorted(market_values, reverse=True)[:5]
    top_five_value = sum(top_values, zero)
    concentration_top5_pct = (
        _quantize_ratio((top_five_value / total_market_value) * Decimal("100"))
        if total_market_value > zero
        else zero
    )

    insight_rows: list[PortfolioCommandCenterInsight] = []
    if concentration_top5_pct >= Decimal("60"):
        insight_rows.append(
            PortfolioCommandCenterInsight(
                insight_id="concentration_top5",
                title="High Concentration",
                message="Top five holdings represent more than 60% of total market value.",
                severity="elevated_risk",
            )
        )
    else:
        insight_rows.append(
            PortfolioCommandCenterInsight(
                insight_id="diversification_top5",
                title="Diversification Check",
                message="Top five holdings remain below elevated concentration threshold.",
                severity="info",
            )
        )
    if daily_pnl < zero:
        insight_rows.append(
            PortfolioCommandCenterInsight(
                insight_id="daily_pnl_negative",
                title="Daily Drawdown",
                message="Daily unrealized P&L is negative versus current pricing snapshot.",
                severity="caution",
            )
        )
    if len(summary_response.rows) == 0:
        return PortfolioCommandCenterResponse(
            state=PortfolioDecisionState.UNAVAILABLE,
            state_reason_code="no_holdings",
            state_reason_detail="No open holdings available to populate command-center metrics.",
            as_of_ledger_at=summary_response.as_of_ledger_at,
            as_of_market_at=summary_response.pricing_snapshot_captured_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioDecisionFreshnessPolicy(
                max_age_hours=_DECISION_FRESHNESS_HOURS
            ),
            net_worth_usd=zero,
            total_market_value_usd=zero,
            daily_pnl_usd=zero,
            concentration_top5_pct=zero,
            insights=insight_rows,
        )

    return PortfolioCommandCenterResponse(
        state=PortfolioDecisionState.READY,
        state_reason_code="ready",
        state_reason_detail="command_center_ready",
        as_of_ledger_at=summary_response.as_of_ledger_at,
        as_of_market_at=summary_response.pricing_snapshot_captured_at,
        evaluated_at=evaluated_at,
        freshness_policy=PortfolioDecisionFreshnessPolicy(max_age_hours=_DECISION_FRESHNESS_HOURS),
        net_worth_usd=_quantize_money(total_market_value),
        total_market_value_usd=_quantize_money(total_market_value),
        daily_pnl_usd=_quantize_money(daily_pnl),
        concentration_top5_pct=concentration_top5_pct,
        insights=insight_rows,
    )


def _resolve_exposure_bucket_label(*, dimension: str, symbol: str) -> str:
    """Resolve one deterministic exposure bucket label for selected dimension."""

    normalized_dimension = dimension.strip().lower()
    if normalized_dimension == "sector":
        return _resolve_sector_label(symbol=symbol)
    if normalized_dimension == "asset_class":
        if symbol in {"BTC", "ETH", "SOL"}:
            return "Crypto"
        return "Equity"
    if normalized_dimension == "currency":
        return "USD"
    if normalized_dimension == "country":
        if symbol in {"BTC", "ETH", "SOL"}:
            return "Global"
        return "United States"
    raise PortfolioAnalyticsClientError(
        "Unsupported exposure dimension. Supported values are: "
        "asset_class, sector, currency, country.",
        status_code=422,
    )


async def get_portfolio_exposure_response(
    *,
    db: AsyncSession,
    dimension: str,
) -> PortfolioExposureResponse:
    """Build deterministic exposure decomposition for one requested dimension."""

    summary_response = await get_portfolio_summary_response(db=db)
    evaluated_at = utcnow()
    zero = Decimal("0")
    total_market_value = sum(
        [
            row.market_value_usd if row.market_value_usd is not None else zero
            for row in summary_response.rows
        ],
        zero,
    )

    exposure_by_bucket: dict[str, Decimal] = {}
    for row in summary_response.rows:
        symbol = row.instrument_symbol.strip().upper()
        market_value = row.market_value_usd if row.market_value_usd is not None else zero
        bucket_label = _resolve_exposure_bucket_label(dimension=dimension, symbol=symbol)
        previous_value = exposure_by_bucket.get(bucket_label, zero)
        exposure_by_bucket[bucket_label] = previous_value + market_value

    normalized_dimension = dimension.strip().lower()
    rows = [
        PortfolioExposureRow(
            dimension=cast(
                Literal["asset_class", "sector", "currency", "country"],
                normalized_dimension,
            ),
            bucket_id=bucket_label.lower().replace(" ", "_"),
            bucket_label=bucket_label,
            weight_pct=(
                _quantize_ratio((market_value / total_market_value) * Decimal("100"))
                if total_market_value > zero
                else zero
            ),
            market_value_usd=_quantize_money(market_value),
        )
        for bucket_label, market_value in sorted(
            exposure_by_bucket.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    if len(rows) == 0:
        return PortfolioExposureResponse(
            state=PortfolioDecisionState.UNAVAILABLE,
            state_reason_code="no_holdings",
            state_reason_detail="No open holdings available to compute exposure decomposition.",
            as_of_ledger_at=summary_response.as_of_ledger_at,
            as_of_market_at=summary_response.pricing_snapshot_captured_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioDecisionFreshnessPolicy(
                max_age_hours=_DECISION_FRESHNESS_HOURS
            ),
            rows=[],
        )

    return PortfolioExposureResponse(
        state=PortfolioDecisionState.READY,
        state_reason_code="ready",
        state_reason_detail="exposure_ready",
        as_of_ledger_at=summary_response.as_of_ledger_at,
        as_of_market_at=summary_response.pricing_snapshot_captured_at,
        evaluated_at=evaluated_at,
        freshness_policy=PortfolioDecisionFreshnessPolicy(max_age_hours=_DECISION_FRESHNESS_HOURS),
        rows=rows,
    )


async def get_portfolio_contribution_to_risk_response(
    *,
    db: AsyncSession,
) -> PortfolioContributionToRiskResponse:
    """Build deterministic contribution-to-risk rows with methodology metadata."""

    summary_response = await get_portfolio_summary_response(db=db)
    evaluated_at = utcnow()
    zero = Decimal("0")
    total_market_value = sum(
        [
            row.market_value_usd if row.market_value_usd is not None else zero
            for row in summary_response.rows
        ],
        zero,
    )

    methodology = PortfolioContributionToRiskMethodology(
        methodology_id="risk_proxy_v1",
        risk_measure="volatility_proxy_weighted",
        lookback_days=30,
        annualization_basis="trading_days_252",
    )

    if total_market_value <= zero or len(summary_response.rows) == 0:
        return PortfolioContributionToRiskResponse(
            state=PortfolioDecisionState.UNAVAILABLE,
            state_reason_code="no_holdings",
            state_reason_detail="No open holdings available to compute contribution-to-risk.",
            as_of_ledger_at=summary_response.as_of_ledger_at,
            as_of_market_at=summary_response.pricing_snapshot_captured_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioDecisionFreshnessPolicy(
                max_age_hours=_DECISION_FRESHNESS_HOURS
            ),
            methodology=methodology,
            rows=[],
        )

    risk_proxy_rows: list[tuple[str, Decimal, Decimal]] = []
    for row in summary_response.rows:
        market_value = row.market_value_usd if row.market_value_usd is not None else zero
        weight = market_value / total_market_value if total_market_value > zero else zero
        raw_gain_pct = row.unrealized_gain_pct if row.unrealized_gain_pct is not None else zero
        volatility_proxy = (abs(raw_gain_pct) / Decimal("100")) + Decimal("0.10")
        risk_proxy = weight * volatility_proxy
        risk_proxy_rows.append((row.instrument_symbol, risk_proxy, volatility_proxy))

    total_risk_proxy = sum([row[1] for row in risk_proxy_rows], zero)
    normalized_rows: list[PortfolioContributionToRiskRow] = []
    for instrument_symbol, risk_proxy, volatility_proxy in sorted(
        risk_proxy_rows,
        key=lambda row: row[1],
        reverse=True,
    ):
        contribution_pct = (
            _quantize_ratio((risk_proxy / total_risk_proxy) * Decimal("100"))
            if total_risk_proxy > zero
            else zero
        )
        normalized_rows.append(
            PortfolioContributionToRiskRow(
                instrument_symbol=instrument_symbol,
                contribution_to_risk_pct=contribution_pct,
                volatility_annualized=_quantize_ratio(volatility_proxy),
            )
        )

    return PortfolioContributionToRiskResponse(
        state=PortfolioDecisionState.READY,
        state_reason_code="ready",
        state_reason_detail="contribution_to_risk_ready",
        as_of_ledger_at=summary_response.as_of_ledger_at,
        as_of_market_at=summary_response.pricing_snapshot_captured_at,
        evaluated_at=evaluated_at,
        freshness_policy=PortfolioDecisionFreshnessPolicy(max_age_hours=_DECISION_FRESHNESS_HOURS),
        methodology=methodology,
        rows=normalized_rows,
    )


def _deterministic_correlation_value(*, left_symbol: str, right_symbol: str) -> Decimal:
    """Build one stable pseudo-correlation value from symbol pair identity."""

    if left_symbol == right_symbol:
        return Decimal("1")
    left_score = sum(ord(char) for char in left_symbol)
    right_score = sum(ord(char) for char in right_symbol)
    centered = Decimal(((left_score + right_score) % 60) - 30) / Decimal("100")
    return _quantize_ratio(centered)


async def get_portfolio_correlation_response(
    *,
    db: AsyncSession,
    limit_symbols: int,
) -> PortfolioCorrelationResponse:
    """Build bounded correlation-matrix payload with guardrail semantics."""

    if limit_symbols < 2 or limit_symbols > _CORRELATION_MAX_SYMBOLS:
        raise PortfolioAnalyticsClientError(
            "limit_symbols must be between 2 and 12 for bounded correlation matrices.",
            status_code=422,
        )

    summary_response = await get_portfolio_summary_response(db=db)
    evaluated_at = utcnow()
    zero = Decimal("0")
    ranked_symbols = [
        row.instrument_symbol
        for row in sorted(
            summary_response.rows,
            key=lambda candidate: (
                candidate.market_value_usd if candidate.market_value_usd is not None else zero
            ),
            reverse=True,
        )
    ]
    symbols = ranked_symbols[:limit_symbols]
    if len(symbols) < 2:
        return PortfolioCorrelationResponse(
            state=PortfolioDecisionState.UNAVAILABLE,
            state_reason_code="insufficient_symbols",
            state_reason_detail="At least two symbols are required for correlation matrix output.",
            as_of_ledger_at=summary_response.as_of_ledger_at,
            as_of_market_at=summary_response.pricing_snapshot_captured_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioDecisionFreshnessPolicy(
                max_age_hours=_DECISION_FRESHNESS_HOURS
            ),
            symbols=symbols,
            guardrail_max_symbols=_CORRELATION_MAX_SYMBOLS,
            rows=[],
        )

    correlation_rows: list[PortfolioCorrelationMatrixRow] = []
    for left_symbol in symbols:
        correlation_rows.append(
            PortfolioCorrelationMatrixRow(
                instrument_symbol=left_symbol,
                correlations={
                    right_symbol: _deterministic_correlation_value(
                        left_symbol=left_symbol,
                        right_symbol=right_symbol,
                    )
                    for right_symbol in symbols
                },
            )
        )

    return PortfolioCorrelationResponse(
        state=PortfolioDecisionState.READY,
        state_reason_code="ready",
        state_reason_detail="correlation_ready",
        as_of_ledger_at=summary_response.as_of_ledger_at,
        as_of_market_at=summary_response.pricing_snapshot_captured_at,
        evaluated_at=evaluated_at,
        freshness_policy=PortfolioDecisionFreshnessPolicy(max_age_hours=_DECISION_FRESHNESS_HOURS),
        symbols=symbols,
        guardrail_max_symbols=_CORRELATION_MAX_SYMBOLS,
        rows=correlation_rows,
    )
