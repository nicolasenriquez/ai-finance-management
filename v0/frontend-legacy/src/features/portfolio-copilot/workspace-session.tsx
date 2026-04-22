import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import { AppApiError } from "../../core/api/errors";
import type {
  PortfolioChartPeriod,
  PortfolioCopilotChatResponse,
  PortfolioCopilotConversationMessage,
  PortfolioCopilotOperation,
  PortfolioCopilotOpportunityStrategyProfile,
  PortfolioCopilotResponseState,
  PortfolioQuantReportScope,
} from "../../core/api/schemas";
import { usePortfolioCopilotChatMutation } from "./hooks";

type CopilotUiState = "idle" | "loading" | "blocked" | "error" | "ready";

export type CopilotLaunchSource =
  | "workspace_shell"
  | "expanded_route";

export type CopilotLaunchContext = {
  route: string;
  period: PortfolioChartPeriod | null;
  scope: PortfolioQuantReportScope;
  instrumentSymbol: string | null;
  source: CopilotLaunchSource;
};

type SubmitCopilotRequestParams = {
  maxToolCalls?: number;
  messageOverride?: string;
};

type PortfolioCopilotWorkspaceState = {
  period: PortfolioChartPeriod;
  operation: PortfolioCopilotOperation;
  scope: PortfolioQuantReportScope;
  instrumentSymbol: string;
  draftMessage: string;
  conversationTurns: PortfolioCopilotConversationMessage[];
  latestResponse: PortfolioCopilotChatResponse | null;
  uiState: CopilotUiState;
  uiErrorMessage: string | null;
  isPending: boolean;
  documentIds: number[];
  attachmentError: string | null;
  launchContext: CopilotLaunchContext | null;
  isLauncherOpen: boolean;
  isLauncherCollapsed: boolean;
};

type PortfolioCopilotWorkspaceActions = {
  setPeriod: (period: PortfolioChartPeriod) => void;
  setOperation: (operation: PortfolioCopilotOperation) => void;
  setScope: (scope: PortfolioQuantReportScope) => void;
  setInstrumentSymbol: (symbol: string) => void;
  setDraftMessage: (message: string) => void;
  setIsLauncherOpen: (isOpen: boolean) => void;
  setIsLauncherCollapsed: (isCollapsed: boolean) => void;
  applyLaunchContext: (context: CopilotLaunchContext) => void;
  submitCopilotRequest: (params?: SubmitCopilotRequestParams) => Promise<void>;
  applyPromptSuggestion: (suggestion: string) => void;
  addDocumentReference: (documentId: number) => void;
  removeDocumentReference: (documentId: number) => void;
  clearAttachmentError: () => void;
};

type PortfolioCopilotWorkspaceContextValue = {
  state: PortfolioCopilotWorkspaceState;
  actions: PortfolioCopilotWorkspaceActions;
};

const PORTFOLIO_COPILOT_MAX_DOCUMENT_REFERENCES = 8;
const PORTFOLIO_COPILOT_OPPORTUNITY_STRATEGY_PROFILE_DEFAULT:
  PortfolioCopilotOpportunityStrategyProfile = "dca_2x_v1";
const PORTFOLIO_COPILOT_DOUBLE_DOWN_THRESHOLD_PCT_DEFAULT = "0.20";
const PORTFOLIO_COPILOT_DOUBLE_DOWN_MULTIPLIER_DEFAULT = "2.0";

const PortfolioCopilotWorkspaceContext =
  createContext<PortfolioCopilotWorkspaceContextValue | null>(null);

function resolveApiErrorMessage(error: unknown): string {
  if (error instanceof AppApiError && error.detail) {
    return error.detail;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Copilot request failed unexpectedly.";
}

function mapResponseStateToUiState(
  responseState: PortfolioCopilotResponseState,
): CopilotUiState {
  if (responseState === "ready") {
    return "ready";
  }
  if (responseState === "blocked") {
    return "blocked";
  }
  return "error";
}

function sanitizePromptSuggestions(suggestions: string[]): string[] {
  const uniqueSuggestions: string[] = [];
  for (const suggestion of suggestions) {
    const trimmedSuggestion = suggestion.trim();
    if (
      trimmedSuggestion.length === 0 ||
      uniqueSuggestions.includes(trimmedSuggestion)
    ) {
      continue;
    }
    uniqueSuggestions.push(trimmedSuggestion);
    if (uniqueSuggestions.length >= 4) {
      break;
    }
  }
  return uniqueSuggestions;
}

export function PortfolioCopilotWorkspaceProvider({
  children,
}: PropsWithChildren) {
  const [period, setPeriod] = useState<PortfolioChartPeriod>("90D");
  const [operation, setOperation] = useState<PortfolioCopilotOperation>("chat");
  const [scope, setScope] = useState<PortfolioQuantReportScope>("portfolio");
  const [instrumentSymbol, setInstrumentSymbol] = useState("");
  const [draftMessage, setDraftMessage] = useState("");
  const [conversationTurns, setConversationTurns] = useState<
    PortfolioCopilotConversationMessage[]
  >([]);
  const [uiState, setUiState] = useState<CopilotUiState>("idle");
  const [latestResponse, setLatestResponse] =
    useState<PortfolioCopilotChatResponse | null>(null);
  const [uiErrorMessage, setUiErrorMessage] = useState<string | null>(null);
  const [documentIds, setDocumentIds] = useState<number[]>([]);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);
  const [launchContext, setLaunchContext] = useState<CopilotLaunchContext | null>(null);
  const [isLauncherOpen, setIsLauncherOpen] = useState(false);
  const [isLauncherCollapsed, setIsLauncherCollapsed] = useState(false);
  const copilotMutation = usePortfolioCopilotChatMutation();

  const applyLaunchContext = useCallback((context: CopilotLaunchContext): void => {
    setLaunchContext(context);
    setIsLauncherOpen(true);
    setIsLauncherCollapsed(false);

    if (context.period !== null) {
      setPeriod(context.period);
    }
    setScope(context.scope);

    if (context.scope === "instrument_symbol" && context.instrumentSymbol) {
      setInstrumentSymbol(context.instrumentSymbol.toUpperCase());
    } else {
      setInstrumentSymbol("");
    }
  }, []);

  const addDocumentReference = useCallback((documentId: number): void => {
    if (!Number.isInteger(documentId) || documentId <= 0) {
      setAttachmentError("Document ID must be one positive integer.");
      return;
    }

    setDocumentIds((previousDocumentIds) => {
      if (previousDocumentIds.includes(documentId)) {
        setAttachmentError(null);
        return previousDocumentIds;
      }
      if (
        previousDocumentIds.length >= PORTFOLIO_COPILOT_MAX_DOCUMENT_REFERENCES
      ) {
        setAttachmentError("A maximum of 8 document references is supported.");
        return previousDocumentIds;
      }
      setAttachmentError(null);
      return [...previousDocumentIds, documentId];
    });
  }, []);

  const removeDocumentReference = useCallback((documentId: number): void => {
    setDocumentIds((previousDocumentIds) =>
      previousDocumentIds.filter((previousDocumentId) => {
        return previousDocumentId !== documentId;
      }),
    );
    setAttachmentError(null);
  }, []);

  const submitCopilotRequest = useCallback(
    async (params?: SubmitCopilotRequestParams): Promise<void> => {
      const trimmedMessage = (params?.messageOverride ?? draftMessage).trim();
      const normalizedInstrumentSymbol = instrumentSymbol.trim().toUpperCase();
      const isScopeRequestReady =
        scope === "portfolio" || normalizedInstrumentSymbol.length > 0;

      if (trimmedMessage.length === 0 || !isScopeRequestReady) {
        return;
      }

      const userTurn: PortfolioCopilotConversationMessage = {
        role: "user",
        content: trimmedMessage.slice(0, 2000),
      };
      const boundedTurns = [...conversationTurns, userTurn].slice(-8);

      setConversationTurns(boundedTurns);
      setUiState("loading");
      setUiErrorMessage(null);

      try {
        const response = await copilotMutation.mutateAsync({
          operation,
          messages: boundedTurns,
          period,
          scope,
          instrument_symbol:
            scope === "instrument_symbol" ? normalizedInstrumentSymbol : null,
          max_tool_calls: params?.maxToolCalls ?? 6,
          opportunity_strategy_profile:
            PORTFOLIO_COPILOT_OPPORTUNITY_STRATEGY_PROFILE_DEFAULT,
          double_down_threshold_pct:
            PORTFOLIO_COPILOT_DOUBLE_DOWN_THRESHOLD_PCT_DEFAULT,
          double_down_multiplier:
            PORTFOLIO_COPILOT_DOUBLE_DOWN_MULTIPLIER_DEFAULT,
          document_ids: documentIds,
        });

        const normalizedResponse: PortfolioCopilotChatResponse = {
          ...response,
          prompt_suggestions: sanitizePromptSuggestions(
            response.prompt_suggestions || [],
          ),
        };
        setLatestResponse(normalizedResponse);
        setUiState(mapResponseStateToUiState(normalizedResponse.state));

        if (
          normalizedResponse.state === "ready" &&
          normalizedResponse.answer_text.trim().length > 0
        ) {
          setConversationTurns((previousTurns) => [
            ...previousTurns.slice(-7),
            {
              role: "assistant",
              content: normalizedResponse.answer_text.trim(),
            },
          ]);
        }
        setDraftMessage("");
      } catch (error) {
        setUiState("error");
        setUiErrorMessage(resolveApiErrorMessage(error));
      }
    },
    [
      conversationTurns,
      copilotMutation,
      documentIds,
      draftMessage,
      instrumentSymbol,
      operation,
      period,
      scope,
    ],
  );

  const applyPromptSuggestion = useCallback((suggestion: string): void => {
    setDraftMessage(suggestion.trim());
  }, []);

  const state = useMemo<PortfolioCopilotWorkspaceState>(() => {
    return {
      period,
      operation,
      scope,
      instrumentSymbol,
      draftMessage,
      conversationTurns,
      latestResponse,
      uiState: copilotMutation.isPending ? "loading" : uiState,
      uiErrorMessage,
      isPending: copilotMutation.isPending,
      documentIds,
      attachmentError,
      launchContext,
      isLauncherOpen,
      isLauncherCollapsed,
    };
  }, [
    attachmentError,
    conversationTurns,
    copilotMutation.isPending,
    documentIds,
    draftMessage,
    instrumentSymbol,
    isLauncherCollapsed,
    isLauncherOpen,
    latestResponse,
    launchContext,
    operation,
    period,
    scope,
    uiErrorMessage,
    uiState,
  ]);

  const actions = useMemo<PortfolioCopilotWorkspaceActions>(() => {
    return {
      setPeriod,
      setOperation,
      setScope,
      setInstrumentSymbol,
      setDraftMessage,
      setIsLauncherOpen,
      setIsLauncherCollapsed,
      applyLaunchContext,
      submitCopilotRequest,
      applyPromptSuggestion,
      addDocumentReference,
      removeDocumentReference,
      clearAttachmentError: () => setAttachmentError(null),
    };
  }, [
    addDocumentReference,
    applyLaunchContext,
    applyPromptSuggestion,
    removeDocumentReference,
    submitCopilotRequest,
  ]);

  const value = useMemo<PortfolioCopilotWorkspaceContextValue>(() => {
    return {
      state,
      actions,
    };
  }, [actions, state]);

  return (
    <PortfolioCopilotWorkspaceContext.Provider value={value}>
      {children}
    </PortfolioCopilotWorkspaceContext.Provider>
  );
}

export function useOptionalPortfolioCopilotWorkspace():
  | PortfolioCopilotWorkspaceContextValue
  | null {
  return useContext(PortfolioCopilotWorkspaceContext);
}

export function usePortfolioCopilotWorkspace():
  PortfolioCopilotWorkspaceContextValue {
  const context = useOptionalPortfolioCopilotWorkspace();
  if (context === null) {
    throw new Error(
      "PortfolioCopilotWorkspaceProvider is required for copilot workspace usage.",
    );
  }
  return context;
}
