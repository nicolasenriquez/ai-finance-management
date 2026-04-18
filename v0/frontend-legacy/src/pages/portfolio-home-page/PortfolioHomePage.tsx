import { Link, useSearchParams } from "react-router-dom";
import { useMemo, useState } from "react";

import { PortfolioPeriodChangeWaterfall } from "../../components/charts/AnalystVisualModules";
import { PortfolioTrendChart } from "../../components/charts/PortfolioTrendChart";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { MetricExplainabilityPopover } from "../../components/metric-explainability/MetricExplainabilityPopover";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { WorkspacePrimaryJobPanel } from "../../components/workspace-layout/WorkspacePrimaryJobPanel";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import { PortfolioHierarchyTable } from "../../features/portfolio-hierarchy/PortfolioHierarchyTable";
import type {
  PortfolioChartPeriod,
  PortfolioHealthProfilePosture,
  PortfolioHierarchyGroupBy,
} from "../../core/api/schemas";
import { formatPricingSnapshotProvenanceLabel } from "../../core/lib/provenance";
import { formatDateTimeLabel } from "../../core/lib/dates";
import { formatUsdMoney } from "../../core/lib/formatters";
import { buildHomeMetricCards } from "../../features/portfolio-workspace/overview";
import { getCoreTenEntriesForRoute } from "../../features/portfolio-workspace/core-ten-catalog";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import {
  usePortfolioCommandCenterQuery,
  usePortfolioHealthSynthesisQuery,
  usePortfolioHierarchyQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"));
}

type DrilldownRouteCard = {
  label: string;
  to: string;
  useCase: string;
  outcome: string;
  routeTag: string;
};

export function PortfolioHomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [hierarchyGroupBy, setHierarchyGroupBy] =
    useState<PortfolioHierarchyGroupBy>("sector");
  const [healthProfilePosture, setHealthProfilePosture] =
    useState<PortfolioHealthProfilePosture>("balanced");

  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const summaryQuery = usePortfolioSummaryQuery();
  const timeSeriesQuery = usePortfolioTimeSeriesQuery(selectedPeriod);
  const hierarchyQuery = usePortfolioHierarchyQuery(hierarchyGroupBy);
  const healthQuery = usePortfolioHealthSynthesisQuery(selectedPeriod, {
    scope: "portfolio",
    profilePosture: healthProfilePosture,
  });
  const commandCenterQuery = usePortfolioCommandCenterQuery();

  const isCoreLoading =
    summaryQuery.isLoading ||
    timeSeriesQuery.isLoading ||
    hierarchyQuery.isLoading;
  const isCoreError =
    summaryQuery.isError ||
    timeSeriesQuery.isError ||
    hierarchyQuery.isError;
  const isCoreSuccess =
    summaryQuery.isSuccess &&
    timeSeriesQuery.isSuccess &&
    hierarchyQuery.isSuccess;
  const isCoreEmpty =
    isCoreSuccess &&
    (
      summaryQuery.data.rows.length === 0 ||
      timeSeriesQuery.data.points.length === 0 ||
      hierarchyQuery.data.groups.length === 0
    );

  const coreErrorCopy = resolveWorkspaceError(
    summaryQuery.error ||
      timeSeriesQuery.error ||
      hierarchyQuery.error,
    "Home analytics unavailable",
    "Home analytics could not be loaded from persisted workspace data.",
  );

  function handlePeriodChange(nextPeriod: PortfolioChartPeriod): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("period", nextPeriod);
      return next;
    });
  }

  async function retryHomeAnalytics(): Promise<void> {
    await Promise.all([
      summaryQuery.refetch(),
      timeSeriesQuery.refetch(),
      hierarchyQuery.refetch(),
    ]);
  }

  const metricCards = isCoreSuccess
    ? buildHomeMetricCards(summaryQuery.data.rows, timeSeriesQuery.data.points)
    : [];
  const commandCenterAsOfLabel = commandCenterQuery.isSuccess
    ? formatDateTimeLabel(commandCenterQuery.data.as_of_ledger_at)
    : "n/a";
  const whatChangedEntries = commandCenterQuery.isSuccess
    ? commandCenterQuery.data.insights.slice(0, 5).map((insight) => {
        const insightText = `${insight.title} ${insight.message}`.toLowerCase();
        const destination =
          insightText.includes("volatility") || insight.severity === "elevated_risk"
            ? `/portfolio/risk?period=${selectedPeriod}`
            : insightText.includes("concentr")
              ? `/portfolio/holdings?period=${selectedPeriod}`
              : insightText.includes("benchmark") || insightText.includes("return")
                ? `/portfolio/performance?period=${selectedPeriod}`
                : `/portfolio/rebalancing?period=${selectedPeriod}`;
        return {
          id: insight.insight_id,
          headline: insight.title,
          message: insight.message,
          destination,
          severity: insight.severity,
        };
      })
    : [];
  const homeCoreTenMetrics = getCoreTenEntriesForRoute("home");
  const dividendNetUsd = isCoreSuccess
    ? summaryQuery.data.rows.reduce((accumulator, row) => {
        return accumulator + Number(row.dividend_net_usd);
      }, 0)
    : 0;
  const homePrimaryKpiValues = useMemo<Record<string, string>>(() => {
    if (!isCoreSuccess) {
      return {} as Record<string, string>;
    }
    const rows = summaryQuery.data.rows;
    const marketValueUsd = rows.reduce((accumulator, row) => {
      return accumulator + Number(row.market_value_usd || "0");
    }, 0);
    const unrealizedGainUsd = rows.reduce((accumulator, row) => {
      return accumulator + Number(row.unrealized_gain_usd || "0");
    }, 0);
    const openCostBasisUsd = rows.reduce((accumulator, row) => {
      return accumulator + Number(row.open_cost_basis_usd || "0");
    }, 0);
    const unrealizedGainPct =
      openCostBasisUsd > 0 ? (unrealizedGainUsd / openCostBasisUsd) * 100 : 0;
    const realizedGainUsd = rows.reduce((accumulator, row) => {
      return accumulator + Number(row.realized_gain_usd || "0");
    }, 0);

    return {
      market_value_usd: formatUsdMoney(marketValueUsd.toFixed(2)),
      unrealized_gain_pct: `${unrealizedGainPct.toFixed(2)}%`,
      realized_gain_usd: formatUsdMoney(realizedGainUsd.toFixed(2)),
      dividend_net_usd: formatUsdMoney(dividendNetUsd.toFixed(2)),
    };
  }, [dividendNetUsd, isCoreSuccess, summaryQuery.data?.rows]);
  const drilldownCards: DrilldownRouteCard[] = [
    {
      label: "Performance lens",
      to: `/portfolio/performance?period=${selectedPeriod}`,
      routeTag: "Attribution",
      useCase: "When you need to identify concentration and contribution drivers.",
      outcome: "Trend + contribution diagnostics for period interpretation.",
    },
    {
      label: "Risk interpretation route",
      to: `/portfolio/risk?period=${selectedPeriod}`,
      routeTag: "Risk",
      useCase: "When drawdown, volatility, or benchmark sensitivity need validation.",
      outcome: "Estimator-led risk context with methodology metadata.",
    },
    {
      label: "Rebalancing lens",
      to: `/portfolio/rebalancing?period=${selectedPeriod}`,
      routeTag: "Rebalancing",
      useCase: "When you need scenario comparison, frontier context, and ML diagnostics.",
      outcome: "Frontier, scenario comparison, forecast intervals, and governance context.",
    },
    {
      label: "Transactions route",
      to: "/portfolio/transactions",
      routeTag: "Ledger",
      useCase: "When you need event-level ledger traceability.",
      outcome: "Deterministic transaction history without estimator overlays.",
    },
  ];

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Overview morning briefing"
      title="Executive morning briefing"
      description="One dominant briefing job with hero insight, bounded supporting modules, and deterministic drill-down routing."
      actions={
        <>
          <PortfolioChartPeriodControl
            value={selectedPeriod}
            onChange={handlePeriodChange}
          />
          <Link className="button-secondary" to="/portfolio">
            Open holdings ledger
          </Link>
        </>
      }
      freshnessTimestamp={summaryQuery.data?.as_of_ledger_at}
      scopeLabel="Ledger truth + persisted market snapshots"
      provenanceLabel={
        summaryQuery.data?.pricing_snapshot_key
          ? formatPricingSnapshotProvenanceLabel(summaryQuery.data.pricing_snapshot_key)
          : "Persisted portfolio analytics APIs"
      }
      provenanceTooltip={summaryQuery.data?.pricing_snapshot_key || undefined}
      periodLabel={selectedPeriod}
      frequencyLabel={timeSeriesQuery.data?.frequency}
      timezoneLabel={timeSeriesQuery.data?.timezone}
    >
      <WorkspacePrimaryJobPanel
        routeLabel="Overview/Home"
        jobTitle="Portfolio operating posture"
        jobDescription="Prioritize a concise operating snapshot before deeper diagnostics: valuation posture, realized outcomes, and income contribution."
        decisionTags={["allocation_review", "income_monitoring", "goal_progress"]}
        coreTenMetrics={homeCoreTenMetrics}
        metricValuesById={homePrimaryKpiValues}
        questionKey="portfolio-operating-posture"
        widgetId="home-primary-job"
        viewportRole="dominant-job"
        supplementary={
          <div className="chart-summary-grid">
            <article className="chart-summary-card">
              <span className="chart-summary-card__label">Dividend income context</span>
              <strong className="chart-summary-card__headline">
                ${dividendNetUsd.toFixed(2)}
              </strong>
              <p className="chart-summary-card__copy">
                Net dividend income in current persisted summary scope.
              </p>
            </article>
            <article className="chart-summary-card chart-summary-card--signal">
              <span className="chart-summary-card__label">Goal progress signal</span>
              <strong className="chart-summary-card__headline">
                {metricCards.length > 0 ? "Interpretable" : "Unavailable"}
              </strong>
              <p className="chart-summary-card__copy">
                Core 10 layer is required before advanced diagnostics are consumed.
              </p>
            </article>
          </div>
        }
      />

      <section className="panel">
        <header className="panel__header">
          <h2 className="panel__title">Decision command center</h2>
          <p className="panel__subtitle">
            First-viewport posture with deterministic insight cards and explicit state metadata.
          </p>
        </header>
        <div className="panel__body">
          {commandCenterQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}
          {commandCenterQuery.isError ? (
            <ErrorBanner
              title="Command center unavailable"
              message="Command center metrics could not be loaded from decision-layer APIs."
              variant="warning"
              actions={
                <button
                  className="button-primary"
                  onClick={() => void commandCenterQuery.refetch()}
                  type="button"
                >
                  Retry command center
                </button>
              }
            />
          ) : null}
          {commandCenterQuery.isSuccess && commandCenterQuery.data.state !== "ready" ? (
            <EmptyState
              title="Command center not ready"
              message={commandCenterQuery.data.state_reason_detail}
            />
          ) : null}
          {commandCenterQuery.isSuccess && commandCenterQuery.data.state === "ready" ? (
            <div className="chart-summary-grid">
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Net worth</span>
                <strong className="chart-summary-card__headline">
                  {formatUsdMoney(commandCenterQuery.data.net_worth_usd)}
                </strong>
                <p className="chart-summary-card__copy">As of {commandCenterAsOfLabel}.</p>
              </article>
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Daily P&L</span>
                <strong className="chart-summary-card__headline">
                  {formatUsdMoney(commandCenterQuery.data.daily_pnl_usd)}
                </strong>
                <p className="chart-summary-card__copy">
                  Latest portfolio day-over-day movement.
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--accent">
                <span className="chart-summary-card__label">Top-5 concentration</span>
                <strong className="chart-summary-card__headline">
                  {Number(commandCenterQuery.data.concentration_top5_pct).toFixed(2)}%
                </strong>
                <p className="chart-summary-card__copy">
                  Concentration posture before deeper risk diagnostics.
                </p>
              </article>
            </div>
          ) : null}
        </div>
      </section>

      <section className="panel" id="what-changed-panel">
        <header className="panel__header">
          <h2 className="panel__title">What changed</h2>
          <p className="panel__subtitle">
            Deterministic highlights linked to the relevant decision lens.
          </p>
        </header>
        <div className="panel__body">
          {commandCenterQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}
          {commandCenterQuery.isSuccess && whatChangedEntries.length === 0 ? (
            <EmptyState
              title="No material changes detected"
              message="No insight cards were emitted for the selected period."
            />
          ) : null}
          {whatChangedEntries.length > 0 ? (
            <div className="what-changed-list" role="list" aria-label="What changed list">
              {whatChangedEntries.map((entry) => (
                <article className="what-changed-card" key={entry.id} role="listitem">
                  <div className="what-changed-card__header">
                    <strong>{entry.headline}</strong>
                    <span className={`status-pill status-pill--${entry.severity === "elevated_risk" ? "negative" : entry.severity === "caution" ? "neutral" : "positive"}`}>
                      {entry.severity}
                    </span>
                  </div>
                  <p>{entry.message}</p>
                  <div className="what-changed-card__footer">
                    <span>As of {commandCenterAsOfLabel}</span>
                    <Link to={entry.destination}>Open details</Link>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      {isCoreLoading ? (
        <WorkspaceStateBanner state="loading" />
      ) : isCoreError ? (
        <WorkspaceStateBanner
          state="error"
          message={coreErrorCopy.message}
        />
      ) : isCoreSuccess && isCoreEmpty ? (
        <WorkspaceStateBanner state="unavailable" />
      ) : isCoreSuccess ? (
        <WorkspaceStateBanner state="ready" />
      ) : null}

      {isCoreLoading ? <LoadingTableSkeleton rows={5} /> : null}

      {isCoreError ? (
        <ErrorBanner
          title={coreErrorCopy.title}
          message={coreErrorCopy.message}
          variant={coreErrorCopy.variant}
          actions={
            <button
              className="button-primary"
              onClick={() => void retryHomeAnalytics()}
              type="button"
            >
              Retry request
            </button>
          }
        />
      ) : null}

      {isCoreSuccess ? (
        isCoreEmpty ? (
          <EmptyState
            title="Home view has no portfolio context yet"
            message="The workspace APIs returned no summary rows or trend points for the selected period."
          />
        ) : (
          <>
            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Portfolio health synthesis</h2>
                <p className="panel__subtitle">
                  Core 10 prioritized interpretation layer with profile-aware weighting.
                </p>
              </header>
              <div className="panel__body">
                <div className="transactions-filters">
                  <label className="transactions-filters__field">
                    <span>Health profile</span>
                    <select
                      aria-label="Health profile posture"
                      className="transactions-filters__select"
                      onChange={(event) => {
                        setHealthProfilePosture(
                          event.target.value as PortfolioHealthProfilePosture,
                        );
                      }}
                      value={healthProfilePosture}
                    >
                      <option value="conservative">Conservative</option>
                      <option value="balanced">Balanced</option>
                      <option value="aggressive">Aggressive</option>
                    </select>
                  </label>
                </div>

                {healthQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}
                {healthQuery.isError ? (
                  <ErrorBanner
                    title="Health synthesis unavailable"
                    message="Portfolio health synthesis could not be loaded for the selected profile."
                    variant="warning"
                    actions={
                      <button
                        className="button-primary"
                        onClick={() => void healthQuery.refetch()}
                        type="button"
                      >
                        Retry health synthesis
                      </button>
                    }
                  />
                ) : null}
                {healthQuery.isSuccess ? (
                  <>
                    <div className="chart-summary-grid">
                      <article className="chart-summary-card chart-summary-card--signal">
                        <span className="chart-summary-card__label">Health label</span>
                        <strong className="chart-summary-card__headline">
                          {healthQuery.data.health_label}
                        </strong>
                        <p className="chart-summary-card__copy">
                          Profile posture: {healthQuery.data.profile_posture}.
                        </p>
                      </article>
                      <article className="chart-summary-card chart-summary-card--accent">
                        <span className="chart-summary-card__label">Health score</span>
                        <strong className="chart-summary-card__headline">
                          {healthQuery.data.health_score}/100
                        </strong>
                        <p className="chart-summary-card__copy">
                          Threshold policy {healthQuery.data.threshold_policy_version}.
                        </p>
                      </article>
                      <article className="chart-summary-card">
                        <span className="chart-summary-card__label">KPI priority model</span>
                        <strong className="chart-summary-card__headline">
                          Core 10 first
                        </strong>
                        <p className="chart-summary-card__copy">
                          Advanced metrics remain available for drill-down diagnostics.
                        </p>
                      </article>
                    </div>

                    <table
                      className="quant-lens-table health-pillars-table"
                      aria-label="Health pillar scores"
                    >
                      <thead>
                        <tr className="quant-lens-table__header">
                          <th scope="col">Pillar</th>
                          <th className="quant-lens-table__value" scope="col">
                            Score
                          </th>
                          <th className="quant-lens-table__value" scope="col">
                            Status
                          </th>
                          <th className="quant-lens-table__value" scope="col">
                            Top metric
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {healthQuery.data.pillars.map((pillar) => (
                          <tr className="quant-lens-table__row" key={pillar.pillar_id}>
                            <th className="quant-lens-table__metric" scope="row">
                              {pillar.label}
                            </th>
                            <td className="quant-lens-table__value">{pillar.score}/100</td>
                            <td className="quant-lens-table__value">{pillar.status}</td>
                            <td className="quant-lens-table__value">
                              {pillar.metrics[0]
                                ? `${pillar.metrics[0].label} (${pillar.metrics[0].value_display})`
                                : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    {healthQuery.data.key_drivers.length > 0 ? (
                      <section className="context-banner context-banner--info" aria-live="polite">
                        <h3 className="context-banner__title">Top health drivers</h3>
                        <p className="context-banner__copy">
                          {healthQuery.data.key_drivers
                            .slice(0, 3)
                            .map(
                              (driver) =>
                                `${driver.label}: ${driver.value_display} (${driver.direction})`,
                            )
                            .join(" · ")}
                        </p>
                      </section>
                    ) : null}
                  </>
                ) : null}
              </div>
            </section>

            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Portfolio KPIs</h2>
                <p className="panel__subtitle">
                  Executive P&amp;L snapshot: market value, unrealized/realized context, and period movement.
                </p>
              </header>
              <div className="panel__body">
                <div className="overview-grid">
                  {metricCards.map((metric) => (
                    <article className="overview-card" key={metric.label}>
                      <div className="overview-card__meta">
                        <span className="overview-card__label">{metric.label}</span>
                        <MetricExplainabilityPopover
                          label={metric.label}
                          shortDefinition={metric.explainability.shortDefinition}
                          whyItMatters={metric.explainability.whyItMatters}
                          interpretation={metric.explainability.interpretation}
                          formulaOrBasis={metric.explainability.formulaOrBasis}
                          comparisonContext={metric.explainability.comparisonContext}
                          caveats={metric.explainability.caveats}
                          currentContextNote={metric.explainability.currentContextNote}
                        />
                      </div>
                      <strong className={`overview-card__value tone-${metric.tone}`}>
                        {metric.value}
                      </strong>
                      <p className="overview-card__copy">{metric.hint}</p>
                    </article>
                  ))}
                </div>
              </div>
            </section>

            <WorkspaceChartPanel
              title="Period change waterfall"
              subtitle="Bridge from start value to current value with explicit contribution components."
              shortDescription="Waterfall-style module for period movement decomposition."
              longDescription="Use this bridge to separate valuation drift from realized/dividend components and reconciliation adjustments."
              questionKey="period-change-bridge"
              widgetId="home-period-waterfall"
              priority="advanced"
            >
              <PortfolioPeriodChangeWaterfall
                points={timeSeriesQuery.data.points}
                summaryRows={summaryQuery.data.rows}
              />
            </WorkspaceChartPanel>

            <WorkspaceChartPanel
              title="Trend preview"
              subtitle="Latest points from portfolio time-series with benchmark overlays and spread context."
              shortDescription="Time-trend comparison against rebased benchmark trajectories."
              longDescription="This preview guides drill-down decisions; final report workflows belong to the Quant/Reports route."
              questionKey="trend-versus-benchmark"
              widgetId="home-trend-preview"
              priority="primary"
              hierarchy="hero"
              viewportRole="hero-insight"
            >
              <PortfolioTrendChart
                analysisActions={
                  <Link
                    className="button-secondary chart-action-link"
                    to={`/portfolio/risk?period=${selectedPeriod}`}
                  >
                    Analyze risk route
                  </Link>
                }
                points={timeSeriesQuery.data.points}
              />
            </WorkspaceChartPanel>

            <PortfolioHierarchyTable
              groupBy={hierarchyGroupBy}
              groups={hierarchyQuery.data.groups}
              onGroupByChange={setHierarchyGroupBy}
            />

            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Drill-down routes</h2>
                <p className="panel__subtitle">
                  Deterministic route selection with explicit “when to use” guidance.
                </p>
              </header>
              <div className="panel__body">
                <div className="drilldown-grid">
                  {drilldownCards.map((card) => (
                    <Link className="drilldown-link" key={card.label} to={card.to}>
                      <span className="drilldown-link__eyebrow">{card.routeTag}</span>
                      <span className="drilldown-link__label">{card.label}</span>
                      <span className="drilldown-link__intent">{card.useCase}</span>
                      <span className="drilldown-link__copy">{card.outcome}</span>
                    </Link>
                  ))}
                </div>
              </div>
            </section>
          </>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
