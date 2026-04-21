"""API routes for PDF normalization."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.pdf_normalization.schemas import (
    PdfNormalizationRequest,
    PdfNormalizationResult,
)
from app.pdf_normalization.service import (
    PdfNormalizationClientError,
    normalize_pdf_from_storage,
)

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/pdf",
    tags=["pdf-normalization"],
)


@router.post("/normalize", response_model=PdfNormalizationResult)
async def normalize_pdf(request: PdfNormalizationRequest) -> PdfNormalizationResult:
    """Normalize canonical dataset 1 records from a stored PDF upload."""

    logger.info("pdf_normalization.request_started", storage_key=request.storage_key)
    try:
        return normalize_pdf_from_storage(
            storage_key=request.storage_key,
            storage_root=Path(settings.pdf_upload_storage_root),
        )
    except PdfNormalizationClientError as exc:
        logger.info(
            "pdf_normalization.request_rejected",
            storage_key=request.storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
