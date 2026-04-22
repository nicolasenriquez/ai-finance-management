"""Database models for PDF persistence."""

from __future__ import annotations

from datetime import date

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin


class SourceDocument(Base, TimestampMixin):
    """Deduplicated source-document metadata persisted by SHA-256."""

    __tablename__ = "source_document"
    __table_args__ = (UniqueConstraint("sha256", name="uq_source_document_sha256"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    import_jobs: Mapped[list[ImportJob]] = relationship(back_populates="source_document")
    canonical_records: Mapped[list[CanonicalPdfRecord]] = relationship(
        back_populates="source_document"
    )


class ImportJob(Base, TimestampMixin):
    """Successful committed persistence run linked to a source document."""

    __tablename__ = "import_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_document.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_records: Mapped[int] = mapped_column(Integer, nullable=False)
    inserted_records: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicate_records: Mapped[int] = mapped_column(Integer, nullable=False)

    source_document: Mapped[SourceDocument] = relationship(back_populates="import_jobs")
    canonical_records: Mapped[list[CanonicalPdfRecord]] = relationship(back_populates="import_job")


class CanonicalPdfRecord(Base, TimestampMixin):
    """Persisted canonical record plus JSON audit payload and provenance."""

    __tablename__ = "canonical_pdf_record"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_canonical_pdf_record_fingerprint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_document.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    import_job_id: Mapped[int] = mapped_column(
        ForeignKey("import_job.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    instrument_symbol: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trade_side: Mapped[str | None] = mapped_column(String(8), nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    fingerprint_version: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    raw_values: Mapped[dict[str, str | None]] = mapped_column(JSON, nullable=False)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)

    source_document: Mapped[SourceDocument] = relationship(back_populates="canonical_records")
    import_job: Mapped[ImportJob] = relationship(back_populates="canonical_records")
