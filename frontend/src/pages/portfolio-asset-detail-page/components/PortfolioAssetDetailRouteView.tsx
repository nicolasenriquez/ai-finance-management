import { useState } from "react";

import { CompactDashboardShell } from "../../../components/shell/CompactDashboardShell";
import { PrimaryModuleSkeleton } from "../../../components/skeletons/PrimaryModuleSkeleton";
import { StoryContractBlock } from "../../../components/storytelling/StoryContractBlock";
import { PrimaryModuleStateFeedback } from "../../../components/workspace-layout/PrimaryModuleStateFeedback";
import { WorkspaceStateBanner } from "../../../components/workspace-layout/WorkspaceStateBanner";
import { useRoutePrimaryModuleStateController } from "../../../features/portfolio-workspace/route-module-state";
import type { PortfolioAssetDetailRouteState } from "../hooks/usePortfolioAssetDetailRouteState";

type PortfolioAssetDetailRouteViewProps = {
  routeState: PortfolioAssetDetailRouteState;
};

export function PortfolioAssetDetailRouteView({
  routeState,
}: PortfolioAssetDetailRouteViewProps) {
  const [isCoreLotPivotOpen, setIsCoreLotPivotOpen] = useState(false);
  const {
    moduleState,
    isPrimaryModuleLoading,
    shouldRenderBlockingFeedback,
    retryModuleLoad,
  } = useRoutePrimaryModuleStateController();
  const shouldRenderSuccessFeedback = moduleState === "success";
  const shouldRenderLoadingSkeleton =
    isPrimaryModuleLoading || routeState.status === "loading";
  const shouldRenderBlockingRouteFeedback =
    shouldRenderBlockingFeedback ||
    routeState.status === "error" ||
    routeState.status === "empty";
  const routeModuleState =
    routeState.status === "error"
      ? "error"
      : routeState.status === "empty"
        ? "empty"
        : moduleState;

  return (
    <CompactDashboardShell
      title={`Asset Detail · ${routeState.ticker}`}
      subtitle="Ticker-level deep dive route with isolated price-action and position context."
      assetDetailHref={`/portfolio/asset-detail/${routeState.ticker}`}
    >
      <section className="panel workspace-panel workspace-panel--hero">
        <p className="route-kicker">Asset detail · Deep dive</p>
        <h2 className="route-heading">{routeState.ticker} deep dive</h2>
        <p className="route-subheading">
          Price action, position context, and benchmark-relative behavior are isolated
          to this route only.
        </p>

        <div className="asset-detail-first-viewport-grid">
          {shouldRenderLoadingSkeleton ? (
            <>
              <PrimaryModuleSkeleton label="Asset hero" rowCount={5} />
              <PrimaryModuleSkeleton label="Asset price action" rowCount={5} />
              <PrimaryModuleSkeleton label="Asset price volume combo" rowCount={5} />
            </>
          ) : shouldRenderBlockingRouteFeedback || routeState.status !== "ready" ? (
            <PrimaryModuleStateFeedback
              moduleState={routeModuleState}
              onRetryModuleLoad={routeState.reload ?? retryModuleLoad}
            />
          ) : (
            <>
              <article className="asset-module-card primary-module-card">
                <h3>Asset hero</h3>
                <p className="asset-module-health" data-lifecycle-state={routeState.heroHealth.lifecycleState}>
                  Contract state: {routeState.heroHealth.lifecycleState}
                </p>
                <ul className="asset-hero-list">
                  <li>
                    <span>Symbol</span>
                    <strong>{routeState.ticker}</strong>
                  </li>
                  <li>
                    <span>Current position</span>
                    <strong>{routeState.assetWeight}</strong>
                  </li>
                  <li>
                    <span>Market value</span>
                    <strong>{routeState.marketValue}</strong>
                  </li>
                  <li>
                    <span>Open lots</span>
                    <strong>{routeState.openLotCount}</strong>
                  </li>
                  <li>
                    <span>Action state</span>
                    <strong>{routeState.heroDecisionState}</strong>
                  </li>
                </ul>
                <StoryContractBlock
                  what={`${routeState.ticker} remains a core position in the live ledger with ${routeState.openLotCount} open lots.`}
                  why="Trend quality is anchored to live health synthesis instead of hardcoded examples."
                  action={`Action state: ${routeState.heroDecisionState}`}
                  evidence={routeState.heroHealth.message}
                />
              </article>

              <article className="asset-module-card primary-module-card">
                <h3>Price action</h3>
                <p className="asset-module-health" data-lifecycle-state={routeState.priceActionHealth.lifecycleState}>
                  Contract state: {routeState.priceActionHealth.lifecycleState}
                </p>
                <p className="asset-module-kicker">Candlestick-only module</p>
                <div className="asset-candlestick-grid" role="img" aria-label={`${routeState.ticker} candlestick sample`}>
                  {routeState.priceBars.map((bar) => (
                    <div key={bar.day} className="asset-candlestick-grid__bar">
                      <p>{bar.day}</p>
                      <p className="numeric-value">{bar.open}</p>
                      <p className="numeric-value">{bar.high}</p>
                      <p className="numeric-value">{bar.low}</p>
                      <p className="numeric-value">{bar.close}</p>
                    </div>
                  ))}
                </div>
                <StoryContractBlock
                  what={`${routeState.ticker} shows live time-series movement across the latest sessions.`}
                  why="Momentum is now tied to the ledger-backed asset route instead of a demo symbol."
                  action="Action state: keep tactical entries constrained to pullback zones."
                  evidence="Time-series bars are derived from the live instrument-scoped portfolio endpoint."
                />
              </article>

              <article className="asset-module-card primary-module-card">
                <h3>Price-volume combo</h3>
                <ul className="asset-price-volume-list">
                  {routeState.priceVolumeCombo.map((row) => (
                    <li key={row.label}>
                      <span>{row.label}</span>
                      <span className="numeric-value">{row.value}</span>
                      <span>{row.context}</span>
                    </li>
                  ))}
                </ul>
                <StoryContractBlock
                  what="Market value, lot count, and health score are now surfaced from live portfolio data."
                  why="The combo module stays tied to ledger-backed position context."
                  action="Action state: wait for stronger confirmation before adding."
                  evidence="Combo rows are derived from the current portfolio and asset health resources."
                />
              </article>
            </>
          )}
        </div>
        {shouldRenderSuccessFeedback ? (
          <PrimaryModuleStateFeedback moduleState={moduleState} />
        ) : null}
      </section>

      <section className="asset-detail-secondary-grid">
        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Position detail</h3>
          <details className="disclosure-panel asset-position-disclosure">
            <summary>Position detail pivot</summary>
            <button
              aria-expanded={isCoreLotPivotOpen}
              className="hierarchy-pivot-toggle"
              onClick={() => setIsCoreLotPivotOpen((previous) => !previous)}
              type="button"
            >
              {isCoreLotPivotOpen
                ? "Hide core lots"
                : `Show core lots (${routeState.positionPivotGroups[0]?.rows.length ?? 0} positions)`}
            </button>
            {isCoreLotPivotOpen ? (
              <table className="route-metric-table hierarchy-pivot-table" aria-label="Asset position hierarchy pivot">
                <thead>
                  <tr>
                    <th scope="col">Position</th>
                    <th scope="col">Weight</th>
                    <th scope="col">Unrealized</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(routeState.positionPivotGroups[0]?.rows ?? []).map((row) => (
                    <tr key={row.id}>
                      <td>{row.label}</td>
                      <td className="numeric-value">{row.weight}</td>
                      <td className="numeric-value">{row.unrealized}</td>
                      <td>{row.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </details>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Benchmark-relative chart</h3>
          <p className="asset-module-health" data-lifecycle-state={routeState.benchmarkHealth.lifecycleState}>
            Contract state: {routeState.benchmarkHealth.lifecycleState}
          </p>
          <ul className="asset-benchmark-list" role="img" aria-label={`${routeState.ticker} benchmark-relative chart`}>
            {routeState.benchmarkRelativeChart.map((point) => (
              <li key={point.window}>
                <span>{point.window}</span>
                <span>{point.asset}</span>
                <span>{point.benchmark}</span>
                <strong>{point.spread}</strong>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Asset risk metrics</h3>
          <p className="asset-module-health" data-lifecycle-state={routeState.riskMetricHealth.lifecycleState}>
            Contract state: {routeState.riskMetricHealth.lifecycleState}
          </p>
          <table className="route-metric-table">
            <thead>
              <tr>
                <th scope="col">Metric</th>
                <th scope="col">Value</th>
                <th scope="col">Interpretation</th>
              </tr>
            </thead>
            <tbody>
              {routeState.assetRiskMetrics.map((metric) => (
                <tr key={metric.metric}>
                  <td>{metric.metric}</td>
                  <td>{metric.value}</td>
                  <td>{metric.interpretation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel workspace-panel workspace-panel--standard">
          <h3 className="route-heading">Narrative notes</h3>
          <ul className="asset-narrative-list">
            {routeState.narrativeNotes.map((note) => (
              <li key={note.title}>
                <strong>{note.title}</strong>
                <p>{note.detail}</p>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="panel workspace-panel workspace-panel--standard">
        <h3 className="route-heading">Asset source contracts</h3>
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
        <p className="asset-contract-evidence-line">
          {routeState.sourceContractEvidenceLine}
        </p>
        <p className="availability-cue-line">Availability cue: direct source extraction</p>
      </section>

      <WorkspaceStateBanner
        state={
          shouldRenderLoadingSkeleton
            ? "loading"
            : routeState.status === "error"
              ? "error"
              : routeState.status === "empty"
                ? "empty"
                : "ready"
        }
        hierarchy="standard"
        message={
          shouldRenderLoadingSkeleton
            ? "Asset detail loading skeletons preserve first-viewport structure."
            : routeState.routeMessage
        }
      />
    </CompactDashboardShell>
  );
}
