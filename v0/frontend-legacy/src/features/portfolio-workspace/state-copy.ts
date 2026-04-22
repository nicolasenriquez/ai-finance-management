export type WorkspaceLifecycleState =
  | "loading"
  | "empty"
  | "ready"
  | "stale"
  | "unavailable"
  | "blocked"
  | "error";

export type WorkspaceLifecycleCopy = {
  title: string;
  message: string;
  tone: "info" | "warning" | "error" | "success";
};

const LIFECYCLE_COPY_BY_STATE: Record<
  WorkspaceLifecycleState,
  WorkspaceLifecycleCopy
> = {
  loading: {
    title: "loading",
    message: "Fetching persisted analytics context for this route.",
    tone: "info",
  },
  empty: {
    title: "empty",
    message: "Route data loaded, but no rows satisfy the selected scope and filters.",
    tone: "warning",
  },
  ready: {
    title: "ready",
    message: "Route context is current and ready for interpretation.",
    tone: "success",
  },
  stale: {
    title: "stale",
    message: "Route context is available but freshness policy indicates stale timing.",
    tone: "warning",
  },
  unavailable: {
    title: "unavailable",
    message: "Required data for this route is unavailable for the selected context.",
    tone: "warning",
  },
  blocked: {
    title: "blocked",
    message: "Request cannot proceed under current route safety boundaries.",
    tone: "warning",
  },
  error: {
    title: "error",
    message: "An unexpected route error occurred while loading analytical context.",
    tone: "error",
  },
};

export function resolveWorkspaceLifecycleCopy(
  state: WorkspaceLifecycleState,
  overrideMessage?: string,
): WorkspaceLifecycleCopy {
  const baseline = LIFECYCLE_COPY_BY_STATE[state];
  if (!overrideMessage) {
    return baseline;
  }
  return {
    ...baseline,
    message: overrideMessage,
  };
}
