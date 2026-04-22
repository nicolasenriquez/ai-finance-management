import type {
  QueryClient,
  UseQueryResult,
} from "@tanstack/react-query";

import {
  buildPortfolioApiFixtureKey,
  buildPortfolioApiPath,
  resolvePortfolioApiFixture,
} from "./portfolio";

export type PortfolioRouteModuleStatus =
  | "loading"
  | "ready"
  | "empty"
  | "error";

export type PortfolioRouteQueryResource<T> = {
  status: PortfolioRouteModuleStatus;
  data: T | null;
  errorMessage: string | null;
  reload: () => void;
};

type QueryObject = Record<string, string | undefined>;

type QueryStateLike<T> = Pick<
  UseQueryResult<T, Error>,
  "data" | "error" | "isError" | "isPending" | "refetch"
>;

export function buildPortfolioRouteQueryKey(
  path: string,
  query: QueryObject = {},
): readonly ["portfolio", string] {
  const fixtureKey = buildPortfolioApiFixtureKey(path, query);
  return ["portfolio", fixtureKey] as const;
}

export function createPortfolioRouteQueryFn<T>({
  path,
  loader,
  query = {},
}: {
  path: string;
  loader: () => Promise<T>;
  query?: QueryObject;
}): () => Promise<T> {
  const fixtureKey = buildPortfolioApiFixtureKey(path, query);
  const requestPath = buildPortfolioApiPath(path, query);

  return async (): Promise<T> => {
    const fixtureData = resolvePortfolioApiFixture<T>(fixtureKey);
    if (fixtureData !== undefined) {
      return fixtureData;
    }

    return loader().catch((error: unknown) => {
      if (error instanceof Error) {
        error.message = `${error.message} (request: ${requestPath})`;
        throw error;
      }
      throw error;
    });
  };
}

export function resolvePortfolioRouteQueryResource<T>(
  queryResult: QueryStateLike<T>,
  isEmpty?: (data: T) => boolean,
): PortfolioRouteQueryResource<T> {
  if (queryResult.isPending) {
    return {
      status: "loading",
      data: null,
      errorMessage: null,
      reload: () => {
        void queryResult.refetch();
      },
    };
  }

  if (queryResult.isError) {
    return {
      status: "error",
      data: null,
      errorMessage: queryResult.error?.message ?? "Unable to load portfolio data.",
      reload: () => {
        void queryResult.refetch();
      },
    };
  }

  const data = queryResult.data ?? null;
  if (data !== null && isEmpty?.(data)) {
    return {
      status: "empty",
      data,
      errorMessage: null,
      reload: () => {
        void queryResult.refetch();
      },
    };
  }

  return {
    status: "ready",
    data,
    errorMessage: null,
    reload: () => {
      void queryResult.refetch();
    },
  };
}

export function resolvePortfolioRouteStatus(
  resources: Array<PortfolioRouteQueryResource<unknown>>,
): PortfolioRouteModuleStatus {
  if (resources.some((resource) => resource.status === "loading")) {
    return "loading";
  }
  if (resources.some((resource) => resource.status === "error")) {
    return "error";
  }
  if (resources.some((resource) => resource.status === "empty")) {
    return "empty";
  }
  return "ready";
}

export function resolvePortfolioRouteErrorMessage(
  resources: Array<PortfolioRouteQueryResource<unknown>>,
): string | null {
  for (const resource of resources) {
    if (resource.status === "error" && resource.errorMessage) {
      return resource.errorMessage;
    }
  }
  return null;
}

export async function prefetchPortfolioRouteQuery<T>({
  queryClient,
  path,
  query = {},
  loader,
}: {
  queryClient: QueryClient;
  path: string;
  query?: QueryObject;
  loader: () => Promise<T>;
}): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey: buildPortfolioRouteQueryKey(path, query),
    queryFn: createPortfolioRouteQueryFn({
      path,
      query,
      loader,
    }),
  });
}
