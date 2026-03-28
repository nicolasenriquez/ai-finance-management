"""Fail-first route and integration tests for portfolio analytics APIs."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator, Mapping
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from types import ModuleType
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import app.market_data.service as market_data_service
import app.pdf_extraction.service as pdf_extraction_service
import app.pdf_normalization.service as pdf_normalization_service
import app.pdf_persistence.service as pdf_persistence_service
import app.portfolio_ledger.service as portfolio_ledger_service
from app.main import app
from app.market_data.models import MarketDataSnapshot, PriceHistory
from app.pdf_persistence.models import CanonicalPdfRecord, ImportJob, SourceDocument
from app.portfolio_ledger.models import DividendEvent, Lot, LotDisposition, PortfolioTransaction

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
_REQUIRED_INTEGRATION_TABLES: tuple[str, ...] = (
    "market_data_snapshot",
    "price_history",
    "source_document",
    "import_job",
    "canonical_pdf_record",
    "portfolio_transaction",
    "dividend_event",
    "corporate_action_event",
    "lot",
    "lot_disposition",
)


def _load_portfolio_analytics_routes_module() -> ModuleType:
    """Load portfolio analytics routes module in fail-first mode."""

    try:
        return import_module("app.portfolio_analytics.routes")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_analytics.routes. "
            "Implement tasks 2.1-3.2 before portfolio analytics route tests can pass.",
        )
        raise AssertionError from exc


def _portfolio_summary_endpoint_path() -> str:
    """Return summary endpoint path and fail if route is not registered."""

    module = _load_portfolio_analytics_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_analytics.routes.settings is missing. "
            "Task 3.1 should expose configured route settings.",
        )

    path = f"{settings.api_prefix}/portfolio/summary"
    registered_paths = {
        route_path
        for route in app.routes
        for route_path in [getattr(route, "path", None)]
        if isinstance(route_path, str)
    }
    if path not in registered_paths:
        pytest.fail(
            f"Fail-first baseline: portfolio analytics route {path} is not registered in app.main. "
            "Implement tasks 3.1-3.2 before this test can pass.",
        )
    return path


def _portfolio_lot_detail_route_template() -> str:
    """Return lot-detail route template and fail if route is not registered."""

    module = _load_portfolio_analytics_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_analytics.routes.settings is missing. "
            "Task 3.1 should expose configured route settings.",
        )

    path_template = f"{settings.api_prefix}/portfolio/lots/{{instrument_symbol}}"
    registered_paths = {
        route_path
        for route in app.routes
        for route_path in [getattr(route, "path", None)]
        if isinstance(route_path, str)
    }
    if path_template not in registered_paths:
        pytest.fail(
            "Fail-first baseline: portfolio lot-detail route template "
            f"{path_template} is not registered in app.main. "
            "Implement tasks 3.1-3.2 before this test can pass.",
        )
    return path_template


def _portfolio_workspace_endpoint_path(*, suffix: str) -> str:
    """Return one workspace endpoint path under configured API prefix."""

    module = _load_portfolio_analytics_routes_module()
    settings = getattr(module, "settings", None)
    if settings is None:
        pytest.fail(
            "Fail-first baseline: app.portfolio_analytics.routes.settings is missing. "
            "Task 3.1 should expose configured route settings.",
        )

    path = f"{settings.api_prefix}/portfolio/{suffix}"
    registered_paths = {
        route_path
        for route in app.routes
        for route_path in [getattr(route, "path", None)]
        if isinstance(route_path, str)
    }
    if path not in registered_paths:
        pytest.fail(
            f"Fail-first baseline: portfolio route {path} is not registered in app.main. "
            "Implement backend workspace tasks before this test can pass.",
        )
    return path


def _assert_decimal_field(row: Mapping[str, object], field: str, expected: str) -> None:
    """Assert one numeric response field using stable Decimal comparison."""

    if field not in row:
        pytest.fail(f"Response row is missing field '{field}'.")
    assert Decimal(str(row[field])) == Decimal(expected)


def _assert_int_field(row: Mapping[str, object], field: str, expected: int) -> None:
    """Assert one integer response field without unsafe object casts."""

    if field not in row:
        pytest.fail(f"Response row is missing field '{field}'.")
    actual = row[field]
    if not isinstance(actual, int):
        pytest.fail(f"Response row field '{field}' must be an integer.")
    assert actual == expected


def _patch_forbidden_upstream_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail immediately if analytics routes invoke PDF/rebuild side effects."""

    def _forbidden_call(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(
            "Portfolio analytics routes must not invoke PDF extraction/normalization/"
            "persistence flows or ledger rebuild side effects.",
        )

    monkeypatch.setattr(pdf_extraction_service, "extract_pdf_from_storage", _forbidden_call)
    monkeypatch.setattr(pdf_normalization_service, "normalize_pdf_from_storage", _forbidden_call)
    monkeypatch.setattr(pdf_persistence_service, "persist_pdf_from_storage", _forbidden_call)
    monkeypatch.setattr(
        market_data_service,
        "refresh_yfinance_supported_universe",
        _forbidden_call,
    )
    monkeypatch.setattr(
        portfolio_ledger_service,
        "rebuild_portfolio_ledger_from_canonical_records",
        _forbidden_call,
    )


async def _table_exists(session: AsyncSession, table_name: str) -> bool:
    """Return whether one table exists in the current test database."""

    result = await session.execute(
        text("SELECT to_regclass(:regclass_name)"),
        {"regclass_name": f"public.{table_name}"},
    )
    return result.scalar_one() is not None


async def _truncate_tables_if_present(session: AsyncSession) -> None:
    """Truncate integration tables to keep route tests deterministic."""

    existing_tables = [
        table_name
        for table_name in _TRUNCATE_CANDIDATES
        if await _table_exists(session, table_name)
    ]
    if not existing_tables:
        return

    truncate_sql = f"TRUNCATE TABLE {', '.join(existing_tables)} RESTART IDENTITY CASCADE"
    await session.execute(text(truncate_sql))
    await session.commit()


async def _seed_persisted_ledger_state(
    engine: AsyncEngine,
    *,
    include_market_data: bool = True,
    price_history_points: int = 1,
) -> None:
    """Insert deterministic persisted ledger rows used by analytics integration tests."""

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        missing_tables = [
            table_name
            for table_name in _REQUIRED_INTEGRATION_TABLES
            if not await _table_exists(session, table_name)
        ]
        if missing_tables:
            missing_tables_csv = ", ".join(missing_tables)
            pytest.fail(
                "Portfolio analytics route integration tests require migrated tables. "
                f"Missing tables: {missing_tables_csv}. "
                "Run 'uv run alembic stamp base && uv run alembic upgrade head'."
            )

        await _truncate_tables_if_present(session)

        source_document = SourceDocument(
            sha256="c9e4f0e913b8fd7307e8a6d032d465ee328e9a18adf83e89f0ff1856209f8d78",
            storage_key="integration-seed/portfolio-analytics.pdf",
            original_filename="portfolio_analytics_seed.pdf",
            content_type="application/pdf",
            file_size_bytes=1024,
            page_count=1,
        )
        session.add(source_document)
        await session.flush()

        import_job = ImportJob(
            source_document_id=source_document.id,
            storage_key=source_document.storage_key,
            normalized_records=5,
            inserted_records=5,
            duplicate_records=0,
        )
        session.add(import_job)
        await session.flush()

        canonical_records: dict[str, CanonicalPdfRecord] = {
            "voo_buy_1": CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type="trade",
                event_date=date(2025, 1, 10),
                instrument_symbol="VOO",
                trade_side="buy",
                fingerprint="analytics-voo-buy-1",
                fingerprint_version="v1",
                canonical_schema_version="dataset_1_v1",
                canonical_payload={
                    "event_type": "trade",
                    "trade_side": "buy",
                    "trade_date": "2025-01-10",
                    "instrument_symbol": "VOO",
                    "aporte_usd": "200.00",
                    "acciones_compradas_qty": "2.000000000",
                    "rescate_usd": None,
                    "acciones_vendidas_qty": None,
                },
                raw_values={},
                provenance={},
            ),
            "voo_buy_2": CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type="trade",
                event_date=date(2025, 1, 12),
                instrument_symbol="VOO",
                trade_side="buy",
                fingerprint="analytics-voo-buy-2",
                fingerprint_version="v1",
                canonical_schema_version="dataset_1_v1",
                canonical_payload={
                    "event_type": "trade",
                    "trade_side": "buy",
                    "trade_date": "2025-01-12",
                    "instrument_symbol": "VOO",
                    "aporte_usd": "120.00",
                    "acciones_compradas_qty": "1.000000000",
                    "rescate_usd": None,
                    "acciones_vendidas_qty": None,
                },
                raw_values={},
                provenance={},
            ),
            "voo_sell_1": CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type="trade",
                event_date=date(2025, 2, 1),
                instrument_symbol="VOO",
                trade_side="sell",
                fingerprint="analytics-voo-sell-1",
                fingerprint_version="v1",
                canonical_schema_version="dataset_1_v1",
                canonical_payload={
                    "event_type": "trade",
                    "trade_side": "sell",
                    "trade_date": "2025-02-01",
                    "instrument_symbol": "VOO",
                    "aporte_usd": None,
                    "acciones_compradas_qty": None,
                    "rescate_usd": "210.00",
                    "acciones_vendidas_qty": "1.500000000",
                },
                raw_values={},
                provenance={},
            ),
            "voo_dividend_1": CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type="dividend",
                event_date=date(2025, 2, 20),
                instrument_symbol="VOO",
                trade_side=None,
                fingerprint="analytics-voo-dividend-1",
                fingerprint_version="v1",
                canonical_schema_version="dataset_1_v1",
                canonical_payload={
                    "event_type": "dividend",
                    "dividend_date": "2025-02-20",
                    "instrument_symbol": "VOO",
                    "gross_usd": "7.00",
                    "taxes_usd": "1.00",
                    "net_usd": "6.00",
                },
                raw_values={},
                provenance={},
            ),
            "aapl_buy_1": CanonicalPdfRecord(
                source_document_id=source_document.id,
                import_job_id=import_job.id,
                event_type="trade",
                event_date=date(2025, 1, 14),
                instrument_symbol="AAPL",
                trade_side="buy",
                fingerprint="analytics-aapl-buy-1",
                fingerprint_version="v1",
                canonical_schema_version="dataset_1_v1",
                canonical_payload={
                    "event_type": "trade",
                    "trade_side": "buy",
                    "trade_date": "2025-01-14",
                    "instrument_symbol": "AAPL",
                    "aporte_usd": "450.00",
                    "acciones_compradas_qty": "3.000000000",
                    "rescate_usd": None,
                    "acciones_vendidas_qty": None,
                },
                raw_values={},
                provenance={},
            ),
        }

        session.add_all(canonical_records.values())
        await session.flush()

        voo_buy_tx_1 = PortfolioTransaction(
            source_document_id=source_document.id,
            import_job_id=import_job.id,
            canonical_record_id=canonical_records["voo_buy_1"].id,
            canonical_fingerprint=canonical_records["voo_buy_1"].fingerprint,
            event_date=date(2025, 1, 10),
            instrument_symbol="VOO",
            trade_side="buy",
            quantity=Decimal("2.000000000"),
            gross_amount_usd=Decimal("200.00"),
            accounting_policy_version="dataset_1_v1",
            canonical_payload=canonical_records["voo_buy_1"].canonical_payload,
        )
        voo_buy_tx_2 = PortfolioTransaction(
            source_document_id=source_document.id,
            import_job_id=import_job.id,
            canonical_record_id=canonical_records["voo_buy_2"].id,
            canonical_fingerprint=canonical_records["voo_buy_2"].fingerprint,
            event_date=date(2025, 1, 12),
            instrument_symbol="VOO",
            trade_side="buy",
            quantity=Decimal("1.000000000"),
            gross_amount_usd=Decimal("120.00"),
            accounting_policy_version="dataset_1_v1",
            canonical_payload=canonical_records["voo_buy_2"].canonical_payload,
        )
        voo_sell_tx_1 = PortfolioTransaction(
            source_document_id=source_document.id,
            import_job_id=import_job.id,
            canonical_record_id=canonical_records["voo_sell_1"].id,
            canonical_fingerprint=canonical_records["voo_sell_1"].fingerprint,
            event_date=date(2025, 2, 1),
            instrument_symbol="VOO",
            trade_side="sell",
            quantity=Decimal("1.500000000"),
            gross_amount_usd=Decimal("210.00"),
            accounting_policy_version="dataset_1_v1",
            canonical_payload=canonical_records["voo_sell_1"].canonical_payload,
        )
        aapl_buy_tx_1 = PortfolioTransaction(
            source_document_id=source_document.id,
            import_job_id=import_job.id,
            canonical_record_id=canonical_records["aapl_buy_1"].id,
            canonical_fingerprint=canonical_records["aapl_buy_1"].fingerprint,
            event_date=date(2025, 1, 14),
            instrument_symbol="AAPL",
            trade_side="buy",
            quantity=Decimal("3.000000000"),
            gross_amount_usd=Decimal("450.00"),
            accounting_policy_version="dataset_1_v1",
            canonical_payload=canonical_records["aapl_buy_1"].canonical_payload,
        )
        session.add_all((voo_buy_tx_1, voo_buy_tx_2, voo_sell_tx_1, aapl_buy_tx_1))
        await session.flush()

        lot_voo_1 = Lot(
            opening_transaction_id=voo_buy_tx_1.id,
            last_corporate_action_event_id=None,
            instrument_symbol="VOO",
            opened_on=date(2025, 1, 10),
            original_qty=Decimal("2.000000000"),
            remaining_qty=Decimal("1.000000000"),
            total_cost_basis_usd=Decimal("100.00"),
            unit_cost_basis_usd=Decimal("50.000000000"),
            accounting_policy_version="dataset_1_v1",
        )
        lot_voo_2 = Lot(
            opening_transaction_id=voo_buy_tx_2.id,
            last_corporate_action_event_id=None,
            instrument_symbol="VOO",
            opened_on=date(2025, 1, 12),
            original_qty=Decimal("1.000000000"),
            remaining_qty=Decimal("0.500000000"),
            total_cost_basis_usd=Decimal("60.00"),
            unit_cost_basis_usd=Decimal("120.000000000"),
            accounting_policy_version="dataset_1_v1",
        )
        lot_aapl_1 = Lot(
            opening_transaction_id=aapl_buy_tx_1.id,
            last_corporate_action_event_id=None,
            instrument_symbol="AAPL",
            opened_on=date(2025, 1, 14),
            original_qty=Decimal("3.000000000"),
            remaining_qty=Decimal("3.000000000"),
            total_cost_basis_usd=Decimal("450.00"),
            unit_cost_basis_usd=Decimal("150.000000000"),
            accounting_policy_version="dataset_1_v1",
        )
        session.add_all((lot_voo_1, lot_voo_2, lot_aapl_1))
        await session.flush()

        session.add_all(
            (
                LotDisposition(
                    lot_id=lot_voo_1.id,
                    sell_transaction_id=voo_sell_tx_1.id,
                    disposition_date=date(2025, 2, 1),
                    matched_qty=Decimal("1.000000000"),
                    matched_cost_basis_usd=Decimal("50.00"),
                    accounting_policy_version="dataset_1_v1",
                ),
                LotDisposition(
                    lot_id=lot_voo_2.id,
                    sell_transaction_id=voo_sell_tx_1.id,
                    disposition_date=date(2025, 2, 1),
                    matched_qty=Decimal("0.500000000"),
                    matched_cost_basis_usd=Decimal("60.00"),
                    accounting_policy_version="dataset_1_v1",
                ),
                DividendEvent(
                    source_document_id=source_document.id,
                    import_job_id=import_job.id,
                    canonical_record_id=canonical_records["voo_dividend_1"].id,
                    canonical_fingerprint=canonical_records["voo_dividend_1"].fingerprint,
                    event_date=date(2025, 2, 20),
                    instrument_symbol="VOO",
                    gross_amount_usd=Decimal("7.00"),
                    taxes_withheld_usd=Decimal("1.00"),
                    net_amount_usd=Decimal("6.00"),
                    accounting_policy_version="dataset_1_v1",
                    canonical_payload=canonical_records["voo_dividend_1"].canonical_payload,
                ),
            )
        )
        if include_market_data:
            if price_history_points < 1:
                pytest.fail("price_history_points must be at least 1 for integration seeding.")
            market_snapshot = MarketDataSnapshot(
                source_type="market_data_provider",
                source_provider="yfinance",
                snapshot_key="yf|d1|1d|3mo|aa1rp1|2025-02-20|s2|testseed000001",
                snapshot_captured_at=datetime(2025, 2, 20, 21, 0, tzinfo=UTC),
                snapshot_metadata={"provider": "yfinance", "seed": "portfolio_analytics_tests"},
            )
            session.add(market_snapshot)
            await session.flush()
            if price_history_points == 1:
                session.add_all(
                    (
                        PriceHistory(
                            snapshot_id=market_snapshot.id,
                            instrument_symbol="AAPL",
                            trading_date=date(2025, 2, 20),
                            price_value=Decimal("190.00"),
                            currency_code="USD",
                            source_payload={"seed": True},
                        ),
                        PriceHistory(
                            snapshot_id=market_snapshot.id,
                            instrument_symbol="VOO",
                            trading_date=date(2025, 2, 20),
                            price_value=Decimal("105.00"),
                            currency_code="USD",
                            source_payload={"seed": True},
                        ),
                    )
                )
            else:
                baseline_trading_date = date(2025, 1, 1)
                generated_rows: list[PriceHistory] = []
                for day_offset in range(price_history_points):
                    trading_day = baseline_trading_date + timedelta(days=day_offset)
                    generated_rows.append(
                        PriceHistory(
                            snapshot_id=market_snapshot.id,
                            instrument_symbol="AAPL",
                            trading_date=trading_day,
                            price_value=Decimal("175.00") + Decimal(day_offset),
                            currency_code="USD",
                            source_payload={"seed": True, "series": "analytics"},
                        )
                    )
                    generated_rows.append(
                        PriceHistory(
                            snapshot_id=market_snapshot.id,
                            instrument_symbol="VOO",
                            trading_date=trading_day,
                            price_value=Decimal("95.00") + (Decimal(day_offset) * Decimal("0.5")),
                            currency_code="USD",
                            source_payload={"seed": True, "series": "analytics"},
                        )
                    )
                session.add_all(generated_rows)

        await session.commit()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Create a test client for route-level API tests."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.integration
def test_summary_endpoint_returns_grouped_rows_with_as_of_ledger_at(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Summary route should expose grouped KPIs from persisted ledger state."""

    summary_path = _portfolio_summary_endpoint_path()
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine))

    response = client.get(summary_path)
    assert response.status_code == 200

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Summary response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)

    as_of_ledger_at = payload.get("as_of_ledger_at")
    assert isinstance(as_of_ledger_at, str)
    assert as_of_ledger_at
    pricing_snapshot_key = payload.get("pricing_snapshot_key")
    assert isinstance(pricing_snapshot_key, str)
    assert pricing_snapshot_key
    pricing_snapshot_captured_at = payload.get("pricing_snapshot_captured_at")
    assert isinstance(pricing_snapshot_captured_at, str)
    assert pricing_snapshot_captured_at

    rows_raw = payload.get("rows")
    if not isinstance(rows_raw, list):
        pytest.fail("Summary response must include a 'rows' list.")
    rows = cast(list[object], rows_raw)

    rows_by_symbol: dict[str, Mapping[str, object]] = {}
    for row_candidate in rows:
        if not isinstance(row_candidate, Mapping):
            pytest.fail("Summary rows must be JSON objects.")
        row = cast(Mapping[str, object], row_candidate)
        symbol = row.get("instrument_symbol")
        if not isinstance(symbol, str):
            pytest.fail("Summary rows must include string instrument_symbol values.")
        rows_by_symbol[symbol] = row

    assert set(rows_by_symbol) == {"AAPL", "VOO"}

    voo_row = rows_by_symbol["VOO"]
    _assert_decimal_field(voo_row, "open_quantity", "1.500000000")
    _assert_decimal_field(voo_row, "open_cost_basis_usd", "160.00")
    _assert_int_field(voo_row, "open_lot_count", 2)
    _assert_decimal_field(voo_row, "realized_proceeds_usd", "210.00")
    _assert_decimal_field(voo_row, "realized_cost_basis_usd", "110.00")
    _assert_decimal_field(voo_row, "realized_gain_usd", "100.00")
    _assert_decimal_field(voo_row, "dividend_gross_usd", "7.00")
    _assert_decimal_field(voo_row, "dividend_taxes_usd", "1.00")
    _assert_decimal_field(voo_row, "dividend_net_usd", "6.00")
    _assert_decimal_field(voo_row, "latest_close_price_usd", "105.00")
    _assert_decimal_field(voo_row, "market_value_usd", "157.50")
    _assert_decimal_field(voo_row, "unrealized_gain_usd", "-2.50")
    _assert_decimal_field(voo_row, "unrealized_gain_pct", "-1.56")

    aapl_row = rows_by_symbol["AAPL"]
    _assert_decimal_field(aapl_row, "open_quantity", "3.000000000")
    _assert_decimal_field(aapl_row, "open_cost_basis_usd", "450.00")
    _assert_int_field(aapl_row, "open_lot_count", 1)
    _assert_decimal_field(aapl_row, "realized_proceeds_usd", "0.00")
    _assert_decimal_field(aapl_row, "realized_cost_basis_usd", "0.00")
    _assert_decimal_field(aapl_row, "realized_gain_usd", "0.00")
    _assert_decimal_field(aapl_row, "dividend_gross_usd", "0.00")
    _assert_decimal_field(aapl_row, "dividend_taxes_usd", "0.00")
    _assert_decimal_field(aapl_row, "dividend_net_usd", "0.00")
    _assert_decimal_field(aapl_row, "latest_close_price_usd", "190.00")
    _assert_decimal_field(aapl_row, "market_value_usd", "570.00")
    _assert_decimal_field(aapl_row, "unrealized_gain_usd", "120.00")
    _assert_decimal_field(aapl_row, "unrealized_gain_pct", "26.67")


@pytest.mark.integration
def test_summary_endpoint_rejects_missing_open_position_price_coverage(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Summary route should fail explicitly when market coverage is incomplete."""

    summary_path = _portfolio_summary_endpoint_path()
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, include_market_data=False))

    response = client.get(summary_path)
    assert response.status_code == 409

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Coverage-failure response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    detail = payload.get("detail")
    if not isinstance(detail, str):
        pytest.fail("Coverage-failure response must include string 'detail'.")
    assert "coverage" in detail.lower()


@pytest.mark.integration
def test_lot_detail_endpoint_normalizes_symbol_and_returns_disposition_history(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Lot-detail route should normalize symbol input and return explainable lots."""

    path_template = _portfolio_lot_detail_route_template()
    normalized_lot_detail_path = path_template.replace("{instrument_symbol}", "%20voo%20")

    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine))

    response = client.get(normalized_lot_detail_path)
    assert response.status_code == 200

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Lot-detail response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)

    as_of_ledger_at = payload.get("as_of_ledger_at")
    assert isinstance(as_of_ledger_at, str)
    assert as_of_ledger_at

    assert payload.get("instrument_symbol") == "VOO"
    lots_raw = payload.get("lots")
    if not isinstance(lots_raw, list):
        pytest.fail("Lot-detail response must include a 'lots' list.")
    lots = cast(list[object], lots_raw)

    total_remaining_qty = Decimal("0")
    has_disposition_history = False
    for lot_candidate in lots:
        if not isinstance(lot_candidate, Mapping):
            pytest.fail("Lot-detail lot rows must be JSON objects.")
        lot = cast(Mapping[str, object], lot_candidate)
        remaining_qty = lot.get("remaining_qty")
        if remaining_qty is None:
            pytest.fail("Lot-detail lot rows must include 'remaining_qty'.")
        total_remaining_qty += Decimal(str(remaining_qty))
        dispositions = lot.get("dispositions")
        if isinstance(dispositions, list) and dispositions:
            has_disposition_history = True

    assert len(lots) == 2
    assert total_remaining_qty == Decimal("1.500000000")
    assert has_disposition_history


@pytest.mark.integration
def test_lot_detail_endpoint_rejects_unknown_symbol_with_explicit_client_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Unknown symbols should return explicit client-facing not-found responses."""

    path_template = _portfolio_lot_detail_route_template()
    unknown_symbol_path = path_template.replace("{instrument_symbol}", "UNKNOWN")

    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine))

    response = client.get(unknown_symbol_path)
    assert response.status_code == 404

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Unknown-symbol response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    detail = payload.get("detail")
    if not isinstance(detail, str):
        pytest.fail("Unknown-symbol response must include string 'detail'.")
    assert "not found" in detail.lower()


@pytest.mark.integration
def test_time_series_endpoint_returns_max_period_points_from_persisted_history(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Time-series route should return deterministic MAX-period points with provenance."""

    time_series_path = _portfolio_workspace_endpoint_path(suffix="time-series")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=35))

    response = client.get(
        time_series_path,
        params={"period": "MAX"},
    )
    assert response.status_code == 200

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Time-series response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    assert payload.get("period") == "MAX"
    assert payload.get("frequency") == "1D"
    assert payload.get("timezone") == "UTC"
    as_of_ledger_at = payload.get("as_of_ledger_at")
    assert isinstance(as_of_ledger_at, str)
    assert as_of_ledger_at

    points_raw = payload.get("points")
    if not isinstance(points_raw, list):
        pytest.fail("Time-series response must include a 'points' list.")
    points = cast(list[object], points_raw)
    assert len(points) == 35

    captured_at_values: list[str] = []
    for point_candidate in points:
        if not isinstance(point_candidate, Mapping):
            pytest.fail("Time-series points must be JSON objects.")
        point = cast(Mapping[str, object], point_candidate)
        captured_at = point.get("captured_at")
        if not isinstance(captured_at, str):
            pytest.fail("Time-series points must include string 'captured_at'.")
        captured_at_values.append(captured_at)
        _assert_decimal_field(
            point, "portfolio_value_usd", str(Decimal(str(point["portfolio_value_usd"])))
        )
        _assert_decimal_field(point, "pnl_usd", str(Decimal(str(point["pnl_usd"]))))

    assert captured_at_values == sorted(captured_at_values)


@pytest.mark.integration
def test_time_series_endpoint_rejects_unsupported_period_with_explicit_detail(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Time-series route should reject unsupported chart periods with explicit detail."""

    time_series_path = _portfolio_workspace_endpoint_path(suffix="time-series")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=35))

    response = client.get(
        time_series_path,
        params={"period": "45D"},
    )
    assert response.status_code == 422
    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Unsupported-period response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    detail = payload.get("detail")
    if not isinstance(detail, str):
        pytest.fail("Unsupported-period response must include string 'detail'.")
    assert "supported periods" in detail.lower()


@pytest.mark.integration
def test_contribution_endpoint_returns_symbol_breakdown_for_max_period(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Contribution route should return per-symbol deterministic rows for MAX period."""

    contribution_path = _portfolio_workspace_endpoint_path(suffix="contribution")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=35))

    response = client.get(
        contribution_path,
        params={"period": "MAX"},
    )
    assert response.status_code == 200

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Contribution response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    assert payload.get("period") == "MAX"
    as_of_ledger_at = payload.get("as_of_ledger_at")
    assert isinstance(as_of_ledger_at, str)
    assert as_of_ledger_at

    rows_raw = payload.get("rows")
    if not isinstance(rows_raw, list):
        pytest.fail("Contribution response must include a 'rows' list.")
    rows = cast(list[object], rows_raw)
    assert len(rows) == 2

    symbols: set[str] = set()
    for row_candidate in rows:
        if not isinstance(row_candidate, Mapping):
            pytest.fail("Contribution rows must be JSON objects.")
        row = cast(Mapping[str, object], row_candidate)
        symbol = row.get("instrument_symbol")
        if not isinstance(symbol, str):
            pytest.fail("Contribution row instrument_symbol must be a string.")
        symbols.add(symbol)
        _assert_decimal_field(
            row,
            "contribution_pnl_usd",
            str(Decimal(str(row["contribution_pnl_usd"]))),
        )
        _assert_decimal_field(
            row,
            "contribution_pct",
            str(Decimal(str(row["contribution_pct"]))),
        )

    assert symbols == {"AAPL", "VOO"}


@pytest.mark.integration
def test_contribution_endpoint_normalizes_lowercase_period_values(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Contribution route should normalize supported period values before computation."""

    contribution_path = _portfolio_workspace_endpoint_path(suffix="contribution")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=35))

    response = client.get(
        contribution_path,
        params={"period": "max"},
    )
    assert response.status_code == 200
    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Contribution response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    assert payload.get("period") == "MAX"


@pytest.mark.integration
def test_contribution_endpoint_rejects_insufficient_history_for_requested_period(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Contribution route should fail explicitly when requested period coverage is missing."""

    contribution_path = _portfolio_workspace_endpoint_path(suffix="contribution")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=10))

    response = client.get(
        contribution_path,
        params={"period": "30D"},
    )
    assert response.status_code == 409
    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Contribution insufficiency response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    detail = payload.get("detail")
    if not isinstance(detail, str):
        pytest.fail("Contribution insufficiency response must include string 'detail'.")
    assert "insufficient persisted history" in detail.lower()


@pytest.mark.integration
def test_risk_estimators_endpoint_returns_metrics_for_supported_window(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Risk-estimators route should return metadata-complete metrics for valid windows."""

    risk_path = _portfolio_workspace_endpoint_path(suffix="risk-estimators")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=35))

    response = client.get(
        risk_path,
        params={"window_days": 30},
    )
    assert response.status_code == 200

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Risk-estimators response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    assert payload.get("window_days") == 30
    as_of_ledger_at = payload.get("as_of_ledger_at")
    assert isinstance(as_of_ledger_at, str)
    assert as_of_ledger_at

    metrics_raw = payload.get("metrics")
    if not isinstance(metrics_raw, list):
        pytest.fail("Risk-estimators response must include a 'metrics' list.")
    metrics = cast(list[object], metrics_raw)
    assert len(metrics) == 3

    metric_ids: set[str] = set()
    for metric_candidate in metrics:
        if not isinstance(metric_candidate, Mapping):
            pytest.fail("Risk-estimator metrics must be JSON objects.")
        metric = cast(Mapping[str, object], metric_candidate)
        estimator_id = metric.get("estimator_id")
        if not isinstance(estimator_id, str):
            pytest.fail("Risk-estimator metric must include string 'estimator_id'.")
        metric_ids.add(estimator_id)
        _assert_decimal_field(metric, "value", str(Decimal(str(metric["value"]))))
        assert metric.get("window_days") == 30
        assert metric.get("return_basis") == "simple"
        annualization_basis = metric.get("annualization_basis")
        if not isinstance(annualization_basis, Mapping):
            pytest.fail("Risk-estimator metric annualization_basis must be an object.")
        annualization_basis_mapping = cast(Mapping[str, object], annualization_basis)
        assert annualization_basis_mapping.get("kind") == "trading_days"
        assert annualization_basis_mapping.get("value") == 252
        as_of_timestamp = metric.get("as_of_timestamp")
        if not isinstance(as_of_timestamp, str):
            pytest.fail("Risk-estimator metric must include string 'as_of_timestamp'.")
        assert as_of_timestamp

    assert metric_ids == {"volatility_annualized", "max_drawdown", "beta"}


@pytest.mark.integration
def test_risk_estimators_endpoint_rejects_unsupported_window_explicitly(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Risk-estimators route should reject unsupported windows with explicit 422 detail."""

    risk_path = _portfolio_workspace_endpoint_path(suffix="risk-estimators")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=35))

    response = client.get(
        risk_path,
        params={"window_days": 45},
    )
    assert response.status_code == 422

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Unsupported-window response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    detail = payload.get("detail")
    if not isinstance(detail, str):
        pytest.fail("Unsupported-window response must include string 'detail'.")
    assert "supported windows" in detail.lower()


@pytest.mark.integration
def test_risk_estimators_endpoint_rejects_insufficient_history_explicitly(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Risk-estimators route should reject requests without required historical coverage."""

    risk_path = _portfolio_workspace_endpoint_path(suffix="risk-estimators")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=10))

    response = client.get(
        risk_path,
        params={"window_days": 30},
    )
    assert response.status_code == 409

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Insufficiency response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    detail = payload.get("detail")
    if not isinstance(detail, str):
        pytest.fail("Insufficiency response must include string 'detail'.")
    assert "insufficient persisted history" in detail.lower()


@pytest.mark.integration
def test_transactions_endpoint_returns_persisted_ledger_events(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_db_engine: AsyncEngine,
) -> None:
    """Transactions route should return persisted trade/dividend ledger events."""

    transactions_path = _portfolio_workspace_endpoint_path(suffix="transactions")
    _patch_forbidden_upstream_calls(monkeypatch)
    asyncio.run(_seed_persisted_ledger_state(test_db_engine, price_history_points=35))

    response = client.get(transactions_path)
    assert response.status_code == 200

    payload_raw = response.json()
    if not isinstance(payload_raw, dict):
        pytest.fail("Transactions response must be a JSON object.")
    payload = cast(dict[str, object], payload_raw)
    as_of_ledger_at = payload.get("as_of_ledger_at")
    assert isinstance(as_of_ledger_at, str)
    assert as_of_ledger_at

    events_raw = payload.get("events")
    if not isinstance(events_raw, list):
        pytest.fail("Transactions response must include an 'events' list.")
    events = cast(list[object], events_raw)
    assert len(events) >= 5

    event_types: set[str] = set()
    for event_candidate in events:
        if not isinstance(event_candidate, Mapping):
            pytest.fail("Transaction events must be JSON objects.")
        event = cast(Mapping[str, object], event_candidate)
        event_id = event.get("id")
        posted_at = event.get("posted_at")
        instrument_symbol = event.get("instrument_symbol")
        event_type = event.get("event_type")
        if not isinstance(event_id, str):
            pytest.fail("Transaction event id must be a string.")
        if not isinstance(posted_at, str):
            pytest.fail("Transaction event posted_at must be a string.")
        if not isinstance(instrument_symbol, str):
            pytest.fail("Transaction event instrument_symbol must be a string.")
        if not isinstance(event_type, str):
            pytest.fail("Transaction event event_type must be a string.")
        event_types.add(event_type)
        _assert_decimal_field(event, "quantity", str(Decimal(str(event["quantity"]))))
        _assert_decimal_field(event, "cash_amount_usd", str(Decimal(str(event["cash_amount_usd"]))))

    assert "buy" in event_types
    assert "sell" in event_types
    assert "dividend" in event_types
