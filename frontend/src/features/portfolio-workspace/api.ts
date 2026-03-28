import { fetchJson } from "../../core/api/client";
import {
  portfolioContributionResponseSchema,
  portfolioRiskEstimatorsResponseSchema,
  portfolioTimeSeriesResponseSchema,
  portfolioTransactionsResponseSchema,
  type PortfolioChartPeriod,
  type PortfolioContributionResponse,
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

export function fetchPortfolioTransactions(): Promise<PortfolioTransactionsResponse> {
  return fetchJson({
    path: "/portfolio/transactions",
    schema: portfolioTransactionsResponseSchema,
  });
}
