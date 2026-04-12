"""API routes for portfolio rebalancing strategy comparisons."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.portfolio_rebalancing.schemas import (
    PortfolioRebalancingScenarioRequest,
    PortfolioRebalancingScenarioResponse,
    PortfolioRebalancingStrategiesResponse,
)
from app.portfolio_rebalancing.service import (
    get_portfolio_rebalancing_scenario_response,
    get_portfolio_rebalancing_strategies_response,
)

settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/portfolio/rebalancing",
    tags=["portfolio-rebalancing"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "/strategies",
    response_model=PortfolioRebalancingStrategiesResponse,
)
async def get_portfolio_rebalancing_strategies(
    db: DbSession,
) -> PortfolioRebalancingStrategiesResponse:
    """Return read-only MVO/HRP/Black-Litterman strategy comparisons."""

    return await get_portfolio_rebalancing_strategies_response(db=db)


@router.post(
    "/scenario",
    response_model=PortfolioRebalancingScenarioResponse,
)
async def post_portfolio_rebalancing_scenario(
    request: PortfolioRebalancingScenarioRequest,
    db: DbSession,
) -> PortfolioRebalancingScenarioResponse:
    """Return constrained scenario diagnostics with infeasible-state metadata."""

    return await get_portfolio_rebalancing_scenario_response(
        db=db,
        request=request,
    )
