"""Verify required schema tables exist in the configured database.

This is used by `just db-upgrade` and `just test-db-upgrade` to detect alembic drift
where the alembic version table is at head but expected tables are missing.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

REQUIRED_TABLES: tuple[str, ...] = (
    "source_document",
    "import_job",
    "canonical_pdf_record",
    "portfolio_transaction",
    "dividend_event",
    "corporate_action_event",
    "lot",
    "lot_disposition",
    "market_data_snapshot",
    "price_history",
)


async def _main(*, context: str) -> int:
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as conn:
            missing_tables: list[str] = []
            for table_name in REQUIRED_TABLES:
                exists = (
                    await conn.execute(
                        text("SELECT to_regclass(:regclass_name)"),
                        {"regclass_name": f"public.{table_name}"},
                    )
                ).scalar_one()
                if exists is None:
                    missing_tables.append(table_name)

            if missing_tables:
                message_prefix = "Alembic drift detected"
                if context.strip():
                    message_prefix = f"{message_prefix} ({context.strip()})"
                print(
                    f"{message_prefix}: missing tables at current revision: "
                    + ", ".join(missing_tables),
                    file=sys.stderr,
                )
                return 1
            return 0
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--context",
        default="",
        help="Optional label used in error messages (e.g. runtime_db, test_db).",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main(context=str(args.context))))


if __name__ == "__main__":
    main()
