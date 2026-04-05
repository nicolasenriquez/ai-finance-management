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
    },
    schema: portfolioCopilotChatResponseSchema,
  });
}
