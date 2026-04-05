"""add portfolio ml model registry snapshot table

Revision ID: e1a9c4d2b6f1
Revises: 7d5f2f8f9c3b
Create Date: 2026-04-05 02:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a9c4d2b6f1"
down_revision: str | Sequence[str] | None = "7d5f2f8f9c3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "portfolio_ml_model_snapshot",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("snapshot_ref", sa.String(length=128), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=True),
        sa.Column("model_family", sa.String(length=64), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("feature_set_hash", sa.String(length=128), nullable=False),
        sa.Column("data_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_status", sa.String(length=32), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_snapshot_ref", sa.String(length=128), nullable=True),
        sa.Column("policy_result", sa.JSON(), nullable=False),
        sa.Column("metric_vector", sa.JSON(), nullable=False),
        sa.Column("baseline_comparator_metrics", sa.JSON(), nullable=False),
        sa.Column("failure_reason_code", sa.String(length=64), nullable=True),
        sa.Column("failure_reason_detail", sa.String(length=255), nullable=True),
        sa.Column("snapshot_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_ref", name="uq_portfolio_ml_model_snapshot_ref"),
    )
    op.create_index(
        "ix_portfolio_ml_model_snapshot_snapshot_ref",
        "portfolio_ml_model_snapshot",
        ["snapshot_ref"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_ml_model_snapshot_scope",
        "portfolio_ml_model_snapshot",
        ["scope"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_ml_model_snapshot_instrument_symbol",
        "portfolio_ml_model_snapshot",
        ["instrument_symbol"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_ml_model_snapshot_model_family",
        "portfolio_ml_model_snapshot",
        ["model_family"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_ml_model_snapshot_lifecycle_state",
        "portfolio_ml_model_snapshot",
        ["lifecycle_state"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_ml_model_snapshot_run_status",
        "portfolio_ml_model_snapshot",
        ["run_status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_portfolio_ml_model_snapshot_run_status",
        table_name="portfolio_ml_model_snapshot",
    )
    op.drop_index(
        "ix_portfolio_ml_model_snapshot_lifecycle_state",
        table_name="portfolio_ml_model_snapshot",
    )
    op.drop_index(
        "ix_portfolio_ml_model_snapshot_model_family",
        table_name="portfolio_ml_model_snapshot",
    )
    op.drop_index(
        "ix_portfolio_ml_model_snapshot_instrument_symbol",
        table_name="portfolio_ml_model_snapshot",
    )
    op.drop_index(
        "ix_portfolio_ml_model_snapshot_scope",
        table_name="portfolio_ml_model_snapshot",
    )
    op.drop_index(
        "ix_portfolio_ml_model_snapshot_snapshot_ref",
        table_name="portfolio_ml_model_snapshot",
    )
    op.drop_table("portfolio_ml_model_snapshot")
