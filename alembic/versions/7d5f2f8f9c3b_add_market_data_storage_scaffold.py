"""add market data storage scaffold

Revision ID: 7d5f2f8f9c3b
Revises: 12ecb9689094
Create Date: 2026-03-24 22:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d5f2f8f9c3b"
down_revision: str | Sequence[str] | None = "12ecb9689094"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "market_data_snapshot",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_provider", sa.String(length=64), nullable=False),
        sa.Column("snapshot_key", sa.String(length=128), nullable=False),
        sa.Column("snapshot_captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snapshot_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_type",
            "source_provider",
            "snapshot_key",
            name="uq_market_data_snapshot_source_identity_key",
        ),
    )
    op.create_index(
        "ix_market_data_snapshot_source_type",
        "market_data_snapshot",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        "ix_market_data_snapshot_source_provider",
        "market_data_snapshot",
        ["source_provider"],
        unique=False,
    )
    op.create_index(
        "ix_market_data_snapshot_snapshot_captured_at",
        "market_data_snapshot",
        ["snapshot_captured_at"],
        unique=False,
    )

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("market_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trading_date", sa.Date(), nullable=True),
        sa.Column("price_value", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("currency_code", sa.String(length=8), nullable=False),
        sa.Column("source_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(market_timestamp IS NOT NULL) <> (trading_date IS NOT NULL)",
            name="ck_price_history_exactly_one_time_key",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["market_data_snapshot.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_price_history_snapshot_id", "price_history", ["snapshot_id"], unique=False
    )
    op.create_index(
        "ix_price_history_instrument_symbol",
        "price_history",
        ["instrument_symbol"],
        unique=False,
    )
    op.create_index(
        "ix_price_history_market_timestamp",
        "price_history",
        ["market_timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_price_history_trading_date",
        "price_history",
        ["trading_date"],
        unique=False,
    )
    op.create_index(
        "uq_price_history_snapshot_symbol_market_timestamp",
        "price_history",
        ["snapshot_id", "instrument_symbol", "market_timestamp"],
        unique=True,
        postgresql_where=sa.text("market_timestamp IS NOT NULL"),
    )
    op.create_index(
        "uq_price_history_snapshot_symbol_trading_date",
        "price_history",
        ["snapshot_id", "instrument_symbol", "trading_date"],
        unique=True,
        postgresql_where=sa.text("trading_date IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "uq_price_history_snapshot_symbol_trading_date",
        table_name="price_history",
    )
    op.drop_index(
        "uq_price_history_snapshot_symbol_market_timestamp",
        table_name="price_history",
    )
    op.drop_index("ix_price_history_trading_date", table_name="price_history")
    op.drop_index("ix_price_history_market_timestamp", table_name="price_history")
    op.drop_index("ix_price_history_instrument_symbol", table_name="price_history")
    op.drop_index("ix_price_history_snapshot_id", table_name="price_history")
    op.drop_table("price_history")

    op.drop_index(
        "ix_market_data_snapshot_snapshot_captured_at",
        table_name="market_data_snapshot",
    )
    op.drop_index(
        "ix_market_data_snapshot_source_provider", table_name="market_data_snapshot"
    )
    op.drop_index(
        "ix_market_data_snapshot_source_type", table_name="market_data_snapshot"
    )
    op.drop_table("market_data_snapshot")
