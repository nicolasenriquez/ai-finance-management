"""add portfolio ledger foundation tables

Revision ID: 12ecb9689094
Revises: c8b0721b0977
Create Date: 2026-03-22 12:56:57.120814

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12ecb9689094"
down_revision: str | Sequence[str] | None = "c8b0721b0977"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "portfolio_transaction",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("import_job_id", sa.Integer(), nullable=False),
        sa.Column("canonical_record_id", sa.Integer(), nullable=False),
        sa.Column("canonical_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("trade_side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("gross_amount_usd", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("accounting_policy_version", sa.String(length=64), nullable=False),
        sa.Column("canonical_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_document.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_job.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_record_id"],
            ["canonical_pdf_record.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canonical_record_id",
            name="uq_portfolio_transaction_canonical_record_id",
        ),
    )
    op.create_index(
        "ix_portfolio_transaction_source_document_id",
        "portfolio_transaction",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_transaction_import_job_id",
        "portfolio_transaction",
        ["import_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_transaction_canonical_record_id",
        "portfolio_transaction",
        ["canonical_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_transaction_event_date",
        "portfolio_transaction",
        ["event_date"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_transaction_instrument_symbol",
        "portfolio_transaction",
        ["instrument_symbol"],
        unique=False,
    )

    op.create_table(
        "dividend_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("import_job_id", sa.Integer(), nullable=False),
        sa.Column("canonical_record_id", sa.Integer(), nullable=False),
        sa.Column("canonical_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("gross_amount_usd", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("taxes_withheld_usd", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("net_amount_usd", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("accounting_policy_version", sa.String(length=64), nullable=False),
        sa.Column("canonical_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_document.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_job.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_record_id"],
            ["canonical_pdf_record.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canonical_record_id",
            name="uq_dividend_event_canonical_record_id",
        ),
    )
    op.create_index(
        "ix_dividend_event_source_document_id",
        "dividend_event",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        "ix_dividend_event_import_job_id",
        "dividend_event",
        ["import_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_dividend_event_canonical_record_id",
        "dividend_event",
        ["canonical_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_dividend_event_event_date",
        "dividend_event",
        ["event_date"],
        unique=False,
    )
    op.create_index(
        "ix_dividend_event_instrument_symbol",
        "dividend_event",
        ["instrument_symbol"],
        unique=False,
    )

    op.create_table(
        "corporate_action_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("import_job_id", sa.Integer(), nullable=False),
        sa.Column("canonical_record_id", sa.Integer(), nullable=False),
        sa.Column("canonical_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("shares_before_qty", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("shares_after_qty", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("split_ratio_value", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("accounting_policy_version", sa.String(length=64), nullable=False),
        sa.Column("canonical_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_document.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_job.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_record_id"],
            ["canonical_pdf_record.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canonical_record_id",
            name="uq_corporate_action_event_canonical_record_id",
        ),
    )
    op.create_index(
        "ix_corporate_action_event_source_document_id",
        "corporate_action_event",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        "ix_corporate_action_event_import_job_id",
        "corporate_action_event",
        ["import_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_corporate_action_event_canonical_record_id",
        "corporate_action_event",
        ["canonical_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_corporate_action_event_event_date",
        "corporate_action_event",
        ["event_date"],
        unique=False,
    )
    op.create_index(
        "ix_corporate_action_event_instrument_symbol",
        "corporate_action_event",
        ["instrument_symbol"],
        unique=False,
    )

    op.create_table(
        "lot",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("opening_transaction_id", sa.Integer(), nullable=False),
        sa.Column("last_corporate_action_event_id", sa.Integer(), nullable=True),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("opened_on", sa.Date(), nullable=False),
        sa.Column("original_qty", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("remaining_qty", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("total_cost_basis_usd", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("unit_cost_basis_usd", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("accounting_policy_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["opening_transaction_id"],
            ["portfolio_transaction.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["last_corporate_action_event_id"],
            ["corporate_action_event.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opening_transaction_id", name="uq_lot_opening_tx"),
    )
    op.create_index(
        "ix_lot_opening_transaction_id", "lot", ["opening_transaction_id"], unique=False
    )
    op.create_index(
        "ix_lot_last_corporate_action_event_id",
        "lot",
        ["last_corporate_action_event_id"],
        unique=False,
    )
    op.create_index("ix_lot_instrument_symbol", "lot", ["instrument_symbol"], unique=False)
    op.create_index("ix_lot_opened_on", "lot", ["opened_on"], unique=False)

    op.create_table(
        "lot_disposition",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=False),
        sa.Column("sell_transaction_id", sa.Integer(), nullable=False),
        sa.Column("disposition_date", sa.Date(), nullable=False),
        sa.Column("matched_qty", sa.Numeric(precision=18, scale=9), nullable=False),
        sa.Column("matched_cost_basis_usd", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("accounting_policy_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lot_id"],
            ["lot.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["sell_transaction_id"],
            ["portfolio_transaction.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lot_id", "sell_transaction_id", name="uq_lot_disposition_lot_sell_tx"),
    )
    op.create_index("ix_lot_disposition_lot_id", "lot_disposition", ["lot_id"], unique=False)
    op.create_index(
        "ix_lot_disposition_sell_transaction_id",
        "lot_disposition",
        ["sell_transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_lot_disposition_disposition_date",
        "lot_disposition",
        ["disposition_date"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_lot_disposition_disposition_date", table_name="lot_disposition")
    op.drop_index("ix_lot_disposition_sell_transaction_id", table_name="lot_disposition")
    op.drop_index("ix_lot_disposition_lot_id", table_name="lot_disposition")
    op.drop_table("lot_disposition")

    op.drop_index("ix_lot_opened_on", table_name="lot")
    op.drop_index("ix_lot_instrument_symbol", table_name="lot")
    op.drop_index("ix_lot_last_corporate_action_event_id", table_name="lot")
    op.drop_index("ix_lot_opening_transaction_id", table_name="lot")
    op.drop_table("lot")

    op.drop_index(
        "ix_corporate_action_event_instrument_symbol",
        table_name="corporate_action_event",
    )
    op.drop_index("ix_corporate_action_event_event_date", table_name="corporate_action_event")
    op.drop_index(
        "ix_corporate_action_event_canonical_record_id",
        table_name="corporate_action_event",
    )
    op.drop_index("ix_corporate_action_event_import_job_id", table_name="corporate_action_event")
    op.drop_index(
        "ix_corporate_action_event_source_document_id",
        table_name="corporate_action_event",
    )
    op.drop_table("corporate_action_event")

    op.drop_index("ix_dividend_event_instrument_symbol", table_name="dividend_event")
    op.drop_index("ix_dividend_event_event_date", table_name="dividend_event")
    op.drop_index("ix_dividend_event_canonical_record_id", table_name="dividend_event")
    op.drop_index("ix_dividend_event_import_job_id", table_name="dividend_event")
    op.drop_index("ix_dividend_event_source_document_id", table_name="dividend_event")
    op.drop_table("dividend_event")

    op.drop_index(
        "ix_portfolio_transaction_instrument_symbol",
        table_name="portfolio_transaction",
    )
    op.drop_index("ix_portfolio_transaction_event_date", table_name="portfolio_transaction")
    op.drop_index(
        "ix_portfolio_transaction_canonical_record_id",
        table_name="portfolio_transaction",
    )
    op.drop_index("ix_portfolio_transaction_import_job_id", table_name="portfolio_transaction")
    op.drop_index(
        "ix_portfolio_transaction_source_document_id",
        table_name="portfolio_transaction",
    )
    op.drop_table("portfolio_transaction")
