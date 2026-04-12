"""Service helpers for holdings-grounded portfolio news context responses."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.portfolio_analytics.service import get_portfolio_summary_response
from app.portfolio_news_context.schemas import (
    PortfolioNewsContextResponse,
    PortfolioNewsContextRow,
    PortfolioNewsContextState,
    PortfolioNewsFreshnessPolicy,
    PortfolioNewsSourceRow,
)
from app.shared.models import utcnow

_WEIGHT_SCALE = Decimal("0.000001")
_FRESHNESS_HOURS = 24


def _quantize_weight(value: Decimal) -> Decimal:
    """Quantize one weight percentage for deterministic rendering."""

    return value.quantize(_WEIGHT_SCALE)


def _source_rows_for_symbol(
    *,
    symbol: str,
    evaluated_at: datetime,
) -> list[PortfolioNewsSourceRow]:
    """Build deterministic source provenance rows for one symbol."""

    published = evaluated_at - timedelta(hours=2)

    return [
        PortfolioNewsSourceRow(
            source_id=f"{symbol.lower()}_newswire",
            source_label="Market Newswire",
            published_at=published,
            url=f"https://example.com/news/{symbol.lower()}",
        ),
    ]


async def get_portfolio_news_context_response(
    *,
    db: AsyncSession,
) -> PortfolioNewsContextResponse:
    """Return holdings-grounded news context with deterministic source provenance."""

    summary_response = await get_portfolio_summary_response(db=db)
    evaluated_at = utcnow()
    zero = Decimal("0")
    total_market_value = sum(
        [
            row.market_value_usd if row.market_value_usd is not None else zero
            for row in summary_response.rows
        ],
        zero,
    )
    if total_market_value <= zero or len(summary_response.rows) == 0:
        return PortfolioNewsContextResponse(
            state=PortfolioNewsContextState.UNAVAILABLE,
            state_reason_code="no_holdings",
            state_reason_detail="No holdings available for symbol-grounded news context.",
            as_of_ledger_at=summary_response.as_of_ledger_at,
            as_of_market_at=summary_response.pricing_snapshot_captured_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioNewsFreshnessPolicy(max_age_hours=_FRESHNESS_HOURS),
            rows=[],
        )

    top_rows = sorted(
        summary_response.rows,
        key=lambda row: row.market_value_usd if row.market_value_usd is not None else zero,
        reverse=True,
    )[:5]
    context_rows: list[PortfolioNewsContextRow] = []
    for row in top_rows:
        market_value = row.market_value_usd if row.market_value_usd is not None else zero
        weight_pct = _quantize_weight((market_value / total_market_value) * Decimal("100"))
        gain_pct = row.unrealized_gain_pct if row.unrealized_gain_pct is not None else zero
        impact_bias = "positive" if gain_pct >= zero else "negative"
        context_rows.append(
            PortfolioNewsContextRow(
                instrument_symbol=row.instrument_symbol,
                market_value_weight_pct=weight_pct,
                summary=(
                    f"{row.instrument_symbol} remains a top portfolio weight. "
                    "Recent market headlines may amplify short-term move interpretation."
                ),
                impact_bias=impact_bias,
                caveats=[
                    "News summaries are contextual and do not imply trade recommendations.",
                    "Source latency can vary by instrument and provider.",
                ],
                sources=_source_rows_for_symbol(
                    symbol=row.instrument_symbol,
                    evaluated_at=evaluated_at,
                ),
            )
        )

    return PortfolioNewsContextResponse(
        state=PortfolioNewsContextState.READY,
        state_reason_code="ready",
        state_reason_detail="news_context_ready",
        as_of_ledger_at=summary_response.as_of_ledger_at,
        as_of_market_at=summary_response.pricing_snapshot_captured_at,
        evaluated_at=evaluated_at,
        freshness_policy=PortfolioNewsFreshnessPolicy(max_age_hours=_FRESHNESS_HOURS),
        rows=context_rows,
    )
