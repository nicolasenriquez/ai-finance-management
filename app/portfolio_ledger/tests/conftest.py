"""Pytest fixtures for portfolio-ledger integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.tests.db_url import resolve_test_database_url

_REQUIRED_INTEGRATION_TABLES: tuple[str, ...] = (
    "source_document",
    "import_job",
    "canonical_pdf_record",
    "portfolio_transaction",
    "dividend_event",
    "corporate_action_event",
    "lot",
    "lot_disposition",
)


async def _assert_required_tables_exist(*, session: AsyncSession) -> None:
    """Fail fast when integration DB schema is not migrated."""

    missing_tables: list[str] = []
    for table_name in _REQUIRED_INTEGRATION_TABLES:
        exists_result = await session.execute(
            text("SELECT to_regclass(:regclass_name)"),
            {"regclass_name": f"public.{table_name}"},
        )
        if exists_result.scalar_one() is None:
            missing_tables.append(table_name)

    if not missing_tables:
        return

    missing_tables_csv = ", ".join(missing_tables)
    pytest.fail(
        "Portfolio-ledger integration tests require migrated tables. "
        f"Missing tables: {missing_tables_csv}. "
        "Run 'uv run alembic stamp base && uv run alembic upgrade head'."
    )


@pytest.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a fresh database engine for each portfolio-ledger test."""

    settings = get_settings()
    test_database_url = resolve_test_database_url(
        runtime_database_url=settings.database_url
    )
    engine = create_async_engine(
        test_database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(
    test_db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each portfolio-ledger test."""

    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session() as session:
        await _assert_required_tables_exist(session=session)
        yield session


@pytest.fixture(scope="function", autouse=True)
async def _assert_integration_schema_for_marked_tests(
    request: pytest.FixtureRequest,
    test_db_engine: AsyncEngine,
) -> AsyncGenerator[None, None]:
    """Fail fast for integration tests even when they use the engine fixture directly."""

    if "integration" not in request.keywords:
        yield
        return

    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session() as session:
        await _assert_required_tables_exist(session=session)

    yield
