import {
  fetchJson,
  fetchText,
} from "../../core/api/client";
import {
  portfolioCommandCenterResponseSchema,
  portfolioContributionToRiskResponseSchema,
  portfolioContributionResponseSchema,
  portfolioCorrelationResponseSchema,
  portfolioEfficientFrontierResponseSchema,
  portfolioExposureResponseSchema,
  portfolioHealthSynthesisResponseSchema,
  portfolioHierarchyResponseSchema,
  portfolioMLAnomaliesResponseSchema,
  portfolioMLClustersResponseSchema,
  portfolioMLForecastResponseSchema,
  portfolioMLRegistryResponseSchema,
  portfolioMLSignalResponseSchema,
  portfolioMonteCarloResponseSchema,
  portfolioQuantMetricsResponseSchema,
  portfolioQuantReportGenerateResponseSchema,
  portfolioReturnDistributionResponseSchema,
  portfolioRiskEvolutionResponseSchema,
  portfolioRiskEstimatorsResponseSchema,
  portfolioTimeSeriesResponseSchema,
  portfolioTransactionsResponseSchema,
  portfolioNewsContextResponseSchema,
  portfolioRebalancingScenarioRequestSchema,
  portfolioRebalancingScenarioResponseSchema,
  portfolioRebalancingStrategiesResponseSchema,
  type PortfolioChartPeriod,
  type PortfolioCommandCenterResponse,
  type PortfolioContributionToRiskResponse,
  type PortfolioContributionResponse,
  type PortfolioCorrelationResponse,
  type PortfolioEfficientFrontierResponse,
  type PortfolioExposureResponse,
  type PortfolioHealthProfilePosture,
  type PortfolioHealthSynthesisResponse,
  type PortfolioHierarchyGroupBy,
  type PortfolioHierarchyResponse,
  type PortfolioMLAnomaliesResponse,
  type PortfolioMLClustersResponse,
  type PortfolioMLForecastResponse,
  type PortfolioMLRegistryResponse,
  type PortfolioMLScope,
  type PortfolioMLSignalResponse,
  type PortfolioMLState,
  type PortfolioNewsContextResponse,
  type PortfolioMonteCarloRequest,
  type PortfolioMonteCarloResponse,
  type PortfolioQuantMetricsResponse,
  type PortfolioQuantReportGenerateRequest,
  type PortfolioQuantReportGenerateResponse,
  type PortfolioRebalancingScenarioRequest,
  type PortfolioRebalancingScenarioResponse,
  type PortfolioRebalancingStrategiesResponse,
  type PortfolioReturnDistributionResponse,
  type PortfolioRiskEvolutionResponse,
  type PortfolioRiskEstimatorsResponse,
  type PortfolioTimeSeriesScope,
  type PortfolioTimeSeriesResponse,
  type PortfolioTransactionsResponse,
} from "../../core/api/schemas";

export function fetchPortfolioCommandCenter(): Promise<PortfolioCommandCenterResponse> {
  return fetchJson({
    path: "/portfolio/command-center",
    schema: portfolioCommandCenterResponseSchema,
  });
}

export function fetchPortfolioExposure(
  dimension: "asset_class" | "sector" | "currency" | "country" = "sector",
): Promise<PortfolioExposureResponse> {
  const query = new URLSearchParams({
    dimension,
  });
  return fetchJson({
    path: `/portfolio/exposure?${query.toString()}`,
    schema: portfolioExposureResponseSchema,
  });
}

export function fetchPortfolioContributionToRisk(): Promise<PortfolioContributionToRiskResponse> {
  return fetchJson({
    path: "/portfolio/contribution-to-risk",
    schema: portfolioContributionToRiskResponseSchema,
  });
}

export function fetchPortfolioCorrelation(
  limitSymbols = 8,
): Promise<PortfolioCorrelationResponse> {
  const query = new URLSearchParams({
    limit_symbols: String(limitSymbols),
  });
  return fetchJson({
    path: `/portfolio/correlation?${query.toString()}`,
    schema: portfolioCorrelationResponseSchema,
  });
}

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

export function fetchPortfolioEfficientFrontier(
  period: PortfolioChartPeriod,
  options?: {
    scope?: PortfolioTimeSeriesScope;
    instrumentSymbol?: string | null;
    frontierPoints?: number;
  },
): Promise<PortfolioEfficientFrontierResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    period,
    scope,
    frontier_points: String(options?.frontierPoints ?? 24),
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/efficient-frontier?${query.toString()}`,
    schema: portfolioEfficientFrontierResponseSchema,
  });
}

export function fetchPortfolioMLSignals(options?: {
  scope?: PortfolioMLScope;
  instrumentSymbol?: string | null;
}): Promise<PortfolioMLSignalResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    scope,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/ml/signals?${query.toString()}`,
    schema: portfolioMLSignalResponseSchema,
  });
}

export function fetchPortfolioMLClusters(options?: {
  scope?: PortfolioMLScope;
  instrumentSymbol?: string | null;
}): Promise<PortfolioMLClustersResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    scope,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/ml/clusters?${query.toString()}`,
    schema: portfolioMLClustersResponseSchema,
  });
}

export function fetchPortfolioMLAnomalies(options?: {
  scope?: PortfolioMLScope;
  instrumentSymbol?: string | null;
}): Promise<PortfolioMLAnomaliesResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    scope,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/ml/anomalies?${query.toString()}`,
    schema: portfolioMLAnomaliesResponseSchema,
  });
}

export function fetchPortfolioMLForecasts(options?: {
  scope?: PortfolioMLScope;
  instrumentSymbol?: string | null;
}): Promise<PortfolioMLForecastResponse> {
  const scope = options?.scope ?? "portfolio";
  const normalizedInstrumentSymbol =
    options?.instrumentSymbol?.trim().toUpperCase() || null;
  const query = new URLSearchParams({
    scope,
  });
  if (scope === "instrument_symbol" && normalizedInstrumentSymbol) {
    query.set("instrument_symbol", normalizedInstrumentSymbol);
  }
  return fetchJson({
    path: `/portfolio/ml/forecasts?${query.toString()}`,
    schema: portfolioMLForecastResponseSchema,
  });
}

export function fetchPortfolioMLRegistry(options?: {
  scope?: PortfolioMLScope | null;
  modelFamily?: string | null;
  lifecycleState?: PortfolioMLState | null;
}): Promise<PortfolioMLRegistryResponse> {
  const query = new URLSearchParams();
  if (options?.scope) {
    query.set("scope", options.scope);
  }
  if (options?.modelFamily && options.modelFamily.trim() !== "") {
    query.set("model_family", options.modelFamily.trim());
  }
  if (options?.lifecycleState) {
    query.set("lifecycle_state", options.lifecycleState);
  }
  return fetchJson({
    path:
      query.toString().length > 0
        ? `/portfolio/ml/registry?${query.toString()}`
        : "/portfolio/ml/registry",
    schema: portfolioMLRegistryResponseSchema,
  });
}

export function fetchPortfolioTransactions(): Promise<PortfolioTransactionsResponse> {
  return fetchJson({
    path: "/portfolio/transactions",
    schema: portfolioTransactionsResponseSchema,
  });
}

export function fetchPortfolioRebalancingStrategies():
Promise<PortfolioRebalancingStrategiesResponse> {
  return fetchJson({
    path: "/portfolio/rebalancing/strategies",
    schema: portfolioRebalancingStrategiesResponseSchema,
  });
}

export function postPortfolioRebalancingScenario(
  request: PortfolioRebalancingScenarioRequest,
): Promise<PortfolioRebalancingScenarioResponse> {
  const normalizedRequest = portfolioRebalancingScenarioRequestSchema.parse(request);
  return fetchJson({
    path: "/portfolio/rebalancing/scenario",
    method: "POST",
    body: normalizedRequest,
    schema: portfolioRebalancingScenarioResponseSchema,
  });
}

export function fetchPortfolioNewsContext(): Promise<PortfolioNewsContextResponse> {
  return fetchJson({
    path: "/portfolio/news/context",
    schema: portfolioNewsContextResponseSchema,
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
