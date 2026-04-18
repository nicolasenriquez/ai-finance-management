import { useMemo } from "react";

import {
  formatPortfolioMoney,
  formatPortfolioPercent,
  getPortfolioSummaryRowsByMarketValue,
  resolvePortfolioAssetDetailHref,
  resolvePortfolioSummaryKpis,
  resolveTickerActionState,
  usePortfolioCommandCenterResource,
  usePortfolioHierarchyResource,
  usePortfolioSummaryResource,
} from "../../../core/api/portfolio";
import { type HierarchyPivotGroup } from "../../../features/portfolio-hierarchy/HierarchyPivotTable";

export type HomeKpi = {
  label: string;
  value: string;
  delta: string;
};

export type HomeTopMover = {
  ticker: string;
  move: string;
  catalyst: string;
};

export type HomeAttentionItem = {
  label: string;
  status: string;
  note: string;
};

export type HomeAllocationSlice = {
  sleeve: string;
  weight: string;
  posture: string;
};

export type HomeHoldingsSummaryRow = {
  ticker: string;
  weight: string;
  unrealized: string;
  state: string;
};

export type PortfolioHomeRouteData = {
  status: "loading" | "ready" | "empty" | "error";
  errorMessage: string | null;
  reload: () => void;
  assetDetailHref: string;
  kpis: HomeKpi[];
  topMovers: HomeTopMover[];
  attentionItems: HomeAttentionItem[];
  allocationSlices: HomeAllocationSlice[];
  holdingsSummaryRows: HomeHoldingsSummaryRow[];
  hierarchyPivotGroups: HierarchyPivotGroup[];
};

function resolveValue(value: string | number | null | undefined): number {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
}

function resolveMomentumCatalyst(unrealizedGainPct: string | number | null | undefined): string {
  const normalizedGain = resolveValue(unrealizedGainPct);
  if (normalizedGain < 0) {
    return `Unrealized loss ${formatPortfolioPercent(normalizedGain, 1)}`;
  }

  return `Unrealized gain ${formatPortfolioPercent(normalizedGain, 1)}`;
}

function resolveAttentionStatus(severity: string): string {
  if (severity === "elevated_risk") {
    return "Watch now";
  }
  if (severity === "caution") {
    return "Review";
  }
  return "Info";
}

function selectCompactHierarchyAssets<
  T extends {
    instrument_symbol: string;
  },
>(assets: T[]): T[] {
  if (assets.length <= 2) {
    return assets;
  }

  return assets.filter((_, index) => index === 0 || index === 2).slice(0, 2);
}

function buildHierarchyPivotGroups(
  totalMarketValue: number,
  groups: Array<{
    group_key: string;
    group_label: string;
    assets: Array<{
      instrument_symbol: string;
      market_value_usd: string | number | null | undefined;
      profit_loss_usd: string | number | null | undefined;
      change_pct?: string | number | null | undefined;
    }>;
  }>,
): HierarchyPivotGroup[] {
  return groups.map((group) => ({
    id: group.group_key,
    label: group.group_label,
    rows: selectCompactHierarchyAssets(group.assets).map((asset) => ({
      id: `${group.group_key}-${asset.instrument_symbol}`,
      label: asset.instrument_symbol,
      weight: totalMarketValue > 0
        ? formatPortfolioPercent((resolveValue(asset.market_value_usd) / totalMarketValue) * 100, 1)
        : "0.0%",
      unrealized: formatPortfolioMoney(asset.profit_loss_usd),
      action: resolveTickerActionState(asset.change_pct),
    })),
  }));
}

function buildAllocationSlices(
  totalMarketValue: number,
  groups: Array<{
    group_label: string;
    total_market_value_usd: string | number | null | undefined;
    total_change_pct?: string | number | null | undefined;
  }>,
): HomeAllocationSlice[] {
  return groups.map((group) => {
    const weight = totalMarketValue > 0
      ? (resolveValue(group.total_market_value_usd) / totalMarketValue) * 100
      : 0;

    return {
      sleeve: group.group_label,
      weight: formatPortfolioPercent(weight, 1),
      posture: resolveValue(group.total_change_pct) >= 0 ? "Core overweight" : "Watch list",
    };
  });
}

export function usePortfolioHomeRouteData(): PortfolioHomeRouteData {
  const commandCenter = usePortfolioCommandCenterResource();
  const summary = usePortfolioSummaryResource();
  const hierarchy = usePortfolioHierarchyResource();

  const status = useMemo(() => {
    if (
      commandCenter.status === "loading" ||
      summary.status === "loading" ||
      hierarchy.status === "loading"
    ) {
      return "loading" as const;
    }

    if (
      commandCenter.status === "error" ||
      summary.status === "error" ||
      hierarchy.status === "error"
    ) {
      return "error" as const;
    }

    if (
      commandCenter.status === "empty" ||
      summary.status === "empty" ||
      hierarchy.status === "empty"
    ) {
      return "empty" as const;
    }

    return "ready" as const;
  }, [commandCenter.status, hierarchy.status, summary.status]);

  const errorMessage = commandCenter.errorMessage ?? summary.errorMessage ?? hierarchy.errorMessage;

  const summaryRows = useMemo(
    () => getPortfolioSummaryRowsByMarketValue(summary.data?.rows ?? []),
    [summary.data?.rows],
  );

  const topMovers = useMemo<HomeTopMover[]>(
    () =>
      summaryRows.slice(0, 3).map((row) => ({
        ticker: row.instrument_symbol,
        move: formatPortfolioPercent(row.unrealized_gain_pct, 1),
        catalyst: resolveMomentumCatalyst(row.unrealized_gain_pct),
      })),
    [summaryRows],
  );

  const totalMarketValue = useMemo(
    () =>
      commandCenter.data ? resolveValue(commandCenter.data.total_market_value_usd) : 0,
    [commandCenter.data],
  );

  const kpiValues = resolvePortfolioSummaryKpis(commandCenter.data, summary.data);
  const kpis: HomeKpi[] = [
    {
      label: "Portfolio value",
      value: kpiValues.portfolioValue,
      delta: commandCenter.data
        ? `${formatPortfolioMoney(commandCenter.data.daily_pnl_usd)} today`
        : "Awaiting portfolio summary",
    },
    {
      label: "YTD return",
      value: summary.data
        ? formatPortfolioPercent(
            summary.data.rows.reduce((runningTotal, row) => {
              return runningTotal + resolveValue(row.unrealized_gain_usd) + resolveValue(row.realized_gain_usd) + resolveValue(row.dividend_net_usd);
            }, 0) /
              Math.max(
                summary.data.rows.reduce(
                  (runningTotal, row) => runningTotal + resolveValue(row.open_cost_basis_usd),
                  0,
                ),
                1,
              ) *
              100,
            1,
          )
        : "Unavailable",
      delta: commandCenter.data
        ? `Top 5 ${formatPortfolioPercent(commandCenter.data.concentration_top5_pct, 1)}`
        : "Awaiting concentration context",
    },
    {
      label: "Unrealized P/L",
      value: kpiValues.unrealizedPnl,
      delta: `Open holdings ${summaryRows.length.toString()}`,
    },
    {
      label: "Dividend run-rate",
      value: kpiValues.dividendRunRate,
      delta: summary.data ? `As of ${summary.data.as_of_ledger_at.slice(0, 10)}` : "Awaiting ledger timestamp",
    },
  ];

  const attentionItems: HomeAttentionItem[] = useMemo(() => {
    const insightItems =
      commandCenter.data?.insights.map((insight) => ({
        label: insight.title,
        status: resolveAttentionStatus(insight.severity),
        note: insight.message,
      })) ?? [];

    const downsideRow = summaryRows.find((row) => resolveValue(row.unrealized_gain_pct) < 0);
    if (downsideRow) {
      insightItems.push({
        label: `${downsideRow.instrument_symbol} downside breach`,
        status: "Wait",
        note: `${downsideRow.instrument_symbol} is under pressure at ${formatPortfolioPercent(downsideRow.unrealized_gain_pct, 1)} unrealized.`,
      });
    }

    return insightItems.slice(0, 3);
  }, [commandCenter.data?.insights, summaryRows]);

  const allocationSlices = useMemo<HomeAllocationSlice[]>(() => {
    const groups = hierarchy.data?.groups ?? [];
    return buildAllocationSlices(totalMarketValue, groups);
  }, [hierarchy.data?.groups, totalMarketValue]);

  const holdingsSummaryRows = useMemo<HomeHoldingsSummaryRow[]>(
    () =>
      summaryRows.slice(0, 4).map((row) => ({
        ticker: row.instrument_symbol,
        weight: totalMarketValue > 0
          ? formatPortfolioPercent((resolveValue(row.market_value_usd) / totalMarketValue) * 100, 1)
          : "0.0%",
        unrealized: formatPortfolioPercent(row.unrealized_gain_pct, 1),
        state: resolveTickerActionState(row.unrealized_gain_pct),
      })),
    [summaryRows, totalMarketValue],
  );

  const hierarchyPivotGroups = useMemo<HierarchyPivotGroup[]>(() => {
    const groups = hierarchy.data?.groups ?? [];
    return buildHierarchyPivotGroups(totalMarketValue, groups);
  }, [hierarchy.data?.groups, totalMarketValue]);

  return {
    status,
    errorMessage,
    reload: () => {
      commandCenter.reload();
      summary.reload();
      hierarchy.reload();
    },
    assetDetailHref: resolvePortfolioAssetDetailHref(summary.data),
    kpis,
    topMovers,
    attentionItems,
    allocationSlices,
    holdingsSummaryRows,
    hierarchyPivotGroups,
  };
}
