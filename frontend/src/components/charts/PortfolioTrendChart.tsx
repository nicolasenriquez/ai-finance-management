import {
  CartesianGrid,
  Line,
  LineChart,
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

type PortfolioTrendChartProps = {
  points: PortfolioTimeSeriesPoint[];
};

function formatAxisMoney(value: number): string {
  return formatUsdMoney(value.toFixed(2));
}

export function PortfolioTrendChart({ points }: PortfolioTrendChartProps) {
  const chartData: TrendChartDatum[] = buildTrendChartData(points);

  return (
    <div className="chart-surface" role="img" aria-label="Portfolio trend chart">
      <LineChart
        data={chartData}
        height={280}
        margin={{ top: 20, right: 20, left: 20, bottom: 8 }}
        width={760}
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
        <Tooltip
          contentStyle={{
            border: "1px solid var(--color-border-strong)",
            borderRadius: "12px",
            background: "var(--color-surface-strong)",
          }}
        />
        <Line
          dataKey="portfolioValue"
          dot={false}
          name="Portfolio value"
          stroke="var(--chart-trend-primary)"
          strokeWidth={3}
          type="monotone"
          yAxisId="left"
        />
        <Line
          dataKey="pnl"
          dot={false}
          name="PnL"
          stroke="var(--chart-trend-secondary)"
          strokeWidth={2}
          type="monotone"
          yAxisId="right"
        />
      </LineChart>
    </div>
  );
}
