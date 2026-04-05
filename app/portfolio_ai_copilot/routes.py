"""API routes for portfolio AI copilot chat workflows."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.portfolio_ai_copilot.schemas import (
    PortfolioCopilotChatRequest,
    PortfolioCopilotChatResponse,
)
from app.portfolio_ai_copilot.service import get_portfolio_copilot_chat_response

settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/portfolio",
    tags=["portfolio-ai-copilot"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/copilot/chat",
    response_model=PortfolioCopilotChatResponse,
)
async def post_portfolio_copilot_chat(
    request: PortfolioCopilotChatRequest,
    db: DbSession,
) -> PortfolioCopilotChatResponse:
    """Return one typed read-only copilot response for chat/opportunity requests."""

    return await get_portfolio_copilot_chat_response(db=db, request=request)
