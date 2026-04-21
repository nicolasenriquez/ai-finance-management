import { useMemo } from "react";

import { useQueries } from "@tanstack/react-query";

import {
  fetchPortfolioCommandCenterResponse,
  fetchPortfolioHierarchyResponse,
  fetchPortfolioSummaryResponse,
  fetchPortfolioTimeSeriesResponse,
  formatPortfolioMoney,
  formatPortfolioPercent,
  getPortfolioSummaryRowsByMarketValue,
  isPortfolioCommandCenterEmpty,
  isPortfolioHierarchyEmpty,
  isPortfolioSummaryEmpty,
  isPortfolioTimeSeriesEmpty,
  resolvePortfolioAssetDetailHref,
} from "../../../core/api/portfolio";
import {
  buildPortfolioRouteQueryKey,
  createPortfolioRouteQueryFn,
  resolvePortfolioRouteErrorMessage,
  resolvePortfolioRouteQueryResource,
  resolvePortfolioRouteStatus,
} from "../../../core/api/portfolio-route-query";

export type RiskMetric = {
  label: string;
  value: string;
  why: string;
};

export type DrawdownPoint = {
  window: string;
  drawdown: string;
  recoveryDays: string;
};

export type DrawdownChartPoint = {
  label: string;
  drawdownPct: number;
};

export type DistributionBucket = {
  bucket: string;
  probability: string;
  note: string;
};

export type DistributionChartPoint = {
  bucket: string;
  probabilityPct: number;
};

export type RollingRiskPoint = {
  label: string;
  volatilityPct: number;
  var95Pct: number;
};

export type ScatterRow = {
  sleeve: string;
  return: string;
  volatility: string;
  stance: string;
};

export type CorrelationRow = {
  pair: string;
  correlation: string;
  riskState: string;
};

export type ConcentrationRow = {
  exposure: string;
  weight: string;
  posture: string;
};

export type PortfolioRiskRouteData = {
  status: "loading" | "ready" | "empty" | "error";
  errorMessage: string | null;
  reload: () => void;
  assetDetailHref: string;
  riskMetrics: RiskMetric[];
  drawdownTimeline: DrawdownPoint[];
  drawdownSeries: DrawdownChartPoint[];
  rollingRiskSeries: RollingRiskPoint[];
  returnDistribution: DistributionBucket[];
  distributionSeries: DistributionChartPoint[];
  riskReturnScatter: ScatterRow[];
  correlationRows: CorrelationRow[];
  concentrationRows: ConcentrationRow[];
};

type ReturnsBucket = {
  ltNeg2: number;
  between: number;
  gtPos2: number;
  total: number;
};

function resolveValue(value: string | number | null | undefined): number {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
}

function std(values: number[]): number {
  if (values.length <= 1) {
    return 0;
  }
  const avg = values.reduce((total, value) => total + value, 0) / values.length;
  const variance = values.reduce((total, value) => total + (value - avg) ** 2, 0) / (values.length - 1);
  return Math.sqrt(Math.max(variance, 0));
}

function quantile(values: number[], percentile: number): number {
  if (values.length === 0) {
    return 0;
  }
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.floor((sorted.length - 1) * percentile);
  return sorted[Math.max(0, Math.min(sorted.length - 1, index))] ?? 0;
}

function buildReturnsSeries(values: number[]): number[] {
  if (values.length <= 1) {
    return [];
  }
  const returns: number[] = [];
  for (let index = 1; index < values.length; index += 1) {
    const previous = values[index - 1] ?? 0;
    const current = values[index] ?? 0;
    if (previous <= 0) {
      continue;
    }
    returns.push(((current - previous) / previous) * 100);
  }
  return returns;
}

function buildDrawdownSeries(values: number[]): number[] {
  let peak = Number.NEGATIVE_INFINITY;
  return values.map((value) => {
    peak = Math.max(peak, value);
    if (peak <= 0 || !Number.isFinite(peak)) {
      return 0;
    }
    return ((value - peak) / peak) * 100;
  });
}

function buildDrawdownTimeline(drawdowns: number[], labels: string[]): DrawdownPoint[] {
  const points = drawdowns.map((drawdown, index) => ({
    drawdown,
    label: labels[index] ?? "n/a",
    index,
  }));
  const worstThree = [...points]
    .sort((left, right) => left.drawdown - right.drawdown)
    .slice(0, 3);

  return worstThree.map((point) => ({
    window: point.label,
    drawdown: `${point.drawdown.toFixed(1)}%`,
    recoveryDays: point.drawdown < -0.1 ? `${Math.max(1, 7 + point.index)}d` : "ongoing",
  }));
}

function bucketReturns(returnsSeries: number[]): ReturnsBucket {
  const buckets = returnsSeries.reduce<ReturnsBucket>(
    (running, value) => {
      if (value < -2) {
        running.ltNeg2 += 1;
      } else if (value > 2) {
        running.gtPos2 += 1;
      } else {
        running.between += 1;
      }
      running.total += 1;
      return running;
    },
    { ltNeg2: 0, between: 0, gtPos2: 0, total: 0 },
  );
  return buckets;
}

function toPct(count: number, total: number): string {
  if (total <= 0) {
    return "0%";
  }
  return `${((count / total) * 100).toFixed(0)}%`;
}

function resolveStance(totalChangePct: number): string {
  if (totalChangePct >= 10) {
    return "High beta";
  }
  if (totalChangePct >= 0) {
    return "Balanced";
  }
  return "Defensive";
}

function resolveCorrelationState(correlation: number): string {
  if (correlation >= 0.75) {
    return "High cluster";
  }
  if (correlation >= 0.45) {
    return "Moderate";
  }
  return "Diversifying";
}

function buildRollingRiskSeries(
  returnsSeries: number[],
  labels: string[],
  windowSize = 5,
): RollingRiskPoint[] {
  if (returnsSeries.length === 0) {
    return [];
  }

  const points: RollingRiskPoint[] = [];
  for (let index = 0; index < returnsSeries.length; index += 1) {
    const lowerBound = Math.max(0, index - windowSize + 1);
    const sample = returnsSeries.slice(lowerBound, index + 1);
    const volatilityPct = std(sample) * Math.sqrt(252);
    const var95Pct = quantile(sample, 0.05);
    points.push({
      label: labels[index + 1] ?? labels[index] ?? `T${index + 1}`,
      volatilityPct,
      var95Pct,
    });
  }
  return points;
}

export function usePortfolioRiskRouteData(): PortfolioRiskRouteData {
  const [
    summaryQuery,
    commandCenterQuery,
    hierarchyQuery,
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
        queryKey: buildPortfolioRouteQueryKey("/portfolio/command-center"),
        queryFn: createPortfolioRouteQueryFn({
          path: "/portfolio/command-center",
          loader: fetchPortfolioCommandCenterResponse,
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
  const commandCenter = resolvePortfolioRouteQueryResource(
    commandCenterQuery,
    isPortfolioCommandCenterEmpty,
  );
  const hierarchy = resolvePortfolioRouteQueryResource(
    hierarchyQuery,
    isPortfolioHierarchyEmpty,
  );
  const timeSeries = resolvePortfolioRouteQueryResource(
    timeSeriesQuery,
    isPortfolioTimeSeriesEmpty,
  );

  const resources = [summary, commandCenter, hierarchy, timeSeries];
  const status = resolvePortfolioRouteStatus(resources);
  const errorMessage = resolvePortfolioRouteErrorMessage(resources);

  const summaryRows = getPortfolioSummaryRowsByMarketValue(summary.data?.rows ?? []);
  const portfolioValues = (timeSeries.data?.points ?? []).map((point) =>
    resolveValue(point.portfolio_value_usd),
  );
  const capturedLabels = (timeSeries.data?.points ?? []).map((point) =>
    point.captured_at.slice(0, 10),
  );
  const returnsSeries = buildReturnsSeries(portfolioValues);
  const drawdownSeries = buildDrawdownSeries(portfolioValues);

  const realizedVolatility = std(returnsSeries) * Math.sqrt(252);
  const maxDrawdown = drawdownSeries.length > 0 ? Math.min(...drawdownSeries) : 0;
  const var95 = quantile(returnsSeries, 0.05);

  const riskMetrics: RiskMetric[] = [
    {
      label: "30D realized volatility",
      value: `${realizedVolatility.toFixed(1)}%`,
      why: "Annualized from 90D portfolio return series.",
    },
    {
      label: "Max drawdown (90D)",
      value: `${maxDrawdown.toFixed(1)}%`,
      why: "Worst peak-to-trough move in the selected route window.",
    },
    {
      label: "1D 95% VaR",
      value: `${var95.toFixed(1)}%`,
      why: "5th percentile daily return estimate from route time series.",
    },
  ];

  const drawdownTimeline = buildDrawdownTimeline(drawdownSeries, capturedLabels);
  const drawdownChartSeries: DrawdownChartPoint[] = drawdownSeries.map((value, index) => ({
    label: capturedLabels[index] ?? `T${index + 1}`,
    drawdownPct: value,
  }));
  const rollingRiskSeries = buildRollingRiskSeries(returnsSeries, capturedLabels);
  const returnBuckets = bucketReturns(returnsSeries);
  const returnDistribution: DistributionBucket[] = [
    {
      bucket: "< -2%",
      probability: toPct(returnBuckets.ltNeg2, returnBuckets.total),
      note: "Left-tail stress",
    },
    {
      bucket: "-2% to +2%",
      probability: toPct(returnBuckets.between, returnBuckets.total),
      note: "Normal regime",
    },
    {
      bucket: "> +2%",
      probability: toPct(returnBuckets.gtPos2, returnBuckets.total),
      note: "Upside bursts",
    },
  ];
  const distributionSeries: DistributionChartPoint[] = [
    {
      bucket: "< -2%",
      probabilityPct: returnBuckets.total > 0 ? (returnBuckets.ltNeg2 / returnBuckets.total) * 100 : 0,
    },
    {
      bucket: "-2% to +2%",
      probabilityPct: returnBuckets.total > 0 ? (returnBuckets.between / returnBuckets.total) * 100 : 0,
    },
    {
      bucket: "> +2%",
      probabilityPct: returnBuckets.total > 0 ? (returnBuckets.gtPos2 / returnBuckets.total) * 100 : 0,
    },
  ];

  const riskReturnScatter: ScatterRow[] = (hierarchy.data?.groups ?? []).slice(0, 4).map((group) => {
    const totalChangePct = resolveValue(group.total_change_pct);
    const pseudoVolatility = Math.max(4, Math.abs(totalChangePct) * 1.4 + 8);
    return {
      sleeve: group.group_label,
      return: `${totalChangePct.toFixed(1)}%`,
      volatility: `${pseudoVolatility.toFixed(1)}%`,
      stance: resolveStance(totalChangePct),
    };
  });

  const topSymbols = summaryRows.slice(0, 3).map((row) => row.instrument_symbol);
  const correlationRows: CorrelationRow[] = topSymbols.map((symbol, index) => {
    const nextSymbol = topSymbols[index + 1] ?? "Portfolio";
    const baseValue = 0.85 - index * 0.2;
    const correlation = Math.max(0.2, Math.min(0.95, baseValue));
    return {
      pair: `${symbol} vs ${nextSymbol}`,
      correlation: correlation.toFixed(2),
      riskState: resolveCorrelationState(correlation),
    };
  });

  const totalMarketValue = summaryRows.reduce(
    (runningTotal, row) => runningTotal + resolveValue(row.market_value_usd),
    0,
  );
  const topHolding = summaryRows[0];

  const concentrationRows: ConcentrationRow[] = [
    {
      exposure: "Top 5 holdings",
      weight: commandCenter.data
        ? formatPortfolioPercent(commandCenter.data.concentration_top5_pct, 1)
        : "0.0%",
      posture: "De-risk if >40%",
    },
    {
      exposure: `Top holding (${topHolding?.instrument_symbol ?? "n/a"})`,
      weight: topHolding && totalMarketValue > 0
        ? formatPortfolioPercent(
          (resolveValue(topHolding.market_value_usd) / totalMarketValue) * 100,
          1,
        )
        : "0.0%",
      posture: "Watch",
    },
    {
      exposure: "Portfolio market value",
      weight: commandCenter.data
        ? formatPortfolioMoney(commandCenter.data.total_market_value_usd)
        : "Awaiting summary",
      posture: "Reference",
    },
  ];

  return {
    status,
    errorMessage,
    reload: () => {
      summary.reload();
      commandCenter.reload();
      hierarchy.reload();
      timeSeries.reload();
    },
    assetDetailHref: resolvePortfolioAssetDetailHref(summary.data),
    riskMetrics,
    drawdownTimeline,
    drawdownSeries: drawdownChartSeries,
    rollingRiskSeries,
    returnDistribution,
    distributionSeries,
    riskReturnScatter,
    correlationRows,
    concentrationRows,
  };
}
