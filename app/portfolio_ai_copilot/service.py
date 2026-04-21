"""Service orchestration for read-only portfolio AI copilot workflows."""

from __future__ import annotations

import asyncio
import json
import math
import re
import statistics
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import cast

from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.market_data.service import (
    MarketDataClientError,
    list_market_data_library_symbols,
    list_price_history_for_symbol,
)
from app.pdf_persistence.models import SourceDocument
from app.portfolio_ai_copilot.provider_groq import (
    GroqProviderError,
    build_groq_chat_completions_adapter_config,
    request_groq_chat_completion,
)
from app.portfolio_ai_copilot.schemas import (
    CopilotEvidenceReference,
    CopilotFundamentalsProxyState,
    CopilotOperation,
    CopilotOpportunityActionState,
    CopilotOpportunityCandidate,
    CopilotOpportunityStrategyProfile,
    CopilotReasonCode,
    CopilotResponseState,
    PortfolioCopilotChatRequest,
    PortfolioCopilotChatResponse,
)
from app.portfolio_analytics.schemas import (
    PortfolioChartPeriod,
    PortfolioHealthProfilePosture,
    PortfolioHierarchyGroupBy,
    PortfolioMonteCarloCalibrationBasis,
    PortfolioMonteCarloRequest,
    PortfolioQuantReportScope,
)
from app.portfolio_analytics.service import (
    PortfolioAnalyticsClientError,
    generate_portfolio_monte_carlo_response,
    get_portfolio_contribution_response,
    get_portfolio_health_synthesis_response,
    get_portfolio_hierarchy_response,
    get_portfolio_quant_metrics_response,
    get_portfolio_return_distribution_response,
    get_portfolio_risk_estimators_response,
    get_portfolio_risk_evolution_response,
    get_portfolio_summary_response,
    get_portfolio_time_series_response,
)
from app.portfolio_ml.schemas import PortfolioMLScope, PortfolioMLState
from app.portfolio_ml.service import (
    PortfolioMLClientError,
    get_portfolio_ml_forecast_response,
    get_portfolio_ml_registry_response,
    get_portfolio_ml_signal_response,
)

logger = get_logger(__name__)

MODEL_CONTEXT_EXCLUDED_FIELDS: frozenset[str] = frozenset(
    {
        "raw_payload",
        "source_payload",
        "canonical_payload",
        "transaction_events",
        "provider_secret",
        "api_key",
        "authorization",
    }
)

_MAX_TOOL_CALLS = 6
_MIN_OPPORTUNITY_ELIGIBLE_COUNT = 20
_MIN_OPPORTUNITY_HISTORY_POINTS = 90
_OPPORTUNITY_52W_WINDOW_POINTS = 252
_DOUBLE_DOWN_THRESHOLD_PCT_DEFAULT = Decimal("0.20")
_DOUBLE_DOWN_MULTIPLIER_DEFAULT = Decimal("2.0")
_FUNDAMENTALS_PROXY_MIN_PASS_COUNT = 2
_FUNDAMENTALS_PROXY_MAX_30D_DRAWDOWN = Decimal("-0.25")
_FUNDAMENTALS_PROXY_MAX_90D_DRAWDOWN = Decimal("-0.35")
_FUNDAMENTALS_PROXY_MAX_30D_VOLATILITY = Decimal("0.060000")
_BOUNDARY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(buy|sell|short|rebalance|auto(?:matically)?|execute)\b", re.IGNORECASE
    ),
    re.compile(r"\b(place|submit)\s+(a\s+)?(trade|order)\b", re.IGNORECASE),
    re.compile(
        r"\b(guarantee|guaranteed|risk[-\s]?free|certain return)\b", re.IGNORECASE
    ),
    re.compile(
        r"\b(raw payload|canonical payload|source payload|transaction events?)\b",
        re.IGNORECASE,
    ),
)

_RISK_WINDOW_BY_PERIOD: dict[PortfolioChartPeriod, int] = {
    PortfolioChartPeriod.D30: 30,
    PortfolioChartPeriod.D90: 90,
    PortfolioChartPeriod.D6M: 126,
    PortfolioChartPeriod.D252: 252,
    PortfolioChartPeriod.YTD: 252,
    PortfolioChartPeriod.MAX: 252,
}

_QUANTIZE_6DP = Decimal("0.000001")
_MAX_DOCUMENT_REFERENCES = 8
_MAX_PROMPT_SUGGESTIONS = 4
_GOVERNED_SQL_DEFAULT_MAX_ROWS = 25
_GOVERNED_SQL_MAX_ROWS_CAP = 50
_GOVERNED_SQL_TIMEOUT_SECONDS = 2.0

_GOVERNED_SQL_LATEST_FORECAST_STATES = """
SELECT
    snapshot_ref,
    scope,
    instrument_symbol,
    model_family,
    lifecycle_state,
    run_status,
    promoted_at,
    expires_at
FROM portfolio_ml_model_snapshot
WHERE (:scope IS NULL OR scope = :scope)
  AND (:lifecycle_state IS NULL OR lifecycle_state = :lifecycle_state)
ORDER BY promoted_at DESC NULLS LAST, id DESC
LIMIT :limit_rows
"""


class PortfolioAiCopilotClientError(ValueError):
    """Raised when copilot request cannot be processed within v1 boundaries."""

    status_code: int
    reason_code: CopilotReasonCode

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        reason_code: CopilotReasonCode,
    ) -> None:
        """Initialize one typed copilot client error."""

        super().__init__(message)
        self.status_code = status_code
        self.reason_code = reason_code


@dataclass(frozen=True)
class _CopilotToolDefinition:
    """One allowlisted tool definition for portfolio copilot orchestration."""

    tool_id: str
    metric_id: str
    execute: Callable[[AsyncSession, PortfolioCopilotChatRequest], Awaitable[object]]


@dataclass(frozen=True)
class _ToolExecutionResult:
    """One executed tool result bundle used for evidence and prompt assembly."""

    tool_id: str
    metric_id: str
    payload: dict[str, object]
    as_of_ledger_at: str | None


@dataclass(frozen=True)
class _OpportunityCandidateInput:
    """One normalized deterministic-opportunity candidate input row."""

    symbol: str
    latest_close_price_usd: Decimal
    rolling_90d_high_price_usd: Decimal
    rolling_52w_high_price_usd: Decimal
    drawdown_from_52w_high_pct: Decimal
    return_30d: Decimal
    return_90d: Decimal
    return_252d: Decimal
    volatility_30d: Decimal
    history_points_count: int
    currently_held: bool


@dataclass(frozen=True)
class _GovernedSqlTemplate:
    """One allowlisted governed SQL template contract."""

    template_id: str
    sql_text: str
    default_max_rows: int
    max_rows_cap: int
    timeout_seconds: float


def sanitize_model_context_payload(
    *, context_payload: dict[str, object]
) -> dict[str, object]:
    """Remove excluded raw/private fields recursively from model-visible context payload."""

    sanitized_payload = _sanitize_context_value(value=context_payload)
    if not isinstance(sanitized_payload, dict):
        return {}
    return cast(dict[str, object], sanitized_payload)


def _sanitize_context_value(*, value: object) -> object:
    """Sanitize one arbitrary value recursively for model prompt visibility."""

    if isinstance(value, dict):
        typed_mapping = cast(dict[str, object], value)
        sanitized_mapping: dict[str, object] = {}
        for key, raw_item in typed_mapping.items():
            if key.lower() in MODEL_CONTEXT_EXCLUDED_FIELDS:
                continue
            sanitized_mapping[key] = _sanitize_context_value(value=raw_item)
        return sanitized_mapping
    if isinstance(value, list):
        typed_list = cast(list[object], value)
        return [_sanitize_context_value(value=item) for item in typed_list]
    return value


def classify_copilot_boundary_violation_reason(*, user_message: str) -> str | None:
    """Return one blocked boundary reason for unsafe asks, otherwise return None."""

    normalized_message = user_message.strip()
    if not normalized_message:
        return "boundary_restricted"

    for boundary_pattern in _BOUNDARY_PATTERNS:
        if boundary_pattern.search(normalized_message):
            return CopilotReasonCode.BOUNDARY_RESTRICTED.value
    return None


def enforce_copilot_request_boundary(*, user_message: str) -> None:
    """Raise typed client error when one user request violates read-only boundaries."""

    violation_reason = classify_copilot_boundary_violation_reason(
        user_message=user_message
    )
    if violation_reason is None:
        return
    raise PortfolioAiCopilotClientError(
        "Request exceeds read-only copilot boundary.",
        status_code=422,
        reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
    )


def map_provider_failure_to_copilot_state(
    *,
    status_code: int | None,
    provider_error_code: str | None,
    error_type: str | None,
) -> dict[str, str]:
    """Normalize provider/runtime failures to stable copilot state + reason codes."""

    normalized_provider_error_code = (provider_error_code or "").strip().lower()
    normalized_error_type = (error_type or "").strip().lower()

    if status_code == 429:
        return {
            "state": CopilotResponseState.ERROR.value,
            "reason_code": CopilotReasonCode.RATE_LIMITED.value,
        }
    if status_code == 403:
        return {
            "state": CopilotResponseState.BLOCKED.value,
            "reason_code": CopilotReasonCode.PROVIDER_BLOCKED_POLICY.value,
        }
    if status_code in {400, 401, 404, 422}:
        return {
            "state": CopilotResponseState.ERROR.value,
            "reason_code": CopilotReasonCode.PROVIDER_MISCONFIGURED.value,
        }
    if normalized_provider_error_code in {
        "invalid_api_key",
        "model_not_found",
        "model_not_allowlisted",
        "missing_api_key",
        "missing_model",
        "missing_model_allowlist",
        "missing_base_url",
    }:
        return {
            "state": CopilotResponseState.ERROR.value,
            "reason_code": CopilotReasonCode.PROVIDER_MISCONFIGURED.value,
        }
    if "auth" in normalized_error_type or "configuration" in normalized_error_type:
        return {
            "state": CopilotResponseState.ERROR.value,
            "reason_code": CopilotReasonCode.PROVIDER_MISCONFIGURED.value,
        }
    if status_code is not None and status_code >= 500:
        return {
            "state": CopilotResponseState.ERROR.value,
            "reason_code": CopilotReasonCode.PROVIDER_UNAVAILABLE.value,
        }
    if "timeout" in normalized_error_type or "transport" in normalized_error_type:
        return {
            "state": CopilotResponseState.ERROR.value,
            "reason_code": CopilotReasonCode.PROVIDER_UNAVAILABLE.value,
        }
    return {
        "state": CopilotResponseState.ERROR.value,
        "reason_code": CopilotReasonCode.PROVIDER_UNAVAILABLE.value,
    }


def compute_deterministic_opportunity_candidates(
    *,
    candidate_inputs: list[dict[str, object]],
    minimum_eligible_count: int = _MIN_OPPORTUNITY_ELIGIBLE_COUNT,
    strategy_profile: CopilotOpportunityStrategyProfile = (
        CopilotOpportunityStrategyProfile.DCA_2X_V1
    ),
    double_down_threshold_pct: Decimal = _DOUBLE_DOWN_THRESHOLD_PCT_DEFAULT,
    double_down_multiplier: Decimal = _DOUBLE_DOWN_MULTIPLIER_DEFAULT,
) -> list[dict[str, object]]:
    """Return deterministic DCA-oriented opportunity ranking rows from normalized inputs."""

    if strategy_profile is not CopilotOpportunityStrategyProfile.DCA_2X_V1:
        raise PortfolioAiCopilotClientError(
            "Unsupported opportunity strategy profile.",
            status_code=422,
            reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
        )
    if double_down_threshold_pct <= Decimal(
        "0"
    ) or double_down_threshold_pct >= Decimal("1"):
        raise PortfolioAiCopilotClientError(
            "double_down_threshold_pct must be in (0, 1).",
            status_code=422,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
        )
    if double_down_multiplier < Decimal("1") or double_down_multiplier > Decimal("3"):
        raise PortfolioAiCopilotClientError(
            "double_down_multiplier must be in [1, 3].",
            status_code=422,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
        )

    normalized_rows: list[_OpportunityCandidateInput] = []
    for input_row in candidate_inputs:
        normalized_input = _normalize_candidate_input_row(candidate_input=input_row)
        if normalized_input is None:
            continue
        normalized_rows.append(normalized_input)

    eligible_rows = [
        row
        for row in normalized_rows
        if (
            row.history_points_count >= _MIN_OPPORTUNITY_HISTORY_POINTS
            and row.latest_close_price_usd > Decimal("0")
            and row.rolling_90d_high_price_usd > Decimal("0")
            and row.rolling_52w_high_price_usd > Decimal("0")
        )
    ]
    if len(eligible_rows) < minimum_eligible_count:
        raise PortfolioAiCopilotClientError(
            "Insufficient eligible opportunity candidates after deterministic filters.",
            status_code=409,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
        )

    discount_by_symbol: dict[str, float] = {
        row.symbol: max(
            0.0,
            float(
                (row.rolling_90d_high_price_usd - row.latest_close_price_usd)
                / row.rolling_90d_high_price_usd
            ),
        )
        for row in eligible_rows
    }
    momentum_by_symbol: dict[str, float] = {
        row.symbol: float(row.return_30d) for row in eligible_rows
    }
    volatility_by_symbol: dict[str, float] = {
        row.symbol: max(float(row.volatility_30d), 0.0) for row in eligible_rows
    }

    discount_scores = _normalize_scores(raw_scores=discount_by_symbol)
    momentum_scores = _normalize_scores(raw_scores=momentum_by_symbol)
    stability_scores = _normalize_inverted_scores(raw_scores=volatility_by_symbol)

    ranked_rows: list[dict[str, object]] = []
    for row in eligible_rows:
        discount_score = discount_scores[row.symbol]
        momentum_score = momentum_scores[row.symbol]
        stability_score = stability_scores[row.symbol]
        (
            fundamentals_proxy_state,
            fundamentals_proxy_score,
            fundamentals_proxy_reason_codes,
        ) = _resolve_fundamentals_proxy_assessment(candidate_row=row)
        action_state, action_multiplier, action_reason_codes = (
            _resolve_dca_action_state(
                candidate_row=row,
                strategy_profile=strategy_profile,
                double_down_threshold_pct=double_down_threshold_pct,
                double_down_multiplier=double_down_multiplier,
                fundamentals_proxy_state=fundamentals_proxy_state,
            )
        )
        opportunity_score = (
            (0.45 * discount_score) + (0.35 * momentum_score) + (0.20 * stability_score)
        )
        deduplicated_action_reasons: list[str] = []
        for reason_code in [*action_reason_codes, *fundamentals_proxy_reason_codes]:
            if reason_code not in deduplicated_action_reasons:
                deduplicated_action_reasons.append(reason_code)
        ranked_rows.append(
            {
                "symbol": row.symbol,
                "currently_held": row.currently_held,
                "action_state": action_state.value,
                "action_multiplier": _quantize_score(float(action_multiplier)),
                "action_reason_codes": deduplicated_action_reasons,
                "fundamentals_proxy_state": fundamentals_proxy_state.value,
                "fundamentals_proxy_score": _quantize_score(
                    float(fundamentals_proxy_score)
                ),
                "opportunity_score": _quantize_score(opportunity_score),
                "discount_score": _quantize_score(discount_score),
                "momentum_score": _quantize_score(momentum_score),
                "stability_score": _quantize_score(stability_score),
                "latest_close_price_usd": row.latest_close_price_usd,
                "rolling_90d_high_price_usd": row.rolling_90d_high_price_usd,
                "rolling_52w_high_price_usd": row.rolling_52w_high_price_usd,
                "drawdown_from_52w_high_pct": row.drawdown_from_52w_high_pct,
                "return_30d": row.return_30d,
                "return_90d": row.return_90d,
                "return_252d": row.return_252d,
                "volatility_30d": row.volatility_30d,
            }
        )

    ranked_rows.sort(
        key=lambda row: (
            _action_priority_for_row(row=row),
            -_row_float_value(row=row, field="opportunity_score"),
            -_row_float_value(row=row, field="discount_score"),
            str(row["symbol"]),
        ),
    )
    return ranked_rows


def _row_float_value(*, row: dict[str, object], field: str) -> float:
    """Extract one row decimal field as float for deterministic sorting."""

    raw_value = row.get(field)
    if isinstance(raw_value, Decimal):
        return float(raw_value)
    if isinstance(raw_value, (int, float)):
        return float(raw_value)
    return 0.0


def _action_priority_for_row(*, row: dict[str, object]) -> int:
    """Resolve deterministic action-priority ordering for one opportunity row."""

    action_state_value = str(row.get("action_state", "")).strip().lower()
    if action_state_value == CopilotOpportunityActionState.DOUBLE_DOWN_CANDIDATE.value:
        return 0
    if action_state_value == CopilotOpportunityActionState.WATCHLIST.value:
        return 1
    if action_state_value == CopilotOpportunityActionState.BASELINE_DCA.value:
        return 2
    return 3


def _normalize_scores(*, raw_scores: Mapping[str, float]) -> dict[str, float]:
    """Min-max normalize score map to stable [0, 1] range."""

    values = list(raw_scores.values())
    if not values:
        return {}
    min_value = min(values)
    max_value = max(values)
    if math.isclose(min_value, max_value):
        return dict.fromkeys(raw_scores, 1.0)
    scale = max_value - min_value
    return {symbol: (value - min_value) / scale for symbol, value in raw_scores.items()}


def _normalize_inverted_scores(*, raw_scores: Mapping[str, float]) -> dict[str, float]:
    """Min-max normalize where lower raw value means higher normalized score."""

    normalized_direct = _normalize_scores(raw_scores=raw_scores)
    if not normalized_direct:
        return {}
    return {symbol: 1.0 - value for symbol, value in normalized_direct.items()}


def _quantize_score(score: float) -> Decimal:
    """Quantize one normalized score to stable six-decimal precision."""

    return Decimal(str(score)).quantize(_QUANTIZE_6DP, rounding=ROUND_HALF_UP)


def _normalize_candidate_input_row(
    *,
    candidate_input: dict[str, object],
) -> _OpportunityCandidateInput | None:
    """Normalize one candidate-input row into deterministic numeric fields."""

    symbol_candidate = candidate_input.get("symbol")
    if not isinstance(symbol_candidate, str) or not symbol_candidate.strip():
        return None
    symbol = symbol_candidate.strip().upper()

    latest_close_price_usd = _decimal_from_object(
        value=candidate_input.get("latest_close_price_usd"),
    )
    rolling_90d_high_price_usd = _decimal_from_object(
        value=candidate_input.get("rolling_90d_high_price_usd"),
    )
    rolling_52w_high_price_usd = _decimal_from_object(
        value=candidate_input.get("rolling_52w_high_price_usd"),
    )
    if rolling_52w_high_price_usd <= Decimal("0"):
        rolling_52w_high_price_usd = rolling_90d_high_price_usd
    drawdown_from_52w_high_pct = _decimal_from_object(
        value=candidate_input.get("drawdown_from_52w_high_pct"),
    )
    if drawdown_from_52w_high_pct <= Decimal("0"):
        drawdown_from_52w_high_pct = _safe_price_drawdown_pct(
            latest_close_price_usd=latest_close_price_usd,
            reference_high_price_usd=rolling_52w_high_price_usd,
        )
    return_30d = _decimal_from_object(value=candidate_input.get("return_30d"))
    return_90d = _decimal_from_object(value=candidate_input.get("return_90d"))
    return_252d = _decimal_from_object(value=candidate_input.get("return_252d"))
    volatility_30d = _decimal_from_object(value=candidate_input.get("volatility_30d"))

    history_points_count_candidate = candidate_input.get("history_points_count")
    if not isinstance(history_points_count_candidate, int):
        return None
    currently_held = bool(candidate_input.get("currently_held", False))
    return _OpportunityCandidateInput(
        symbol=symbol,
        latest_close_price_usd=latest_close_price_usd,
        rolling_90d_high_price_usd=rolling_90d_high_price_usd,
        rolling_52w_high_price_usd=rolling_52w_high_price_usd,
        drawdown_from_52w_high_pct=drawdown_from_52w_high_pct,
        return_30d=return_30d,
        return_90d=return_90d,
        return_252d=return_252d,
        volatility_30d=volatility_30d,
        history_points_count=history_points_count_candidate,
        currently_held=currently_held,
    )


def _safe_price_drawdown_pct(
    *,
    latest_close_price_usd: Decimal,
    reference_high_price_usd: Decimal,
) -> Decimal:
    """Compute bounded drawdown percentage from one reference high price."""

    if reference_high_price_usd <= Decimal("0"):
        return Decimal("0")
    if latest_close_price_usd <= Decimal("0"):
        return Decimal("0")
    raw_drawdown = (
        reference_high_price_usd - latest_close_price_usd
    ) / reference_high_price_usd
    if raw_drawdown <= Decimal("0"):
        return Decimal("0")
    return raw_drawdown


def _resolve_fundamentals_proxy_assessment(
    *,
    candidate_row: _OpportunityCandidateInput,
) -> tuple[CopilotFundamentalsProxyState, Decimal, list[str]]:
    """Resolve one deterministic fundamentals proxy assessment from available price context."""

    pass_count = 0
    reason_codes: list[str] = []

    if candidate_row.return_30d >= _FUNDAMENTALS_PROXY_MAX_30D_DRAWDOWN:
        pass_count += 1
        reason_codes.append("proxy_return_30d_within_floor")
    else:
        reason_codes.append("proxy_return_30d_below_floor")

    if candidate_row.return_90d >= _FUNDAMENTALS_PROXY_MAX_90D_DRAWDOWN:
        pass_count += 1
        reason_codes.append("proxy_return_90d_within_floor")
    else:
        reason_codes.append("proxy_return_90d_below_floor")

    if candidate_row.volatility_30d <= _FUNDAMENTALS_PROXY_MAX_30D_VOLATILITY:
        pass_count += 1
        reason_codes.append("proxy_volatility_30d_within_ceiling")
    else:
        reason_codes.append("proxy_volatility_30d_above_ceiling")

    proxy_score = Decimal(str(pass_count / 3.0))
    if pass_count >= _FUNDAMENTALS_PROXY_MIN_PASS_COUNT:
        return (CopilotFundamentalsProxyState.PASSED, proxy_score, reason_codes)
    if pass_count == 1:
        return (CopilotFundamentalsProxyState.INCONCLUSIVE, proxy_score, reason_codes)
    return (CopilotFundamentalsProxyState.FAILED, proxy_score, reason_codes)


def _resolve_dca_action_state(
    *,
    candidate_row: _OpportunityCandidateInput,
    strategy_profile: CopilotOpportunityStrategyProfile,
    double_down_threshold_pct: Decimal,
    double_down_multiplier: Decimal,
    fundamentals_proxy_state: CopilotFundamentalsProxyState,
) -> tuple[CopilotOpportunityActionState, Decimal, list[str]]:
    """Resolve deterministic DCA action state, multiplier, and reason codes."""

    reasons: list[str] = [f"strategy_profile_{strategy_profile.value}"]
    has_full_52w_history = (
        candidate_row.history_points_count >= _OPPORTUNITY_52W_WINDOW_POINTS
    )
    if has_full_52w_history:
        reasons.append("full_52w_history")
    else:
        reasons.append("insufficient_52w_history")
    threshold_met = (
        has_full_52w_history
        and candidate_row.drawdown_from_52w_high_pct >= double_down_threshold_pct
    )
    if threshold_met:
        reasons.append("double_down_threshold_met")
    elif has_full_52w_history:
        reasons.append("double_down_threshold_not_met")
    else:
        reasons.append("double_down_threshold_not_evaluable")

    if candidate_row.currently_held:
        reasons.append("currently_held")
        if (
            threshold_met
            and fundamentals_proxy_state is CopilotFundamentalsProxyState.PASSED
        ):
            reasons.append("fundamentals_proxy_passed")
            return (
                CopilotOpportunityActionState.DOUBLE_DOWN_CANDIDATE,
                double_down_multiplier,
                reasons,
            )
        if fundamentals_proxy_state is CopilotFundamentalsProxyState.FAILED:
            reasons.append("fundamentals_proxy_failed")
            return (CopilotOpportunityActionState.HOLD_OFF, Decimal("0"), reasons)
        if fundamentals_proxy_state is CopilotFundamentalsProxyState.INCONCLUSIVE:
            reasons.append("fundamentals_proxy_inconclusive")
        return (CopilotOpportunityActionState.BASELINE_DCA, Decimal("1"), reasons)

    reasons.append("not_currently_held")
    if fundamentals_proxy_state is CopilotFundamentalsProxyState.FAILED:
        reasons.append("fundamentals_proxy_failed")
        return (CopilotOpportunityActionState.HOLD_OFF, Decimal("0"), reasons)
    if fundamentals_proxy_state is CopilotFundamentalsProxyState.PASSED:
        reasons.append("fundamentals_proxy_passed")
    else:
        reasons.append("fundamentals_proxy_inconclusive")
    return (CopilotOpportunityActionState.WATCHLIST, Decimal("1"), reasons)


def _decimal_from_object(*, value: object) -> Decimal:
    """Parse one object into Decimal with fail-fast numeric validation."""

    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        trimmed_value = value.strip()
        if not trimmed_value:
            return Decimal("0")
        try:
            return Decimal(trimmed_value)
        except InvalidOperation as exc:
            raise PortfolioAiCopilotClientError(
                "Invalid numeric candidate input.",
                status_code=422,
                reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
            ) from exc
    return Decimal("0")


def _extract_latest_user_message(*, request: PortfolioCopilotChatRequest) -> str:
    """Extract latest user message from bounded request history."""

    for message in reversed(request.messages):
        if message.role.value == "user":
            return message.content.strip()
    return ""


def _build_governed_sql_template_registry() -> dict[str, _GovernedSqlTemplate]:
    """Build allowlisted governed SQL template registry for copilot SQL tooling."""

    return {
        "portfolio_ml_latest_forecast_states": _GovernedSqlTemplate(
            template_id="portfolio_ml_latest_forecast_states",
            sql_text=_GOVERNED_SQL_LATEST_FORECAST_STATES,
            default_max_rows=_GOVERNED_SQL_DEFAULT_MAX_ROWS,
            max_rows_cap=_GOVERNED_SQL_MAX_ROWS_CAP,
            timeout_seconds=_GOVERNED_SQL_TIMEOUT_SECONDS,
        )
    }


def _normalize_governed_sql_params(
    *,
    template: _GovernedSqlTemplate,
    template_params: Mapping[str, object],
) -> dict[str, object]:
    """Validate and normalize governed SQL template parameters."""

    if template.template_id != "portfolio_ml_latest_forecast_states":
        raise PortfolioAiCopilotClientError(
            "governed_sql_template_not_allowlisted: unsupported template.",
            status_code=422,
            reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
        )

    allowed_keys = {"scope", "lifecycle_state", "max_rows"}
    unknown_keys = sorted(
        str(key) for key in template_params.keys() if str(key) not in allowed_keys
    )
    if len(unknown_keys) > 0:
        raise PortfolioAiCopilotClientError(
            "governed_sql_invalid_parameters: unrecognized parameter keys "
            f"{', '.join(unknown_keys)}.",
            status_code=422,
            reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
        )

    scope_value = template_params.get("scope")
    normalized_scope: str | None = None
    if scope_value is not None:
        if not isinstance(scope_value, str):
            raise PortfolioAiCopilotClientError(
                "governed_sql_invalid_parameters: scope must be a string.",
                status_code=422,
                reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
            )
        candidate_scope = scope_value.strip().lower()
        if candidate_scope not in {
            PortfolioMLScope.PORTFOLIO.value,
            PortfolioMLScope.INSTRUMENT_SYMBOL.value,
        }:
            raise PortfolioAiCopilotClientError(
                "governed_sql_invalid_parameters: unsupported scope value.",
                status_code=422,
                reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
            )
        normalized_scope = candidate_scope

    lifecycle_state_value = template_params.get("lifecycle_state")
    normalized_lifecycle_state: str | None = None
    if lifecycle_state_value is not None:
        if not isinstance(lifecycle_state_value, str):
            raise PortfolioAiCopilotClientError(
                "governed_sql_invalid_parameters: lifecycle_state must be a string.",
                status_code=422,
                reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
            )
        candidate_lifecycle_state = lifecycle_state_value.strip().lower()
        if candidate_lifecycle_state not in {state.value for state in PortfolioMLState}:
            raise PortfolioAiCopilotClientError(
                "governed_sql_invalid_parameters: unsupported lifecycle_state value.",
                status_code=422,
                reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
            )
        normalized_lifecycle_state = candidate_lifecycle_state

    max_rows_value = template_params.get("max_rows")
    normalized_max_rows = template.default_max_rows
    if max_rows_value is not None:
        if not isinstance(max_rows_value, int):
            raise PortfolioAiCopilotClientError(
                "governed_sql_invalid_parameters: max_rows must be an integer.",
                status_code=422,
                reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
            )
        if max_rows_value < 1 or max_rows_value > template.max_rows_cap:
            raise PortfolioAiCopilotClientError(
                "governed_sql_invalid_parameters: max_rows is outside allowed bounds.",
                status_code=422,
                reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
            )
        normalized_max_rows = max_rows_value

    return {
        "scope": normalized_scope,
        "lifecycle_state": normalized_lifecycle_state,
        "limit_rows": normalized_max_rows,
    }


async def execute_governed_sql_template(
    *,
    db: AsyncSession | None,
    template_id: str,
    template_params: Mapping[str, object],
    raw_sql: str | None = None,
) -> dict[str, object]:
    """Execute one allowlisted read-only SQL template with strict policy controls."""

    if raw_sql is not None and raw_sql.strip() != "":
        raise PortfolioAiCopilotClientError(
            "governed_sql_policy: free-form SQL input is prohibited.",
            status_code=422,
            reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
        )

    normalized_template_id = template_id.strip()
    registry = _build_governed_sql_template_registry()
    template = registry.get(normalized_template_id)
    if template is None:
        raise PortfolioAiCopilotClientError(
            "governed_sql_template_not_allowlisted: template_id is not allowlisted.",
            status_code=422,
            reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
        )

    normalized_params = _normalize_governed_sql_params(
        template=template,
        template_params=template_params,
    )
    if db is None:
        raise PortfolioAiCopilotClientError(
            "governed_sql_execution_unavailable: database session is required.",
            status_code=500,
            reason_code=CopilotReasonCode.PROVIDER_UNAVAILABLE,
        )

    try:
        execution_result = await asyncio.wait_for(
            db.execute(text(template.sql_text), normalized_params),
            timeout=template.timeout_seconds,
        )
    except TimeoutError as exc:
        raise PortfolioAiCopilotClientError(
            "governed_sql_timeout: template execution exceeded timeout limit.",
            status_code=504,
            reason_code=CopilotReasonCode.PROVIDER_UNAVAILABLE,
        ) from exc

    rows: list[dict[str, object]] = []
    for row_mapping in execution_result.mappings().all():
        row_payload: dict[str, object] = {}
        for key, value in row_mapping.items():
            row_payload[str(key)] = value
        rows.append(row_payload)

    executed_at = datetime.now(UTC).isoformat()
    audit_id = (
        f"governed_sql_{normalized_template_id}_{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    )
    return {
        "template_id": normalized_template_id,
        "audit_id": audit_id,
        "bounded_row_count": len(rows),
        "max_rows": normalized_params["limit_rows"],
        "timeout_ms": int(template.timeout_seconds * 1000),
        "as_of_ledger_at": executed_at,
        "rows": rows,
    }


async def validate_document_references(
    *,
    db: AsyncSession,
    document_ids: Sequence[int],
) -> list[int]:
    """Validate bounded document references against persisted source-document rows."""

    normalized_document_ids: list[int] = []
    for document_id in document_ids:
        if document_id <= 0:
            raise PortfolioAiCopilotClientError(
                "document_reference_invalid: document_id values must be positive integers.",
                status_code=422,
                reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
            )
        if document_id not in normalized_document_ids:
            normalized_document_ids.append(document_id)

    if len(normalized_document_ids) > _MAX_DOCUMENT_REFERENCES:
        raise PortfolioAiCopilotClientError(
            "document_reference_invalid: too many document references for one request.",
            status_code=422,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
        )
    if len(normalized_document_ids) == 0:
        return []

    existing_rows_result = await db.execute(
        select(SourceDocument.id).where(SourceDocument.id.in_(normalized_document_ids))
    )
    existing_ids = {
        int(document_id) for document_id in existing_rows_result.scalars().all()
    }
    missing_ids = [
        document_id
        for document_id in normalized_document_ids
        if document_id not in existing_ids
    ]
    if len(missing_ids) > 0:
        missing_ids_text = ", ".join(str(document_id) for document_id in missing_ids)
        raise PortfolioAiCopilotClientError(
            "document_reference_not_found: unresolved document_id values "
            f"{missing_ids_text}.",
            status_code=422,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
        )
    return normalized_document_ids


async def _build_document_reference_context(
    *,
    db: AsyncSession,
    document_ids: Sequence[int],
) -> list[dict[str, object]]:
    """Build one bounded document-reference context payload from ingestion records."""

    if len(document_ids) == 0:
        return []

    result = await db.execute(
        select(SourceDocument).where(SourceDocument.id.in_(document_ids))
    )
    rows = result.scalars().all()

    by_id: dict[int, SourceDocument] = {}
    for row in rows:
        by_id[row.id] = row

    normalized_context: list[dict[str, object]] = []
    for document_id in document_ids:
        source_document = by_id.get(document_id)
        if source_document is None:
            continue
        normalized_context.append(
            {
                "document_id": source_document.id,
                "storage_key": source_document.storage_key,
                "original_filename": source_document.original_filename,
                "content_type": source_document.content_type,
                "created_at": (
                    source_document.created_at.isoformat()
                    if isinstance(source_document.created_at, datetime)
                    else str(source_document.created_at)
                ),
            }
        )
    return normalized_context


def _safe_prompt_suggestions(
    *,
    request: PortfolioCopilotChatRequest,
    state: CopilotResponseState,
    selected_tool_ids: Sequence[str],
    reason_code: CopilotReasonCode | None,
    has_document_references: bool,
) -> list[str]:
    """Build prompt suggestions defensively without masking primary response semantics."""

    try:
        return _build_prompt_suggestions(
            request=request,
            state=state,
            selected_tool_ids=selected_tool_ids,
            reason_code=reason_code,
            has_document_references=has_document_references,
        )
    except Exception:
        logger.info(
            "portfolio_ai_copilot.prompt_suggestion_failed",
            operation=request.operation.value,
            scope=request.scope.value,
            state=state.value,
            reason_code=reason_code.value if reason_code else None,
            exc_info=True,
        )
        return []


def resolve_phase_m_question_pack(
    *,
    request: PortfolioCopilotChatRequest,
    decision_lens: str | None = None,
) -> list[str]:
    """Resolve one guided question pack for phase-m decision lenses and scope."""

    normalized_lens = (decision_lens or "").strip().lower()
    if normalized_lens == "":
        normalized_lens = "dashboard"

    base_by_lens: dict[str, list[str]] = {
        "dashboard": [
            "Why did my portfolio move the most today?",
            "Which holdings explain most of current concentration?",
        ],
        "risk": [
            "Which symbols contribute the most to portfolio risk?",
            "How has drawdown risk changed versus last month?",
        ],
        "rebalancing": [
            "Compare MVO, HRP, and Black-Litterman weights for my top holdings.",
            "What constraints reduce concentration without increasing volatility too much?",
        ],
        "copilot": [
            "Summarize current portfolio posture with assumptions and caveats.",
            "Show what changed since the last evaluation snapshot.",
        ],
    }
    suggestions = base_by_lens.get(normalized_lens, base_by_lens["dashboard"]).copy()
    if request.scope == PortfolioQuantReportScope.INSTRUMENT_SYMBOL:
        suggestions.append(
            "What instrument-specific risk signals diverge from portfolio-level context?"
        )
    if request.operation == CopilotOperation.OPPORTUNITY_SCAN:
        suggestions.append(
            "Which symbols qualify for deterministic double-down candidates right now?"
        )
    return suggestions[:_MAX_PROMPT_SUGGESTIONS]


def _build_prompt_suggestions(
    *,
    request: PortfolioCopilotChatRequest,
    state: CopilotResponseState,
    selected_tool_ids: Sequence[str],
    reason_code: CopilotReasonCode | None,
    has_document_references: bool,
) -> list[str]:
    """Build bounded prompt suggestion metadata from active context and lifecycle state."""

    suggestions = resolve_phase_m_question_pack(request=request)

    if "portfolio_ml_forecasts" in selected_tool_ids:
        suggestions.append(
            "Show the current forecast champion lifecycle state and expiry window."
        )
    if (
        "portfolio_ml_capm" in selected_tool_ids
        or "portfolio_ml_signals" in selected_tool_ids
    ):
        suggestions.append(
            "Explain CAPM beta and expected return with benchmark provenance."
        )
    if "portfolio_ml_registry" in selected_tool_ids:
        suggestions.append(
            "List the latest registry promotion decisions and replacement lineage."
        )
    if "portfolio_sql_template" in selected_tool_ids:
        suggestions.append(
            "Inspect governed SQL template output metadata and row bounds."
        )
    if "opportunity_scanner" in selected_tool_ids:
        suggestions.append(
            "Which currently held symbols meet the 20% drawdown double-down threshold today?"
        )
        suggestions.append(
            "Show baseline DCA vs. hold-off candidates with the deterministic reason codes."
        )
    if has_document_references:
        suggestions.append(
            "Summarize key findings from the referenced documents before forecasting."
        )
    if (
        state == CopilotResponseState.BLOCKED
        and reason_code == CopilotReasonCode.INSUFFICIENT_CONTEXT
    ):
        suggestions.append(
            "Retry with one valid document_id or switch scope to portfolio for broader context."
        )
    if request.scope == PortfolioQuantReportScope.INSTRUMENT_SYMBOL:
        suggestions.append(
            "Compare instrument signal and forecast state against portfolio aggregate context."
        )

    if len(suggestions) == 0:
        suggestions.append(
            "Explain portfolio risk and trend movement over the selected period."
        )

    deduplicated_suggestions: list[str] = []
    for suggestion in suggestions:
        if suggestion not in deduplicated_suggestions:
            deduplicated_suggestions.append(suggestion)
    return deduplicated_suggestions[:_MAX_PROMPT_SUGGESTIONS]


async def get_portfolio_copilot_chat_response(
    *,
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> PortfolioCopilotChatResponse:
    """Return one typed copilot response for chat or opportunity scan operation."""

    latest_user_message = _extract_latest_user_message(request=request)
    validated_document_ids: list[int] = []
    document_reference_context: list[dict[str, object]] = []
    logger.info(
        "portfolio_ai_copilot.chat_started",
        operation=request.operation.value,
        period=request.period.value,
        scope=request.scope.value,
        instrument_symbol=request.instrument_symbol,
        message_count=len(request.messages),
        document_id_count=len(request.document_ids),
    )
    try:
        enforce_copilot_request_boundary(user_message=latest_user_message)
        if request.max_tool_calls > _MAX_TOOL_CALLS:
            raise PortfolioAiCopilotClientError(
                "Request exceeds maximum tool-call budget.",
                status_code=422,
                reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
            )
        validated_document_ids = await validate_document_references(
            db=db,
            document_ids=request.document_ids,
        )
        document_reference_context = await _build_document_reference_context(
            db=db,
            document_ids=validated_document_ids,
        )

        if request.operation == CopilotOperation.OPPORTUNITY_SCAN:
            response = await _build_opportunity_scan_response(
                db=db,
                request=request,
                latest_user_message=latest_user_message,
                document_reference_context=document_reference_context,
            )
            logger.info(
                "portfolio_ai_copilot.chat_completed",
                operation=request.operation.value,
                state=response.state.value,
                reason_code=(
                    response.reason_code.value if response.reason_code else None
                ),
                evidence_count=len(response.evidence),
                opportunity_candidate_count=len(response.opportunity_candidates),
            )
            return response

        tool_results = await _execute_allowlisted_tools(
            db=db,
            request=request,
            latest_user_message=latest_user_message,
        )
        selected_tool_ids = [result.tool_id for result in tool_results]
        prompt_context = _build_prompt_context_from_tool_results(
            request=request,
            tool_results=tool_results,
            document_reference_context=document_reference_context,
        )
        answer_text = await _request_provider_narration(
            request=request,
            latest_user_message=latest_user_message,
            prompt_context=prompt_context,
        )

        evidence_rows = [
            CopilotEvidenceReference(
                tool_id=result.tool_id,
                metric_id=result.metric_id,
                as_of_ledger_at=result.as_of_ledger_at,
            )
            for result in tool_results
        ]
        if len(validated_document_ids) > 0:
            evidence_rows.append(
                CopilotEvidenceReference(
                    tool_id="document_reference_context",
                    metric_id="document_ids",
                    as_of_ledger_at=datetime.now(UTC).isoformat(),
                )
            )

        response = PortfolioCopilotChatResponse(
            state=CopilotResponseState.READY,
            answer=answer_text,
            evidence=evidence_rows,
            limitations=_default_limitations(),
            reason_code=None,
            prompt_suggestions=_safe_prompt_suggestions(
                request=request,
                state=CopilotResponseState.READY,
                selected_tool_ids=selected_tool_ids,
                reason_code=None,
                has_document_references=len(validated_document_ids) > 0,
            ),
        )
        logger.info(
            "portfolio_ai_copilot.chat_completed",
            operation=request.operation.value,
            state=response.state.value,
            reason_code=None,
            evidence_count=len(response.evidence),
            opportunity_candidate_count=0,
        )
        return response
    except PortfolioAiCopilotClientError as exc:
        blocked_or_error_response = _response_for_client_error(error=exc)
        response = blocked_or_error_response.model_copy(
            update={
                "prompt_suggestions": _safe_prompt_suggestions(
                    request=request,
                    state=blocked_or_error_response.state,
                    selected_tool_ids=[],
                    reason_code=blocked_or_error_response.reason_code,
                    has_document_references=len(validated_document_ids) > 0,
                )
            }
        )
        logger.info(
            "portfolio_ai_copilot.chat_rejected",
            operation=request.operation.value,
            reason_code=exc.reason_code.value,
            state=response.state.value,
            error=str(exc),
        )
        return response
    except (
        PortfolioAnalyticsClientError,
        MarketDataClientError,
        PortfolioMLClientError,
    ) as exc:
        logger.info(
            "portfolio_ai_copilot.chat_rejected",
            operation=request.operation.value,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT.value,
            state=CopilotResponseState.BLOCKED.value,
            error=str(exc),
        )
        return PortfolioCopilotChatResponse(
            state=CopilotResponseState.BLOCKED,
            answer="",
            evidence=[],
            limitations=[
                *_default_limitations(),
                "Required portfolio or market-data context was unavailable for this request.",
            ],
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
            prompt_suggestions=_safe_prompt_suggestions(
                request=request,
                state=CopilotResponseState.BLOCKED,
                selected_tool_ids=[],
                reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
                has_document_references=len(validated_document_ids) > 0,
            ),
        )
    except GroqProviderError as exc:
        mapped_failure = map_provider_failure_to_copilot_state(
            status_code=exc.status_code,
            provider_error_code=exc.provider_error_code,
            error_type=exc.error_type,
        )
        provider_failure_response = _response_for_provider_failure(
            mapped_state=mapped_failure.get("state"),
            mapped_reason_code=mapped_failure.get("reason_code"),
            error_message=str(exc),
        )
        response = provider_failure_response.model_copy(
            update={
                "prompt_suggestions": _safe_prompt_suggestions(
                    request=request,
                    state=provider_failure_response.state,
                    selected_tool_ids=[],
                    reason_code=provider_failure_response.reason_code,
                    has_document_references=len(validated_document_ids) > 0,
                )
            }
        )
        logger.info(
            "portfolio_ai_copilot.chat_failed",
            operation=request.operation.value,
            provider_status_code=exc.status_code,
            provider_error_code=exc.provider_error_code,
            mapped_state=response.state.value,
            mapped_reason_code=(
                response.reason_code.value if response.reason_code else None
            ),
            error=str(exc),
        )
        return response
    except Exception as exc:
        logger.error(
            "portfolio_ai_copilot.chat_failed",
            operation=request.operation.value,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        return PortfolioCopilotChatResponse(
            state=CopilotResponseState.ERROR,
            answer="",
            evidence=[],
            limitations=[
                *_default_limitations(),
                "Unexpected runtime failure occurred while processing this copilot request.",
            ],
            reason_code=CopilotReasonCode.PROVIDER_UNAVAILABLE,
            prompt_suggestions=_safe_prompt_suggestions(
                request=request,
                state=CopilotResponseState.ERROR,
                selected_tool_ids=[],
                reason_code=CopilotReasonCode.PROVIDER_UNAVAILABLE,
                has_document_references=len(validated_document_ids) > 0,
            ),
        )


def _response_for_client_error(
    *, error: PortfolioAiCopilotClientError
) -> PortfolioCopilotChatResponse:
    """Map one typed client error to frozen blocked/error response semantics."""

    if error.reason_code in {
        CopilotReasonCode.BOUNDARY_RESTRICTED,
        CopilotReasonCode.INSUFFICIENT_CONTEXT,
        CopilotReasonCode.PROVIDER_BLOCKED_POLICY,
    }:
        return PortfolioCopilotChatResponse(
            state=CopilotResponseState.BLOCKED,
            answer="",
            evidence=[],
            limitations=[*_default_limitations(), str(error)],
            reason_code=error.reason_code,
        )
    return PortfolioCopilotChatResponse(
        state=CopilotResponseState.ERROR,
        answer="",
        evidence=[],
        limitations=[*_default_limitations(), str(error)],
        reason_code=error.reason_code,
    )


def _response_for_provider_failure(
    *,
    mapped_state: str | None,
    mapped_reason_code: str | None,
    error_message: str,
) -> PortfolioCopilotChatResponse:
    """Build one typed response from normalized provider failure mapping."""

    state = (
        CopilotResponseState(mapped_state)
        if mapped_state in {state.value for state in CopilotResponseState}
        else CopilotResponseState.ERROR
    )
    reason_code = (
        CopilotReasonCode(mapped_reason_code)
        if mapped_reason_code in {reason.value for reason in CopilotReasonCode}
        else CopilotReasonCode.PROVIDER_UNAVAILABLE
    )
    return PortfolioCopilotChatResponse(
        state=state,
        answer="",
        evidence=[],
        limitations=[*_default_limitations(), error_message],
        reason_code=reason_code,
    )


def _default_limitations() -> list[str]:
    """Return stable limitation messaging for all copilot responses."""

    return [
        "Read-only analytical copilot; no trade execution, order routing, or account mutation.",
        "Outputs are grounded in allowlisted aggregated analytics and deterministic market rules.",
        "Responses are informational only and not financial advice.",
    ]


async def _request_provider_narration(
    *,
    request: PortfolioCopilotChatRequest,
    latest_user_message: str,
    prompt_context: dict[str, object],
) -> str:
    """Request one provider narration response for assembled bounded prompt context."""

    config = build_groq_chat_completions_adapter_config()
    context_json = json.dumps(prompt_context, default=str, sort_keys=True)
    if request.operation is CopilotOperation.OPPORTUNITY_SCAN:
        system_prompt = (
            "You are a read-only portfolio analytics copilot specialized in deterministic "
            "DCA opportunity scans. Use only provided context and do not invent unavailable facts. "
            "Never provide trade execution instructions or guaranteed return claims. "
            "Treat deterministic candidate action_state and reason codes as the source of truth. "
            "When fundamentals proxy is limited, explicitly call it a proxy and recommend manual "
            "fundamental verification."
        )
        user_prompt = (
            f"Operation: {request.operation.value}\n"
            f"Strategy profile: {request.opportunity_strategy_profile.value}\n"
            f"Double-down threshold pct: {request.double_down_threshold_pct}\n"
            f"Double-down multiplier: {request.double_down_multiplier}\n"
            f"Period: {request.period.value}\n"
            f"Scope: {request.scope.value}\n"
            f"Instrument: {request.instrument_symbol or 'N/A'}\n"
            f"User question: {latest_user_message}\n"
            "Context JSON:\n"
            f"{context_json}\n"
            "Respond in markdown with these sections: "
            "1) Double-Down Candidates, 2) Baseline DCA, 3) Watchlist, 4) Hold-Off Risks, "
            "5) Limits and Next Checks."
        )
    else:
        system_prompt = (
            "You are a read-only portfolio analytics copilot. "
            "Use only provided context and do not invent unavailable facts. "
            "Never provide trade execution instructions or guaranteed return claims. "
            "Always include uncertainty when evidence is limited."
        )
        user_prompt = (
            f"Operation: {request.operation.value}\n"
            f"Period: {request.period.value}\n"
            f"Scope: {request.scope.value}\n"
            f"Instrument: {request.instrument_symbol or 'N/A'}\n"
            f"User question: {latest_user_message}\n"
            "Context JSON:\n"
            f"{context_json}\n"
            "Respond with concise portfolio analysis grounded in the context."
        )
    return await request_groq_chat_completion(
        config=config,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )


def _build_prompt_context_from_tool_results(
    *,
    request: PortfolioCopilotChatRequest,
    tool_results: Sequence[_ToolExecutionResult],
    document_reference_context: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Build one privacy-minimized prompt context from tool execution outputs."""

    context_payload: dict[str, object] = {
        "operation": request.operation.value,
        "period": request.period.value,
        "scope": request.scope.value,
        "instrument_symbol": request.instrument_symbol,
        "tool_context": {result.tool_id: result.payload for result in tool_results},
        "document_references": list(document_reference_context),
    }
    return sanitize_model_context_payload(context_payload=context_payload)


async def _build_opportunity_scan_response(
    *,
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
    latest_user_message: str,
    document_reference_context: Sequence[Mapping[str, object]],
) -> PortfolioCopilotChatResponse:
    """Build one deterministic opportunity-scan response with separate narration."""

    candidate_inputs = await _load_opportunity_candidate_inputs(db=db)
    ranked_candidates_raw = compute_deterministic_opportunity_candidates(
        candidate_inputs=candidate_inputs,
        minimum_eligible_count=_MIN_OPPORTUNITY_ELIGIBLE_COUNT,
        strategy_profile=request.opportunity_strategy_profile,
        double_down_threshold_pct=request.double_down_threshold_pct,
        double_down_multiplier=request.double_down_multiplier,
    )
    top_candidates_raw = ranked_candidates_raw[:10]
    top_candidates = [
        CopilotOpportunityCandidate.model_validate(candidate)
        for candidate in top_candidates_raw
    ]
    prompt_context: dict[str, object] = {
        "operation": request.operation.value,
        "period": request.period.value,
        "scope": request.scope.value,
        "instrument_symbol": request.instrument_symbol,
        "opportunity_strategy_profile": request.opportunity_strategy_profile.value,
        "double_down_threshold_pct": request.double_down_threshold_pct,
        "double_down_multiplier": request.double_down_multiplier,
        "candidate_count": len(top_candidates_raw),
        "candidates": top_candidates_raw,
        "document_references": list(document_reference_context),
    }
    answer_text = await _request_provider_narration(
        request=request,
        latest_user_message=latest_user_message,
        prompt_context=sanitize_model_context_payload(context_payload=prompt_context),
    )
    evidence_rows = [
        CopilotEvidenceReference(
            tool_id="opportunity_scanner",
            metric_id="dca_action_state",
            as_of_ledger_at=datetime.now(UTC).isoformat(),
        )
    ]
    if len(document_reference_context) > 0:
        evidence_rows.append(
            CopilotEvidenceReference(
                tool_id="document_reference_context",
                metric_id="document_ids",
                as_of_ledger_at=datetime.now(UTC).isoformat(),
            )
        )
    return PortfolioCopilotChatResponse(
        state=CopilotResponseState.READY,
        answer=answer_text,
        evidence=evidence_rows,
        limitations=[
            *_default_limitations(),
            "Deterministic DCA candidate classification precedes AI narration in this workflow.",
            "Fundamentals are represented by a deterministic proxy and still require manual verification.",
        ],
        reason_code=None,
        prompt_suggestions=_safe_prompt_suggestions(
            request=request,
            state=CopilotResponseState.READY,
            selected_tool_ids=["opportunity_scanner"],
            reason_code=None,
            has_document_references=len(document_reference_context) > 0,
        ),
        opportunity_candidates=top_candidates,
        opportunity_narration=answer_text,
    )


async def _load_opportunity_candidate_inputs(
    *, db: AsyncSession
) -> list[dict[str, object]]:
    """Load deterministic scanner inputs from starter universe and persisted market data."""

    starter_symbols = list_market_data_library_symbols(size=100)
    summary_response = await get_portfolio_summary_response(db=db)
    held_symbols = {
        row.instrument_symbol.strip().upper() for row in summary_response.rows
    }

    candidate_inputs: list[dict[str, object]] = []
    for symbol in starter_symbols:
        price_history_rows = await list_price_history_for_symbol(
            db=db, instrument_symbol=symbol
        )
        normalized_closes = _extract_recent_unique_usd_closes(
            price_history_rows=price_history_rows
        )
        if not normalized_closes:
            continue

        latest_close = normalized_closes[0]
        rolling_90d_window = normalized_closes[:_MIN_OPPORTUNITY_HISTORY_POINTS]
        rolling_52w_window = normalized_closes[:_OPPORTUNITY_52W_WINDOW_POINTS]
        rolling_90d_high = (
            max(rolling_90d_window) if rolling_90d_window else Decimal("0")
        )
        rolling_52w_high = (
            max(rolling_52w_window) if rolling_52w_window else Decimal("0")
        )
        drawdown_from_52w_high_pct = _safe_price_drawdown_pct(
            latest_close_price_usd=latest_close,
            reference_high_price_usd=rolling_52w_high,
        )
        return_30d, return_90d, return_252d, volatility_30d = _compute_return_metrics(
            descending_close_values=normalized_closes
        )
        candidate_inputs.append(
            {
                "symbol": symbol,
                "latest_close_price_usd": latest_close,
                "rolling_90d_high_price_usd": rolling_90d_high,
                "rolling_52w_high_price_usd": rolling_52w_high,
                "drawdown_from_52w_high_pct": drawdown_from_52w_high_pct,
                "return_30d": return_30d,
                "return_90d": return_90d,
                "return_252d": return_252d,
                "volatility_30d": volatility_30d,
                "history_points_count": len(normalized_closes),
                "currently_held": symbol in held_symbols,
            }
        )
    return candidate_inputs


def _extract_recent_unique_usd_closes(
    *, price_history_rows: Sequence[object]
) -> list[Decimal]:
    """Extract descending unique-date USD close values for one symbol history series."""

    normalized_closes: list[Decimal] = []
    seen_calendar_keys: set[str] = set()
    for row_candidate in price_history_rows:
        if not isinstance(row_candidate, BaseModel):
            continue
        row_mapping = cast(dict[str, object], row_candidate.model_dump(mode="python"))
        currency_code = str(row_mapping.get("currency_code", "")).upper()
        if currency_code != "USD":
            continue
        price_value_candidate = row_mapping.get("price_value")
        if not isinstance(
            price_value_candidate, Decimal
        ) or price_value_candidate <= Decimal("0"):
            continue
        trading_date_candidate = row_mapping.get("trading_date")
        market_timestamp_candidate = row_mapping.get("market_timestamp")

        calendar_key = _resolve_calendar_key(
            trading_date=trading_date_candidate,
            market_timestamp=market_timestamp_candidate,
        )
        if calendar_key is None or calendar_key in seen_calendar_keys:
            continue
        seen_calendar_keys.add(calendar_key)
        normalized_closes.append(price_value_candidate)
    return normalized_closes


def _resolve_calendar_key(
    *, trading_date: object, market_timestamp: object
) -> str | None:
    """Resolve deterministic per-day key for one market-data row."""

    if hasattr(trading_date, "isoformat"):
        isoformat_method = getattr(trading_date, "isoformat", None)
        if callable(isoformat_method):
            return str(isoformat_method())
    if isinstance(market_timestamp, datetime):
        return market_timestamp.date().isoformat()
    return None


def _compute_return_metrics(
    *,
    descending_close_values: Sequence[Decimal],
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Compute return metrics and 30-day volatility from descending close sequence."""

    return_30d = _compute_period_return(
        descending_close_values=descending_close_values,
        period_days=30,
    )
    return_90d = _compute_period_return(
        descending_close_values=descending_close_values,
        period_days=90,
    )
    return_252d = _compute_period_return(
        descending_close_values=descending_close_values,
        period_days=252,
    )

    volatility_30d = _compute_30d_volatility(
        descending_close_values=descending_close_values
    )
    return return_30d, return_90d, return_252d, volatility_30d


def _compute_period_return(
    *,
    descending_close_values: Sequence[Decimal],
    period_days: int,
) -> Decimal:
    """Compute one period return from descending closes."""

    if period_days <= 0:
        return Decimal("0")
    if len(descending_close_values) < period_days + 1:
        return Decimal("0")

    latest_close = descending_close_values[0]
    baseline_close = descending_close_values[period_days]
    if baseline_close <= Decimal("0"):
        return Decimal("0")
    return (latest_close / baseline_close) - Decimal("1")


def _compute_30d_volatility(*, descending_close_values: Sequence[Decimal]) -> Decimal:
    """Compute rolling 30-day return volatility from descending closes."""

    if len(descending_close_values) < 31:
        return Decimal("0")

    daily_returns: list[float] = []
    for index in range(30):
        newer = descending_close_values[index]
        older = descending_close_values[index + 1]
        if older <= Decimal("0"):
            continue
        daily_returns.append(float((newer / older) - Decimal("1")))
    if len(daily_returns) >= 2:
        return Decimal(str(statistics.stdev(daily_returns)))
    return Decimal("0")


async def _execute_allowlisted_tools(
    *,
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
    latest_user_message: str,
) -> list[_ToolExecutionResult]:
    """Execute bounded allowlisted tools and return serialized evidence payloads."""

    selected_tool_ids = _select_allowlisted_tool_ids(
        request=request,
        latest_user_message=latest_user_message,
    )[: request.max_tool_calls]
    if not selected_tool_ids:
        raise PortfolioAiCopilotClientError(
            "No allowlisted tools were selected for this request.",
            status_code=409,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
        )

    tool_registry = _build_allowlisted_tool_registry()
    tool_results: list[_ToolExecutionResult] = []
    for tool_id in selected_tool_ids:
        tool_definition = tool_registry.get(tool_id)
        if tool_definition is None:
            continue
        raw_payload = await tool_definition.execute(db, request)
        payload_mapping = _serialize_tool_payload(raw_payload=raw_payload)
        sanitized_payload = sanitize_model_context_payload(
            context_payload=payload_mapping
        )
        tool_results.append(
            _ToolExecutionResult(
                tool_id=tool_definition.tool_id,
                metric_id=tool_definition.metric_id,
                payload=sanitized_payload,
                as_of_ledger_at=_extract_as_of_ledger_at(payload=sanitized_payload),
            )
        )
    if not tool_results:
        raise PortfolioAiCopilotClientError(
            "No allowlisted tool payloads were available for safe response generation.",
            status_code=409,
            reason_code=CopilotReasonCode.INSUFFICIENT_CONTEXT,
        )
    return tool_results


def _extract_as_of_ledger_at(*, payload: Mapping[str, object]) -> str | None:
    """Extract as_of_ledger_at field from serialized tool payload for evidence metadata."""

    as_of_candidate = payload.get("as_of_ledger_at")
    if isinstance(as_of_candidate, str):
        return as_of_candidate
    if isinstance(as_of_candidate, datetime):
        return as_of_candidate.isoformat()
    if hasattr(as_of_candidate, "isoformat"):
        isoformat_method = getattr(as_of_candidate, "isoformat", None)
        if callable(isoformat_method):
            return str(isoformat_method())
    return None


def _serialize_tool_payload(*, raw_payload: object) -> dict[str, object]:
    """Serialize one tool payload object into mapping form for prompt/evidence usage."""

    if isinstance(raw_payload, BaseModel):
        return cast(dict[str, object], raw_payload.model_dump(mode="python"))
    if isinstance(raw_payload, dict):
        return cast(dict[str, object], raw_payload)
    raise PortfolioAiCopilotClientError(
        "Tool payload could not be serialized safely.",
        status_code=500,
        reason_code=CopilotReasonCode.PROVIDER_UNAVAILABLE,
    )


def _select_allowlisted_tool_ids(
    *,
    request: PortfolioCopilotChatRequest,
    latest_user_message: str,
) -> list[str]:
    """Select one deterministic bounded allowlisted-tool plan from user request context."""

    normalized_message = latest_user_message.lower()
    selected_tool_ids: list[str] = [
        "portfolio_summary",
        "portfolio_health_synthesis",
        "portfolio_risk_estimators",
    ]
    if request.scope.value == "instrument_symbol":
        selected_tool_ids.append("portfolio_time_series")
    if request.sql_template_id is not None:
        selected_tool_ids.append("portfolio_sql_template")
    keyword_to_tool_id: tuple[tuple[str, str], ...] = (
        ("time series", "portfolio_time_series"),
        ("trend", "portfolio_time_series"),
        ("contribution", "portfolio_contribution"),
        ("drawdown", "portfolio_risk_evolution"),
        ("volatility", "portfolio_risk_evolution"),
        ("distribution", "portfolio_return_distribution"),
        ("histogram", "portfolio_return_distribution"),
        ("hierarchy", "portfolio_hierarchy"),
        ("sector", "portfolio_hierarchy"),
        ("allocation", "portfolio_hierarchy"),
        ("monte carlo", "portfolio_monte_carlo"),
        ("simulation", "portfolio_monte_carlo"),
        ("quant", "portfolio_quant_metrics"),
        ("sharpe", "portfolio_quant_metrics"),
        ("sortino", "portfolio_quant_metrics"),
        ("beta", "portfolio_quant_metrics"),
        ("ml signal", "portfolio_ml_signals"),
        ("signal", "portfolio_ml_signals"),
        ("capm", "portfolio_ml_capm"),
        ("forecast", "portfolio_ml_forecasts"),
        ("registry", "portfolio_ml_registry"),
        ("champion", "portfolio_ml_registry"),
        ("model governance", "portfolio_ml_registry"),
        ("sql template", "portfolio_sql_template"),
    )
    for keyword, tool_id in keyword_to_tool_id:
        if keyword in normalized_message and tool_id not in selected_tool_ids:
            selected_tool_ids.append(tool_id)

    deduplicated_tool_ids: list[str] = []
    for tool_id in selected_tool_ids:
        if tool_id not in deduplicated_tool_ids:
            deduplicated_tool_ids.append(tool_id)
    return deduplicated_tool_ids[:_MAX_TOOL_CALLS]


def _build_allowlisted_tool_registry() -> dict[str, _CopilotToolDefinition]:
    """Build frozen v1 allowlisted tool registry for copilot orchestration."""

    return {
        "portfolio_summary": _CopilotToolDefinition(
            tool_id="portfolio_summary",
            metric_id="rows",
            execute=_tool_portfolio_summary,
        ),
        "portfolio_time_series": _CopilotToolDefinition(
            tool_id="portfolio_time_series",
            metric_id="points",
            execute=_tool_portfolio_time_series,
        ),
        "portfolio_contribution": _CopilotToolDefinition(
            tool_id="portfolio_contribution",
            metric_id="rows",
            execute=_tool_portfolio_contribution,
        ),
        "portfolio_risk_estimators": _CopilotToolDefinition(
            tool_id="portfolio_risk_estimators",
            metric_id="metrics",
            execute=_tool_portfolio_risk_estimators,
        ),
        "portfolio_risk_evolution": _CopilotToolDefinition(
            tool_id="portfolio_risk_evolution",
            metric_id="drawdown_path_points",
            execute=_tool_portfolio_risk_evolution,
        ),
        "portfolio_return_distribution": _CopilotToolDefinition(
            tool_id="portfolio_return_distribution",
            metric_id="buckets",
            execute=_tool_portfolio_return_distribution,
        ),
        "portfolio_hierarchy": _CopilotToolDefinition(
            tool_id="portfolio_hierarchy",
            metric_id="groups",
            execute=_tool_portfolio_hierarchy,
        ),
        "portfolio_monte_carlo": _CopilotToolDefinition(
            tool_id="portfolio_monte_carlo",
            metric_id="summary",
            execute=_tool_portfolio_monte_carlo,
        ),
        "portfolio_health_synthesis": _CopilotToolDefinition(
            tool_id="portfolio_health_synthesis",
            metric_id="health_score",
            execute=_tool_portfolio_health_synthesis,
        ),
        "portfolio_quant_metrics": _CopilotToolDefinition(
            tool_id="portfolio_quant_metrics",
            metric_id="metrics",
            execute=_tool_portfolio_quant_metrics,
        ),
        "portfolio_ml_signals": _CopilotToolDefinition(
            tool_id="portfolio_ml_signals",
            metric_id="signals",
            execute=_tool_portfolio_ml_signals,
        ),
        "portfolio_ml_capm": _CopilotToolDefinition(
            tool_id="portfolio_ml_capm",
            metric_id="capm",
            execute=_tool_portfolio_ml_capm,
        ),
        "portfolio_ml_forecasts": _CopilotToolDefinition(
            tool_id="portfolio_ml_forecasts",
            metric_id="horizons",
            execute=_tool_portfolio_ml_forecasts,
        ),
        "portfolio_ml_registry": _CopilotToolDefinition(
            tool_id="portfolio_ml_registry",
            metric_id="rows",
            execute=_tool_portfolio_ml_registry,
        ),
        "portfolio_sql_template": _CopilotToolDefinition(
            tool_id="portfolio_sql_template",
            metric_id="rows",
            execute=_tool_portfolio_sql_template,
        ),
    }


async def _tool_portfolio_summary(
    db: AsyncSession,
    _request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio-summary tool."""

    return await get_portfolio_summary_response(db=db)


async def _tool_portfolio_time_series(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio time-series tool."""

    return await get_portfolio_time_series_response(
        db=db,
        period=request.period,
        scope=request.scope,
        instrument_symbol=request.instrument_symbol,
    )


async def _tool_portfolio_contribution(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio-contribution tool."""

    return await get_portfolio_contribution_response(
        db=db,
        period=request.period,
    )


async def _tool_portfolio_risk_estimators(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted risk-estimators tool."""

    return await get_portfolio_risk_estimators_response(
        db=db,
        window_days=_RISK_WINDOW_BY_PERIOD[request.period],
        scope=request.scope,
        instrument_symbol=request.instrument_symbol,
        period=request.period,
    )


async def _tool_portfolio_risk_evolution(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted risk-evolution tool."""

    return await get_portfolio_risk_evolution_response(
        db=db,
        period=request.period,
        scope=request.scope,
        instrument_symbol=request.instrument_symbol,
    )


async def _tool_portfolio_return_distribution(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted return-distribution tool."""

    return await get_portfolio_return_distribution_response(
        db=db,
        period=request.period,
        scope=request.scope,
        instrument_symbol=request.instrument_symbol,
    )


async def _tool_portfolio_hierarchy(
    db: AsyncSession,
    _request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio-hierarchy tool."""

    return await get_portfolio_hierarchy_response(
        db=db,
        group_by=PortfolioHierarchyGroupBy.SECTOR,
    )


async def _tool_portfolio_monte_carlo(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted Monte Carlo tool with bounded diagnostics settings."""

    monte_carlo_request = PortfolioMonteCarloRequest(
        scope=request.scope,
        instrument_symbol=request.instrument_symbol,
        period=request.period,
        sims=500,
        enable_profile_comparison=True,
        calibration_basis=PortfolioMonteCarloCalibrationBasis.MONTHLY,
    )
    return await generate_portfolio_monte_carlo_response(
        db=db,
        request=monte_carlo_request,
    )


async def _tool_portfolio_health_synthesis(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio-health synthesis tool."""

    return await get_portfolio_health_synthesis_response(
        db=db,
        period=request.period,
        scope=request.scope,
        instrument_symbol=request.instrument_symbol,
        profile_posture=PortfolioHealthProfilePosture.BALANCED,
    )


async def _tool_portfolio_quant_metrics(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted quant-metrics tool."""

    return await get_portfolio_quant_metrics_response(
        db=db,
        period=request.period,
    )


def _resolve_portfolio_ml_scope(
    *,
    request: PortfolioCopilotChatRequest,
) -> PortfolioMLScope:
    """Resolve one portfolio_ml scope enum from copilot request scope."""

    if request.scope == PortfolioQuantReportScope.INSTRUMENT_SYMBOL:
        return PortfolioMLScope.INSTRUMENT_SYMBOL
    return PortfolioMLScope.PORTFOLIO


async def _tool_portfolio_ml_signals(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio_ml signals tool."""

    del db
    return await get_portfolio_ml_signal_response(
        scope=_resolve_portfolio_ml_scope(request=request),
        instrument_symbol=request.instrument_symbol,
    )


async def _tool_portfolio_ml_capm(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio_ml CAPM summary tool."""

    del db
    signal_response = await get_portfolio_ml_signal_response(
        scope=_resolve_portfolio_ml_scope(request=request),
        instrument_symbol=request.instrument_symbol,
    )
    capm_payload = cast(
        dict[str, object], signal_response.capm.model_dump(mode="python")
    )
    return {
        "state": signal_response.state.value,
        "state_reason_code": signal_response.state_reason_code,
        "state_reason_detail": signal_response.state_reason_detail,
        "as_of_ledger_at": signal_response.as_of_ledger_at,
        "as_of_market_at": signal_response.as_of_market_at,
        "evaluated_at": signal_response.evaluated_at,
        "capm": capm_payload,
    }


async def _tool_portfolio_ml_forecasts(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio_ml forecasts tool."""

    return await get_portfolio_ml_forecast_response(
        scope=_resolve_portfolio_ml_scope(request=request),
        instrument_symbol=request.instrument_symbol,
        db=db,
    )


async def _tool_portfolio_ml_registry(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute allowlisted portfolio_ml registry tool."""

    return await get_portfolio_ml_registry_response(
        db=db,
        scope=request.scope.value,
    )


async def _tool_portfolio_sql_template(
    db: AsyncSession,
    request: PortfolioCopilotChatRequest,
) -> object:
    """Execute one governed SQL template via allowlisted read-only tool path."""

    if request.sql_template_id is None:
        raise PortfolioAiCopilotClientError(
            "governed_sql_template_not_allowlisted: missing template_id.",
            status_code=422,
            reason_code=CopilotReasonCode.BOUNDARY_RESTRICTED,
        )
    return await execute_governed_sql_template(
        db=db,
        template_id=request.sql_template_id,
        template_params=request.sql_template_params,
        raw_sql=request.raw_sql,
    )
