"""Database models for portfolio ML model-registry persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin


class PortfolioMLModelSnapshot(Base, TimestampMixin):
    """Persisted model snapshot metadata for governance and registry audit contracts."""

    __tablename__ = "portfolio_ml_model_snapshot"
    __table_args__ = (
        UniqueConstraint("snapshot_ref", name="uq_portfolio_ml_model_snapshot_ref"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_ref: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    instrument_symbol: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    model_family: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    lifecycle_state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    feature_set_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    data_window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_window_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    run_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    replaced_snapshot_ref: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    policy_result: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    metric_vector: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    baseline_comparator_metrics: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False
    )
    failure_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason_detail: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    snapshot_metadata: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True
    )
