import { Link, useSearchParams } from "react-router-dom";

import { PortfolioContributionChart } from "../../components/charts/PortfolioContributionChart";
import { PortfolioTrendChart } from "../../components/charts/PortfolioTrendChart";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { formatUsdMoney } from "../../core/lib/formatters";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import {
  usePortfolioContributionQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";
import { topContributionRows } from "../../features/portfolio-workspace/overview";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"));
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

  function handlePeriodChange(nextPeriod: "30D" | "90D" | "252D" | "MAX"): void {
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

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Analytics route"
      title="Performance and contribution analytics"
      description="Route-level analytics payloads with controlled period selection and explicit fallback behavior."
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
            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Portfolio trend dataset</h2>
                <p className="panel__subtitle">
                  Recharts performance view generated directly from time-series payload.
                </p>
              </header>
              <div className="panel__body">
                <PortfolioTrendChart points={timeSeriesQuery.data.points} />
              </div>
            </section>

            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Contribution leaders</h2>
                <p className="panel__subtitle">
                  Top symbols by absolute contribution in selected period.
                </p>
              </header>
              <div className="panel__body">
                <PortfolioContributionChart rows={contributionRows} />
                <ul className="trend-list">
                  {contributionRows.map((row) => (
                    <li className="trend-list__row" key={row.instrument_symbol}>
                      <span className="trend-list__date">{row.instrument_symbol}</span>
                      <span className="trend-list__value">
                        {formatUsdMoney(row.contribution_pnl_usd)}
                      </span>
                      <span className="trend-list__value">{row.contribution_pct}%</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          </>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
