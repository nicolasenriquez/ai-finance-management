"""YFinance adapter for first-slice market-data provider ingestion."""

from __future__ import annotations

import asyncio
import importlib
import math
import re
import socket
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Final, TypeGuard, cast

_CURRENCY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z]{3,8}$")
_CANONICAL_HISTORY_PERIOD_ORDER: Final[tuple[str, ...]] = ("5y", "3y", "1y", "6mo")
_YAHOO_REQUIRED_ENDPOINTS: Final[tuple[str, ...]] = (
    "query2.finance.yahoo.com",
    "guce.yahoo.com",
)
_YFINANCE_PROVIDER_SYMBOL_ALIASES: Final[dict[str, str]] = {
    "BRK.B": "BRK-B",
}


@dataclass(frozen=True)
class YFinanceAdapterConfig:
    """Configuration surface for yfinance provider fetch behavior."""

    period: str
    history_fallback_periods: tuple[str, ...]
    default_currency: str
    interval: str
    timeout_seconds: float
    max_retries: int
    retry_backoff_seconds: float
    request_spacing_seconds: float
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
    request_spacing_seconds: float = 0.0,
    history_fallback_periods: Iterable[str] | None = None,
    default_currency: str = "USD",
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
    normalized_history_fallback_periods: tuple[str, ...]
    if history_fallback_periods is None:
        normalized_history_fallback_periods = ("3y", "1y", "6mo")
    else:
        normalized_history_fallback_periods = _normalize_history_fallback_periods(
            history_fallback_periods=history_fallback_periods,
        )
    normalized_history_fallback_periods = _apply_shorter_history_period_filter(
        periods=normalized_history_fallback_periods,
        primary_period=normalized_period,
    )

    normalized_default_currency = default_currency.strip().upper()
    if _CURRENCY_PATTERN.fullmatch(normalized_default_currency) is None:
        raise YFinanceAdapterError(
            "YFinance default_currency must be a supported uppercase currency code.",
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
    if request_spacing_seconds < 0:
        raise YFinanceAdapterError(
            "YFinance request_spacing_seconds must be zero or greater.",
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
        history_fallback_periods=normalized_history_fallback_periods,
        default_currency=normalized_default_currency,
        interval=normalized_interval,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
        request_spacing_seconds=request_spacing_seconds,
        auto_adjust=auto_adjust,
        repair=repair,
    )


def _normalize_history_fallback_periods(
    *,
    history_fallback_periods: Iterable[str],
) -> tuple[str, ...]:
    """Normalize one ordered period fallback ladder and enforce bounded uniqueness."""

    normalized_periods: list[str] = []
    seen_periods: set[str] = set()
    for raw_period in history_fallback_periods:
        normalized_period = raw_period.strip()
        if not normalized_period:
            raise YFinanceAdapterError(
                "YFinance history_fallback_periods must contain only non-empty values.",
                status_code=422,
            )
        normalized_period_key = normalized_period.lower()
        if normalized_period_key in seen_periods:
            raise YFinanceAdapterError(
                "YFinance history_fallback_periods must not include duplicates.",
                status_code=422,
            )
        seen_periods.add(normalized_period_key)
        normalized_periods.append(normalized_period)

    if not normalized_periods:
        raise YFinanceAdapterError(
            "YFinance history_fallback_periods must include at least one fallback period.",
            status_code=422,
        )
    return tuple(normalized_periods)


def _apply_shorter_history_period_filter(
    *,
    periods: tuple[str, ...],
    primary_period: str,
) -> tuple[str, ...]:
    """Filter fallback periods to avoid duplicate/non-shorter primary-period attempts."""

    if not periods:
        return periods

    normalized_primary_period_key = primary_period.strip().lower()
    canonical_index_by_period = {
        period: index for index, period in enumerate(_CANONICAL_HISTORY_PERIOD_ORDER)
    }
    normalized_period_keys = [period.strip().lower() for period in periods]

    if normalized_primary_period_key in canonical_index_by_period and all(
        period_key in canonical_index_by_period for period_key in normalized_period_keys
    ):
        primary_index = canonical_index_by_period[normalized_primary_period_key]
        period_keys_set = set(normalized_period_keys)
        return tuple(
            canonical_period
            for canonical_period in _CANONICAL_HISTORY_PERIOD_ORDER
            if canonical_index_by_period[canonical_period] > primary_index
            and canonical_period in period_keys_set
        )

    return tuple(
        period
        for period in periods
        if period.strip().lower() != normalized_primary_period_key
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
            "YFinance provider fetch failed with an unexpected error: "
            f"{_format_provider_exception_reason(exc)}.",
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
    history_fallback_symbols: list[str] = []
    history_fallback_periods_by_symbol: dict[str, str] = {}
    currency_assumed_symbols: list[str] = []

    for symbol_index, symbol in enumerate(symbols):
        if symbol_index > 0 and config.request_spacing_seconds > 0:
            time.sleep(config.request_spacing_seconds)
        symbol_rows = _fetch_symbol_rows(
            yf=yf,
            symbol=symbol,
            currency_code=None,
            config=config,
        )
        if not symbol_rows:
            missing_symbols.append(symbol)
            continue
        rows.extend(symbol_rows)
        rows_by_symbol[symbol] = len(symbol_rows)
        currencies_by_symbol[symbol] = symbol_rows[0].currency_code
        effective_period = _extract_symbol_effective_period_from_rows(rows=symbol_rows)
        if effective_period is not None and effective_period != config.period:
            history_fallback_symbols.append(symbol)
            history_fallback_periods_by_symbol[symbol] = effective_period
        if _rows_use_assumed_default_currency(rows=symbol_rows):
            currency_assumed_symbols.append(symbol)

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
        "history_fallback_symbols": history_fallback_symbols,
        "history_fallback_periods_by_symbol": history_fallback_periods_by_symbol,
        "currency_assumed_symbols": currency_assumed_symbols,
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
    currency_code: str | None,
    config: YFinanceAdapterConfig,
) -> list[YFinanceNormalizedRow]:
    """Fetch one symbol history and normalize into day-level close rows."""

    download_result_candidate = _download_symbol_history(
        yf=yf,
        symbol=symbol,
        config=config,
    )
    effective_period = config.period
    download_result = download_result_candidate
    if _is_download_result_with_period(download_result_candidate):
        download_result = download_result_candidate[0]
        effective_period = download_result_candidate[1]

    close_series = _extract_close_series(download_result=download_result, symbol=symbol)
    series_items = _extract_close_items(close_series=close_series, symbol=symbol)

    normalized_points: list[tuple[date, Decimal]] = []
    for raw_market_key, raw_close in series_items:
        if _is_missing_numeric_value(raw_close):
            continue
        trading_day = _coerce_trading_date(raw_market_key=raw_market_key, symbol=symbol)
        close_value = _coerce_decimal(raw_value=raw_close, symbol=symbol)
        normalized_points.append((trading_day, close_value))

    if not normalized_points:
        return []

    resolved_currency_code = currency_code
    currency_source = "provider"
    if resolved_currency_code is None:
        try:
            resolved_currency_code = _fetch_symbol_currency(
                yf=yf,
                symbol=symbol,
            )
        except YFinanceAdapterError as exc:
            if _is_missing_currency_metadata_error(exc):
                resolved_currency_code = config.default_currency
                currency_source = "assumed_default"
            else:
                raise

    normalized_rows: list[YFinanceNormalizedRow] = []
    provider_symbol = _resolve_provider_symbol(symbol=symbol)
    for trading_day, close_value in normalized_points:
        source_payload: dict[str, object] = {
            "provider": "yfinance",
            "field": "Close",
            "symbol": symbol,
            "provider_symbol": provider_symbol,
            "trading_date": trading_day.isoformat(),
            "period": effective_period,
            "interval": config.interval,
            "auto_adjust": config.auto_adjust,
            "repair": config.repair,
            "currency_source": currency_source,
        }
        normalized_rows.append(
            YFinanceNormalizedRow(
                instrument_symbol=symbol,
                trading_date=trading_day,
                close_value=close_value,
                currency_code=resolved_currency_code,
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

    provider_symbol = _resolve_provider_symbol(symbol=symbol)
    ticker_client = ticker_ctor(provider_symbol)
    fast_info, fast_info_access_failed = _get_mapping_attribute_or_none(
        ticker_client,
        attribute_name="fast_info",
    )
    currency_candidate = _extract_mapping_string(fast_info, key="currency")

    info_access_failed = False
    if currency_candidate is None:
        info_mapping, info_access_failed = _get_mapping_attribute_or_none(
            ticker_client,
            attribute_name="info",
        )
        currency_candidate = _extract_mapping_string(info_mapping, key="currency")

    if currency_candidate is None:
        if fast_info_access_failed or info_access_failed:
            raise YFinanceAdapterError(
                f"YFinance currency metadata access failed for symbol '{symbol}'.",
                status_code=502,
            )
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


def _is_missing_currency_metadata_error(exc: YFinanceAdapterError) -> bool:
    """Return whether adapter error represents missing provider currency metadata."""

    return "did not provide currency metadata" in str(exc)


def _get_mapping_attribute_or_none(
    value: object,
    *,
    attribute_name: str,
) -> tuple[Mapping[str, object] | None, bool]:
    """Return mapping attribute value when available and safely accessible."""

    try:
        attribute_value = getattr(value, attribute_name)
    except Exception:
        return None, True

    if isinstance(attribute_value, Mapping):
        return cast(Mapping[str, object], attribute_value), False
    return None, False


def _download_symbol_history(
    *,
    yf: object,
    symbol: str,
    config: YFinanceAdapterConfig,
) -> object | tuple[object, str]:
    """Download one symbol history with bounded retry and fallback behavior."""

    download_function = getattr(yf, "download", None)
    if not callable(download_function):
        raise YFinanceAdapterError(
            "YFinance provider client does not expose download function.",
            status_code=502,
        )
    typed_download_function = download_function
    if _is_real_yfinance_download_function(download_function=typed_download_function):
        _assert_yahoo_endpoints_resolvable()

    attempted_periods: list[str] = []
    periods_to_try = (config.period, *config.history_fallback_periods)
    for period in periods_to_try:
        attempted_periods.append(period)
        result = _download_symbol_history_for_period(
            download_function=typed_download_function,
            symbol=symbol,
            period=period,
            config=config,
        )
        if result is not None:
            return result, period

    attempted_periods_text = ", ".join(attempted_periods)
    raise YFinanceAdapterError(
        "YFinance exhausted configured history fallback periods for symbol "
        f"'{symbol}' (attempted: {attempted_periods_text}).",
        status_code=502,
    )


def _download_symbol_history_for_period(
    *,
    download_function: Callable[..., object],
    symbol: str,
    period: str,
    config: YFinanceAdapterConfig,
) -> object | None:
    """Download one symbol period with bounded transport retries."""

    attempt = 0
    last_error: Exception | None = None
    provider_symbol = _resolve_provider_symbol(symbol=symbol)
    while attempt <= config.max_retries:
        try:
            result = download_function(
                tickers=provider_symbol,
                period=period,
                interval=config.interval,
                auto_adjust=config.auto_adjust,
                repair=config.repair,
                progress=False,
                threads=False,
                timeout=config.timeout_seconds,
            )
            if _is_empty_frame(result):
                return None
            return result
        except Exception as exc:
            last_error = exc
            if attempt >= config.max_retries:
                break
            if config.retry_backoff_seconds > 0:
                time.sleep(config.retry_backoff_seconds)
            attempt += 1

    reason = "unknown provider failure"
    if last_error is not None:
        if _is_dns_or_endpoint_resolution_error(last_error):
            reason = _format_dns_endpoint_failure_reason(last_error)
        else:
            reason = _format_provider_exception_reason(last_error)
    raise YFinanceAdapterError(
        f"YFinance failed while downloading history for symbol '{symbol}' "
        f"using period '{period}' ({reason}).",
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


def _extract_close_items(
    *, close_series: object, symbol: str
) -> list[tuple[object, object]]:
    """Return close items from supported one-dimensional and tabular payload shapes."""

    if _is_tabular_close_payload(close_series):
        return _extract_tabular_close_items(
            close_series=close_series,
            symbol=symbol,
            provider_symbol=_resolve_provider_symbol(symbol=symbol),
        )
    return _extract_series_items(close_series=close_series, symbol=symbol)


def _extract_series_items(
    *, close_series: object, symbol: str
) -> list[tuple[object, object]]:
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
    provider_symbol: str,
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
        or _close_column_matches_symbol(
            column_key=column_item[0], symbol=provider_symbol
        )
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
        column_key_parts = cast(
            tuple[object, ...], column_key
        )  # ty: ignore[redundant-cast]
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
    normalized_candidate = cast(
        tuple[object, ...], candidate
    )  # ty: ignore[redundant-cast]
    return len(normalized_candidate) == 2


def _is_download_result_with_period(
    candidate: object,
) -> TypeGuard[tuple[object, str]]:
    """Return whether download result includes payload plus effective period tuple."""

    if not _is_two_item_tuple(candidate):
        return False
    _, period = candidate
    return isinstance(period, str)


def _extract_symbol_effective_period_from_rows(
    *,
    rows: list[YFinanceNormalizedRow],
) -> str | None:
    """Extract one effective provider period from normalized row payload metadata."""

    if not rows:
        return None
    first_payload = rows[0].source_payload
    raw_period = first_payload.get("period")
    if isinstance(raw_period, str):
        normalized_period = raw_period.strip()
        if normalized_period:
            return normalized_period
    return None


def _rows_use_assumed_default_currency(*, rows: list[YFinanceNormalizedRow]) -> bool:
    """Return whether normalized rows were emitted with assumed default currency."""

    if not rows:
        return False
    first_payload = rows[0].source_payload
    raw_currency_source = first_payload.get("currency_source")
    return raw_currency_source == "assumed_default"


def _coerce_trading_date(*, raw_market_key: object, symbol: str) -> date:
    """Coerce provider market key to day-level trading date."""

    normalized_date = _coerce_day_level_temporal_key(value=raw_market_key)
    if normalized_date is not None:
        return normalized_date

    raise YFinanceAdapterError(
        f"YFinance returned unsupported trading-date key for symbol '{symbol}'.",
        status_code=502,
    )


def _coerce_day_level_temporal_key(*, value: object) -> date | None:
    """Return one approved day-level date from provider temporal key variants."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        converted_value = to_pydatetime()
        normalized_from_pydatetime = _coerce_day_level_temporal_key(
            value=converted_value
        )
        if normalized_from_pydatetime is not None:
            return normalized_from_pydatetime

    item_method = getattr(value, "item", None)
    if callable(item_method):
        converted_item = item_method()
        if converted_item is value:
            return None
        normalized_from_item = _coerce_day_level_temporal_key(value=converted_item)
        if normalized_from_item is not None:
            return normalized_from_item

    return None


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


def _extract_mapping_string(
    mapping: Mapping[str, object] | None, *, key: str
) -> str | None:
    """Extract one string field from mapping payload when present."""

    if mapping is None:
        return None
    try:
        raw_value = mapping.get(key)
    except Exception:
        return None
    if isinstance(raw_value, str):
        normalized = raw_value.strip()
        if normalized:
            return normalized
    return None


def _resolve_provider_symbol(*, symbol: str) -> str:
    """Map one canonical symbol to provider-specific fetch symbol when required."""

    normalized_symbol = symbol.strip().upper()
    return _YFINANCE_PROVIDER_SYMBOL_ALIASES.get(normalized_symbol, normalized_symbol)


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


def _format_provider_exception_reason(exc: Exception) -> str:
    """Return one compact exception reason for structured blocker reporting."""

    message = str(exc).strip()
    if message:
        return f"{type(exc).__name__}: {message}"
    return type(exc).__name__


def _is_real_yfinance_download_function(
    *, download_function: Callable[..., object]
) -> bool:
    """Return whether download function belongs to yfinance implementation modules."""

    module_name = getattr(download_function, "__module__", "")
    if not isinstance(module_name, str):
        return False
    return module_name.startswith("yfinance")


def _assert_yahoo_endpoints_resolvable() -> None:
    """Fail fast when required Yahoo endpoints are not DNS-resolvable."""

    for endpoint in _YAHOO_REQUIRED_ENDPOINTS:
        try:
            socket.getaddrinfo(endpoint, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise YFinanceAdapterError(
                "YFinance endpoint DNS resolution failed before history download "
                f"(endpoint='{endpoint}', error={_format_provider_exception_reason(exc)}).",
                status_code=502,
            ) from exc


def _is_dns_or_endpoint_resolution_error(exc: Exception) -> bool:
    """Return whether provider exception indicates DNS/endpoint resolution failure."""

    if isinstance(exc, socket.gaierror):
        return True
    normalized_message = str(exc).strip().lower()
    if not normalized_message:
        return False
    return (
        "could not resolve host" in normalized_message
        or "name or service not known" in normalized_message
        or "temporary failure in name resolution" in normalized_message
        or "nodename nor servname provided" in normalized_message
    )


def _format_dns_endpoint_failure_reason(exc: Exception) -> str:
    """Return normalized DNS/endpoint reason for operator-facing transport diagnostics."""

    return (
        "endpoint/DNS resolution failed; verify outbound DNS/network access to Yahoo "
        f"hosts ({_format_provider_exception_reason(exc)})"
    )
