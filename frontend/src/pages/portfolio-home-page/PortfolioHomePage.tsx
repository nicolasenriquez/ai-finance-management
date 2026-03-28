import { Link, useSearchParams } from "react-router-dom";

import { PortfolioTrendChart } from "../../components/charts/PortfolioTrendChart";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { buildHomeMetricCards } from "../../features/portfolio-workspace/overview";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import { usePortfolioTimeSeriesQuery } from "../../features/portfolio-workspace/hooks";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"));
}

export function PortfolioHomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const summaryQuery = usePortfolioSummaryQuery();
  const timeSeriesQuery = usePortfolioTimeSeriesQuery(selectedPeriod);

  const isLoading = summaryQuery.isLoading || timeSeriesQuery.isLoading;
  const isError = summaryQuery.isError || timeSeriesQuery.isError;
  const isSuccess = summaryQuery.isSuccess && timeSeriesQuery.isSuccess;
  const isEmpty =
    isSuccess &&
    (summaryQuery.data.rows.length === 0 || timeSeriesQuery.data.points.length === 0);

  const errorCopy = resolveWorkspaceError(
    summaryQuery.error || timeSeriesQuery.error,
    "Home analytics unavailable",
    "Home analytics could not be loaded from persisted workspace data.",
  );

  function handlePeriodChange(nextPeriod: "30D" | "90D" | "252D" | "MAX"): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("period", nextPeriod);
      return next;
    });
  }

  async function retryHomeAnalytics(): Promise<void> {
    await Promise.all([summaryQuery.refetch(), timeSeriesQuery.refetch()]);
  }

  const metricCards = isSuccess
    ? buildHomeMetricCards(summaryQuery.data.rows, timeSeriesQuery.data.points)
    : [];

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Workspace home"
      title="Portfolio command home"
      description="High-signal portfolio context with explicit freshness, scope, and provenance."
      actions={
        <>
          <PortfolioChartPeriodControl
            value={selectedPeriod}
            onChange={handlePeriodChange}
          />
          <Link className="button-secondary" to="/portfolio">
            Open grouped summary
          </Link>
        </>
      }
      freshnessTimestamp={summaryQuery.data?.as_of_ledger_at}
      scopeLabel="Ledger truth + persisted market snapshots"
      provenanceLabel={
        summaryQuery.data?.pricing_snapshot_key || "Persisted portfolio analytics APIs"
      }
      periodLabel={selectedPeriod}
      frequencyLabel={timeSeriesQuery.data?.frequency}
      timezoneLabel={timeSeriesQuery.data?.timezone}
    >
      {isLoading ? <LoadingTableSkeleton rows={5} /> : null}

      {isError ? (
        <ErrorBanner
          title={errorCopy.title}
          message={errorCopy.message}
          variant={errorCopy.variant}
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

      {isSuccess ? (
        isEmpty ? (
          <EmptyState
            title="Home view has no portfolio context yet"
            message="The workspace APIs returned no summary rows or trend points for the selected period."
          />
        ) : (
          <>
            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Portfolio KPIs</h2>
                <p className="panel__subtitle">
                  Aggregate valuation, unrealized drift, and period movement.
                </p>
              </header>
              <div className="panel__body">
                <div className="overview-grid">
                  {metricCards.map((metric) => (
                    <article className="overview-card" key={metric.label}>
                      <span className="overview-card__label">{metric.label}</span>
                      <strong className={`overview-card__value tone-${metric.tone}`}>
                        {metric.value}
                      </strong>
                      <p className="overview-card__copy">{metric.hint}</p>
                    </article>
                  ))}
                </div>
              </div>
            </section>

            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Trend preview</h2>
                <p className="panel__subtitle">
                  Latest points from portfolio time-series for rapid signal checks.
                </p>
              </header>
              <div className="panel__body">
                <PortfolioTrendChart points={timeSeriesQuery.data.points} />
              </div>
            </section>

            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Drill-down routes</h2>
                <p className="panel__subtitle">
                  Deterministic entry points into analytics, risk, and transactions views.
                </p>
              </header>
              <div className="panel__body">
                <div className="drilldown-grid">
                  <Link
                    className="drilldown-link"
                    to={`/portfolio/analytics?period=${selectedPeriod}`}
                  >
                    <span className="drilldown-link__label">Analytics route</span>
                    <span className="drilldown-link__copy">
                      Open performance and contribution charts for {selectedPeriod}.
                    </span>
                  </Link>
                  <Link
                    className="drilldown-link"
                    to={`/portfolio/risk?period=${selectedPeriod}`}
                  >
                    <span className="drilldown-link__label">Risk route</span>
                    <span className="drilldown-link__copy">
                      Inspect estimator cards and metadata for {selectedPeriod}.
                    </span>
                  </Link>
                  <Link className="drilldown-link" to="/portfolio/transactions">
                    <span className="drilldown-link__label">Transactions route</span>
                    <span className="drilldown-link__copy">
                      Review ledger-history events without diagnostics scope.
                    </span>
                  </Link>
                </div>
              </div>
            </section>
          </>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
