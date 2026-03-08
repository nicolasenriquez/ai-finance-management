"""API tests for the PDF preflight endpoint."""

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app


def _build_blank_pdf_bytes() -> bytes:
    """Create a blank PDF payload."""

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _build_encrypted_pdf_bytes() -> bytes:
    """Create an encrypted PDF payload."""

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_preflight_endpoint_returns_extractable_for_text_pdf() -> None:
    """The preflight route should accept text-based PDF bytes."""

    client = TestClient(app)
    pdf_bytes = Path("app/golden_sets/dataset_1/202602_stocks.pdf").read_bytes()

    response = client.post(
        "/api/pdf/preflight",
        content=pdf_bytes,
        headers={"Content-Type": "application/pdf"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "extractable"
    assert body["encrypted"] is False


def test_preflight_endpoint_returns_ocr_required_for_blank_pdf() -> None:
    """Blank PDFs should return an OCR-required status."""

    client = TestClient(app)

    response = client.post(
        "/api/pdf/preflight",
        content=_build_blank_pdf_bytes(),
        headers={"Content-Type": "application/pdf"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ocr_required"


def test_preflight_endpoint_returns_encrypted_for_encrypted_pdf() -> None:
    """Encrypted PDFs should be reported as unsupported."""

    client = TestClient(app)

    response = client.post(
        "/api/pdf/preflight",
        content=_build_encrypted_pdf_bytes(),
        headers={"Content-Type": "application/pdf"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "encrypted"


def test_preflight_endpoint_rejects_non_pdf_content_type() -> None:
    """Only application/pdf requests should be accepted."""

    client = TestClient(app)

    response = client.post(
        "/api/pdf/preflight",
        content=b"hello",
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 415


def test_preflight_endpoint_rejects_invalid_pdf_payload() -> None:
    """Invalid PDF bytes should return a request error."""

    client = TestClient(app)

    response = client.post(
        "/api/pdf/preflight",
        content=b"not-a-pdf",
        headers={"Content-Type": "application/pdf"},
    )

    assert response.status_code == 400
