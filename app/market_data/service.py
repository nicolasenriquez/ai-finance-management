"""Service boundary for market-data write and read operations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Final, cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.market_data.models import MarketDataSnapshot, PriceHistory
from app.market_data.schemas import (
    MarketDataPriceRow,
    MarketDataPriceWrite,
    MarketDataSnapshotWriteRequest,
    MarketDataSnapshotWriteResult,
)
from app.shared.models import utcnow

logger = get_logger(__name__)

_SUPPORTED_DATASET_1_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "AMD",
        "APLD",
        "BBAI",
        "BRK.B",
        "GLD",
        "GOOGL",
        "HOOD",
        "META",
        "NVDA",
        "PLTR",
        "QQQM",
        "SCHD",
        "SCHG",
        "SMH",
        "SOFI",
        "SPMO",
        "TSLA",
        "UUUU",
        "VOO",
    }
)
_SYMBOL_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9][A-Z0-9.\-]*$")


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
        return f"{self.instrument_symbol}|" f"{market_timestamp_key}|" f"{trading_date_key}"


class MarketDataClientError(ValueError):
    """Raised when market-data boundary input cannot be processed safely."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize client-facing market-data error."""

        super().__init__(message)
        self.status_code = status_code


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
    if normalized_symbol not in _SUPPORTED_DATASET_1_SYMBOLS:
        raise MarketDataClientError(
            f"Symbol '{normalized_symbol}' is outside the current dataset_1-supported market-data scope.",
            status_code=422,
        )
    return normalized_symbol


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
