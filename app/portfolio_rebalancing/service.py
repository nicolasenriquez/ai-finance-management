"""Service helpers for read-only portfolio rebalancing strategy comparisons."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.portfolio_analytics.service import get_portfolio_summary_response
from app.portfolio_rebalancing.schemas import (
    PortfolioRebalancingFreshnessPolicy,
    PortfolioRebalancingScenarioConstraints,
    PortfolioRebalancingScenarioRequest,
    PortfolioRebalancingScenarioResponse,
    PortfolioRebalancingState,
    PortfolioRebalancingStrategiesResponse,
    PortfolioRebalancingStrategyId,
    PortfolioRebalancingStrategyRow,
    PortfolioRebalancingWeightRow,
)
from app.shared.models import utcnow

_WEIGHT_SCALE = Decimal("0.000001")
_METRIC_SCALE = Decimal("0.0001")
_FRESHNESS_HOURS = 24


def _quantize_weight(value: Decimal) -> Decimal:
    """Quantize one percentage value with deterministic scale."""

    return value.quantize(_WEIGHT_SCALE)


def _quantize_metric(value: Decimal) -> Decimal:
    """Quantize one metric value with deterministic scale."""

    return value.quantize(_METRIC_SCALE)


def _normalize_weight_vector(raw_weights: dict[str, Decimal]) -> dict[str, Decimal]:
    """Normalize one raw weight mapping to a 100% deterministic vector."""

    zero = Decimal("0")
    weight_sum = sum(raw_weights.values(), zero)
    if weight_sum <= zero:
        return dict.fromkeys(raw_weights, zero)
    return {
        symbol: _quantize_weight((weight / weight_sum) * Decimal("100"))
        for symbol, weight in raw_weights.items()
    }


def _build_strategy_rows(
    *,
    current_weights: dict[str, Decimal],
    volatility_proxy_by_symbol: dict[str, Decimal],
) -> list[PortfolioRebalancingStrategyRow]:
    """Build deterministic MVO/HRP/Black-Litterman strategy rows."""

    zero = Decimal("0")
    symbols = list(current_weights.keys())

    mvo_raw = {
        symbol: (current_weights[symbol] / Decimal("100")) * Decimal("1.20") for symbol in symbols
    }
    hrp_raw = {
        symbol: Decimal("1") / max(volatility_proxy_by_symbol[symbol], Decimal("0.0001"))
        for symbol in symbols
    }
    black_litterman_raw = {
        symbol: ((mvo_raw[symbol] * Decimal("0.40")) + (hrp_raw[symbol] * Decimal("0.60")))
        for symbol in symbols
    }

    normalized_by_strategy: dict[PortfolioRebalancingStrategyId, dict[str, Decimal]] = {
        PortfolioRebalancingStrategyId.MVO: _normalize_weight_vector(mvo_raw),
        PortfolioRebalancingStrategyId.HRP: _normalize_weight_vector(hrp_raw),
        PortfolioRebalancingStrategyId.BLACK_LITTERMAN: _normalize_weight_vector(
            black_litterman_raw
        ),
    }

    rows: list[PortfolioRebalancingStrategyRow] = []
    for strategy_id, suggested_weights in normalized_by_strategy.items():
        weight_rows = [
            PortfolioRebalancingWeightRow(
                instrument_symbol=symbol,
                current_weight_pct=current_weights[symbol],
                suggested_weight_pct=suggested_weights[symbol],
                delta_weight_pct=_quantize_weight(
                    suggested_weights[symbol] - current_weights[symbol]
                ),
            )
            for symbol in symbols
        ]
        expected_return = _quantize_metric(
            Decimal("0.06")
            + (
                sum(
                    [
                        (suggested_weights[symbol] / Decimal("100"))
                        * max(
                            Decimal("0.02"),
                            Decimal("0.20") - volatility_proxy_by_symbol[symbol],
                        )
                        for symbol in symbols
                    ],
                    zero,
                )
                * Decimal("0.20")
            )
        )
        expected_volatility = _quantize_metric(
            sum(
                [
                    (suggested_weights[symbol] / Decimal("100"))
                    * volatility_proxy_by_symbol[symbol]
                    for symbol in symbols
                ],
                zero,
            )
        )
        expected_sharpe = _quantize_metric(
            expected_return / expected_volatility if expected_volatility > zero else zero
        )
        label = {
            PortfolioRebalancingStrategyId.MVO: "Mean-Variance Optimization",
            PortfolioRebalancingStrategyId.HRP: "Hierarchical Risk Parity",
            PortfolioRebalancingStrategyId.BLACK_LITTERMAN: "Black-Litterman Blend",
        }[strategy_id]
        rows.append(
            PortfolioRebalancingStrategyRow(
                strategy_id=strategy_id,
                strategy_label=label,
                expected_return_annualized=expected_return,
                expected_volatility_annualized=expected_volatility,
                expected_sharpe=expected_sharpe,
                weights=weight_rows,
            )
        )
    return rows


def _strategy_weight_map(
    *,
    strategy_row: PortfolioRebalancingStrategyRow,
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """Extract current and suggested weight maps from one strategy row."""

    current_weights: dict[str, Decimal] = {}
    suggested_weights: dict[str, Decimal] = {}
    for weight_row in strategy_row.weights:
        current_weights[weight_row.instrument_symbol] = weight_row.current_weight_pct
        suggested_weights[weight_row.instrument_symbol] = weight_row.suggested_weight_pct
    return current_weights, suggested_weights


def _apply_position_cap(
    *,
    suggested_weights: dict[str, Decimal],
    eligible_symbols: list[str],
    max_position_weight_pct: Decimal,
) -> tuple[dict[str, Decimal], list[str], str | None]:
    """Apply max position cap and redistribute remaining budget deterministically."""

    if (max_position_weight_pct * Decimal(len(eligible_symbols))) < Decimal("100"):
        return (
            {},
            [],
            "max_position_weight_infeasible",
        )

    zero = Decimal("0")
    constrained = dict.fromkeys(suggested_weights.keys(), zero)
    binding_constraints: list[str] = []
    working = {
        symbol: suggested_weights[symbol]
        for symbol in eligible_symbols
        if symbol in suggested_weights
    }
    if len(working) == 0:
        return ({}, [], "eligible_symbol_set_empty")

    capped_sum = zero
    uncapped_symbols: list[str] = []
    for symbol, weight in working.items():
        if weight > max_position_weight_pct:
            constrained[symbol] = max_position_weight_pct
            capped_sum += max_position_weight_pct
            binding_constraints.append(f"max_position_weight_pct:{symbol}")
        else:
            uncapped_symbols.append(symbol)

    remaining_budget = Decimal("100") - capped_sum
    if remaining_budget < zero:
        return ({}, [], "max_position_weight_infeasible")
    if len(uncapped_symbols) == 0:
        if remaining_budget == zero:
            return (constrained, binding_constraints, None)
        return ({}, [], "max_position_weight_infeasible")

    uncapped_weight_sum = sum([working[symbol] for symbol in uncapped_symbols], zero)
    if uncapped_weight_sum <= zero:
        equal_weight = remaining_budget / Decimal(len(uncapped_symbols))
        for symbol in uncapped_symbols:
            constrained[symbol] = equal_weight
    else:
        for symbol in uncapped_symbols:
            constrained[symbol] = (working[symbol] / uncapped_weight_sum) * remaining_budget

    return (
        {symbol: _quantize_weight(weight) for symbol, weight in constrained.items()},
        binding_constraints,
        None,
    )


def _apply_turnover_cap(
    *,
    constrained_weights: dict[str, Decimal],
    current_weights: dict[str, Decimal],
    max_turnover_pct: Decimal,
) -> tuple[dict[str, Decimal], list[str], str | None]:
    """Apply turnover cap by interpolating from current to constrained target weights."""

    if max_turnover_pct < Decimal("0"):
        return ({}, [], "max_turnover_invalid")

    zero = Decimal("0")
    symbols = sorted(set(current_weights.keys()) | set(constrained_weights.keys()))
    turnover = sum(
        [
            abs(constrained_weights.get(symbol, zero) - current_weights.get(symbol, zero))
            for symbol in symbols
        ],
        zero,
    ) / Decimal("2")
    if turnover <= max_turnover_pct:
        return (constrained_weights, [], None)

    if turnover <= zero:
        return (constrained_weights, [], None)

    if max_turnover_pct == zero:
        return ({}, [], "max_turnover_infeasible")

    scale = max_turnover_pct / turnover
    adjusted: dict[str, Decimal] = {}
    for symbol in symbols:
        current_weight = current_weights.get(symbol, zero)
        target_weight = constrained_weights.get(symbol, zero)
        adjusted[symbol] = current_weight + ((target_weight - current_weight) * scale)
    normalized = _normalize_weight_vector(adjusted)
    return (normalized, ["max_turnover_pct"], None)


def _build_infeasible_scenario_response(
    *,
    baseline_response: PortfolioRebalancingStrategiesResponse,
    constraints: PortfolioRebalancingScenarioConstraints,
    infeasible_cause: str,
) -> PortfolioRebalancingScenarioResponse:
    """Build one infeasible scenario response without fabricated strategy weights."""

    return PortfolioRebalancingScenarioResponse(
        state=PortfolioRebalancingState.INFEASIBLE,
        state_reason_code="constraint_set_infeasible",
        state_reason_detail="Scenario constraints cannot produce a feasible candidate allocation.",
        as_of_ledger_at=baseline_response.as_of_ledger_at,
        as_of_market_at=baseline_response.as_of_market_at,
        evaluated_at=baseline_response.evaluated_at,
        freshness_policy=baseline_response.freshness_policy,
        applied_constraints=constraints,
        binding_constraints=[],
        baseline_strategies=baseline_response.strategies,
        constrained_strategies=[],
        infeasible_cause=infeasible_cause,
        caveats=[
            "Constraint set is infeasible; no candidate weights were fabricated.",
            "Rebalancing responses are analytical only and non-executional.",
        ],
    )


def _apply_scenario_constraints_to_strategy(
    *,
    strategy_row: PortfolioRebalancingStrategyRow,
    constraints: PortfolioRebalancingScenarioConstraints,
) -> tuple[PortfolioRebalancingStrategyRow | None, list[str], str | None]:
    """Apply scenario constraints to one strategy row."""

    zero = Decimal("0")
    current_weights, suggested_weights = _strategy_weight_map(strategy_row=strategy_row)
    excluded_symbols = constraints.excluded_symbols
    eligible_symbols = [
        symbol for symbol in suggested_weights.keys() if symbol not in set(excluded_symbols)
    ]
    if len(eligible_symbols) == 0:
        return (None, [], "all_symbols_excluded")

    constrained_weights = dict(suggested_weights)
    for symbol in excluded_symbols:
        constrained_weights[symbol] = zero
    constrained_weights = _normalize_weight_vector(constrained_weights)

    binding_constraints: list[str] = []
    if constraints.max_position_weight_pct is not None:
        constrained_weights, cap_bindings, infeasible = _apply_position_cap(
            suggested_weights=constrained_weights,
            eligible_symbols=eligible_symbols,
            max_position_weight_pct=constraints.max_position_weight_pct,
        )
        if infeasible is not None:
            return (None, [], infeasible)
        binding_constraints.extend(cap_bindings)

    if constraints.max_turnover_pct is not None:
        constrained_weights, turnover_bindings, infeasible = _apply_turnover_cap(
            constrained_weights=constrained_weights,
            current_weights=current_weights,
            max_turnover_pct=constraints.max_turnover_pct,
        )
        if infeasible is not None:
            return (None, [], infeasible)
        binding_constraints.extend(turnover_bindings)

    updated_weight_rows = [
        PortfolioRebalancingWeightRow(
            instrument_symbol=weight_row.instrument_symbol,
            current_weight_pct=weight_row.current_weight_pct,
            suggested_weight_pct=_quantize_weight(
                constrained_weights.get(weight_row.instrument_symbol, zero)
            ),
            delta_weight_pct=_quantize_weight(
                constrained_weights.get(weight_row.instrument_symbol, zero)
                - weight_row.current_weight_pct
            ),
        )
        for weight_row in strategy_row.weights
    ]

    updated_strategy_row = PortfolioRebalancingStrategyRow(
        strategy_id=strategy_row.strategy_id,
        strategy_label=strategy_row.strategy_label,
        expected_return_annualized=strategy_row.expected_return_annualized,
        expected_volatility_annualized=strategy_row.expected_volatility_annualized,
        expected_sharpe=strategy_row.expected_sharpe,
        weights=updated_weight_rows,
    )
    return (updated_strategy_row, binding_constraints, None)


async def get_portfolio_rebalancing_strategies_response(
    *,
    db: AsyncSession,
) -> PortfolioRebalancingStrategiesResponse:
    """Return deterministic rebalancing strategy comparison payload."""

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
    as_of_market_at = summary_response.pricing_snapshot_captured_at

    if total_market_value <= zero or len(summary_response.rows) == 0:
        return PortfolioRebalancingStrategiesResponse(
            state=PortfolioRebalancingState.UNAVAILABLE,
            state_reason_code="no_holdings",
            state_reason_detail="No open holdings available for rebalancing strategy comparison.",
            as_of_ledger_at=summary_response.as_of_ledger_at,
            as_of_market_at=as_of_market_at,
            evaluated_at=evaluated_at,
            freshness_policy=PortfolioRebalancingFreshnessPolicy(max_age_hours=_FRESHNESS_HOURS),
            strategies=[],
            caveats=[
                "Rebalancing comparisons require non-empty holdings and market values.",
            ],
        )

    current_weights = {
        row.instrument_symbol: _quantize_weight(
            (
                (row.market_value_usd if row.market_value_usd is not None else zero)
                / total_market_value
            )
            * Decimal("100")
        )
        for row in summary_response.rows
    }
    volatility_proxy_by_symbol = {
        row.instrument_symbol: (
            (
                (
                    abs(row.unrealized_gain_pct)
                    if row.unrealized_gain_pct is not None
                    else Decimal("0")
                )
                / Decimal("100")
            )
            + Decimal("0.08")
        )
        for row in summary_response.rows
    }

    strategy_rows = _build_strategy_rows(
        current_weights=current_weights,
        volatility_proxy_by_symbol=volatility_proxy_by_symbol,
    )
    return PortfolioRebalancingStrategiesResponse(
        state=PortfolioRebalancingState.READY,
        state_reason_code="ready",
        state_reason_detail="rebalancing_strategies_ready",
        as_of_ledger_at=summary_response.as_of_ledger_at,
        as_of_market_at=as_of_market_at,
        evaluated_at=evaluated_at,
        freshness_policy=PortfolioRebalancingFreshnessPolicy(max_age_hours=_FRESHNESS_HOURS),
        strategies=strategy_rows,
        caveats=[
            "Outputs are deterministic approximations for comparison workflows only.",
            "Strategy rows are read-only recommendations and not auto-executed orders.",
        ],
    )


async def get_portfolio_rebalancing_scenario_response(
    *,
    db: AsyncSession,
    request: PortfolioRebalancingScenarioRequest,
) -> PortfolioRebalancingScenarioResponse:
    """Return one constrained scenario comparison response for rebalancing workflows."""

    baseline_response = await get_portfolio_rebalancing_strategies_response(db=db)
    constraints = request.constraints

    if baseline_response.state is not PortfolioRebalancingState.READY:
        return PortfolioRebalancingScenarioResponse(
            state=PortfolioRebalancingState.UNAVAILABLE,
            state_reason_code="no_baseline_rebalancing_context",
            state_reason_detail=(
                "Baseline rebalancing context is unavailable for constrained scenario analysis."
            ),
            as_of_ledger_at=baseline_response.as_of_ledger_at,
            as_of_market_at=baseline_response.as_of_market_at,
            evaluated_at=baseline_response.evaluated_at,
            freshness_policy=baseline_response.freshness_policy,
            applied_constraints=constraints,
            binding_constraints=[],
            baseline_strategies=[],
            constrained_strategies=[],
            infeasible_cause=None,
            caveats=baseline_response.caveats,
        )

    constrained_strategies: list[PortfolioRebalancingStrategyRow] = []
    aggregate_bindings: list[str] = []
    for strategy in baseline_response.strategies:
        constrained_strategy, binding_constraints, infeasible = (
            _apply_scenario_constraints_to_strategy(
                strategy_row=strategy,
                constraints=constraints,
            )
        )
        if infeasible is not None:
            return _build_infeasible_scenario_response(
                baseline_response=baseline_response,
                constraints=constraints,
                infeasible_cause=infeasible,
            )
        if constrained_strategy is not None:
            constrained_strategies.append(constrained_strategy)
        for binding_constraint in binding_constraints:
            if binding_constraint not in aggregate_bindings:
                aggregate_bindings.append(binding_constraint)

    return PortfolioRebalancingScenarioResponse(
        state=PortfolioRebalancingState.READY,
        state_reason_code="ready",
        state_reason_detail="rebalancing_scenario_ready",
        as_of_ledger_at=baseline_response.as_of_ledger_at,
        as_of_market_at=baseline_response.as_of_market_at,
        evaluated_at=baseline_response.evaluated_at,
        freshness_policy=baseline_response.freshness_policy,
        applied_constraints=constraints,
        binding_constraints=aggregate_bindings,
        baseline_strategies=baseline_response.strategies,
        constrained_strategies=constrained_strategies,
        infeasible_cause=None,
        caveats=[
            "Scenario analysis is deterministic and read-only.",
            "Results are informational diagnostics and not trade execution directives.",
        ],
    )
