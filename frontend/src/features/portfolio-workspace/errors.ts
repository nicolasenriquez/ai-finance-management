import { AppApiError } from "../../core/api/errors";

export type WorkspaceErrorCopy = {
  title: string;
  message: string;
  variant: "error" | "warning";
};

export function resolveWorkspaceError(
  error: unknown,
  fallbackTitle: string,
  fallbackMessage: string,
): WorkspaceErrorCopy {
  if (error instanceof AppApiError && error.kind === "not_found") {
    return {
      title: `${fallbackTitle} not found`,
      message:
        error.detail || "The requested analytics resource was not found in API scope.",
      variant: "warning",
    };
  }

  if (error instanceof AppApiError && error.detail) {
    return {
      title: fallbackTitle,
      message: error.detail,
      variant: "error",
    };
  }

  return {
    title: fallbackTitle,
    message: fallbackMessage,
    variant: "error",
  };
}
