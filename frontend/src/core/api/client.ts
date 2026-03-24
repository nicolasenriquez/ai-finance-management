import { z } from "zod";

import { getFrontendEnv } from "../config/env";
import { AppApiError } from "./errors";

async function readErrorDetail(response: Response): Promise<string | undefined> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : undefined;
  } catch {
    return undefined;
  }
}

function buildErrorFromResponse(
  response: Response,
  detail?: string,
): AppApiError {
  if (response.status === 404) {
    return new AppApiError(detail || "Requested portfolio resource was not found.", {
      kind: "not_found",
      statusCode: response.status,
      detail,
    });
  }

  if (response.status >= 400 && response.status < 500) {
    return new AppApiError(detail || "The request could not be processed.", {
      kind: "validation_error",
      statusCode: response.status,
      detail,
    });
  }

  return new AppApiError(
    detail || "Portfolio analytics is temporarily unavailable.",
    {
      kind: "server_error",
      statusCode: response.status,
      detail,
    },
  );
}

export async function fetchJson<Target>({
  path,
  schema,
}: {
  path: string;
  schema: z.ZodType<Target>;
}): Promise<Target> {
  const { apiPrefix } = getFrontendEnv();

  let response: Response;
  try {
    response = await fetch(`${apiPrefix}${path}`, {
      headers: {
        Accept: "application/json",
      },
    });
  } catch (error) {
    throw new AppApiError("Network error while loading portfolio analytics.", {
      kind: "network_error",
      detail: error instanceof Error ? error.message : undefined,
    });
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw buildErrorFromResponse(response, detail);
  }

  const payload = await response.json();
  const parsed = schema.safeParse(payload);
  if (!parsed.success) {
    throw new AppApiError("Unexpected payload received from portfolio analytics API.", {
      kind: "unexpected_payload",
      detail: parsed.error.message,
    });
  }

  return parsed.data;
}
