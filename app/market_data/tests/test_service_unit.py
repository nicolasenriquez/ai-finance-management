"""Unit tests for market-data service fail-fast and idempotency guards."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.market_data.providers.yfinance_adapter import YFinanceAdapterError, YFinanceNormalizedRow
from app.market_data.schemas import MarketDataPriceWrite, MarketDataSnapshotWriteRequest
from app.market_data.service import (
    MarketDataClientError,
    ingest_market_data_snapshot,
    ingest_yfinance_daily_close_snapshot,
    list_price_history_for_symbol,
    list_supported_market_data_symbols,
    refresh_yfinance_supported_universe,
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


def _provider_settings() -> Settings:
    """Build one settings object suitable for provider-ingest unit tests."""

    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        market_data_yfinance_period="5y",
        market_data_yfinance_interval="1d",
        market_data_yfinance_timeout_seconds=30.0,
        market_data_yfinance_max_retries=1,
        market_data_yfinance_retry_backoff_seconds=0.0,
        market_data_yfinance_auto_adjust=False,
        market_data_yfinance_repair=False,
    )


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


@pytest.mark.asyncio
async def test_provider_ingest_normalizes_dotted_symbol_and_builds_bounded_snapshot_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider ingest should preserve canonical dotted symbols and bounded snapshot keys."""

    captured_request: dict[str, MarketDataSnapshotWriteRequest] = {}

    async def fake_fetch(
        *,
        symbols: tuple[str, ...],
        config: object,
    ) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
        del config
        assert symbols == ("BRK.B",)
        return (
            [
                YFinanceNormalizedRow(
                    instrument_symbol="BRK.B",
                    trading_date=date(2026, 3, 24),
                    close_value=Decimal("510.123456789"),
                    currency_code="USD",
                    source_payload={"provider": "yfinance", "field": "Close"},
                )
            ],
            {"provider": "yfinance"},
        )

    async def fake_ingest(
        *,
        db: AsyncSession,
        request: MarketDataSnapshotWriteRequest,
    ) -> object:
        del db
        captured_request["request"] = request

        class _FakeResult:
            snapshot_id = 1
            inserted_prices = 1
            updated_prices = 0

        return _FakeResult()

    monkeypatch.setattr("app.market_data.service.fetch_yfinance_daily_close_rows", fake_fetch)
    monkeypatch.setattr("app.market_data.service.ingest_market_data_snapshot", fake_ingest)

    result = await ingest_yfinance_daily_close_snapshot(
        db=cast(AsyncSession, _NeverCalledSession()),
        symbols=[" brk.b "],
        snapshot_captured_at=datetime(2026, 3, 24, 15, 0, tzinfo=UTC),
        settings=_provider_settings(),
    )

    assert result.snapshot_id == 1
    request = captured_request["request"]
    assert request.source_type == "market_data_provider"
    assert request.source_provider == "yfinance"
    assert request.prices[0].instrument_symbol == "BRK.B"
    assert request.prices[0].trading_date == date(2026, 3, 24)
    assert request.prices[0].market_timestamp is None
    assert "aa0rp0" in request.snapshot_key
    assert len(request.snapshot_key) <= 128


@pytest.mark.asyncio
async def test_provider_ingest_rejects_duplicate_symbols_before_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider ingest should fail fast before fetch when symbols duplicate after normalization."""

    async def fake_fetch(
        *,
        symbols: tuple[str, ...],
        config: object,
    ) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
        del symbols
        del config
        pytest.fail("Provider fetch should not be called on duplicate symbol input.")

    monkeypatch.setattr("app.market_data.service.fetch_yfinance_daily_close_rows", fake_fetch)

    with pytest.raises(MarketDataClientError, match="duplicates after normalization") as exc_info:
        await ingest_yfinance_daily_close_snapshot(
            db=cast(AsyncSession, _NeverCalledSession()),
            symbols=["VOO", " voo "],
            snapshot_captured_at=datetime(2026, 3, 24, 15, 0, tzinfo=UTC),
            settings=_provider_settings(),
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_provider_ingest_surfaces_adapter_fail_fast_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider ingest should surface adapter errors as market-data client errors."""

    async def fake_fetch(
        *,
        symbols: tuple[str, ...],
        config: object,
    ) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
        del symbols
        del config
        raise YFinanceAdapterError("Provider payload is malformed.", status_code=502)

    monkeypatch.setattr("app.market_data.service.fetch_yfinance_daily_close_rows", fake_fetch)

    with pytest.raises(MarketDataClientError, match=r"Provider payload is malformed\.") as exc_info:
        await ingest_yfinance_daily_close_snapshot(
            db=cast(AsyncSession, _NeverCalledSession()),
            symbols=["VOO"],
            snapshot_captured_at=datetime(2026, 3, 24, 15, 0, tzinfo=UTC),
            settings=_provider_settings(),
        )
    assert exc_info.value.status_code == 502


def test_list_supported_market_data_symbols_returns_stable_sorted_universe() -> None:
    """Supported symbol universe should be deterministic and sorted."""

    symbols = list_supported_market_data_symbols()

    assert symbols == sorted(symbols)
    assert len(symbols) == len(set(symbols))
    assert "BRK.B" in symbols
    assert "VOO" in symbols


@pytest.mark.asyncio
async def test_refresh_supported_universe_returns_structured_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refresh should use supported-universe symbols and return one structured outcome."""

    captured_symbols: dict[str, list[str]] = {}

    async def fake_ingest(
        *,
        db: AsyncSession,
        symbols: list[str],
        snapshot_captured_at: datetime | None,
        settings: Settings | None,
    ) -> object:
        del db
        del settings
        captured_symbols["symbols"] = symbols
        assert snapshot_captured_at == datetime(2026, 3, 24, 15, 0, tzinfo=UTC)

        class _FakeResult:
            snapshot_id = 42
            inserted_prices = len(symbols)
            updated_prices = 0

        return _FakeResult()

    monkeypatch.setattr("app.market_data.service.ingest_yfinance_daily_close_snapshot", fake_ingest)

    result = await refresh_yfinance_supported_universe(
        db=cast(AsyncSession, _NeverCalledSession()),
        snapshot_captured_at=datetime(2026, 3, 24, 15, 0, tzinfo=UTC),
        settings=_provider_settings(),
    )

    expected_symbols = list_supported_market_data_symbols()
    assert captured_symbols["symbols"] == expected_symbols
    assert result.status == "completed"
    assert result.source_type == "market_data_provider"
    assert result.source_provider == "yfinance"
    assert result.requested_symbols == expected_symbols
    assert result.snapshot_id == 42
    assert result.inserted_prices == len(expected_symbols)
    assert result.updated_prices == 0
    assert result.snapshot_key
    assert result.snapshot_captured_at == datetime(2026, 3, 24, 15, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_refresh_supported_universe_fails_fast_on_incomplete_provider_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refresh should fail fast when provider coverage is incomplete."""

    async def fake_fetch(
        *,
        symbols: tuple[str, ...],
        config: object,
    ) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
        del symbols
        del config
        raise YFinanceAdapterError(
            "YFinance response is missing complete daily close coverage for requested symbol(s): VOO.",
            status_code=502,
        )

    monkeypatch.setattr("app.market_data.service.fetch_yfinance_daily_close_rows", fake_fetch)

    with pytest.raises(
        MarketDataClientError,
        match="missing complete daily close coverage",
    ) as exc_info:
        await refresh_yfinance_supported_universe(
            db=cast(AsyncSession, _NeverCalledSession()),
            snapshot_captured_at=datetime(2026, 3, 24, 15, 0, tzinfo=UTC),
            settings=_provider_settings(),
        )
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_refresh_supported_universe_surfaces_adapter_shape_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refresh should fail explicitly when adapter rejects unsupported Close payload shape."""

    async def fake_fetch(
        *,
        symbols: tuple[str, ...],
        config: object,
    ) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
        del symbols
        del config
        raise YFinanceAdapterError(
            "YFinance returned unsupported trading-date key for symbol 'AMD'.",
            status_code=502,
        )

    monkeypatch.setattr("app.market_data.service.fetch_yfinance_daily_close_rows", fake_fetch)

    with pytest.raises(
        MarketDataClientError,
        match="unsupported trading-date key for symbol 'AMD'",
    ) as exc_info:
        await refresh_yfinance_supported_universe(
            db=cast(AsyncSession, _NeverCalledSession()),
            snapshot_captured_at=datetime(2026, 3, 24, 15, 0, tzinfo=UTC),
            settings=_provider_settings(),
        )
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_refresh_supported_universe_succeeds_through_provider_ingest_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refresh should succeed when provider rows are valid for full supported scope."""

    async def fake_fetch(
        *,
        symbols: tuple[str, ...],
        config: object,
    ) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
        del config
        rows = [
            YFinanceNormalizedRow(
                instrument_symbol=symbol,
                trading_date=date(2026, 3, 24),
                close_value=Decimal("100.000000000") + Decimal(index),
                currency_code="USD",
                source_payload={"provider": "yfinance", "field": "Close", "symbol": symbol},
            )
            for index, symbol in enumerate(symbols)
        ]
        return (
            rows,
            {
                "provider": "yfinance",
                "rows_by_symbol": dict.fromkeys(symbols, 1),
            },
        )

    async def fake_ingest(
        *,
        db: AsyncSession,
        request: MarketDataSnapshotWriteRequest,
    ) -> object:
        del db

        class _FakeResult:
            snapshot_id = 99
            inserted_prices = len(request.prices)
            updated_prices = 0

        return _FakeResult()

    monkeypatch.setattr("app.market_data.service.fetch_yfinance_daily_close_rows", fake_fetch)
    monkeypatch.setattr("app.market_data.service.ingest_market_data_snapshot", fake_ingest)

    result = await refresh_yfinance_supported_universe(
        db=cast(AsyncSession, _NeverCalledSession()),
        snapshot_captured_at=datetime(2026, 3, 24, 15, 0, tzinfo=UTC),
        settings=_provider_settings(),
    )

    expected_symbols = list_supported_market_data_symbols()
    assert result.status == "completed"
    assert result.source_provider == "yfinance"
    assert result.requested_symbols == expected_symbols
    assert result.snapshot_id == 99
    assert result.inserted_prices == len(expected_symbols)
    assert result.updated_prices == 0
