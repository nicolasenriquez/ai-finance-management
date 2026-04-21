"""Service layer for PDF preflight analysis."""

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.logging import get_logger
from app.pdf_preflight.schemas import ExtractabilityStatus, PdfPreflightResult

logger = get_logger(__name__)


class PdfPreflightError(ValueError):
    """Raised when the submitted bytes cannot be analyzed as a PDF."""

    pass


def _count_non_whitespace_characters(text: str) -> int:
    """Count non-whitespace characters in extracted text."""

    return sum(1 for character in text if not character.isspace())


def analyze_pdf(document_bytes: bytes, *, min_text_chars: int) -> PdfPreflightResult:
    """Analyze PDF extractability before running extraction.

    Args:
        document_bytes: Raw PDF bytes to inspect.
        min_text_chars: Minimum non-whitespace character threshold required
            for the PDF to be considered extractable without OCR.

    Returns:
        A typed preflight result that indicates whether extraction can proceed.

    Raises:
        PdfPreflightError: If the bytes are empty or not a valid PDF document.
    """
    if not document_bytes:
        raise PdfPreflightError("Request body must contain PDF bytes.")

    try:
        reader = PdfReader(BytesIO(document_bytes))
    except PdfReadError as exc:
        logger.error("pdf_preflight.analysis_failed", error=str(exc), exc_info=True)
        raise PdfPreflightError(
            "Submitted content is not a valid PDF document."
        ) from exc

    document_is_encrypted = reader.is_encrypted
    if document_is_encrypted:
        decrypt_result = reader.decrypt("")
        if decrypt_result == 0:
            result = PdfPreflightResult(
                status=ExtractabilityStatus.ENCRYPTED,
                message="PDF is encrypted and cannot be extracted without decryption support.",
                encrypted=True,
                page_count=None,
                extracted_text_char_count=0,
                min_text_chars_required=min_text_chars,
            )
            logger.info(
                "pdf_preflight.analysis_completed",
                status=result.status,
                encrypted=result.encrypted,
                page_count=result.page_count,
                extracted_text_char_count=result.extracted_text_char_count,
                min_text_chars_required=result.min_text_chars_required,
            )
            return result

    page_count = len(reader.pages)
    extracted_text_char_count = 0
    for page in reader.pages:
        page_text = page.extract_text() or ""
        extracted_text_char_count += _count_non_whitespace_characters(page_text)

    if extracted_text_char_count < min_text_chars:
        result = PdfPreflightResult(
            status=ExtractabilityStatus.OCR_REQUIRED,
            message="PDF does not contain enough extractable text; OCR would be required.",
            encrypted=document_is_encrypted,
            page_count=page_count,
            extracted_text_char_count=extracted_text_char_count,
            min_text_chars_required=min_text_chars,
        )
    else:
        result = PdfPreflightResult(
            status=ExtractabilityStatus.EXTRACTABLE,
            message="PDF contains enough extractable text to proceed.",
            encrypted=document_is_encrypted,
            page_count=page_count,
            extracted_text_char_count=extracted_text_char_count,
            min_text_chars_required=min_text_chars,
        )

    logger.info(
        "pdf_preflight.analysis_completed",
        status=result.status,
        encrypted=result.encrypted,
        page_count=result.page_count,
        extracted_text_char_count=result.extracted_text_char_count,
        min_text_chars_required=result.min_text_chars_required,
    )
    return result
