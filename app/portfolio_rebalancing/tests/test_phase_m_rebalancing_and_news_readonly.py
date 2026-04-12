"""Integration tests for phase-m rebalancing/news read-only and deterministic behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.portfolio_analytics.schemas import PortfolioSummaryResponse, PortfolioSummaryRow


class _FakeDbSession:
    """Minimal fake DB session for asserting read-only endpoint semantics."""

    commit_calls: int
    flush_calls: int

    def __init__(self) -> None:
        self.commit_calls = 0
        self.flush_calls = 0

    async def commit(self) -> None:
        """Track unexpected commit calls."""

        self.commit_calls += 1

    async def flush(self) -> None:
        """Track unexpected flush calls."""

        self.flush_calls += 1


def _fixed_summary_response() -> PortfolioSummaryResponse:
    """Build one deterministic summary payload for integration endpoint tests."""

    as_of_ledger_at = datetime(2026, 4, 6, 12, 0, tzinfo=UTC)
    as_of_market_at = datetime(2026, 4, 6, 12, 0, tzinfo=UTC)
    return PortfolioSummaryResponse(
        as_of_ledger_at=as_of_ledger_at,
        pricing_snapshot_key="snapshot_20260406",
        pricing_snapshot_captured_at=as_of_market_at,
        rows=[
            PortfolioSummaryRow(
                instrument_symbol="AAPL",
                open_quantity=Decimal("10"),
                open_cost_basis_usd=Decimal("1600.00"),
                open_lot_count=1,
                realized_proceeds_usd=Decimal("0"),
                realized_cost_basis_usd=Decimal("0"),
                realized_gain_usd=Decimal("0"),
                dividend_gross_usd=Decimal("0"),
                dividend_taxes_usd=Decimal("0"),
                dividend_net_usd=Decimal("0"),
                latest_close_price_usd=Decimal("200.00"),
                market_value_usd=Decimal("2000.00"),
                unrealized_gain_usd=Decimal("400.00"),
                unrealized_gain_pct=Decimal("25.00"),
            ),
            PortfolioSummaryRow(
                instrument_symbol="MSFT",
                open_quantity=Decimal("5"),
                open_cost_basis_usd=Decimal("1400.00"),
                open_lot_count=1,
                realized_proceeds_usd=Decimal("0"),
                realized_cost_basis_usd=Decimal("0"),
                realized_gain_usd=Decimal("0"),
                dividend_gross_usd=Decimal("0"),
                dividend_taxes_usd=Decimal("0"),
                dividend_net_usd=Decimal("0"),
                latest_close_price_usd=Decimal("320.00"),
                market_value_usd=Decimal("1600.00"),
                unrealized_gain_usd=Decimal("200.00"),
                unrealized_gain_pct=Decimal("14.29"),
            ),
            PortfolioSummaryRow(
                instrument_symbol="BTC",
                open_quantity=Decimal("0.05"),
                open_cost_basis_usd=Decimal("2500.00"),
                open_lot_count=1,
                realized_proceeds_usd=Decimal("0"),
                realized_cost_basis_usd=Decimal("0"),
                realized_gain_usd=Decimal("0"),
                dividend_gross_usd=Decimal("0"),
                dividend_taxes_usd=Decimal("0"),
                dividend_net_usd=Decimal("0"),
                latest_close_price_usd=Decimal("60000.00"),
                market_value_usd=Decimal("3000.00"),
                unrealized_gain_usd=Decimal("500.00"),
                unrealized_gain_pct=Decimal("20.00"),
            ),
        ],
    )


def _install_readonly_test_overrides(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> _FakeDbSession:
    """Install dependency and service overrides for deterministic read-only assertions."""

    import app.portfolio_news_context.service as news_service
    import app.portfolio_rebalancing.service as rebalancing_service

    fake_db = _FakeDbSession()
    fixed_summary = _fixed_summary_response()
    fixed_now = datetime(2026, 4, 6, 12, 5, tzinfo=UTC)

    async def _fake_summary_response(**_: object) -> PortfolioSummaryResponse:
        return fixed_summary

    async def _override_get_db() -> _FakeDbSession:
        return fake_db

    monkeypatch.setattr(
        rebalancing_service,
        "get_portfolio_summary_response",
        _fake_summary_response,
    )
    monkeypatch.setattr(
        news_service,
        "get_portfolio_summary_response",
        _fake_summary_response,
    )
    monkeypatch.setattr(rebalancing_service, "utcnow", lambda: fixed_now)
    monkeypatch.setattr(news_service, "utcnow", lambda: fixed_now)

    app.dependency_overrides[get_db] = _override_get_db
    return fake_db


@pytest.mark.integration
def test_rebalancing_and_news_endpoints_are_deterministic_and_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Equivalent input state should return stable payloads without write-side effects."""

    fake_db = _install_readonly_test_overrides(monkeypatch=monkeypatch)
    settings = get_settings()
    rebalancing_path = f"{settings.api_prefix}/portfolio/rebalancing/strategies"
    news_path = f"{settings.api_prefix}/portfolio/news/context"

    try:
        with TestClient(app) as client:
            first_rebalancing = client.get(rebalancing_path)
            second_rebalancing = client.get(rebalancing_path)
            first_news = client.get(news_path)
            second_news = client.get(news_path)
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert first_rebalancing.status_code == 200
    assert second_rebalancing.status_code == 200
    assert first_news.status_code == 200
    assert second_news.status_code == 200

    assert first_rebalancing.json() == second_rebalancing.json()
    assert first_news.json() == second_news.json()
    assert fake_db.commit_calls == 0
    assert fake_db.flush_calls == 0


@pytest.mark.integration
def test_rebalancing_scenario_returns_explicit_infeasible_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Infeasible constraints should return explicit metadata and no fabricated weights."""

    fake_db = _install_readonly_test_overrides(monkeypatch=monkeypatch)
    settings = get_settings()
    scenario_path = f"{settings.api_prefix}/portfolio/rebalancing/scenario"

    try:
        with TestClient(app) as client:
            response = client.post(
                scenario_path,
                json={
                    "constraints": {
                        "max_position_weight_pct": "20.0",
                    }
                },
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "infeasible"
    assert payload["state_reason_code"] == "constraint_set_infeasible"
    assert payload["infeasible_cause"] == "max_position_weight_infeasible"
    assert payload["constrained_strategies"] == []
    assert len(payload["baseline_strategies"]) > 0
    assert fake_db.commit_calls == 0
    assert fake_db.flush_calls == 0
