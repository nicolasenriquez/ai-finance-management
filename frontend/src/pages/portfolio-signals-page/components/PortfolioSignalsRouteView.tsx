import { CompactDashboardShell } from "../../../components/shell/CompactDashboardShell";
import { PrimaryModuleSkeleton } from "../../../components/skeletons/PrimaryModuleSkeleton";
import { StoryContractBlock } from "../../../components/storytelling/StoryContractBlock";
import { PrimaryModuleStateFeedback } from "../../../components/workspace-layout/PrimaryModuleStateFeedback";
import { WorkspaceStateBanner } from "../../../components/workspace-layout/WorkspaceStateBanner";
import { useRoutePrimaryModuleStateController } from "../../../features/portfolio-workspace/route-module-state";
import type { YFinanceAdapterRow } from "../../../features/portfolio-workspace/yfinance-extraction-adapters";
import type { PortfolioSignalsRouteState } from "../hooks/usePortfolioSignalsRouteState";

type PortfolioSignalsRouteViewProps = {
  routeState: PortfolioSignalsRouteState;
};

function formatAdapterValue(row: YFinanceAdapterRow): string {
  if (row.value === null) {
    return "Unavailable";
  }
  if (row.unit === "percent") {
    return `${(row.value * 100).toFixed(2)}%`;
  }
  if (row.unit === "count") {
    return row.value.toFixed(0);
  }
  if (row.unit === "volume") {
    return row.value.toLocaleString();
  }
  if (row.unit === "price") {
    return row.value.toFixed(2);
  }
  return row.value.toFixed(2);
}

function resolveAvailabilityCue(availability: YFinanceAdapterRow["availability"]): string {
  if (availability === "direct") {
    return "Availability cue: direct source extraction";
  }
  if (availability === "derived") {
    return "Availability cue: derived from direct source data";
  }
  return "Availability cue: unavailable until source contract resolves";
}

export function PortfolioSignalsRouteView({
  routeState,
}: PortfolioSignalsRouteViewProps) {
  const {
    moduleState,
    isPrimaryModuleLoading,
    shouldRenderBlockingFeedback,
    retryModuleLoad,
  } = useRoutePrimaryModuleStateController();
  const shouldRenderSuccessFeedback = moduleState === "success";
  const topMomentumTickers =
    routeState.momentumRanking.length > 0
      ? routeState.momentumRanking.map((candidate) => candidate.ticker).join(", ")
      : "Live holdings";

  return (
    <CompactDashboardShell
      title="Portfolio Signals"
      subtitle="Secondary opportunities route for tactical review with explicit contract visibility."
      assetDetailHref={routeState.assetDetailHref}
    >
      <section className="panel workspace-panel workspace-panel--hero">
        <p className="route-kicker">Signals · Secondary tactical overlay</p>
        <h2 className="route-heading">Which opportunities deserve review?</h2>
        <p className="route-subheading">
          Tactical review remains secondary and compact: trend regime context first,
          momentum ranking second, technical table third, and watchlist panel fourth.
        </p>

        <div className="signals-first-viewport-grid">
          {isPrimaryModuleLoading ? (
            <>
              <PrimaryModuleSkeleton label="Signals trend regime summary" rowCount={5} />
              <PrimaryModuleSkeleton label="Signals momentum ranking" rowCount={5} />
              <PrimaryModuleSkeleton label="Signals technical table" rowCount={5} />
              <PrimaryModuleSkeleton label="Signals watchlist panel" rowCount={5} />
            </>
          ) : shouldRenderBlockingFeedback ? (
            <PrimaryModuleStateFeedback
              moduleState={moduleState}
              onRetryModuleLoad={retryModuleLoad}
            />
          ) : (
            <>
              <article className="signals-module-card primary-module-card">
                <h3>Trend regime summary</h3>
                <p className="signals-module-health" data-lifecycle-state={routeState.trendRegimeHealth.lifecycleState}>
                  Contract state: {routeState.trendRegimeHealth.lifecycleState}
                </p>
                <table className="route-metric-table">
                  <thead>
                    <tr>
                      <th scope="col">Sleeve</th>
                      <th scope="col">Regime</th>
                      <th scope="col">Posture</th>
                    </tr>
                  </thead>
                  <tbody>
                    {routeState.trendRegimeSummary.map((row) => (
                      <tr key={row.sleeve}>
                        <td>{row.sleeve}</td>
                        <td>{row.regime}</td>
                        <td>{row.posture}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <StoryContractBlock
                  what="Growth leadership remains in uptrend while cyclicals remain range-bound."
                  why="Momentum breadth supports selective adds, not broad risk-on expansion."
                  action="Action state: keep tactical review secondary to home/risk context."
                  evidence="Trend regime summary from market-prices + derived-signals contracts."
                />
              </article>

              <article className="signals-module-card primary-module-card">
                <h3>Momentum ranking</h3>
                <p className="signals-module-health" data-lifecycle-state={routeState.momentumHealth.lifecycleState}>
                  Contract state: {routeState.momentumHealth.lifecycleState}
                </p>
                <ol className="signals-ranked-list">
                  {routeState.momentumRanking.map((candidate) => (
                    <li key={candidate.ticker}>
                      <p className="signals-ranked-list__row">
                        <span>{candidate.ticker}</span>
                        <span className="numeric-value">{candidate.momentumScore}</span>
                      </p>
                      <p className="signals-ranked-list__meta">{candidate.trend}</p>
                      <p className="signals-ranked-list__meta">{candidate.setup}</p>
                    </li>
                  ))}
                </ol>
                <StoryContractBlock
                  what={`${topMomentumTickers} remain the top-ranked momentum candidates.`}
                  why="Score alignment confirms trend strength but does not override risk posture."
                  action="Action state: review in rank order before promoting add/buy."
                  evidence="Momentum ranking is now derived from live ledger-backed holdings."
                />
              </article>

              <article className="signals-module-card primary-module-card">
                <h3>Technical signals table</h3>
                <p
                  className="signals-module-health"
                  data-lifecycle-state={routeState.technicalSignalsHealth.lifecycleState}
                >
                  Contract state: {routeState.technicalSignalsHealth.lifecycleState}
                </p>
                {!routeState.technicalSignalsGate.enabled ? (
                  <p className="signals-module-unavailable-copy">
                    Module unavailable: {routeState.technicalSignalsGate.reason}
                  </p>
                ) : (
                  <table className="route-metric-table">
                    <thead>
                      <tr>
                        <th scope="col">Ticker</th>
                        <th scope="col">Regime</th>
                        <th scope="col">ATR</th>
                        <th scope="col">Trigger</th>
                        <th scope="col">Action state</th>
                      </tr>
                    </thead>
                    <tbody>
                      {routeState.technicalSignalRows.map((row) => (
                        <tr key={row.ticker}>
                          <td>{row.ticker}</td>
                          <td>{row.regime}</td>
                          <td>{row.atr}</td>
                          <td>{row.trigger}</td>
                          <td>{row.decisionState}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <StoryContractBlock
                  what="Technical signals are gated by explicit source contracts and feature controls."
                  why="Advanced decision states require both signal + fundamentals contracts."
                  action="Action state: wait unless advanced decision gate is enabled."
                  evidence={`Gate: ${routeState.technicalSignalsGate.reason}`}
                />
              </article>

              <article className="signals-module-card primary-module-card">
                <h3>Watchlist panel</h3>
                <p className="signals-module-health" data-lifecycle-state={routeState.watchlistHealth.lifecycleState}>
                  Contract state: {routeState.watchlistHealth.lifecycleState}
                </p>
                {!routeState.watchlistFundamentalsGate.enabled ? (
                  <p className="signals-module-unavailable-copy">
                    Fundamentals overlay unavailable: {routeState.watchlistFundamentalsGate.reason}
                  </p>
                ) : (
                  <ul className="signals-watchlist">
                    {routeState.watchlistCandidates.map((candidate) => (
                      <li key={candidate.ticker}>
                        <strong>{candidate.ticker}</strong>
                        <p>{candidate.note}</p>
                        <p className="signals-watchlist__valuation">{candidate.valuation}</p>
                      </li>
                    ))}
                  </ul>
                )}
                <StoryContractBlock
                  what="Watchlist names retain directional setup but contract confidence varies."
                  why="Fundamentals freshness is delayed, so conviction stays capped."
                  action="Action state: keep in watchlist until fundamentals gate and freshness improve."
                  evidence={routeState.watchlistHealth.message}
                />
              </article>
            </>
          )}
        </div>
        {shouldRenderSuccessFeedback ? (
          <PrimaryModuleStateFeedback moduleState={moduleState} />
        ) : null}
      </section>

      <WorkspaceStateBanner
        state={isPrimaryModuleLoading ? "loading" : "unavailable"}
        hierarchy="standard"
        message={
          isPrimaryModuleLoading
            ? "Signals route loading skeletons preserve first-viewport layout while contracts resolve."
            : routeState.routeMessage
        }
      />

      <section className="panel workspace-panel workspace-panel--standard">
        <h3>Technical and fundamentals availability baseline</h3>
        <table className="route-metric-table">
          <thead>
            <tr>
              <th scope="col">Metric</th>
              <th scope="col">Availability</th>
              <th scope="col">Reason</th>
            </tr>
          </thead>
          <tbody>
            {routeState.researchMetricAvailability.map((metric) => (
              <tr key={metric.metricId}>
                <td>{metric.label}</td>
                <td data-availability={metric.availability}>{metric.availability}</td>
                <td>{metric.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="availability-cue-line">
          Fallback reason-code copy: signal contract not connected.
        </p>
      </section>

      <section className="panel workspace-panel workspace-panel--standard">
        <h3>YFinance extraction adapters (confirmed available)</h3>
        <table className="route-metric-table">
          <thead>
            <tr>
              <th scope="col">Metric</th>
              <th scope="col">Value</th>
              <th scope="col">Availability</th>
              <th scope="col">Source path</th>
              <th scope="col">Availability cue</th>
            </tr>
          </thead>
          <tbody>
            {routeState.yfinanceAdapterRows.map((adapterRow) => (
              <tr key={adapterRow.metricId}>
                <td>{adapterRow.label}</td>
                <td className="numeric-value">{formatAdapterValue(adapterRow)}</td>
                <td data-availability={adapterRow.availability}>{adapterRow.availability}</td>
                <td>{adapterRow.sourceField}</td>
                <td>{resolveAvailabilityCue(adapterRow.availability)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel workspace-panel workspace-panel--standard">
        <h3>Signals source contracts</h3>
        <table className="route-metric-table">
          <thead>
            <tr>
              <th scope="col">Category</th>
              <th scope="col">source_id</th>
              <th scope="col">as_of</th>
              <th scope="col">freshness_state</th>
              <th scope="col">confidence_state</th>
            </tr>
          </thead>
          <tbody>
            {routeState.sourceContractRows.map((contract) => (
              <tr key={contract.category}>
                <td>{contract.category}</td>
                <td>{contract.source_id}</td>
                <td>{contract.as_of}</td>
                <td>{contract.freshness_state}</td>
                <td>{contract.confidence_state}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="signals-contract-evidence-line">
          {routeState.sourceContractEvidenceLine}
        </p>
        <p className="availability-cue-line">Availability cue: direct source extraction</p>
      </section>

      <details className="panel disclosure-panel">
        <summary>Advanced tactical disclosure</summary>
        <p>
          Tactical overlays remain secondary and do not replace executive route
          interpretation.
        </p>
        <p>
          Expand this section for setup evidence before promoting any candidate from
          watchlist to add/buy review.
        </p>
      </details>
    </CompactDashboardShell>
  );
}
