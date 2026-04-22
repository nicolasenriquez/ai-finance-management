"""Fail-first contract tests for portfolio-ledger SQLAlchemy models."""

from __future__ import annotations

from importlib import import_module

import pytest
from sqlalchemy import Table, UniqueConstraint


def _load_models_module() -> object:
    """Load portfolio-ledger models module in fail-first mode for task 2.2."""

    try:
        return import_module("app.portfolio_ledger.models")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ledger.models. "
            "Implement task 2.2 before model schema tests can pass.",
        )
        raise AssertionError from exc


def _load_model_class(name: str) -> object:
    """Load one named model class from portfolio-ledger models."""

    module = _load_models_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing model class {name}. "
            "Implement task 2.2 before model schema tests can pass.",
        )
    return candidate


def _get_table(table_name: str) -> Table:
    """Return SQLAlchemy table metadata entry by name."""

    from app.core.database import Base

    table = Base.metadata.tables.get(table_name)
    if table is None:
        pytest.fail(
            f"Expected SQLAlchemy table '{table_name}' to exist in metadata for task 2.2.",
        )
    return table


def _unique_column_sets(table: Table) -> set[frozenset[str]]:
    """Return unique-constraint column sets for a table."""

    unique_sets: set[frozenset[str]] = set()
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            unique_sets.add(frozenset(column.name for column in constraint.columns))
    for column in table.columns:
        if column.unique:
            unique_sets.add(frozenset({column.name}))
    return unique_sets


def _foreign_key_pairs(table: Table) -> set[tuple[str, str]]:
    """Return (local_column, referenced_table.column) pairs for foreign keys."""

    pairs: set[tuple[str, str]] = set()
    for constraint in table.foreign_key_constraints:
        for element in constraint.elements:
            target = f"{element.column.table.name}.{element.column.name}"
            pairs.add((element.parent.name, target))
    return pairs


def test_minimal_portfolio_ledger_models_are_defined_for_dataset_1_v1() -> None:
    """Task 2.2 requires the five minimal ledger and lot models."""

    _load_model_class("PortfolioTransaction")
    _load_model_class("DividendEvent")
    _load_model_class("CorporateActionEvent")
    _load_model_class("Lot")
    _load_model_class("LotDisposition")

    assert _get_table("portfolio_transaction") is not None
    assert _get_table("dividend_event") is not None
    assert _get_table("corporate_action_event") is not None
    assert _get_table("lot") is not None
    assert _get_table("lot_disposition") is not None


def test_minimal_uniqueness_contract_supports_idempotent_rebuild_foundation() -> None:
    """Event tables and lot derivation tables must enforce deterministic uniqueness."""

    transaction_unique_sets = _unique_column_sets(_get_table("portfolio_transaction"))
    assert frozenset({"canonical_record_id"}) in transaction_unique_sets

    dividend_unique_sets = _unique_column_sets(_get_table("dividend_event"))
    assert frozenset({"canonical_record_id"}) in dividend_unique_sets

    corporate_action_unique_sets = _unique_column_sets(_get_table("corporate_action_event"))
    assert frozenset({"canonical_record_id"}) in corporate_action_unique_sets

    lot_unique_sets = _unique_column_sets(_get_table("lot"))
    assert frozenset({"opening_transaction_id"}) in lot_unique_sets

    lot_disposition_unique_sets = _unique_column_sets(_get_table("lot_disposition"))
    assert frozenset({"lot_id", "sell_transaction_id"}) in lot_disposition_unique_sets


def test_lineage_and_derivation_foreign_keys_are_explicit() -> None:
    """Task 2.2 tables should keep explicit lineage and derivation links."""

    event_fk_expectations = {
        ("source_document_id", "source_document.id"),
        ("import_job_id", "import_job.id"),
        ("canonical_record_id", "canonical_pdf_record.id"),
    }

    assert event_fk_expectations.issubset(
        _foreign_key_pairs(_get_table("portfolio_transaction")),
    )
    assert event_fk_expectations.issubset(
        _foreign_key_pairs(_get_table("dividend_event")),
    )
    assert event_fk_expectations.issubset(
        _foreign_key_pairs(_get_table("corporate_action_event")),
    )

    assert {
        ("opening_transaction_id", "portfolio_transaction.id"),
    }.issubset(_foreign_key_pairs(_get_table("lot")))
    assert {
        ("lot_id", "lot.id"),
        ("sell_transaction_id", "portfolio_transaction.id"),
    }.issubset(_foreign_key_pairs(_get_table("lot_disposition")))
