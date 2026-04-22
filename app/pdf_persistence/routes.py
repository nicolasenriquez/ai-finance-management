"""API routes for PDF persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.pdf_persistence.schemas import PdfPersistenceRequest, PdfPersistenceResult
from app.pdf_persistence.service import (
    PdfPersistenceClientError,
    persist_pdf_from_storage,
)

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/pdf",
    tags=["pdf-persistence"],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/persist", response_model=PdfPersistenceResult)
async def persist_pdf(request: PdfPersistenceRequest, db: DbSession) -> PdfPersistenceResult:
    """Persist canonical dataset 1 records for a stored PDF upload."""

    logger.info("pdf_persistence.request_started", storage_key=request.storage_key)
    try:
        result = await persist_pdf_from_storage(
            storage_key=request.storage_key,
            storage_root=Path(settings.pdf_upload_storage_root),
            db=db,
        )
    except PdfPersistenceClientError as exc:
        logger.info(
            "pdf_persistence.request_rejected",
            storage_key=request.storage_key,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc

    logger.info(
        "pdf_persistence.request_completed",
        storage_key=result.storage_key,
        source_document_id=result.source_document_id,
        source_document_status=result.source_document_status.value,
        import_job_id=result.import_job_id,
        inserted_records=result.summary.inserted_records,
        duplicate_records=result.summary.duplicate_records,
    )
    return result
