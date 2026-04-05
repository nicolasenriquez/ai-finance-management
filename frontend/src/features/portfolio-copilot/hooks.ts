import { useMutation } from "@tanstack/react-query";

import type {
  PortfolioCopilotChatRequest,
  PortfolioCopilotChatResponse,
} from "../../core/api/schemas";
import { postPortfolioCopilotChat } from "./api";

export function usePortfolioCopilotChatMutation() {
  return useMutation<PortfolioCopilotChatResponse, Error, PortfolioCopilotChatRequest>({
    mutationFn: (request) => postPortfolioCopilotChat(request),
  });
}
