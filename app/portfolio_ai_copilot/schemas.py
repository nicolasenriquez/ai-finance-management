"""Typed schemas for portfolio AI copilot request/response contracts."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    opportunity_score: Decimal
    discount_score: Decimal
    momentum_score: Decimal
    stability_score: Decimal
    latest_close_price_usd: Decimal
    rolling_90d_high_price_usd: Decimal
    return_30d: Decimal
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

    @model_validator(mode="after")
    def validate_scope_constraints(self) -> Self:
        """Enforce scope/symbol symmetry for request safety."""

        normalized_symbol = self.instrument_symbol.strip() if self.instrument_symbol else None
        if self.scope == PortfolioQuantReportScope.PORTFOLIO:
            if normalized_symbol:
                raise ValueError(
                    "instrument_symbol must be omitted when chart scope is 'portfolio'."
                )
            self.instrument_symbol = None
            return self

        if not normalized_symbol:
            raise ValueError(
                "instrument_symbol is required when chart scope is 'instrument_symbol'."
            )
        self.instrument_symbol = normalized_symbol.upper()
        return self


class PortfolioCopilotChatResponse(BaseModel):
    """Typed v1 copilot response contract with state parity metadata."""

    model_config = ConfigDict(extra="forbid")

    state: CopilotResponseState
    answer_text: str = ""
    evidence: list[CopilotEvidenceReference] = Field(default_factory=list[CopilotEvidenceReference])
    limitations: list[str] = Field(default_factory=list)
    reason_code: CopilotReasonCode | None = None
    opportunity_candidates: list[CopilotOpportunityCandidate] = Field(
        default_factory=list[CopilotOpportunityCandidate]
    )
    opportunity_narration: str | None = None

    @model_validator(mode="after")
    def validate_state_reason_consistency(self) -> Self:
        """Require stable reason semantics for blocked/error response states."""

        normalized_answer = self.answer_text.strip()
        if self.state == CopilotResponseState.READY:
            if not normalized_answer:
                raise ValueError("answer_text must be non-empty when state='ready'.")
            if self.reason_code is not None:
                raise ValueError("reason_code must be null when state='ready'.")
            return self

        if self.reason_code is None:
            raise ValueError("reason_code is required when state is 'blocked' or 'error'.")

        if (
            self.state == CopilotResponseState.BLOCKED
            and self.reason_code not in _BLOCKED_REASON_CODES
        ):
            raise ValueError("Blocked responses must use one blocked reason code.")
        if self.state == CopilotResponseState.ERROR and self.reason_code not in _ERROR_REASON_CODES:
            raise ValueError("Error responses must use one error reason code.")
        return self
