import { useMemo } from "react";

import {
  formatPortfolioMoney,
  formatPortfolioPercent,
  getPortfolioContributionRowsByImpact,
  getPortfolioSummaryRowsByMarketValue,
  resolvePortfolioAssetDetailHref,
  resolveTickerActionState,
  usePortfolioContributionResource,
  usePortfolioHierarchyResource,
  usePortfolioSummaryResource,
} from "../../../core/api/portfolio";

export type AnalyticsContributionDriver = {
  ticker: string;
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

export type PortfolioAnalyticsRouteData = {
  status: "loading" | "ready" | "empty" | "error";
  errorMessage: string | null;
  reload: () => void;
  assetDetailHref: string;
  contributionDrivers: AnalyticsContributionDriver[];
  drillDownRows: AnalyticsDrillDownRow[];
};

function resolveValue(value: string | number | null | undefined): number {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
}

export function usePortfolioAnalyticsRouteData(): PortfolioAnalyticsRouteData {
  const summary = usePortfolioSummaryResource();
  const hierarchy = usePortfolioHierarchyResource();
  const contribution = usePortfolioContributionResource("YTD");

  const status = useMemo(() => {
    if (summary.status === "loading" || hierarchy.status === "loading" || contribution.status === "loading") {
      return "loading" as const;
    }
    if (summary.status === "error" || hierarchy.status === "error" || contribution.status === "error") {
      return "error" as const;
    }
    if (summary.status === "empty" || hierarchy.status === "empty" || contribution.status === "empty") {
      return "empty" as const;
    }
    return "ready" as const;
  }, [contribution.status, hierarchy.status, summary.status]);

  const errorMessage = summary.errorMessage ?? hierarchy.errorMessage ?? contribution.errorMessage;

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
      contributionRows.slice(0, 3).map((row) => {
        const summaryRow = summaryRows.find((candidate) => candidate.instrument_symbol === row.instrument_symbol);
        const contributionValue = formatPortfolioMoney(row.contribution_pnl_usd);
        const consistency = resolveValue(summaryRow?.unrealized_gain_pct) >= 0 ? "Positive" : "Negative";
        return {
          ticker: row.instrument_symbol,
          contribution: contributionValue,
          frame: sectorBySymbol.get(row.instrument_symbol) ?? "Portfolio contribution",
          consistency,
        };
      }),
    [contributionRows, sectorBySymbol, summaryRows],
  );

  const drillDownRows = useMemo<AnalyticsDrillDownRow[]>(
    () =>
      summaryRows.slice(0, 3).map((row) => ({
        ticker: row.instrument_symbol,
        sector: sectorBySymbol.get(row.instrument_symbol) ?? "Unassigned",
        contribution: formatPortfolioPercent(row.unrealized_gain_pct, 1),
        consistency: resolveValue(row.unrealized_gain_pct) >= 0 ? "High" : "Low",
        posture: resolveTickerActionState(row.unrealized_gain_pct),
      })),
    [sectorBySymbol, summaryRows],
  );

  return {
    status,
    errorMessage,
    reload: () => {
      summary.reload();
      hierarchy.reload();
      contribution.reload();
    },
    assetDetailHref: resolvePortfolioAssetDetailHref(summary.data),
    contributionDrivers,
    drillDownRows,
  };
}
