import {
  useMutation,
  useQuery,
} from "@tanstack/react-query";

import { shouldRetryApiError } from "../../core/api/errors";
import type {
  PortfolioChartPeriod,
  PortfolioHealthProfilePosture,
  PortfolioHierarchyGroupBy,
  PortfolioMLScope,
  PortfolioMLState,
  PortfolioMonteCarloRequest,
  PortfolioMonteCarloResponse,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportGenerateResponse,
  PortfolioTimeSeriesScope,
  PortfolioTransactionEvent,
  PortfolioTransactionsResponse,
} from "../../core/api/schemas";
import {
  fetchPortfolioContribution,
  fetchPortfolioEfficientFrontier,
  fetchPortfolioHealthSynthesis,
  fetchPortfolioHierarchy,
  fetchPortfolioMLForecasts,
  fetchPortfolioMLRegistry,
  fetchPortfolioMLSignals,
  fetchPortfolioReturnDistribution,
  fetchPortfolioRiskEvolution,
  fetchPortfolioQuantMetrics,
  fetchPortfolioQuantReportHtml,
  fetchPortfolioRiskEstimators,
  fetchPortfolioTimeSeries,
  fetchPortfolioTransactions,
  generatePortfolioMonteCarlo,
  generatePortfolioQuantReport,
} from "./api";

export type PortfolioRiskWindowDays = 30 | 90 | 126 | 252;
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
    "6M": 126,
    "252D": 252,
    YTD: 252,
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

export function usePortfolioHealthSynthesisQuery(
  period: PortfolioChartPeriod,
  options: {
    scope: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    profilePosture: PortfolioHealthProfilePosture;
    enabled?: boolean;
  },
) {
  const normalizedInstrumentSymbol =
    options.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    options.scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "health-synthesis",
      period,
      options.scope,
      normalizedInstrumentSymbol,
      options.profilePosture,
    ],
    queryFn: () =>
      fetchPortfolioHealthSynthesis(period, {
        scope: options.scope,
        instrumentSymbol: normalizedInstrumentSymbol,
        profilePosture: options.profilePosture,
      }),
    enabled: options.enabled ?? isValidScopeRequest,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioRiskEstimatorsQuery(windowDays: PortfolioRiskWindowDays) {
  return usePortfolioRiskEstimatorsScopedQuery(windowDays, {
    scope: "portfolio",
    instrumentSymbol: null,
    period: "252D",
  });
}

export function usePortfolioRiskEstimatorsScopedQuery(
  windowDays: PortfolioRiskWindowDays,
  options: {
    scope: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    period: PortfolioChartPeriod;
    enabled?: boolean;
  },
) {
  const normalizedInstrumentSymbol =
    options.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    options.scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "risk-estimators",
      windowDays,
      options.scope,
      normalizedInstrumentSymbol,
      options.period,
    ],
    queryFn: () =>
      fetchPortfolioRiskEstimators(windowDays, {
        scope: options.scope,
        instrumentSymbol: normalizedInstrumentSymbol,
        period: options.period,
      }),
    enabled: options.enabled ?? isValidScopeRequest,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioRiskEvolutionQuery(
  period: PortfolioChartPeriod,
  options: {
    scope: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    enabled?: boolean;
  },
) {
  const normalizedInstrumentSymbol =
    options.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    options.scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "risk-evolution",
      period,
      options.scope,
      normalizedInstrumentSymbol,
    ],
    queryFn: () =>
      fetchPortfolioRiskEvolution(period, {
        scope: options.scope,
        instrumentSymbol: normalizedInstrumentSymbol,
      }),
    enabled: options.enabled ?? isValidScopeRequest,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioReturnDistributionQuery(
  period: PortfolioChartPeriod,
  options: {
    scope: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    binCount?: number;
    enabled?: boolean;
  },
) {
  const normalizedInstrumentSymbol =
    options.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    options.scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "return-distribution",
      period,
      options.scope,
      normalizedInstrumentSymbol,
      options.binCount ?? 12,
    ],
    queryFn: () =>
      fetchPortfolioReturnDistribution(period, {
        scope: options.scope,
        instrumentSymbol: normalizedInstrumentSymbol,
        binCount: options.binCount,
      }),
    enabled: options.enabled ?? isValidScopeRequest,
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

export function usePortfolioEfficientFrontierQuery(
  period: PortfolioChartPeriod,
  options: {
    scope: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    frontierPoints?: number;
    enabled?: boolean;
  },
) {
  const normalizedInstrumentSymbol =
    options.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    options.scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "efficient-frontier",
      period,
      options.scope,
      normalizedInstrumentSymbol,
      options.frontierPoints ?? 24,
    ],
    queryFn: () =>
      fetchPortfolioEfficientFrontier(period, {
        scope: options.scope,
        instrumentSymbol: normalizedInstrumentSymbol,
        frontierPoints: options.frontierPoints,
      }),
    enabled: options.enabled ?? isValidScopeRequest,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioMLSignalQuery(options: {
  scope: PortfolioMLScope;
  instrumentSymbol?: string | null;
  enabled?: boolean;
}) {
  const normalizedInstrumentSymbol =
    options.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    options.scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "ml",
      "signals",
      options.scope,
      normalizedInstrumentSymbol,
    ],
    queryFn: () =>
      fetchPortfolioMLSignals({
        scope: options.scope,
        instrumentSymbol: normalizedInstrumentSymbol,
      }),
    enabled: options.enabled ?? isValidScopeRequest,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioMLForecastQuery(options: {
  scope: PortfolioMLScope;
  instrumentSymbol?: string | null;
  enabled?: boolean;
}) {
  const normalizedInstrumentSymbol =
    options.instrumentSymbol?.trim().toUpperCase() || null;
  const isValidScopeRequest =
    options.scope === "portfolio" || normalizedInstrumentSymbol !== null;
  return useQuery({
    queryKey: [
      "portfolio",
      "ml",
      "forecasts",
      options.scope,
      normalizedInstrumentSymbol,
    ],
    queryFn: () =>
      fetchPortfolioMLForecasts({
        scope: options.scope,
        instrumentSymbol: normalizedInstrumentSymbol,
      }),
    enabled: options.enabled ?? isValidScopeRequest,
    staleTime: 30_000,
    retry: (failureCount, error) =>
      failureCount < 1 && shouldRetryApiError(error),
  });
}

export function usePortfolioMLRegistryQuery(options?: {
  scope?: PortfolioMLScope | null;
  modelFamily?: string | null;
  lifecycleState?: PortfolioMLState | null;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: [
      "portfolio",
      "ml",
      "registry",
      options?.scope ?? null,
      options?.modelFamily ?? null,
      options?.lifecycleState ?? null,
    ],
    queryFn: () =>
      fetchPortfolioMLRegistry({
        scope: options?.scope ?? null,
        modelFamily: options?.modelFamily ?? null,
        lifecycleState: options?.lifecycleState ?? null,
      }),
    enabled: options?.enabled ?? true,
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

export function usePortfolioMonteCarloMutation() {
  return useMutation<
    PortfolioMonteCarloResponse,
    Error,
    PortfolioMonteCarloRequest
  >({
    mutationFn: (request) => generatePortfolioMonteCarlo(request),
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
