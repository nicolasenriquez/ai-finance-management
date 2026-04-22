"""Build a versioned market-data symbol universe from yfinance discovery surfaces."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import yfinance as yf

_SYMBOL_PATTERN: Final[str] = r"^[A-Z0-9][A-Z0-9.\-]*$"
_DATASET_DEFAULT_PATH: Final[Path] = Path("app/golden_sets/dataset_1/202602_stocks.json")
_OUTPUT_DEFAULT_PATH: Final[Path] = Path("app/market_data/symbol_universe.v1.json")
_EQUITY_SCREEN_QUERIES: Final[tuple[str, ...]] = (
    "aggressive_small_caps",
    "day_gainers",
    "day_losers",
    "growth_technology_stocks",
    "most_actives",
    "most_shorted_stocks",
    "small_cap_gainers",
    "undervalued_growth_stocks",
    "undervalued_large_caps",
)
_LIQUID_US_EXCHANGES: Final[frozenset[str]] = frozenset(
    {"ASE", "BTS", "NCM", "NGM", "NMS", "NYQ", "PCX"}
)
_STARTER_100_COUNT: Final[int] = 100
_STARTER_200_COUNT: Final[int] = 200
_STOCK_FILL_TARGET: Final[int] = 120


def _dedupe_preserve_order(symbols: list[str]) -> list[str]:
    """Return symbols with duplicates removed while preserving first-seen order."""

    seen: set[str] = set()
    normalized: list[str] = []
    for symbol in symbols:
        if symbol in seen:
            continue
        seen.add(symbol)
        normalized.append(symbol)
    return normalized


def _load_required_portfolio_symbols(*, dataset_json_path: Path) -> list[str]:
    """Load required portfolio symbols from canonical dataset_1 JSON."""

    payload = json.loads(dataset_json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Dataset JSON must contain one object payload.")

    tables = payload.get("tables")
    if not isinstance(tables, dict):
        raise ValueError("Dataset JSON is missing object field 'tables'.")
    trade_table = tables.get("compra_venta_activos")
    if not isinstance(trade_table, dict):
        raise ValueError("Dataset JSON is missing object field 'tables.compra_venta_activos'.")
    rows = trade_table.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Dataset JSON is missing array field 'tables.compra_venta_activos.rows'.")

    symbols: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_symbol = row.get("simbolo_activo")
        if not isinstance(raw_symbol, str):
            continue
        normalized_symbol = raw_symbol.strip().upper()
        if normalized_symbol:
            symbols.append(normalized_symbol)

    if not symbols:
        raise ValueError("Dataset JSON did not yield any required portfolio symbols.")

    deduped_symbols = _dedupe_preserve_order(symbols)
    for symbol in deduped_symbols:
        if not _is_valid_symbol(symbol):
            raise ValueError(f"Dataset symbol is not valid for market-data universe: {symbol}.")
    return sorted(deduped_symbols)


def _is_valid_symbol(symbol: str) -> bool:
    """Return whether symbol matches repository-safe ticker pattern."""

    import re

    return re.fullmatch(_SYMBOL_PATTERN, symbol) is not None


def _collect_equity_candidates() -> list[str]:
    """Collect US-liquid equity candidates from predefined yfinance screen queries."""

    symbols: list[str] = []
    for query_name in _EQUITY_SCREEN_QUERIES:
        response = yf.screen(query_name, count=250)
        quotes = response.get("quotes")
        if not isinstance(quotes, list):
            continue
        for quote_row in quotes:
            if not isinstance(quote_row, dict):
                continue
            quote_type = quote_row.get("quoteType")
            exchange = quote_row.get("exchange")
            raw_symbol = quote_row.get("symbol")
            if quote_type != "EQUITY":
                continue
            if not isinstance(exchange, str) or exchange not in _LIQUID_US_EXCHANGES:
                continue
            if not isinstance(raw_symbol, str):
                continue
            symbol = raw_symbol.strip().upper()
            if not symbol or not _is_valid_symbol(symbol):
                continue
            symbols.append(symbol)
    return _dedupe_preserve_order(symbols)


def _collect_etf_candidates() -> list[str]:
    """Collect US-liquid ETF candidates from yfinance lookup surface."""

    etf_frame = yf.Lookup("ETF").get_etf(count=500)
    symbols: list[str] = []
    for index_symbol, row in etf_frame.iterrows():
        if not isinstance(index_symbol, str):
            continue
        raw_exchange = row.get("exchange")
        if not isinstance(raw_exchange, str) or raw_exchange not in _LIQUID_US_EXCHANGES:
            continue
        symbol = index_symbol.strip().upper()
        if not symbol or not _is_valid_symbol(symbol):
            continue
        symbols.append(symbol)
    return _dedupe_preserve_order(symbols)


def _build_starter_200(
    *,
    required_portfolio_symbols: list[str],
    equity_candidates: list[str],
    etf_candidates: list[str],
) -> list[str]:
    """Build one deterministic 200-symbol starter universe."""

    starter_200: list[str] = list(required_portfolio_symbols)

    for symbol in equity_candidates:
        if len(starter_200) >= _STOCK_FILL_TARGET:
            break
        if symbol not in starter_200:
            starter_200.append(symbol)

    for symbol in etf_candidates:
        if len(starter_200) >= _STARTER_200_COUNT:
            break
        if symbol not in starter_200:
            starter_200.append(symbol)

    for symbol in equity_candidates:
        if len(starter_200) >= _STARTER_200_COUNT:
            break
        if symbol not in starter_200:
            starter_200.append(symbol)

    if len(starter_200) < _STARTER_200_COUNT:
        raise ValueError(
            "Unable to build starter_200_symbols with configured discovery strategy. "
            f"Built {len(starter_200)} symbols."
        )
    return starter_200[:_STARTER_200_COUNT]


def _build_symbol_universe_payload(*, dataset_json_path: Path) -> dict[str, object]:
    """Build one versioned symbol-universe payload for repository use."""

    required_portfolio_symbols = _load_required_portfolio_symbols(
        dataset_json_path=dataset_json_path
    )
    equity_candidates = _collect_equity_candidates()
    etf_candidates = _collect_etf_candidates()
    starter_200_symbols = _build_starter_200(
        required_portfolio_symbols=required_portfolio_symbols,
        equity_candidates=equity_candidates,
        etf_candidates=etf_candidates,
    )
    starter_100_symbols = starter_200_symbols[:_STARTER_100_COUNT]

    missing_required_from_100 = sorted(set(required_portfolio_symbols) - set(starter_100_symbols))
    if missing_required_from_100:
        raise ValueError(
            "starter_100_symbols is missing required portfolio symbols: "
            f"{', '.join(missing_required_from_100)}."
        )
    missing_required_from_200 = sorted(set(required_portfolio_symbols) - set(starter_200_symbols))
    if missing_required_from_200:
        raise ValueError(
            "starter_200_symbols is missing required portfolio symbols: "
            f"{', '.join(missing_required_from_200)}."
        )

    payload: dict[str, object] = {
        "schema_version": "v1",
        "generated_at_utc": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        "source_provider": "yfinance",
        "required_portfolio_symbols": required_portfolio_symbols,
        "core_refresh_symbols": required_portfolio_symbols,
        "starter_100_symbols": starter_100_symbols,
        "starter_200_symbols": starter_200_symbols,
        "selection_metadata": {
            "equity_queries": list(_EQUITY_SCREEN_QUERIES),
            "etf_lookup_query": "ETF",
            "liquid_us_exchanges": sorted(_LIQUID_US_EXCHANGES),
            "stock_fill_target": _STOCK_FILL_TARGET,
        },
    }
    return payload


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for symbol-universe generation script."""

    parser = argparse.ArgumentParser(
        description=(
            "Build a versioned market-data symbol universe JSON (required portfolio + "
            "starter 100/200 libraries) using yfinance discovery surfaces."
        )
    )
    parser.add_argument(
        "--dataset-json-path",
        type=Path,
        default=_DATASET_DEFAULT_PATH,
        help="Path to canonical dataset JSON used to derive required portfolio symbols.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=_OUTPUT_DEFAULT_PATH,
        help="Output path for generated symbol universe JSON.",
    )
    return parser


def main() -> int:
    """Generate symbol-universe payload and persist JSON to output path."""

    parser = _build_parser()
    args = parser.parse_args()

    payload = _build_symbol_universe_payload(dataset_json_path=args.dataset_json_path)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
