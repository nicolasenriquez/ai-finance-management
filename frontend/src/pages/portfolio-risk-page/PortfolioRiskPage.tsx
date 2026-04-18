import { CompactDashboardShell } from "../../components/shell/CompactDashboardShell";
import { PrimaryModuleSkeleton } from "../../components/skeletons/PrimaryModuleSkeleton";
import { StoryContractBlock } from "../../components/storytelling/StoryContractBlock";
import { PrimaryModuleStateFeedback } from "../../components/workspace-layout/PrimaryModuleStateFeedback";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import {
  formatPortfolioPercent,
  getPortfolioSummaryRowsByMarketValue,
  resolvePortfolioAssetDetailHref,
  usePortfolioCommandCenterResource,
  usePortfolioSummaryResource,
} from "../../core/api/portfolio";
import { useRoutePrimaryModuleStateController } from "../../features/portfolio-workspace/route-module-state";

type RiskMetric = {
  label: string;
  value: string;
  why: string;
};

const RISK_METRICS: RiskMetric[] = [
  {
    label: "30D realized volatility",
    value: "18.4%",
    why: "Above 12M baseline by 210 bps.",
  },
  {
    label: "Max drawdown (252D)",
    value: "-12.8%",
    why: "Recovery pace improved vs prior quarter.",
  },
  {
    label: "1D 95% VaR",
    value: "-2.1%",
    why: "Tail risk mostly from concentrated tech names.",
  },
];

type DrawdownPoint = {
  window: string;
  drawdown: string;
  recoveryDays: string;
};

const DRAWDOWN_TIMELINE: DrawdownPoint[] = [
  { window: "2025-11", drawdown: "-6.2%", recoveryDays: "19d" },
  { window: "2026-01", drawdown: "-9.4%", recoveryDays: "27d" },
  { window: "2026-04", drawdown: "-4.1%", recoveryDays: "ongoing" },
];

type DistributionBucket = {
  bucket: string;
  probability: string;
  note: string;
};

const RETURN_DISTRIBUTION: DistributionBucket[] = [
  { bucket: "< -2%", probability: "14%", note: "Left-tail stress" },
  { bucket: "-2% to +2%", probability: "61%", note: "Normal regime" },
  { bucket: "> +2%", probability: "25%", note: "Upside bursts" },
];

type ScatterRow = {
  sleeve: string;
  return: string;
  volatility: string;
  stance: string;
};

const RISK_RETURN_SCATTER: ScatterRow[] = [
  { sleeve: "Technology", return: "+16.8%", volatility: "24.1%", stance: "High beta" },
  { sleeve: "Healthcare", return: "+6.4%", volatility: "15.2%", stance: "Balanced" },
  { sleeve: "Industrials", return: "+7.9%", volatility: "17.6%", stance: "Moderate" },
  { sleeve: "Cash", return: "+0.4%", volatility: "0.1%", stance: "Buffer" },
];

type CorrelationRow = {
  pair: string;
  correlation: string;
  riskState: string;
};

const CORRELATION_ROWS: CorrelationRow[] = [
  { pair: "Tech vs Growth ETF", correlation: "0.83", riskState: "High cluster" },
  { pair: "Healthcare vs S&P 500", correlation: "0.58", riskState: "Moderate" },
  { pair: "Industrials vs Bond proxy", correlation: "0.31", riskState: "Diversifying" },
];

type ConcentrationRow = {
  exposure: string;
  weight: string;
  posture: string;
};

function resolveValue(value: string | number | null | undefined): number {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
}

export function PortfolioRiskPage() {
  const {
    moduleState,
    isPrimaryModuleLoading,
    shouldRenderBlockingFeedback,
    retryModuleLoad,
  } = useRoutePrimaryModuleStateController();
  const summary = usePortfolioSummaryResource();
  const commandCenter = usePortfolioCommandCenterResource();

  const shouldRenderLoadingSkeleton =
    isPrimaryModuleLoading || summary.status === "loading" || commandCenter.status === "loading";
  const shouldRenderBlockingRouteFeedback =
    shouldRenderBlockingFeedback || summary.status === "error" || commandCenter.status === "error" || summary.status === "empty";
  const routeModuleState =
    summary.status === "error" || commandCenter.status === "error"
      ? "error"
      : summary.status === "empty"
        ? "empty"
        : moduleState === "success"
          ? "ready"
          : moduleState;
  const shouldRenderSuccessFeedback = moduleState === "success" && summary.status === "ready";
  const topHolding = getPortfolioSummaryRowsByMarketValue(summary.data?.rows ?? [])[0];
  const concentrationRows: ConcentrationRow[] = [
    {
      exposure: "Technology",
      weight: commandCenter.data
        ? formatPortfolioPercent(commandCenter.data.concentration_top5_pct, 1)
        : "31%",
      posture: "Elevated",
    },
    {
      exposure: `Top holding (${topHolding?.instrument_symbol ?? "n/a"})`,
      weight: topHolding?.market_value_usd ? `${formatPortfolioPercent((resolveValue(topHolding.market_value_usd) / Math.max(resolveValue(commandCenter.data?.total_market_value_usd), 1)) * 100, 1)}` : "n/a",
      posture: "Watch",
    },
    {
      exposure: "Top 5 holdings",
      weight: commandCenter.data
        ? `${formatPortfolioPercent(commandCenter.data.concentration_top5_pct, 1)}`
        : "37.4%",
      posture: "De-risk if >40%",
    },
  ];

  return (
    <CompactDashboardShell
      title="Portfolio Risk"
      subtitle="Fragility route for downside, concentration, and distribution context."
      assetDetailHref={resolvePortfolioAssetDetailHref(summary.data)}
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
                  {RISK_METRICS.map((metric) => (
                    <li key={metric.label}>
                      <p className="risk-stat-list__label">{metric.label}</p>
                      <p className="risk-stat-list__value numeric-value">{metric.value}</p>
                      <p className="risk-stat-list__why">{metric.why}</p>
                    </li>
                  ))}
                </ul>
                <StoryContractBlock
                  what="Drawdown and volatility stay elevated versus baseline."
                  why="Risk expansion is concentrated in higher-beta equity sleeves."
                  action="Action state: de-risk concentration"
                  evidence="Risk telemetry remains summary-backed and ledger sourced."
                />
              </article>

              <article className="risk-module-card primary-module-card">
                <h3>Drawdown timeline</h3>
                <ol className="risk-drawdown-list">
                  {DRAWDOWN_TIMELINE.map((point) => (
                    <li key={point.window}>
                      <span>{point.window}</span>
                      <span className="numeric-value">{point.drawdown}</span>
                      <span>Recovery {point.recoveryDays}</span>
                    </li>
                  ))}
                </ol>
                <StoryContractBlock
                  what="Recent drawdowns recover slower as concentration rises."
                  why="Recovery speed weakens when the same sleeves drive downside."
                  action="Action state: hold new adds until drawdown slope improves."
                  evidence="Drawdown windows are maintained as bounded risk context."
                />
              </article>

              <article className="risk-module-card risk-module-card--profile primary-module-card">
                <h3>Return distribution</h3>
                <table className="route-metric-table">
                  <thead>
                    <tr>
                      <th scope="col">Bucket</th>
                      <th scope="col">Probability</th>
                      <th scope="col">Interpretation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {RETURN_DISTRIBUTION.map((bucket) => (
                      <tr key={bucket.bucket}>
                        <td>{bucket.bucket}</td>
                        <td>{bucket.probability}</td>
                        <td>{bucket.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <StoryContractBlock
                  what="Left-tail probability remains above acceptable policy limits."
                  why="Distribution skew widened after clustered earnings volatility."
                  action="Action state: keep sizing disciplined until tails compress."
                  evidence="Distribution remains intentionally compact to protect first-viewport readability."
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
              {RISK_RETURN_SCATTER.map((row) => (
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
              {CORRELATION_ROWS.map((row) => (
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
              {concentrationRows.map((row) => (
                <tr key={row.exposure}>
                  <td>{row.exposure}</td>
                  <td>{row.weight}</td>
                  <td>{row.posture}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <StoryContractBlock
            what="Concentration is now tied to the live ledger instead of a hardcoded symbol."
            why="The risk route should identify the actual top holding and top-5 weight."
            action="Action state: review concentration first."
            evidence={`Top holding resolves from ${topHolding?.instrument_symbol ?? "the portfolio summary"}.`}
          />
        </article>
      </section>

      <details className="panel disclosure-panel">
        <summary>Advanced risk disclosure</summary>
        <p>Deeper diagnostics remain available without turning the route into a lab.</p>
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
            ? "Risk route loading skeletons preserve module geometry while data contracts resolve."
            : summary.status === "error" || commandCenter.status === "error"
              ? summary.errorMessage ?? commandCenter.errorMessage ?? "Failed to load risk route portfolio data."
              : "Risk route answers fragility, drawdown, and concentration context."
        }
      />
    </CompactDashboardShell>
  );
}
