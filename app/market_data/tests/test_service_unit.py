"""Unit tests for market-data service fail-fast and idempotency guards."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.market_data.schemas import MarketDataPriceWrite, MarketDataSnapshotWriteRequest
from app.market_data.service import (
    MarketDataClientError,
    ingest_market_data_snapshot,
    list_price_history_for_symbol,
)


class _NeverCalledBeginContext:
    """Fail-fast begin context used to ensure DB is never touched."""

    async def __aenter__(self) -> None:
        """Fail when the service attempts to enter DB transaction scope."""

        pytest.fail("Fail-fast guard failed: DB transaction should not start for invalid input.")

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: object | None,
    ) -> bool:
        """Return false in case context manager is unexpectedly entered."""

        return False


class _NeverCalledSession:
    """Minimal fake AsyncSession that fails if DB access occurs."""

    def begin(self) -> _NeverCalledBeginContext:
        """Return a begin-context that fails immediately on use."""

        return _NeverCalledBeginContext()


def _valid_request(*, symbol: str = "VOO") -> MarketDataSnapshotWriteRequest:
    """Build one valid baseline snapshot request for unit tests."""

    return MarketDataSnapshotWriteRequest(
        source_type="quote_feed",
        source_provider="provider_a",
        snapshot_key="snapshot-2026-03-24T10:00Z",
        snapshot_captured_at=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
        prices=[
            MarketDataPriceWrite(
                instrument_symbol=symbol,
                market_timestamp=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
                price_value=Decimal("510.123456789"),
                currency_code="usd",
                source_payload={"raw": "510.123456789"},
            )
        ],
    )


@pytest.mark.asyncio
async def test_ingest_rejects_snapshot_timestamp_without_timezone() -> None:
    """Ingest must reject snapshot timestamps that are not timezone-aware."""

    request = MarketDataSnapshotWriteRequest(
        source_type="quote_feed",
        source_provider="provider_a",
        snapshot_key="snapshot-without-timezone",
        snapshot_captured_at=datetime(2026, 3, 24, 10, 0, tzinfo=UTC).replace(tzinfo=None),
        prices=[
            MarketDataPriceWrite(
                instrument_symbol="VOO",
                market_timestamp=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
                price_value=Decimal("510.123456789"),
                currency_code="USD",
            )
        ],
    )

    with pytest.raises(MarketDataClientError, match="snapshot_captured_at") as exc_info:
        await ingest_market_data_snapshot(
            db=cast(AsyncSession, _NeverCalledSession()),
            request=request,
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_ingest_rejects_symbol_outside_dataset_1_scope_before_db_access() -> None:
    """Ingest must fail fast on symbols outside the current dataset_1 universe."""

    request = _valid_request(symbol="MSFT")

    with pytest.raises(MarketDataClientError, match="dataset_1-supported") as exc_info:
        await ingest_market_data_snapshot(
            db=cast(AsyncSession, _NeverCalledSession()),
            request=request,
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_ingest_rejects_duplicate_symbol_time_keys_in_one_payload() -> None:
    """Ingest must reject one payload containing duplicate symbol/time keys."""

    request = MarketDataSnapshotWriteRequest(
        source_type="quote_feed",
        source_provider="provider_a",
        snapshot_key="snapshot-duplicate-keys",
        snapshot_captured_at=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
        prices=[
            MarketDataPriceWrite(
                instrument_symbol=" voo ",
                market_timestamp=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
                price_value=Decimal("510.123456789"),
                currency_code="USD",
            ),
            MarketDataPriceWrite(
                instrument_symbol="VOO",
                market_timestamp=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
                price_value=Decimal("511.000000000"),
                currency_code="EUR",
            ),
        ],
    )

    with pytest.raises(MarketDataClientError, match="duplicate symbol/time keys") as exc_info:
        await ingest_market_data_snapshot(
            db=cast(AsyncSession, _NeverCalledSession()),
            request=request,
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_read_boundary_rejects_unsafe_symbol_shape_before_db_access() -> None:
    """Read boundary must reject unsafe symbol shapes before querying DB."""

    with pytest.raises(MarketDataClientError, match="safe ticker-style symbol") as exc_info:
        await list_price_history_for_symbol(
            db=cast(AsyncSession, _NeverCalledSession()),
            instrument_symbol="BRK/B",
        )
    assert exc_info.value.status_code == 422
