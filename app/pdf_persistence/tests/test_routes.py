"""Fail-first route and integration tests for PDF persistence."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine
from app.main import app
from app.pdf_ingestion.service import build_metadata_storage_key
from app.pdf_persistence.service import persist_pdf_from_storage

_GOLDEN_PDF_PATH = Path("app/golden_sets/dataset_1/202602_stocks.pdf")


def _load_text_pdf_bytes() -> bytes:
    """Load dataset 1 PDF bytes from repository fixtures."""

    return _GOLDEN_PDF_PATH.read_bytes()


def _load_persistence_routes_module() -> ModuleType:
    """Load persistence routes module in fail-first mode."""

    try:
        module = import_module("app.pdf_persistence.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.pdf_persistence.routes. "
            "Implement task 3.2 before persistence route tests can pass.",
        )
        raise AssertionError from exc

    return module


def _persistence_endpoint_path() -> str:
    """Return persistence endpoint path and fail fast when route is not registered."""

    module = _load_persistence_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.pdf_persistence.routes.settings is missing. "
            "Task 3.2 should expose configured route settings.",
        )

    path = f"{settings.api_prefix}/pdf/persist"
    registered_paths = {
        path
        for route in app.routes
        for path in [getattr(route, "path", None)]
        if isinstance(path, str)
    }
    if path not in registered_paths:
        pytest.fail(
            f"Fail-first baseline: persistence route {path} is not registered in app.main. "
            "Implement task 3.2 before this test can pass.",
        )
    return path


def _ingest_pdf(client: TestClient, *, filename: str) -> str:
    """Ingest dataset 1 PDF and return the generated storage key."""

    response = client.post(
        "/api/pdf/ingest",
        files={
            "file": (
                filename,
                _load_text_pdf_bytes(),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201
    response_payload = response.json()
    if not isinstance(response_payload, dict):
        pytest.fail("Ingestion response payload must be a JSON object.")
    storage_key = response_payload.get("storage_key")
    if not isinstance(storage_key, str):
        pytest.fail("Ingestion response must include string storage_key.")
    return storage_key


async def _truncate_persistence_tables() -> None:
    """Truncate persistence tables to keep route tests isolated."""

    settings = get_settings()
    cleanup_engine: AsyncEngine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )
    try:
        async with cleanup_engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE TABLE canonical_pdf_record, import_job, source_document "
                    "RESTART IDENTITY CASCADE"
                )
            )
    except SQLAlchemyError as exc:
        pytest.fail(
            "Route integration tests require migrated persistence tables. "
            "Run 'uv run alembic upgrade head' before testing."
        )
        raise AssertionError from exc
    finally:
        await cleanup_engine.dispose()


@pytest.fixture(autouse=True)
def reset_persistence_tables() -> None:
    """Reset persistence tables between tests for deterministic assertions."""

    engine.sync_engine.dispose()
    asyncio.run(_truncate_persistence_tables())


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Create a test client for route-level API tests."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def persist_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Configure persistence upload storage to use a temporary test directory."""

    module = _load_persistence_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.pdf_persistence.routes.settings is missing. "
            "Task 3.2 should expose configured route settings.",
        )
    monkeypatch.setattr(settings, "pdf_upload_storage_root", str(tmp_path))
    return tmp_path


@pytest.mark.integration
def test_persist_endpoint_first_request_creates_document_and_inserts_records(
    client: TestClient,
    persist_storage: Path,
) -> None:
    """First persistence request should create a document and insert canonical records."""

    endpoint = _persistence_endpoint_path()
    storage_key = _ingest_pdf(client, filename="first.pdf")

    response = client.post(endpoint, json={"storage_key": storage_key})
    assert response.status_code in {200, 201}

    body = response.json()
    assert body["storage_key"] == storage_key
    assert body["source_document_status"] == "created"
    assert body["import_job_id"] >= 1
    assert body["summary"]["normalized_records"] >= 1
    assert body["summary"]["inserted_records"] >= 1
    assert body["summary"]["duplicate_records"] == 0


@pytest.mark.integration
def test_persist_endpoint_rerun_reuses_document_and_skips_duplicates(
    client: TestClient,
    persist_storage: Path,
) -> None:
    """Rerunning the same storage key should reuse document and skip duplicate records."""

    endpoint = _persistence_endpoint_path()
    storage_key = _ingest_pdf(client, filename="rerun.pdf")

    first_response = client.post(endpoint, json={"storage_key": storage_key})
    assert first_response.status_code in {200, 201}
    first_body = first_response.json()

    second_response = client.post(endpoint, json={"storage_key": storage_key})
    assert second_response.status_code in {200, 201}
    second_body = second_response.json()

    assert second_body["source_document_status"] == "reused"
    assert second_body["source_document_id"] == first_body["source_document_id"]
    assert second_body["import_job_id"] != first_body["import_job_id"]
    assert second_body["summary"]["inserted_records"] == 0
    assert (
        second_body["summary"]["duplicate_records"] == second_body["summary"]["normalized_records"]
    )


@pytest.mark.integration
def test_persist_endpoint_failed_request_leaves_no_partial_import_state(
    client: TestClient,
    persist_storage: Path,
) -> None:
    """A failed persistence request should not leave partial imported state."""

    endpoint = _persistence_endpoint_path()
    valid_storage_key = _ingest_pdf(client, filename="valid.pdf")
    valid_bytes = (persist_storage / valid_storage_key).read_bytes()

    invalid_storage_key = "corrupt-copy.pdf"
    invalid_pdf_path = persist_storage / invalid_storage_key
    invalid_pdf_path.write_bytes(valid_bytes)
    invalid_manifest_path = persist_storage / build_metadata_storage_key(invalid_storage_key)
    invalid_manifest_path.write_text("{invalid-json", encoding="utf-8")

    failed_response = client.post(endpoint, json={"storage_key": invalid_storage_key})
    assert failed_response.status_code >= 400

    recovery_response = client.post(endpoint, json={"storage_key": valid_storage_key})
    assert recovery_response.status_code in {200, 201}
    recovery_body = recovery_response.json()
    assert recovery_body["source_document_status"] == "created"
    assert recovery_body["summary"]["inserted_records"] >= 1


@pytest.mark.integration
async def test_persist_endpoint_concurrent_duplicate_requests_are_duplicate_safe(
    persist_storage: Path,
) -> None:
    """Concurrent persistence calls should avoid duplicate source-document rows."""

    with TestClient(app) as setup_client:
        storage_key = _ingest_pdf(setup_client, filename="concurrent.pdf")

    async def persist_once() -> dict[str, object]:
        async with AsyncSessionLocal() as db_session:
            result = await persist_pdf_from_storage(
                storage_key=storage_key,
                storage_root=persist_storage,
                db=db_session,
            )
            return result.model_dump(mode="json")

    first_body, second_body = await asyncio.wait_for(
        asyncio.gather(persist_once(), persist_once()),
        timeout=180.0,
    )

    assert first_body["source_document_id"] == second_body["source_document_id"]
    assert {first_body["source_document_status"], second_body["source_document_status"]} <= {
        "created",
        "reused",
    }


@pytest.mark.integration
def test_persist_endpoint_same_hash_different_storage_keys_reuse_first_document(
    client: TestClient,
    persist_storage: Path,
) -> None:
    """Same PDF bytes with later storage key should reuse first-seen source document."""

    endpoint = _persistence_endpoint_path()
    first_storage_key = _ingest_pdf(client, filename="first-seen.pdf")
    second_storage_key = _ingest_pdf(client, filename="later-copy.pdf")
    assert first_storage_key != second_storage_key

    first_response = client.post(endpoint, json={"storage_key": first_storage_key})
    assert first_response.status_code in {200, 201}
    first_body = first_response.json()

    second_response = client.post(endpoint, json={"storage_key": second_storage_key})
    assert second_response.status_code in {200, 201}
    second_body = second_response.json()

    assert first_body["source_document_status"] == "created"
    assert second_body["source_document_status"] == "reused"
    assert second_body["source_document_id"] == first_body["source_document_id"]
