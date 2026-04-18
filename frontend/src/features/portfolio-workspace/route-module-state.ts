import {
  useEffect,
  useState,
} from "react";

import { useLocation } from "react-router-dom";

export type RoutePrimaryModuleState =
  | "loading"
  | "ready"
  | "empty"
  | "unavailable"
  | "success"
  | "error";

type RoutePrimaryModuleFeedback = {
  message: string;
  tone: "warning" | "success" | "error";
  isRetryable: boolean;
  blocksPrimaryModules: boolean;
};

const ROUTE_PRIMARY_MODULE_FEEDBACK_BY_STATE: Record<
  Exclude<RoutePrimaryModuleState, "loading" | "ready">,
  RoutePrimaryModuleFeedback
> = {
  empty: {
    message: "No rows match current route scope.",
    tone: "warning",
    isRetryable: false,
    blocksPrimaryModules: true,
  },
  unavailable: {
    message: "Required source contract is unavailable for this module.",
    tone: "warning",
    isRetryable: false,
    blocksPrimaryModules: true,
  },
  success: {
    message: "Module refresh completed successfully.",
    tone: "success",
    isRetryable: false,
    blocksPrimaryModules: false,
  },
  error: {
    message: "Module request failed. Retry to reload route evidence.",
    tone: "error",
    isRetryable: true,
    blocksPrimaryModules: true,
  },
};

type RoutePrimaryModuleStateController = {
  moduleState: RoutePrimaryModuleState;
  isPrimaryModuleLoading: boolean;
  shouldRenderBlockingFeedback: boolean;
  feedback: RoutePrimaryModuleFeedback | null;
  retryModuleLoad: () => void;
};

function resolveRoutePrimaryModuleState(rawValue: string | null): RoutePrimaryModuleState {
  const normalizedValue = rawValue?.toLowerCase();
  if (
    normalizedValue === "loading" ||
    normalizedValue === "empty" ||
    normalizedValue === "unavailable" ||
    normalizedValue === "success" ||
    normalizedValue === "error"
  ) {
    return normalizedValue;
  }
  return "ready";
}

function resolveRoutePrimaryModuleStateFromSearch(search: string): RoutePrimaryModuleState {
  const searchParams = new URLSearchParams(search);
  return resolveRoutePrimaryModuleState(searchParams.get("module_state"));
}

export function resolveRoutePrimaryModuleFeedback(
  moduleState: RoutePrimaryModuleState,
): RoutePrimaryModuleFeedback | null {
  if (moduleState === "loading" || moduleState === "ready") {
    return null;
  }
  return ROUTE_PRIMARY_MODULE_FEEDBACK_BY_STATE[moduleState];
}

export function useRoutePrimaryModuleStateController(): RoutePrimaryModuleStateController {
  const location = useLocation();
  const [moduleState, setModuleState] = useState<RoutePrimaryModuleState>(() =>
    resolveRoutePrimaryModuleStateFromSearch(location.search),
  );

  useEffect(() => {
    setModuleState(resolveRoutePrimaryModuleStateFromSearch(location.search));
  }, [location.search]);

  const feedback = resolveRoutePrimaryModuleFeedback(moduleState);

  return {
    moduleState,
    isPrimaryModuleLoading: moduleState === "loading",
    shouldRenderBlockingFeedback: feedback?.blocksPrimaryModules ?? false,
    feedback,
    retryModuleLoad: () => {
      setModuleState("ready");
    },
  };
}

export function useRoutePrimaryModuleState(): RoutePrimaryModuleState {
  const { moduleState } = useRoutePrimaryModuleStateController();
  return moduleState;
}

export function useIsPrimaryModuleLoading(): boolean {
  return useRoutePrimaryModuleState() === "loading";
}
