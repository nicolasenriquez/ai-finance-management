"""Service layer for PDF ingestion."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

from app.core.logging import get_logger
from app.pdf_ingestion.schemas import PdfIngestionResult
from app.pdf_preflight.service import PdfPreflightError, analyze_pdf

logger = get_logger(__name__)


class PdfIngestionClientError(ValueError):
    """Raised when client-provided upload input is invalid."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize client-facing ingestion error.

        Args:
            message: Human-readable error message for the API response.
            status_code: HTTP status code that should be returned.
        """
        super().__init__(message)
        self.status_code = status_code


def compute_sha256_digest(document_bytes: bytes) -> str:
    """Compute SHA-256 digest for uploaded bytes.

    Args:
        document_bytes: Raw bytes of the uploaded PDF.

    Returns:
        Lowercase hexadecimal SHA-256 digest string.
    """
    return sha256(document_bytes).hexdigest()


def count_pdf_pages(document_bytes: bytes) -> int | None:
    """Read a PDF page count when possible.

    Args:
        document_bytes: Raw bytes of the uploaded PDF.

    Returns:
        Number of pages when determinable, otherwise `None` for
        encrypted PDFs that cannot be decrypted with an empty password.

    Raises:
        PdfIngestionClientError: If the bytes are empty or not a valid PDF.
    """
    if not document_bytes:
        raise PdfIngestionClientError(
            "Uploaded file is empty.",
            status_code=400,
        )

    try:
        reader = PdfReader(BytesIO(document_bytes))
    except PdfReadError as exc:
        raise PdfIngestionClientError(
            "Submitted content is not a valid PDF document.",
            status_code=400,
        ) from exc

    if reader.is_encrypted and reader.decrypt("") == 0:
        return None

    try:
        return len(reader.pages)
    except FileNotDecryptedError:
        return None
    except PdfReadError as exc:
        raise PdfIngestionClientError(
            "Submitted content is not a valid PDF document.",
            status_code=400,
        ) from exc


def build_storage_key(document_id: str) -> str:
    """Build a storage key from generated document metadata.

    Args:
        document_id: Generated upload document identifier.

    Returns:
        Relative storage key that does not include absolute paths.
    """
    return f"{document_id}.pdf"


def ingest_pdf_bytes(
    *,
    document_bytes: bytes,
    original_filename: str,
    content_type: str | None,
    storage_root: Path,
    max_upload_bytes: int,
    max_page_count: int,
    min_text_chars: int,
) -> PdfIngestionResult:
    """Validate, hash, store, and preflight uploaded PDF bytes.

    Args:
        document_bytes: Raw PDF bytes from the upload payload.
        original_filename: Original filename provided by client.
        content_type: Content type declared by the upload request.
        storage_root: Base directory where accepted PDFs are stored.
        max_upload_bytes: Maximum allowed upload size in bytes.
        max_page_count: Maximum allowed page count for accepted PDFs.
        min_text_chars: Configured preflight text threshold.

    Returns:
        Typed ingestion result with metadata and nested preflight output.

    Raises:
        PdfIngestionClientError: If upload validation fails.
        OSError: If file storage fails unexpectedly.
    """
    normalized_content_type = (content_type or "").split(";", maxsplit=1)[0].strip().lower()
    if normalized_content_type != "application/pdf":
        raise PdfIngestionClientError(
            "Upload must use Content-Type application/pdf.",
            status_code=415,
        )

    file_size_bytes = len(document_bytes)
    if file_size_bytes > max_upload_bytes:
        raise PdfIngestionClientError(
            f"Uploaded PDF exceeds max size of {max_upload_bytes} bytes.",
            status_code=413,
        )

    page_count = count_pdf_pages(document_bytes)
    if page_count is not None and page_count > max_page_count:
        raise PdfIngestionClientError(
            f"Uploaded PDF exceeds max page count of {max_page_count}.",
            status_code=422,
        )

    document_id = uuid4().hex
    storage_key = build_storage_key(document_id)
    storage_path = storage_root / storage_key
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(document_bytes)

    try:
        preflight_result = analyze_pdf(document_bytes, min_text_chars=min_text_chars)
    except PdfPreflightError as exc:
        raise PdfIngestionClientError(str(exc), status_code=400) from exc

    response_page_count = page_count if page_count is not None else preflight_result.page_count
    response = PdfIngestionResult(
        document_id=document_id,
        original_filename=original_filename,
        content_type=normalized_content_type,
        file_size_bytes=file_size_bytes,
        sha256=compute_sha256_digest(document_bytes),
        page_count=response_page_count,
        storage_key=storage_key,
        preflight=preflight_result,
    )

    logger.info(
        "pdf_ingestion.upload_completed",
        document_id=response.document_id,
        original_filename=response.original_filename,
        storage_key=response.storage_key,
        page_count=response.page_count,
        file_size_bytes=response.file_size_bytes,
        preflight_status=response.preflight.status,
    )
    return response
