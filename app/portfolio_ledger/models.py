"""Database models for portfolio-ledger and lot derivation foundations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.pdf_persistence.models import CanonicalPdfRecord, ImportJob, SourceDocument
from app.shared.models import TimestampMixin


class PortfolioTransaction(Base, TimestampMixin):
    """Derived trade-ledger row created from one canonical trade record."""

    __tablename__ = "portfolio_transaction"
    __table_args__ = (
        UniqueConstraint(
            "canonical_record_id",
            name="uq_portfolio_transaction_canonical_record_id",
        ),
    )

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
    canonical_record_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_pdf_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    canonical_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    instrument_symbol: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    trade_side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    gross_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accounting_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)

    source_document: Mapped[SourceDocument] = relationship()
    import_job: Mapped[ImportJob] = relationship()
    canonical_record: Mapped[CanonicalPdfRecord] = relationship()
    opened_lots: Mapped[list[Lot]] = relationship(
        back_populates="opening_transaction",
        foreign_keys="Lot.opening_transaction_id",
    )
    lot_dispositions: Mapped[list[LotDisposition]] = relationship(
        back_populates="sell_transaction",
        foreign_keys="LotDisposition.sell_transaction_id",
    )


class DividendEvent(Base, TimestampMixin):
    """Derived dividend-income row created from one canonical dividend record."""

    __tablename__ = "dividend_event"
    __table_args__ = (
        UniqueConstraint(
            "canonical_record_id", name="uq_dividend_event_canonical_record_id"
        ),
    )

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
    canonical_record_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_pdf_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    canonical_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    instrument_symbol: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    gross_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    taxes_withheld_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accounting_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)

    source_document: Mapped[SourceDocument] = relationship()
    import_job: Mapped[ImportJob] = relationship()
    canonical_record: Mapped[CanonicalPdfRecord] = relationship()


class CorporateActionEvent(Base, TimestampMixin):
    """Derived corporate-action row created from one canonical split record."""

    __tablename__ = "corporate_action_event"
    __table_args__ = (
        UniqueConstraint(
            "canonical_record_id",
            name="uq_corporate_action_event_canonical_record_id",
        ),
    )

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
    canonical_record_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_pdf_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    canonical_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    instrument_symbol: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    shares_before_qty: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    shares_after_qty: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    split_ratio_value: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    accounting_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)

    source_document: Mapped[SourceDocument] = relationship()
    import_job: Mapped[ImportJob] = relationship()
    canonical_record: Mapped[CanonicalPdfRecord] = relationship()
    impacted_lots: Mapped[list[Lot]] = relationship(
        back_populates="last_corporate_action_event",
    )


class Lot(Base, TimestampMixin):
    """Open or closed lot derived from a buy-side portfolio transaction."""

    __tablename__ = "lot"
    __table_args__ = (
        UniqueConstraint("opening_transaction_id", name="uq_lot_opening_tx"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opening_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_transaction.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    last_corporate_action_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("corporate_action_event.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    instrument_symbol: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    opened_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    original_qty: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    remaining_qty: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    total_cost_basis_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    unit_cost_basis_usd: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    accounting_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)

    opening_transaction: Mapped[PortfolioTransaction] = relationship(
        back_populates="opened_lots",
        foreign_keys=[opening_transaction_id],
    )
    last_corporate_action_event: Mapped[CorporateActionEvent | None] = relationship(
        back_populates="impacted_lots",
    )
    dispositions: Mapped[list[LotDisposition]] = relationship(back_populates="lot")


class LotDisposition(Base, TimestampMixin):
    """Sell-side lot match row produced by FIFO disposition logic."""

    __tablename__ = "lot_disposition"
    __table_args__ = (
        UniqueConstraint(
            "lot_id",
            "sell_transaction_id",
            name="uq_lot_disposition_lot_sell_tx",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[int] = mapped_column(
        ForeignKey("lot.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sell_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_transaction.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    disposition_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    matched_qty: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    matched_cost_basis_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    accounting_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)

    lot: Mapped[Lot] = relationship(back_populates="dispositions")
    sell_transaction: Mapped[PortfolioTransaction] = relationship(
        back_populates="lot_dispositions",
        foreign_keys=[sell_transaction_id],
    )
