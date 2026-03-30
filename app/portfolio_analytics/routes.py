"""API routes for portfolio analytics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.portfolio_analytics.schemas import (
    PortfolioChartPeriod,
    PortfolioContributionResponse,
    PortfolioHierarchyGroupBy,
    PortfolioHierarchyResponse,
    PortfolioLotDetailResponse,
    PortfolioQuantMetricsResponse,
    PortfolioQuantReportGenerateRequest,
    PortfolioQuantReportGenerateResponse,
    PortfolioQuantReportScope,
    PortfolioRiskEstimatorsResponse,
    PortfolioSummaryResponse,
    PortfolioTimeSeriesResponse,
    PortfolioTransactionsResponse,
)
from app.portfolio_analytics.service import (
    PortfolioAnalyticsClientError,
    generate_portfolio_quant_report_response,
    get_portfolio_contribution_response,
    get_portfolio_hierarchy_response,
    get_portfolio_lot_detail_response,
    get_portfolio_quant_metrics_response,
    get_portfolio_quant_report_html_content,
    get_portfolio_risk_estimators_response,
    get_portfolio_summary_response,
    get_portfolio_time_series_response,
    get_portfolio_transactions_response,
    normalize_chart_period,
    normalize_chart_scope,
)

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/portfolio",
    tags=["portfolio-analytics"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _response_field(response: object, field_name: str) -> object | None:
    """Read one response field from either typed model instances or dict-like mocks."""

    if isinstance(response, Mapping):
        mapped_response = cast(Mapping[str, object], response)
        return mapped_response.get(field_name)
    return getattr(response, field_name, None)


def _response_list_len(response: object, field_name: str) -> int:
    """Return list length from one field for structured logging."""

    field_value = _response_field(response, field_name)
    if isinstance(field_value, list):
        typed_list = cast(list[object], field_value)
        return len(typed_list)
    return 0


def _response_isoformat(response: object, field_name: str) -> str | None:
    """Return ISO-8601 string value for one datetime-like field."""

    field_value = _response_field(response, field_name)
    if hasattr(field_value, "isoformat"):
        isoformat_method = getattr(field_value, "isoformat", None)
        if callable(isoformat_method):
            return str(isoformat_method())
    if isinstance(field_value, str):
        return field_value
    return None


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(db: DbSession) -> PortfolioSummaryResponse:
    """Return grouped portfolio analytics computed from persisted ledger data."""

    logger.info("portfolio_analytics.summary_request_started")
    try:
        response = await get_portfolio_summary_response(db=db)
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.summary_request_rejected",
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.summary_request_completed",
        row_count=len(response.rows),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


@router.get(
    "/lots/{instrument_symbol}",
    response_model=PortfolioLotDetailResponse,
)
async def get_portfolio_lot_detail(
    instrument_symbol: str,
    db: DbSession,
) -> PortfolioLotDetailResponse:
    """Return explainable lot-detail analytics for one instrument symbol."""

    logger.info(
        "portfolio_analytics.lot_detail_request_started",
        instrument_symbol=instrument_symbol,
    )
    try:
        response = await get_portfolio_lot_detail_response(
            instrument_symbol=instrument_symbol,
            db=db,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.lot_detail_request_rejected",
            instrument_symbol=instrument_symbol,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.lot_detail_request_completed",
        instrument_symbol=response.instrument_symbol,
        lot_count=len(response.lots),
        as_of_ledger_at=response.as_of_ledger_at.isoformat(),
    )
    return response


@router.get(
    "/time-series",
    response_model=PortfolioTimeSeriesResponse,
)
async def get_portfolio_time_series(
    db: DbSession,
    period: Annotated[
        str,
        Query(description="Supported chart period enum: 30D, 90D, 252D, MAX."),
    ] = PortfolioChartPeriod.D30.value,
    scope: Annotated[
        str,
        Query(description=("Supported chart scope enum: portfolio, instrument_symbol.")),
    ] = PortfolioQuantReportScope.PORTFOLIO.value,
    instrument_symbol: Annotated[
        str | None,
        Query(description="Instrument symbol required when scope=instrument_symbol."),
    ] = None,
) -> PortfolioTimeSeriesResponse:
    """Return chart-ready portfolio time-series with explicit temporal metadata."""

    try:
        normalized_period = normalize_chart_period(period_value=period)
        normalized_scope, normalized_instrument_symbol = normalize_chart_scope(
            scope_value=scope,
            instrument_symbol_value=instrument_symbol,
        )
        logger.info(
            "portfolio_analytics.time_series_request_started",
            period=normalized_period.value,
            scope=normalized_scope.value,
            instrument_symbol=normalized_instrument_symbol,
        )
        response = await get_portfolio_time_series_response(
            db=db,
            period=normalized_period,
            scope=normalized_scope,
            instrument_symbol=normalized_instrument_symbol,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.time_series_request_rejected",
            period=period,
            scope=scope,
            instrument_symbol=instrument_symbol,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.time_series_request_completed",
        period=normalized_period.value,
        scope=normalized_scope.value,
        instrument_symbol=normalized_instrument_symbol,
        point_count=_response_list_len(response, "points"),
        as_of_ledger_at=_response_isoformat(response, "as_of_ledger_at"),
    )
    return response


@router.get(
    "/contribution",
    response_model=PortfolioContributionResponse,
)
async def get_portfolio_contribution(
    db: DbSession,
    period: Annotated[
        str,
        Query(description="Supported chart period enum: 30D, 90D, 252D, MAX."),
    ] = PortfolioChartPeriod.D30.value,
) -> PortfolioContributionResponse:
    """Return per-symbol contribution aggregates for selected chart period."""

    try:
        normalized_period = normalize_chart_period(period_value=period)
        logger.info(
            "portfolio_analytics.contribution_request_started",
            period=normalized_period.value,
        )
        response = await get_portfolio_contribution_response(
            db=db,
            period=normalized_period,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.contribution_request_rejected",
            period=period,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.contribution_request_completed",
        period=normalized_period.value,
        row_count=_response_list_len(response, "rows"),
        as_of_ledger_at=_response_isoformat(response, "as_of_ledger_at"),
    )
    return response


@router.get(
    "/risk-estimators",
    response_model=PortfolioRiskEstimatorsResponse,
)
async def get_portfolio_risk_estimators(
    db: DbSession,
    window_days: Annotated[
        int,
        Query(description="Supported v1 risk windows: 30, 90, 252."),
    ] = 30,
) -> PortfolioRiskEstimatorsResponse:
    """Return bounded portfolio risk metrics with explicit methodology metadata."""

    logger.info(
        "portfolio_analytics.risk_estimators_request_started",
        window_days=window_days,
    )
    try:
        response = await get_portfolio_risk_estimators_response(
            db=db,
            window_days=window_days,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.risk_estimators_request_rejected",
            window_days=window_days,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.risk_estimators_request_completed",
        window_days=window_days,
        metric_count=_response_list_len(response, "metrics"),
        as_of_ledger_at=_response_isoformat(response, "as_of_ledger_at"),
    )
    return response


@router.get(
    "/quant-metrics",
    response_model=PortfolioQuantMetricsResponse,
)
async def get_portfolio_quant_metrics(
    db: DbSession,
    period: Annotated[
        str,
        Query(description="Supported chart period enum: 30D, 90D, 252D, MAX."),
    ] = PortfolioChartPeriod.D90.value,
) -> PortfolioQuantMetricsResponse:
    """Return QuantStats-derived metrics for the selected portfolio chart period."""

    try:
        normalized_period = normalize_chart_period(period_value=period)
        logger.info(
            "portfolio_analytics.quant_metrics_request_started",
            period=normalized_period.value,
        )
        response = await get_portfolio_quant_metrics_response(
            db=db,
            period=normalized_period,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.quant_metrics_request_rejected",
            period=period,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.quant_metrics_request_completed",
        period=normalized_period.value,
        metric_count=_response_list_len(response, "metrics"),
        benchmark_symbol=_response_field(response, "benchmark_symbol"),
        as_of_ledger_at=_response_isoformat(response, "as_of_ledger_at"),
    )
    return response


@router.post(
    "/quant-reports",
    response_model=PortfolioQuantReportGenerateResponse,
    status_code=201,
)
async def generate_portfolio_quant_report(
    request: PortfolioQuantReportGenerateRequest,
    db: DbSession,
) -> PortfolioQuantReportGenerateResponse:
    """Generate one bounded QuantStats HTML tearsheet and return retrieval metadata."""

    logger.info(
        "portfolio_analytics.quant_report_request_started",
        scope=request.scope.value,
        period=request.period.value,
        instrument_symbol=request.instrument_symbol,
    )
    try:
        response = await generate_portfolio_quant_report_response(
            db=db,
            request=request,
            api_prefix=settings.api_prefix,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.quant_report_request_rejected",
            scope=request.scope.value,
            period=request.period.value,
            instrument_symbol=request.instrument_symbol,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.quant_report_request_completed",
        report_id=response.report_id,
        lifecycle_status=response.lifecycle_status.value,
        scope=response.scope.value,
        period=response.period.value,
        instrument_symbol=response.instrument_symbol,
        benchmark_symbol=response.benchmark_symbol,
    )
    return response


@router.get(
    "/quant-reports/{report_id}",
    response_class=HTMLResponse,
)
async def get_portfolio_quant_report_html(
    report_id: str,
) -> HTMLResponse:
    """Return one generated QuantStats tearsheet HTML artifact by report id."""

    logger.info(
        "portfolio_analytics.quant_report_artifact_request_started",
        report_id=report_id,
    )
    try:
        html_content = get_portfolio_quant_report_html_content(
            report_id=report_id,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.quant_report_artifact_request_rejected",
            report_id=report_id,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.quant_report_artifact_request_completed",
        report_id=report_id,
        content_length=len(html_content),
    )
    return HTMLResponse(content=html_content, status_code=200)


@router.get(
    "/hierarchy",
    response_model=PortfolioHierarchyResponse,
)
async def get_portfolio_hierarchy(
    db: DbSession,
    group_by: Annotated[
        PortfolioHierarchyGroupBy,
        Query(description="Hierarchy grouping: sector or symbol."),
    ] = PortfolioHierarchyGroupBy.SECTOR,
) -> PortfolioHierarchyResponse:
    """Return home-view portfolio hierarchy rows grouped by sector or symbol."""

    logger.info(
        "portfolio_analytics.hierarchy_request_started",
        group_by=group_by.value,
    )
    try:
        response = await get_portfolio_hierarchy_response(
            db=db,
            group_by=group_by,
        )
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.hierarchy_request_rejected",
            group_by=group_by.value,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.hierarchy_request_completed",
        group_by=group_by.value,
        group_count=_response_list_len(response, "groups"),
        as_of_ledger_at=_response_isoformat(response, "as_of_ledger_at"),
    )
    return response


@router.get(
    "/transactions",
    response_model=PortfolioTransactionsResponse,
)
async def get_portfolio_transactions(
    db: DbSession,
) -> PortfolioTransactionsResponse:
    """Return persisted ledger-event history for transactions workspace route."""

    logger.info("portfolio_analytics.transactions_request_started")
    try:
        response = await get_portfolio_transactions_response(db=db)
    except PortfolioAnalyticsClientError as exc:
        logger.info(
            "portfolio_analytics.transactions_request_rejected",
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "portfolio_analytics.transactions_request_completed",
        event_count=_response_list_len(response, "events"),
        as_of_ledger_at=_response_isoformat(response, "as_of_ledger_at"),
    )
    return response
