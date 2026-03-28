import {
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatUsdMoney } from "../../core/lib/formatters";
import type { PortfolioContributionRow } from "../../core/api/schemas";
import {
  buildContributionChartData,
  type ContributionChartDatum,
} from "../../features/portfolio-workspace/overview";

type PortfolioContributionChartProps = {
  rows: PortfolioContributionRow[];
};

function formatAxisMoney(value: number): string {
  return formatUsdMoney(value.toFixed(2));
}

export function PortfolioContributionChart({
  rows,
}: PortfolioContributionChartProps) {
  const chartData: ContributionChartDatum[] = buildContributionChartData(rows);

  return (
    <div
      className="chart-surface"
      role="img"
      aria-label="Contribution by symbol chart"
    >
      <BarChart
        data={chartData}
        height={280}
        margin={{ top: 20, right: 20, left: 20, bottom: 8 }}
        width={760}
      >
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
        <XAxis dataKey="instrumentSymbol" stroke="var(--chart-axis)" />
        <YAxis
          stroke="var(--chart-axis)"
          tickFormatter={formatAxisMoney}
          width={96}
        />
        <Tooltip
          contentStyle={{
            border: "1px solid var(--color-border-strong)",
            borderRadius: "12px",
            background: "var(--color-surface-strong)",
          }}
        />
        <Bar
          dataKey="contributionPnl"
          fill="var(--chart-contribution-primary)"
          name="contributionPnl"
          radius={[8, 8, 0, 0]}
        />
      </BarChart>
    </div>
  );
}
