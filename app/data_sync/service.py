"""Service orchestration for local dataset bootstrap and market refresh commands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Final, Literal, cast

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.data_sync.schemas import (
    DatasetBootstrapRunResult,
    DataSyncLocalRunResult,
    PortfolioLedgerRebuildRunResult,
)
from app.market_data.schemas import MarketDataRefreshRunResult
from app.market_data.service import MarketDataClientError, refresh_yfinance_supported_universe
from app.pdf_ingestion.service import PdfIngestionClientError, ingest_pdf_bytes
from app.pdf_persistence.service import PdfPersistenceClientError, persist_pdf_from_storage
from app.portfolio_ledger.service import (
    PortfolioLedgerClientError,
    rebuild_portfolio_ledger_from_canonical_records,
)

logger = get_logger(__name__)

_DEFAULT_DATASET_1_PDF_PATH: Final[Path] = Path("app/golden_sets/dataset_1/202602_stocks.pdf")
_REFRESH_SCOPE_MODES: Final[frozenset[str]] = frozenset({"core", "100", "200"})

DataSyncRefreshScopeMode = Literal["core", "100", "200"]


class DataSyncClientError(ValueError):
    """Raised when local data-sync command workflows cannot complete safely."""

    status_code: int
    stage: str

    def __init__(self, message: str, *, status_code: int, stage: str) -> None:
        """Initialize client-facing data-sync orchestration error."""

        super().__init__(message)
        self.status_code = status_code
        self.stage = stage


async def run_dataset1_bootstrap(
    *,
    db: AsyncSession,
    dataset_pdf_path: Path | None = None,
    settings: Settings | None = None,
) -> DatasetBootstrapRunResult:
    """Run dataset_1 ingest -> persist -> rebuild using existing service seams."""

    effective_settings = settings if settings is not None else get_settings()
    resolved_dataset_pdf_path = _resolve_dataset_pdf_path(dataset_pdf_path=dataset_pdf_path)
    storage_root = Path(effective_settings.pdf_upload_storage_root)

    logger.info(
        "data_sync.bootstrap_started",
        dataset_pdf_path=str(resolved_dataset_pdf_path),
        storage_root=str(storage_root),
    )

    try:
        document_bytes = resolved_dataset_pdf_path.read_bytes()
    except OSError as exc:
        logger.error(
            "data_sync.bootstrap_failed",
            stage="input",
            dataset_pdf_path=str(resolved_dataset_pdf_path),
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise DataSyncClientError(
            f"Dataset bootstrap failed while reading PDF: {resolved_dataset_pdf_path}.",
            status_code=500,
            stage="input",
        ) from exc

    try:
        ingestion_result = ingest_pdf_bytes(
            document_bytes=document_bytes,
            original_filename=resolved_dataset_pdf_path.name,
            content_type="application/pdf",
            storage_root=storage_root,
            max_upload_bytes=effective_settings.pdf_upload_max_bytes,
            max_page_count=effective_settings.pdf_upload_max_pages,
            min_text_chars=effective_settings.pdf_preflight_min_text_chars,
        )
    except PdfIngestionClientError as exc:
        logger.error(
            "data_sync.bootstrap_failed",
            stage="ingest",
            dataset_pdf_path=str(resolved_dataset_pdf_path),
            error=str(exc),
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            exc_info=True,
        )
        raise DataSyncClientError(
            f"Dataset bootstrap failed during ingest stage: {exc}",
            status_code=exc.status_code,
            stage="ingest",
        ) from exc

    try:
        persistence_result = await persist_pdf_from_storage(
            storage_key=ingestion_result.storage_key,
            storage_root=storage_root,
            db=db,
        )
    except PdfPersistenceClientError as exc:
        logger.error(
            "data_sync.bootstrap_failed",
            stage="persist",
            storage_key=ingestion_result.storage_key,
            error=str(exc),
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            exc_info=True,
        )
        raise DataSyncClientError(
            f"Dataset bootstrap failed during persist stage: {exc}",
            status_code=exc.status_code,
            stage="persist",
        ) from exc

    try:
        rebuild_payload = await rebuild_portfolio_ledger_from_canonical_records(
            source_document_id=persistence_result.source_document_id,
            db=db,
        )
    except PortfolioLedgerClientError as exc:
        logger.error(
            "data_sync.bootstrap_failed",
            stage="rebuild",
            source_document_id=persistence_result.source_document_id,
            error=str(exc),
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            exc_info=True,
        )
        raise DataSyncClientError(
            f"Dataset bootstrap failed during rebuild stage: {exc}",
            status_code=exc.status_code,
            stage="rebuild",
        ) from exc

    try:
        rebuild_result = PortfolioLedgerRebuildRunResult.model_validate(rebuild_payload)
    except ValidationError as exc:
        logger.error(
            "data_sync.bootstrap_failed",
            stage="rebuild",
            source_document_id=persistence_result.source_document_id,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise DataSyncClientError(
            "Dataset bootstrap rebuild stage returned unsupported evidence payload.",
            status_code=500,
            stage="rebuild",
        ) from exc

    result = DatasetBootstrapRunResult(
        dataset_pdf_path=str(resolved_dataset_pdf_path),
        storage_key=ingestion_result.storage_key,
        source_document_id=persistence_result.source_document_id,
        import_job_id=persistence_result.import_job_id,
        normalized_records=persistence_result.summary.normalized_records,
        inserted_records=persistence_result.summary.inserted_records,
        duplicate_records=persistence_result.summary.duplicate_records,
        rebuild=rebuild_result,
    )
    logger.info(
        "data_sync.bootstrap_completed",
        dataset_pdf_path=result.dataset_pdf_path,
        storage_key=result.storage_key,
        source_document_id=result.source_document_id,
        import_job_id=result.import_job_id,
        inserted_records=result.inserted_records,
        duplicate_records=result.duplicate_records,
        processed_records=result.rebuild.processed_records,
    )
    return result


async def run_market_refresh_yfinance(
    *,
    db: AsyncSession,
    refresh_scope_mode: str | None = None,
    snapshot_captured_at: datetime | None = None,
    settings: Settings | None = None,
) -> MarketDataRefreshRunResult:
    """Run one explicit yfinance supported-universe market refresh."""

    resolved_refresh_scope_mode = _normalize_refresh_scope_mode(refresh_scope_mode)
    logger.info(
        "data_sync.market_refresh_started",
        source_provider="yfinance",
        refresh_scope_mode=resolved_refresh_scope_mode,
    )
    try:
        result = await refresh_yfinance_supported_universe(
            db=db,
            refresh_scope_mode=resolved_refresh_scope_mode,
            snapshot_captured_at=snapshot_captured_at,
            settings=settings,
        )
    except MarketDataClientError as exc:
        logger.error(
            "data_sync.market_refresh_failed",
            source_provider="yfinance",
            refresh_scope_mode=resolved_refresh_scope_mode,
            error=str(exc),
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            exc_info=True,
        )
        raise DataSyncClientError(
            f"YFinance market refresh failed: {exc}",
            status_code=exc.status_code,
            stage="market_refresh",
        ) from exc

    logger.info(
        "data_sync.market_refresh_completed",
        source_provider=result.source_provider,
        refresh_scope_mode=result.refresh_scope_mode,
        snapshot_id=result.snapshot_id,
        snapshot_key=result.snapshot_key,
        requested_symbols_count=result.requested_symbols_count,
        inserted_prices=result.inserted_prices,
        updated_prices=result.updated_prices,
        retry_attempted_symbols_count=result.retry_attempted_symbols_count,
        failed_symbols_count=result.failed_symbols_count,
        history_fallback_symbols_count=len(result.history_fallback_symbols),
        currency_assumed_symbols_count=len(result.currency_assumed_symbols),
    )
    return result


async def run_data_sync_local(
    *,
    db: AsyncSession,
    dataset_pdf_path: Path | None = None,
    refresh_scope_mode: str | None = None,
    snapshot_captured_at: datetime | None = None,
    settings: Settings | None = None,
) -> DataSyncLocalRunResult:
    """Run local bootstrap first, then yfinance market refresh with fail-fast semantics."""

    resolved_refresh_scope_mode = _normalize_refresh_scope_mode(refresh_scope_mode)
    logger.info(
        "data_sync.local_sync_started",
        source_provider="yfinance",
        refresh_scope_mode=resolved_refresh_scope_mode,
    )
    try:
        bootstrap_result = await run_dataset1_bootstrap(
            db=db,
            dataset_pdf_path=dataset_pdf_path,
            settings=settings,
        )
        market_refresh_result = await run_market_refresh_yfinance(
            db=db,
            refresh_scope_mode=resolved_refresh_scope_mode,
            snapshot_captured_at=snapshot_captured_at,
            settings=settings,
        )
    except DataSyncClientError as exc:
        logger.error(
            "data_sync.local_sync_failed",
            stage=exc.stage,
            error=str(exc),
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            exc_info=True,
        )
        raise

    result = DataSyncLocalRunResult(
        bootstrap=bootstrap_result,
        market_refresh=market_refresh_result,
    )
    logger.info(
        "data_sync.local_sync_completed",
        source_document_id=result.bootstrap.source_document_id,
        import_job_id=result.bootstrap.import_job_id,
        refresh_scope_mode=result.market_refresh.refresh_scope_mode,
        snapshot_id=result.market_refresh.snapshot_id,
        snapshot_key=result.market_refresh.snapshot_key,
        requested_symbols_count=result.market_refresh.requested_symbols_count,
        retry_attempted_symbols_count=result.market_refresh.retry_attempted_symbols_count,
        failed_symbols_count=result.market_refresh.failed_symbols_count,
        history_fallback_symbols_count=len(result.market_refresh.history_fallback_symbols),
        currency_assumed_symbols_count=len(result.market_refresh.currency_assumed_symbols),
    )
    return result


def _resolve_dataset_pdf_path(*, dataset_pdf_path: Path | None) -> Path:
    """Resolve and validate dataset_1 PDF path for local bootstrap commands."""

    candidate_path = dataset_pdf_path or _DEFAULT_DATASET_1_PDF_PATH
    if candidate_path.suffix.lower() != ".pdf":
        raise DataSyncClientError(
            "Dataset bootstrap input must point to a PDF file.",
            status_code=422,
            stage="input",
        )

    if not candidate_path.is_file():
        raise DataSyncClientError(
            f"Dataset bootstrap PDF file was not found: {candidate_path}.",
            status_code=404,
            stage="input",
        )
    return candidate_path


def _normalize_refresh_scope_mode(
    refresh_scope_mode: str | None,
) -> DataSyncRefreshScopeMode:
    """Normalize refresh-scope selector to one supported typed mode."""

    if refresh_scope_mode is None:
        return "core"

    if refresh_scope_mode not in _REFRESH_SCOPE_MODES:
        raise DataSyncClientError(
            "YFinance market refresh failed: refresh_scope_mode must be one of: core, 100, 200.",
            status_code=422,
            stage="market_refresh",
        )
    return cast(DataSyncRefreshScopeMode, refresh_scope_mode)
