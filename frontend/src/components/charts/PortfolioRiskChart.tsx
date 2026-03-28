import {
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PortfolioRiskEstimatorMetric } from "../../core/api/schemas";
import {
  buildRiskChartData,
  type RiskChartDatum,
} from "../../features/portfolio-workspace/overview";

type PortfolioRiskChartProps = {
  metrics: PortfolioRiskEstimatorMetric[];
};

export function PortfolioRiskChart({ metrics }: PortfolioRiskChartProps) {
  const chartData: RiskChartDatum[] = buildRiskChartData(metrics);

  return (
    <div className="chart-surface" role="img" aria-label="Risk metrics chart">
      <BarChart
        data={chartData}
        height={280}
        margin={{ top: 20, right: 20, left: 20, bottom: 8 }}
        width={760}
      >
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
        <XAxis dataKey="estimatorId" stroke="var(--chart-axis)" />
        <YAxis stroke="var(--chart-axis)" width={96} />
        <Tooltip
          contentStyle={{
            border: "1px solid var(--color-border-strong)",
            borderRadius: "12px",
            background: "var(--color-surface-strong)",
          }}
        />
        <Bar
          dataKey="value"
          fill="var(--chart-risk-primary)"
          radius={[8, 8, 0, 0]}
        />
      </BarChart>
    </div>
  );
}
