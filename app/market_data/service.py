"""Service boundary for market-data write and read operations."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal, cast

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.market_data.models import MarketDataSnapshot, PriceHistory
from app.market_data.providers.yfinance_adapter import (
    YFinanceAdapterConfig,
    YFinanceAdapterError,
    YFinanceNormalizedRow,
    build_yfinance_adapter_config,
    fetch_yfinance_daily_close_rows,
)
from app.market_data.schemas import (
    MarketDataPriceRow,
    MarketDataPriceWrite,
    MarketDataRefreshRunResult,
    MarketDataSnapshotWriteRequest,
    MarketDataSnapshotWriteResult,
)
from app.shared.models import utcnow

logger = get_logger(__name__)

_SYMBOL_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9][A-Z0-9.\-]*$")
_YFINANCE_SOURCE_TYPE: Final[str] = "market_data_provider"
_YFINANCE_SOURCE_PROVIDER: Final[str] = "yfinance"
_SUPPORTED_LIBRARY_SIZES: Final[frozenset[int]] = frozenset({100, 200})
_REFRESH_SCOPE_MODES: Final[frozenset[str]] = frozenset({"core", "100", "200"})

MarketDataRefreshScopeMode = Literal["core", "100", "200"]


@dataclass(frozen=True)
class _NormalizedPriceWrite:
    """Normalized and validated market-data price row."""

    instrument_symbol: str
    market_timestamp: datetime | None
    trading_date: date | None
    price_value: Decimal
    currency_code: str
    source_payload: dict[str, object] | None

    def dedup_key(self) -> str:
        """Return deterministic in-request key used for duplicate detection."""

        market_timestamp_key = (
            self.market_timestamp.isoformat() if self.market_timestamp is not None else "none"
        )
        trading_date_key = (
            self.trading_date.isoformat() if self.trading_date is not None else "none"
        )
        return f"{self.instrument_symbol}|{market_timestamp_key}|{trading_date_key}"


@dataclass(frozen=True)
class _YFinanceRefreshPlan:
    """One deterministic yfinance refresh plan for consistent ingest behavior."""

    normalized_symbols: list[str]
    normalized_snapshot_captured_at: datetime
    provider_config: YFinanceAdapterConfig
    snapshot_key: str


@dataclass(frozen=True)
class _YFinanceScopeFetchResult:
    """Fetched yfinance rows and recovery diagnostics for one refresh scope run."""

    rows: list[YFinanceNormalizedRow]
    provider_metadata: dict[str, object]
    retry_attempted_symbols: list[str]
    failed_symbols: list[str]
    history_fallback_symbols: list[str]
    history_fallback_periods_by_symbol: dict[str, str]
    currency_assumed_symbols: list[str]


@dataclass(frozen=True)
class _MarketDataSymbolUniverse:
    """Versioned market-data symbol universe loaded from repository JSON."""

    required_portfolio_symbols: tuple[str, ...]
    core_refresh_symbols: tuple[str, ...]
    starter_100_symbols: tuple[str, ...]
    starter_200_symbols: tuple[str, ...]

    @property
    def supported_scope(self) -> frozenset[str]:
        """Return current supported ingestion scope as normalized symbol set."""

        return frozenset(self.starter_200_symbols)


@dataclass(frozen=True)
class MarketDataConsistentSnapshotCoverage:
    """One consistent persisted snapshot coverage for required symbols in USD."""

    snapshot_id: int
    snapshot_key: str
    snapshot_captured_at: datetime
    latest_close_price_usd_by_symbol: dict[str, Decimal]


class MarketDataClientError(ValueError):
    """Raised when market-data boundary input cannot be processed safely."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize client-facing market-data error."""

        super().__init__(message)
        self.status_code = status_code


async def ingest_yfinance_daily_close_snapshot(
    *,
    db: AsyncSession,
    symbols: list[str],
    snapshot_captured_at: datetime | None = None,
    settings: Settings | None = None,
) -> MarketDataSnapshotWriteResult:
    """Fetch and persist yfinance day-level close rows through market-data ingestion."""

    refresh_plan = _build_yfinance_refresh_plan(
        symbols=symbols,
        snapshot_captured_at=snapshot_captured_at,
        settings=settings,
    )

    logger.info(
        "market_data.provider_ingest_started",
        source_provider=_YFINANCE_SOURCE_PROVIDER,
        requested_symbols=len(refresh_plan.normalized_symbols),
        period=refresh_plan.provider_config.period,
        interval=refresh_plan.provider_config.interval,
    )

    try:
        fetched_rows, provider_metadata = await fetch_yfinance_daily_close_rows(
            symbols=tuple(refresh_plan.normalized_symbols),
            config=refresh_plan.provider_config,
        )
    except YFinanceAdapterError as exc:
        logger.error(
            "market_data.provider_ingest_failed",
            source_provider=_YFINANCE_SOURCE_PROVIDER,
            requested_symbols=refresh_plan.normalized_symbols,
            period=refresh_plan.provider_config.period,
            interval=refresh_plan.provider_config.interval,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise MarketDataClientError(
            _normalize_adapter_error_message_for_market_data(message=str(exc)),
            status_code=exc.status_code,
        ) from exc

    price_rows = [_to_price_write(row=row) for row in fetched_rows]
    snapshot_metadata: dict[str, object] = {
        **provider_metadata,
        "requested_symbols": refresh_plan.normalized_symbols,
        "response_rows": len(price_rows),
    }

    ingest_result = await ingest_market_data_snapshot(
        db=db,
        request=MarketDataSnapshotWriteRequest(
            source_type=_YFINANCE_SOURCE_TYPE,
            source_provider=_YFINANCE_SOURCE_PROVIDER,
            snapshot_key=refresh_plan.snapshot_key,
            snapshot_captured_at=refresh_plan.normalized_snapshot_captured_at,
            snapshot_metadata=snapshot_metadata,
            prices=price_rows,
        ),
    )
    logger.info(
        "market_data.provider_ingest_completed",
        source_provider=_YFINANCE_SOURCE_PROVIDER,
        requested_symbols=len(refresh_plan.normalized_symbols),
        response_rows=len(price_rows),
        snapshot_id=ingest_result.snapshot_id,
        inserted_prices=ingest_result.inserted_prices,
        updated_prices=ingest_result.updated_prices,
    )
    return ingest_result


async def refresh_yfinance_supported_universe(
    *,
    db: AsyncSession,
    refresh_scope_mode: str | None = None,
    snapshot_captured_at: datetime | None = None,
    settings: Settings | None = None,
) -> MarketDataRefreshRunResult:
    """Run one operator-facing full refresh for the supported symbol universe."""

    normalized_refresh_scope_mode = _normalize_refresh_scope_mode(refresh_scope_mode)
    supported_symbols = _resolve_refresh_scope_symbols(
        refresh_scope_mode=normalized_refresh_scope_mode,
        settings=settings,
    )
    refresh_plan = _build_yfinance_refresh_plan(
        symbols=supported_symbols,
        snapshot_captured_at=snapshot_captured_at,
        settings=settings,
    )
    logger.info(
        "market_data.refresh_started",
        source_provider=_YFINANCE_SOURCE_PROVIDER,
        refresh_scope="supported_universe",
        refresh_scope_mode=normalized_refresh_scope_mode,
        requested_symbols=refresh_plan.normalized_symbols,
        requested_symbols_count=len(refresh_plan.normalized_symbols),
        snapshot_key=refresh_plan.snapshot_key,
    )

    retry_attempted_symbols: list[str] = []
    failed_symbols: list[str] = []
    history_fallback_symbols: list[str] = []
    history_fallback_periods_by_symbol: dict[str, str] = {}
    currency_assumed_symbols: list[str] = []
    try:
        if normalized_refresh_scope_mode == "core":
            ingest_result = await ingest_yfinance_daily_close_snapshot(
                db=db,
                symbols=refresh_plan.normalized_symbols,
                snapshot_captured_at=refresh_plan.normalized_snapshot_captured_at,
                settings=settings,
            )
        else:
            fetch_result = await _fetch_yfinance_rows_with_non_portfolio_tolerance(
                symbols=refresh_plan.normalized_symbols,
                provider_config=refresh_plan.provider_config,
                settings=settings,
            )
            retry_attempted_symbols = fetch_result.retry_attempted_symbols
            failed_symbols = fetch_result.failed_symbols
            history_fallback_symbols = fetch_result.history_fallback_symbols
            history_fallback_periods_by_symbol = fetch_result.history_fallback_periods_by_symbol
            currency_assumed_symbols = fetch_result.currency_assumed_symbols
            ingest_result = await _ingest_fetched_yfinance_scope_rows(
                db=db,
                refresh_plan=refresh_plan,
                fetched_rows=fetch_result.rows,
                provider_metadata=fetch_result.provider_metadata,
            )
    except MarketDataClientError as exc:
        logger.error(
            "market_data.refresh_failed",
            source_provider=_YFINANCE_SOURCE_PROVIDER,
            refresh_scope="supported_universe",
            refresh_scope_mode=normalized_refresh_scope_mode,
            requested_symbols=refresh_plan.normalized_symbols,
            requested_symbols_count=len(refresh_plan.normalized_symbols),
            snapshot_key=refresh_plan.snapshot_key,
            error=str(exc),
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            retry_attempted_symbols_count=len(retry_attempted_symbols),
            failed_symbols_count=len(failed_symbols),
            exc_info=True,
        )
        raise

    refresh_result = MarketDataRefreshRunResult(
        source_type=_YFINANCE_SOURCE_TYPE,
        source_provider=_YFINANCE_SOURCE_PROVIDER,
        refresh_scope_mode=normalized_refresh_scope_mode,
        requested_symbols=refresh_plan.normalized_symbols,
        requested_symbols_count=len(refresh_plan.normalized_symbols),
        snapshot_key=refresh_plan.snapshot_key,
        snapshot_captured_at=refresh_plan.normalized_snapshot_captured_at,
        snapshot_id=ingest_result.snapshot_id,
        inserted_prices=ingest_result.inserted_prices,
        updated_prices=ingest_result.updated_prices,
        retry_attempted_symbols=retry_attempted_symbols,
        retry_attempted_symbols_count=len(retry_attempted_symbols),
        failed_symbols=failed_symbols,
        failed_symbols_count=len(failed_symbols),
        history_fallback_symbols=history_fallback_symbols,
        history_fallback_periods_by_symbol=history_fallback_periods_by_symbol,
        currency_assumed_symbols=currency_assumed_symbols,
    )
    logger.info(
        "market_data.refresh_completed",
        source_provider=refresh_result.source_provider,
        refresh_scope="supported_universe",
        refresh_scope_mode=refresh_result.refresh_scope_mode,
        status=refresh_result.status,
        snapshot_id=refresh_result.snapshot_id,
        snapshot_key=refresh_result.snapshot_key,
        requested_symbols_count=refresh_result.requested_symbols_count,
        inserted_prices=refresh_result.inserted_prices,
        updated_prices=refresh_result.updated_prices,
        retry_attempted_symbols_count=refresh_result.retry_attempted_symbols_count,
        failed_symbols_count=refresh_result.failed_symbols_count,
        history_fallback_symbols_count=len(refresh_result.history_fallback_symbols),
        currency_assumed_symbols_count=len(refresh_result.currency_assumed_symbols),
    )
    return refresh_result


async def _fetch_yfinance_rows_with_non_portfolio_tolerance(
    *,
    symbols: list[str],
    provider_config: YFinanceAdapterConfig,
    settings: Settings | None,
) -> _YFinanceScopeFetchResult:
    """Fetch per symbol with one retry pass; fail-fast only on required symbol failures."""

    universe = _get_market_data_symbol_universe(settings=settings)
    required_portfolio_symbols = set(universe.required_portfolio_symbols)

    fetched_rows: list[YFinanceNormalizedRow] = []
    rows_by_symbol: dict[str, int] = {}
    currencies_by_symbol: dict[str, str] = {}
    history_fallback_symbols: list[str] = []
    history_fallback_periods_by_symbol: dict[str, str] = {}
    currency_assumed_symbols: list[str] = []
    first_pass_errors: dict[str, YFinanceAdapterError] = {}

    for symbol_index, symbol in enumerate(symbols):
        await _sleep_for_symbol_spacing(
            symbol_index=symbol_index,
            request_spacing_seconds=provider_config.request_spacing_seconds,
        )
        try:
            symbol_rows, symbol_metadata = await fetch_yfinance_daily_close_rows(
                symbols=(symbol,),
                config=provider_config,
            )
        except YFinanceAdapterError as exc:
            first_pass_errors[symbol] = exc
            continue
        fetched_rows.extend(symbol_rows)
        rows_by_symbol[symbol] = len(symbol_rows)
        currency_code = _extract_symbol_currency_from_metadata(
            metadata=symbol_metadata,
            symbol=symbol,
            rows=symbol_rows,
        )
        if currency_code is not None:
            currencies_by_symbol[symbol] = currency_code
        _merge_recovery_diagnostics_from_metadata(
            metadata=symbol_metadata,
            history_fallback_symbols=history_fallback_symbols,
            history_fallback_periods_by_symbol=history_fallback_periods_by_symbol,
            currency_assumed_symbols=currency_assumed_symbols,
        )

    retry_attempted_symbols: list[str] = []
    final_errors: dict[str, YFinanceAdapterError] = {}
    if first_pass_errors:
        retry_attempted_symbols = [symbol for symbol in symbols if symbol in first_pass_errors]
        logger.info(
            "market_data.refresh_retrying",
            source_provider=_YFINANCE_SOURCE_PROVIDER,
            retry_attempted_symbols=retry_attempted_symbols,
            retry_attempted_symbols_count=len(retry_attempted_symbols),
        )
        for retry_index, symbol in enumerate(retry_attempted_symbols):
            await _sleep_for_symbol_spacing(
                symbol_index=retry_index,
                request_spacing_seconds=provider_config.request_spacing_seconds,
            )
            try:
                symbol_rows, symbol_metadata = await fetch_yfinance_daily_close_rows(
                    symbols=(symbol,),
                    config=provider_config,
                )
            except YFinanceAdapterError as exc:
                final_errors[symbol] = exc
                continue
            fetched_rows.extend(symbol_rows)
            rows_by_symbol[symbol] = len(symbol_rows)
            currency_code = _extract_symbol_currency_from_metadata(
                metadata=symbol_metadata,
                symbol=symbol,
                rows=symbol_rows,
            )
            if currency_code is not None:
                currencies_by_symbol[symbol] = currency_code
            _merge_recovery_diagnostics_from_metadata(
                metadata=symbol_metadata,
                history_fallback_symbols=history_fallback_symbols,
                history_fallback_periods_by_symbol=history_fallback_periods_by_symbol,
                currency_assumed_symbols=currency_assumed_symbols,
            )

    failed_symbols = [symbol for symbol in symbols if symbol in final_errors]
    required_failures = [
        symbol for symbol in failed_symbols if symbol in required_portfolio_symbols
    ]
    if required_failures:
        required_failures_text = ", ".join(required_failures)
        first_required_failure = required_failures[0]
        required_failure = final_errors[first_required_failure]
        raise MarketDataClientError(
            "YFinance retry could not recover required portfolio symbol(s): "
            f"{required_failures_text}.",
            status_code=required_failure.status_code,
        ) from required_failure

    if not fetched_rows:
        raise MarketDataClientError(
            "YFinance response contained no valid daily close rows after retry for refresh scope.",
            status_code=502,
        )

    provider_metadata: dict[str, object] = {
        "provider": "yfinance",
        "period": provider_config.period,
        "interval": provider_config.interval,
        "auto_adjust": provider_config.auto_adjust,
        "repair": provider_config.repair,
        "requested_symbols": symbols,
        "rows_by_symbol": rows_by_symbol,
        "currencies_by_symbol": currencies_by_symbol,
        "retry_attempted_symbols": retry_attempted_symbols,
        "retry_attempted_symbols_count": len(retry_attempted_symbols),
        "failed_symbols": failed_symbols,
        "failed_symbols_count": len(failed_symbols),
        "history_fallback_symbols": history_fallback_symbols,
        "history_fallback_periods_by_symbol": history_fallback_periods_by_symbol,
        "currency_assumed_symbols": currency_assumed_symbols,
    }
    return _YFinanceScopeFetchResult(
        rows=fetched_rows,
        provider_metadata=provider_metadata,
        retry_attempted_symbols=retry_attempted_symbols,
        failed_symbols=failed_symbols,
        history_fallback_symbols=history_fallback_symbols,
        history_fallback_periods_by_symbol=history_fallback_periods_by_symbol,
        currency_assumed_symbols=currency_assumed_symbols,
    )


def _extract_symbol_currency_from_metadata(
    *,
    metadata: dict[str, object],
    symbol: str,
    rows: list[YFinanceNormalizedRow],
) -> str | None:
    """Extract one symbol currency from adapter metadata with row fallback."""

    metadata_currencies = metadata.get("currencies_by_symbol")
    if isinstance(metadata_currencies, dict):
        typed_metadata_currencies = cast(dict[str, object], metadata_currencies)
        candidate_currency = typed_metadata_currencies.get(symbol)
        if isinstance(candidate_currency, str):
            normalized_currency = candidate_currency.strip().upper()
            if normalized_currency:
                return normalized_currency

    if rows:
        return rows[0].currency_code
    return None


def _merge_recovery_diagnostics_from_metadata(
    *,
    metadata: dict[str, object],
    history_fallback_symbols: list[str],
    history_fallback_periods_by_symbol: dict[str, str],
    currency_assumed_symbols: list[str],
) -> None:
    """Merge one symbol-fetch metadata payload into recovery diagnostics."""

    (
        incoming_history_fallback_symbols,
        incoming_history_fallback_periods_by_symbol,
        incoming_currency_assumed_symbols,
    ) = _extract_recovery_diagnostics_from_metadata(metadata=metadata)

    for symbol in incoming_history_fallback_symbols:
        if symbol not in history_fallback_symbols:
            history_fallback_symbols.append(symbol)

    for symbol, period in incoming_history_fallback_periods_by_symbol.items():
        history_fallback_periods_by_symbol[symbol] = period

    for symbol in incoming_currency_assumed_symbols:
        if symbol not in currency_assumed_symbols:
            currency_assumed_symbols.append(symbol)


def _extract_recovery_diagnostics_from_metadata(
    *,
    metadata: dict[str, object],
) -> tuple[list[str], dict[str, str], list[str]]:
    """Extract typed recovery diagnostics from provider metadata payload."""

    history_fallback_symbols = _extract_symbol_list_from_metadata(
        metadata=metadata,
        key="history_fallback_symbols",
    )
    history_fallback_periods_by_symbol = _extract_symbol_period_map_from_metadata(
        metadata=metadata,
        key="history_fallback_periods_by_symbol",
    )
    currency_assumed_symbols = _extract_symbol_list_from_metadata(
        metadata=metadata,
        key="currency_assumed_symbols",
    )
    return (
        history_fallback_symbols,
        history_fallback_periods_by_symbol,
        currency_assumed_symbols,
    )


def _extract_symbol_list_from_metadata(
    *,
    metadata: dict[str, object],
    key: str,
) -> list[str]:
    """Extract normalized symbol list from provider metadata key when present."""

    raw_symbols = metadata.get(key)
    if not isinstance(raw_symbols, list):
        return []

    normalized_symbols: list[str] = []
    typed_raw_symbols = cast(list[object], raw_symbols)
    for raw_symbol in typed_raw_symbols:
        if isinstance(raw_symbol, str):
            normalized_symbol = raw_symbol.strip().upper()
            if normalized_symbol and normalized_symbol not in normalized_symbols:
                normalized_symbols.append(normalized_symbol)
    return normalized_symbols


def _extract_symbol_period_map_from_metadata(
    *,
    metadata: dict[str, object],
    key: str,
) -> dict[str, str]:
    """Extract symbol-to-period mapping from provider metadata key when present."""

    raw_mapping = metadata.get(key)
    if not isinstance(raw_mapping, dict):
        return {}

    normalized_mapping: dict[str, str] = {}
    typed_raw_mapping = cast(dict[object, object], raw_mapping)
    for raw_symbol, raw_period in typed_raw_mapping.items():
        if not isinstance(raw_symbol, str) or not isinstance(raw_period, str):
            continue
        normalized_symbol = raw_symbol.strip().upper()
        normalized_period = raw_period.strip()
        if normalized_symbol and normalized_period:
            normalized_mapping[normalized_symbol] = normalized_period
    return normalized_mapping


def _normalize_adapter_error_message_for_market_data(*, message: str) -> str:
    """Normalize adapter errors into the refresh contract phrasing when needed."""

    if (
        "empty history for symbol" in message
        and "exhausted configured history fallback" not in message
    ):
        symbol_match = re.search(r"symbol '([^']+)'", message)
        if symbol_match is not None:
            symbol = symbol_match.group(1).strip().upper()
            return (
                "YFinance exhausted configured history fallback periods for symbol " f"'{symbol}'."
            )
        return "YFinance exhausted configured history fallback periods for one symbol."
    return message


async def _sleep_for_symbol_spacing(
    *,
    symbol_index: int,
    request_spacing_seconds: float,
) -> None:
    """Pace symbol requests to reduce upstream throttling risk."""

    if symbol_index <= 0 or request_spacing_seconds <= 0:
        return
    await asyncio.sleep(request_spacing_seconds)


async def _ingest_fetched_yfinance_scope_rows(
    *,
    db: AsyncSession,
    refresh_plan: _YFinanceRefreshPlan,
    fetched_rows: list[YFinanceNormalizedRow],
    provider_metadata: dict[str, object],
) -> MarketDataSnapshotWriteResult:
    """Persist one already-fetched yfinance scope payload into the snapshot boundary."""

    price_rows = [_to_price_write(row=row) for row in fetched_rows]
    snapshot_metadata: dict[str, object] = {
        **provider_metadata,
        "requested_symbols": refresh_plan.normalized_symbols,
        "response_rows": len(price_rows),
    }
    return await ingest_market_data_snapshot(
        db=db,
        request=MarketDataSnapshotWriteRequest(
            source_type=_YFINANCE_SOURCE_TYPE,
            source_provider=_YFINANCE_SOURCE_PROVIDER,
            snapshot_key=refresh_plan.snapshot_key,
            snapshot_captured_at=refresh_plan.normalized_snapshot_captured_at,
            snapshot_metadata=snapshot_metadata,
            prices=price_rows,
        ),
    )


async def ingest_market_data_snapshot(
    *,
    db: AsyncSession,
    request: MarketDataSnapshotWriteRequest,
) -> MarketDataSnapshotWriteResult:
    """Persist one market-data snapshot with idempotent write semantics."""

    source_type = _normalize_source_identity(request.source_type, field="source_type")
    source_provider = _normalize_source_identity(request.source_provider, field="source_provider")
    snapshot_key = _normalize_required_text(request.snapshot_key, field="snapshot_key")
    snapshot_captured_at = _normalize_timestamp_with_timezone(
        request.snapshot_captured_at,
        field="snapshot_captured_at",
    )
    if snapshot_captured_at is None:
        raise MarketDataClientError(
            "Field 'snapshot_captured_at' must include a timestamp value.",
            status_code=422,
        )

    normalized_prices = [_normalize_price_write(price_write=row) for row in request.prices]
    _ensure_no_duplicate_rows_in_request(rows=normalized_prices)

    logger.info(
        "market_data.ingest_started",
        source_type=source_type,
        source_provider=source_provider,
        snapshot_key=snapshot_key,
        requested_prices=len(normalized_prices),
    )

    try:
        async with db.begin():
            snapshot = await _resolve_or_create_snapshot(
                db=db,
                source_type=source_type,
                source_provider=source_provider,
                snapshot_key=snapshot_key,
                snapshot_captured_at=snapshot_captured_at,
                snapshot_metadata=request.snapshot_metadata,
            )

            inserted_prices = 0
            updated_prices = 0
            for price_write in normalized_prices:
                was_inserted = await _insert_or_update_price_row(
                    db=db,
                    snapshot_id=snapshot.id,
                    price_write=price_write,
                )
                if was_inserted:
                    inserted_prices += 1
                else:
                    updated_prices += 1
    except SQLAlchemyError as exc:
        logger.error(
            "market_data.ingest_failed",
            source_type=source_type,
            source_provider=source_provider,
            snapshot_key=snapshot_key,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise MarketDataClientError(
            "Failed to persist market-data snapshot due to a database error.",
            status_code=500,
        ) from exc

    result = MarketDataSnapshotWriteResult(
        snapshot_id=snapshot.id,
        inserted_prices=inserted_prices,
        updated_prices=updated_prices,
    )
    logger.info(
        "market_data.ingest_completed",
        source_type=source_type,
        source_provider=source_provider,
        snapshot_key=snapshot_key,
        snapshot_id=result.snapshot_id,
        inserted_prices=result.inserted_prices,
        updated_prices=result.updated_prices,
    )
    return result


async def list_price_history_for_symbol(
    *,
    db: AsyncSession,
    instrument_symbol: str,
) -> list[MarketDataPriceRow]:
    """Return persisted market-data rows for one instrument symbol."""

    normalized_symbol = _normalize_symbol(instrument_symbol, field="instrument_symbol")
    logger.info(
        "market_data.read_started",
        instrument_symbol=normalized_symbol,
    )

    try:
        async with db.begin():
            query = (
                select(PriceHistory, MarketDataSnapshot)
                .join(
                    MarketDataSnapshot,
                    PriceHistory.snapshot_id == MarketDataSnapshot.id,
                )
                .where(PriceHistory.instrument_symbol == normalized_symbol)
                .order_by(
                    PriceHistory.market_timestamp.desc().nullslast(),
                    PriceHistory.trading_date.desc().nullslast(),
                    PriceHistory.id.desc(),
                )
            )
            query_result = await db.execute(query)
            rows = cast(
                list[tuple[PriceHistory, MarketDataSnapshot]],
                query_result.tuples().all(),
            )
    except SQLAlchemyError as exc:
        logger.error(
            "market_data.read_failed",
            instrument_symbol=normalized_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise MarketDataClientError(
            "Failed to load market-data history due to a database error.",
            status_code=500,
        ) from exc

    response_rows = [
        MarketDataPriceRow(
            instrument_symbol=price_row.instrument_symbol,
            market_timestamp=price_row.market_timestamp,
            trading_date=price_row.trading_date,
            price_value=price_row.price_value,
            currency_code=price_row.currency_code,
            snapshot_id=snapshot_row.id,
            source_type=snapshot_row.source_type,
            source_provider=snapshot_row.source_provider,
            snapshot_key=snapshot_row.snapshot_key,
            snapshot_captured_at=snapshot_row.snapshot_captured_at,
        )
        for price_row, snapshot_row in rows
    ]
    logger.info(
        "market_data.read_completed",
        instrument_symbol=normalized_symbol,
        row_count=len(response_rows),
    )
    return response_rows


async def resolve_latest_consistent_snapshot_coverage_for_symbols(
    *,
    db: AsyncSession,
    required_symbols: set[str],
) -> MarketDataConsistentSnapshotCoverage | None:
    """Resolve latest persisted snapshot with USD coverage for all required symbols."""

    if not required_symbols:
        return None

    normalized_required_symbols = sorted(
        {
            _normalize_required_text(symbol, field="required_symbols[]").upper()
            for symbol in required_symbols
        }
    )
    if not normalized_required_symbols:
        return None

    logger.info(
        "market_data.snapshot_coverage_started",
        required_symbols=normalized_required_symbols,
        required_symbols_count=len(normalized_required_symbols),
    )

    try:
        coverage_snapshot_query = (
            select(
                MarketDataSnapshot.id,
                MarketDataSnapshot.snapshot_key,
                MarketDataSnapshot.snapshot_captured_at,
            )
            .join(
                PriceHistory,
                PriceHistory.snapshot_id == MarketDataSnapshot.id,
            )
            .where(
                PriceHistory.instrument_symbol.in_(normalized_required_symbols),
                PriceHistory.currency_code == "USD",
            )
            .group_by(
                MarketDataSnapshot.id,
                MarketDataSnapshot.snapshot_key,
                MarketDataSnapshot.snapshot_captured_at,
            )
            .having(
                func.count(func.distinct(PriceHistory.instrument_symbol))
                == len(normalized_required_symbols),
            )
            .order_by(
                MarketDataSnapshot.snapshot_captured_at.desc(),
                MarketDataSnapshot.id.desc(),
            )
            .limit(1)
        )
        coverage_snapshot_result = await db.execute(coverage_snapshot_query)
        coverage_snapshot_row = coverage_snapshot_result.one_or_none()
        if coverage_snapshot_row is None:
            logger.info(
                "market_data.snapshot_coverage_completed",
                required_symbols_count=len(normalized_required_symbols),
                snapshot_found=False,
            )
            return None

        snapshot_id = int(coverage_snapshot_row[0])
        snapshot_key = str(coverage_snapshot_row[1])
        snapshot_captured_at = cast(datetime, coverage_snapshot_row[2])

        prices_query = (
            select(PriceHistory)
            .where(
                PriceHistory.snapshot_id == snapshot_id,
                PriceHistory.instrument_symbol.in_(normalized_required_symbols),
                PriceHistory.currency_code == "USD",
            )
            .order_by(
                PriceHistory.instrument_symbol.asc(),
                PriceHistory.market_timestamp.desc().nullslast(),
                PriceHistory.trading_date.desc().nullslast(),
                PriceHistory.id.desc(),
            )
        )
        prices_result = await db.execute(prices_query)
        price_rows = cast(list[PriceHistory], prices_result.scalars().all())
    except SQLAlchemyError as exc:
        logger.error(
            "market_data.snapshot_coverage_failed",
            required_symbols=normalized_required_symbols,
            required_symbols_count=len(normalized_required_symbols),
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise MarketDataClientError(
            "Failed to resolve market-data snapshot coverage due to a database error.",
            status_code=500,
        ) from exc

    latest_close_price_usd_by_symbol: dict[str, Decimal] = {}
    for price_row in price_rows:
        symbol = price_row.instrument_symbol
        if symbol in latest_close_price_usd_by_symbol:
            continue
        latest_close_price_usd_by_symbol[symbol] = price_row.price_value

    coverage = MarketDataConsistentSnapshotCoverage(
        snapshot_id=snapshot_id,
        snapshot_key=snapshot_key,
        snapshot_captured_at=snapshot_captured_at,
        latest_close_price_usd_by_symbol=latest_close_price_usd_by_symbol,
    )
    logger.info(
        "market_data.snapshot_coverage_completed",
        required_symbols=normalized_required_symbols,
        required_symbols_count=len(normalized_required_symbols),
        snapshot_found=True,
        snapshot_id=coverage.snapshot_id,
        snapshot_key=coverage.snapshot_key,
        priced_symbols_count=len(coverage.latest_close_price_usd_by_symbol),
    )
    return coverage


def _to_price_write(*, row: YFinanceNormalizedRow) -> MarketDataPriceWrite:
    """Convert one adapter-normalized row into existing ingestion write schema."""

    return MarketDataPriceWrite(
        instrument_symbol=row.instrument_symbol,
        trading_date=row.trading_date,
        price_value=row.close_value,
        currency_code=row.currency_code,
        source_payload=row.source_payload,
    )


def list_supported_market_data_symbols(*, settings: Settings | None = None) -> list[str]:
    """Return current supported refresh scope in stable sorted order."""

    universe = _get_market_data_symbol_universe(settings=settings)
    return sorted(universe.core_refresh_symbols)


def list_market_data_library_symbols(
    *,
    size: int = 200,
    settings: Settings | None = None,
) -> list[str]:
    """Return starter market-data library symbols for size 100 or 200."""

    if size not in _SUPPORTED_LIBRARY_SIZES:
        raise MarketDataClientError(
            "Market-data symbol library size must be one of: 100, 200.",
            status_code=422,
        )

    universe = _get_market_data_symbol_universe(settings=settings)
    if size == 100:
        return list(universe.starter_100_symbols)
    return list(universe.starter_200_symbols)


def _resolve_refresh_scope_symbols(
    *,
    refresh_scope_mode: MarketDataRefreshScopeMode,
    settings: Settings | None = None,
) -> list[str]:
    """Resolve deterministic symbol list for one refresh scope mode."""

    if refresh_scope_mode == "core":
        return list_supported_market_data_symbols(settings=settings)
    if refresh_scope_mode == "100":
        return list_market_data_library_symbols(size=100, settings=settings)
    return list_market_data_library_symbols(size=200, settings=settings)


def _normalize_refresh_scope_mode(value: str | None) -> MarketDataRefreshScopeMode:
    """Normalize and validate operator refresh scope mode input."""

    if value is None:
        return "core"

    normalized_value = _normalize_required_text(value, field="refresh_scope_mode").lower()
    if normalized_value not in _REFRESH_SCOPE_MODES:
        supported_modes = ", ".join(sorted(_REFRESH_SCOPE_MODES))
        raise MarketDataClientError(
            "Field 'refresh_scope_mode' (refresh scope mode) must be one of: "
            f"{supported_modes}.",
            status_code=422,
        )
    return cast(MarketDataRefreshScopeMode, normalized_value)


def _normalize_requested_symbols(*, symbols: list[str]) -> list[str]:
    """Normalize requested symbol list and reject duplicates after normalization."""

    if not symbols:
        raise MarketDataClientError(
            "At least one symbol must be requested for provider ingestion.",
            status_code=422,
        )

    normalized_symbols: list[str] = []
    seen_symbols: set[str] = set()
    duplicate_symbols: list[str] = []
    for symbol in symbols:
        normalized_symbol = _normalize_symbol(symbol, field="symbols[]")
        if normalized_symbol in seen_symbols:
            duplicate_symbols.append(normalized_symbol)
            continue
        seen_symbols.add(normalized_symbol)
        normalized_symbols.append(normalized_symbol)

    if duplicate_symbols:
        duplicate_symbol_text = ", ".join(sorted(set(duplicate_symbols)))
        raise MarketDataClientError(
            "Provider symbol request contains duplicates after normalization: "
            f"{duplicate_symbol_text}.",
            status_code=422,
        )

    return normalized_symbols


def _build_yfinance_refresh_plan(
    *,
    symbols: list[str],
    snapshot_captured_at: datetime | None,
    settings: Settings | None,
) -> _YFinanceRefreshPlan:
    """Build one deterministic yfinance refresh plan for reuse across workflows."""

    effective_settings = settings if settings is not None else get_settings()
    normalized_symbols = _normalize_requested_symbols(symbols=symbols)
    normalized_snapshot_captured_at = _normalize_timestamp_with_timezone(
        snapshot_captured_at if snapshot_captured_at is not None else utcnow(),
        field="snapshot_captured_at",
    )
    if normalized_snapshot_captured_at is None:
        raise MarketDataClientError(
            "Field 'snapshot_captured_at' must include a timestamp value.",
            status_code=422,
        )

    try:
        provider_config = build_yfinance_adapter_config(
            period=effective_settings.market_data_yfinance_period,
            interval=effective_settings.market_data_yfinance_interval,
            timeout_seconds=effective_settings.market_data_yfinance_timeout_seconds,
            max_retries=effective_settings.market_data_yfinance_max_retries,
            retry_backoff_seconds=effective_settings.market_data_yfinance_retry_backoff_seconds,
            request_spacing_seconds=effective_settings.market_data_yfinance_request_spacing_seconds,
            history_fallback_periods=effective_settings.market_data_yfinance_history_fallback_periods,
            default_currency=effective_settings.market_data_yfinance_default_currency,
            auto_adjust=effective_settings.market_data_yfinance_auto_adjust,
            repair=effective_settings.market_data_yfinance_repair,
        )
    except YFinanceAdapterError as exc:
        raise MarketDataClientError(str(exc), status_code=exc.status_code) from exc

    snapshot_key = _build_yfinance_snapshot_key(
        symbols=normalized_symbols,
        period=provider_config.period,
        interval=provider_config.interval,
        auto_adjust=provider_config.auto_adjust,
        repair=provider_config.repair,
        snapshot_captured_at=normalized_snapshot_captured_at,
    )
    return _YFinanceRefreshPlan(
        normalized_symbols=normalized_symbols,
        normalized_snapshot_captured_at=normalized_snapshot_captured_at,
        provider_config=provider_config,
        snapshot_key=snapshot_key,
    )


def _build_yfinance_snapshot_key(
    *,
    symbols: list[str],
    period: str,
    interval: str,
    auto_adjust: bool,
    repair: bool,
    snapshot_captured_at: datetime,
) -> str:
    """Build bounded deterministic yfinance snapshot key for idempotent writes."""

    symbol_fingerprint_source = ",".join(sorted(symbols))
    symbol_fingerprint = hashlib.sha256(symbol_fingerprint_source.encode("utf-8")).hexdigest()[:12]
    semantic_flags = f"aa{int(auto_adjust)}rp{int(repair)}"
    key = (
        "yf|d1|"
        f"{interval}|"
        f"{period}|"
        f"{semantic_flags}|"
        f"{snapshot_captured_at.date().isoformat()}|"
        f"s{len(symbols)}|"
        f"{symbol_fingerprint}"
    )
    if len(key) > 128:
        raise MarketDataClientError(
            "Generated yfinance snapshot key exceeds storage limit.",
            status_code=422,
        )
    return key


async def _resolve_or_create_snapshot(
    *,
    db: AsyncSession,
    source_type: str,
    source_provider: str,
    snapshot_key: str,
    snapshot_captured_at: datetime,
    snapshot_metadata: dict[str, object] | None,
) -> MarketDataSnapshot:
    """Resolve one deterministic snapshot context row."""

    inserted_snapshot_id = await _insert_snapshot_if_absent(
        db=db,
        source_type=source_type,
        source_provider=source_provider,
        snapshot_key=snapshot_key,
        snapshot_captured_at=snapshot_captured_at,
        snapshot_metadata=snapshot_metadata,
    )
    if isinstance(inserted_snapshot_id, int):
        inserted_snapshot = await db.get(MarketDataSnapshot, inserted_snapshot_id)
        if isinstance(inserted_snapshot, MarketDataSnapshot):
            return inserted_snapshot
        raise MarketDataClientError(
            "Failed to resolve newly inserted market-data snapshot row.",
            status_code=500,
        )

    query = select(MarketDataSnapshot).where(
        MarketDataSnapshot.source_type == source_type,
        MarketDataSnapshot.source_provider == source_provider,
        MarketDataSnapshot.snapshot_key == snapshot_key,
    )
    query_result = await db.execute(query)
    existing_snapshot = query_result.scalar_one_or_none()
    if isinstance(existing_snapshot, MarketDataSnapshot):
        existing_snapshot.snapshot_captured_at = snapshot_captured_at
        existing_snapshot.snapshot_metadata = snapshot_metadata
        existing_snapshot.updated_at = utcnow()
        return existing_snapshot

    raise MarketDataClientError(
        "Failed to resolve market-data snapshot row after conflict-safe insert attempt.",
        status_code=500,
    )


async def _insert_snapshot_if_absent(
    *,
    db: AsyncSession,
    source_type: str,
    source_provider: str,
    snapshot_key: str,
    snapshot_captured_at: datetime,
    snapshot_metadata: dict[str, object] | None,
) -> int | None:
    """Atomically insert snapshot row when it does not already exist."""

    now = utcnow()
    insert_statement = (
        postgresql_insert(MarketDataSnapshot)
        .values(
            source_type=source_type,
            source_provider=source_provider,
            snapshot_key=snapshot_key,
            snapshot_captured_at=snapshot_captured_at,
            snapshot_metadata=snapshot_metadata,
            created_at=now,
            updated_at=now,
        )
        .on_conflict_do_nothing(
            constraint="uq_market_data_snapshot_source_identity_key",
        )
        .returning(MarketDataSnapshot.id)
    )
    insert_result = await db.execute(insert_statement)
    inserted_snapshot_id = insert_result.scalar_one_or_none()
    if isinstance(inserted_snapshot_id, int):
        return inserted_snapshot_id
    return None


async def _insert_or_update_price_row(
    *,
    db: AsyncSession,
    snapshot_id: int,
    price_write: _NormalizedPriceWrite,
) -> bool:
    """Insert or update one deterministic price row by unique time key."""

    was_inserted = await _insert_price_row_if_absent(
        db=db,
        snapshot_id=snapshot_id,
        price_write=price_write,
    )
    if was_inserted:
        return True

    existing_row = await _find_existing_price_row(
        db=db,
        snapshot_id=snapshot_id,
        price_write=price_write,
    )
    if not isinstance(existing_row, PriceHistory):
        raise MarketDataClientError(
            "Failed to resolve existing market-data price row after conflict-safe insert attempt.",
            status_code=500,
        )

    existing_row.price_value = price_write.price_value
    existing_row.currency_code = price_write.currency_code
    existing_row.source_payload = price_write.source_payload
    existing_row.updated_at = utcnow()
    return False


async def _insert_price_row_if_absent(
    *,
    db: AsyncSession,
    snapshot_id: int,
    price_write: _NormalizedPriceWrite,
) -> bool:
    """Atomically insert one price row when its deterministic key is absent."""

    now = utcnow()
    insert_statement = postgresql_insert(PriceHistory).values(
        snapshot_id=snapshot_id,
        instrument_symbol=price_write.instrument_symbol,
        market_timestamp=price_write.market_timestamp,
        trading_date=price_write.trading_date,
        price_value=price_write.price_value,
        currency_code=price_write.currency_code,
        source_payload=price_write.source_payload,
        created_at=now,
        updated_at=now,
    )
    if price_write.market_timestamp is not None:
        insert_statement = insert_statement.on_conflict_do_nothing(
            index_elements=[
                PriceHistory.snapshot_id,
                PriceHistory.instrument_symbol,
                PriceHistory.market_timestamp,
            ],
            index_where=PriceHistory.market_timestamp.is_not(None),
        )
    else:
        insert_statement = insert_statement.on_conflict_do_nothing(
            index_elements=[
                PriceHistory.snapshot_id,
                PriceHistory.instrument_symbol,
                PriceHistory.trading_date,
            ],
            index_where=PriceHistory.trading_date.is_not(None),
        )

    insert_result = await db.execute(
        insert_statement.returning(PriceHistory.id),
    )
    inserted_price_row_id = insert_result.scalar_one_or_none()
    if isinstance(inserted_price_row_id, int):
        return True
    return False


async def _find_existing_price_row(
    *,
    db: AsyncSession,
    snapshot_id: int,
    price_write: _NormalizedPriceWrite,
) -> PriceHistory | None:
    """Return existing persisted row for one deterministic price key."""

    if price_write.market_timestamp is not None:
        query = select(PriceHistory).where(
            PriceHistory.snapshot_id == snapshot_id,
            PriceHistory.instrument_symbol == price_write.instrument_symbol,
            PriceHistory.market_timestamp == price_write.market_timestamp,
        )
    else:
        query = select(PriceHistory).where(
            PriceHistory.snapshot_id == snapshot_id,
            PriceHistory.instrument_symbol == price_write.instrument_symbol,
            PriceHistory.trading_date == price_write.trading_date,
        )
    query_result = await db.execute(query)
    existing_row = query_result.scalar_one_or_none()
    if isinstance(existing_row, PriceHistory):
        return existing_row
    return None


def _ensure_no_duplicate_rows_in_request(*, rows: list[_NormalizedPriceWrite]) -> None:
    """Reject duplicate deterministic keys in one request payload."""

    seen_keys: set[str] = set()
    duplicate_keys: list[str] = []
    for row in rows:
        key = row.dedup_key()
        if key in seen_keys:
            duplicate_keys.append(key)
        else:
            seen_keys.add(key)

    if duplicate_keys:
        raise MarketDataClientError(
            "Market-data snapshot payload contains duplicate symbol/time keys.",
            status_code=422,
        )


def _normalize_price_write(*, price_write: MarketDataPriceWrite) -> _NormalizedPriceWrite:
    """Normalize one price-write row for deterministic persistence."""

    normalized_symbol = _normalize_symbol(
        price_write.instrument_symbol,
        field="instrument_symbol",
    )
    normalized_currency = _normalize_required_text(
        price_write.currency_code,
        field="currency_code",
    ).upper()
    normalized_market_timestamp = _normalize_timestamp_with_timezone(
        price_write.market_timestamp,
        field="market_timestamp",
        allow_none=True,
    )

    if normalized_market_timestamp is None and price_write.trading_date is None:
        raise MarketDataClientError(
            "Either market_timestamp or trading_date must be provided.",
            status_code=422,
        )
    if normalized_market_timestamp is not None and price_write.trading_date is not None:
        raise MarketDataClientError(
            "Provide only one of market_timestamp or trading_date for one price row.",
            status_code=422,
        )

    return _NormalizedPriceWrite(
        instrument_symbol=normalized_symbol,
        market_timestamp=normalized_market_timestamp,
        trading_date=price_write.trading_date,
        price_value=price_write.price_value,
        currency_code=normalized_currency,
        source_payload=price_write.source_payload,
    )


def _normalize_symbol(value: object, *, field: str) -> str:
    """Normalize and validate one instrument symbol."""

    normalized_symbol = _normalize_required_text(value, field=field).upper()
    if _SYMBOL_PATTERN.fullmatch(normalized_symbol) is None:
        raise MarketDataClientError(
            f"Field '{field}' must be a safe ticker-style symbol.",
            status_code=422,
        )
    supported_scope = _get_market_data_symbol_universe().supported_scope
    if normalized_symbol not in supported_scope:
        raise MarketDataClientError(
            f"Symbol '{normalized_symbol}' is outside the current dataset_1-supported market-data scope.",
            status_code=422,
        )
    return normalized_symbol


def _get_market_data_symbol_universe(
    *,
    settings: Settings | None = None,
) -> _MarketDataSymbolUniverse:
    """Resolve one validated market-data symbol universe from configured path."""

    effective_settings = settings if settings is not None else get_settings()
    return _load_market_data_symbol_universe_from_path(
        universe_path=effective_settings.market_data_symbol_universe_path,
    )


@lru_cache(maxsize=8)
def _load_market_data_symbol_universe_from_path(
    *,
    universe_path: str,
) -> _MarketDataSymbolUniverse:
    """Load and validate market-data symbol universe JSON from one path."""

    resolved_universe_path = Path(universe_path)
    try:
        raw_payload = resolved_universe_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MarketDataClientError(
            "Failed to read configured market-data symbol universe file: "
            f"{resolved_universe_path}.",
            status_code=500,
        ) from exc

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise MarketDataClientError(
            "Configured market-data symbol universe file contains invalid JSON: "
            f"{resolved_universe_path}.",
            status_code=500,
        ) from exc

    if not isinstance(payload, dict):
        raise MarketDataClientError(
            "Configured market-data symbol universe file must contain one JSON object.",
            status_code=500,
        )
    typed_payload = cast(dict[str, object], payload)

    required_portfolio_symbols = _parse_symbol_array_from_universe_payload(
        payload=typed_payload,
        field="required_portfolio_symbols",
    )
    core_refresh_symbols = _parse_symbol_array_from_universe_payload(
        payload=typed_payload,
        field="core_refresh_symbols",
    )
    starter_100_symbols = _parse_symbol_array_from_universe_payload(
        payload=typed_payload,
        field="starter_100_symbols",
    )
    starter_200_symbols = _parse_symbol_array_from_universe_payload(
        payload=typed_payload,
        field="starter_200_symbols",
    )

    if len(starter_100_symbols) != 100:
        raise MarketDataClientError(
            "Field 'starter_100_symbols' must contain exactly 100 unique symbols.",
            status_code=500,
        )
    if len(starter_200_symbols) != 200:
        raise MarketDataClientError(
            "Field 'starter_200_symbols' must contain exactly 200 unique symbols.",
            status_code=500,
        )

    _ensure_symbol_subset(
        subset_symbols=required_portfolio_symbols,
        superset_symbols=core_refresh_symbols,
        subset_field="required_portfolio_symbols",
        superset_field="core_refresh_symbols",
    )
    _ensure_symbol_subset(
        subset_symbols=required_portfolio_symbols,
        superset_symbols=starter_100_symbols,
        subset_field="required_portfolio_symbols",
        superset_field="starter_100_symbols",
    )
    _ensure_symbol_subset(
        subset_symbols=required_portfolio_symbols,
        superset_symbols=starter_200_symbols,
        subset_field="required_portfolio_symbols",
        superset_field="starter_200_symbols",
    )
    _ensure_symbol_subset(
        subset_symbols=starter_100_symbols,
        superset_symbols=starter_200_symbols,
        subset_field="starter_100_symbols",
        superset_field="starter_200_symbols",
    )
    _ensure_symbol_subset(
        subset_symbols=core_refresh_symbols,
        superset_symbols=starter_200_symbols,
        subset_field="core_refresh_symbols",
        superset_field="starter_200_symbols",
    )

    return _MarketDataSymbolUniverse(
        required_portfolio_symbols=required_portfolio_symbols,
        core_refresh_symbols=core_refresh_symbols,
        starter_100_symbols=starter_100_symbols,
        starter_200_symbols=starter_200_symbols,
    )


def _parse_symbol_array_from_universe_payload(
    *,
    payload: dict[str, object],
    field: str,
) -> tuple[str, ...]:
    """Parse and validate one symbol-array field from universe JSON payload."""

    raw_symbols = payload.get(field)
    if not isinstance(raw_symbols, list):
        raise MarketDataClientError(
            f"Field '{field}' in market-data symbol universe must be a JSON array.",
            status_code=500,
        )
    raw_symbol_values = cast(list[object], raw_symbols)

    normalized_symbols: list[str] = []
    seen_symbols: set[str] = set()
    duplicate_symbols: set[str] = set()
    for raw_symbol in raw_symbol_values:
        if not isinstance(raw_symbol, str):
            raise MarketDataClientError(
                f"Field '{field}' must contain only ticker symbol strings.",
                status_code=500,
            )
        normalized_symbol = raw_symbol.strip().upper()
        if not normalized_symbol:
            raise MarketDataClientError(
                f"Field '{field}' must not contain blank ticker symbols.",
                status_code=500,
            )
        if _SYMBOL_PATTERN.fullmatch(normalized_symbol) is None:
            raise MarketDataClientError(
                f"Field '{field}' contains unsupported ticker symbol '{normalized_symbol}'.",
                status_code=500,
            )
        if normalized_symbol in seen_symbols:
            duplicate_symbols.add(normalized_symbol)
            continue
        seen_symbols.add(normalized_symbol)
        normalized_symbols.append(normalized_symbol)

    if duplicate_symbols:
        duplicate_symbol_text = ", ".join(sorted(duplicate_symbols))
        raise MarketDataClientError(
            f"Field '{field}' contains duplicate ticker symbols: {duplicate_symbol_text}.",
            status_code=500,
        )
    return tuple(normalized_symbols)


def _ensure_symbol_subset(
    *,
    subset_symbols: tuple[str, ...],
    superset_symbols: tuple[str, ...],
    subset_field: str,
    superset_field: str,
) -> None:
    """Validate subset relation across two symbol collections."""

    missing_symbols = sorted(set(subset_symbols) - set(superset_symbols))
    if missing_symbols:
        missing_symbol_text = ", ".join(missing_symbols)
        raise MarketDataClientError(
            f"Field '{subset_field}' includes symbols missing from '{superset_field}': "
            f"{missing_symbol_text}.",
            status_code=500,
        )


def _normalize_source_identity(value: object, *, field: str) -> str:
    """Normalize source identity fields for deterministic matching."""

    return _normalize_required_text(value, field=field).lower()


def _normalize_required_text(value: object, *, field: str) -> str:
    """Normalize a required text field to stripped form."""

    if not isinstance(value, str):
        raise MarketDataClientError(
            f"Field '{field}' must be a non-empty string.",
            status_code=422,
        )
    normalized_value = value.strip()
    if not normalized_value:
        raise MarketDataClientError(
            f"Field '{field}' must be a non-empty string.",
            status_code=422,
        )
    return normalized_value


def _normalize_timestamp_with_timezone(
    value: datetime | None,
    *,
    field: str,
    allow_none: bool = False,
) -> datetime | None:
    """Normalize timezone-aware timestamps to UTC for deterministic keys."""

    if value is None:
        if allow_none:
            return None
        raise MarketDataClientError(
            f"Field '{field}' must include a timestamp value.",
            status_code=422,
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise MarketDataClientError(
            f"Field '{field}' must include timezone information.",
            status_code=422,
        )
    return value.astimezone(UTC)
