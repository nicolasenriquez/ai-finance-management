"""Pytest fixtures for shared module tests."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.database import Base

_TEST_TABLE_PREFIX = "test_"


def _create_test_only_tables(sync_conn: Connection) -> None:
    """Create only local shared-test tables to avoid mutating app schema."""

    for table in Base.metadata.sorted_tables:
        if table.name.startswith(_TEST_TABLE_PREFIX):
            table.create(bind=sync_conn, checkfirst=True)


def _drop_test_only_tables(sync_conn: Connection) -> None:
    """Drop only local shared-test tables to avoid schema drift in integration DB."""

    for table in reversed(Base.metadata.sorted_tables):
        if table.name.startswith(_TEST_TABLE_PREFIX):
            table.drop(bind=sync_conn, checkfirst=True)


@pytest.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create fresh database engine for each test."""
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session and only test-local tables for shared tests."""

    async with test_db_engine.begin() as conn:
        await conn.run_sync(_create_test_only_tables)

    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session

    async with test_db_engine.begin() as conn:
        await conn.run_sync(_drop_test_only_tables)
