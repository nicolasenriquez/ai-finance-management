import { CompactDashboardShell } from "../../components/shell/CompactDashboardShell";
import { PrimaryModuleSkeleton } from "../../components/skeletons/PrimaryModuleSkeleton";
import { StoryContractBlock } from "../../components/storytelling/StoryContractBlock";
import { PrimaryModuleStateFeedback } from "../../components/workspace-layout/PrimaryModuleStateFeedback";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import { useRoutePrimaryModuleStateController } from "../../features/portfolio-workspace/route-module-state";
import { usePortfolioRiskRouteData } from "./hooks/usePortfolioRiskRouteData";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const percentFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 1,
});

type TooltipValue = number | string | ReadonlyArray<number | string> | undefined;

function resolveTooltipNumber(value: TooltipValue): number {
  if (Array.isArray(value)) {
    return Number(value[0] ?? 0);
  }
  return Number(value ?? 0);
}

export function PortfolioRiskPage() {
  const {
    moduleState,
    isPrimaryModuleLoading,
    shouldRenderBlockingFeedback,
    retryModuleLoad,
  } = useRoutePrimaryModuleStateController();
  const routeData = usePortfolioRiskRouteData();

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

  return (
    <CompactDashboardShell
      title="Portfolio Risk"
      subtitle="Fragility route for downside, concentration, and distribution context."
      assetDetailHref={routeData.assetDetailHref}
    >
      <section className="panel workspace-panel workspace-panel--hero">
        <p className="route-kicker">Risk · Downside control</p>
        <h2 className="route-heading">How fragile is the portfolio?</h2>
        <p className="route-subheading">
          Fragility stays explicit: posture first, drawdown second, and return
          distribution third before secondary diagnostics.
        </p>

        <div className="risk-first-viewport-grid">
          {shouldRenderLoadingSkeleton ? (
            <>
              <PrimaryModuleSkeleton label="Risk posture" rowCount={5} />
              <PrimaryModuleSkeleton label="Risk drawdown timeline" rowCount={5} />
              <PrimaryModuleSkeleton label="Risk return distribution" rowCount={5} />
            </>
          ) : shouldRenderBlockingRouteFeedback ? (
            <PrimaryModuleStateFeedback
              moduleState={routeModuleState}
              onRetryModuleLoad={retryModuleLoad}
            />
          ) : (
            <>
              <article className="risk-module-card primary-module-card">
                <h3>Risk posture</h3>
                <ul className="risk-stat-list">
                  {routeData.riskMetrics.map((metric) => (
                    <li key={metric.label}>
                      <p className="risk-stat-list__label">{metric.label}</p>
                      <p className="risk-stat-list__value numeric-value">{metric.value}</p>
                      <p className="risk-stat-list__why">{metric.why}</p>
                    </li>
                  ))}
                </ul>
                <div className="route-primary-chart" role="img" aria-label="Rolling volatility and VaR risk chart">
                  {routeData.rollingRiskSeries.length === 0 ? (
                    <p className="route-chart-empty">Rolling risk estimate awaits enough return observations.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={routeData.rollingRiskSeries}
                        margin={{ top: 8, right: 12, left: 8, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={18} />
                        <YAxis
                          tickFormatter={(value: number) => `${percentFormatter.format(value)}%`}
                          tick={{ fontSize: 11 }}
                          width={68}
                        />
                        <Tooltip
                          formatter={(value: TooltipValue, name) => [
                            `${percentFormatter.format(resolveTooltipNumber(value))}%`,
                            name === "var95Pct" ? "VaR 95%" : "Rolling volatility",
                          ]}
                        />
                        <Legend />
                        <Line
                          dataKey="volatilityPct"
                          type="monotone"
                          stroke="var(--status-info)"
                          strokeWidth={2}
                          dot={false}
                          name="Rolling volatility"
                        />
                        <Line
                          dataKey="var95Pct"
                          type="monotone"
                          stroke="var(--status-error)"
                          strokeWidth={2}
                          dot={false}
                          name="VaR 95%"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <StoryContractBlock
                  what="Drawdown and volatility are computed from contract-backed route time series."
                  why="Risk expansion remains concentrated when leadership sleeves drive returns."
                  action="Action state: de-risk concentration when drawdown and VaR worsen together."
                  evidence="Risk posture values are derived from `/portfolio/time-series`, `/portfolio/summary`, and `/portfolio/command-center`."
                />
              </article>

              <article className="risk-module-card primary-module-card">
                <h3>Drawdown timeline</h3>
                <div className="route-primary-chart" role="img" aria-label="Portfolio drawdown timeline chart">
                  {routeData.drawdownSeries.length === 0 ? (
                    <p className="route-chart-empty">Drawdown timeline awaits route time-series points.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={routeData.drawdownSeries}
                        margin={{ top: 8, right: 12, left: 8, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={18} />
                        <YAxis
                          tickFormatter={(value: number) => `${percentFormatter.format(value)}%`}
                          tick={{ fontSize: 11 }}
                          width={68}
                        />
                        <Tooltip
                          formatter={(value: TooltipValue) =>
                            `${percentFormatter.format(resolveTooltipNumber(value))}%`}
                          labelFormatter={(label) => `Date: ${label}`}
                        />
                        <Area
                          dataKey="drawdownPct"
                          type="monotone"
                          stroke="var(--status-error)"
                          fill="var(--risk-drawdown-fill)"
                          strokeWidth={2}
                          name="Drawdown"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <StoryContractBlock
                  what="Drawdown windows now track the worst points in the selected route window."
                  why="Peak-to-trough context is required before adding tactical risk."
                  action="Action state: wait on aggressive adds while drawdown slope remains negative."
                  evidence="Timeline rows are derived from route-level 90D time series values."
                />
              </article>

              <article className="risk-module-card risk-module-card--profile primary-module-card">
                <h3>Return distribution</h3>
                <div className="route-primary-chart" role="img" aria-label="Portfolio return distribution chart">
                  {routeData.distributionSeries.length === 0 ? (
                    <p className="route-chart-empty">Distribution buckets are unavailable for selected scope.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={routeData.distributionSeries}
                        margin={{ top: 8, right: 12, left: 8, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
                        <YAxis
                          tickFormatter={(value: number) => `${percentFormatter.format(value)}%`}
                          tick={{ fontSize: 11 }}
                          width={64}
                        />
                        <Tooltip
                          formatter={(value: TooltipValue) =>
                            `${percentFormatter.format(resolveTooltipNumber(value))}%`}
                        />
                        <Bar dataKey="probabilityPct" fill="var(--status-success)" name="Probability" />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <StoryContractBlock
                  what="Distribution buckets are generated from realized route return observations."
                  why="Left-tail share and central tendency guide downside pacing decisions."
                  action="Action state: keep sizing disciplined until left-tail frequency contracts."
                  evidence="Distribution is derived from contract-backed return series, not static placeholders."
                />
              </article>
            </>
          )}
        </div>
        {shouldRenderSuccessFeedback ? (
          <PrimaryModuleStateFeedback moduleState={moduleState} />
        ) : null}
      </section>

      <section className="risk-secondary-grid">
        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Risk/return scatter</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Sleeve</th>
                <th scope="col">Return</th>
                <th scope="col">Volatility</th>
                <th scope="col">Stance</th>
              </tr>
            </thead>
            <tbody>
              {routeData.riskReturnScatter.map((row) => (
                <tr key={row.sleeve}>
                  <td>{row.sleeve}</td>
                  <td>{row.return}</td>
                  <td>{row.volatility}</td>
                  <td>{row.stance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Correlation heatmap</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Pair</th>
                <th scope="col">Correlation</th>
                <th scope="col">Risk state</th>
              </tr>
            </thead>
            <tbody>
              {routeData.correlationRows.map((row) => (
                <tr key={row.pair}>
                  <td>{row.pair}</td>
                  <td>{row.correlation}</td>
                  <td>{row.riskState}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Concentration table</h3>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Exposure</th>
                <th scope="col">Weight</th>
                <th scope="col">Posture</th>
              </tr>
            </thead>
            <tbody>
              {routeData.concentrationRows.map((row) => (
                <tr key={row.exposure}>
                  <td>{row.exposure}</td>
                  <td>{row.weight}</td>
                  <td>{row.posture}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <StoryContractBlock
            what="Concentration table reflects live top-holding and top-5 exposure context."
            why="Concentration drift is the fastest path to hidden portfolio fragility."
            action="Action state: review concentration before promoting tactical adds."
            evidence="Concentration rows use command-center and summary contracts from the current scope."
          />
        </article>
      </section>

      <details className="panel disclosure-panel">
        <summary>Advanced risk disclosure</summary>
        <p>Secondary risk diagnostics remain bounded and cannot displace first-viewport fragility interpretation.</p>
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
            ? "Risk route loading skeletons preserve module geometry while contracts resolve."
            : routeData.status === "error"
              ? routeData.errorMessage ?? "Failed to load risk route portfolio data."
              : "Risk route answers fragility using contract-backed drawdown, distribution, and concentration context."
        }
      />
    </CompactDashboardShell>
  );
}
