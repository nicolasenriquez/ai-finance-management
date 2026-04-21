"""Fail-first tests for PDF normalization behavior."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from app.pdf_normalization.schemas import PdfNormalizationResult

NormalizationCallable = Callable[..., object]

_GOLDEN_PDF_PATH = Path("app/golden_sets/dataset_1/202602_stocks.pdf")


def _load_golden_pdf_bytes() -> bytes:
    """Load dataset 1 PDF bytes from repository fixtures."""

    return _GOLDEN_PDF_PATH.read_bytes()


def _seed_storage_key(tmp_path: Path) -> str:
    """Write dataset 1 PDF into a temporary storage root."""

    storage_key = "dataset_1.pdf"
    (tmp_path / storage_key).write_bytes(_load_golden_pdf_bytes())
    return storage_key


def _load_normalization_module() -> object:
    """Load normalization service module in fail-first mode."""

    try:
        return import_module("app.pdf_normalization.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.pdf_normalization.service. "
            "Implement tasks 2.1-2.2 before normalization tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> NormalizationCallable:
    """Load named callable from normalization service module."""

    module = _load_normalization_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(NormalizationCallable, candidate)


def test_parse_date_value_normalizes_iso_date() -> None:
    """Normalization should parse ISO date strings deterministically."""

    parse_date_value = _load_callable("parse_date_value", task_hint="2.2")

    parsed = parse_date_value("2024-12-26")
    assert parsed == date(2024, 12, 26)


def test_parse_decimal_comma_value_parses_locale_numbers() -> None:
    """Normalization should parse decimal-comma source values."""

    parse_decimal_comma_value = _load_callable(
        "parse_decimal_comma_value", task_hint="2.2"
    )

    assert parse_decimal_comma_value("US $ 112,80") == Decimal("112.80")
    assert parse_decimal_comma_value("0,284897406") == Decimal("0.284897406")


def test_normalize_blank_cell_returns_none_for_empty_values() -> None:
    """Blank source cells should normalize to None."""

    normalize_blank_cell = _load_callable("normalize_blank_cell", task_hint="2.2")

    assert normalize_blank_cell(None) is None
    assert normalize_blank_cell("") is None
    assert normalize_blank_cell("   ") is None
    assert normalize_blank_cell("US $ 1,00") == "US $ 1,00"


def test_derive_trade_side_is_deterministic_for_buy_and_sell() -> None:
    """Trade side derivation should be deterministic from monetary and quantity fields."""

    derive_trade_side = _load_callable("derive_trade_side", task_hint="2.2")

    buy_side = derive_trade_side(
        aporte_usd=Decimal("10.00"),
        acciones_compradas_qty=Decimal("1.50"),
        rescate_usd=None,
        acciones_vendidas_qty=None,
    )
    sell_side = derive_trade_side(
        aporte_usd=None,
        acciones_compradas_qty=None,
        rescate_usd=Decimal("10.00"),
        acciones_vendidas_qty=Decimal("1.50"),
    )
    assert buy_side == "buy"
    assert sell_side == "sell"


def test_derive_trade_side_rejects_ambiguous_combinations() -> None:
    """Ambiguous trade-side combinations should fail fast."""

    derive_trade_side = _load_callable("derive_trade_side", task_hint="2.2")

    with pytest.raises(Exception):  # noqa: B017
        derive_trade_side(
            aporte_usd=Decimal("10.00"),
            acciones_compradas_qty=Decimal("1.50"),
            rescate_usd=Decimal("5.00"),
            acciones_vendidas_qty=Decimal("0.50"),
        )


def test_normalize_pdf_from_storage_returns_canonical_records(tmp_path: Path) -> None:
    """Normalization should return canonical records for dataset 1."""

    normalize_pdf_from_storage = _load_callable(
        "normalize_pdf_from_storage", task_hint="2.1"
    )
    storage_key = _seed_storage_key(tmp_path)

    result = cast(
        PdfNormalizationResult,
        normalize_pdf_from_storage(storage_key=storage_key, storage_root=tmp_path),
    )

    assert result.storage_key == storage_key
    assert result.summary.trade_records == 136
    assert result.summary.dividend_records == 34
    assert result.summary.split_records == 1


def test_normalize_trade_row_rejects_invalid_trade_row() -> None:
    """Normalization should reject invalid trade-row field combinations."""

    normalize_trade_row = _load_callable("normalize_trade_row", task_hint="2.2")

    ambiguous_trade_row = {
        "fecha": "2025-01-10",
        "nombre_activo": "Vanguard S&P 500 ETF",
        "simbolo_activo": "VOO",
        "categoria_activo": "ETF",
        "aporte_dolares": "US $ 10,00",
        "acciones_compradas": "0,010000000",
        "rescate_dolares": "US $ 2,00",
        "acciones_vendidas": "0,002000000",
    }

    with pytest.raises(Exception):  # noqa: B017
        normalize_trade_row(
            raw_cells=ambiguous_trade_row,
            row_id=1,
            row_index=1,
            source_page=1,
            table_name="compra_venta_activos",
        )
