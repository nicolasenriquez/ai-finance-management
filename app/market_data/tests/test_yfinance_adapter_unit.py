"""Unit tests for yfinance adapter config and fail-fast normalization behavior."""

from __future__ import annotations

from datetime import date
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
