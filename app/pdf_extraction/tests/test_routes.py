"""API tests for PDF extraction endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pdf_extraction.routes import settings as extraction_settings

_GOLDEN_PDF_PATH = Path("app/golden_sets/dataset_1/202602_stocks.pdf")


def _load_text_pdf_bytes() -> bytes:
    """Load the repository golden-set PDF fixture."""

    return _GOLDEN_PDF_PATH.read_bytes()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for route-level API tests."""

    return TestClient(app)


@pytest.fixture
def extraction_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Configure extraction storage to use a temporary test directory."""

    monkeypatch.setattr(extraction_settings, "pdf_upload_storage_root", str(tmp_path))
    return tmp_path


def test_extract_endpoint_returns_dataset_1_tables(
    client: TestClient, extraction_storage: Path
) -> None:
    """Successful extraction returns deterministic table counts."""

    storage_key = "dataset_1.pdf"
    (extraction_storage / storage_key).write_bytes(_load_text_pdf_bytes())

    response = client.post(
        "/api/pdf/extract",
        json={"storage_key": storage_key},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "pdfplumber"
    assert body["storage_key"] == storage_key
    assert body["source_pdf_pages"] == 9

    counts_by_table = {
        table["table_name"]: len(table["rows"]) for table in body["tables"]
    }
    assert counts_by_table == {
        "compra_venta_activos": 136,
        "dividendos_recibidos": 34,
        "splits": 1,
    }


def test_extract_endpoint_rejects_missing_storage_key_file(
    client: TestClient, extraction_storage: Path
) -> None:
    """Extraction should fail clearly when file does not exist."""

    response = client.post(
        "/api/pdf/extract",
        json={"storage_key": "missing.pdf"},
    )

    assert response.status_code == 404
    assert "Stored PDF was not found" in response.json()["detail"]


def test_extract_endpoint_rejects_storage_key_path_traversal(
    client: TestClient, extraction_storage: Path
) -> None:
    """Extraction should reject storage keys escaping upload root."""

    response = client.post(
        "/api/pdf/extract",
        json={"storage_key": "../dataset_1.pdf"},
    )

    assert response.status_code == 400
    assert "inside the configured upload root" in response.json()["detail"]
