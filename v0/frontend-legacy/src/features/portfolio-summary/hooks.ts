import { useQuery } from "@tanstack/react-query";

import { shouldRetryApiError } from "../../core/api/errors";
import { fetchPortfolioSummary } from "./api";

export function usePortfolioSummaryQuery() {
  return useQuery({
    queryKey: ["portfolio", "summary"],
    queryFn: fetchPortfolioSummary,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}
