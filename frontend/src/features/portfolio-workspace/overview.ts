import Decimal from "decimal.js";

import type {
  PortfolioContributionRow,
  PortfolioRiskEstimatorMetric,
  PortfolioSummaryRow,
  PortfolioTimeSeriesPoint,
} from "../../core/api/schemas";
import { formatUsdMoney, resolveMoneyTone, type ValueTone } from "../../core/lib/formatters";
import type { PortfolioTransactionEvent } from "./hooks";

type MetricCard = {
  label: string;
  value: string;
  tone: ValueTone;
  hint: string;
};

const ZERO = new Decimal(0);

function toDecimal(value: string): Decimal {
  return new Decimal(value);
}

function sumSummaryValues(
  rows: PortfolioSummaryRow[],
  selector: (row: PortfolioSummaryRow) => string | null,
): Decimal {
  return rows.reduce<Decimal>((acc, row) => {
    const value = selector(row);
    if (value === null) {
      return acc;
    }

    return acc.add(toDecimal(value));
  }, ZERO);
}

export function buildHomeMetricCards(
  summaryRows: PortfolioSummaryRow[],
  points: PortfolioTimeSeriesPoint[],
): MetricCard[] {
  const marketValue = sumSummaryValues(summaryRows, (row) => row.market_value_usd);
  const unrealizedGain = sumSummaryValues(summaryRows, (row) => row.unrealized_gain_usd);
  const latestPoint = points.at(-1);
  const firstPoint = points.at(0);
  const periodPnl =
    latestPoint && firstPoint
      ? toDecimal(latestPoint.portfolio_value_usd).sub(
          toDecimal(firstPoint.portfolio_value_usd),
        )
      : ZERO;

  return [
    {
      label: "Market value",
      value: formatUsdMoney(marketValue.toFixed(2)),
      tone: resolveMoneyTone(marketValue.toFixed(2)),
      hint: "Open-position valuation from persisted pricing snapshot coverage.",
    },
    {
      label: "Unrealized gain",
      value: formatUsdMoney(unrealizedGain.toFixed(2)),
      tone: resolveMoneyTone(unrealizedGain.toFixed(2)),
      hint: "Difference between open cost basis and market valuation.",
    },
    {
      label: "Period change",
      value: formatUsdMoney(periodPnl.toFixed(2)),
      tone: resolveMoneyTone(periodPnl.toFixed(2)),
      hint: "Latest value versus first available point in selected period.",
    },
  ];
}

export function topContributionRows(
  rows: PortfolioContributionRow[],
): PortfolioContributionRow[] {
  return [...rows]
    .sort((left, right) => {
      const leftAbs = toDecimal(left.contribution_pnl_usd).abs();
      const rightAbs = toDecimal(right.contribution_pnl_usd).abs();
      return rightAbs.comparedTo(leftAbs);
    })
    .slice(0, 5);
}

export function sortRiskMetrics(
  metrics: PortfolioRiskEstimatorMetric[],
): PortfolioRiskEstimatorMetric[] {
  return [...metrics].sort((left, right) =>
    left.estimator_id.localeCompare(right.estimator_id),
  );
}

export type TrendChartDatum = {
  capturedAt: string;
  portfolioValue: number;
  pnl: number;
};

export type ContributionChartDatum = {
  instrumentSymbol: string;
  contributionPnl: number;
  contributionPct: number;
};

export type RiskChartDatum = {
  estimatorId: string;
  value: number;
};

export function buildTrendChartData(
  points: PortfolioTimeSeriesPoint[],
): TrendChartDatum[] {
  return points.map((point) => ({
    capturedAt: point.captured_at,
    portfolioValue: Number(point.portfolio_value_usd),
    pnl: Number(point.pnl_usd),
  }));
}

export function buildContributionChartData(
  rows: PortfolioContributionRow[],
): ContributionChartDatum[] {
  return rows.map((row) => ({
    instrumentSymbol: row.instrument_symbol,
    contributionPnl: Number(row.contribution_pnl_usd),
    contributionPct: Number(row.contribution_pct),
  }));
}

export function buildRiskChartData(
  metrics: PortfolioRiskEstimatorMetric[],
): RiskChartDatum[] {
  return metrics.map((metric) => ({
    estimatorId: metric.estimator_id,
    value: Number(metric.value),
  }));
}

export function sortTransactionsDeterministically(
  events: PortfolioTransactionEvent[],
): PortfolioTransactionEvent[] {
  return [...events].sort((left, right) => {
    const postedAtComparison = right.posted_at.localeCompare(left.posted_at);
    if (postedAtComparison !== 0) {
      return postedAtComparison;
    }

    return left.id.localeCompare(right.id);
  });
}

export function filterTransactions(
  events: PortfolioTransactionEvent[],
  symbolFilter: string,
  eventTypeFilter: string,
): PortfolioTransactionEvent[] {
  const normalizedSymbolFilter = symbolFilter.trim().toUpperCase();
  const normalizedEventTypeFilter = eventTypeFilter.trim().toLowerCase();

  return events.filter((event) => {
    const symbolMatches =
      normalizedSymbolFilter.length === 0 ||
      event.instrument_symbol.toUpperCase().includes(normalizedSymbolFilter);
    const eventTypeMatches =
      normalizedEventTypeFilter.length === 0 ||
      normalizedEventTypeFilter === "all" ||
      event.event_type.toLowerCase() === normalizedEventTypeFilter;

    return symbolMatches && eventTypeMatches;
  });
}
