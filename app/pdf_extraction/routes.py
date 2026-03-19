"""API routes for PDF extraction."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.pdf_extraction.schemas import PdfExtractionRequest, PdfExtractionResult
from app.pdf_extraction.service import PdfExtractionClientError, extract_pdf_from_storage

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/pdf",
    tags=["pdf-extraction"],
)


@router.post(
    "/extract",
    response_model=PdfExtractionResult,
)
async def extract_pdf(request: PdfExtractionRequest) -> PdfExtractionResult:
    """Extract deterministic table rows from a stored PDF upload."""

    logger.info("pdf_extraction.request_started", storage_key=request.storage_key)
    try:
        return extract_pdf_from_storage(
            storage_key=request.storage_key,
            storage_root=Path(settings.pdf_upload_storage_root),
        )
    except PdfExtractionClientError as exc:
        logger.info(
            "pdf_extraction.request_rejected",
            storage_key=request.storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
