import { useQuery } from "@tanstack/react-query";

import { shouldRetryApiError } from "../../core/api/errors";
import { fetchPortfolioLotDetail } from "./api";

export function usePortfolioLotDetailQuery(symbol: string) {
  return useQuery({
    queryKey: ["portfolio", "lot-detail", symbol],
    queryFn: () => fetchPortfolioLotDetail(symbol),
    enabled: symbol.trim().length > 0,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}
