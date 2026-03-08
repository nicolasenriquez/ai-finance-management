"""Unit tests for the PDF preflight service."""

from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.pdf_preflight.schemas import ExtractabilityStatus
from app.pdf_preflight.service import PdfPreflightError, analyze_pdf


def _load_text_pdf_bytes() -> bytes:
    """Load the repository golden-set PDF as a text-based fixture."""

    pdf_path = Path("app/golden_sets/dataset_1/202602_stocks.pdf")
    return pdf_path.read_bytes()


def _build_blank_pdf_bytes() -> bytes:
    """Create a blank PDF for low-text OCR-required tests."""

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)

    buffer = bytearray()
    from io import BytesIO

    bytes_buffer = BytesIO()
    writer.write(bytes_buffer)
    buffer.extend(bytes_buffer.getvalue())
    return bytes(buffer)


def _build_encrypted_pdf_bytes() -> bytes:
    """Create an encrypted PDF for preflight tests."""

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")

    from io import BytesIO

    bytes_buffer = BytesIO()
    writer.write(bytes_buffer)
    return bytes_buffer.getvalue()


def _build_empty_password_encrypted_pdf_bytes() -> bytes:
    """Create a PDF encrypted with an empty user password."""

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("", "secret")

    from io import BytesIO

    bytes_buffer = BytesIO()
    writer.write(bytes_buffer)
    return bytes_buffer.getvalue()


def test_analyze_pdf_returns_extractable_for_text_pdf() -> None:
    """Text-based PDFs should be marked extractable."""

    result = analyze_pdf(_load_text_pdf_bytes(), min_text_chars=20)

    assert result.status == ExtractabilityStatus.EXTRACTABLE
    assert result.encrypted is False
    assert result.page_count is not None
    assert result.page_count > 0
    assert result.extracted_text_char_count >= result.min_text_chars_required


def test_analyze_pdf_returns_ocr_required_for_blank_pdf() -> None:
    """Blank PDFs should fail preflight when OCR is not supported."""

    result = analyze_pdf(_build_blank_pdf_bytes(), min_text_chars=20)

    assert result.status == ExtractabilityStatus.OCR_REQUIRED
    assert result.encrypted is False
    assert result.page_count == 1
    assert result.extracted_text_char_count == 0


def test_analyze_pdf_returns_encrypted_for_encrypted_pdf() -> None:
    """Encrypted PDFs should be flagged without attempting extraction."""

    result = analyze_pdf(_build_encrypted_pdf_bytes(), min_text_chars=20)

    assert result.status == ExtractabilityStatus.ENCRYPTED
    assert result.encrypted is True
    assert result.extracted_text_char_count == 0
    assert result.page_count is None


def test_analyze_pdf_allows_empty_password_encrypted_pdf() -> None:
    """Readable encrypted PDFs should continue preflight analysis."""

    result = analyze_pdf(_build_empty_password_encrypted_pdf_bytes(), min_text_chars=20)

    assert result.status == ExtractabilityStatus.OCR_REQUIRED
    assert result.encrypted is True
    assert result.page_count == 1
    assert result.extracted_text_char_count == 0


def test_analyze_pdf_rejects_invalid_pdf_bytes() -> None:
    """Invalid bytes should raise a preflight error."""

    with pytest.raises(PdfPreflightError):
        analyze_pdf(b"not-a-pdf", min_text_chars=20)
