import { z } from "zod";

import { getFrontendEnv } from "../config/env";
import { AppApiError } from "./errors";

type JsonRequestMethod = "GET" | "POST";

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

async function sendApiRequest({
  path,
  method,
  accept,
  body,
}: {
  path: string;
  method: JsonRequestMethod;
  accept: string;
  body?: unknown;
}): Promise<Response> {
  const { apiPrefix } = getFrontendEnv();
  const headers: Record<string, string> = {
    Accept: accept,
  };
  const requestInit: RequestInit = {
    method,
    headers,
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    requestInit.body = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${apiPrefix}${path}`, requestInit);
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

  return response;
}

export async function fetchJson<Target>({
  path,
  schema,
  method = "GET",
  body,
}: {
  path: string;
  schema: z.ZodType<Target>;
  method?: JsonRequestMethod;
  body?: unknown;
}): Promise<Target> {
  const response = await sendApiRequest({
    path,
    method,
    accept: "application/json",
    body,
  });

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

export async function fetchText({
  path,
  method = "GET",
}: {
  path: string;
  method?: JsonRequestMethod;
}): Promise<string> {
  const response = await sendApiRequest({
    path,
    method,
    accept: "text/html",
  });
  return response.text();
}
