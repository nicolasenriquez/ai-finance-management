import {
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
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
  const chartData: ContributionChartDatum[] = buildContributionChartData(rows)
    .sort((left, right) => Math.abs(right.contributionPnl) - Math.abs(left.contributionPnl))
    .slice(0, 8);

  return (
    <div
      className="chart-surface"
      role="img"
      aria-label="Contribution by symbol chart"
    >
      <div className="chart-canvas">
        <ResponsiveContainer height={280} width="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 20, right: 20, left: 20, bottom: 8 }}
          >
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
            <XAxis
              stroke="var(--chart-axis)"
              tickFormatter={formatAxisMoney}
              type="number"
            />
            <YAxis
              dataKey="instrumentSymbol"
              stroke="var(--chart-axis)"
              type="category"
              width={96}
            />
            <ReferenceLine stroke="var(--color-border-strong)" x={0} />
            <Tooltip
              formatter={(value) => {
                if (typeof value !== "number") {
                  return value;
                }
                return formatUsdMoney(value.toFixed(2));
              }}
              contentStyle={{
                border: "1px solid var(--color-border-strong)",
                borderRadius: "12px",
                background: "var(--color-surface-strong)",
              }}
            />
            <Bar
              dataKey="contributionPnl"
              name="Contribution (USD)"
              radius={[6, 6, 6, 6]}
            >
              {chartData.map((row) => (
                <Cell
                  fill={
                    row.contributionPnl >= 0
                      ? "var(--color-positive)"
                      : "var(--color-negative)"
                  }
                  key={row.instrumentSymbol}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
