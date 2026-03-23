"""Fail-first integration tests for duplicate-safe portfolio-ledger rebuilds."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import func, select, table, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.pdf_persistence.models import CanonicalPdfRecord, ImportJob, SourceDocument
from app.portfolio_ledger.models import DividendEvent, Lot, LotDisposition, PortfolioTransaction

RebuildCallable = Callable[..., Awaitable[Mapping[str, object]]]

_SEED_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "dataset_1_v1_canonical_seed.json"
_LEDGER_TABLES: tuple[str, ...] = (
    "portfolio_transaction",
    "dividend_event",
    "corporate_action_event",
    "lot",
    "lot_disposition",
)
_TRUNCATE_CANDIDATES: tuple[str, ...] = (
    "lot_disposition",
    "lot",
    "corporate_action_event",
    "dividend_event",
    "portfolio_transaction",
    "canonical_pdf_record",
    "import_job",
    "source_document",
)


def _load_portfolio_ledger_module() -> object:
    """Load portfolio-ledger service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ledger.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ledger.service. "
            "Implement tasks 2.2-3.3 before ledger rebuild integration tests can pass.",
        )
        raise AssertionError from exc


def _load_rebuild_callable(name: str, *, task_hint: str) -> RebuildCallable:
    """Load named rebuild callable from portfolio-ledger service module."""

    module = _load_portfolio_ledger_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(RebuildCallable, candidate)


def _load_seed_fixture() -> tuple[dict[str, object], list[dict[str, object]]]:
    """Load deterministic persisted-canonical seed data for integration tests."""

    payload = cast(dict[str, object], json.loads(_SEED_FIXTURE_PATH.read_text()))
    source_document = payload.get("source_document")
    canonical_records = payload.get("canonical_records")
    if not isinstance(source_document, dict) or not isinstance(canonical_records, list):
        pytest.fail(
            f"Invalid seed fixture structure in {_SEED_FIXTURE_PATH}.",
        )
    return cast(dict[str, object], source_document), cast(
        list[dict[str, object]], canonical_records
    )


async def _table_exists(db: AsyncSession, table_name: str) -> bool:
    """Return whether a public table exists in the current database."""

    result = await db.execute(
        text("SELECT to_regclass(:regclass_name)"),
        {"regclass_name": f"public.{table_name}"},
    )
    return result.scalar_one() is not None


async def _truncate_tables_if_present(db: AsyncSession) -> None:
    """Truncate known integration tables when they exist."""

    existing_tables = [
        table_name for table_name in _TRUNCATE_CANDIDATES if await _table_exists(db, table_name)
    ]
    if not existing_tables:
        return

    truncate_sql = f"TRUNCATE TABLE {', '.join(existing_tables)} RESTART IDENTITY CASCADE"
    await db.execute(text(truncate_sql))
    await db.commit()


async def _seed_persisted_canonical_input(db: AsyncSession) -> int:
    """Insert deterministic source-document and canonical-record seed rows."""

    source_payload, canonical_records = _load_seed_fixture()

    source_document = SourceDocument(
        sha256=cast(str, source_payload["sha256"]),
        storage_key=cast(str, source_payload["storage_key"]),
        original_filename=cast(str, source_payload["original_filename"]),
        content_type=cast(str, source_payload["content_type"]),
        file_size_bytes=cast(int, source_payload["file_size_bytes"]),
        page_count=cast(int, source_payload["page_count"]),
    )
    db.add(source_document)
    await db.flush()

    import_job = ImportJob(
        source_document_id=source_document.id,
        storage_key=cast(str, source_payload["storage_key"]),
        normalized_records=len(canonical_records),
        inserted_records=len(canonical_records),
        duplicate_records=0,
    )
    db.add(import_job)
    await db.flush()

    for record in canonical_records:
        db.add(
            CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type=cast(str, record["event_type"]),
                event_date=date.fromisoformat(cast(str, record["event_date"])),
                instrument_symbol=cast(str, record["instrument_symbol"]),
                trade_side=cast(str | None, record["trade_side"]),
                fingerprint=cast(str, record["fingerprint"]),
                fingerprint_version=cast(str, record["fingerprint_version"]),
                canonical_schema_version=cast(str, record["canonical_schema_version"]),
                canonical_payload=cast(dict[str, object], record["canonical_payload"]),
                raw_values=cast(dict[str, str | None], record["raw_values"]),
                provenance=cast(dict[str, object], record["provenance"]),
            )
        )

    await db.commit()
    return source_document.id


async def _seed_fractional_buy_sell_input(db: AsyncSession) -> int:
    """Insert canonical input with fractional-share buy and sell records."""

    source_document = SourceDocument(
        sha256="f9f47e367d92343f1138ddcc9ffd613fe79a7e540c38fe2d5f97de6ec7f4e00f",
        storage_key="integration-seed/fractional-basis.pdf",
        original_filename="fractional_basis_seed.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        page_count=1,
    )
    db.add(source_document)
    await db.flush()

    canonical_records: list[dict[str, object]] = [
        {
            "event_type": "trade",
            "event_date": "2025-01-10",
            "instrument_symbol": "VOO",
            "trade_side": "buy",
            "fingerprint": "fractional-buy-2025-01-10",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "buy",
                "trade_date": "2025-01-10",
                "instrument_symbol": "VOO",
                "aporte_usd": "100.00",
                "acciones_compradas_qty": "3.000000000",
                "rescate_usd": None,
                "acciones_vendidas_qty": None,
            },
            "raw_values": {
                "fecha": "2025-01-10",
                "simbolo_activo": "VOO",
                "aporte_dolares": "US $ 100,00",
                "acciones_compradas": "3,000000000",
                "rescate_dolares": None,
                "acciones_vendidas": None,
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 1,
                "source_page": 1,
            },
        },
        {
            "event_type": "trade",
            "event_date": "2025-01-20",
            "instrument_symbol": "VOO",
            "trade_side": "sell",
            "fingerprint": "fractional-sell-2025-01-20",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "sell",
                "trade_date": "2025-01-20",
                "instrument_symbol": "VOO",
                "aporte_usd": None,
                "acciones_compradas_qty": None,
                "rescate_usd": "70.00",
                "acciones_vendidas_qty": "2.000000000",
            },
            "raw_values": {
                "fecha": "2025-01-20",
                "simbolo_activo": "VOO",
                "aporte_dolares": None,
                "acciones_compradas": None,
                "rescate_dolares": "US $ 70,00",
                "acciones_vendidas": "2,000000000",
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 2,
                "source_page": 1,
            },
        },
    ]

    import_job = ImportJob(
        source_document_id=source_document.id,
        storage_key=source_document.storage_key,
        normalized_records=len(canonical_records),
        inserted_records=len(canonical_records),
        duplicate_records=0,
    )
    db.add(import_job)
    await db.flush()

    for record in canonical_records:
        db.add(
            CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type=cast(str, record["event_type"]),
                event_date=date.fromisoformat(cast(str, record["event_date"])),
                instrument_symbol=cast(str, record["instrument_symbol"]),
                trade_side=cast(str | None, record["trade_side"]),
                fingerprint=cast(str, record["fingerprint"]),
                fingerprint_version=cast(str, record["fingerprint_version"]),
                canonical_schema_version=cast(str, record["canonical_schema_version"]),
                canonical_payload=cast(dict[str, object], record["canonical_payload"]),
                raw_values=cast(dict[str, str | None], record["raw_values"]),
                provenance=cast(dict[str, object], record["provenance"]),
            )
        )

    await db.commit()
    return source_document.id


async def _seed_fractional_buy_three_partial_sells_input(db: AsyncSession) -> int:
    """Insert canonical input for one fractional lot consumed by three partial sells."""

    source_document = SourceDocument(
        sha256="aef21db7f81a4bcf2575f9e8f5c0e8c1799749bcc4f5bf444f0540927a7f7562",
        storage_key="integration-seed/fractional-three-sells.pdf",
        original_filename="fractional_three_sells_seed.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        page_count=1,
    )
    db.add(source_document)
    await db.flush()

    canonical_records: list[dict[str, object]] = [
        {
            "event_type": "trade",
            "event_date": "2025-01-10",
            "instrument_symbol": "VOO",
            "trade_side": "buy",
            "fingerprint": "fractional-three-buy-2025-01-10",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "buy",
                "trade_date": "2025-01-10",
                "instrument_symbol": "VOO",
                "aporte_usd": "100.00",
                "acciones_compradas_qty": "3.000000000",
                "rescate_usd": None,
                "acciones_vendidas_qty": None,
            },
            "raw_values": {
                "fecha": "2025-01-10",
                "simbolo_activo": "VOO",
                "aporte_dolares": "US $ 100,00",
                "acciones_compradas": "3,000000000",
                "rescate_dolares": None,
                "acciones_vendidas": None,
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 1,
                "source_page": 1,
            },
        },
        {
            "event_type": "trade",
            "event_date": "2025-01-20",
            "instrument_symbol": "VOO",
            "trade_side": "sell",
            "fingerprint": "fractional-three-sell-2025-01-20",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "sell",
                "trade_date": "2025-01-20",
                "instrument_symbol": "VOO",
                "aporte_usd": None,
                "acciones_compradas_qty": None,
                "rescate_usd": "40.00",
                "acciones_vendidas_qty": "1.000000000",
            },
            "raw_values": {
                "fecha": "2025-01-20",
                "simbolo_activo": "VOO",
                "aporte_dolares": None,
                "acciones_compradas": None,
                "rescate_dolares": "US $ 40,00",
                "acciones_vendidas": "1,000000000",
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 2,
                "source_page": 1,
            },
        },
        {
            "event_type": "trade",
            "event_date": "2025-01-21",
            "instrument_symbol": "VOO",
            "trade_side": "sell",
            "fingerprint": "fractional-three-sell-2025-01-21",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "sell",
                "trade_date": "2025-01-21",
                "instrument_symbol": "VOO",
                "aporte_usd": None,
                "acciones_compradas_qty": None,
                "rescate_usd": "35.00",
                "acciones_vendidas_qty": "1.000000000",
            },
            "raw_values": {
                "fecha": "2025-01-21",
                "simbolo_activo": "VOO",
                "aporte_dolares": None,
                "acciones_compradas": None,
                "rescate_dolares": "US $ 35,00",
                "acciones_vendidas": "1,000000000",
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 3,
                "source_page": 1,
            },
        },
        {
            "event_type": "trade",
            "event_date": "2025-01-22",
            "instrument_symbol": "VOO",
            "trade_side": "sell",
            "fingerprint": "fractional-three-sell-2025-01-22",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "sell",
                "trade_date": "2025-01-22",
                "instrument_symbol": "VOO",
                "aporte_usd": None,
                "acciones_compradas_qty": None,
                "rescate_usd": "30.00",
                "acciones_vendidas_qty": "1.000000000",
            },
            "raw_values": {
                "fecha": "2025-01-22",
                "simbolo_activo": "VOO",
                "aporte_dolares": None,
                "acciones_compradas": None,
                "rescate_dolares": "US $ 30,00",
                "acciones_vendidas": "1,000000000",
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 4,
                "source_page": 1,
            },
        },
    ]

    import_job = ImportJob(
        source_document_id=source_document.id,
        storage_key=source_document.storage_key,
        normalized_records=len(canonical_records),
        inserted_records=len(canonical_records),
        duplicate_records=0,
    )
    db.add(import_job)
    await db.flush()

    for record in canonical_records:
        db.add(
            CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type=cast(str, record["event_type"]),
                event_date=date.fromisoformat(cast(str, record["event_date"])),
                instrument_symbol=cast(str, record["instrument_symbol"]),
                trade_side=cast(str | None, record["trade_side"]),
                fingerprint=cast(str, record["fingerprint"]),
                fingerprint_version=cast(str, record["fingerprint_version"]),
                canonical_schema_version=cast(str, record["canonical_schema_version"]),
                canonical_payload=cast(dict[str, object], record["canonical_payload"]),
                raw_values=cast(dict[str, str | None], record["raw_values"]),
                provenance=cast(dict[str, object], record["provenance"]),
            )
        )

    await db.commit()
    return source_document.id


async def _seed_same_day_split_before_sell_input(db: AsyncSession) -> int:
    """Insert canonical input where a same-day split must occur before sell."""

    source_document = SourceDocument(
        sha256="6ce2e228381efe868a08d805fb2d0dbddcf84af18e3014f805f7096e6b35e718",
        storage_key="integration-seed/same-day-split-before-sell.pdf",
        original_filename="same_day_split_before_sell_seed.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        page_count=1,
    )
    db.add(source_document)
    await db.flush()

    canonical_records: list[dict[str, object]] = [
        {
            "event_type": "trade",
            "event_date": "2025-01-10",
            "instrument_symbol": "VOO",
            "trade_side": "buy",
            "fingerprint": "same-day-split-buy-2025-01-10",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "buy",
                "trade_date": "2025-01-10",
                "instrument_symbol": "VOO",
                "aporte_usd": "100.00",
                "acciones_compradas_qty": "1.000000000",
                "rescate_usd": None,
                "acciones_vendidas_qty": None,
            },
            "raw_values": {
                "fecha": "2025-01-10",
                "simbolo_activo": "VOO",
                "aporte_dolares": "US $ 100,00",
                "acciones_compradas": "1,000000000",
                "rescate_dolares": None,
                "acciones_vendidas": None,
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 1,
                "source_page": 1,
            },
        },
        {
            "event_type": "split",
            "event_date": "2025-02-10",
            "instrument_symbol": "VOO",
            "trade_side": None,
            "fingerprint": "same-day-split-event-2025-02-10",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "split",
                "split_date": "2025-02-10",
                "instrument_symbol": "VOO",
                "shares_before_qty": "1.000000000",
                "shares_after_qty": "2.000000000",
                "split_ratio_value": "2.00",
            },
            "raw_values": {
                "fecha": "2025-02-10",
                "simbolo_activo": "VOO",
                "acciones_antes": "1,000000000",
                "acciones_despues": "2,000000000",
                "ratio_split": "2,00",
            },
            "provenance": {
                "table_name": "splits",
                "row_index": 1,
                "source_page": 2,
            },
        },
        {
            "event_type": "trade",
            "event_date": "2025-02-10",
            "instrument_symbol": "VOO",
            "trade_side": "sell",
            "fingerprint": "same-day-split-sell-2025-02-10",
            "fingerprint_version": "v1",
            "canonical_schema_version": "dataset_1_v1",
            "canonical_payload": {
                "event_type": "trade",
                "trade_side": "sell",
                "trade_date": "2025-02-10",
                "instrument_symbol": "VOO",
                "aporte_usd": None,
                "acciones_compradas_qty": None,
                "rescate_usd": "120.00",
                "acciones_vendidas_qty": "2.000000000",
            },
            "raw_values": {
                "fecha": "2025-02-10",
                "simbolo_activo": "VOO",
                "aporte_dolares": None,
                "acciones_compradas": None,
                "rescate_dolares": "US $ 120,00",
                "acciones_vendidas": "2,000000000",
            },
            "provenance": {
                "table_name": "compra_venta_activos",
                "row_index": 2,
                "source_page": 2,
            },
        },
    ]

    import_job = ImportJob(
        source_document_id=source_document.id,
        storage_key=source_document.storage_key,
        normalized_records=len(canonical_records),
        inserted_records=len(canonical_records),
        duplicate_records=0,
    )
    db.add(import_job)
    await db.flush()

    for record in canonical_records:
        db.add(
            CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type=cast(str, record["event_type"]),
                event_date=date.fromisoformat(cast(str, record["event_date"])),
                instrument_symbol=cast(str, record["instrument_symbol"]),
                trade_side=cast(str | None, record["trade_side"]),
                fingerprint=cast(str, record["fingerprint"]),
                fingerprint_version=cast(str, record["fingerprint_version"]),
                canonical_schema_version=cast(str, record["canonical_schema_version"]),
                canonical_payload=cast(dict[str, object], record["canonical_payload"]),
                raw_values=cast(dict[str, str | None], record["raw_values"]),
                provenance=cast(dict[str, object], record["provenance"]),
            )
        )

    await db.commit()
    return source_document.id


async def _fetch_ledger_table_counts(db: AsyncSession) -> dict[str, int]:
    """Fetch row counts for ledger and lot tables that rebuild should populate."""

    counts: dict[str, int] = {}
    for table_name in _LEDGER_TABLES:
        if not await _table_exists(db, table_name):
            pytest.fail(
                "Ledger integration tests require migrated ledger tables. "
                "Implement task 2.2 and run migrations before expecting pass.",
            )
        count_statement = select(func.count()).select_from(table(table_name))
        result = await db.execute(count_statement)
        counts[table_name] = result.scalar_one()
    return counts


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_rerun_from_persisted_canonical_input_is_duplicate_safe(
    test_db_session: AsyncSession,
) -> None:
    """Rerunning ledger rebuild for the same canonical source should not duplicate rows."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_persisted_canonical_input(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)
    first_counts = await _fetch_ledger_table_counts(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)
    second_counts = await _fetch_ledger_table_counts(test_db_session)

    assert second_counts == first_counts
    assert first_counts["portfolio_transaction"] >= 1
    assert first_counts["dividend_event"] >= 1
    assert first_counts["corporate_action_event"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_updates_existing_derived_trade_when_canonical_payload_changes(
    test_db_session: AsyncSession,
) -> None:
    """Rebuild should update derived trade rows when canonical payload values change."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_fractional_buy_sell_input(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    sell_trade_result = await test_db_session.execute(
        select(PortfolioTransaction).where(
            PortfolioTransaction.source_document_id == source_document_id,
            PortfolioTransaction.trade_side == "sell",
        )
    )
    initial_sell_trade = sell_trade_result.scalar_one()
    assert initial_sell_trade.gross_amount_usd == Decimal("70.00")

    sell_canonical_result = await test_db_session.execute(
        select(CanonicalPdfRecord).where(
            CanonicalPdfRecord.source_document_id == source_document_id,
            CanonicalPdfRecord.event_type == "trade",
            CanonicalPdfRecord.trade_side == "sell",
        )
    )
    sell_canonical_record = sell_canonical_result.scalar_one()
    updated_payload = dict(sell_canonical_record.canonical_payload)
    updated_payload["rescate_usd"] = "80.00"
    sell_canonical_record.canonical_payload = updated_payload
    await test_db_session.commit()

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    refreshed_sell_trade_result = await test_db_session.execute(
        select(PortfolioTransaction)
        .execution_options(populate_existing=True)
        .where(
            PortfolioTransaction.source_document_id == source_document_id,
            PortfolioTransaction.trade_side == "sell",
        )
    )
    refreshed_sell_trade = refreshed_sell_trade_result.scalar_one()
    assert refreshed_sell_trade.gross_amount_usd == Decimal("80.00")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_does_not_expire_preloaded_transaction_instance(
    test_db_session: AsyncSession,
) -> None:
    """Rebuild should not expire caller-loaded ledger instances in async sessions."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_fractional_buy_sell_input(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    preloaded_trade_result = await test_db_session.execute(
        select(PortfolioTransaction).where(
            PortfolioTransaction.source_document_id == source_document_id,
            PortfolioTransaction.trade_side == "sell",
        )
    )
    preloaded_trade = preloaded_trade_result.scalar_one()

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    assert preloaded_trade.trade_side == "sell"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_event_upsert_updates_updated_at_on_canonical_change(
    test_db_session: AsyncSession,
) -> None:
    """Rebuild upsert should update event-row updated_at when canonical values change."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_fractional_buy_sell_input(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    initial_sell_trade_result = await test_db_session.execute(
        select(PortfolioTransaction).where(
            PortfolioTransaction.source_document_id == source_document_id,
            PortfolioTransaction.trade_side == "sell",
        )
    )
    initial_sell_trade = initial_sell_trade_result.scalar_one()
    initial_updated_at = cast(datetime, initial_sell_trade.updated_at)
    initial_sell_trade_id = initial_sell_trade.id

    sell_canonical_result = await test_db_session.execute(
        select(CanonicalPdfRecord).where(
            CanonicalPdfRecord.source_document_id == source_document_id,
            CanonicalPdfRecord.event_type == "trade",
            CanonicalPdfRecord.trade_side == "sell",
        )
    )
    sell_canonical_record = sell_canonical_result.scalar_one()
    updated_payload = dict(sell_canonical_record.canonical_payload)
    updated_payload["rescate_usd"] = "80.00"
    sell_canonical_record.canonical_payload = updated_payload
    await test_db_session.commit()

    await asyncio.sleep(0.01)
    await rebuild(source_document_id=source_document_id, db=test_db_session)

    refreshed_sell_trade_result = await test_db_session.execute(
        select(PortfolioTransaction)
        .execution_options(populate_existing=True)
        .where(PortfolioTransaction.id == initial_sell_trade_id)
    )
    refreshed_sell_trade = refreshed_sell_trade_result.scalar_one()
    refreshed_updated_at = cast(datetime, refreshed_sell_trade.updated_at)

    assert refreshed_sell_trade.gross_amount_usd == Decimal("80.00")
    assert refreshed_updated_at > initial_updated_at


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_event_type_change_prunes_stale_trade_row(
    test_db_session: AsyncSession,
) -> None:
    """Rebuild should remove stale trade rows when canonical event type changes."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_fractional_buy_sell_input(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    sell_canonical_result = await test_db_session.execute(
        select(CanonicalPdfRecord).where(
            CanonicalPdfRecord.source_document_id == source_document_id,
            CanonicalPdfRecord.event_type == "trade",
            CanonicalPdfRecord.trade_side == "sell",
        )
    )
    sell_canonical_record = sell_canonical_result.scalar_one()
    canonical_record_id = sell_canonical_record.id
    updated_payload = dict(sell_canonical_record.canonical_payload)
    updated_payload["event_type"] = "dividend"
    updated_payload["gross_usd"] = "80.00"
    updated_payload["taxes_usd"] = "8.00"
    updated_payload["net_usd"] = "72.00"
    sell_canonical_record.event_type = "dividend"
    sell_canonical_record.trade_side = None
    sell_canonical_record.canonical_payload = updated_payload
    await test_db_session.commit()

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    stale_trade_result = await test_db_session.execute(
        select(PortfolioTransaction).where(
            PortfolioTransaction.canonical_record_id == canonical_record_id,
        )
    )
    assert stale_trade_result.scalar_one_or_none() is None

    derived_dividend_result = await test_db_session.execute(
        select(DividendEvent).where(
            DividendEvent.canonical_record_id == canonical_record_id,
        )
    )
    derived_dividend = derived_dividend_result.scalar_one()
    assert derived_dividend.gross_amount_usd == Decimal("80.00")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_prunes_stale_rows_when_canonical_record_moves_sources(
    test_db_session: AsyncSession,
) -> None:
    """Rebuild should remove stale derived rows no longer in source canonical set."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_fractional_buy_sell_input(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    moved_source_document = SourceDocument(
        sha256="66aab1ccdb988f9942df98576435b7f6f5e6d55146c00fb96416f6171178f73f",
        storage_key="integration-seed/moved-canonical-target.pdf",
        original_filename="moved_canonical_target.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        page_count=1,
    )
    test_db_session.add(moved_source_document)
    await test_db_session.flush()

    moved_import_job = ImportJob(
        source_document_id=moved_source_document.id,
        storage_key=moved_source_document.storage_key,
        normalized_records=1,
        inserted_records=1,
        duplicate_records=0,
    )
    test_db_session.add(moved_import_job)
    await test_db_session.flush()

    sell_canonical_result = await test_db_session.execute(
        select(CanonicalPdfRecord).where(
            CanonicalPdfRecord.source_document_id == source_document_id,
            CanonicalPdfRecord.event_type == "trade",
            CanonicalPdfRecord.trade_side == "sell",
        )
    )
    sell_canonical_record = sell_canonical_result.scalar_one()
    sell_canonical_record.source_document_id = moved_source_document.id
    sell_canonical_record.import_job_id = moved_import_job.id
    await test_db_session.commit()

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    remaining_transaction_result = await test_db_session.execute(
        select(PortfolioTransaction).where(
            PortfolioTransaction.source_document_id == source_document_id,
        )
    )
    remaining_transactions = list(remaining_transaction_result.scalars().all())
    assert len(remaining_transactions) == 1
    assert remaining_transactions[0].trade_side == "buy"

    lot_result = await test_db_session.execute(
        select(Lot)
        .join(
            PortfolioTransaction,
            Lot.opening_transaction_id == PortfolioTransaction.id,
        )
        .where(PortfolioTransaction.source_document_id == source_document_id),
    )
    lot_rows = list(lot_result.scalars().all())
    assert len(lot_rows) == 1
    lot_row = lot_rows[0]
    assert lot_row.remaining_qty == Decimal("3.000000000")
    assert lot_row.total_cost_basis_usd == Decimal("100.00")

    disposition_result = await test_db_session.execute(
        select(LotDisposition).where(LotDisposition.lot_id == lot_row.id),
    )
    disposition_rows = list(disposition_result.scalars().all())
    assert len(disposition_rows) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_clears_stale_lot_dispositions_for_moved_in_buy_record(
    test_db_session: AsyncSession,
) -> None:
    """Rebuild should clear stale lot dispositions for transactions moved into source."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    original_source_document_id = await _seed_fractional_buy_sell_input(test_db_session)

    await rebuild(source_document_id=original_source_document_id, db=test_db_session)

    moved_source_document = SourceDocument(
        sha256="b0a7f5e589539aabf14591eb39f3671b4c16a0de0c29f70de72f9e20857f4cf5",
        storage_key="integration-seed/moved-in-buy-source.pdf",
        original_filename="moved_in_buy_source.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        page_count=1,
    )
    test_db_session.add(moved_source_document)
    await test_db_session.flush()

    moved_import_job = ImportJob(
        source_document_id=moved_source_document.id,
        storage_key=moved_source_document.storage_key,
        normalized_records=1,
        inserted_records=1,
        duplicate_records=0,
    )
    test_db_session.add(moved_import_job)
    await test_db_session.flush()

    buy_canonical_result = await test_db_session.execute(
        select(CanonicalPdfRecord).where(
            CanonicalPdfRecord.source_document_id == original_source_document_id,
            CanonicalPdfRecord.event_type == "trade",
            CanonicalPdfRecord.trade_side == "buy",
        )
    )
    buy_canonical_record = buy_canonical_result.scalar_one()
    buy_canonical_record.source_document_id = moved_source_document.id
    buy_canonical_record.import_job_id = moved_import_job.id
    await test_db_session.commit()

    await rebuild(source_document_id=moved_source_document.id, db=test_db_session)

    moved_transaction_result = await test_db_session.execute(
        select(PortfolioTransaction).where(
            PortfolioTransaction.source_document_id == moved_source_document.id,
            PortfolioTransaction.trade_side == "buy",
        )
    )
    moved_transactions = list(moved_transaction_result.scalars().all())
    assert len(moved_transactions) == 1

    lot_result = await test_db_session.execute(
        select(Lot).where(Lot.opening_transaction_id == moved_transactions[0].id),
    )
    moved_lot = lot_result.scalar_one()
    assert moved_lot.remaining_qty == Decimal("3.000000000")
    assert moved_lot.total_cost_basis_usd == Decimal("100.00")

    disposition_result = await test_db_session.execute(
        select(LotDisposition).where(LotDisposition.lot_id == moved_lot.id),
    )
    disposition_rows = list(disposition_result.scalars().all())
    assert len(disposition_rows) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_concurrent_from_persisted_canonical_input_is_duplicate_safe(
    test_db_engine: AsyncEngine,
) -> None:
    """Concurrent rebuilds for identical canonical input should stay duplicate-safe."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as setup_session:
        await _truncate_tables_if_present(setup_session)
        source_document_id = await _seed_persisted_canonical_input(setup_session)

    async def rebuild_once() -> Mapping[str, object]:
        async with session_factory() as db_session:
            return await rebuild(source_document_id=source_document_id, db=db_session)

    await asyncio.wait_for(
        asyncio.gather(rebuild_once(), rebuild_once()),
        timeout=180.0,
    )

    async with session_factory() as verify_session:
        counts = await _fetch_ledger_table_counts(verify_session)

    assert counts["portfolio_transaction"] >= 1
    assert counts["dividend_event"] >= 1
    assert counts["corporate_action_event"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_autobegin_session_isolated_from_caller_transaction_state(
    test_db_session: AsyncSession,
    test_db_engine: AsyncEngine,
) -> None:
    """Rebuild should avoid mutating caller autobegin state and still persist writes."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_persisted_canonical_input(test_db_session)

    # Trigger SQLAlchemy autobegin before rebuild to mirror common pre-check usage.
    await test_db_session.execute(select(func.count()).select_from(table("source_document")))
    assert test_db_session.in_transaction()

    await rebuild(source_document_id=source_document_id, db=test_db_session)
    assert test_db_session.in_transaction()

    verify_session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with verify_session_factory() as verify_session:
        counts = await _fetch_ledger_table_counts(verify_session)

    assert counts["portfolio_transaction"] >= 1
    assert counts["dividend_event"] >= 1
    assert counts["corporate_action_event"] >= 1
    await test_db_session.rollback()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_fractional_buy_sell_keeps_basis_cent_consistent(
    test_db_session: AsyncSession,
) -> None:
    """Fractional buy/sell rebuild should avoid basis drift from unit rounding."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_fractional_buy_sell_input(test_db_session)

    await rebuild(source_document_id=source_document_id, db=test_db_session)

    lot_result = await test_db_session.execute(
        select(Lot)
        .join(
            PortfolioTransaction,
            Lot.opening_transaction_id == PortfolioTransaction.id,
        )
        .where(PortfolioTransaction.source_document_id == source_document_id),
    )
    lot_rows = list(lot_result.scalars().all())
    assert len(lot_rows) == 1
    lot_row = lot_rows[0]

    disposition_result = await test_db_session.execute(
        select(LotDisposition).where(LotDisposition.lot_id == lot_row.id),
    )
    disposition_rows = list(disposition_result.scalars().all())
    assert len(disposition_rows) == 1
    disposition_row = disposition_rows[0]

    assert lot_row.unit_cost_basis_usd == Decimal("33.333333333")
    assert lot_row.total_cost_basis_usd == Decimal("33.33")
    assert disposition_row.matched_cost_basis_usd == Decimal("66.67")
    assert disposition_row.matched_cost_basis_usd + lot_row.total_cost_basis_usd == Decimal(
        "100.00"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_fractional_three_partial_sells_preserves_basis_and_open_lot_count(
    test_db_session: AsyncSession,
) -> None:
    """Three partial sells should keep cent-accurate basis and report zero open lots."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_fractional_buy_three_partial_sells_input(test_db_session)

    rebuild_result = await rebuild(source_document_id=source_document_id, db=test_db_session)
    assert rebuild_result["open_lots"] == 0

    lot_result = await test_db_session.execute(
        select(Lot)
        .join(
            PortfolioTransaction,
            Lot.opening_transaction_id == PortfolioTransaction.id,
        )
        .where(PortfolioTransaction.source_document_id == source_document_id),
    )
    lot_rows = list(lot_result.scalars().all())
    assert len(lot_rows) == 1
    lot_row = lot_rows[0]
    assert lot_row.remaining_qty == Decimal("0.000000000")
    assert lot_row.total_cost_basis_usd == Decimal("0.00")

    disposition_basis_result = await test_db_session.execute(
        select(LotDisposition.matched_cost_basis_usd)
        .join(
            PortfolioTransaction,
            LotDisposition.sell_transaction_id == PortfolioTransaction.id,
        )
        .where(LotDisposition.lot_id == lot_row.id)
        .order_by(PortfolioTransaction.event_date.asc(), PortfolioTransaction.id.asc()),
    )
    matched_basis_values = list(disposition_basis_result.scalars().all())
    assert matched_basis_values == [
        Decimal("33.33"),
        Decimal("33.33"),
        Decimal("33.34"),
    ]
    assert sum(matched_basis_values, start=Decimal("0")) == Decimal("100.00")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebuild_same_day_split_before_sell_uses_canonical_event_order(
    test_db_session: AsyncSession,
) -> None:
    """Same-day split should be applied before sell when canonical order requires it."""

    rebuild = _load_rebuild_callable(
        "rebuild_portfolio_ledger_from_canonical_records",
        task_hint="3.3",
    )
    await _truncate_tables_if_present(test_db_session)
    source_document_id = await _seed_same_day_split_before_sell_input(test_db_session)

    rebuild_result = await rebuild(source_document_id=source_document_id, db=test_db_session)
    assert rebuild_result["open_lots"] == 0
    assert rebuild_result["lot_dispositions"] == 1

    lot_result = await test_db_session.execute(
        select(Lot)
        .join(
            PortfolioTransaction,
            Lot.opening_transaction_id == PortfolioTransaction.id,
        )
        .where(PortfolioTransaction.source_document_id == source_document_id),
    )
    lot_rows = list(lot_result.scalars().all())
    assert len(lot_rows) == 1
    lot_row = lot_rows[0]
    assert lot_row.remaining_qty == Decimal("0.000000000")
    assert lot_row.total_cost_basis_usd == Decimal("0.00")

    disposition_result = await test_db_session.execute(
        select(LotDisposition).where(LotDisposition.lot_id == lot_row.id),
    )
    disposition_rows = list(disposition_result.scalars().all())
    assert len(disposition_rows) == 1
    disposition_row = disposition_rows[0]
    assert disposition_row.matched_qty == Decimal("2.000000000")
    assert disposition_row.matched_cost_basis_usd == Decimal("100.00")
