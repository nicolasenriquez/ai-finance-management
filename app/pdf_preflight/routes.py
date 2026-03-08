"""API routes for PDF preflight analysis."""

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.pdf_preflight.schemas import PdfPreflightResult
from app.pdf_preflight.service import PdfPreflightError, analyze_pdf

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=f"{settings.api_prefix}/pdf",
    tags=["pdf-preflight"],
)


@router.post("/preflight", response_model=PdfPreflightResult)
async def preflight_pdf(request: Request) -> PdfPreflightResult:
    """Inspect a PDF and return whether extraction can proceed."""

    content_type_header = request.headers.get("content-type", "")
    content_type = content_type_header.split(";", maxsplit=1)[0].strip().lower()
    if content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be application/pdf.",
        )

    document_bytes = await request.body()

    try:
        return analyze_pdf(
            document_bytes,
            min_text_chars=settings.pdf_preflight_min_text_chars,
        )
    except PdfPreflightError as exc:
        logger.info("pdf_preflight.request_rejected", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
