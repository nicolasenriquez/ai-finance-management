"""API routes for portfolio ML signal contracts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.portfolio_ml.schemas import (
    PortfolioMLAnomaliesResponse,
    PortfolioMLClustersResponse,
    PortfolioMLForecastResponse,
    PortfolioMLRegistryResponse,
    PortfolioMLScope,
    PortfolioMLSignalResponse,
)
from app.portfolio_ml.service import (
    PortfolioMLClientError,
    get_portfolio_ml_anomalies_response,
    get_portfolio_ml_clusters_response,
    get_portfolio_ml_forecast_response,
    get_portfolio_ml_registry_response,
    get_portfolio_ml_signal_response,
)

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/portfolio/ml",
    tags=["portfolio-ml"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/signals", response_model=PortfolioMLSignalResponse)
async def get_portfolio_ml_signals(
    scope: Annotated[PortfolioMLScope, Query()] = PortfolioMLScope.PORTFOLIO,
    instrument_symbol: Annotated[str | None, Query()] = None,
) -> PortfolioMLSignalResponse:
    """Return one typed read-only portfolio ML signal payload."""

    logger.info(
        "portfolio_ml.signal_request_started",
        scope=scope.value,
        instrument_symbol=instrument_symbol,
    )

    if scope is PortfolioMLScope.INSTRUMENT_SYMBOL and (
        instrument_symbol is None or instrument_symbol.strip() == ""
    ):
        logger.info(
            "portfolio_ml.signal_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=422,
            error="instrument_symbol is required when scope=instrument_symbol.",
        )
        raise HTTPException(
            status_code=422,
            detail="instrument_symbol is required when scope=instrument_symbol.",
        )

    try:
        response_payload = await get_portfolio_ml_signal_response(
            scope=scope,
            instrument_symbol=instrument_symbol,
        )
    except PortfolioMLClientError as exc:
        logger.info(
            "portfolio_ml.signal_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    response = PortfolioMLSignalResponse.model_validate(response_payload)

    logger.info(
        "portfolio_ml.signal_request_completed",
        scope=scope.value,
        instrument_symbol=response.instrument_symbol,
        state=response.state.value,
        signal_count=len(response.signals),
    )
    return response


@router.get("/clusters", response_model=PortfolioMLClustersResponse)
async def get_portfolio_ml_clusters(
    db: DbSession,
    scope: Annotated[PortfolioMLScope, Query()] = PortfolioMLScope.PORTFOLIO,
    instrument_symbol: Annotated[str | None, Query()] = None,
) -> PortfolioMLClustersResponse:
    """Return one typed read-only portfolio ML clustering payload."""

    logger.info(
        "portfolio_ml.cluster_request_started",
        scope=scope.value,
        instrument_symbol=instrument_symbol,
    )
    if scope is PortfolioMLScope.INSTRUMENT_SYMBOL and (
        instrument_symbol is None or instrument_symbol.strip() == ""
    ):
        logger.info(
            "portfolio_ml.cluster_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=422,
            error="instrument_symbol is required when scope=instrument_symbol.",
        )
        raise HTTPException(
            status_code=422,
            detail="instrument_symbol is required when scope=instrument_symbol.",
        )

    try:
        response_payload = await get_portfolio_ml_clusters_response(
            scope=scope,
            instrument_symbol=instrument_symbol,
            db=db,
        )
    except PortfolioMLClientError as exc:
        logger.info(
            "portfolio_ml.cluster_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    response = PortfolioMLClustersResponse.model_validate(response_payload)
    logger.info(
        "portfolio_ml.cluster_request_completed",
        scope=scope.value,
        instrument_symbol=response.instrument_symbol,
        state=response.state.value,
        row_count=len(response.rows),
    )
    return response


@router.get("/anomalies", response_model=PortfolioMLAnomaliesResponse)
async def get_portfolio_ml_anomalies(
    db: DbSession,
    scope: Annotated[PortfolioMLScope, Query()] = PortfolioMLScope.PORTFOLIO,
    instrument_symbol: Annotated[str | None, Query()] = None,
) -> PortfolioMLAnomaliesResponse:
    """Return one typed read-only portfolio ML anomaly payload."""

    logger.info(
        "portfolio_ml.anomaly_request_started",
        scope=scope.value,
        instrument_symbol=instrument_symbol,
    )
    if scope is PortfolioMLScope.INSTRUMENT_SYMBOL and (
        instrument_symbol is None or instrument_symbol.strip() == ""
    ):
        logger.info(
            "portfolio_ml.anomaly_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=422,
            error="instrument_symbol is required when scope=instrument_symbol.",
        )
        raise HTTPException(
            status_code=422,
            detail="instrument_symbol is required when scope=instrument_symbol.",
        )

    try:
        response_payload = await get_portfolio_ml_anomalies_response(
            scope=scope,
            instrument_symbol=instrument_symbol,
            db=db,
        )
    except PortfolioMLClientError as exc:
        logger.info(
            "portfolio_ml.anomaly_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    response = PortfolioMLAnomaliesResponse.model_validate(response_payload)
    logger.info(
        "portfolio_ml.anomaly_request_completed",
        scope=scope.value,
        instrument_symbol=response.instrument_symbol,
        state=response.state.value,
        row_count=len(response.rows),
    )
    return response


@router.get("/forecasts", response_model=PortfolioMLForecastResponse)
async def get_portfolio_ml_forecasts(
    db: DbSession,
    scope: Annotated[PortfolioMLScope, Query()] = PortfolioMLScope.PORTFOLIO,
    instrument_symbol: Annotated[str | None, Query()] = None,
) -> PortfolioMLForecastResponse:
    """Return one typed read-only portfolio ML forecast payload."""

    logger.info(
        "portfolio_ml.forecast_request_started",
        scope=scope.value,
        instrument_symbol=instrument_symbol,
    )

    if scope is PortfolioMLScope.INSTRUMENT_SYMBOL and (
        instrument_symbol is None or instrument_symbol.strip() == ""
    ):
        logger.info(
            "portfolio_ml.forecast_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=422,
            error="instrument_symbol is required when scope=instrument_symbol.",
        )
        raise HTTPException(
            status_code=422,
            detail="instrument_symbol is required when scope=instrument_symbol.",
        )

    try:
        response_payload = await get_portfolio_ml_forecast_response(
            scope=scope,
            instrument_symbol=instrument_symbol,
            db=db,
        )
    except PortfolioMLClientError as exc:
        logger.info(
            "portfolio_ml.forecast_request_rejected",
            scope=scope.value,
            instrument_symbol=instrument_symbol,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    response = PortfolioMLForecastResponse.model_validate(response_payload)
    logger.info(
        "portfolio_ml.forecast_request_completed",
        scope=scope.value,
        instrument_symbol=response.instrument_symbol,
        state=response.state.value,
        horizon_count=len(response.horizons),
    )
    return response


@router.get("/registry", response_model=PortfolioMLRegistryResponse)
async def get_portfolio_ml_registry(
    db: DbSession,
    scope: Annotated[str | None, Query()] = None,
    model_family: Annotated[str | None, Query()] = None,
    lifecycle_state: Annotated[str | None, Query()] = None,
) -> PortfolioMLRegistryResponse:
    """Return one typed read-only model-registry audit payload."""

    logger.info(
        "portfolio_ml.registry_request_started",
        scope=scope,
        model_family=model_family,
        lifecycle_state=lifecycle_state,
    )
    try:
        response_payload = await get_portfolio_ml_registry_response(
            db=db,
            scope=scope,
            model_family=model_family,
            lifecycle_state=lifecycle_state,
        )
    except PortfolioMLClientError as exc:
        logger.info(
            "portfolio_ml.registry_request_rejected",
            scope=scope,
            model_family=model_family,
            lifecycle_state=lifecycle_state,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    response = PortfolioMLRegistryResponse.model_validate(response_payload)
    logger.info(
        "portfolio_ml.registry_request_completed",
        state=response.state.value,
        row_count=len(response.rows),
    )
    return response
