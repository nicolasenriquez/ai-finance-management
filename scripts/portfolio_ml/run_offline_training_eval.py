"""Run offline portfolio_ml forecast evaluation and optional registry inspection."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Literal

from app.core.database import AsyncSessionLocal
from app.portfolio_ml.schemas import PortfolioMLScope
from app.portfolio_ml.service import (
    PortfolioMLClientError,
    get_portfolio_ml_forecast_response,
    get_portfolio_ml_registry_response,
)


def _parse_args() -> argparse.Namespace:
    """Parse bounded CLI arguments for offline portfolio_ml workflow execution."""

    parser = argparse.ArgumentParser(
        description=(
            "Run offline portfolio_ml forecast evaluation and optionally inspect "
            "registry rows using allowlisted filters."
        ),
    )
    parser.add_argument(
        "--scope",
        choices=["portfolio", "instrument_symbol"],
        default="portfolio",
        help="Forecast scope to evaluate.",
    )
    parser.add_argument(
        "--instrument-symbol",
        default=None,
        help="Instrument symbol required when scope=instrument_symbol.",
    )
    parser.add_argument(
        "--include-registry",
        action="store_true",
        help="Fetch registry rows after forecast evaluation.",
    )
    parser.add_argument(
        "--registry-model-family",
        default=None,
        help="Optional registry model_family filter.",
    )
    parser.add_argument(
        "--registry-lifecycle-state",
        choices=["ready", "unavailable", "stale", "error"],
        default=None,
        help="Optional registry lifecycle_state filter.",
    )
    return parser.parse_args()


def _normalize_scope(*, scope: str) -> PortfolioMLScope:
    """Normalize CLI scope token to typed portfolio_ml scope."""

    normalized_scope = scope.strip().lower()
    if normalized_scope == PortfolioMLScope.PORTFOLIO.value:
        return PortfolioMLScope.PORTFOLIO
    if normalized_scope == PortfolioMLScope.INSTRUMENT_SYMBOL.value:
        return PortfolioMLScope.INSTRUMENT_SYMBOL
    raise ValueError("Unsupported --scope value.")


def _normalize_instrument_symbol(
    *,
    scope: PortfolioMLScope,
    instrument_symbol: str | None,
) -> str | None:
    """Normalize instrument symbol and enforce scope symmetry."""

    if scope == PortfolioMLScope.PORTFOLIO:
        return None
    if instrument_symbol is None or instrument_symbol.strip() == "":
        raise ValueError("--instrument-symbol is required when --scope=instrument_symbol.")
    return instrument_symbol.strip().upper()


async def _run_workflow(
    *,
    scope: PortfolioMLScope,
    instrument_symbol: str | None,
    include_registry: bool,
    registry_model_family: str | None,
    registry_lifecycle_state: Literal["ready", "unavailable", "stale", "error"] | None,
) -> int:
    """Execute one offline forecast and optional registry inspection workflow."""

    async with AsyncSessionLocal() as db:
        forecast_response = await get_portfolio_ml_forecast_response(
            scope=scope,
            instrument_symbol=instrument_symbol,
            db=db,
        )
        print("# Forecast Response")
        print(json.dumps(forecast_response.model_dump(mode="json"), indent=2, sort_keys=True))

        if not include_registry:
            return 0

        registry_response = await get_portfolio_ml_registry_response(
            db=db,
            scope=scope.value,
            model_family=registry_model_family,
            lifecycle_state=registry_lifecycle_state,
        )
        print("\n# Registry Response")
        print(json.dumps(registry_response.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


def main() -> int:
    """Run CLI entrypoint for offline portfolio_ml workflow commands."""

    args = _parse_args()
    try:
        scope = _normalize_scope(scope=str(args.scope))
        instrument_symbol = _normalize_instrument_symbol(
            scope=scope,
            instrument_symbol=args.instrument_symbol,
        )
    except ValueError as exc:
        print(f"Argument error: {exc}")
        return 2

    try:
        return asyncio.run(
            _run_workflow(
                scope=scope,
                instrument_symbol=instrument_symbol,
                include_registry=bool(args.include_registry),
                registry_model_family=args.registry_model_family,
                registry_lifecycle_state=args.registry_lifecycle_state,
            )
        )
    except PortfolioMLClientError as exc:
        print(f"portfolio_ml workflow failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
