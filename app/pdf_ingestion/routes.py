"""API routes for PDF ingestion."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.pdf_ingestion.schemas import PdfIngestionResult
from app.pdf_ingestion.service import PdfIngestionClientError, ingest_pdf_bytes

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/pdf",
    tags=["pdf-ingestion"],
)

upload_file_field = File(...)


@router.post(
    "/ingest",
    response_model=PdfIngestionResult,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_pdf(file: UploadFile = upload_file_field) -> PdfIngestionResult:
    """Ingest an uploaded PDF through validation, storage, and preflight."""

    original_filename = file.filename or "uploaded.pdf"
    logger.info(
        "pdf_ingestion.upload_started",
        original_filename=original_filename,
        content_type=file.content_type,
    )

    try:
        document_bytes = await file.read()
        return ingest_pdf_bytes(
            document_bytes=document_bytes,
            original_filename=original_filename,
            content_type=file.content_type,
            storage_root=Path(settings.pdf_upload_storage_root),
            max_upload_bytes=settings.pdf_upload_max_bytes,
            max_page_count=settings.pdf_upload_max_pages,
            min_text_chars=settings.pdf_preflight_min_text_chars,
        )
    except PdfIngestionClientError as exc:
        logger.info(
            "pdf_ingestion.upload_rejected",
            original_filename=original_filename,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()
