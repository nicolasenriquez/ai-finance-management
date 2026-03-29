import {
  fetchJson,
  fetchText,
} from "../../core/api/client";
import {
  portfolioContributionResponseSchema,
  portfolioHierarchyResponseSchema,
  portfolioQuantMetricsResponseSchema,
  portfolioQuantReportGenerateResponseSchema,
  portfolioRiskEstimatorsResponseSchema,
  portfolioTimeSeriesResponseSchema,
  portfolioTransactionsResponseSchema,
  type PortfolioChartPeriod,
  type PortfolioContributionResponse,
  type PortfolioHierarchyGroupBy,
  type PortfolioHierarchyResponse,
  type PortfolioQuantMetricsResponse,
  type PortfolioQuantReportGenerateRequest,
  type PortfolioQuantReportGenerateResponse,
  type PortfolioRiskEstimatorsResponse,
  type PortfolioTimeSeriesResponse,
  type PortfolioTransactionsResponse,
} from "../../core/api/schemas";

export function fetchPortfolioTimeSeries(
  period: PortfolioChartPeriod,
): Promise<PortfolioTimeSeriesResponse> {
  const query = new URLSearchParams({
    period,
  });
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

export function fetchPortfolioRiskEstimators(
  windowDays: 30 | 90 | 252,
): Promise<PortfolioRiskEstimatorsResponse> {
  const query = new URLSearchParams({
    window_days: String(windowDays),
  });
  return fetchJson({
    path: `/portfolio/risk-estimators?${query.toString()}`,
    schema: portfolioRiskEstimatorsResponseSchema,
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

export function fetchPortfolioQuantReportHtml(reportId: string): Promise<string> {
  return fetchText({
    path: `/portfolio/quant-reports/${encodeURIComponent(reportId)}`,
  });
}
