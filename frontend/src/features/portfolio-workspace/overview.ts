import Decimal from "decimal.js";

import type {
  PortfolioContributionRow,
  PortfolioQuantMetric,
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
  explainability: {
    shortDefinition: string;
    whyItMatters: string;
    interpretation: string;
    formulaOrBasis: string;
    comparisonContext: string;
    caveats: string;
    currentContextNote: string;
  };
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
      explainability: {
        shortDefinition: "Current total value of open positions using persisted prices.",
        whyItMatters: "Shows present portfolio scale and exposure.",
        interpretation: "Higher market value indicates larger marked-to-market exposure.",
        formulaOrBasis: "Sum of summary rows market_value_usd.",
        comparisonContext: "Compare to open cost basis and prior period snapshots.",
        caveats: "Depends on latest persisted snapshot availability.",
        currentContextNote: `Current market value is ${formatUsdMoney(marketValue.toFixed(2))}.`,
      },
    },
    {
      label: "Unrealized gain",
      value: formatUsdMoney(unrealizedGain.toFixed(2)),
      tone: resolveMoneyTone(unrealizedGain.toFixed(2)),
      hint: "Difference between open cost basis and market valuation.",
      explainability: {
        shortDefinition: "Open-position gain/loss relative to cost basis.",
        whyItMatters: "Clarifies whether current holdings are above or below entry cost.",
        interpretation: "Positive is above cost basis; negative is below.",
        formulaOrBasis: "Sum of summary rows unrealized_gain_usd.",
        comparisonContext: "Compare with period change and benchmark-relative return.",
        caveats: "Unrealized values can reverse before any trade is closed.",
        currentContextNote: `Current unrealized gain is ${formatUsdMoney(unrealizedGain.toFixed(2))}.`,
      },
    },
    {
      label: "Period change",
      value: formatUsdMoney(periodPnl.toFixed(2)),
      tone: resolveMoneyTone(periodPnl.toFixed(2)),
      hint: "Latest value versus first available point in selected period.",
      explainability: {
        shortDefinition: "Change in portfolio value over selected period.",
        whyItMatters: "Signals recent direction and magnitude of portfolio movement.",
        interpretation: "Positive indicates appreciation over selected window.",
        formulaOrBasis: "Latest portfolio_value_usd - first portfolio_value_usd.",
        comparisonContext: "Compare against benchmark return spread in trend module.",
        caveats: "Period change depends on available history points and selected scope.",
        currentContextNote: `Current selected-period change is ${formatUsdMoney(periodPnl.toFixed(2))}.`,
      },
    },
  ];
}

function formatQuantMetricValue(metric: PortfolioQuantMetric): string {
  const decimalValue = toDecimal(metric.value);
  if (metric.display_as === "percent") {
    const percentValue = decimalValue.times(100);
    const signPrefix = percentValue.greaterThan(0) ? "+" : "";
    return `${signPrefix}${percentValue.toFixed(2)}%`;
  }
  return decimalValue.toFixed(3);
}

function resolveQuantMetricTone(metric: PortfolioQuantMetric): ValueTone {
  const decimalValue = toDecimal(metric.value);
  if (decimalValue.greaterThan(0)) {
    return "positive";
  }
  if (decimalValue.lessThan(0)) {
    return "negative";
  }
  return "neutral";
}

function resolveQuantMetricFormula(metricId: string): string {
  if (metricId === "sharpe") {
    return "Excess return divided by return volatility.";
  }
  if (metricId === "sortino") {
    return "Excess return divided by downside volatility.";
  }
  if (metricId === "calmar") {
    return "CAGR divided by absolute max drawdown.";
  }
  if (metricId === "volatility") {
    return "Annualized standard deviation of periodic returns.";
  }
  if (metricId === "max_drawdown") {
    return "Minimum value of running drawdown series.";
  }
  if (metricId === "win_rate") {
    return "Share of periods with strictly positive return.";
  }
  if (metricId === "alpha") {
    return "Benchmark-relative excess return estimate.";
  }
  if (metricId === "beta") {
    return "Sensitivity of strategy returns versus benchmark returns.";
  }
  if (metricId === "cagr") {
    return "Compound annual growth rate over selected period.";
  }
  if (metricId === "total_return") {
    return "Compounded total return for selected period.";
  }
  return `QuantStats metric: ${metricId}.`;
}

function resolveQuantMetricInterpretation(metric: PortfolioQuantMetric): string {
  const value = toDecimal(metric.value);
  if (metric.metric_id === "sharpe") {
    if (value.greaterThanOrEqualTo(1)) {
      return "Strong risk-adjusted profile for this period.";
    }
    if (value.greaterThanOrEqualTo(0)) {
      return "Marginal risk-adjusted profile; monitor consistency.";
    }
    return "Negative risk-adjusted profile; returns did not compensate volatility.";
  }
  if (metric.metric_id === "sortino") {
    if (value.greaterThanOrEqualTo(1.2)) {
      return "Healthy downside-adjusted return profile.";
    }
    if (value.greaterThanOrEqualTo(0)) {
      return "Moderate downside efficiency; monitor drawdown sensitivity.";
    }
    return "Weak downside-adjusted profile in selected period.";
  }
  if (metric.metric_id === "calmar") {
    if (value.greaterThanOrEqualTo(0.7)) {
      return "Return/drawdown tradeoff is strong for this window.";
    }
    if (value.greaterThanOrEqualTo(0.2)) {
      return "Return/drawdown tradeoff is acceptable but not robust.";
    }
    return "Return/drawdown tradeoff is weak for this window.";
  }
  if (metric.metric_id === "volatility") {
    if (value.lessThanOrEqualTo(0.15)) {
      return "Low realized volatility for equity-heavy portfolios.";
    }
    if (value.lessThanOrEqualTo(0.25)) {
      return "Moderate realized volatility.";
    }
    return "Elevated realized volatility; monitor risk budget.";
  }
  if (metric.metric_id === "max_drawdown") {
    if (value.greaterThanOrEqualTo(-0.1)) {
      return "Drawdown remained relatively contained.";
    }
    if (value.greaterThanOrEqualTo(-0.2)) {
      return "Moderate drawdown pressure in period.";
    }
    return "Deep drawdown observed; stress tolerance required.";
  }
  if (metric.metric_id === "win_rate") {
    if (value.greaterThanOrEqualTo(0.55)) {
      return "Positive-return periods dominate this window.";
    }
    if (value.greaterThanOrEqualTo(0.45)) {
      return "Balanced win/loss period distribution.";
    }
    return "Negative-return periods dominate this window.";
  }
  if (metric.metric_id === "beta") {
    if (value.greaterThanOrEqualTo(0.8) && value.lessThanOrEqualTo(1.2)) {
      return "Benchmark-like market sensitivity.";
    }
    if (value.lessThan(0.8)) {
      return "Lower market sensitivity than benchmark.";
    }
    return "Higher market sensitivity than benchmark.";
  }
  if (metric.metric_id === "alpha") {
    return value.greaterThan(0)
      ? "Positive benchmark-relative excess return."
      : "No positive benchmark-relative excess return in selected period.";
  }
  if (metric.metric_id === "cagr" || metric.metric_id === "total_return") {
    return value.greaterThan(0)
      ? "Positive compounded growth for selected period."
      : "Compounded growth was negative for selected period.";
  }
  return "Interpret alongside other metrics and period context.";
}

function resolveQuantMetricCurrentContext(metric: PortfolioQuantMetric): string {
  const formattedValue = formatQuantMetricValue(metric);
  if (metric.metric_id === "sharpe") {
    return `Current Sharpe is ${formattedValue}; values above 1.0 are generally stronger.`;
  }
  if (metric.metric_id === "sortino") {
    return `Current Sortino is ${formattedValue}; values above 1.2 are generally stronger.`;
  }
  if (metric.metric_id === "calmar") {
    return `Current Calmar is ${formattedValue}; higher values indicate better drawdown efficiency.`;
  }
  if (metric.metric_id === "volatility") {
    return `Current annualized volatility is ${formattedValue}; lower values indicate lower realized dispersion.`;
  }
  if (metric.metric_id === "max_drawdown") {
    return `Current max drawdown is ${formattedValue}; values closer to 0% are preferable.`;
  }
  if (metric.metric_id === "win_rate") {
    return `Current win rate is ${formattedValue}; above 50% means more positive than negative periods.`;
  }
  return `Current value is ${formattedValue} for selected period.`;
}

export function buildQuantMetricCards(metrics: PortfolioQuantMetric[]): MetricCard[] {
  const orderedMetricIds: string[] = [
    "sharpe",
    "sortino",
    "calmar",
    "volatility",
    "max_drawdown",
    "alpha",
    "beta",
    "win_rate",
  ];
  const metricById = new Map(metrics.map((metric) => [metric.metric_id, metric]));

  return orderedMetricIds
    .map((metricId) => metricById.get(metricId))
    .filter((metric): metric is PortfolioQuantMetric => metric !== undefined)
    .slice(0, 6)
    .map((metric) => ({
      label: metric.label,
      value: formatQuantMetricValue(metric),
      tone: resolveQuantMetricTone(metric),
      hint: metric.description,
      explainability: {
        shortDefinition: metric.description,
        whyItMatters: "Supports risk-adjusted interpretation in report workflows.",
        interpretation: resolveQuantMetricInterpretation(metric),
        formulaOrBasis: resolveQuantMetricFormula(metric.metric_id),
        comparisonContext: "Compare across 30D/90D/252D windows and benchmark-omission state.",
        caveats: "Quant metrics depend on available aligned return history.",
        currentContextNote: resolveQuantMetricCurrentContext(metric),
      },
    }));
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
  benchmarkSp500: number | null;
  benchmarkNasdaq100: number | null;
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
    benchmarkSp500:
      point.benchmark_sp500_value_usd === null
        ? null
        : Number(point.benchmark_sp500_value_usd),
    benchmarkNasdaq100:
      point.benchmark_nasdaq100_value_usd === null
        ? null
        : Number(point.benchmark_nasdaq100_value_usd),
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
