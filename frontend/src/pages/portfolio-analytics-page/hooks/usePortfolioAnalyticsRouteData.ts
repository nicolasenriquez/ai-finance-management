import { useMemo } from "react";

import { useQueries } from "@tanstack/react-query";

import {
  fetchPortfolioContributionResponse,
  fetchPortfolioHierarchyResponse,
  fetchPortfolioSummaryResponse,
  fetchPortfolioTimeSeriesResponse,
  formatPortfolioMoney,
  formatPortfolioPercent,
  getPortfolioContributionRowsByImpact,
  getPortfolioSummaryRowsByMarketValue,
  isPortfolioContributionEmpty,
  isPortfolioHierarchyEmpty,
  isPortfolioSummaryEmpty,
  isPortfolioTimeSeriesEmpty,
  resolvePortfolioAssetDetailHref,
  resolveTickerActionState,
} from "../../../core/api/portfolio";
import {
  buildPortfolioRouteQueryKey,
  createPortfolioRouteQueryFn,
  resolvePortfolioRouteErrorMessage,
  resolvePortfolioRouteQueryResource,
  resolvePortfolioRouteStatus,
} from "../../../core/api/portfolio-route-query";

export type AnalyticsContributionDriver = {
  ticker: string;
  contributionValue: number;
  contribution: string;
  frame: string;
  consistency: string;
};

export type AnalyticsDrillDownRow = {
  ticker: string;
  sector: string;
  contribution: string;
  consistency: string;
  posture: string;
};

export type AnalyticsPerformancePoint = {
  capturedAt: string;
  portfolioValue: number;
  benchmarkValue: number;
};

export type PortfolioAnalyticsRouteData = {
  status: "loading" | "ready" | "empty" | "error";
  errorMessage: string | null;
  reload: () => void;
  assetDetailHref: string;
  contributionDrivers: AnalyticsContributionDriver[];
  drillDownRows: AnalyticsDrillDownRow[];
  performanceSeries: AnalyticsPerformancePoint[];
};

function resolveValue(value: string | number | null | undefined): number {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
}

export function usePortfolioAnalyticsRouteData(): PortfolioAnalyticsRouteData {
  const [
    summaryQuery,
    hierarchyQuery,
    contributionQuery,
    timeSeriesQuery,
  ] = useQueries({
    queries: [
      {
        queryKey: buildPortfolioRouteQueryKey("/portfolio/summary"),
        queryFn: createPortfolioRouteQueryFn({
          path: "/portfolio/summary",
          loader: fetchPortfolioSummaryResponse,
        }),
        retry: false,
      },
      {
        queryKey: buildPortfolioRouteQueryKey("/portfolio/hierarchy", {
          group_by: "sector",
        }),
        queryFn: createPortfolioRouteQueryFn({
          path: "/portfolio/hierarchy",
          query: {
            group_by: "sector",
          },
          loader: fetchPortfolioHierarchyResponse,
        }),
        retry: false,
      },
      {
        queryKey: buildPortfolioRouteQueryKey("/portfolio/contribution", { period: "YTD" }),
        queryFn: createPortfolioRouteQueryFn({
          path: "/portfolio/contribution",
          query: {
            period: "YTD",
          },
          loader: () => fetchPortfolioContributionResponse("YTD"),
        }),
        retry: false,
      },
      {
        queryKey: buildPortfolioRouteQueryKey("/portfolio/time-series", {
          period: "90D",
          scope: "portfolio",
        }),
        queryFn: createPortfolioRouteQueryFn({
          path: "/portfolio/time-series",
          query: {
            period: "90D",
            scope: "portfolio",
          },
          loader: () => fetchPortfolioTimeSeriesResponse("90D", "portfolio"),
        }),
        retry: false,
      },
    ],
  });

  const summary = resolvePortfolioRouteQueryResource(
    summaryQuery,
    isPortfolioSummaryEmpty,
  );
  const hierarchy = resolvePortfolioRouteQueryResource(
    hierarchyQuery,
    isPortfolioHierarchyEmpty,
  );
  const contribution = resolvePortfolioRouteQueryResource(
    contributionQuery,
    isPortfolioContributionEmpty,
  );
  const timeSeries = resolvePortfolioRouteQueryResource(
    timeSeriesQuery,
    isPortfolioTimeSeriesEmpty,
  );

  const resources = [summary, hierarchy, contribution, timeSeries];
  const status = resolvePortfolioRouteStatus(resources);
  const errorMessage = resolvePortfolioRouteErrorMessage(resources);

  const summaryRows = useMemo(
    () => getPortfolioSummaryRowsByMarketValue(summary.data?.rows ?? []),
    [summary.data?.rows],
  );
  const contributionRows = useMemo(
    () => getPortfolioContributionRowsByImpact(contribution.data?.rows ?? []),
    [contribution.data?.rows],
  );

  const sectorBySymbol = useMemo(() => {
    const mappedSectorBySymbol = new Map<string, string>();
    for (const group of hierarchy.data?.groups ?? []) {
      for (const asset of group.assets) {
        mappedSectorBySymbol.set(asset.instrument_symbol, asset.sector_label);
      }
    }
    return mappedSectorBySymbol;
  }, [hierarchy.data?.groups]);

  const contributionDrivers = useMemo<AnalyticsContributionDriver[]>(
    () =>
      contributionRows.slice(0, 5).map((row) => {
        const summaryRow = summaryRows.find((candidate) => candidate.instrument_symbol === row.instrument_symbol);
        const contributionValue = resolveValue(row.contribution_pnl_usd);
        const consistency = resolveValue(summaryRow?.unrealized_gain_pct) >= 0 ? "Positive" : "Negative";
        return {
          ticker: row.instrument_symbol,
          contributionValue,
          contribution: formatPortfolioMoney(contributionValue),
          frame: sectorBySymbol.get(row.instrument_symbol) ?? "Portfolio contribution",
          consistency,
        };
      }),
    [contributionRows, sectorBySymbol, summaryRows],
  );

  const drillDownRows = useMemo<AnalyticsDrillDownRow[]>(
    () =>
      summaryRows.slice(0, 6).map((row) => ({
        ticker: row.instrument_symbol,
        sector: sectorBySymbol.get(row.instrument_symbol) ?? "Unassigned",
        contribution: formatPortfolioPercent(row.unrealized_gain_pct, 1),
        consistency: resolveValue(row.unrealized_gain_pct) >= 0 ? "High" : "Low",
        posture: resolveTickerActionState(row.unrealized_gain_pct),
      })),
    [sectorBySymbol, summaryRows],
  );

  const performanceSeries = useMemo<AnalyticsPerformancePoint[]>(
    () =>
      (timeSeries.data?.points ?? []).slice(-40).map((point) => ({
        capturedAt: point.captured_at,
        portfolioValue: resolveValue(point.portfolio_value_usd),
        benchmarkValue:
          resolveValue(point.benchmark_sp500_value_usd) ||
          resolveValue(point.benchmark_nasdaq100_value_usd),
      })),
    [timeSeries.data?.points],
  );

  return {
    status,
    errorMessage,
    reload: () => {
      summary.reload();
      hierarchy.reload();
      contribution.reload();
      timeSeries.reload();
    },
    assetDetailHref: resolvePortfolioAssetDetailHref(summary.data),
    contributionDrivers,
    drillDownRows,
    performanceSeries,
  };
}
