"""add pdf persistence schema

Revision ID: c8b0721b0977
Revises: e4a05b88d90b
Create Date: 2026-03-21 14:34:46.630296

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8b0721b0977"
down_revision: str | Sequence[str] | None = "e4a05b88d90b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "source_document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sha256", name="uq_source_document_sha256"),
    )
    op.create_table(
        "import_job",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("normalized_records", sa.Integer(), nullable=False),
        sa.Column("inserted_records", sa.Integer(), nullable=False),
        sa.Column("duplicate_records", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_document.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_import_job_source_document_id",
        "import_job",
        ["source_document_id"],
        unique=False,
    )

    op.create_table(
        "canonical_pdf_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("import_job_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("trade_side", sa.String(length=8), nullable=True),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("fingerprint_version", sa.String(length=32), nullable=False),
        sa.Column("canonical_schema_version", sa.String(length=32), nullable=False),
        sa.Column("canonical_payload", sa.JSON(), nullable=False),
        sa.Column("raw_values", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_job.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_document.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint", name="uq_canonical_pdf_record_fingerprint"),
    )
    op.create_index(
        "ix_canonical_pdf_record_source_document_id",
        "canonical_pdf_record",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        "ix_canonical_pdf_record_import_job_id",
        "canonical_pdf_record",
        ["import_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_canonical_pdf_record_event_type",
        "canonical_pdf_record",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_canonical_pdf_record_event_date",
        "canonical_pdf_record",
        ["event_date"],
        unique=False,
    )
    op.create_index(
        "ix_canonical_pdf_record_instrument_symbol",
        "canonical_pdf_record",
        ["instrument_symbol"],
        unique=False,
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_canonical_pdf_record_instrument_symbol",
        table_name="canonical_pdf_record",
    )
    op.drop_index(
        "ix_canonical_pdf_record_event_date",
        table_name="canonical_pdf_record",
    )
    op.drop_index(
        "ix_canonical_pdf_record_event_type",
        table_name="canonical_pdf_record",
    )
    op.drop_index(
        "ix_canonical_pdf_record_import_job_id",
        table_name="canonical_pdf_record",
    )
    op.drop_index(
        "ix_canonical_pdf_record_source_document_id",
        table_name="canonical_pdf_record",
    )
    op.drop_table("canonical_pdf_record")

    op.drop_index(
        "ix_import_job_source_document_id",
        table_name="import_job",
    )
    op.drop_table("import_job")

    op.drop_table("source_document")
