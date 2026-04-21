"""Contract tests for dataset-driven market symbol universe artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

_DATASET_PATH = Path("app/golden_sets/dataset_1/202602_stocks.json")
_UNIVERSE_PATH = Path("app/market_data/symbol_universe.v1.json")


class TradeRow(TypedDict):
    """Minimal trade row shape needed for the symbol-universe contract."""

    simbolo_activo: str


class TradeTable(TypedDict):
    """Minimal table shape for dataset_1 trade rows."""

    rows: list[TradeRow]


class DatasetTables(TypedDict):
    """Dataset table collection used by the contract test."""

    compra_venta_activos: TradeTable


class DatasetPayload(TypedDict):
    """Dataset payload shape used by the contract test."""

    tables: DatasetTables


class SymbolUniversePayload(TypedDict):
    """Symbol-universe payload shape used by the contract test."""

    required_portfolio_symbols: list[str]
    core_refresh_symbols: list[str]


def _load_dataset_trade_symbols() -> list[str]:
    """Load distinct trade symbols from canonical dataset_1 JSON."""

    payload = cast(
        DatasetPayload, json.loads(_DATASET_PATH.read_text(encoding="utf-8"))
    )
    dataset_payload = payload
    trade_rows = dataset_payload["tables"]["compra_venta_activos"]["rows"]
    symbols = {
        str(row["simbolo_activo"]).strip().upper()
        for row in trade_rows
        if row["simbolo_activo"]
    }
    return sorted(symbols)


def _load_symbol_universe_payload() -> SymbolUniversePayload:
    """Load market symbol-universe artifact from repository."""

    payload = cast(
        SymbolUniversePayload, json.loads(_UNIVERSE_PATH.read_text(encoding="utf-8"))
    )
    return payload


def test_symbol_universe_required_symbols_match_dataset_trade_symbols() -> None:
    """Required symbols must mirror dataset trade symbols exactly."""

    dataset_symbols = _load_dataset_trade_symbols()
    symbol_universe_payload = _load_symbol_universe_payload()
    required_symbols = symbol_universe_payload["required_portfolio_symbols"]
    assert required_symbols == dataset_symbols


def test_symbol_universe_core_refresh_symbols_match_required_symbols() -> None:
    """Core refresh symbols must stay aligned with required portfolio symbols."""

    symbol_universe_payload = _load_symbol_universe_payload()
    required_symbols = symbol_universe_payload["required_portfolio_symbols"]
    core_refresh_symbols = symbol_universe_payload["core_refresh_symbols"]
    assert core_refresh_symbols == required_symbols
