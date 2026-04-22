import { CompactDashboardShell } from "../../components/shell/CompactDashboardShell";
import { PrimaryModuleSkeleton } from "../../components/skeletons/PrimaryModuleSkeleton";
import { StoryContractBlock } from "../../components/storytelling/StoryContractBlock";
import { PrimaryModuleStateFeedback } from "../../components/workspace-layout/PrimaryModuleStateFeedback";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import { useRoutePrimaryModuleStateController } from "../../features/portfolio-workspace/route-module-state";
import { HierarchyPivotTable } from "../../features/portfolio-hierarchy/HierarchyPivotTable";
import { usePortfolioHomeRouteData } from "./hooks/usePortfolioHomeRouteData";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type HomeEquityChartPoint = {
  label: string;
  portfolio: number;
  benchmark: number;
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

function resolveTooltipNumber(value: TooltipValue): number {
  if (Array.isArray(value)) {
    return Number(value[0] ?? 0);
  }
  return Number(value ?? 0);
}

export function PortfolioHomePage() {
  const {
    moduleState,
    isPrimaryModuleLoading,
    shouldRenderBlockingFeedback,
    retryModuleLoad,
  } = useRoutePrimaryModuleStateController();
  const routeData = usePortfolioHomeRouteData();

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
  const equityChartSeries: HomeEquityChartPoint[] = routeData.equitySeries.map((point) => ({
    label: toChartDateLabel(point.capturedAt),
    portfolio: point.portfolioValue,
    benchmark: point.benchmarkValue,
  }));

  return (
    <CompactDashboardShell
      title="Portfolio Home"
      subtitle="Default executive route for current portfolio state, benchmark context, and immediate attention."
      assetDetailHref={routeData.assetDetailHref}
    >
      <section className="panel workspace-panel workspace-panel--hero">
        <p className="route-kicker">Home · Executive command center</p>
        <h2 className="route-heading">How is my portfolio doing right now?</h2>
        <p className="route-subheading">
          First-surface modules answer portfolio state, benchmark context, and
          immediate attention before deeper analysis.
        </p>
        <div className="home-kpi-strip">
          {routeData.kpis.map((kpi) => (
            <article className="home-kpi-card" key={kpi.label}>
              <p className="home-kpi-card__label">{kpi.label}</p>
              <p className="home-kpi-card__value numeric-value">{kpi.value}</p>
              <p className="home-kpi-card__delta">{kpi.delta}</p>
            </article>
          ))}
        </div>
        <div className="home-primary-grid">
          {shouldRenderLoadingSkeleton ? (
            <>
              <PrimaryModuleSkeleton label="Home equity curve" rowCount={5} />
              <PrimaryModuleSkeleton label="Home attention panel" rowCount={4} />
            </>
          ) : shouldRenderBlockingRouteFeedback ? (
            <PrimaryModuleStateFeedback
              moduleState={routeModuleState}
              onRetryModuleLoad={retryModuleLoad}
            />
          ) : (
            <>
              <article className="home-module-card primary-module-card">
                <h3>Equity curve vs benchmark</h3>
                <div className="route-primary-chart" role="img" aria-label="Portfolio and benchmark equity curve comparison">
                  {equityChartSeries.length === 0 ? (
                    <p className="route-chart-empty">Awaiting equity-curve points for selected scope.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={equityChartSeries} margin={{ top: 8, right: 12, left: 8, bottom: 0 }}>
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
                        <Line
                          type="monotone"
                          dataKey="portfolio"
                          stroke="var(--status-info)"
                          strokeWidth={2}
                          dot={false}
                          name="Portfolio"
                        />
                        <Line
                          type="monotone"
                          dataKey="benchmark"
                          stroke="var(--status-success)"
                          strokeWidth={2}
                          dot={false}
                          name="Benchmark"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <StoryContractBlock
                  what="Portfolio equity curve remains above benchmark across observed windows."
                  why="Relative leadership from the strongest holdings supports a modest spread advantage."
                  action="Action state: wait"
                  evidence="Portfolio summary and hierarchy are sourced from the live ledger-backed API."
                />
              </article>
              <article className="home-module-card home-module-card--attention primary-module-card">
                <h3>Needs attention immediately</h3>
                <ul className="home-attention-list">
                  {routeData.attentionItems.map((item) => (
                    <li key={item.label}>
                      <p className="home-attention-list__row">
                        <span>{item.label}</span>
                        <span>{item.status}</span>
                      </p>
                      <p className="home-attention-list__note">{item.note}</p>
                    </li>
                  ))}
                </ul>
                <StoryContractBlock
                  what="Concentration and weak holdings are surfaced as explicit attention items."
                  why="The first route should make downside and portfolio rotation visible immediately."
                  action="Action state: review concentration and down-side positions first."
                  evidence="Attention items are derived from command-center insights and the actual summary ledger."
                />
              </article>
            </>
          )}
        </div>
        {shouldRenderSuccessFeedback ? (
          <PrimaryModuleStateFeedback moduleState={moduleState} />
        ) : null}
      </section>

      <section className="home-secondary-grid home-secondary-grid--triple">
        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Allocation snapshot</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Sleeve</th>
                <th scope="col">Weight</th>
                <th scope="col">Posture</th>
              </tr>
            </thead>
            <tbody>
              {routeData.allocationSlices.map((slice) => (
                <tr key={slice.sleeve}>
                  <td>{slice.sleeve}</td>
                  <td>{slice.weight}</td>
                  <td>{slice.posture}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Top movers</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Ticker</th>
                <th scope="col">Move</th>
                <th scope="col">Catalyst</th>
              </tr>
            </thead>
            <tbody>
              {routeData.topMovers.map((mover) => (
                <tr key={mover.ticker}>
                  <td>{mover.ticker}</td>
                  <td>{mover.move}</td>
                  <td>{mover.catalyst}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Holdings summary table</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Ticker</th>
                <th scope="col">Weight</th>
                <th scope="col">Unrealized</th>
                <th scope="col">Action state</th>
              </tr>
            </thead>
            <tbody>
              {routeData.holdingsSummaryRows.map((row) => (
                <tr key={row.ticker}>
                  <td>{row.ticker}</td>
                  <td>{row.weight}</td>
                  <td>{row.unrealized}</td>
                  <td>{row.state}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <StoryContractBlock
            what="Core holdings remain concentrated in fewer leadership names."
            why="Concentration supports upside but increases downside spillover risk."
            action="Action state: keep adds selective and monitor concentration cap."
            evidence="Holdings summary rows are derived from the live ledger-backed summary endpoint."
          />
        </article>
      </section>

      <details className="panel disclosure-panel">
        <summary>Holdings summary pivot</summary>
        <HierarchyPivotTable
          groups={routeData.hierarchyPivotGroups}
          tableLabel="Home holdings hierarchy pivot"
        />
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
            ? "Home route loading skeletons preserve module geometry while data contracts resolve."
            : routeData.status === "error"
              ? routeData.errorMessage ?? "Failed to load home route portfolio data."
              : "Home route answers state, benchmark spread, and immediate attention in first viewport modules."
        }
      />
    </CompactDashboardShell>
  );
}
