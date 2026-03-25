"""Unit tests for yfinance adapter config and fail-fast normalization behavior."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.market_data.providers.yfinance_adapter import (
    YFinanceAdapterConfig,
    YFinanceAdapterError,
    YFinanceNormalizedRow,
    build_yfinance_adapter_config,
    fetch_yfinance_daily_close_rows,
)


def _valid_config() -> YFinanceAdapterConfig:
    """Return valid first-slice yfinance adapter config for tests."""

    return build_yfinance_adapter_config(
        period="5y",
        interval="1d",
        timeout_seconds=30.0,
        max_retries=1,
        retry_backoff_seconds=0.0,
        auto_adjust=False,
        repair=False,
    )


class _FakeDownloadResult:
    """Minimal download payload exposing the Close field through get()."""

    def __init__(self, close_payload: object) -> None:
        """Store one fake close payload for deterministic tests."""

        self._close_payload = close_payload

    def get(self, key: str) -> object | None:
        """Return fake close payload when key is Close."""

        if key == "Close":
            return self._close_payload
        return None


class _FakeCloseSeries:
    """Minimal series-like object exposing items()."""

    def __init__(self, *, points: list[tuple[object, object]]) -> None:
        """Store deterministic market-key/value points."""

        self._points = points

    def items(self) -> list[tuple[object, object]]:
        """Return deterministic market-key/value items."""

        return list(self._points)


class _FakeTemporalScalarWithItem:
    """Minimal scalar exposing item() for temporal key normalization tests."""

    def __init__(self, value: date | datetime) -> None:
        """Store deterministic day-level temporal value."""

        self._value = value

    def item(self) -> date | datetime:
        """Return wrapped temporal value similar to numpy scalar item()."""

        return self._value


class _FakeTemporalWithToPyDatetimeDate:
    """Temporal key exposing to_pydatetime() returning a date object."""

    def __init__(self, value: date) -> None:
        """Store deterministic day-level date value."""

        self._value = value

    def to_pydatetime(self) -> date:
        """Return stored date value for adapter coercion tests."""

        return self._value


class _FakeCloseTable:
    """Minimal tabular close payload exposing columns plus items()."""

    def __init__(self, *, columns: list[tuple[object, _FakeCloseSeries]]) -> None:
        """Store deterministic column-key/series mappings."""

        self._columns = columns
        self.columns = [column_key for column_key, _ in columns]

    def items(self) -> list[tuple[object, object]]:
        """Return deterministic column-key/value items."""

        return [(column_key, column_value) for column_key, column_value in self._columns]


def test_build_config_rejects_auto_adjust_true() -> None:
    """Adapter config must reject auto_adjust=True in first slice."""

    with pytest.raises(YFinanceAdapterError, match="auto_adjust=False") as exc_info:
        build_yfinance_adapter_config(
            period="5y",
            interval="1d",
            timeout_seconds=30.0,
            max_retries=1,
            retry_backoff_seconds=0.0,
            auto_adjust=True,
            repair=False,
        )
    assert exc_info.value.status_code == 422


def test_build_config_rejects_repair_true() -> None:
    """Adapter config must reject repair=True in first slice."""

    with pytest.raises(YFinanceAdapterError, match="repair=False") as exc_info:
        build_yfinance_adapter_config(
            period="5y",
            interval="1d",
            timeout_seconds=30.0,
            max_retries=1,
            retry_backoff_seconds=0.0,
            auto_adjust=False,
            repair=True,
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_fetch_rejects_empty_symbols_before_thread_boundary() -> None:
    """Fetch wrapper must fail fast when no symbols are requested."""

    with pytest.raises(YFinanceAdapterError, match="At least one symbol") as exc_info:
        await fetch_yfinance_daily_close_rows(
            symbols=(),
            config=_valid_config(),
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_fetch_surfaces_unexpected_provider_reason_for_blocker_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fetch wrapper should include compact provider reason for unexpected failures."""

    def fake_sync_fetch(
        symbols: tuple[str, ...],
        config: YFinanceAdapterConfig,
    ) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
        del symbols
        del config
        raise RuntimeError("provider socket timeout")

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_yfinance_daily_close_rows_sync",
        fake_sync_fetch,
    )

    with pytest.raises(
        YFinanceAdapterError,
        match="RuntimeError: provider socket timeout",
    ) as exc_info:
        await fetch_yfinance_daily_close_rows(
            symbols=("VOO",),
            config=_valid_config(),
        )
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_fetch_rejects_missing_requested_symbol_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fetch wrapper must reject provider payloads missing requested symbols."""

    def fake_currency(*, yf: object, symbol: str) -> str:
        del yf
        del symbol
        return "USD"

    def fake_rows(
        *,
        yf: object,
        symbol: str,
        currency_code: str,
        config: YFinanceAdapterConfig,
    ) -> list[YFinanceNormalizedRow]:
        del yf
        del symbol
        del currency_code
        del config
        return []

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_currency",
        fake_currency,
    )
    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_rows",
        fake_rows,
    )

    with pytest.raises(
        YFinanceAdapterError, match="missing complete daily close coverage"
    ) as exc_info:
        await fetch_yfinance_daily_close_rows(
            symbols=("VOO",),
            config=_valid_config(),
        )
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_fetch_returns_rows_and_metadata_when_provider_is_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fetch wrapper should return deterministic rows/metadata when provider data is complete."""

    def fake_currency(*, yf: object, symbol: str) -> str:
        del yf
        del symbol
        return "USD"

    def fake_rows(
        *,
        yf: object,
        symbol: str,
        currency_code: str,
        config: YFinanceAdapterConfig,
    ) -> list[YFinanceNormalizedRow]:
        del yf
        del currency_code
        del config
        return [
            YFinanceNormalizedRow(
                instrument_symbol=symbol,
                trading_date=date(2026, 3, 24),
                close_value=Decimal("510.123456789"),
                currency_code="USD",
                source_payload={"provider": "yfinance", "field": "Close"},
            )
        ]

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_currency",
        fake_currency,
    )
    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_rows",
        fake_rows,
    )

    rows, metadata = await fetch_yfinance_daily_close_rows(
        symbols=("VOO", "BRK.B"),
        config=_valid_config(),
    )

    assert len(rows) == 2
    assert rows[0].instrument_symbol == "VOO"
    assert rows[1].instrument_symbol == "BRK.B"
    assert metadata["requested_symbols"] == ["VOO", "BRK.B"]
    assert metadata["rows_by_symbol"] == {"VOO": 1, "BRK.B": 1}


@pytest.mark.asyncio
async def test_fetch_uses_provider_symbol_alias_for_brk_b_and_keeps_canonical_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adapter should fetch BRK.B through provider alias while preserving canonical symbol."""

    captured_symbols: dict[str, list[str]] = {
        "ticker": [],
        "download": [],
    }

    class _FakeTickerClient:
        """Minimal ticker metadata client with deterministic currency payload."""

        def __init__(self) -> None:
            self.fast_info: dict[str, str] = {"currency": "USD"}
            self.info: dict[str, str] = {"currency": "USD"}

    class _FakeYFinanceModule:
        """Minimal yfinance module capturing symbol usage for alias verification."""

        @staticmethod
        def Ticker(symbol: str) -> _FakeTickerClient:
            captured_symbols["ticker"].append(symbol)
            return _FakeTickerClient()

        @staticmethod
        def download(
            *,
            tickers: str,
            period: str,
            interval: str,
            auto_adjust: bool,
            repair: bool,
            progress: bool,
            threads: bool,
            timeout: float,
        ) -> object:
            del period
            del interval
            del auto_adjust
            del repair
            del progress
            del threads
            del timeout
            captured_symbols["download"].append(tickers)
            return _FakeDownloadResult(
                _FakeCloseSeries(points=[(datetime(2026, 3, 24, tzinfo=UTC), 500.0)])
            )

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._load_yfinance_module",
        lambda: _FakeYFinanceModule(),
    )

    rows, metadata = await fetch_yfinance_daily_close_rows(
        symbols=("BRK.B",),
        config=_valid_config(),
    )

    assert captured_symbols["ticker"] == ["BRK-B"]
    assert captured_symbols["download"] == ["BRK-B"]
    assert len(rows) == 1
    assert rows[0].instrument_symbol == "BRK.B"
    assert rows[0].source_payload["provider_symbol"] == "BRK-B"
    assert metadata["rows_by_symbol"] == {"BRK.B": 1}


@pytest.mark.asyncio
async def test_fetch_currency_falls_back_to_info_when_fast_info_get_raises_key_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Currency resolution should fall back to info mapping when fast_info get() fails."""

    class _FastInfoKeyError:
        """Fast-info stub that raises KeyError during get() access."""

        def get(self, key: str) -> object:
            raise KeyError(key)

    class _FakeTickerClient:
        """Minimal ticker metadata client exposing fallback info currency."""

        def __init__(self) -> None:
            self.fast_info: object = _FastInfoKeyError()
            self.info: dict[str, str] = {"currency": "USD"}

    class _FakeYFinanceModule:
        """Minimal yfinance module for deterministic fallback coverage."""

        @staticmethod
        def Ticker(symbol: str) -> _FakeTickerClient:
            del symbol
            return _FakeTickerClient()

        @staticmethod
        def download(
            *,
            tickers: str,
            period: str,
            interval: str,
            auto_adjust: bool,
            repair: bool,
            progress: bool,
            threads: bool,
            timeout: float,
        ) -> object:
            del tickers
            del period
            del interval
            del auto_adjust
            del repair
            del progress
            del threads
            del timeout
            return _FakeDownloadResult(
                _FakeCloseSeries(points=[(datetime(2026, 3, 24, tzinfo=UTC), 120.0)])
            )

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._load_yfinance_module",
        lambda: _FakeYFinanceModule(),
    )

    rows, metadata = await fetch_yfinance_daily_close_rows(
        symbols=("VOO",),
        config=_valid_config(),
    )

    assert len(rows) == 1
    assert rows[0].instrument_symbol == "VOO"
    assert rows[0].currency_code == "USD"
    assert metadata["rows_by_symbol"] == {"VOO": 1}


@pytest.mark.asyncio
async def test_fetch_currency_falls_back_to_info_when_fast_info_property_access_raises_key_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Currency resolution should fall back when fast_info property access raises KeyError."""

    class _FakeTickerClient:
        """Minimal ticker metadata client with fast_info property access failure."""

        @property
        def fast_info(self) -> object:
            """Raise provider-style key error while resolving fast metadata."""

            raise KeyError("currency")

        @property
        def info(self) -> dict[str, str]:
            """Expose fallback info mapping with valid currency."""

            return {"currency": "USD"}

    class _FakeYFinanceModule:
        """Minimal yfinance module for deterministic metadata property access coverage."""

        @staticmethod
        def Ticker(symbol: str) -> _FakeTickerClient:
            del symbol
            return _FakeTickerClient()

        @staticmethod
        def download(
            *,
            tickers: str,
            period: str,
            interval: str,
            auto_adjust: bool,
            repair: bool,
            progress: bool,
            threads: bool,
            timeout: float,
        ) -> object:
            del tickers
            del period
            del interval
            del auto_adjust
            del repair
            del progress
            del threads
            del timeout
            return _FakeDownloadResult(
                _FakeCloseSeries(points=[(datetime(2026, 3, 24, tzinfo=UTC), 120.0)])
            )

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._load_yfinance_module",
        lambda: _FakeYFinanceModule(),
    )

    rows, metadata = await fetch_yfinance_daily_close_rows(
        symbols=("VOO",),
        config=_valid_config(),
    )

    assert len(rows) == 1
    assert rows[0].instrument_symbol == "VOO"
    assert rows[0].currency_code == "USD"
    assert metadata["rows_by_symbol"] == {"VOO": 1}


@pytest.mark.asyncio
async def test_fetch_currency_raises_adapter_error_when_info_property_access_raises_key_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Currency resolution should fail with adapter error if info property access fails."""

    class _FakeTickerClient:
        """Minimal ticker metadata client with info property access failure."""

        @property
        def fast_info(self) -> dict[str, str]:
            """Return no currency in fast-info to force info fallback path."""

            return {}

        @property
        def info(self) -> object:
            """Raise provider-style key error while resolving info metadata."""

            raise KeyError("currency")

    class _FakeYFinanceModule:
        """Minimal yfinance module for deterministic info property access failure coverage."""

        @staticmethod
        def Ticker(symbol: str) -> _FakeTickerClient:
            del symbol
            return _FakeTickerClient()

        @staticmethod
        def download(
            *,
            tickers: str,
            period: str,
            interval: str,
            auto_adjust: bool,
            repair: bool,
            progress: bool,
            threads: bool,
            timeout: float,
        ) -> object:
            del tickers
            del period
            del interval
            del auto_adjust
            del repair
            del progress
            del threads
            del timeout
            return _FakeDownloadResult(
                _FakeCloseSeries(points=[(datetime(2026, 3, 24, tzinfo=UTC), 120.0)])
            )

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._load_yfinance_module",
        lambda: _FakeYFinanceModule(),
    )

    with pytest.raises(
        YFinanceAdapterError,
        match="did not provide currency metadata",
    ) as exc_info:
        await fetch_yfinance_daily_close_rows(
            symbols=("VOO",),
            config=_valid_config(),
        )
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_fetch_symbol_rows_supports_tabular_close_payload_for_requested_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row normalization should support tabular Close payloads keyed by symbol."""

    close_table = _FakeCloseTable(
        columns=[
            (
                "AMD",
                _FakeCloseSeries(
                    points=[
                        (datetime(2026, 3, 24, tzinfo=UTC), 118.25),
                        (datetime(2026, 3, 25, tzinfo=UTC), 119.75),
                    ]
                ),
            )
        ]
    )

    def fake_download(
        *,
        yf: object,
        symbol: str,
        config: YFinanceAdapterConfig,
    ) -> object:
        del yf
        del symbol
        del config
        return _FakeDownloadResult(close_table)

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._download_symbol_history",
        fake_download,
    )

    def fake_currency(*, yf: object, symbol: str) -> str:
        del yf
        del symbol
        return "USD"

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_currency",
        fake_currency,
    )

    rows, metadata = await fetch_yfinance_daily_close_rows(
        symbols=("AMD",),
        config=_valid_config(),
    )

    assert [row.trading_date for row in rows] == [date(2026, 3, 24), date(2026, 3, 25)]
    assert [row.close_value for row in rows] == [Decimal("118.25"), Decimal("119.75")]
    assert all(row.instrument_symbol == "AMD" for row in rows)
    assert all(row.currency_code == "USD" for row in rows)
    assert metadata["rows_by_symbol"] == {"AMD": 2}


@pytest.mark.asyncio
async def test_fetch_symbol_rows_supports_temporal_scalar_item_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row normalization should support day-level temporal keys exposing item()."""

    close_series = _FakeCloseSeries(
        points=[
            (_FakeTemporalScalarWithItem(date(2026, 3, 24)), 118.25),
            (_FakeTemporalScalarWithItem(datetime(2026, 3, 25, tzinfo=UTC)), 119.75),
        ]
    )

    def fake_download(
        *,
        yf: object,
        symbol: str,
        config: YFinanceAdapterConfig,
    ) -> object:
        del yf
        del symbol
        del config
        return _FakeDownloadResult(close_series)

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._download_symbol_history",
        fake_download,
    )

    def fake_currency(*, yf: object, symbol: str) -> str:
        del yf
        del symbol
        return "USD"

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_currency",
        fake_currency,
    )

    rows, metadata = await fetch_yfinance_daily_close_rows(
        symbols=("AMD",),
        config=_valid_config(),
    )

    assert [row.trading_date for row in rows] == [date(2026, 3, 24), date(2026, 3, 25)]
    assert [row.close_value for row in rows] == [Decimal("118.25"), Decimal("119.75")]
    assert metadata["rows_by_symbol"] == {"AMD": 2}


@pytest.mark.asyncio
async def test_fetch_symbol_rows_supports_to_pydatetime_returning_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row normalization should support to_pydatetime() values that are already dates."""

    close_series = _FakeCloseSeries(
        points=[
            (_FakeTemporalWithToPyDatetimeDate(date(2026, 3, 24)), 118.25),
            (_FakeTemporalWithToPyDatetimeDate(date(2026, 3, 25)), 119.75),
        ]
    )

    def fake_download(
        *,
        yf: object,
        symbol: str,
        config: YFinanceAdapterConfig,
    ) -> object:
        del yf
        del symbol
        del config
        return _FakeDownloadResult(close_series)

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._download_symbol_history",
        fake_download,
    )

    def fake_currency(*, yf: object, symbol: str) -> str:
        del yf
        del symbol
        return "USD"

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_currency",
        fake_currency,
    )

    rows, metadata = await fetch_yfinance_daily_close_rows(
        symbols=("AMD",),
        config=_valid_config(),
    )

    assert [row.trading_date for row in rows] == [date(2026, 3, 24), date(2026, 3, 25)]
    assert [row.close_value for row in rows] == [Decimal("118.25"), Decimal("119.75")]
    assert metadata["rows_by_symbol"] == {"AMD": 2}


@pytest.mark.asyncio
async def test_fetch_symbol_rows_rejects_tabular_close_payload_with_single_unmatched_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tabular Close payload should fail when one column key does not match symbol."""

    close_table = _FakeCloseTable(
        columns=[
            (
                "VOO",
                _FakeCloseSeries(points=[(datetime(2026, 3, 24, tzinfo=UTC), 500.0)]),
            )
        ]
    )

    def fake_download(
        *,
        yf: object,
        symbol: str,
        config: YFinanceAdapterConfig,
    ) -> object:
        del yf
        del symbol
        del config
        return _FakeDownloadResult(close_table)

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._download_symbol_history",
        fake_download,
    )

    def fake_currency(*, yf: object, symbol: str) -> str:
        del yf
        del symbol
        return "USD"

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_currency",
        fake_currency,
    )

    with pytest.raises(YFinanceAdapterError, match="unsupported tabular Close payload") as exc_info:
        await fetch_yfinance_daily_close_rows(
            symbols=("AMD",),
            config=_valid_config(),
        )

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_fetch_symbol_rows_rejects_tabular_close_payload_with_ambiguous_symbol_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tabular Close payload should fail fast when symbol column cannot be resolved safely."""

    close_table = _FakeCloseTable(
        columns=[
            (
                "VOO",
                _FakeCloseSeries(points=[(datetime(2026, 3, 24, tzinfo=UTC), 500.0)]),
            ),
            (
                "NVDA",
                _FakeCloseSeries(points=[(datetime(2026, 3, 24, tzinfo=UTC), 900.0)]),
            ),
        ]
    )

    def fake_download(
        *,
        yf: object,
        symbol: str,
        config: YFinanceAdapterConfig,
    ) -> object:
        del yf
        del symbol
        del config
        return _FakeDownloadResult(close_table)

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._download_symbol_history",
        fake_download,
    )

    def fake_currency(*, yf: object, symbol: str) -> str:
        del yf
        del symbol
        return "USD"

    monkeypatch.setattr(
        "app.market_data.providers.yfinance_adapter._fetch_symbol_currency",
        fake_currency,
    )

    with pytest.raises(YFinanceAdapterError, match="unsupported tabular Close payload") as exc_info:
        await fetch_yfinance_daily_close_rows(
            symbols=("AMD",),
            config=_valid_config(),
        )

    assert exc_info.value.status_code == 502
