"""Typed schemas for portfolio AI copilot request/response contracts."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from enum import StrEnum
from typing import Self, cast

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.portfolio_analytics.schemas import (
    PortfolioChartPeriod,
    PortfolioQuantReportScope,
)


class CopilotOperation(StrEnum):
    """Supported portfolio copilot operations."""

    CHAT = "chat"
    OPPORTUNITY_SCAN = "opportunity_scan"


class CopilotConversationRole(StrEnum):
    """Supported prior-turn roles for stateless copilot requests."""

    USER = "user"
    ASSISTANT = "assistant"


class CopilotResponseState(StrEnum):
    """Stable response states for backend/frontend parity."""

    READY = "ready"
    BLOCKED = "blocked"
    ERROR = "error"


class CopilotOpportunityActionState(StrEnum):
    """Deterministic DCA action classifications for opportunity-scan rows."""

    BASELINE_DCA = "baseline_dca"
    DOUBLE_DOWN_CANDIDATE = "double_down_candidate"
    WATCHLIST = "watchlist"
    HOLD_OFF = "hold_off"


class CopilotFundamentalsProxyState(StrEnum):
    """Deterministic fundamentals-proxy gate outcome for candidate rows."""

    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class CopilotOpportunityStrategyProfile(StrEnum):
    """Supported deterministic opportunity-scan strategy profiles."""

    DCA_2X_V1 = "dca_2x_v1"


class CopilotReasonCode(StrEnum):
    """Stable blocked/error reason codes for portfolio copilot responses."""

    BOUNDARY_RESTRICTED = "boundary_restricted"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    PROVIDER_BLOCKED_POLICY = "provider_blocked_policy"
    RATE_LIMITED = "rate_limited"
    PROVIDER_MISCONFIGURED = "provider_misconfigured"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


_BLOCKED_REASON_CODES: frozenset[CopilotReasonCode] = frozenset(
    {
        CopilotReasonCode.BOUNDARY_RESTRICTED,
        CopilotReasonCode.INSUFFICIENT_CONTEXT,
        CopilotReasonCode.PROVIDER_BLOCKED_POLICY,
    }
)

_ERROR_REASON_CODES: frozenset[CopilotReasonCode] = frozenset(
    {
        CopilotReasonCode.RATE_LIMITED,
        CopilotReasonCode.PROVIDER_MISCONFIGURED,
        CopilotReasonCode.PROVIDER_UNAVAILABLE,
    }
)


class CopilotConversationMessage(BaseModel):
    """One user or assistant message in bounded request history."""

    model_config = ConfigDict(extra="forbid")

    role: CopilotConversationRole
    content: str = Field(min_length=1, max_length=2000)


class CopilotEvidenceReference(BaseModel):
    """One evidence row referencing one executed analytical tool output."""

    model_config = ConfigDict(extra="forbid")

    tool_id: str = Field(min_length=1)
    metric_id: str | None = None
    as_of_ledger_at: str | None = None


class CopilotOpportunityCandidate(BaseModel):
    """One deterministic opportunity candidate row with normalized score parts."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    currently_held: bool
    action_state: CopilotOpportunityActionState
    action_multiplier: Decimal
    action_reason_codes: list[str] = Field(default_factory=list[str], max_length=8)
    fundamentals_proxy_state: CopilotFundamentalsProxyState
    fundamentals_proxy_score: Decimal
    opportunity_score: Decimal
    discount_score: Decimal
    momentum_score: Decimal
    stability_score: Decimal
    latest_close_price_usd: Decimal
    rolling_90d_high_price_usd: Decimal
    rolling_52w_high_price_usd: Decimal
    drawdown_from_52w_high_pct: Decimal
    return_30d: Decimal
    return_90d: Decimal
    return_252d: Decimal
    volatility_30d: Decimal


class PortfolioCopilotChatRequest(BaseModel):
    """Bounded v1 copilot request contract."""

    model_config = ConfigDict(extra="forbid")

    operation: CopilotOperation = CopilotOperation.CHAT
    messages: list[CopilotConversationMessage] = Field(min_length=1, max_length=8)
    period: PortfolioChartPeriod = PortfolioChartPeriod.D90
    scope: PortfolioQuantReportScope = PortfolioQuantReportScope.PORTFOLIO
    instrument_symbol: str | None = None
    max_tool_calls: int = Field(default=6, ge=1, le=6)
    opportunity_strategy_profile: CopilotOpportunityStrategyProfile = (
        CopilotOpportunityStrategyProfile.DCA_2X_V1
    )
    double_down_threshold_pct: Decimal = Field(
        default=Decimal("0.20"),
        gt=Decimal("0"),
        lt=Decimal("1"),
    )
    double_down_multiplier: Decimal = Field(
        default=Decimal("2.0"),
        ge=Decimal("1"),
        le=Decimal("3"),
    )
    document_ids: list[int] = Field(default_factory=list[int], max_length=8)
    sql_template_id: str | None = Field(default=None, min_length=1, max_length=128)
    sql_template_params: dict[str, object] = Field(default_factory=dict[str, object])
    raw_sql: str | None = Field(default=None, min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_scope_constraints(self) -> Self:
        """Enforce scope/symbol symmetry for request safety."""

        normalized_symbol = (
            self.instrument_symbol.strip() if self.instrument_symbol else None
        )
        if self.scope == PortfolioQuantReportScope.PORTFOLIO:
            if normalized_symbol:
                raise ValueError(
                    "instrument_symbol must be omitted when chart scope is 'portfolio'."
                )
            self.instrument_symbol = None
        else:
            if not normalized_symbol:
                raise ValueError(
                    "instrument_symbol is required when chart scope is 'instrument_symbol'."
                )
            self.instrument_symbol = normalized_symbol.upper()

        normalized_document_ids: list[int] = []
        for document_id in self.document_ids:
            if document_id <= 0:
                raise ValueError("document_ids values must be positive integers.")
            if document_id not in normalized_document_ids:
                normalized_document_ids.append(document_id)
        self.document_ids = normalized_document_ids

        if self.sql_template_id is None:
            if len(self.sql_template_params) > 0:
                raise ValueError(
                    "sql_template_params requires one sql_template_id value.",
                )
        else:
            self.sql_template_id = self.sql_template_id.strip()
            if self.sql_template_id == "":
                raise ValueError("sql_template_id must be non-empty when provided.")

        if self.raw_sql is not None:
            trimmed_raw_sql = self.raw_sql.strip()
            self.raw_sql = trimmed_raw_sql if trimmed_raw_sql else None
        return self


class PortfolioCopilotChatResponse(BaseModel):
    """Typed v1 copilot response contract with state parity metadata."""

    model_config = ConfigDict(extra="allow")

    state: CopilotResponseState
    answer: str = ""
    evidence: list[CopilotEvidenceReference] = Field(
        default_factory=list[CopilotEvidenceReference]
    )
    assumptions: list[str] = Field(default_factory=list[str])
    caveats: list[str] = Field(default_factory=list[str])
    suggested_follow_ups: list[str] = Field(default_factory=list[str], max_length=6)

    # Compatibility fields retained during response contract migration.
    limitations: list[str] = Field(default_factory=list)
    prompt_suggestions: list[str] = Field(default_factory=list[str], max_length=4)
    reason_code: CopilotReasonCode | None = None
    opportunity_candidates: list[CopilotOpportunityCandidate] = Field(
        default_factory=list[CopilotOpportunityCandidate]
    )
    opportunity_narration: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_phase_m_compatibility_fields(cls, value: object) -> object:
        """Map legacy response keys to phase-m structured envelope fields."""

        if not isinstance(value, Mapping):
            return value
        source_mapping = cast(Mapping[object, object], value)
        normalized: dict[str, object] = {
            str(key): mapped_value for key, mapped_value in source_mapping.items()
        }
        answer_value = normalized.get("answer")
        answer_text_value = normalized.get("answer_text")
        if (
            not isinstance(answer_value, str) or answer_value.strip() == ""
        ) and isinstance(answer_text_value, str):
            normalized["answer"] = answer_text_value
        caveats_value = normalized.get("caveats")
        limitations_value = normalized.get("limitations")
        follow_ups_value = normalized.get("suggested_follow_ups")
        prompt_suggestions_value = normalized.get("prompt_suggestions")
        caveats_count = (
            len(cast(list[object], caveats_value))
            if isinstance(caveats_value, list)
            else 0
        )
        follow_ups_count = (
            len(cast(list[object], follow_ups_value))
            if isinstance(follow_ups_value, list)
            else 0
        )
        if (caveats_count == 0) and isinstance(limitations_value, list):
            normalized["caveats"] = normalized["limitations"]
        if (follow_ups_count == 0) and isinstance(prompt_suggestions_value, list):
            normalized["suggested_follow_ups"] = normalized["prompt_suggestions"]
        return normalized

    @model_validator(mode="after")
    def validate_state_reason_consistency(self) -> Self:
        """Require stable reason semantics for blocked/error response states."""

        normalized_assumptions: list[str] = []
        for assumption in self.assumptions:
            trimmed_assumption = assumption.strip()
            if trimmed_assumption:
                normalized_assumptions.append(trimmed_assumption)
        self.assumptions = normalized_assumptions

        normalized_caveats: list[str] = []
        for caveat in self.caveats:
            trimmed_caveat = caveat.strip()
            if trimmed_caveat:
                normalized_caveats.append(trimmed_caveat)
        self.caveats = normalized_caveats

        normalized_follow_ups: list[str] = []
        for follow_up in self.suggested_follow_ups:
            trimmed_follow_up = follow_up.strip()
            if trimmed_follow_up:
                normalized_follow_ups.append(trimmed_follow_up)
        self.suggested_follow_ups = normalized_follow_ups[:6]

        normalized_prompt_suggestions: list[str] = []
        for suggestion in self.prompt_suggestions:
            trimmed_suggestion = suggestion.strip()
            if trimmed_suggestion:
                normalized_prompt_suggestions.append(trimmed_suggestion)
        self.prompt_suggestions = normalized_prompt_suggestions[:4]

        normalized_answer = self.answer.strip()
        if self.state == CopilotResponseState.READY:
            if not normalized_answer:
                raise ValueError("answer must be non-empty when state='ready'.")
            if self.reason_code is not None:
                raise ValueError("reason_code must be null when state='ready'.")
            self.answer = normalized_answer
            self.limitations = self.caveats
            if len(self.prompt_suggestions) == 0:
                self.prompt_suggestions = self.suggested_follow_ups[:4]
            return self

        if self.reason_code is None:
            raise ValueError(
                "reason_code is required when state is 'blocked' or 'error'."
            )
        self.answer = ""
        if len(self.caveats) == 0 and len(self.limitations) > 0:
            self.caveats = self.limitations
        if len(self.suggested_follow_ups) == 0 and len(self.prompt_suggestions) > 0:
            self.suggested_follow_ups = self.prompt_suggestions[:6]
        self.limitations = self.caveats

        if (
            self.state == CopilotResponseState.BLOCKED
            and self.reason_code not in _BLOCKED_REASON_CODES
        ):
            raise ValueError("Blocked responses must use one blocked reason code.")
        if (
            self.state == CopilotResponseState.ERROR
            and self.reason_code not in _ERROR_REASON_CODES
        ):
            raise ValueError("Error responses must use one error reason code.")
        return self

    @computed_field(return_type=str)
    def answer_text(self) -> str:
        """Expose compatibility answer_text view while phase-m clients migrate."""

        return self.answer
