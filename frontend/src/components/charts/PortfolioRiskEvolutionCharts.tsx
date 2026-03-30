import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  PortfolioReturnDistributionBucket,
  PortfolioRiskDrawdownPoint,
  PortfolioRiskRollingPoint,
} from "../../core/api/schemas";
import { formatDateLabel } from "../../core/lib/dates";

type DrawdownTimelineChartProps = {
  points: PortfolioRiskDrawdownPoint[];
  showDrawdown: boolean;
};

type RollingTimelineChartProps = {
  points: PortfolioRiskRollingPoint[];
  showVolatility: boolean;
  showBeta: boolean;
};

type ReturnDistributionChartProps = {
  buckets: PortfolioReturnDistributionBucket[];
};

function toPercentLabel(value: number): string {
  const percentValue = value * 100;
  const signPrefix = percentValue > 0 ? "+" : "";
  return `${signPrefix}${percentValue.toFixed(2)}%`;
}

function toNumberLabel(value: number): string {
  return value.toFixed(3);
}

function toFiniteOrNull(value: string | null): number | null {
  if (value === null) {
    return null;
  }
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : null;
}

function buildDrawdownData(points: PortfolioRiskDrawdownPoint[]): Array<{
  capturedAt: string;
  drawdown: number;
}> {
  return points.map((point) => ({
    capturedAt: point.captured_at,
    drawdown: Number(point.drawdown),
  }));
}

function buildRollingData(points: PortfolioRiskRollingPoint[]): Array<{
  capturedAt: string;
  volatility: number | null;
  beta: number | null;
}> {
  return points.map((point) => ({
    capturedAt: point.captured_at,
    volatility: toFiniteOrNull(point.volatility_annualized),
    beta: toFiniteOrNull(point.beta),
  }));
}

function buildDistributionData(
  buckets: PortfolioReturnDistributionBucket[],
): Array<{
  bucketLabel: string;
  count: number;
  frequency: number;
}> {
  return buckets.map((bucket) => ({
    bucketLabel: `${(Number(bucket.lower_bound) * 100).toFixed(1)}% to ${(Number(bucket.upper_bound) * 100).toFixed(1)}%`,
    count: bucket.count,
    frequency: Number(bucket.frequency),
  }));
}

export function DrawdownTimelineChart({
  points,
  showDrawdown,
}: DrawdownTimelineChartProps) {
  const chartData = buildDrawdownData(points);

  if (!showDrawdown) {
    return <p className="chart-fallback-copy">Drawdown series is hidden by current toggle state.</p>;
  }

  return (
    <div className="chart-surface" role="img" aria-label="Drawdown path timeline chart">
      <div className="chart-canvas">
        <ResponsiveContainer height={280} width="100%">
          <LineChart data={chartData} margin={{ top: 16, right: 16, left: 16, bottom: 8 }}>
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
            <XAxis dataKey="capturedAt" minTickGap={24} stroke="var(--chart-axis)" tickFormatter={formatDateLabel} />
            <YAxis stroke="var(--chart-axis)" tickFormatter={toPercentLabel} width={96} />
            <Tooltip
              formatter={(value) => {
                if (typeof value !== "number") {
                  return value;
                }
                return toPercentLabel(value);
              }}
              labelFormatter={(label) => formatDateLabel(String(label))}
              contentStyle={{
                border: "1px solid var(--color-border-strong)",
                borderRadius: "12px",
                background: "var(--color-surface-strong)",
              }}
            />
            <Line
              dataKey="drawdown"
              dot={false}
              name="Drawdown"
              stroke="var(--color-negative)"
              strokeWidth={2}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function RollingEstimatorsTimelineChart({
  points,
  showVolatility,
  showBeta,
}: RollingTimelineChartProps) {
  const chartData = buildRollingData(points);

  if (!showVolatility && !showBeta) {
    return (
      <p className="chart-fallback-copy">
        Rolling timeline series are hidden by current toggle state.
      </p>
    );
  }

  return (
    <div className="chart-surface" role="img" aria-label="Rolling estimators timeline chart">
      <div className="chart-canvas">
        <ResponsiveContainer height={300} width="100%">
          <LineChart data={chartData} margin={{ top: 16, right: 20, left: 16, bottom: 8 }}>
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
            <XAxis dataKey="capturedAt" minTickGap={24} stroke="var(--chart-axis)" tickFormatter={formatDateLabel} />
            <YAxis
              stroke="var(--chart-axis)"
              tickFormatter={toPercentLabel}
              width={96}
              yAxisId="left"
            />
            <YAxis
              orientation="right"
              stroke="var(--chart-axis)"
              tickFormatter={toNumberLabel}
              width={72}
              yAxisId="right"
            />
            <Tooltip
              formatter={(value, name) => {
                if (typeof value !== "number") {
                  return value;
                }
                if (name === "Rolling volatility") {
                  return toPercentLabel(value);
                }
                return toNumberLabel(value);
              }}
              labelFormatter={(label) => formatDateLabel(String(label))}
              contentStyle={{
                border: "1px solid var(--color-border-strong)",
                borderRadius: "12px",
                background: "var(--color-surface-strong)",
              }}
            />
            {showVolatility ? (
              <Line
                dataKey="volatility"
                dot={false}
                isAnimationActive={false}
                name="Rolling volatility"
                stroke="var(--color-warning)"
                strokeWidth={2}
                type="monotone"
                yAxisId="left"
              />
            ) : null}
            {showBeta ? (
              <Line
                dataKey="beta"
                dot={false}
                isAnimationActive={false}
                name="Rolling beta"
                stroke="var(--color-accent)"
                strokeWidth={2}
                type="monotone"
                yAxisId="right"
              />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function ReturnDistributionChart({
  buckets,
}: ReturnDistributionChartProps) {
  const chartData = buildDistributionData(buckets);
  return (
    <div className="chart-surface" role="img" aria-label="Return distribution chart">
      <div className="chart-canvas">
        <ResponsiveContainer height={280} width="100%">
          <BarChart data={chartData} margin={{ top: 16, right: 16, left: 16, bottom: 8 }}>
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
            <XAxis dataKey="bucketLabel" minTickGap={24} stroke="var(--chart-axis)" />
            <YAxis stroke="var(--chart-axis)" />
            <Tooltip
              formatter={(value, name) => {
                if (typeof value !== "number") {
                  return value;
                }
                if (name === "Frequency") {
                  return `${(value * 100).toFixed(2)}%`;
                }
                return value.toFixed(0);
              }}
              contentStyle={{
                border: "1px solid var(--color-border-strong)",
                borderRadius: "12px",
                background: "var(--color-surface-strong)",
              }}
            />
            <Bar dataKey="count" fill="var(--color-accent)" name="Count" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
