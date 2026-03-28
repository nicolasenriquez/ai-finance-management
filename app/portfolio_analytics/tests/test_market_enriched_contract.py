"""Fail-first contract tests for market-enriched portfolio summary schemas."""

from __future__ import annotations

from collections.abc import Iterable

from app.portfolio_analytics.schemas import (
    PortfolioSummaryResponse,
    PortfolioSummaryRow,
)


def _assert_fields_present(*, actual: Iterable[str], required: set[str]) -> None:
    """Assert required fields exist in one schema field set."""

    actual_set = set(actual)
    missing = required - actual_set
    assert not missing, f"Missing required fields: {sorted(missing)}"


def test_summary_row_schema_requires_market_enriched_fields() -> None:
    """Summary row schema should include bounded market-enriched valuation fields."""

    _assert_fields_present(
        actual=PortfolioSummaryRow.model_fields.keys(),
        required={
            "latest_close_price_usd",
            "market_value_usd",
            "unrealized_gain_usd",
            "unrealized_gain_pct",
        },
    )


def test_summary_response_schema_requires_pricing_snapshot_provenance() -> None:
    """Summary response schema should include explicit pricing snapshot provenance."""

    _assert_fields_present(
        actual=PortfolioSummaryResponse.model_fields.keys(),
        required={
            "pricing_snapshot_key",
            "pricing_snapshot_captured_at",
        },
    )
