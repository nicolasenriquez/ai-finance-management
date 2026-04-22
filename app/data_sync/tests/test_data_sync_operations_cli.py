"""Unit tests for local data-sync CLI command entrypoints."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.data_sync.schemas import (
    DatasetBootstrapRunResult,
    DataSyncLocalRunResult,
    PortfolioLedgerRebuildRunResult,
)
from app.data_sync.service import DataSyncClientError
from app.market_data.schemas import MarketDataRefreshRunResult
from scripts import data_sync_operations


class _FakeSessionContext:
    """Minimal async context manager that returns one opaque DB handle."""

    async def __aenter__(self) -> object:
        """Enter context returning one fake database object."""

        return object()

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: object | None,
    ) -> bool:
        """Exit context without suppressing exceptions."""

        return False


def _fake_session_local() -> _FakeSessionContext:
    """Build one fake AsyncSessionLocal replacement for CLI unit tests."""

    return _FakeSessionContext()


def test_parse_iso_datetime_accepts_z_suffix() -> None:
    """Datetime parser should accept Z suffix and normalize to UTC-aware values."""

    parsed = data_sync_operations.parse_iso_datetime("2026-03-25T18:00:00Z")

    assert parsed == datetime(2026, 3, 25, 18, 0, tzinfo=UTC)


def test_parse_iso_datetime_rejects_naive_values() -> None:
    """Datetime parser should reject values without explicit timezone offset."""

    with pytest.raises(SystemExit):
        data_sync_operations.build_parser().parse_args(
            [
                "market-refresh-yfinance",
                "--snapshot-captured-at",
                "2026-03-25T18:00:00",
            ]
        )


def test_parse_refresh_scope_rejects_unsupported_value() -> None:
    """CLI parser should reject unsupported refresh-scope selectors."""

    with pytest.raises(SystemExit):
        data_sync_operations.build_parser().parse_args(
            [
                "market-refresh-yfinance",
                "--refresh-scope",
                "999",
            ]
        )


@pytest.mark.asyncio
async def test_async_main_bootstrap_prints_json_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Bootstrap command should emit deterministic JSON result and exit zero."""

    async def fake_bootstrap(
        *,
        db: object,
        dataset_pdf_path: Path | None,
        settings: object | None = None,
    ) -> DatasetBootstrapRunResult:
        del db
        del settings
        assert dataset_pdf_path == Path("custom_dataset.pdf")
        return DatasetBootstrapRunResult(
            dataset_pdf_path="custom_dataset.pdf",
            storage_key="uploads/custom_dataset.pdf",
            source_document_id=7,
            import_job_id=9,
            normalized_records=3,
            inserted_records=3,
            duplicate_records=0,
            rebuild=PortfolioLedgerRebuildRunResult(
                source_document_id=7,
                processed_records=3,
                portfolio_transactions=2,
                dividend_events=1,
                corporate_action_events=0,
                open_lots=2,
                lot_dispositions=0,
            ),
        )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "data_sync_operations.py",
            "data-bootstrap-dataset1",
            "--dataset-pdf-path",
            "custom_dataset.pdf",
        ],
    )
    monkeypatch.setattr("app.core.database.AsyncSessionLocal", _fake_session_local)
    monkeypatch.setattr(data_sync_operations, "run_dataset1_bootstrap", fake_bootstrap)

    exit_code = await data_sync_operations.async_main()

    assert exit_code == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["status"] == "completed"
    assert parsed["source_document_id"] == 7
    assert parsed["rebuild"]["processed_records"] == 3


@pytest.mark.asyncio
async def test_async_main_market_refresh_emits_fail_fast_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Market refresh command should emit structured failure payload and exit non-zero."""

    async def fake_refresh(
        *,
        db: object,
        refresh_scope_mode: str | None,
        snapshot_captured_at: datetime | None,
        settings: object | None = None,
    ) -> MarketDataRefreshRunResult:
        del db
        assert refresh_scope_mode is None
        del snapshot_captured_at
        del settings
        raise DataSyncClientError(
            "YFinance market refresh failed: Provider timeout.",
            status_code=502,
            stage="market_refresh",
        )

    monkeypatch.setattr(sys, "argv", ["data_sync_operations.py", "market-refresh-yfinance"])
    monkeypatch.setattr("app.core.database.AsyncSessionLocal", _fake_session_local)
    monkeypatch.setattr(data_sync_operations, "run_market_refresh_yfinance", fake_refresh)

    exit_code = await data_sync_operations.async_main()

    assert exit_code == 1
    stderr_payload = json.loads(capsys.readouterr().err)
    assert stderr_payload["status"] == "failed"
    assert stderr_payload["stage"] == "market_refresh"
    assert stderr_payload["status_code"] == 502


@pytest.mark.asyncio
async def test_async_main_data_sync_local_passes_both_optional_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Combined local sync command should pass optional dataset and snapshot arguments."""

    expected_snapshot = datetime(2026, 3, 25, 18, 30, tzinfo=UTC)

    async def fake_data_sync_local(
        *,
        db: object,
        dataset_pdf_path: Path | None,
        refresh_scope_mode: str | None,
        snapshot_captured_at: datetime | None,
        settings: object | None = None,
    ) -> DataSyncLocalRunResult:
        del db
        del settings
        assert dataset_pdf_path == Path("dataset_override.pdf")
        assert refresh_scope_mode == "200"
        assert snapshot_captured_at == expected_snapshot
        return DataSyncLocalRunResult(
            bootstrap=DatasetBootstrapRunResult(
                dataset_pdf_path="dataset_override.pdf",
                storage_key="uploads/dataset_override.pdf",
                source_document_id=11,
                import_job_id=13,
                normalized_records=10,
                inserted_records=10,
                duplicate_records=0,
                rebuild=PortfolioLedgerRebuildRunResult(
                    source_document_id=11,
                    processed_records=10,
                    portfolio_transactions=8,
                    dividend_events=2,
                    corporate_action_events=0,
                    open_lots=5,
                    lot_dispositions=3,
                ),
            ),
            market_refresh=MarketDataRefreshRunResult(
                source_type="market_data_provider",
                source_provider="yfinance",
                refresh_scope_mode="core",
                requested_symbols=["AMD", "VOO"],
                requested_symbols_count=2,
                snapshot_key="yfinance-supported-2026-03-25",
                snapshot_captured_at=expected_snapshot,
                snapshot_id=21,
                inserted_prices=2,
                updated_prices=0,
                retry_attempted_symbols=["AMD"],
                retry_attempted_symbols_count=1,
                failed_symbols=[],
                failed_symbols_count=0,
                history_fallback_symbols=["AMD"],
                history_fallback_periods_by_symbol={"AMD": "1y"},
                currency_assumed_symbols=["AMD"],
            ),
        )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "data_sync_operations.py",
            "data-sync-local",
            "--dataset-pdf-path",
            "dataset_override.pdf",
            "--snapshot-captured-at",
            "2026-03-25T18:30:00Z",
            "--refresh-scope",
            "200",
        ],
    )
    monkeypatch.setattr("app.core.database.AsyncSessionLocal", _fake_session_local)
    monkeypatch.setattr(data_sync_operations, "run_data_sync_local", fake_data_sync_local)

    exit_code = await data_sync_operations.async_main()

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["bootstrap"]["source_document_id"] == 11
    assert payload["market_refresh"]["source_provider"] == "yfinance"
    assert payload["market_refresh"]["history_fallback_symbols"] == ["AMD"]
    assert payload["market_refresh"]["currency_assumed_symbols"] == ["AMD"]


@pytest.mark.asyncio
async def test_async_main_market_refresh_passes_refresh_scope_argument(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Market refresh command should propagate explicit refresh scope to service layer."""

    expected_snapshot = datetime(2026, 3, 25, 18, 30, tzinfo=UTC)

    async def fake_refresh(
        *,
        db: object,
        refresh_scope_mode: str | None,
        snapshot_captured_at: datetime | None,
        settings: object | None = None,
    ) -> MarketDataRefreshRunResult:
        del db
        del settings
        assert refresh_scope_mode == "100"
        assert snapshot_captured_at == expected_snapshot
        return MarketDataRefreshRunResult(
            source_type="market_data_provider",
            source_provider="yfinance",
            refresh_scope_mode="100",
            requested_symbols=["AMD", "VOO"],
            requested_symbols_count=2,
            snapshot_key="yfinance-supported-2026-03-25",
            snapshot_captured_at=expected_snapshot,
            snapshot_id=31,
            inserted_prices=2,
            updated_prices=0,
            history_fallback_symbols=["AMD"],
            history_fallback_periods_by_symbol={"AMD": "1y"},
            currency_assumed_symbols=["AMD"],
        )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "data_sync_operations.py",
            "market-refresh-yfinance",
            "--snapshot-captured-at",
            "2026-03-25T18:30:00Z",
            "--refresh-scope",
            "100",
        ],
    )
    monkeypatch.setattr("app.core.database.AsyncSessionLocal", _fake_session_local)
    monkeypatch.setattr(data_sync_operations, "run_market_refresh_yfinance", fake_refresh)

    exit_code = await data_sync_operations.async_main()

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["refresh_scope_mode"] == "100"
    assert payload["history_fallback_symbols"] == ["AMD"]
    assert payload["currency_assumed_symbols"] == ["AMD"]
