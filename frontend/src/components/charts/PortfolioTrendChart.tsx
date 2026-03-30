import type { ReactNode } from "react";
import {
  useMemo,
  useState,
} from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDateLabel } from "../../core/lib/dates";
import { formatUsdMoney } from "../../core/lib/formatters";
import {
  buildTrendChartData,
  type TrendChartDatum,
} from "../../features/portfolio-workspace/overview";
import type { PortfolioTimeSeriesPoint } from "../../core/api/schemas";
import { MetricExplainabilityPopover } from "../metric-explainability/MetricExplainabilityPopover";

type PortfolioTrendChartProps = {
  points: PortfolioTimeSeriesPoint[];
  analysisActions?: ReactNode;
};

function formatAxisMoney(value: number): string {
  return formatUsdMoney(value.toFixed(2));
}

type TrendChartPoint = TrendChartDatum & {
  trendline: number;
};

type TrendTooltipEntry = {
  dataKey?: string;
  value?: number | string;
  payload?: TrendChartPoint;
};

function toPercentLabel(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "—";
  }
  if (value > 0) {
    return `+${value.toFixed(2)}%`;
  }
  return `${value.toFixed(2)}%`;
}

function toSignedMoneyLabel(value: number): string {
  const formatted = formatUsdMoney(value.toFixed(2));
  return value > 0 ? `+${formatted}` : formatted;
}

function resolveToneClass(value: number): "positive" | "negative" | "neutral" {
  if (value > 0) {
    return "positive";
  }
  if (value < 0) {
    return "negative";
  }
  return "neutral";
}

function computeRelativePerformance(current: number | null, baseline: number | null): number | null {
  if (current === null || baseline === null || baseline === 0) {
    return null;
  }
  return ((current - baseline) / baseline) * 100;
}

export function PortfolioTrendChart({ points, analysisActions }: PortfolioTrendChartProps) {
  const chartData: TrendChartDatum[] = buildTrendChartData(points);
  const enrichedChartData = useMemo<TrendChartPoint[]>(() => {
    if (chartData.length <= 1) {
      return chartData.map((point) => ({ ...point, trendline: point.portfolioValue }));
    }

    const pointsCount = chartData.length;
    let sumX = 0;
    let sumY = 0;
    let sumXY = 0;
    let sumXX = 0;
    chartData.forEach((point, index) => {
      sumX += index;
      sumY += point.portfolioValue;
      sumXY += index * point.portfolioValue;
      sumXX += index * index;
    });

    const denominator = pointsCount * sumXX - sumX * sumX;
    const slope = denominator === 0 ? 0 : (pointsCount * sumXY - sumX * sumY) / denominator;
    const intercept = (sumY - slope * sumX) / pointsCount;

    return chartData.map((point, index) => ({
      ...point,
      trendline: slope * index + intercept,
    }));
  }, [chartData]);

  const hasSp500Series = useMemo(
    () => enrichedChartData.some((point) => point.benchmarkSp500 !== null),
    [enrichedChartData],
  );
  const hasNasdaq100Series = useMemo(
    () => enrichedChartData.some((point) => point.benchmarkNasdaq100 !== null),
    [enrichedChartData],
  );
  const firstPoint = enrichedChartData.at(0);
  const latestPoint = enrichedChartData.at(-1);
  const portfolioBaseline = firstPoint ? firstPoint.portfolioValue : null;
  const sp500Baseline = firstPoint?.benchmarkSp500 ?? null;
  const nasdaqBaseline = firstPoint?.benchmarkNasdaq100 ?? null;
  const portfolioReturn = latestPoint
    ? computeRelativePerformance(latestPoint.portfolioValue, portfolioBaseline)
    : null;
  const sp500Return = latestPoint
    ? computeRelativePerformance(latestPoint.benchmarkSp500, sp500Baseline)
    : null;
  const nasdaqReturn = latestPoint
    ? computeRelativePerformance(latestPoint.benchmarkNasdaq100, nasdaqBaseline)
    : null;
  const spreadVsSp500 =
    portfolioReturn !== null && sp500Return !== null
      ? portfolioReturn - sp500Return
      : null;
  const spreadVsNasdaq =
    portfolioReturn !== null && nasdaqReturn !== null
      ? portfolioReturn - nasdaqReturn
      : null;
  const maxSpread = [spreadVsSp500, spreadVsNasdaq].reduce<number | null>(
    (current, candidate) => {
      if (candidate === null) {
        return current;
      }
      if (current === null || Math.abs(candidate) > Math.abs(current)) {
        return candidate;
      }
      return current;
    },
    null,
  );

  const [showSp500, setShowSp500] = useState(true);
  const [showNasdaq100, setShowNasdaq100] = useState(true);
  const [showPortfolio, setShowPortfolio] = useState(true);
  const [showPnl, setShowPnl] = useState(true);
  const [showTrendline, setShowTrendline] = useState(true);

  function renderTrendTooltip(raw: unknown) {
    const tooltip = raw as {
      active?: boolean;
      label?: string;
      payload?: TrendTooltipEntry[];
    };
    if (!tooltip.active || !tooltip.payload || tooltip.payload.length === 0) {
      return null;
    }

    const point = tooltip.payload[0]?.payload;
    if (!point) {
      return null;
    }

    const portfolioReturn = computeRelativePerformance(point.portfolioValue, portfolioBaseline);
    const sp500Return = computeRelativePerformance(point.benchmarkSp500, sp500Baseline);
    const nasdaqReturn = computeRelativePerformance(point.benchmarkNasdaq100, nasdaqBaseline);
    const spreadVsSp500 =
      portfolioReturn !== null && sp500Return !== null
        ? portfolioReturn - sp500Return
        : null;
    const spreadVsNasdaq =
      portfolioReturn !== null && nasdaqReturn !== null
        ? portfolioReturn - nasdaqReturn
        : null;
    const pnlTone = resolveToneClass(point.pnl);
    const totalReturnTone =
      portfolioReturn !== null && portfolioReturn >= 0 ? "positive" : "negative";

    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip__header">
          <p className="chart-tooltip__date">{formatDateLabel(point.capturedAt)}</p>
          <span className={`status-pill status-pill--${totalReturnTone}`}>
            {toPercentLabel(portfolioReturn)} total
          </span>
        </div>
        <div className="chart-tooltip__rows">
          <div className="chart-tooltip__row">
            <span>Portfolio Value</span>
            <strong>{formatUsdMoney(point.portfolioValue.toFixed(2))}</strong>
          </div>
          <div className={`chart-tooltip__row tone-${pnlTone}`}>
            <span>Unrealized P&amp;L vs cost basis</span>
            <strong>{toSignedMoneyLabel(point.pnl)}</strong>
          </div>
          <div className="chart-tooltip__row">
            <span>Trend estimate</span>
            <strong>{formatUsdMoney(point.trendline.toFixed(2))}</strong>
          </div>
          {showSp500 && point.benchmarkSp500 !== null ? (
            <div className="chart-tooltip__row">
              <span>S&amp;P 500 benchmark (normalized)</span>
              <strong>{formatUsdMoney(point.benchmarkSp500.toFixed(2))}</strong>
            </div>
          ) : null}
          {showNasdaq100 && point.benchmarkNasdaq100 !== null ? (
            <div className="chart-tooltip__row">
              <span>NASDAQ-100 benchmark (normalized)</span>
              <strong>{formatUsdMoney(point.benchmarkNasdaq100.toFixed(2))}</strong>
            </div>
          ) : null}
        </div>
        {spreadVsSp500 !== null || spreadVsNasdaq !== null ? (
          <div className="chart-tooltip__footer">
            {spreadVsSp500 !== null ? (
              <p>
                Spread vs S&P 500:{" "}
                <strong className={`tone-${resolveToneClass(spreadVsSp500)}`}>
                  {toPercentLabel(spreadVsSp500)}
                </strong>
              </p>
            ) : null}
            {spreadVsNasdaq !== null ? (
              <p>
                Spread vs NASDAQ-100:{" "}
                <strong className={`tone-${resolveToneClass(spreadVsNasdaq)}`}>
                  {toPercentLabel(spreadVsNasdaq)}
                </strong>
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="chart-surface" role="img" aria-label="Portfolio trend chart">
      <div className="chart-header">
        <div>
          <h3 className="panel__title">Portfolio Performance</h3>
          <p className="panel__subtitle">Net worth growth with market benchmarking</p>
        </div>
        <div className="chart-controls-group">
          <div className="chart-controls">
            <button
              aria-pressed={showPortfolio}
              className="chart-chip"
              onClick={() => setShowPortfolio((previous) => !previous)}
              type="button"
            >
              Portfolio
            </button>
            <button
              aria-pressed={showPnl}
              className="chart-chip"
              onClick={() => setShowPnl((previous) => !previous)}
              type="button"
            >
              P&amp;L
            </button>
            <button
              aria-pressed={showTrendline}
              className="chart-chip"
              onClick={() => setShowTrendline((previous) => !previous)}
              type="button"
            >
              Trend estimate
            </button>
            <button
              aria-pressed={showSp500 && hasSp500Series}
              className="chart-chip"
              disabled={!hasSp500Series}
              onClick={() => setShowSp500((previous) => !previous)}
              type="button"
            >
              S&P 500
            </button>
            <button
              aria-pressed={showNasdaq100 && hasNasdaq100Series}
              className="chart-chip"
              disabled={!hasNasdaq100Series}
              onClick={() => setShowNasdaq100((previous) => !previous)}
              type="button"
            >
              NASDAQ-100
            </button>
          </div>
          {analysisActions ? (
            <div className="chart-persistent-actions">{analysisActions}</div>
          ) : null}
        </div>
      </div>
      <div className="chart-canvas">
        <ResponsiveContainer height={320} width="100%">
          <LineChart
            data={enrichedChartData}
            margin={{ top: 20, right: 20, left: 20, bottom: 8 }}
          >
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
            <XAxis
              dataKey="capturedAt"
              minTickGap={24}
              stroke="var(--chart-axis)"
              tickFormatter={formatDateLabel}
            />
            <YAxis
              stroke="var(--chart-axis)"
              tickFormatter={formatAxisMoney}
              width={96}
              yAxisId="left"
            />
            <YAxis
              orientation="right"
              stroke="var(--chart-axis)"
              tickFormatter={formatAxisMoney}
              width={96}
              yAxisId="right"
            />
            <Tooltip content={renderTrendTooltip} />
            {showPortfolio ? (
              <Line
                activeDot={{
                  r: 5,
                  stroke: "var(--chart-trend-primary)",
                  strokeWidth: 2,
                }}
                dataKey="portfolioValue"
                dot={false}
                name="Portfolio value"
                stroke="var(--chart-trend-primary)"
                strokeWidth={3}
                type="monotone"
                yAxisId="left"
              />
            ) : null}
            {showPnl ? (
              <Line
                dataKey="pnl"
                dot={false}
                name="Unrealized P&L vs cost basis"
                stroke="var(--chart-trend-secondary)"
                strokeWidth={2}
                type="monotone"
                yAxisId="right"
              />
            ) : null}
            {showTrendline ? (
              <Line
                dataKey="trendline"
                dot={false}
                name="Trend estimate"
                stroke="var(--color-text-muted)"
                strokeDasharray="6 4"
                strokeWidth={2}
                type="monotone"
                yAxisId="left"
              />
            ) : null}
            {showSp500 && hasSp500Series ? (
              <Line
                dataKey="benchmarkSp500"
                dot={false}
                name="S&P 500 proxy"
                stroke="var(--chart-benchmark-sp500)"
                strokeDasharray="6 4"
                strokeWidth={2}
                type="monotone"
                yAxisId="left"
              />
            ) : null}
            {showNasdaq100 && hasNasdaq100Series ? (
              <Line
                dataKey="benchmarkNasdaq100"
                dot={false}
                name="NASDAQ-100 proxy"
                stroke="var(--chart-benchmark-nasdaq100)"
                strokeDasharray="6 4"
                strokeWidth={2}
                type="monotone"
                yAxisId="left"
              />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-definition-row">
        <MetricExplainabilityPopover
          label="Trend estimate"
          shortDefinition="Linear-regression trend estimate over the selected chart window."
          whyItMatters="Highlights directional drift independent of day-to-day noise."
          interpretation="If portfolio value persistently sits below this line, momentum is weakening."
          formulaOrBasis="Ordinary least squares on index position versus portfolio value."
          comparisonContext="Compare trend slope with benchmark-relative spread cards."
          caveats="Regression trend is descriptive, not predictive."
        />
        <MetricExplainabilityPopover
          label="Normalized benchmarks"
          shortDefinition="Benchmark series rebased to portfolio start value for comparable trajectory."
          whyItMatters="Allows shape comparison against S&P 500 and NASDAQ-100 without absolute index-level distortion."
          interpretation="A higher normalized benchmark line means benchmark outperformed your portfolio since period start."
          formulaOrBasis="portfolio_start_value * (benchmark_price_t / benchmark_price_start)."
          comparisonContext="Use together with excess return and spread values."
          caveats="Normalization compares path/relative return, not nominal index points."
        />
        <MetricExplainabilityPopover
          label="Unrealized P&L vs cost basis"
          shortDefinition="Difference between current market value and open cost basis."
          whyItMatters="Shows unrealized gain/loss without mixing in realized exits."
          interpretation="Positive values indicate open positions are above cost basis."
          formulaOrBasis="Portfolio value - open cost basis at the selected timestamp."
          comparisonContext="Compare against period return and benchmark spread."
          caveats="Unrealized P&L is mark-to-market and can change with each price update."
          currentContextNote={
            latestPoint
              ? `Latest available value is ${toSignedMoneyLabel(latestPoint.pnl)}.`
              : undefined
          }
        />
      </div>
      <div className="chart-summary-grid">
        <article className="chart-summary-card">
          <span className="chart-summary-card__label">Total Return</span>
          <div className="chart-summary-card__rows">
            <p>
              <span>Portfolio</span>
              <strong className={`tone-${resolveToneClass(portfolioReturn ?? 0)}`}>
                {toPercentLabel(portfolioReturn)}
              </strong>
            </p>
            <p>
              <span>S&P 500</span>
              <strong className={`tone-${resolveToneClass(sp500Return ?? 0)}`}>
                {toPercentLabel(sp500Return)}
              </strong>
            </p>
            <p>
              <span>NASDAQ-100</span>
              <strong className={`tone-${resolveToneClass(nasdaqReturn ?? 0)}`}>
                {toPercentLabel(nasdaqReturn)}
              </strong>
            </p>
          </div>
        </article>
        <article className="chart-summary-card chart-summary-card--accent">
          <span className="chart-summary-card__label">Excess Portfolio Return</span>
          <strong className={`chart-summary-card__headline tone-${resolveToneClass(maxSpread ?? 0)}`}>
            {toPercentLabel(maxSpread)}
          </strong>
          <p className="chart-summary-card__copy">Relative to best available benchmark spread</p>
        </article>
        <article className="chart-summary-card chart-summary-card--signal">
          <span className="chart-summary-card__label">Market Outperformance</span>
          <strong className={`chart-summary-card__headline tone-${resolveToneClass(maxSpread ?? 0)}`}>
            {maxSpread !== null && maxSpread > 0 ? "Exceptional" : "Neutral"}
          </strong>
          <p className="chart-summary-card__copy">Signal derived from benchmark-relative return</p>
        </article>
      </div>
    </div>
  );
}
