"""YFinance adapter for first-slice market-data provider ingestion."""

from __future__ import annotations

import asyncio
import importlib
import math
import re
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Final, TypeGuard, cast

_CURRENCY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z]{3,8}$")


@dataclass(frozen=True)
class YFinanceAdapterConfig:
    """Configuration surface for yfinance provider fetch behavior."""

    period: str
    interval: str
    timeout_seconds: float
    max_retries: int
    retry_backoff_seconds: float
    auto_adjust: bool
    repair: bool


@dataclass(frozen=True)
class YFinanceNormalizedRow:
    """One normalized yfinance row ready for service-level write mapping."""

    instrument_symbol: str
    trading_date: date
    close_value: Decimal
    currency_code: str
    source_payload: dict[str, object]


class YFinanceAdapterError(ValueError):
    """Raised when provider fetch or normalization cannot continue safely."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize adapter error with client-facing status code."""

        super().__init__(message)
        self.status_code = status_code


def build_yfinance_adapter_config(
    *,
    period: str,
    interval: str,
    timeout_seconds: float,
    max_retries: int,
    retry_backoff_seconds: float,
    auto_adjust: bool,
    repair: bool,
) -> YFinanceAdapterConfig:
    """Create one validated yfinance adapter config."""

    normalized_period = period.strip()
    normalized_interval = interval.strip().lower()
    if not normalized_period:
        raise YFinanceAdapterError(
            "YFinance period must be configured as a non-empty string.",
            status_code=422,
        )
    if normalized_interval != "1d":
        raise YFinanceAdapterError(
            "YFinance first-slice integration only supports interval '1d'.",
            status_code=422,
        )
    if timeout_seconds <= 0:
        raise YFinanceAdapterError(
            "YFinance timeout_seconds must be greater than zero.",
            status_code=422,
        )
    if max_retries < 0:
        raise YFinanceAdapterError(
            "YFinance max_retries must be zero or greater.",
            status_code=422,
        )
    if retry_backoff_seconds < 0:
        raise YFinanceAdapterError(
            "YFinance retry_backoff_seconds must be zero or greater.",
            status_code=422,
        )
    if auto_adjust:
        raise YFinanceAdapterError(
            "YFinance first-slice integration requires auto_adjust=False.",
            status_code=422,
        )
    if repair:
        raise YFinanceAdapterError(
            "YFinance first-slice integration requires repair=False.",
            status_code=422,
        )

    return YFinanceAdapterConfig(
        period=normalized_period,
        interval=normalized_interval,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
        auto_adjust=auto_adjust,
        repair=repair,
    )


async def fetch_yfinance_daily_close_rows(
    *,
    symbols: tuple[str, ...],
    config: YFinanceAdapterConfig,
) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
    """Fetch and normalize yfinance day-level close rows for requested symbols."""

    if not symbols:
        raise YFinanceAdapterError(
            "At least one symbol is required for yfinance market-data fetch.",
            status_code=422,
        )

    try:
        rows, metadata = await asyncio.to_thread(
            _fetch_yfinance_daily_close_rows_sync,
            symbols,
            config,
        )
    except YFinanceAdapterError:
        raise
    except Exception as exc:
        raise YFinanceAdapterError(
            "YFinance provider fetch failed with an unexpected error.",
            status_code=502,
        ) from exc

    return rows, metadata


def _fetch_yfinance_daily_close_rows_sync(
    symbols: tuple[str, ...],
    config: YFinanceAdapterConfig,
) -> tuple[list[YFinanceNormalizedRow], dict[str, object]]:
    """Perform blocking yfinance fetch and normalization in a sync boundary."""

    yf = _load_yfinance_module()

    rows: list[YFinanceNormalizedRow] = []
    missing_symbols: list[str] = []
    rows_by_symbol: dict[str, int] = {}
    currencies_by_symbol: dict[str, str] = {}

    for symbol in symbols:
        currency_code = _fetch_symbol_currency(yf=yf, symbol=symbol)
        symbol_rows = _fetch_symbol_rows(
            yf=yf,
            symbol=symbol,
            currency_code=currency_code,
            config=config,
        )
        if not symbol_rows:
            missing_symbols.append(symbol)
            continue
        rows.extend(symbol_rows)
        rows_by_symbol[symbol] = len(symbol_rows)
        currencies_by_symbol[symbol] = currency_code

    if missing_symbols:
        missing_text = ", ".join(missing_symbols)
        raise YFinanceAdapterError(
            "YFinance response is missing complete daily close coverage for requested "
            f"symbol(s): {missing_text}.",
            status_code=502,
        )

    if not rows:
        raise YFinanceAdapterError(
            "YFinance response contained no valid daily close rows.",
            status_code=502,
        )

    metadata: dict[str, object] = {
        "provider": "yfinance",
        "period": config.period,
        "interval": config.interval,
        "auto_adjust": config.auto_adjust,
        "repair": config.repair,
        "requested_symbols": list(symbols),
        "rows_by_symbol": rows_by_symbol,
        "currencies_by_symbol": currencies_by_symbol,
    }
    return rows, metadata


def _load_yfinance_module() -> object:
    """Load yfinance lazily through importlib to keep strict typing gates green."""

    try:
        return importlib.import_module("yfinance")
    except ImportError as exc:
        raise YFinanceAdapterError(
            "YFinance dependency is not installed.",
            status_code=500,
        ) from exc


def _fetch_symbol_rows(
    *,
    yf: object,
    symbol: str,
    currency_code: str,
    config: YFinanceAdapterConfig,
) -> list[YFinanceNormalizedRow]:
    """Fetch one symbol history and normalize into day-level close rows."""

    download_result = _download_symbol_history(
        yf=yf,
        symbol=symbol,
        config=config,
    )
    close_series = _extract_close_series(download_result=download_result, symbol=symbol)
    series_items = _extract_close_items(close_series=close_series, symbol=symbol)

    normalized_rows: list[YFinanceNormalizedRow] = []
    for raw_market_key, raw_close in series_items:
        if _is_missing_numeric_value(raw_close):
            continue
        trading_day = _coerce_trading_date(raw_market_key=raw_market_key, symbol=symbol)
        close_value = _coerce_decimal(raw_value=raw_close, symbol=symbol)
        source_payload: dict[str, object] = {
            "provider": "yfinance",
            "field": "Close",
            "symbol": symbol,
            "trading_date": trading_day.isoformat(),
            "period": config.period,
            "interval": config.interval,
            "auto_adjust": config.auto_adjust,
            "repair": config.repair,
        }
        normalized_rows.append(
            YFinanceNormalizedRow(
                instrument_symbol=symbol,
                trading_date=trading_day,
                close_value=close_value,
                currency_code=currency_code,
                source_payload=source_payload,
            )
        )

    return normalized_rows


def _fetch_symbol_currency(
    *,
    yf: object,
    symbol: str,
) -> str:
    """Resolve one symbol currency from explicit provider metadata."""

    ticker_ctor = getattr(yf, "Ticker", None)
    if not callable(ticker_ctor):
        raise YFinanceAdapterError(
            "YFinance provider client does not expose Ticker metadata access.",
            status_code=502,
        )

    ticker_client = ticker_ctor(symbol)
    fast_info = cast(
        Mapping[str, object] | None,
        getattr(ticker_client, "fast_info", None),
    )
    currency_candidate = _extract_mapping_string(fast_info, key="currency")

    if currency_candidate is None:
        info_mapping = cast(
            Mapping[str, object] | None,
            getattr(ticker_client, "info", None),
        )
        currency_candidate = _extract_mapping_string(info_mapping, key="currency")

    if currency_candidate is None:
        raise YFinanceAdapterError(
            f"YFinance did not provide currency metadata for symbol '{symbol}'.",
            status_code=502,
        )

    normalized_currency = currency_candidate.strip().upper()
    if _CURRENCY_PATTERN.fullmatch(normalized_currency) is None:
        raise YFinanceAdapterError(
            f"YFinance returned unsupported currency metadata for symbol '{symbol}'.",
            status_code=502,
        )
    return normalized_currency


def _download_symbol_history(
    *,
    yf: object,
    symbol: str,
    config: YFinanceAdapterConfig,
) -> object:
    """Download one symbol history with bounded retry behavior."""

    download_function = getattr(yf, "download", None)
    if not callable(download_function):
        raise YFinanceAdapterError(
            "YFinance provider client does not expose download function.",
            status_code=502,
        )

    attempt = 0
    last_error: Exception | None = None
    while attempt <= config.max_retries:
        try:
            result = download_function(
                tickers=symbol,
                period=config.period,
                interval=config.interval,
                auto_adjust=config.auto_adjust,
                repair=config.repair,
                progress=False,
                threads=False,
                timeout=config.timeout_seconds,
            )
            if _is_empty_frame(result):
                raise YFinanceAdapterError(
                    f"YFinance returned empty history for symbol '{symbol}'.",
                    status_code=502,
                )
            return result
        except YFinanceAdapterError:
            raise
        except Exception as exc:
            last_error = exc
            if attempt >= config.max_retries:
                break
            if config.retry_backoff_seconds > 0:
                time.sleep(config.retry_backoff_seconds)
            attempt += 1
            continue
        attempt += 1

    raise YFinanceAdapterError(
        f"YFinance failed while downloading history for symbol '{symbol}'.",
        status_code=502,
    ) from last_error


def _extract_close_series(*, download_result: object, symbol: str) -> object:
    """Return close-price series object from download dataframe-like payload."""

    get_method = getattr(download_result, "get", None)
    if not callable(get_method):
        raise YFinanceAdapterError(
            f"YFinance returned unsupported history shape for symbol '{symbol}'.",
            status_code=502,
        )
    close_series = get_method("Close")
    if close_series is None:
        raise YFinanceAdapterError(
            f"YFinance history for symbol '{symbol}' is missing Close data.",
            status_code=502,
        )
    return close_series


def _extract_close_items(*, close_series: object, symbol: str) -> list[tuple[object, object]]:
    """Return close items from supported one-dimensional and tabular payload shapes."""

    if _is_tabular_close_payload(close_series):
        return _extract_tabular_close_items(close_series=close_series, symbol=symbol)
    return _extract_series_items(close_series=close_series, symbol=symbol)


def _extract_series_items(*, close_series: object, symbol: str) -> list[tuple[object, object]]:
    """Return close-series items as list of market-key/value pairs."""

    items_candidate = getattr(close_series, "items", None)
    if not callable(items_candidate):
        raise YFinanceAdapterError(
            f"YFinance Close series for symbol '{symbol}' is not iterable.",
            status_code=502,
        )

    raw_items_candidate = items_candidate()
    if not isinstance(raw_items_candidate, Iterable):
        raise YFinanceAdapterError(
            f"YFinance Close series for symbol '{symbol}' is not iterable.",
            status_code=502,
        )

    raw_items_iterable = cast(Iterable[object], raw_items_candidate)
    normalized_items: list[tuple[object, object]] = []
    for item in raw_items_iterable:
        if not _is_two_item_tuple(item):
            raise YFinanceAdapterError(
                f"YFinance Close series items are malformed for symbol '{symbol}'.",
                status_code=502,
            )
        normalized_items.append(item)
    return normalized_items


def _extract_tabular_close_items(
    *,
    close_series: object,
    symbol: str,
) -> list[tuple[object, object]]:
    """Return market-key/value items from a tabular close payload for one symbol."""

    column_items = _extract_series_items(close_series=close_series, symbol=symbol)
    if not column_items:
        raise YFinanceAdapterError(
            f"YFinance returned empty tabular Close payload for symbol '{symbol}'.",
            status_code=502,
        )

    matching_columns = [
        column_item
        for column_item in column_items
        if _close_column_matches_symbol(column_key=column_item[0], symbol=symbol)
    ]
    if len(matching_columns) == 1:
        _, column_series = matching_columns[0]
        return _extract_series_items(close_series=column_series, symbol=symbol)

    raise YFinanceAdapterError(
        f"YFinance returned unsupported tabular Close payload for symbol '{symbol}'.",
        status_code=502,
    )


def _is_tabular_close_payload(close_series: object) -> bool:
    """Return whether close payload is tabular and needs symbol-column resolution."""

    return getattr(close_series, "columns", None) is not None


def _close_column_matches_symbol(*, column_key: object, symbol: str) -> bool:
    """Return whether one tabular close column key maps to requested symbol."""

    normalized_symbol = symbol.strip().upper()
    if isinstance(column_key, str):
        return column_key.strip().upper() == normalized_symbol
    if isinstance(column_key, tuple):
        column_key_parts = cast(tuple[object, ...], column_key)  # ty: ignore[redundant-cast]
        return any(
            isinstance(part, str) and part.strip().upper() == normalized_symbol
            for part in column_key_parts
        )
    return False


def _is_two_item_tuple(candidate: object) -> TypeGuard[tuple[object, object]]:
    """Return whether candidate is a two-item tuple of generic objects."""

    if not isinstance(candidate, tuple):
        return False
    # pyright strict narrows `candidate` to tuple[Unknown, ...], so we explicitly
    # widen element type to object before length check.
    normalized_candidate = cast(tuple[object, ...], candidate)  # ty: ignore[redundant-cast]
    return len(normalized_candidate) == 2


def _coerce_trading_date(*, raw_market_key: object, symbol: str) -> date:
    """Coerce provider market key to day-level trading date."""

    if isinstance(raw_market_key, datetime):
        return raw_market_key.date()
    if isinstance(raw_market_key, date):
        return raw_market_key

    to_pydatetime = getattr(raw_market_key, "to_pydatetime", None)
    if callable(to_pydatetime):
        converted_datetime = to_pydatetime()
        if isinstance(converted_datetime, datetime):
            return converted_datetime.date()

    raise YFinanceAdapterError(
        f"YFinance returned unsupported trading-date key for symbol '{symbol}'.",
        status_code=502,
    )


def _coerce_decimal(*, raw_value: object, symbol: str) -> Decimal:
    """Convert one provider numeric close value to Decimal safely."""

    try:
        decimal_value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError) as exc:
        raise YFinanceAdapterError(
            f"YFinance returned invalid numeric close value for symbol '{symbol}'.",
            status_code=502,
        ) from exc

    if not decimal_value.is_finite():
        raise YFinanceAdapterError(
            f"YFinance returned non-finite close value for symbol '{symbol}'.",
            status_code=502,
        )
    return decimal_value


def _extract_mapping_string(mapping: Mapping[str, object] | None, *, key: str) -> str | None:
    """Extract one string field from mapping payload when present."""

    if mapping is None:
        return None
    raw_value = mapping.get(key)
    if isinstance(raw_value, str):
        normalized = raw_value.strip()
        if normalized:
            return normalized
    return None


def _is_missing_numeric_value(raw_value: object) -> bool:
    """Return whether one numeric candidate should be treated as missing."""

    if raw_value is None:
        return True
    if isinstance(raw_value, float):
        return math.isnan(raw_value)
    isna_method = getattr(raw_value, "isna", None)
    if callable(isna_method):
        try:
            return bool(isna_method())
        except Exception:
            return False
    return False


def _is_empty_frame(frame: object) -> bool:
    """Return whether a dataframe-like provider payload is empty."""

    empty_attr = getattr(frame, "empty", None)
    if isinstance(empty_attr, bool):
        return empty_attr
    return False
