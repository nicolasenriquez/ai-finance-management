"""Integration tests for market-data write safety and migration-backed behavior."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest
from sqlalchemy import func, select, table, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.market_data.models import PriceHistory
from app.market_data.schemas import MarketDataPriceWrite, MarketDataSnapshotWriteRequest
from app.market_data.service import MarketDataClientError, ingest_market_data_snapshot
from app.pdf_persistence.models import CanonicalPdfRecord, ImportJob, SourceDocument
from app.portfolio_ledger.models import (
    CorporateActionEvent,
    DividendEvent,
    Lot,
    LotDisposition,
    PortfolioTransaction,
)

_TRUNCATE_CANDIDATES: tuple[str, ...] = (
    "price_history",
    "market_data_snapshot",
    "lot_disposition",
    "lot",
    "corporate_action_event",
    "dividend_event",
    "portfolio_transaction",
    "canonical_pdf_record",
    "import_job",
    "source_document",
)
_LEDGER_TRUTH_TABLES: tuple[str, ...] = (
    "canonical_pdf_record",
    "portfolio_transaction",
    "dividend_event",
    "corporate_action_event",
    "lot",
    "lot_disposition",
)


async def _table_exists(db: AsyncSession, table_name: str) -> bool:
    """Return whether one table exists in public schema."""

    result = await db.execute(
        text("SELECT to_regclass(:regclass_name)"),
        {"regclass_name": f"public.{table_name}"},
    )
    return result.scalar_one() is not None


async def _truncate_tables_if_present(db: AsyncSession) -> None:
    """Truncate integration tables when they exist in the current schema."""

    existing_tables = [
        table_name for table_name in _TRUNCATE_CANDIDATES if await _table_exists(db, table_name)
    ]
    if not existing_tables:
        return

    truncate_sql = f"TRUNCATE TABLE {', '.join(existing_tables)} RESTART IDENTITY CASCADE"
    await db.execute(text(truncate_sql))
    await db.commit()


async def _seed_ledger_truth(db: AsyncSession) -> None:
    """Insert one deterministic canonical+ledger truth graph for safety assertions."""

    source_document = SourceDocument(
        sha256="2fb6150427f43fc14db2380de0f6dc3361804580a2fbd8fca6794f4f29e19e17",
        storage_key="integration-seed/market-data-safety.pdf",
        original_filename="market_data_safety.pdf",
        content_type="application/pdf",
        file_size_bytes=2048,
        page_count=2,
    )
    db.add(source_document)
    await db.flush()

    import_job = ImportJob(
        source_document_id=source_document.id,
        storage_key=source_document.storage_key,
        normalized_records=4,
        inserted_records=4,
        duplicate_records=0,
    )
    db.add(import_job)
    await db.flush()

    canonical_buy = CanonicalPdfRecord(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        event_type="trade",
        event_date=date(2026, 1, 10),
        instrument_symbol="VOO",
        trade_side="buy",
        fingerprint="market-data-ledger-buy",
        fingerprint_version="v1",
        canonical_schema_version="dataset_1_v1",
        canonical_payload={"event_type": "trade", "trade_side": "buy"},
        raw_values={},
        provenance={"table_name": "compra_venta_activos", "row_index": 1, "source_page": 1},
    )
    canonical_sell = CanonicalPdfRecord(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        event_type="trade",
        event_date=date(2026, 1, 20),
        instrument_symbol="VOO",
        trade_side="sell",
        fingerprint="market-data-ledger-sell",
        fingerprint_version="v1",
        canonical_schema_version="dataset_1_v1",
        canonical_payload={"event_type": "trade", "trade_side": "sell"},
        raw_values={},
        provenance={"table_name": "compra_venta_activos", "row_index": 2, "source_page": 1},
    )
    canonical_dividend = CanonicalPdfRecord(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        event_type="dividend",
        event_date=date(2026, 1, 25),
        instrument_symbol="VOO",
        trade_side=None,
        fingerprint="market-data-ledger-dividend",
        fingerprint_version="v1",
        canonical_schema_version="dataset_1_v1",
        canonical_payload={"event_type": "dividend"},
        raw_values={},
        provenance={"table_name": "dividendos_recibidos", "row_index": 1, "source_page": 2},
    )
    canonical_split = CanonicalPdfRecord(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        event_type="split",
        event_date=date(2026, 2, 1),
        instrument_symbol="VOO",
        trade_side=None,
        fingerprint="market-data-ledger-split",
        fingerprint_version="v1",
        canonical_schema_version="dataset_1_v1",
        canonical_payload={"event_type": "split"},
        raw_values={},
        provenance={"table_name": "splits", "row_index": 1, "source_page": 2},
    )
    db.add_all([canonical_buy, canonical_sell, canonical_dividend, canonical_split])
    await db.flush()

    buy_tx = PortfolioTransaction(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        canonical_record_id=canonical_buy.id,
        canonical_fingerprint=canonical_buy.fingerprint,
        event_date=canonical_buy.event_date,
        instrument_symbol="VOO",
        trade_side="buy",
        quantity=Decimal("2.000000000"),
        gross_amount_usd=Decimal("800.00"),
        accounting_policy_version="dataset_1_v1",
        canonical_payload={"event_type": "trade", "trade_side": "buy"},
    )
    sell_tx = PortfolioTransaction(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        canonical_record_id=canonical_sell.id,
        canonical_fingerprint=canonical_sell.fingerprint,
        event_date=canonical_sell.event_date,
        instrument_symbol="VOO",
        trade_side="sell",
        quantity=Decimal("1.000000000"),
        gross_amount_usd=Decimal("430.00"),
        accounting_policy_version="dataset_1_v1",
        canonical_payload={"event_type": "trade", "trade_side": "sell"},
    )
    dividend_event = DividendEvent(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        canonical_record_id=canonical_dividend.id,
        canonical_fingerprint=canonical_dividend.fingerprint,
        event_date=canonical_dividend.event_date,
        instrument_symbol="VOO",
        gross_amount_usd=Decimal("2.30"),
        taxes_withheld_usd=Decimal("0.10"),
        net_amount_usd=Decimal("2.20"),
        accounting_policy_version="dataset_1_v1",
        canonical_payload={"event_type": "dividend"},
    )
    corporate_action_event = CorporateActionEvent(
        source_document_id=source_document.id,
        import_job_id=import_job.id,
        canonical_record_id=canonical_split.id,
        canonical_fingerprint=canonical_split.fingerprint,
        event_date=canonical_split.event_date,
        instrument_symbol="VOO",
        action_type="split",
        shares_before_qty=Decimal("1.000000000"),
        shares_after_qty=Decimal("2.000000000"),
        split_ratio_value=Decimal("2.000000000"),
        accounting_policy_version="dataset_1_v1",
        canonical_payload={"event_type": "split"},
    )
    db.add_all([buy_tx, sell_tx, dividend_event, corporate_action_event])
    await db.flush()

    lot = Lot(
        opening_transaction_id=buy_tx.id,
        last_corporate_action_event_id=corporate_action_event.id,
        instrument_symbol="VOO",
        opened_on=date(2026, 1, 10),
        original_qty=Decimal("2.000000000"),
        remaining_qty=Decimal("1.000000000"),
        total_cost_basis_usd=Decimal("400.00"),
        unit_cost_basis_usd=Decimal("400.000000000"),
        accounting_policy_version="dataset_1_v1",
    )
    db.add(lot)
    await db.flush()

    lot_disposition = LotDisposition(
        lot_id=lot.id,
        sell_transaction_id=sell_tx.id,
        disposition_date=date(2026, 1, 20),
        matched_qty=Decimal("1.000000000"),
        matched_cost_basis_usd=Decimal("400.00"),
        accounting_policy_version="dataset_1_v1",
    )
    db.add(lot_disposition)
    await db.commit()


async def _fetch_table_count(db: AsyncSession, table_name: str) -> int:
    """Return row count for one table."""

    query = select(func.count()).select_from(table(table_name))
    result = await db.execute(query)
    return result.scalar_one()


async def _fetch_truth_counts(db: AsyncSession) -> dict[str, int]:
    """Return current row counts for canonical+ledger truth tables."""

    return {
        table_name: await _fetch_table_count(db, table_name) for table_name in _LEDGER_TRUTH_TABLES
    }


def _build_valid_request(*, price: str = "510.123456789") -> MarketDataSnapshotWriteRequest:
    """Return a valid market-data snapshot request used across integration tests."""

    return MarketDataSnapshotWriteRequest(
        source_type="quote_feed",
        source_provider="provider_a",
        snapshot_key="snapshot-2026-03-24T10:00Z",
        snapshot_captured_at=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
        prices=[
            MarketDataPriceWrite(
                instrument_symbol="VOO",
                market_timestamp=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
                price_value=Decimal(price),
                currency_code="USD",
                source_payload={"raw": price},
            )
        ],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingest_is_idempotent_for_same_snapshot_symbol_and_time_key(
    test_db_session: AsyncSession,
) -> None:
    """Repeated ingestion of one deterministic key must not create duplicate rows."""

    await _truncate_tables_if_present(test_db_session)

    first = await ingest_market_data_snapshot(
        db=test_db_session,
        request=_build_valid_request(price="510.123456789"),
    )
    second = await ingest_market_data_snapshot(
        db=test_db_session,
        request=_build_valid_request(price="511.000000000"),
    )

    price_rows_result = await test_db_session.execute(select(PriceHistory))
    price_rows = price_rows_result.scalars().all()

    assert first.inserted_prices == 1
    assert first.updated_prices == 0
    assert second.inserted_prices == 0
    assert second.updated_prices == 1
    assert len(price_rows) == 1
    assert price_rows[0].price_value == Decimal("511.000000000")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingest_concurrent_duplicate_requests_are_duplicate_safe(
    test_db_engine: AsyncEngine,
) -> None:
    """Concurrent duplicate ingests should not fail or duplicate persisted rows."""

    session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as setup_session:
        await _truncate_tables_if_present(setup_session)

    request = _build_valid_request(price="510.123456789")

    async def ingest_once() -> None:
        async with session_factory() as db_session:
            await ingest_market_data_snapshot(db=db_session, request=request)

    await asyncio.wait_for(
        asyncio.gather(*[ingest_once() for _ in range(8)]),
        timeout=180.0,
    )

    async with session_factory() as verify_session:
        snapshot_count = await _fetch_table_count(verify_session, "market_data_snapshot")
        price_count = await _fetch_table_count(verify_session, "price_history")
        rows_result = await verify_session.execute(select(PriceHistory))
        rows = rows_result.scalars().all()

    assert snapshot_count == 1
    assert price_count == 1
    assert len(rows) == 1
    assert rows[0].price_value == Decimal("510.123456789")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_refresh_success_does_not_mutate_ledger_truth(
    test_db_session: AsyncSession,
) -> None:
    """Successful market-data refresh must not mutate canonical/ledger truth tables."""

    await _truncate_tables_if_present(test_db_session)
    await _seed_ledger_truth(test_db_session)
    before_counts = await _fetch_truth_counts(test_db_session)
    await test_db_session.rollback()

    await ingest_market_data_snapshot(
        db=test_db_session,
        request=_build_valid_request(),
    )
    after_counts = await _fetch_truth_counts(test_db_session)

    assert before_counts == after_counts


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_refresh_failure_does_not_mutate_ledger_truth(
    test_db_session: AsyncSession,
) -> None:
    """Rejected market-data refresh must not mutate canonical/ledger truth tables."""

    await _truncate_tables_if_present(test_db_session)
    await _seed_ledger_truth(test_db_session)
    before_counts = await _fetch_truth_counts(test_db_session)

    with pytest.raises(MarketDataClientError, match="dataset_1-supported"):
        await ingest_market_data_snapshot(
            db=test_db_session,
            request=MarketDataSnapshotWriteRequest(
                source_type="quote_feed",
                source_provider="provider_a",
                snapshot_key="snapshot-invalid-symbol",
                snapshot_captured_at=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
                prices=[
                    MarketDataPriceWrite(
                        instrument_symbol="MSFT",
                        market_timestamp=datetime(2026, 3, 24, 10, 0, tzinfo=UTC),
                        price_value=Decimal("400.000000000"),
                        currency_code="USD",
                    )
                ],
            ),
        )
    after_counts = await _fetch_truth_counts(test_db_session)

    assert before_counts == after_counts


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_migration_schema_contract_is_present(
    test_db_session: AsyncSession,
) -> None:
    """Migration must expose expected market-data tables, constraints, and indexes."""

    required_relations = (
        "public.market_data_snapshot",
        "public.price_history",
        "public.ix_market_data_snapshot_source_type",
        "public.ix_market_data_snapshot_source_provider",
        "public.ix_market_data_snapshot_snapshot_captured_at",
        "public.ix_price_history_snapshot_id",
        "public.ix_price_history_instrument_symbol",
        "public.ix_price_history_market_timestamp",
        "public.ix_price_history_trading_date",
        "public.uq_price_history_snapshot_symbol_market_timestamp",
        "public.uq_price_history_snapshot_symbol_trading_date",
    )

    for relation_name in required_relations:
        result = await test_db_session.execute(
            text("SELECT to_regclass(:regclass_name)"),
            {"regclass_name": relation_name},
        )
        assert result.scalar_one() is not None

    constraint_names_result = await test_db_session.execute(text("""
            SELECT conname
            FROM pg_constraint
            WHERE conname IN (
                'uq_market_data_snapshot_source_identity_key',
                'ck_price_history_exactly_one_time_key'
            )
            ORDER BY conname
            """))
    constraint_names = [cast(str, row[0]) for row in constraint_names_result.all()]
    assert constraint_names == [
        "ck_price_history_exactly_one_time_key",
        "uq_market_data_snapshot_source_identity_key",
    ]
