"""Contract tests for portfolio-ledger schema and accounting-policy constants."""

from __future__ import annotations

from datetime import date
from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, cast

import pytest
from pydantic import ValidationError

if TYPE_CHECKING:
    from app.portfolio_ledger.accounting import (
        AccountingPolicyConfig,
        AccountingPolicyVersion,
        LotMatchingMethod,
        UnsupportedAccountingConcern,
    )
    from app.portfolio_ledger.schemas import LedgerEventType, PersistedCanonicalRecord


def _load_accounting_module() -> ModuleType:
    """Load accounting module in fail-first mode for task 2.1."""

    try:
        return import_module("app.portfolio_ledger.accounting")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ledger.accounting. "
            "Implement task 2.1 before policy contract tests can pass.",
        )
        raise AssertionError from exc


def _load_schemas_module() -> ModuleType:
    """Load schemas module in fail-first mode for task 2.1."""

    try:
        return import_module("app.portfolio_ledger.schemas")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ledger.schemas. "
            "Implement task 2.1 before schema contract tests can pass.",
        )
        raise AssertionError from exc


def _load_from_module(module_name: str, symbol_name: str) -> object:
    """Load one named symbol from a module and fail fast when missing."""

    module = (
        _load_accounting_module()
        if module_name == "accounting"
        else _load_schemas_module()
    )
    symbol = getattr(module, symbol_name, None)
    if symbol is None:
        pytest.fail(
            f"Fail-first baseline: missing symbol {symbol_name} in app.portfolio_ledger.{module_name}. "
            "Implement task 2.1 before this test can pass.",
        )
    return symbol


def test_dataset_1_v1_policy_is_explicit_and_fifo() -> None:
    """Dataset 1 accounting policy must be explicitly versioned and FIFO-based."""

    policy = cast(
        "AccountingPolicyConfig",
        _load_from_module(
            "accounting",
            "DATASET_1_V1_ACCOUNTING_POLICY",
        ),
    )
    version_enum = cast(
        "type[AccountingPolicyVersion]",
        _load_from_module(
            "accounting",
            "AccountingPolicyVersion",
        ),
    )
    lot_method_enum = cast(
        "type[LotMatchingMethod]",
        _load_from_module(
            "accounting",
            "LotMatchingMethod",
        ),
    )
    event_type_enum = cast(
        "type[LedgerEventType]",
        _load_from_module(
            "schemas",
            "LedgerEventType",
        ),
    )

    assert policy.version == version_enum.DATASET_1_V1
    assert policy.lot_matching_method == lot_method_enum.FIFO
    assert policy.buy_cost_basis_field == "aporte_usd"
    assert policy.sell_proceeds_field == "rescate_usd"
    assert policy.dividends_change_lot_basis is False
    assert policy.splits_realize_gain is False
    assert policy.supported_event_types == (
        event_type_enum.TRADE,
        event_type_enum.DIVIDEND,
        event_type_enum.SPLIT,
    )


def test_dataset_1_v1_policy_keeps_fee_and_fx_unsupported() -> None:
    """Dataset 1 policy must keep unsupported accounting concerns explicit."""

    policy = cast(
        "AccountingPolicyConfig",
        _load_from_module(
            "accounting",
            "DATASET_1_V1_ACCOUNTING_POLICY",
        ),
    )
    unsupported_enum = cast(
        "type[UnsupportedAccountingConcern]",
        _load_from_module(
            "accounting",
            "UnsupportedAccountingConcern",
        ),
    )

    assert policy.infer_fee_adjustments is False
    assert policy.infer_fx_adjustments is False
    assert set(policy.unsupported_concerns) == {
        unsupported_enum.FEE_ADJUSTMENT,
        unsupported_enum.FX_ADJUSTMENT,
        unsupported_enum.UNSUPPORTED_CORPORATE_ACTION,
    }


def test_persisted_canonical_record_schema_limits_event_types_to_dataset_1() -> None:
    """Persisted canonical schema should accept only trade/dividend/split event types."""

    persisted_record_type = cast(
        "type[PersistedCanonicalRecord]",
        _load_from_module(
            "schemas",
            "PersistedCanonicalRecord",
        ),
    )

    valid_record = persisted_record_type.model_validate(
        {
            "canonical_record_id": 1,
            "source_document_id": 1,
            "import_job_id": 1,
            "fingerprint": "fp-1",
            "event_type": "trade",
            "event_date": date(2025, 1, 10),
            "instrument_symbol": "VOO",
            "trade_side": "buy",
            "canonical_payload": {"event_type": "trade"},
        }
    )
    assert valid_record is not None

    with pytest.raises(ValidationError):
        persisted_record_type.model_validate(
            {
                "canonical_record_id": 1,
                "source_document_id": 1,
                "import_job_id": 1,
                "fingerprint": "fp-2",
                "event_type": "fee",
                "event_date": date(2025, 1, 10),
                "instrument_symbol": "VOO",
                "trade_side": None,
                "canonical_payload": {"event_type": "fee"},
            }
        )
