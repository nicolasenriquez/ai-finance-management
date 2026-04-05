import type { PortfolioChartPeriod } from "../../core/api/schemas";

export const PORTFOLIO_CHART_PERIOD_OPTIONS: ReadonlyArray<PortfolioChartPeriod> =
  ["30D", "90D", "6M", "252D", "YTD", "MAX"];

export function isPortfolioChartPeriod(
  value: string | null | undefined,
): value is PortfolioChartPeriod {
  if (!value) {
    return false;
  }

  return PORTFOLIO_CHART_PERIOD_OPTIONS.some((period) => period === value);
}

export function resolvePortfolioChartPeriod(
  value: string | null | undefined,
  fallback: PortfolioChartPeriod = "30D",
): PortfolioChartPeriod {
  if (isPortfolioChartPeriod(value)) {
    return value;
  }

  return fallback;
}
