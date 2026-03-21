"""API tests for PDF ingestion endpoint."""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app
from app.pdf_ingestion.routes import settings as ingestion_settings
from app.pdf_ingestion.service import build_metadata_storage_key


def _build_blank_pdf_bytes(page_count: int = 1) -> bytes:
    """Create a blank PDF payload with a configurable page count."""

    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=200, height=200)

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _load_text_pdf_bytes() -> bytes:
    """Load the repository golden-set PDF fixture."""

    return Path("app/golden_sets/dataset_1/202602_stocks.pdf").read_bytes()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for route-level API tests."""

    return TestClient(app)


@pytest.fixture
def ingest_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Configure ingestion storage to use a temporary test directory."""

    monkeypatch.setattr(ingestion_settings, "pdf_upload_storage_root", str(tmp_path))
    return tmp_path


def test_ingest_endpoint_uploads_pdf_and_returns_preflight(
    client: TestClient, ingest_storage: Path
) -> None:
    """Successful upload should return metadata and preflight details."""

    response = client.post(
        "/api/pdf/ingest",
        files={
            "file": (
                "statement.pdf",
                _load_text_pdf_bytes(),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document_id"]
    assert body["original_filename"] == "statement.pdf"
    assert body["storage_key"].endswith(".pdf")
    assert not Path(body["storage_key"]).is_absolute()
    assert body["preflight"]["status"] == "extractable"
    assert (ingest_storage / body["storage_key"]).exists()
    assert (ingest_storage / build_metadata_storage_key(body["storage_key"])).exists()


def test_ingest_endpoint_rejects_non_pdf_content_type(
    client: TestClient, ingest_storage: Path
) -> None:
    """Non-PDF multipart uploads should return explicit client errors."""

    response = client.post(
        "/api/pdf/ingest",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415


def test_ingest_endpoint_rejects_over_page_limit(
    client: TestClient, ingest_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uploads above max page count should be rejected."""

    monkeypatch.setattr(ingestion_settings, "pdf_upload_max_pages", 1)

    response = client.post(
        "/api/pdf/ingest",
        files={
            "file": (
                "many-pages.pdf",
                _build_blank_pdf_bytes(page_count=2),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
