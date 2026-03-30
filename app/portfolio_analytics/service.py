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
    PortfolioContributionResponse,
    PortfolioContributionRow,
    PortfolioHierarchyAssetRow,
    PortfolioHierarchyGroupBy,
    PortfolioHierarchyGroupRow,
    PortfolioHierarchyLotRow,
    PortfolioHierarchyResponse,
    PortfolioLotDetailResponse,
    PortfolioLotDetailRow,
    PortfolioQuantBenchmarkContext,
    PortfolioQuantMetric,
    PortfolioQuantMetricsResponse,
    PortfolioQuantReportGenerateRequest,
    PortfolioQuantReportGenerateResponse,
    PortfolioQuantReportLifecycleStatus,
    PortfolioQuantReportScope,
    PortfolioRiskEstimatorMetric,
    PortfolioRiskEstimatorsResponse,
    PortfolioSummaryResponse,
    PortfolioSummaryRow,
    PortfolioTimeSeriesPoint,
    PortfolioTimeSeriesResponse,
    PortfolioTransactionEvent,
    PortfolioTransactionsResponse,
)
from app.portfolio_ledger.models import DividendEvent, Lot, LotDisposition, PortfolioTransaction
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
    PortfolioChartPeriod.D252: 252,
    PortfolioChartPeriod.MAX: None,
}
_SUPPORTED_RISK_WINDOWS: set[int] = {30, 90, 252}
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
                required_points=window_days + 1,
                minimum_points=window_days + 1,
                insufficient_history_detail=(
                    f"Insufficient persisted history for risk window {window_days}."
                ),
            )
            price_frame = _build_aligned_price_frame(
                aligned_timestamps=aligned_timestamps,
                price_series_by_symbol=price_series_by_symbol,
            )
            computed_metrics = _compute_risk_metrics_from_price_frame(
                price_frame=price_frame,
                open_quantity_by_symbol=open_quantity_by_symbol,
                window_days=window_days,
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
            metrics = [
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
            response = PortfolioRiskEstimatorsResponse(
                as_of_ledger_at=as_of_ledger_at,
                window_days=window_days,
                metrics=metrics,
            )
    except MarketDataClientError as exc:
        logger.error(
            "portfolio_analytics.risk_estimators_failed",
            window_days=window_days,
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
        metric_count=len(response.metrics),
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

    for benchmark_field, candidate_symbols in _BENCHMARK_CANDIDATE_SYMBOLS_BY_ID.items():
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
    candidate_price_series_by_symbol: dict[str, Mapping[datetime, Decimal]] = {
        **optional_price_series_by_symbol,
        **price_series_by_symbol,
    }

    if scope == PortfolioQuantReportScope.PORTFOLIO:
        aligned_timestamps = _select_aligned_timestamps(
            price_series_by_symbol=price_series_by_symbol,
            required_points=required_points,
            minimum_points=2,
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


def _serialize_lot_disposition_row(lot_disposition: LotDisposition) -> dict[str, object]:
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
