"""Database models for market-data snapshot and price-history storage."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin


class MarketDataSnapshot(Base, TimestampMixin):
    """One provider snapshot context used for market-data ingestion."""

    __tablename__ = "market_data_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_provider",
            "snapshot_key",
            name="uq_market_data_snapshot_source_identity_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    snapshot_key: Mapped[str] = mapped_column(String(128), nullable=False)
    snapshot_captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    snapshot_metadata: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True
    )

    prices: Mapped[list[PriceHistory]] = relationship(back_populates="snapshot")


class PriceHistory(Base, TimestampMixin):
    """One market-data value for one instrument at one market time context."""

    __tablename__ = "price_history"
    __table_args__ = (
        CheckConstraint(
            "(market_timestamp IS NOT NULL) <> (trading_date IS NOT NULL)",
            name="ck_price_history_exactly_one_time_key",
        ),
        Index(
            "uq_price_history_snapshot_symbol_market_timestamp",
            "snapshot_id",
            "instrument_symbol",
            "market_timestamp",
            unique=True,
            postgresql_where=text("market_timestamp IS NOT NULL"),
        ),
        Index(
            "uq_price_history_snapshot_symbol_trading_date",
            "snapshot_id",
            "instrument_symbol",
            "trading_date",
            unique=True,
            postgresql_where=text("trading_date IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("market_data_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    instrument_symbol: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    market_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    trading_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    price_value: Mapped[Decimal] = mapped_column(Numeric(18, 9), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False)
    source_payload: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True
    )

    snapshot: Mapped[MarketDataSnapshot] = relationship(back_populates="prices")
