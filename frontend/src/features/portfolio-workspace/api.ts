import {
  fetchJson,
  fetchText,
} from "../../core/api/client";
import {
  portfolioContributionResponseSchema,
  portfolioHealthSynthesisResponseSchema,
  portfolioHierarchyResponseSchema,
  portfolioMonteCarloResponseSchema,
  portfolioQuantMetricsResponseSchema,
  portfolioQuantReportGenerateResponseSchema,
  portfolioReturnDistributionResponseSchema,
  portfolioRiskEvolutionResponseSchema,
  portfolioRiskEstimatorsResponseSchema,
  portfolioTimeSeriesResponseSchema,
  portfolioTransactionsResponseSchema,
  type PortfolioChartPeriod,
  type PortfolioContributionResponse,
  type PortfolioHealthProfilePosture,
  type PortfolioHealthSynthesisResponse,
  type PortfolioHierarchyGroupBy,
  type PortfolioHierarchyResponse,
  type PortfolioMonteCarloRequest,
  type PortfolioMonteCarloResponse,
  type PortfolioQuantMetricsResponse,
  type PortfolioQuantReportGenerateRequest,
  type PortfolioQuantReportGenerateResponse,
  type PortfolioReturnDistributionResponse,
  type PortfolioRiskEvolutionResponse,
  type PortfolioRiskEstimatorsResponse,
  type PortfolioTimeSeriesScope,
  type PortfolioTimeSeriesResponse,
  type PortfolioTransactionsResponse,
} from "../../core/api/schemas";

export function fetchPortfolioTimeSeries(
  period: PortfolioChartPeriod,
  options?: {
    scope?: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
  },
): Promise<PortfolioTimeSeriesResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    period,
    scope,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/time-series?${query.toString()}`,
    schema: portfolioTimeSeriesResponseSchema,
  });
}

export function fetchPortfolioContribution(
  period: PortfolioChartPeriod,
): Promise<PortfolioContributionResponse> {
  const query = new URLSearchParams({
    period,
  });
  return fetchJson({
    path: `/portfolio/contribution?${query.toString()}`,
    schema: portfolioContributionResponseSchema,
  });
}

export function fetchPortfolioHealthSynthesis(
  period: PortfolioChartPeriod,
  options?: {
    scope?: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    profilePosture?: PortfolioHealthProfilePosture;
  },
): Promise<PortfolioHealthSynthesisResponse> {
  const scope = options?.scope ?? "portfolio";
  const profilePosture = options?.profilePosture ?? "balanced";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    period,
    scope,
    profile_posture: profilePosture,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/health-synthesis?${query.toString()}`,
    schema: portfolioHealthSynthesisResponseSchema,
  });
}

export function fetchPortfolioRiskEstimators(
  windowDays: 30 | 90 | 126 | 252,
  options?: {
    scope?: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    period?: PortfolioChartPeriod;
  },
): Promise<PortfolioRiskEstimatorsResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const period = options?.period ?? "252D";
  const query = new URLSearchParams({
    window_days: String(windowDays),
    scope,
    period,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/risk-estimators?${query.toString()}`,
    schema: portfolioRiskEstimatorsResponseSchema,
  });
}

export function fetchPortfolioRiskEvolution(
  period: PortfolioChartPeriod,
  options?: {
    scope?: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
  },
): Promise<PortfolioRiskEvolutionResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    period,
    scope,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/risk-evolution?${query.toString()}`,
    schema: portfolioRiskEvolutionResponseSchema,
  });
}

export function fetchPortfolioReturnDistribution(
  period: PortfolioChartPeriod,
  options?: {
    scope?: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    binCount?: number;
  },
): Promise<PortfolioReturnDistributionResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    period,
    scope,
    bin_count: String(options?.binCount ?? 12),
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/return-distribution?${query.toString()}`,
    schema: portfolioReturnDistributionResponseSchema,
  });
}

export function fetchPortfolioQuantMetrics(
  period: PortfolioChartPeriod,
): Promise<PortfolioQuantMetricsResponse> {
  const query = new URLSearchParams({
    period,
  });
  return fetchJson({
    path: `/portfolio/quant-metrics?${query.toString()}`,
    schema: portfolioQuantMetricsResponseSchema,
  });
}

export function fetchPortfolioTransactions(): Promise<PortfolioTransactionsResponse> {
  return fetchJson({
    path: "/portfolio/transactions",
    schema: portfolioTransactionsResponseSchema,
  });
}

export function fetchPortfolioHierarchy(
  groupBy: PortfolioHierarchyGroupBy,
): Promise<PortfolioHierarchyResponse> {
  const query = new URLSearchParams({
    group_by: groupBy,
  });
  return fetchJson({
    path: `/portfolio/hierarchy?${query.toString()}`,
    schema: portfolioHierarchyResponseSchema,
  });
}

export function generatePortfolioQuantReport(
  request: PortfolioQuantReportGenerateRequest,
): Promise<PortfolioQuantReportGenerateResponse> {
  return fetchJson({
    path: "/portfolio/quant-reports",
    method: "POST",
    body: request,
    schema: portfolioQuantReportGenerateResponseSchema,
  });
}

export function generatePortfolioMonteCarlo(
  request: PortfolioMonteCarloRequest,
): Promise<PortfolioMonteCarloResponse> {
  const normalizedScope = request.scope;
  const normalizedInstrumentSymbol =
    request.instrument_symbol?.trim().toUpperCase() || null;
  return fetchJson({
    path: "/portfolio/monte-carlo",
    method: "POST",
    body: {
      ...request,
      scope: normalizedScope,
      instrument_symbol:
        normalizedScope === "instrument_symbol" ? normalizedInstrumentSymbol : null,
    },
    schema: portfolioMonteCarloResponseSchema,
  });
}

export function fetchPortfolioQuantReportHtml(reportId: string): Promise<string> {
  return fetchText({
    path: `/portfolio/quant-reports/${encodeURIComponent(reportId)}`,
  });
}
