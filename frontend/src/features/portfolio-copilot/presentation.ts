import type { PortfolioCopilotReasonCode } from "../../core/api/schemas";

export const PORTFOLIO_COPILOT_REASON_MESSAGE_BY_CODE: Record<
  PortfolioCopilotReasonCode,
  string
> = {
  boundary_restricted:
    "Request is outside the read-only portfolio copilot boundary.",
  insufficient_context:
    "Required portfolio or market context is insufficient for this request.",
  provider_blocked_policy:
    "Provider policy or permission blocked this request.",
  rate_limited:
    "Provider rate limit reached. Retry after a short cooldown window.",
  provider_misconfigured:
    "Provider configuration is invalid or incomplete.",
  provider_unavailable:
    "Provider is temporarily unavailable or timed out.",
};

export function resolveReasonMessage(
  reasonCode: PortfolioCopilotReasonCode | null,
): string {
  if (reasonCode === null) {
    return "No reason code provided.";
  }
  return PORTFOLIO_COPILOT_REASON_MESSAGE_BY_CODE[reasonCode];
}
