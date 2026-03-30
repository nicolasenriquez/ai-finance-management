import { Link, useSearchParams } from "react-router-dom";

import { PortfolioRiskChart } from "../../components/charts/PortfolioRiskChart";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { MetricExplainabilityPopover } from "../../components/metric-explainability/MetricExplainabilityPopover";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { AppApiError } from "../../core/api/errors";
import type { PortfolioRiskEstimatorMetric } from "../../core/api/schemas";
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

type RiskMetricUnit = "ratio" | "percent" | "unitless";

function resolveRiskMetricUnit(estimatorId: string): RiskMetricUnit {
  const normalizedEstimatorId = estimatorId.toLowerCase();
  if (
    normalizedEstimatorId.includes("volatility") ||
    normalizedEstimatorId.includes("drawdown") ||
    normalizedEstimatorId.includes("downside_deviation") ||
    normalizedEstimatorId.includes("value_at_risk") ||
    normalizedEstimatorId.includes("shortfall")
  ) {
    return "percent";
  }
  if (normalizedEstimatorId.includes("beta")) {
    return "ratio";
  }
  return "unitless";
}

function resolveRiskMetricInterpretation(unit: RiskMetricUnit): string {
  if (unit === "percent") {
    return "Lower percentage values usually indicate lower observed risk magnitude for the selected window.";
  }
  if (unit === "ratio") {
    return "Ratio values near 1 imply market-like sensitivity; higher or lower values indicate divergence from benchmark-like behavior.";
  }
  return "Interpret this value against prior periods and adjacent estimators rather than as an isolated score.";
}

function formatRiskMetricLabel(estimatorId: string): string {
  const normalizedEstimatorId = estimatorId.toLowerCase();
  if (normalizedEstimatorId === "value_at_risk_95") {
    return "VaR (95%)";
  }
  if (normalizedEstimatorId === "expected_shortfall_95") {
    return "Expected Shortfall (95%)";
  }
  if (normalizedEstimatorId === "downside_deviation_annualized") {
    return "Downside Deviation (Annualized)";
  }

  return estimatorId
    .split("_")
    .map((chunk) =>
      chunk.length > 0 ? `${chunk[0].toUpperCase()}${chunk.slice(1).toLowerCase()}` : chunk,
    )
    .join(" ");
}

function formatRiskMetricValue(metric: PortfolioRiskEstimatorMetric): string {
  const value = Number(metric.value);
  if (!Number.isFinite(value)) {
    return metric.value;
  }

  const unit = resolveRiskMetricUnit(metric.estimator_id);
  if (unit === "percent") {
    const percentValue = value * 100;
    const signPrefix = percentValue > 0 ? "+" : "";
    return `${signPrefix}${percentValue.toFixed(2)}%`;
  }

  if (unit === "ratio") {
    return value.toFixed(3);
  }

  return value.toFixed(4);
}

function groupRiskMetricsByUnit(
  metrics: PortfolioRiskEstimatorMetric[],
): Array<{ key: RiskMetricUnit; title: string; metrics: PortfolioRiskEstimatorMetric[] }> {
  const grouped: Record<RiskMetricUnit, PortfolioRiskEstimatorMetric[]> = {
    percent: [],
    ratio: [],
    unitless: [],
  };

  metrics.forEach((metric) => {
    grouped[resolveRiskMetricUnit(metric.estimator_id)].push(metric);
  });

  const orderedGroups: Array<{ key: RiskMetricUnit; title: string; metrics: PortfolioRiskEstimatorMetric[] }> = [
    { key: "percent", title: "Percent-based estimators", metrics: grouped.percent },
    { key: "ratio", title: "Ratio estimators", metrics: grouped.ratio },
    { key: "unitless", title: "Unitless estimators", metrics: grouped.unitless },
  ];

  return orderedGroups.filter((group) => group.metrics.length > 0);
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
  const unitSet = new Set(orderedMetrics.map((metric) => resolveRiskMetricUnit(metric.estimator_id)));
  const hasMixedRiskUnits = unitSet.size > 1;
  const metricGroups = groupRiskMetricsByUnit(orderedMetrics);

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
          <Link className="button-secondary" to="/portfolio/home">
            Back to home
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
          <WorkspaceChartPanel
            title="Estimator metrics"
            subtitle={`Window: ${riskQuery.data.window_days} days, return basis and annualization metadata shown per metric.`}
            shortDescription="Risk estimators rendered with mixed-unit guardrails and one compact metadata ledger."
            longDescription="Charts are split by unit type when needed so comparisons stay valid; row-level ledger keeps formula context without duplicating large cards."
          >
            {hasMixedRiskUnits ? (
              <>
                <section className="context-banner context-banner--info" aria-live="polite">
                  <h3 className="context-banner__title">Mixed-unit guardrail applied</h3>
                  <p className="context-banner__copy">
                    Estimator units are mixed, so charts are split by unit type to prevent invalid one-axis comparisons.
                  </p>
                </section>
                <div className="risk-chart-groups">
                  {metricGroups.map((group) => (
                    <section className="risk-chart-group" key={group.key}>
                      <h3 className="risk-chart-group__title">{group.title}</h3>
                      <PortfolioRiskChart metrics={group.metrics} />
                    </section>
                  ))}
                </div>
              </>
            ) : (
              <PortfolioRiskChart metrics={orderedMetrics} />
            )}

            <div
              aria-label="Risk metric ledger"
              className="risk-metrics-ledger"
              role="table"
            >
              <div className="risk-metrics-ledger__header" role="row">
                <span role="columnheader">Estimator</span>
                <span role="columnheader">Value</span>
                <span role="columnheader">Method</span>
                <span role="columnheader">As of</span>
              </div>
              {orderedMetrics.map((metric) => {
                const metricUnit = resolveRiskMetricUnit(metric.estimator_id);
                return (
                  <div className="risk-metrics-ledger__row" key={metric.estimator_id} role="row">
                    <span className="risk-metrics-ledger__estimator" role="cell">
                      <span className="risk-metrics-ledger__estimator-label">
                        {formatRiskMetricLabel(metric.estimator_id)}
                      </span>
                      <MetricExplainabilityPopover
                        label={formatRiskMetricLabel(metric.estimator_id)}
                        shortDefinition="Risk estimator computed from selected-window return history."
                        whyItMatters="Helps assess whether realized performance is aligned with the risk profile taken."
                        interpretation={resolveRiskMetricInterpretation(metricUnit)}
                        formulaOrBasis={`Estimator ${metric.estimator_id}, return basis ${metric.return_basis}, annualization ${metric.annualization_basis.kind}=${metric.annualization_basis.value}.`}
                        comparisonContext="Compare against the same estimator across periods and against return outcomes."
                        caveats="Estimator stability depends on window length and available history coverage."
                        currentContextNote={`Current value is ${formatRiskMetricValue(metric)} as of ${formatDateTimeLabel(metric.as_of_timestamp)}.`}
                      />
                    </span>
                    <strong className="risk-metrics-ledger__value" role="cell">
                      {formatRiskMetricValue(metric)}
                    </strong>
                    <span className="risk-metrics-ledger__method" role="cell">
                      <span className="risk-method-chips">
                        <span className="risk-method-chip">Window {metric.window_days}D</span>
                        <span className="risk-method-chip">
                          Return {metric.return_basis === "simple" ? "simple daily" : "log daily"}
                        </span>
                        <span className="risk-method-chip">
                          Annualized @{metric.annualization_basis.value} trading days
                        </span>
                      </span>
                    </span>
                    <span className="risk-metrics-ledger__asof" role="cell">
                      as of {formatDateTimeLabel(metric.as_of_timestamp)}
                    </span>
                  </div>
                );
              })}
            </div>
          </WorkspaceChartPanel>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
