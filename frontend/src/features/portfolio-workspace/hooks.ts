import { useQuery } from "@tanstack/react-query";

import { shouldRetryApiError } from "../../core/api/errors";
import type {
  PortfolioChartPeriod,
  PortfolioTransactionEvent,
  PortfolioTransactionsResponse,
} from "../../core/api/schemas";
import {
  fetchPortfolioContribution,
  fetchPortfolioRiskEstimators,
  fetchPortfolioTimeSeries,
  fetchPortfolioTransactions,
} from "./api";

export type PortfolioRiskWindowDays = 30 | 90 | 252;
export type { PortfolioTransactionEvent, PortfolioTransactionsResponse };

const RISK_WINDOW_PERIOD_MAP: Record<PortfolioChartPeriod, PortfolioRiskWindowDays> =
  {
    "30D": 30,
    "90D": 90,
    "252D": 252,
    MAX: 252,
  };

export function mapChartPeriodToRiskWindow(
  period: PortfolioChartPeriod,
): PortfolioRiskWindowDays {
  return RISK_WINDOW_PERIOD_MAP[period];
}

export function usePortfolioTimeSeriesQuery(period: PortfolioChartPeriod) {
  return useQuery({
    queryKey: ["portfolio", "time-series", period],
    queryFn: () => fetchPortfolioTimeSeries(period),
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioContributionQuery(period: PortfolioChartPeriod) {
  return useQuery({
    queryKey: ["portfolio", "contribution", period],
    queryFn: () => fetchPortfolioContribution(period),
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioRiskEstimatorsQuery(windowDays: PortfolioRiskWindowDays) {
  return useQuery({
    queryKey: ["portfolio", "risk-estimators", windowDays],
    queryFn: () => fetchPortfolioRiskEstimators(windowDays),
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioTransactionsQuery() {
  return useQuery({
    queryKey: ["portfolio", "transactions"],
    queryFn: fetchPortfolioTransactions,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}
