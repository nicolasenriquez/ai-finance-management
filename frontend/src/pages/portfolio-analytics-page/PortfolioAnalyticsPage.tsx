import { CompactDashboardShell } from "../../components/shell/CompactDashboardShell";
import { PrimaryModuleSkeleton } from "../../components/skeletons/PrimaryModuleSkeleton";
import { StoryContractBlock } from "../../components/storytelling/StoryContractBlock";
import { PrimaryModuleStateFeedback } from "../../components/workspace-layout/PrimaryModuleStateFeedback";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import { useRoutePrimaryModuleStateController } from "../../features/portfolio-workspace/route-module-state";
import { usePortfolioAnalyticsRouteData } from "./hooks/usePortfolioAnalyticsRouteData";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type MonthlyHeatmapCell = {
  month: string;
  portfolio: string;
  benchmark: string;
  state: "strong" | "neutral" | "weak";
};

const MONTHLY_HEATMAP: MonthlyHeatmapCell[] = [
  { month: "Jan", portfolio: "+2.3%", benchmark: "+1.8%", state: "strong" },
  { month: "Feb", portfolio: "-0.4%", benchmark: "-0.6%", state: "neutral" },
  { month: "Mar", portfolio: "+3.2%", benchmark: "+2.1%", state: "strong" },
  { month: "Apr", portfolio: "+1.1%", benchmark: "+0.7%", state: "neutral" },
  { month: "May", portfolio: "-1.2%", benchmark: "-0.8%", state: "weak" },
  { month: "Jun", portfolio: "+2.7%", benchmark: "+1.5%", state: "strong" },
];

type RollingReturnPoint = {
  window: string;
  portfolio: string;
  benchmark: string;
  spread: string;
};

const ROLLING_RETURN_WINDOWS: RollingReturnPoint[] = [
  { window: "30D", portfolio: "+1.4%", benchmark: "+0.8%", spread: "+60 bps" },
  { window: "90D", portfolio: "+4.7%", benchmark: "+2.6%", spread: "+210 bps" },
  { window: "180D", portfolio: "+9.5%", benchmark: "+7.0%", spread: "+250 bps" },
];

type PerformanceChartPoint = {
  label: string;
  portfolio: number;
  benchmark: number;
};

type ContributionRankPoint = {
  ticker: string;
  impact: number;
};

type WaterfallPoint = {
  label: string;
  delta: number;
  cumulative: number;
};

type TooltipValue = number | string | ReadonlyArray<number | string> | undefined;

const moneyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function toChartDateLabel(capturedAt: string): string {
  const normalized = capturedAt.slice(0, 10);
  const [year, month, day] = normalized.split("-");
  if (!year || !month || !day) {
    return normalized;
  }
  return `${month}/${day}`;
}

function buildAttributionWaterfallSeries(
  points: ContributionRankPoint[],
): WaterfallPoint[] {
  let cumulative = 0;
  const rows = points.map((point) => {
    cumulative += point.impact;
    return {
      label: point.ticker,
      delta: point.impact,
      cumulative,
    };
  });
  return rows;
}

function resolveTooltipNumber(value: TooltipValue): number {
  if (Array.isArray(value)) {
    return Number(value[0] ?? 0);
  }
  return Number(value ?? 0);
}

export function PortfolioAnalyticsPage() {
  const {
    moduleState,
    isPrimaryModuleLoading,
    shouldRenderBlockingFeedback,
    retryModuleLoad,
  } = useRoutePrimaryModuleStateController();
  const routeData = usePortfolioAnalyticsRouteData();
  const shouldRenderLoadingSkeleton = isPrimaryModuleLoading;
  const shouldRenderBlockingRouteFeedback = shouldRenderBlockingFeedback;
  const routeModuleState =
    routeData.status === "error"
      ? "error"
      : routeData.status === "empty"
        ? "empty"
        : moduleState === "success"
          ? "ready"
          : moduleState;
  const shouldRenderSuccessFeedback = moduleState === "success" && routeData.status === "ready";
  const topContributorLabels = routeData.contributionDrivers
    .slice(0, 2)
    .map((driver) => driver.ticker)
    .join(" and ");
  const performanceChartSeries: PerformanceChartPoint[] = routeData.performanceSeries.map((point) => ({
    label: toChartDateLabel(point.capturedAt),
    portfolio: point.portfolioValue,
    benchmark: point.benchmarkValue,
  }));
  const contributionRankSeries: ContributionRankPoint[] = routeData.contributionDrivers
    .slice(0, 5)
    .map((driver) => ({
      ticker: driver.ticker,
      impact: driver.contributionValue,
    }));
  const attributionWaterfallSeries = buildAttributionWaterfallSeries(
    routeData.contributionDrivers.slice(0, 4).map((driver) => ({
      ticker: driver.ticker,
      impact: driver.contributionValue,
    })),
  );

  return (
    <CompactDashboardShell
      title="Portfolio Analytics"
      subtitle="Performance explainability route for attribution and consistency review."
      assetDetailHref={routeData.assetDetailHref}
    >
      <section className="panel workspace-panel workspace-panel--hero">
        <p className="route-kicker">Analytics · Explainability</p>
        <h2 className="route-heading">Why did the portfolio move?</h2>
        <p className="route-subheading">
          Explainability stays compact: performance first, attribution second, and
          consistency validation via bounded secondary modules.
        </p>

        <div className="analytics-first-viewport-grid">
          {shouldRenderLoadingSkeleton ? (
            <>
              <PrimaryModuleSkeleton label="Analytics performance curve" rowCount={5} />
              <PrimaryModuleSkeleton label="Analytics attribution waterfall" rowCount={5} />
              <PrimaryModuleSkeleton label="Analytics contribution leaders" rowCount={5} />
            </>
          ) : shouldRenderBlockingRouteFeedback ? (
            <PrimaryModuleStateFeedback
              moduleState={routeModuleState}
              onRetryModuleLoad={retryModuleLoad}
            />
          ) : (
            <>
              <article className="analytics-module-card primary-module-card">
                <h3>Performance curve</h3>
                <div className="route-primary-chart" role="img" aria-label="Portfolio and benchmark performance curve">
                  {performanceChartSeries.length === 0 ? (
                    <p className="route-chart-empty">Awaiting relative-performance points for selected scope.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={performanceChartSeries}
                        margin={{ top: 8, right: 12, left: 8, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={18} />
                        <YAxis
                          tickFormatter={(value: number) => moneyFormatter.format(value)}
                          tick={{ fontSize: 11 }}
                          width={94}
                        />
                        <Tooltip
                          formatter={(value: TooltipValue) =>
                            moneyFormatter.format(resolveTooltipNumber(value))}
                          labelFormatter={(label) => `Date: ${label}`}
                        />
                        <Legend />
                        <Line type="monotone" dataKey="portfolio" stroke="var(--status-info)" strokeWidth={2} dot={false} name="Portfolio" />
                        <Line type="monotone" dataKey="benchmark" stroke="var(--status-success)" strokeWidth={2} dot={false} name="Benchmark" />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <StoryContractBlock
                  what="Portfolio return stays above benchmark across the visible periods."
                  why="Relative leadership from the highest-conviction holdings supports the spread."
                  action="Action state: keep winners while monitoring concentration."
                  evidence="Performance curve remains a compact visual; detailed contribution comes from the ledger-backed portfolio API."
                />
              </article>

              <article className="analytics-module-card primary-module-card">
                <h3>Attribution waterfall</h3>
                <div className="route-primary-chart" role="img" aria-label="Portfolio attribution waterfall chart">
                  {attributionWaterfallSeries.length === 0 ? (
                    <p className="route-chart-empty">Attribution waterfall pending contribution payload.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart
                        data={attributionWaterfallSeries}
                        margin={{ top: 8, right: 12, left: 8, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                        <YAxis
                          tickFormatter={(value: number) => moneyFormatter.format(value)}
                          tick={{ fontSize: 11 }}
                          width={90}
                        />
                        <Tooltip
                          formatter={(value: TooltipValue, name) => [
                            moneyFormatter.format(resolveTooltipNumber(value)),
                            name === "delta" ? "Impact" : "Cumulative",
                          ]}
                        />
                        <Legend />
                        <Bar dataKey="delta" name="Impact">
                          {attributionWaterfallSeries.map((point) => (
                            <Cell
                              key={point.label}
                              fill={point.delta >= 0 ? "var(--status-success)" : "var(--status-error)"}
                            />
                          ))}
                        </Bar>
                        <Line
                          dataKey="cumulative"
                          type="monotone"
                          stroke="var(--status-info)"
                          strokeWidth={2}
                          dot={false}
                          name="Cumulative"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <StoryContractBlock
                  what="Attribution remains net positive after sector and stock-selection effects."
                  why="Selection alpha offsets smaller FX and fee drags."
                  action="Action state: keep current model weights and monitor negative drags."
                  evidence="Waterfall module uses bounded explanatory framing while the contribution table uses live portfolio symbols."
                />
              </article>

              <article className="analytics-module-card primary-module-card">
                <h3>Contribution leaders</h3>
                <div className="route-primary-chart" role="img" aria-label="Portfolio contribution ranking chart">
                  {contributionRankSeries.length === 0 ? (
                    <p className="route-chart-empty">Contribution ranking pending contribution payload.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={contributionRankSeries}
                        layout="vertical"
                        margin={{ top: 8, right: 12, left: 8, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis
                          type="number"
                          tickFormatter={(value: number) => moneyFormatter.format(value)}
                          tick={{ fontSize: 11 }}
                        />
                        <YAxis type="category" dataKey="ticker" tick={{ fontSize: 11 }} width={52} />
                        <Tooltip
                          formatter={(value: TooltipValue) =>
                            moneyFormatter.format(resolveTooltipNumber(value))}
                        />
                        <Bar dataKey="impact" name="Contribution">
                          {contributionRankSeries.map((point) => (
                            <Cell
                              key={point.ticker}
                              fill={point.impact >= 0 ? "var(--status-success)" : "var(--status-error)"}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <StoryContractBlock
                  what={`${topContributorLabels} remain the strongest contribution leaders.`}
                  why="Contribution breadth is still concentrated in a small number of sleeves."
                  action="Action state: maintain leaders and monitor concentration spillover."
                  evidence="Leader rank uses the live contribution endpoint backed by the portfolio ledger."
                />
              </article>
            </>
          )}
        </div>
        {shouldRenderSuccessFeedback ? (
          <PrimaryModuleStateFeedback moduleState={moduleState} />
        ) : null}
      </section>

      <section className="analytics-secondary-grid">
        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Monthly return heatmap</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Month</th>
                <th scope="col">Portfolio</th>
                <th scope="col">Benchmark</th>
                <th scope="col">State cue</th>
              </tr>
            </thead>
            <tbody>
              {MONTHLY_HEATMAP.map((cell) => (
                <tr key={cell.month}>
                  <td>{cell.month}</td>
                  <td>{cell.portfolio}</td>
                  <td>{cell.benchmark}</td>
                  <td>{cell.state === "strong" ? "Strong (outperforming month)" : cell.state === "weak" ? "Weak (underperforming month)" : "Neutral (within band)"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Rolling return chart</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Window</th>
                <th scope="col">Portfolio</th>
                <th scope="col">Benchmark</th>
                <th scope="col">Spread</th>
              </tr>
            </thead>
            <tbody>
              {ROLLING_RETURN_WINDOWS.map((row) => (
                <tr key={row.window}>
                  <td>{row.window}</td>
                  <td>{row.portfolio}</td>
                  <td>{row.benchmark}</td>
                  <td>{row.spread}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Drill-down contribution table</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Ticker</th>
                <th scope="col">Sector</th>
                <th scope="col">Contribution</th>
                <th scope="col">Consistency</th>
                <th scope="col">Posture</th>
              </tr>
            </thead>
            <tbody>
              {routeData.drillDownRows.map((row) => (
                <tr key={row.ticker}>
                  <td>{row.ticker}</td>
                  <td>{row.sector}</td>
                  <td>{row.contribution}</td>
                  <td>{row.consistency}</td>
                  <td>{row.posture}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <StoryContractBlock
            what="Contribution drill-down keeps the row-level explanation compact and auditable."
            why="The route answers why first, then shows a bounded table for evidence."
            action="Action state: review top contributors before expanding into deeper report views."
            evidence="Contribution and sector labels are sourced from the live ledger-backed portfolio API."
          />
        </article>
      </section>

      <details className="panel disclosure-panel">
        <summary>Advanced attribution disclosure</summary>
        <p>Deeper decomposition stays bounded so this route answers why first.</p>
      </details>

      <WorkspaceStateBanner
        state={
          shouldRenderLoadingSkeleton
            ? "loading"
            : shouldRenderBlockingRouteFeedback
              ? routeModuleState
              : "ready"
        }
        hierarchy="standard"
        message={
          shouldRenderLoadingSkeleton
            ? "Analytics route loading skeletons preserve module geometry while data contracts resolve."
            : routeData.status === "error"
              ? routeData.errorMessage ?? "Failed to load analytics route portfolio data."
              : "Analytics route answers why, which holdings drove the result, and whether performance is consistent."
        }
      />
    </CompactDashboardShell>
  );
}
