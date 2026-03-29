"""Unit tests for QuantStats report artifact lifecycle and retrieval semantics."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from app.portfolio_analytics.schemas import PortfolioChartPeriod, PortfolioQuantReportScope


def test_quant_report_retrieval_returns_expired_error_and_cleans_up_artifact(
    tmp_path: Path,
) -> None:
    """Expired report artifacts should fail explicitly and be removed from lifecycle state."""

    service_module = import_module("app.portfolio_analytics.service")
    client_error_type = cast(type[Exception], service_module.PortfolioAnalyticsClientError)
    artifact_type = service_module._QuantReportArtifact
    registry = cast(dict[str, object], service_module._QUANT_REPORT_ARTIFACTS_BY_ID)
    get_html_content = cast(
        Callable[..., str],
        service_module.get_portfolio_quant_report_html_content,
    )

    registry.clear()
    report_id = "expired-report-id"
    output_path = tmp_path / "expired-report.html"
    output_path.write_text("<html>expired</html>", encoding="utf-8")
    generated_at = datetime.now(UTC) - timedelta(minutes=10)
    expired_at = datetime.now(UTC) - timedelta(minutes=1)

    registry[report_id] = artifact_type(
        report_id=report_id,
        scope=PortfolioQuantReportScope.PORTFOLIO,
        instrument_symbol=None,
        period=PortfolioChartPeriod.D30,
        benchmark_symbol=None,
        generated_at=generated_at,
        expires_at=expired_at,
        output_path=output_path,
    )

    with pytest.raises(client_error_type) as exc_info:
        get_html_content(report_id=report_id)

    assert getattr(exc_info.value, "status_code", None) == 410
    assert report_id not in registry
    assert not output_path.exists()
