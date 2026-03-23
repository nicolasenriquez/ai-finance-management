"""API routes for portfolio analytics."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.portfolio_analytics.schemas import (
    PortfolioLotDetailResponse,
    PortfolioSummaryResponse,
)
from app.portfolio_analytics.service import (
    PortfolioAnalyticsClientError,
    get_portfolio_lot_detail_response,
    get_portfolio_summary_response,
)

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/portfolio",
    tags=["portfolio-analytics"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


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
