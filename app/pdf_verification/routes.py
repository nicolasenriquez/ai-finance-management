"""API routes for PDF verification."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.pdf_verification.schemas import PdfVerificationRequest, PdfVerificationResult
from app.pdf_verification.service import (
    PdfVerificationClientError,
    verify_pdf_from_storage,
)

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/pdf",
    tags=["pdf-verification"],
)


@router.post("/verify", response_model=PdfVerificationResult)
async def verify_pdf(request: PdfVerificationRequest) -> PdfVerificationResult:
    """Verify normalized dataset 1 records against the checked-in golden contract."""

    logger.info("pdf_verification.request_started", storage_key=request.storage_key)
    try:
        return verify_pdf_from_storage(
            storage_key=request.storage_key,
            storage_root=Path(settings.pdf_upload_storage_root),
        )
    except PdfVerificationClientError as exc:
        logger.info(
            "pdf_verification.request_rejected",
            storage_key=request.storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
