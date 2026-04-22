import { fetchJson } from "../../core/api/client";
import {
  portfolioCopilotChatResponseSchema,
  type PortfolioCopilotChatRequest,
  type PortfolioCopilotChatResponse,
} from "../../core/api/schemas";

export function postPortfolioCopilotChat(
  request: PortfolioCopilotChatRequest,
): Promise<PortfolioCopilotChatResponse> {
  const normalizedScope = request.scope;
  const normalizedInstrumentSymbol =
    request.instrument_symbol?.trim().toUpperCase() || null;
  const normalizedMessages = request.messages
    .slice(-8)
    .map((message) => ({
      role: message.role,
      content: message.content.trim().slice(0, 2000),
    }))
    .filter((message) => message.content.length > 0);
  const normalizedDocumentIds: number[] = [];
  for (const candidateDocumentId of request.document_ids || []) {
    if (
      Number.isInteger(candidateDocumentId) &&
      candidateDocumentId > 0 &&
      !normalizedDocumentIds.includes(candidateDocumentId)
    ) {
      normalizedDocumentIds.push(candidateDocumentId);
    }
    if (normalizedDocumentIds.length >= 8) {
      break;
    }
  }

  return fetchJson({
    path: "/portfolio/copilot/chat",
    method: "POST",
    body: {
      ...request,
      messages: normalizedMessages,
      scope: normalizedScope,
      instrument_symbol:
        normalizedScope === "instrument_symbol" ? normalizedInstrumentSymbol : null,
      max_tool_calls: Math.min(Math.max(request.max_tool_calls, 1), 6),
      opportunity_strategy_profile: request.opportunity_strategy_profile || "dca_2x_v1",
      double_down_threshold_pct: request.double_down_threshold_pct || "0.20",
      double_down_multiplier: request.double_down_multiplier || "2.0",
      document_ids: normalizedDocumentIds,
    },
    schema: portfolioCopilotChatResponseSchema,
  }).then((responsePayload) => ({
    ...responsePayload,
    answer: responsePayload.answer || responsePayload.answer_text || "",
    answer_text: responsePayload.answer_text || responsePayload.answer || "",
    assumptions: responsePayload.assumptions || [],
    caveats: responsePayload.caveats || responsePayload.limitations || [],
    suggested_follow_ups:
      responsePayload.suggested_follow_ups || responsePayload.prompt_suggestions || [],
    limitations: responsePayload.limitations || responsePayload.caveats || [],
    opportunity_candidates: responsePayload.opportunity_candidates.map((candidate) => ({
      ...candidate,
      action_reason_codes: candidate.action_reason_codes || [],
    })),
    prompt_suggestions: responsePayload.prompt_suggestions || [],
  }));
}
