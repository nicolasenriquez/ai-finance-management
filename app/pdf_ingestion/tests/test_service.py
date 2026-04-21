"""Unit tests for the PDF ingestion service."""

from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.pdf_ingestion.service import (
    PdfIngestionClientError,
    build_metadata_storage_key,
    build_storage_key,
    compute_sha256_digest,
    ingest_pdf_bytes,
    load_ingestion_result_from_storage,
)


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


def test_compute_sha256_digest_is_deterministic() -> None:
    """SHA-256 helper should return the same digest for the same payload."""

    payload = b"pdf-bytes"

    assert compute_sha256_digest(payload) == compute_sha256_digest(payload)
    assert len(compute_sha256_digest(payload)) == 64


def test_build_storage_key_uses_generated_document_id() -> None:
    """Storage key should be generated from document ID, not client filename."""

    storage_key = build_storage_key("doc123")

    assert storage_key == "doc123.pdf"
    assert "/" not in storage_key


def test_build_metadata_storage_key_uses_pdf_storage_key() -> None:
    """Metadata key should stay adjacent to the stored PDF."""

    metadata_key = build_metadata_storage_key("doc123.pdf")

    assert metadata_key == "doc123.metadata.json"
    assert "/" not in metadata_key


def test_ingest_pdf_bytes_stores_file_and_returns_metadata(tmp_path: Path) -> None:
    """Valid upload should be hashed, stored, and preflighted."""

    document_bytes = _load_text_pdf_bytes()

    result = ingest_pdf_bytes(
        document_bytes=document_bytes,
        original_filename="../../unsafe-name.pdf",
        content_type="application/pdf",
        storage_root=tmp_path,
        max_upload_bytes=20 * 1024 * 1024,
        max_page_count=100,
        min_text_chars=20,
    )

    assert result.document_id
    assert result.original_filename == "../../unsafe-name.pdf"
    assert result.sha256 == compute_sha256_digest(document_bytes)
    assert result.storage_key.endswith(".pdf")
    assert "/" not in result.storage_key
    assert (tmp_path / result.storage_key).exists()
    assert (tmp_path / build_metadata_storage_key(result.storage_key)).exists()
    assert result.preflight.status == "extractable"


def test_load_ingestion_result_from_storage_returns_manifest_metadata(
    tmp_path: Path,
) -> None:
    """Stored ingestion metadata should be recoverable by storage key."""

    ingested_result = ingest_pdf_bytes(
        document_bytes=_load_text_pdf_bytes(),
        original_filename="statement.pdf",
        content_type="application/pdf",
        storage_root=tmp_path,
        max_upload_bytes=20 * 1024 * 1024,
        max_page_count=100,
        min_text_chars=20,
    )

    loaded_result = load_ingestion_result_from_storage(
        storage_key=ingested_result.storage_key,
        storage_root=tmp_path,
    )

    assert loaded_result == ingested_result


def test_load_ingestion_result_from_storage_rejects_missing_manifest(
    tmp_path: Path,
) -> None:
    """Missing metadata manifests should fail explicitly."""

    storage_key = "statement.pdf"
    (tmp_path / storage_key).write_bytes(_load_text_pdf_bytes())

    with pytest.raises(PdfIngestionClientError) as exc_info:
        load_ingestion_result_from_storage(
            storage_key=storage_key, storage_root=tmp_path
        )

    assert exc_info.value.status_code == 404


def test_ingest_pdf_bytes_rejects_oversized_upload(tmp_path: Path) -> None:
    """Uploads over the configured byte limit should fail explicitly."""

    document_bytes = _load_text_pdf_bytes()

    with pytest.raises(PdfIngestionClientError) as exc_info:
        ingest_pdf_bytes(
            document_bytes=document_bytes,
            original_filename="statement.pdf",
            content_type="application/pdf",
            storage_root=tmp_path,
            max_upload_bytes=len(document_bytes) - 1,
            max_page_count=100,
            min_text_chars=20,
        )

    assert exc_info.value.status_code == 413


def test_ingest_pdf_bytes_rejects_invalid_pdf_payload(tmp_path: Path) -> None:
    """Invalid PDF bytes should be rejected as client input errors."""

    with pytest.raises(PdfIngestionClientError) as exc_info:
        ingest_pdf_bytes(
            document_bytes=b"not-a-pdf",
            original_filename="statement.pdf",
            content_type="application/pdf",
            storage_root=tmp_path,
            max_upload_bytes=1024,
            max_page_count=50,
            min_text_chars=20,
        )

    assert exc_info.value.status_code == 400


def test_ingest_pdf_bytes_rejects_over_page_limit(tmp_path: Path) -> None:
    """PDFs over the configured page limit should be rejected."""

    document_bytes = _build_blank_pdf_bytes(page_count=2)

    with pytest.raises(PdfIngestionClientError) as exc_info:
        ingest_pdf_bytes(
            document_bytes=document_bytes,
            original_filename="statement.pdf",
            content_type="application/pdf",
            storage_root=tmp_path,
            max_upload_bytes=1024 * 1024,
            max_page_count=1,
            min_text_chars=20,
        )

    assert exc_info.value.status_code == 422
