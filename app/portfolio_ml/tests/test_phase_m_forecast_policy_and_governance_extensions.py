"""Tests for phase-m forecast policy and governance registry extensions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

import pytest

from app.portfolio_ml.models import PortfolioMLModelSnapshot
from app.portfolio_ml.schemas import PortfolioMLScope
from app.portfolio_ml.service import (
    enforce_supported_model_policy,
    get_portfolio_ml_forecast_response,
    get_portfolio_ml_registry_response,
    run_baseline_candidate_forecasts,
)


def test_baseline_candidate_forecasts_include_quantile_boosting_family() -> None:
    """Forecast baseline candidate set should include quantile-boosting family."""

    candidates = run_baseline_candidate_forecasts(
        series_values=[
            Decimal("100.0"),
            Decimal("100.8"),
            Decimal("101.2"),
            Decimal("101.7"),
            Decimal("102.1"),
            Decimal("102.5"),
            Decimal("103.0"),
            Decimal("103.4"),
            Decimal("103.9"),
            Decimal("104.2"),
        ],
        horizon_count=3,
        seasonal_period=3,
    )

    assert "quantile_boosting" in candidates
    assert len(candidates["quantile_boosting"]) == 3


def test_model_policy_supports_segmentation_and_anomaly_families() -> None:
    """Model-family policy should allow segmentation and anomaly governance families."""

    assert (
        enforce_supported_model_policy(model_family="kmeans_proxy_v1")
        == "kmeans_proxy_v1"
    )
    assert (
        enforce_supported_model_policy(model_family="isolation_forest_proxy_v1")
        == "isolation_forest_proxy_v1"
    )
    assert (
        enforce_supported_model_policy(model_family="quantile_boosting")
        == "quantile_boosting"
    )


@pytest.mark.asyncio
async def test_forecast_policy_disallow_records_quantile_candidate_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disallowed quantile candidate should be captured with explicit policy reason metadata."""

    import app.portfolio_ml.service as service_module

    captured_upserts: list[dict[str, object]] = []

    async def _fake_upsert(**kwargs: object) -> object:
        payload = cast(dict[str, object], kwargs.get("snapshot_payload"))
        captured_upserts.append(payload)
        return object()

    def _fake_policy_allowance(
        *,
        scope: PortfolioMLScope,
        model_family: str,
    ) -> tuple[bool, str | None]:
        if scope is PortfolioMLScope.PORTFOLIO and model_family == "quantile_boosting":
            return (False, "policy_disallowed_for_scope")
        return (True, None)

    monkeypatch.setattr(service_module, "_upsert_model_snapshot", _fake_upsert)
    monkeypatch.setattr(
        service_module,
        "_is_forecast_family_policy_allowed_for_scope",
        _fake_policy_allowance,
    )

    response = await get_portfolio_ml_forecast_response(
        scope=PortfolioMLScope.PORTFOLIO,
        instrument_symbol=None,
        db=cast(Any, object()),
    )

    quantile_audit_rows = [
        row
        for row in captured_upserts
        if row.get("model_family") == "quantile_boosting"
    ]
    assert len(quantile_audit_rows) >= 1
    policy_result = cast(dict[str, object], quantile_audit_rows[0]["policy_result"])
    assert policy_result.get("reason_code") == "policy_disallowed_for_scope"
    assert response.state.value in {"ready", "unavailable", "stale"}


class _FakeScalarResult:
    """Minimal scalar-result adapter for fake SQLAlchemy execute responses."""

    _rows: list[PortfolioMLModelSnapshot]

    def __init__(self, rows: list[PortfolioMLModelSnapshot]) -> None:
        self._rows = rows

    def all(self) -> list[PortfolioMLModelSnapshot]:
        """Return seeded rows."""

        return self._rows


class _FakeExecuteResult:
    """Minimal execute result exposing scalars().all()."""

    _rows: list[PortfolioMLModelSnapshot]

    def __init__(self, rows: list[PortfolioMLModelSnapshot]) -> None:
        self._rows = rows

    def scalars(self) -> _FakeScalarResult:
        """Return scalar wrapper."""

        return _FakeScalarResult(self._rows)


class _FakeRegistryDb:
    """Minimal async DB adapter for registry response service tests."""

    _rows: list[PortfolioMLModelSnapshot]

    def __init__(self, rows: list[PortfolioMLModelSnapshot]) -> None:
        self._rows = rows

    async def execute(self, _: object) -> _FakeExecuteResult:
        """Return deterministic registry rows."""

        return _FakeExecuteResult(self._rows)


@pytest.mark.asyncio
async def test_registry_surfaces_family_specific_stale_state_and_governance_metadata() -> (
    None
):
    """Registry should expose stale family reason and reproducibility metadata."""

    evaluated_at = datetime(2026, 4, 6, 15, 0, tzinfo=UTC)
    snapshot = PortfolioMLModelSnapshot(
        snapshot_ref="portfolio_kmeans_proxy_v1_20260406T150000Z",
        scope="portfolio",
        instrument_symbol=None,
        model_family="kmeans_proxy_v1",
        lifecycle_state="ready",
        feature_set_hash="portfolio_ml_features_segmentation_v1",
        data_window_start=evaluated_at - timedelta(days=120),
        data_window_end=evaluated_at - timedelta(days=1),
        run_status="completed",
        promoted_at=evaluated_at - timedelta(hours=30),
        expires_at=evaluated_at - timedelta(hours=1),
        replaced_snapshot_ref=None,
        policy_result={"qualified": True, "reason_code": "ready"},
        metric_vector={"row_count": 3},
        baseline_comparator_metrics={},
        failure_reason_code="kmeans_proxy_v1_source_data_stale",
        failure_reason_detail="Source snapshot age exceeds freshness policy threshold.",
        snapshot_metadata={
            "policy_version": "segmentation_policy_v1_20260406",
            "feature_set_version": "segmentation_features_v1",
        },
    )
    fake_db = _FakeRegistryDb([snapshot])

    response = await get_portfolio_ml_registry_response(
        db=cast(Any, fake_db),
        scope="portfolio",
        model_family="kmeans_proxy_v1",
        lifecycle_state=None,
    )

    assert response.state.value == "stale"
    assert response.state_reason_code == "kmeans_proxy_v1_source_data_stale"
    assert len(response.rows) == 1
    first_row = response.rows[0]
    assert first_row.policy_version == "segmentation_policy_v1_20260406"
    assert first_row.feature_set_version == "segmentation_features_v1"
