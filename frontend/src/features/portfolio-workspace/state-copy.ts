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

export type UnavailableReasonCode =
  | "fundamental_contract_missing"
  | "technical_contract_missing"
  | "source_contract_missing"
  | "freshness_sla_expired"
  | "provider_timeout"
  | "provider_failure"
  | "timezone_session_mismatch";

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

const UNAVAILABLE_REASON_COPY: Record<UnavailableReasonCode, string> = {
  fundamental_contract_missing:
    "research data pending: fundamental contract is not connected for this metric.",
  technical_contract_missing:
    "signal contract not connected: technical state remains unavailable.",
  source_contract_missing:
    "source contract missing: required data contract is not connected.",
  freshness_sla_expired:
    "evidence freshness expired: action state is downgraded until data refresh succeeds.",
  provider_timeout:
    "provider timeout while resolving contract data. Retry is required.",
  provider_failure:
    "provider failure while resolving contract data. Retry is required.",
  timezone_session_mismatch:
    "timezone/session mismatch: market session context does not match expected route policy.",
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

export function resolveUnavailableReasonCopy(reasonCode: UnavailableReasonCode): string {
  return UNAVAILABLE_REASON_COPY[reasonCode];
}
