export type AppApiErrorKind =
  | "not_found"
  | "validation_error"
  | "server_error"
  | "network_error"
  | "unexpected_payload";

export class AppApiError extends Error {
  readonly kind: AppApiErrorKind;
  readonly statusCode?: number;
  readonly detail?: string;

  constructor(
    message: string,
    options: {
      kind: AppApiErrorKind;
      statusCode?: number;
      detail?: string;
    },
  ) {
    super(message);
    this.name = "AppApiError";
    this.kind = options.kind;
    this.statusCode = options.statusCode;
    this.detail = options.detail;
  }
}

export function shouldRetryApiError(error: unknown): boolean {
  if (!(error instanceof AppApiError)) {
    return true;
  }

  return error.kind !== "not_found" && error.kind !== "validation_error";
}
