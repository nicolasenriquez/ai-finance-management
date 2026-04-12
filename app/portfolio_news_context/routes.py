"""API routes for holdings-grounded portfolio news context."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.portfolio_news_context.schemas import PortfolioNewsContextResponse
from app.portfolio_news_context.service import get_portfolio_news_context_response

settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/portfolio/news",
    tags=["portfolio-news-context"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "/context",
    response_model=PortfolioNewsContextResponse,
)
async def get_portfolio_news_context(
    db: DbSession,
) -> PortfolioNewsContextResponse:
    """Return holdings-grounded news context with source provenance metadata."""

    return await get_portfolio_news_context_response(db=db)
