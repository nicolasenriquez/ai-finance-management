import { Link, useSearchParams } from "react-router-dom";

import { PortfolioContributionWaterfall } from "../../components/charts/AnalystVisualModules";
import { PortfolioContributionChart } from "../../components/charts/PortfolioContributionChart";
import { PortfolioTrendChart } from "../../components/charts/PortfolioTrendChart";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { WorkspacePrimaryJobPanel } from "../../components/workspace-layout/WorkspacePrimaryJobPanel";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import type {
  PortfolioChartPeriod,
  PortfolioContributionRow,
} from "../../core/api/schemas";
import { formatUsdMoney } from "../../core/lib/formatters";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import {
  usePortfolioContributionQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";
import { topContributionRows } from "../../features/portfolio-workspace/overview";
import { getCoreTenEntriesForRoute } from "../../features/portfolio-workspace/core-ten-catalog";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"));
}

type ContributionTone = "positive" | "negative" | "neutral";

function resolveContributionTone(value: number): ContributionTone {
  if (value > 0) {
    return "positive";
  }
  if (value < 0) {
    return "negative";
  }
  return "neutral";
}

function formatSignedPercent(value: number): string {
  if (!Number.isFinite(value)) {
    return "0.00%";
  }
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function buildContributionInsight(rows: PortfolioContributionRow[]): {
  rows: Array<{
    instrumentSymbol: string;
    contributionPnlUsd: number;
    netSharePct: number;
    absSharePct: number;
    tone: ContributionTone;
  }>;
  topPositive: string | null;
  topDrag: string | null;
  concentrationPct: string;
} {
  const rankedRows = topContributionRows(rows).map((row) => ({
    instrumentSymbol: row.instrument_symbol,
    contributionPnlUsd: Number(row.contribution_pnl_usd),
  }));
  const totalNetContribution = rankedRows.reduce(
    (accumulator, row) => accumulator + row.contributionPnlUsd,
    0,
  );
  const totalAbsContribution = rankedRows.reduce(
    (accumulator, row) => accumulator + Math.abs(row.contributionPnlUsd),
    0,
  );

  const enrichedRows = rankedRows.map((row) => ({
    ...row,
    netSharePct:
      totalNetContribution === 0
        ? 0
        : (row.contributionPnlUsd / totalNetContribution) * 100,
    absSharePct:
      totalAbsContribution === 0
        ? 0
        : (Math.abs(row.contributionPnlUsd) / totalAbsContribution) * 100,
    tone: resolveContributionTone(row.contributionPnlUsd),
  }));

  const topPositiveRow = enrichedRows.find((row) => row.contributionPnlUsd > 0);
  const topDragRow = enrichedRows.find((row) => row.contributionPnlUsd < 0);
  const concentrationPct = enrichedRows.length > 0
    ? enrichedRows[0].absSharePct.toFixed(2)
    : "0.00";

  return {
    rows: enrichedRows,
    topPositive: topPositiveRow
      ? `${topPositiveRow.instrumentSymbol} ${formatUsdMoney(topPositiveRow.contributionPnlUsd.toFixed(2))}`
      : null,
    topDrag: topDragRow
      ? `${topDragRow.instrumentSymbol} ${formatUsdMoney(topDragRow.contributionPnlUsd.toFixed(2))}`
      : null,
    concentrationPct,
  };
}

export function PortfolioAnalyticsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const timeSeriesQuery = usePortfolioTimeSeriesQuery(selectedPeriod);
  const contributionQuery = usePortfolioContributionQuery(selectedPeriod);

  const isLoading = timeSeriesQuery.isLoading || contributionQuery.isLoading;
  const isError = timeSeriesQuery.isError || contributionQuery.isError;
  const isSuccess = timeSeriesQuery.isSuccess && contributionQuery.isSuccess;
  const isEmpty =
    isSuccess &&
    (timeSeriesQuery.data.points.length === 0 || contributionQuery.data.rows.length === 0);

  const errorCopy = resolveWorkspaceError(
    timeSeriesQuery.error || contributionQuery.error,
    "Analytics workspace unavailable",
    "Analytics charts could not be built from persisted portfolio payloads.",
  );

  function handlePeriodChange(nextPeriod: PortfolioChartPeriod): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("period", nextPeriod);
      return next;
    });
  }

  async function retryAnalytics(): Promise<void> {
    await Promise.all([timeSeriesQuery.refetch(), contributionQuery.refetch()]);
  }

  const contributionRows = isSuccess ? topContributionRows(contributionQuery.data.rows) : [];
  const contributionInsight = isSuccess
    ? buildContributionInsight(contributionQuery.data.rows)
    : null;
  const analyticsCoreTenMetrics = getCoreTenEntriesForRoute("analytics");

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Analytics route"
      title="Performance and contribution analytics"
      description="Route-level analytics payloads with controlled period selection and explicit fallback behavior. Preview metrics are supplemental to risk-context interpretation."
      actions={
        <>
          <PortfolioChartPeriodControl
            value={selectedPeriod}
            onChange={handlePeriodChange}
          />
          <Link className="button-secondary" to="/portfolio/home">
            Back to home
          </Link>
        </>
      }
      freshnessTimestamp={timeSeriesQuery.data?.as_of_ledger_at}
      scopeLabel="Portfolio chart endpoints"
      provenanceLabel="Persisted time-series + contribution APIs"
      periodLabel={selectedPeriod}
      frequencyLabel={timeSeriesQuery.data?.frequency}
      timezoneLabel={timeSeriesQuery.data?.timezone}
    >
      <WorkspacePrimaryJobPanel
        routeLabel="Analytics"
        jobTitle="Attribution concentration interpretation"
        jobDescription="Use one attribution-first viewport to identify concentration drivers before navigating to risk or reporting diagnostics."
        decisionTags={["allocation_review", "risk_posture"]}
        coreTenMetrics={analyticsCoreTenMetrics}
        supplementary={
          <div className="chart-summary-grid">
            <article className="chart-summary-card">
              <span className="chart-summary-card__label">Allocation drift watch</span>
              <strong className="chart-summary-card__headline">
                {contributionInsight ? `${contributionInsight.concentrationPct}%` : "—"}
              </strong>
              <p className="chart-summary-card__copy">
                Top-symbol absolute contribution share for selected period.
              </p>
            </article>
          </div>
        }
      />

      {isLoading ? (
        <WorkspaceStateBanner state="loading" />
      ) : isError ? (
        <WorkspaceStateBanner state="error" message={errorCopy.message} />
      ) : isSuccess && isEmpty ? (
        <WorkspaceStateBanner state="unavailable" />
      ) : isSuccess ? (
        <WorkspaceStateBanner state="ready" />
      ) : null}

      {isLoading ? <LoadingTableSkeleton rows={6} /> : null}

      {isError ? (
        <ErrorBanner
          title={errorCopy.title}
          message={errorCopy.message}
          variant={errorCopy.variant}
          actions={
            <button
              className="button-primary"
              onClick={() => void retryAnalytics()}
              type="button"
            >
              Retry request
            </button>
          }
        />
      ) : null}

      {isSuccess ? (
        isEmpty ? (
          <EmptyState
            title="Analytics route returned no chartable rows"
            message="The selected period has no trend points or contribution rows. Change period or verify persisted history coverage."
          />
        ) : (
          <>
            <WorkspaceChartPanel
              title="Portfolio trend dataset"
              subtitle="Recharts performance view with benchmark overlays sourced from persisted prices."
              shortDescription="Trend context for selected period before attribution deep-dive."
              longDescription="Use this normalized trend view to decide whether performance needs attribution diagnostics or risk interpretation next."
            >
              <PortfolioTrendChart points={timeSeriesQuery.data.points} />
            </WorkspaceChartPanel>

            <WorkspaceChartPanel
              title="Contribution leaders"
              subtitle="Top symbols by absolute contribution to selected-period P&L."
              shortDescription="Diverging bar view with net-share and absolute-share context for attribution clarity."
              longDescription="Use net share to understand directional drag/lift versus period net result, and absolute share to quantify concentration of movers."
            >
              {contributionInsight ? (
                <div className="chart-summary-grid">
                  <article className="chart-summary-card">
                    <span className="chart-summary-card__label">Top positive</span>
                    <strong className="chart-summary-card__headline tone-positive">
                      {contributionInsight.topPositive || "No positive movers"}
                    </strong>
                    <p className="chart-summary-card__copy">
                      Largest positive symbol contribution in selected period.
                    </p>
                  </article>
                  <article className="chart-summary-card chart-summary-card--signal">
                    <span className="chart-summary-card__label">Top drag</span>
                    <strong className="chart-summary-card__headline tone-negative">
                      {contributionInsight.topDrag || "No negative movers"}
                    </strong>
                    <p className="chart-summary-card__copy">
                      Largest negative symbol contribution in selected period.
                    </p>
                  </article>
                  <article className="chart-summary-card chart-summary-card--accent">
                    <span className="chart-summary-card__label">Concentration</span>
                    <strong className="chart-summary-card__headline">
                      {contributionInsight.concentrationPct}%
                    </strong>
                    <p className="chart-summary-card__copy">
                      Share of absolute move explained by the top-ranked symbol.
                    </p>
                  </article>
                </div>
              ) : null}

              <PortfolioContributionChart rows={contributionRows} />

              {contributionInsight ? (
                <div
                  className="contribution-focus__table"
                  role="table"
                  aria-label="Contribution leaders table"
                >
                  <div className="contribution-focus__header" role="row">
                    <span role="columnheader">Symbol</span>
                    <span role="columnheader">Contribution</span>
                    <span role="columnheader">Net share (vs net period)</span>
                    <span role="columnheader">Absolute share</span>
                  </div>
                  {contributionInsight.rows.map((row) => (
                    <div className="contribution-focus__row" key={row.instrumentSymbol} role="row">
                      <span className="contribution-focus__symbol" role="cell">
                        {row.instrumentSymbol}
                      </span>
                      <span className={`contribution-focus__value tone-${row.tone}`} role="cell">
                        {formatUsdMoney(row.contributionPnlUsd.toFixed(2))}
                      </span>
                      <span className={`contribution-focus__value tone-${row.tone}`} role="cell">
                        {formatSignedPercent(row.netSharePct)}
                      </span>
                      <span className="contribution-focus__value" role="cell">
                        {row.absSharePct.toFixed(2)}%
                      </span>
                    </div>
                  ))}
                </div>
              ) : null}
            </WorkspaceChartPanel>

            <WorkspaceChartPanel
              title="Contribution waterfall"
              subtitle="Sequential bridge of top symbol contributions to period impact."
              shortDescription="Waterfall-style module to separate additive positive and negative drivers."
              longDescription="Interpret this as an attribution bridge, not a risk estimator; values are absolute contribution deltas from current period payload."
            >
              <PortfolioContributionWaterfall rows={contributionRows} />
            </WorkspaceChartPanel>
          </>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
