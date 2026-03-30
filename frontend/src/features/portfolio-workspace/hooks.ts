import {
  useMutation,
  useQuery,
} from "@tanstack/react-query";

import { shouldRetryApiError } from "../../core/api/errors";
import type {
  PortfolioChartPeriod,
  PortfolioHierarchyGroupBy,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportGenerateResponse,
  PortfolioTimeSeriesScope,
  PortfolioTransactionEvent,
  PortfolioTransactionsResponse,
} from "../../core/api/schemas";
import {
  fetchPortfolioContribution,
  fetchPortfolioHierarchy,
  fetchPortfolioQuantMetrics,
  fetchPortfolioQuantReportHtml,
  fetchPortfolioRiskEstimators,
  fetchPortfolioTimeSeries,
  fetchPortfolioTransactions,
  generatePortfolioQuantReport,
} from "./api";

export type PortfolioRiskWindowDays = 30 | 90 | 252;
export type { PortfolioTransactionEvent, PortfolioTransactionsResponse };

type PortfolioTimeSeriesQueryOptions = {
  scope?: PortfolioTimeSeriesScope;
  instrumentSymbol?: string | null;
  enabled?: boolean;
};

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

export function usePortfolioTimeSeriesQuery(
  period: PortfolioChartPeriod,
  options?: PortfolioTimeSeriesQueryOptions,
) {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "time-series",
      period,
      scope,
      normalizedInstrumentSymbol,
    ],
    queryFn: () =>
      fetchPortfolioTimeSeries(period, {
        scope,
        instrumentSymbol: normalizedInstrumentSymbol,
      }),
    enabled: options?.enabled ?? isValidScopeRequest,
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

export function usePortfolioQuantMetricsQuery(period: PortfolioChartPeriod) {
  return useQuery({
    queryKey: ["portfolio", "quant-metrics", period],
    queryFn: () => fetchPortfolioQuantMetrics(period),
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

export function usePortfolioHierarchyQuery(groupBy: PortfolioHierarchyGroupBy) {
  return useQuery({
    queryKey: ["portfolio", "hierarchy", groupBy],
    queryFn: () => fetchPortfolioHierarchy(groupBy),
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioQuantReportGenerateMutation() {
  return useMutation<
    PortfolioQuantReportGenerateResponse,
    Error,
    PortfolioQuantReportGenerateRequest
  >({
    mutationFn: (request) => generatePortfolioQuantReport(request),
  });
}

export function usePortfolioQuantReportHtmlQuery(reportId: string | null) {
  return useQuery({
    queryKey: ["portfolio", "quant-report-html", reportId],
    queryFn: () => {
      if (!reportId) {
        throw new Error("Quant report id is required.");
      }
      return fetchPortfolioQuantReportHtml(reportId);
    },
    enabled: reportId !== null,
    staleTime: 0,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}
