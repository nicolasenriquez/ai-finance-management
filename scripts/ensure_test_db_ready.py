"""Ensure the isolated test database exists and is writable.

This is invoked by `just test-db-upgrade` before running alembic migrations.
It can create the target database when TEST_DATABASE_ADMIN_URL or equivalent
permissions are available, then verifies the current user has CREATE on schema
public.
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine


def _escape_identifier(value: str) -> str:
    return value.replace('"', '""')


async def _main() -> int:
    test_database_url = os.environ["TEST_DATABASE_URL"]
    target_url = make_url(test_database_url)
    target_db_name = target_url.database
    target_db_owner = target_url.username

    if not target_db_name:
        print("TEST_DATABASE_URL must include a database name.", file=sys.stderr)
        return 1

    admin_url_raw = os.environ.get("TEST_DATABASE_ADMIN_URL", "").strip()
    if admin_url_raw:
        admin_url = make_url(admin_url_raw)
    else:
        admin_db_name = os.environ.get("TEST_DATABASE_ADMIN_DB", "postgres")
        admin_url = target_url.set(database=admin_db_name)

    engine = create_async_engine(str(admin_url), isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as connection:
            exists = (
                await connection.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                    {"database_name": target_db_name},
                )
            ).scalar_one_or_none()

            if exists is None:
                escaped_db_name = _escape_identifier(target_db_name)
                owner_clause = ""
                if target_db_owner:
                    escaped_owner = _escape_identifier(target_db_owner)
                    owner_clause = f' OWNER "{escaped_owner}"'
                await connection.execute(
                    text(f'CREATE DATABASE "{escaped_db_name}"{owner_clause}')
                )
                print(f"Created missing test database: {target_db_name}")
            else:
                print(f"Test database already exists: {target_db_name}")

            if target_db_owner:
                escaped_db_name = _escape_identifier(target_db_name)
                escaped_owner = _escape_identifier(target_db_owner)
                try:
                    await connection.execute(
                        text(
                            f'ALTER DATABASE "{escaped_db_name}" OWNER TO "{escaped_owner}"'
                        )
                    )

                    schema_admin_url = admin_url.set(database=target_db_name)
                    schema_engine = create_async_engine(
                        str(schema_admin_url), isolation_level="AUTOCOMMIT"
                    )
                    try:
                        async with schema_engine.connect() as schema_connection:
                            await schema_connection.execute(
                                text(f'ALTER SCHEMA public OWNER TO "{escaped_owner}"')
                            )
                            await schema_connection.execute(
                                text(f'GRANT ALL ON SCHEMA public TO "{escaped_owner}"')
                            )
                    finally:
                        await schema_engine.dispose()
                except Exception as owner_bootstrap_error:
                    print(
                        "Skipped owner/schema bootstrap normalization: "
                        f"{owner_bootstrap_error}",
                        file=sys.stderr,
                    )
    finally:
        await engine.dispose()

    verification_engine = create_async_engine(str(target_url))
    try:
        async with verification_engine.connect() as connection:
            can_create = (
                await connection.execute(
                    text(
                        "SELECT has_schema_privilege(current_user, 'public', 'CREATE')"
                    )
                )
            ).scalar_one()
            if not can_create:
                print(
                    "Test DB user lacks CREATE on schema public. "
                    "Use TEST_DATABASE_ADMIN_URL for bootstrap or grant schema privileges.",
                    file=sys.stderr,
                )
                return 1
    finally:
        await verification_engine.dispose()

    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
