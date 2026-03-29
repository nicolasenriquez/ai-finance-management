import { Link, useSearchParams } from "react-router-dom";

import { PortfolioRiskChart } from "../../components/charts/PortfolioRiskChart";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { AppApiError } from "../../core/api/errors";
import { formatDateTimeLabel } from "../../core/lib/dates";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import {
  mapChartPeriodToRiskWindow,
  usePortfolioRiskEstimatorsQuery,
} from "../../features/portfolio-workspace/hooks";
import { sortRiskMetrics } from "../../features/portfolio-workspace/overview";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"), "252D");
}

function resolveRiskErrorCopy(error: unknown): {
  title: string;
  message: string;
  variant: "error" | "warning";
} {
  if (error instanceof AppApiError && error.detail) {
    const detailLower = error.detail.toLowerCase();
    if (detailLower.includes("unsupported")) {
      return {
        title: "Risk scope unsupported",
        message: error.detail,
        variant: "warning",
      };
    }

    if (detailLower.includes("insufficient")) {
      return {
        title: "Risk data insufficient",
        message: error.detail,
        variant: "warning",
      };
    }
  }

  return resolveWorkspaceError(
    error,
    "Risk workspace unavailable",
    "Risk estimators are unavailable for the selected period scope.",
  );
}

export function PortfolioRiskPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const selectedWindow = mapChartPeriodToRiskWindow(selectedPeriod);
  const riskQuery = usePortfolioRiskEstimatorsQuery(selectedWindow);

  const isLoading = riskQuery.isLoading;
  const isError = riskQuery.isError;
  const isSuccess = riskQuery.isSuccess;
  const isEmpty = isSuccess && riskQuery.data.metrics.length === 0;
  const errorCopy = resolveRiskErrorCopy(riskQuery.error);

  function handlePeriodChange(nextPeriod: "30D" | "90D" | "252D" | "MAX"): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("period", nextPeriod);
      return next;
    });
  }

  const orderedMetrics = isSuccess ? sortRiskMetrics(riskQuery.data.metrics) : [];

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Risk route"
      title="Bounded estimator workspace"
      description="Risk estimators with explicit methodology metadata, unsupported-scope visibility, and risk-context interpretation boundaries."
      actions={
        <>
          <PortfolioChartPeriodControl
            value={selectedPeriod}
            onChange={handlePeriodChange}
          />
          <Link className="button-secondary" to="/portfolio/analytics">
            Open analytics route
          </Link>
        </>
      }
      freshnessTimestamp={riskQuery.data?.as_of_ledger_at}
      scopeLabel="Persisted estimator contract"
      provenanceLabel="Risk endpoint methodology metadata"
      periodLabel={selectedPeriod}
    >
      {isLoading ? <LoadingTableSkeleton rows={4} /> : null}

      {isError ? (
        <ErrorBanner
          title={errorCopy.title}
          message={errorCopy.message}
          variant={errorCopy.variant}
          actions={
            <button
              className="button-primary"
              onClick={() => void riskQuery.refetch()}
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
            title="No risk metrics for selected scope"
            message="Risk estimator payload returned no metrics. Try another period scope or confirm historical coverage."
          />
        ) : (
          <section className="panel">
            <header className="panel__header">
              <h2 className="panel__title">Estimator metrics</h2>
              <p className="panel__subtitle">
                Window: {riskQuery.data.window_days} days, return basis and annualization
                metadata shown per metric.
              </p>
            </header>
            <div className="panel__body">
              <PortfolioRiskChart metrics={orderedMetrics} />
              <div className="lot-metrics">
                {orderedMetrics.map((metric) => (
                  <article className="metric-card" key={metric.estimator_id}>
                    <span className="metric-card__label">{metric.estimator_id}</span>
                    <strong className="metric-card__value">{metric.value}</strong>
                    <p className="metric-hint">
                      window {metric.window_days}d | return {metric.return_basis} |
                      annualization {metric.annualization_basis.kind}=
                      {metric.annualization_basis.value}
                    </p>
                    <p className="metric-hint">
                      as of {formatDateTimeLabel(metric.as_of_timestamp)}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </section>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
