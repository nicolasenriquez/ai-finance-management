import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link, useSearchParams } from "react-router-dom";

import { PortfolioRiskChart } from "../../components/charts/PortfolioRiskChart";
import {
  DrawdownTimelineChart,
  ReturnDistributionChart,
  RollingEstimatorsTimelineChart,
} from "../../components/charts/PortfolioRiskEvolutionCharts";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { MetricExplainabilityPopover } from "../../components/metric-explainability/MetricExplainabilityPopover";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { WorkspacePrimaryJobPanel } from "../../components/workspace-layout/WorkspacePrimaryJobPanel";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import { AppApiError } from "../../core/api/errors";
import type {
  PortfolioChartPeriod,
  PortfolioRiskEstimatorMetric,
  PortfolioTimeSeriesPoint,
  PortfolioTimeSeriesScope,
} from "../../core/api/schemas";
import { formatDateTimeLabel } from "../../core/lib/dates";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { fetchPortfolioTimeSeries } from "../../features/portfolio-workspace/api";
import { fetchPortfolioSummary } from "../../features/portfolio-summary/api";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import {
  mapChartPeriodToRiskWindow,
  usePortfolioHealthSynthesisQuery,
  usePortfolioReturnDistributionQuery,
  usePortfolioRiskEstimatorsScopedQuery,
  usePortfolioRiskEvolutionQuery,
} from "../../features/portfolio-workspace/hooks";
import { sortRiskMetrics } from "../../features/portfolio-workspace/overview";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";
import { getCoreTenEntriesForRoute } from "../../features/portfolio-workspace/core-ten-catalog";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"), "252D");
}

function resolveScopeFromSearchParams(
  searchParams: URLSearchParams,
): PortfolioTimeSeriesScope {
  const scope = searchParams.get("scope");
  if (scope === "instrument_symbol") {
    return "instrument_symbol";
  }
  return "portfolio";
}

function resolveInstrumentSymbolFromSearchParams(
  searchParams: URLSearchParams,
): string | null {
  const symbol = searchParams.get("instrument_symbol");
  if (!symbol) {
    return null;
  }
  const normalized = symbol.trim().toUpperCase();
  return normalized.length > 0 ? normalized : null;
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

type CorrelationMatrixCell = {
  rowSymbol: string;
  colSymbol: string;
  value: number | null;
};

type CorrelationEdge = {
  leftSymbol: string;
  rightSymbol: string;
  value: number;
};

type TailRiskSnapshot = {
  leftTailMassRatio: number | null;
  rightTailMassRatio: number | null;
  tailBalanceRatio: number | null;
  downsideBucketLabel: string;
  downsideBucketFrequencyRatio: number | null;
  valueAtRiskRatio: number | null;
  expectedShortfallRatio: number | null;
  tailGapRatio: number | null;
};

function buildReturnSeries(points: PortfolioTimeSeriesPoint[]): Map<string, number> {
  const orderedPoints = [...points].sort((left, right) =>
    left.captured_at.localeCompare(right.captured_at),
  );
  const returnsByTimestamp = new Map<string, number>();
  for (let index = 1; index < orderedPoints.length; index += 1) {
    const previousValue = Number(orderedPoints[index - 1].portfolio_value_usd);
    const currentValue = Number(orderedPoints[index].portfolio_value_usd);
    if (!Number.isFinite(previousValue) || !Number.isFinite(currentValue) || previousValue <= 0) {
      continue;
    }
    returnsByTimestamp.set(
      orderedPoints[index].captured_at,
      (currentValue - previousValue) / previousValue,
    );
  }
  return returnsByTimestamp;
}

function computePearsonCorrelation(left: number[], right: number[]): number | null {
  if (left.length < 6 || right.length < 6 || left.length !== right.length) {
    return null;
  }
  const sampleCount = left.length;
  const leftMean = left.reduce((accumulator, value) => accumulator + value, 0) / sampleCount;
  const rightMean = right.reduce((accumulator, value) => accumulator + value, 0) / sampleCount;

  let covarianceAccumulator = 0;
  let leftVarianceAccumulator = 0;
  let rightVarianceAccumulator = 0;
  for (let index = 0; index < sampleCount; index += 1) {
    const leftCentered = left[index] - leftMean;
    const rightCentered = right[index] - rightMean;
    covarianceAccumulator += leftCentered * rightCentered;
    leftVarianceAccumulator += leftCentered * leftCentered;
    rightVarianceAccumulator += rightCentered * rightCentered;
  }
  if (leftVarianceAccumulator <= 0 || rightVarianceAccumulator <= 0) {
    return null;
  }
  return covarianceAccumulator / Math.sqrt(leftVarianceAccumulator * rightVarianceAccumulator);
}

function computeCorrelationBetweenSeries(
  leftSeries: Map<string, number>,
  rightSeries: Map<string, number>,
): number | null {
  const leftValues: number[] = [];
  const rightValues: number[] = [];
  for (const [timestamp, leftReturn] of leftSeries.entries()) {
    const rightReturn = rightSeries.get(timestamp);
    if (rightReturn === undefined) {
      continue;
    }
    leftValues.push(leftReturn);
    rightValues.push(rightReturn);
  }
  return computePearsonCorrelation(leftValues, rightValues);
}

function resolveCorrelationTone(value: number | null): "positive" | "negative" | "neutral" {
  if (value === null) {
    return "neutral";
  }
  if (value >= 0.65) {
    return "positive";
  }
  if (value <= -0.45) {
    return "negative";
  }
  return "neutral";
}

function formatCorrelation(value: number | null): string {
  if (value === null) {
    return "n/a";
  }
  return value.toFixed(2);
}

function resolveTailRiskSnapshot(
  metrics: PortfolioRiskEstimatorMetric[],
  bucketData: Array<{ lower_bound: string; upper_bound: string; frequency: string; count: number }>,
): TailRiskSnapshot {
  const orderedBuckets = [...bucketData].sort(
    (left, right) => Number(left.lower_bound) - Number(right.lower_bound),
  );
  const tailBucketCount = Math.max(1, Math.ceil(orderedBuckets.length * 0.2));
  const leftTailBuckets = orderedBuckets.slice(0, tailBucketCount);
  const rightTailBuckets = orderedBuckets.slice(-tailBucketCount);
  const leftTailMassRatio = leftTailBuckets.reduce((accumulator, bucket) => {
    return accumulator + Number(bucket.frequency);
  }, 0);
  const rightTailMassRatio = rightTailBuckets.reduce((accumulator, bucket) => {
    return accumulator + Number(bucket.frequency);
  }, 0);
  const tailBalanceRatio = rightTailMassRatio - leftTailMassRatio;
  const downsideBucket = orderedBuckets[0];
  const valueAtRiskMetric = metrics.find((metric) => metric.estimator_id === "value_at_risk_95");
  const expectedShortfallMetric = metrics.find(
    (metric) => metric.estimator_id === "expected_shortfall_95",
  );
  const valueAtRiskRatio = valueAtRiskMetric ? Number(valueAtRiskMetric.value) : null;
  const expectedShortfallRatio = expectedShortfallMetric
    ? Number(expectedShortfallMetric.value)
    : null;
  const tailGapRatio =
    valueAtRiskRatio !== null && expectedShortfallRatio !== null
      ? Math.abs(expectedShortfallRatio) - Math.abs(valueAtRiskRatio)
      : null;

  return {
    leftTailMassRatio: Number.isFinite(leftTailMassRatio) ? leftTailMassRatio : null,
    rightTailMassRatio: Number.isFinite(rightTailMassRatio) ? rightTailMassRatio : null,
    tailBalanceRatio: Number.isFinite(tailBalanceRatio) ? tailBalanceRatio : null,
    downsideBucketLabel: downsideBucket
      ? `${(Number(downsideBucket.lower_bound) * 100).toFixed(2)}% to ${(Number(
          downsideBucket.upper_bound,
        ) * 100).toFixed(2)}%`
      : "n/a",
    downsideBucketFrequencyRatio: downsideBucket ? Number(downsideBucket.frequency) : null,
    valueAtRiskRatio:
      valueAtRiskRatio !== null && Number.isFinite(valueAtRiskRatio)
        ? valueAtRiskRatio
        : null,
    expectedShortfallRatio:
      expectedShortfallRatio !== null && Number.isFinite(expectedShortfallRatio)
        ? expectedShortfallRatio
        : null,
    tailGapRatio: tailGapRatio !== null && Number.isFinite(tailGapRatio) ? tailGapRatio : null,
  };
}

export function PortfolioRiskPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const selectedScope = resolveScopeFromSearchParams(searchParams);
  const selectedInstrumentSymbol = resolveInstrumentSymbolFromSearchParams(searchParams);
  const isInstrumentScope = selectedScope === "instrument_symbol";
  const isScopeReady = !isInstrumentScope || selectedInstrumentSymbol !== null;
  const selectedWindow = mapChartPeriodToRiskWindow(selectedPeriod);
  const riskQuery = usePortfolioRiskEstimatorsScopedQuery(selectedWindow, {
    scope: selectedScope,
    instrumentSymbol: selectedInstrumentSymbol,
    period: selectedPeriod,
    enabled: isScopeReady,
  });
  const riskEvolutionQuery = usePortfolioRiskEvolutionQuery(selectedPeriod, {
    scope: selectedScope,
    instrumentSymbol: selectedInstrumentSymbol,
    enabled: isScopeReady,
  });
  const returnDistributionQuery = usePortfolioReturnDistributionQuery(selectedPeriod, {
    scope: selectedScope,
    instrumentSymbol: selectedInstrumentSymbol,
    binCount: 12,
    enabled: isScopeReady,
  });
  const healthQuery = usePortfolioHealthSynthesisQuery(selectedPeriod, {
    scope: selectedScope,
    instrumentSymbol: selectedInstrumentSymbol,
    profilePosture: "balanced",
    enabled: isScopeReady,
  });
  const [correlationSymbols, setCorrelationSymbols] = useState<string[]>([]);
  const [correlationSeriesEntries, setCorrelationSeriesEntries] = useState<
    Array<{ symbol: string; points: PortfolioTimeSeriesPoint[] }>
  >([]);
  const [correlationSeriesState, setCorrelationSeriesState] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [correlationReloadToken, setCorrelationReloadToken] = useState(0);
  const [showDrawdownSeries, setShowDrawdownSeries] = useState(true);
  const [showRollingVolatilitySeries, setShowRollingVolatilitySeries] = useState(true);
  const [showRollingBetaSeries, setShowRollingBetaSeries] = useState(true);

  const isLoading = riskQuery.isLoading;
  const isError = riskQuery.isError;
  const isSuccess = riskQuery.isSuccess;
  const isEmpty = isSuccess && riskQuery.data.metrics.length === 0;
  const errorCopy = resolveRiskErrorCopy(riskQuery.error);

  useEffect(() => {
    if (selectedScope !== "portfolio") {
      setCorrelationSymbols([]);
      setCorrelationSeriesEntries([]);
      setCorrelationSeriesState("idle");
      return;
    }
    let isActive = true;
    async function hydrateCorrelationSymbols(): Promise<void> {
      try {
        const summaryResponse = await fetchPortfolioSummary();
        if (!isActive) {
          return;
        }
        const symbols = [...summaryResponse.rows]
          .sort((left, right) => {
            const leftMarketValue = Number(left.market_value_usd ?? "0");
            const rightMarketValue = Number(right.market_value_usd ?? "0");
            return rightMarketValue - leftMarketValue;
          })
          .map((row) => row.instrument_symbol.trim().toUpperCase())
          .filter((symbol, index, list) => {
            return symbol.length > 0 && list.indexOf(symbol) === index;
          })
          .slice(0, 6);
        setCorrelationSymbols(symbols);
      } catch {
        if (!isActive) {
          return;
        }
        setCorrelationSymbols([]);
      }
    }
    void hydrateCorrelationSymbols();
    return () => {
      isActive = false;
    };
  }, [correlationReloadToken, selectedScope]);

  useEffect(() => {
    if (
      selectedScope !== "portfolio" ||
      !isScopeReady ||
      correlationSymbols.length < 2
    ) {
      setCorrelationSeriesEntries([]);
      setCorrelationSeriesState("idle");
      return;
    }
    let isActive = true;
    setCorrelationSeriesState("loading");
    async function hydrateCorrelationSeries(): Promise<void> {
      try {
        const entries = await Promise.all(
          correlationSymbols.map(async (symbol) => {
            const response = await fetchPortfolioTimeSeries(selectedPeriod, {
              scope: "instrument_symbol",
              instrumentSymbol: symbol,
            });
            return {
              symbol,
              points: response.points,
            };
          }),
        );
        if (!isActive) {
          return;
        }
        setCorrelationSeriesEntries(entries);
        setCorrelationSeriesState("ready");
      } catch {
        if (!isActive) {
          return;
        }
        setCorrelationSeriesEntries([]);
        setCorrelationSeriesState("error");
      }
    }
    void hydrateCorrelationSeries();
    return () => {
      isActive = false;
    };
  }, [
    correlationReloadToken,
    correlationSymbols,
    isScopeReady,
    selectedPeriod,
    selectedScope,
  ]);

  function handlePeriodChange(nextPeriod: PortfolioChartPeriod): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("period", nextPeriod);
      return next;
    });
  }

  function handleScopeChange(nextScope: PortfolioTimeSeriesScope): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("scope", nextScope);
      if (nextScope === "portfolio") {
        next.delete("instrument_symbol");
      }
      return next;
    });
  }

  function handleInstrumentSymbolChange(nextSymbol: string): void {
    const normalized = nextSymbol.trim().toUpperCase();
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      if (normalized.length === 0) {
        next.delete("instrument_symbol");
      } else {
        next.set("instrument_symbol", normalized);
      }
      return next;
    });
  }

  const orderedMetrics = isSuccess ? sortRiskMetrics(riskQuery.data.metrics) : [];
  const riskCoreTenMetrics = getCoreTenEntriesForRoute("risk");
  const unitSet = new Set(orderedMetrics.map((metric) => resolveRiskMetricUnit(metric.estimator_id)));
  const hasMixedRiskUnits = unitSet.size > 1;
  const metricGroups = groupRiskMetricsByUnit(orderedMetrics);
  const correlationMatrixData = useMemo(() => {
    if (correlationSeriesState !== "ready") {
      return {
        symbols: [] as string[],
        matrix: [] as CorrelationMatrixCell[],
        edges: [] as CorrelationEdge[],
      };
    }
    const returnsBySymbol = new Map<string, Map<string, number>>();
    for (const entry of correlationSeriesEntries) {
      returnsBySymbol.set(entry.symbol, buildReturnSeries(entry.points));
    }
    const symbols = Array.from(returnsBySymbol.keys());
    const matrix: CorrelationMatrixCell[] = [];
    const edges: CorrelationEdge[] = [];

    for (const rowSymbol of symbols) {
      const rowSeries = returnsBySymbol.get(rowSymbol);
      if (!rowSeries) {
        continue;
      }
      for (const colSymbol of symbols) {
        const colSeries = returnsBySymbol.get(colSymbol);
        if (!colSeries) {
          continue;
        }
        const value =
          rowSymbol === colSymbol
            ? 1
            : computeCorrelationBetweenSeries(rowSeries, colSeries);
        matrix.push({
          rowSymbol,
          colSymbol,
          value,
        });
        if (
          rowSymbol < colSymbol &&
          value !== null &&
          Math.abs(value) >= 0.65
        ) {
          edges.push({
            leftSymbol: rowSymbol,
            rightSymbol: colSymbol,
            value,
          });
        }
      }
    }

    return {
      symbols,
      matrix,
      edges: edges.sort((left, right) => Math.abs(right.value) - Math.abs(left.value)),
    };
  }, [correlationSeriesEntries, correlationSeriesState]);
  const tailRiskSnapshot = useMemo(() => {
    if (!returnDistributionQuery.isSuccess || orderedMetrics.length === 0) {
      return null;
    }
    return resolveTailRiskSnapshot(orderedMetrics, returnDistributionQuery.data.buckets);
  }, [orderedMetrics, returnDistributionQuery.data, returnDistributionQuery.isSuccess]);

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Risk route"
      title="Bounded estimator workspace"
      description="Risk estimators with explicit methodology metadata, unsupported-scope visibility, and risk-context interpretation boundaries."
      actions={
        <>
          <label className="period-control">
            <span className="period-control__label">Scope</span>
            <select
              aria-label="Select risk scope"
              className="period-control__select"
              onChange={(event) => handleScopeChange(event.target.value as PortfolioTimeSeriesScope)}
              value={selectedScope}
            >
              <option value="portfolio">Portfolio</option>
              <option value="instrument_symbol">Instrument</option>
            </select>
          </label>
          {selectedScope === "instrument_symbol" ? (
            <label className="period-control">
              <span className="period-control__label">Symbol</span>
              <input
                aria-label="Instrument symbol"
                className="period-control__select"
                onChange={(event) => handleInstrumentSymbolChange(event.target.value)}
                placeholder="AAPL"
                value={selectedInstrumentSymbol ?? ""}
              />
            </label>
          ) : null}
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
      <WorkspacePrimaryJobPanel
        routeLabel="Risk"
        jobTitle="Risk posture interpretation"
        jobDescription="Use one bounded risk interpretation layer before deep chart drill-down so unit semantics remain explicit."
        decisionTags={["risk_posture"]}
        coreTenMetrics={riskCoreTenMetrics}
      />

      {!isScopeReady ? (
        <WorkspaceStateBanner
          state="blocked"
          message="Instrument scope requires one symbol before risk requests can be submitted."
        />
      ) : isLoading ? (
        <WorkspaceStateBanner state="loading" />
      ) : isError ? (
        <WorkspaceStateBanner state="error" message={errorCopy.message} />
      ) : isSuccess && isEmpty ? (
        <WorkspaceStateBanner state="unavailable" />
      ) : isSuccess ? (
        <WorkspaceStateBanner state="ready" />
      ) : null}

      {isLoading ? <LoadingTableSkeleton rows={4} /> : null}

      {!isScopeReady ? (
        <ErrorBanner
          title="Risk scope requires symbol"
          message="Provide an instrument symbol to request instrument-scoped risk diagnostics."
          variant="warning"
        />
      ) : null}

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

      {isScopeReady ? (
        <WorkspaceChartPanel
          title="Health context bridge"
          subtitle="Risk pillar contribution linked to aggregate portfolio-health interpretation."
          shortDescription="Shows how current estimator posture affects overall health label and score."
          longDescription="Use this bridge to connect estimator readings with executive health interpretation before moving to timeline diagnostics."
        >
          {healthQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}
          {healthQuery.isError ? (
            <ErrorBanner
              title="Health context unavailable"
              message="Risk-to-health bridge could not be loaded for selected scope."
              variant="warning"
              actions={
                <button
                  className="button-primary"
                  onClick={() => void healthQuery.refetch()}
                  type="button"
                >
                  Retry health context
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
                    Score {healthQuery.data.health_score}/100 for balanced posture.
                  </p>
                </article>
                <article className="chart-summary-card chart-summary-card--accent">
                  <span className="chart-summary-card__label">Risk pillar score</span>
                  <strong className="chart-summary-card__headline">
                    {healthQuery.data.pillars.find((pillar) => pillar.pillar_id === "risk")?.score ?? 0}/100
                  </strong>
                  <p className="chart-summary-card__copy">
                    Derived from drawdown, volatility, VaR, and expected shortfall posture.
                  </p>
                </article>
              </div>
              <section className="context-banner context-banner--info" aria-live="polite">
                <h3 className="context-banner__title">Health driver link</h3>
                <p className="context-banner__copy">
                  {healthQuery.data.key_drivers
                    .filter((driver) => driver.direction === "penalizing")
                    .slice(0, 2)
                    .map((driver) => `${driver.label} ${driver.value_display}`)
                    .join(" · ") || "No dominant penalizing risk drivers in current profile."}
                </p>
              </section>
            </>
          ) : null}
        </WorkspaceChartPanel>
      ) : null}

      {isScopeReady ? (
        <WorkspaceChartPanel
          title="Drawdown path timeline"
          subtitle="Peak-to-trough path across selected scope and period."
          shortDescription="Use drawdown trajectory to understand depth and recovery rhythm, not only endpoint severity."
          longDescription="Drawdown values are expressed as relative decline from the running peak in the selected scope. Persistent deep drawdowns indicate slower capital recovery dynamics."
          actions={
            <button
              aria-label="Toggle drawdown series"
              aria-pressed={showDrawdownSeries}
              className="chart-chip"
              onClick={() => setShowDrawdownSeries((previous) => !previous)}
              type="button"
            >
              Drawdown series
            </button>
          }
        >
          {riskEvolutionQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}
          {riskEvolutionQuery.isError ? (
            <ErrorBanner
              title="Risk evolution unavailable"
              message="Drawdown timeline could not be loaded for selected scope and period."
              variant="warning"
              actions={
                <button
                  className="button-primary"
                  onClick={() => void riskEvolutionQuery.refetch()}
                  type="button"
                >
                  Retry timeline
                </button>
              }
            />
          ) : null}
          {riskEvolutionQuery.isSuccess &&
          riskEvolutionQuery.data.drawdown_path_points.length > 0 ? (
            <DrawdownTimelineChart
              points={riskEvolutionQuery.data.drawdown_path_points}
              showDrawdown={showDrawdownSeries}
            />
          ) : null}
        </WorkspaceChartPanel>
      ) : null}

      {isScopeReady ? (
        <WorkspaceChartPanel
          title="Rolling estimator timeline"
          subtitle="Time-evolution context for rolling volatility and rolling beta."
          shortDescription="Rolling metrics provide trend context to support current snapshot interpretation."
          longDescription="Rolling estimators are computed over a bounded trailing window. Use these paths to detect regime shifts rather than relying on one-point values."
          actions={
            <div className="chart-controls">
              <button
                aria-label="Toggle rolling volatility series"
                aria-pressed={showRollingVolatilitySeries}
                className="chart-chip"
                onClick={() => setShowRollingVolatilitySeries((previous) => !previous)}
                type="button"
              >
                Rolling volatility
              </button>
              <button
                aria-label="Toggle rolling beta series"
                aria-pressed={showRollingBetaSeries}
                className="chart-chip"
                onClick={() => setShowRollingBetaSeries((previous) => !previous)}
                type="button"
              >
                Rolling beta
              </button>
            </div>
          }
        >
          {riskEvolutionQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}
          {riskEvolutionQuery.isError ? (
            <ErrorBanner
              title="Rolling estimators unavailable"
              message="Rolling timeline data could not be loaded for selected scope and period."
              variant="warning"
              actions={
                <button
                  className="button-primary"
                  onClick={() => void riskEvolutionQuery.refetch()}
                  type="button"
                >
                  Retry rolling series
                </button>
              }
            />
          ) : null}
          {riskEvolutionQuery.isSuccess && riskEvolutionQuery.data.rolling_points.length > 0 ? (
            <RollingEstimatorsTimelineChart
              points={riskEvolutionQuery.data.rolling_points}
              showVolatility={showRollingVolatilitySeries}
              showBeta={showRollingBetaSeries}
            />
          ) : null}
        </WorkspaceChartPanel>
      ) : null}

      {isScopeReady ? (
        <WorkspaceChartPanel
          title="Correlation cluster network"
          subtitle="Cross-symbol co-movement map for the largest tracked holdings."
          shortDescription="Pairwise correlation matrix plus high-link clusters to spot concentration-through-correlation."
          longDescription="Correlations are computed from aligned daily return series on the selected period. Use this map to find hidden concentration where symbols move together even if position weights differ."
        >
          {selectedScope !== "portfolio" ? (
            <ErrorBanner
              title="Correlation map available on portfolio scope"
              message="Switch scope to portfolio to evaluate cross-symbol co-movement network."
              variant="warning"
            />
          ) : null}
          {selectedScope === "portfolio" && correlationSeriesState === "loading" ? (
            <LoadingTableSkeleton rows={2} />
          ) : null}
          {selectedScope === "portfolio" && correlationSeriesState === "error" ? (
            <ErrorBanner
              title="Correlation network unavailable"
              message="Instrument time-series pull failed while building the cluster network."
              variant="warning"
              actions={
                <button
                  className="button-primary"
                  onClick={() =>
                    setCorrelationReloadToken((previousToken) => previousToken + 1)
                  }
                  type="button"
                >
                  Retry correlation map
                </button>
              }
            />
          ) : null}
          {selectedScope === "portfolio" &&
          correlationSeriesState === "ready" &&
          correlationMatrixData.symbols.length >= 2 ? (
            <>
              <div
                className="correlation-matrix"
                role="table"
                aria-label="Symbol correlation matrix"
              >
                <div className="correlation-matrix__row correlation-matrix__row--header" role="row">
                  <span role="columnheader">Symbol</span>
                  {correlationMatrixData.symbols.map((symbol) => (
                    <span key={symbol} role="columnheader">
                      {symbol}
                    </span>
                  ))}
                </div>
                {correlationMatrixData.symbols.map((rowSymbol) => (
                  <div className="correlation-matrix__row" key={rowSymbol} role="row">
                    <span className="correlation-matrix__symbol" role="rowheader">
                      {rowSymbol}
                    </span>
                    {correlationMatrixData.symbols.map((colSymbol) => {
                      const cell = correlationMatrixData.matrix.find(
                        (candidate) =>
                          candidate.rowSymbol === rowSymbol &&
                          candidate.colSymbol === colSymbol,
                      );
                      const tone = resolveCorrelationTone(cell?.value ?? null);
                      return (
                        <span
                          className={`correlation-matrix__cell correlation-matrix__cell--${tone}`}
                          key={`${rowSymbol}-${colSymbol}`}
                          role="cell"
                        >
                          {formatCorrelation(cell?.value ?? null)}
                        </span>
                      );
                    })}
                  </div>
                ))}
              </div>
              <section className="correlation-network">
                <h3>Cluster links (|corr| ≥ 0.65)</h3>
                {correlationMatrixData.edges.length > 0 ? (
                  <ul className="correlation-network__list">
                    {correlationMatrixData.edges.map((edge) => (
                      <li key={`${edge.leftSymbol}-${edge.rightSymbol}`}>
                        <strong>
                          {edge.leftSymbol} ↔ {edge.rightSymbol}
                        </strong>
                        <span>{edge.value > 0 ? "positive" : "inverse"} {edge.value.toFixed(2)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>
                    No high-correlation clusters above 0.65 in the selected period.
                  </p>
                )}
              </section>
            </>
          ) : null}
        </WorkspaceChartPanel>
      ) : null}

      {isScopeReady ? (
        <WorkspaceChartPanel
          title="Return distribution"
          subtitle="Deterministic equal-width buckets over aligned return history."
          shortDescription="Distribution shape complements drawdown and rolling metrics for risk storytelling."
          longDescription="Histogram buckets are deterministic for equivalent input state and policy. Evaluate skew, tail concentration, and central tendency together with volatility and drawdown modules."
        >
          {returnDistributionQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}
          {returnDistributionQuery.isError ? (
            <ErrorBanner
              title="Return distribution unavailable"
              message="Return-distribution buckets could not be loaded for selected scope and period."
              variant="warning"
              actions={
                <button
                  className="button-primary"
                  onClick={() => void returnDistributionQuery.refetch()}
                  type="button"
                >
                  Retry distribution
                </button>
              }
            />
          ) : null}
          {returnDistributionQuery.isSuccess && returnDistributionQuery.data.buckets.length > 0 ? (
            <>
              <ReturnDistributionChart buckets={returnDistributionQuery.data.buckets} />
              <p className="chart-footnote">
                Bucket policy: {returnDistributionQuery.data.bucket_policy.method} (
                {returnDistributionQuery.data.bucket_policy.bin_count} bins), sample size{" "}
                {returnDistributionQuery.data.sample_size}.
              </p>
            </>
          ) : null}
        </WorkspaceChartPanel>
      ) : null}

      {isScopeReady ? (
        <WorkspaceChartPanel
          title="Tail risk diagnostics"
          subtitle="Left-tail concentration, stress-gap, and downside bucket severity."
          shortDescription="Diagnoses asymmetry between downside and upside tails using return-distribution and VaR/ES estimators."
          longDescription="Tail diagnostics should be interpreted with drawdown and rolling modules. A larger ES-vs-VaR gap and heavier left-tail bucket mass imply more severe downside paths when losses occur."
        >
          {!tailRiskSnapshot ? (
            <EmptyState
              title="Tail diagnostics pending"
              message="Tail risk module requires both estimator and distribution responses."
            />
          ) : (
            <>
              <div className="chart-summary-grid tail-risk-grid">
                <article className="chart-summary-card chart-summary-card--signal">
                  <span className="chart-summary-card__label">Left-tail mass</span>
                  <strong className="chart-summary-card__headline">
                    {((tailRiskSnapshot.leftTailMassRatio ?? 0) * 100).toFixed(2)}%
                  </strong>
                  <p className="chart-summary-card__copy">
                    Lowest 20% bucket mass of return distribution.
                  </p>
                </article>
                <article className="chart-summary-card chart-summary-card--accent">
                  <span className="chart-summary-card__label">Tail balance</span>
                  <strong className="chart-summary-card__headline">
                    {tailRiskSnapshot.tailBalanceRatio === null
                      ? "—"
                      : `${tailRiskSnapshot.tailBalanceRatio > 0 ? "+" : ""}${(tailRiskSnapshot.tailBalanceRatio * 100).toFixed(2)}%`}
                  </strong>
                  <p className="chart-summary-card__copy">
                    Right tail minus left tail mass.
                  </p>
                </article>
                <article className="chart-summary-card">
                  <span className="chart-summary-card__label">Stress gap (ES - VaR)</span>
                  <strong className="chart-summary-card__headline">
                    {tailRiskSnapshot.tailGapRatio === null
                      ? "—"
                      : `${(tailRiskSnapshot.tailGapRatio * 100).toFixed(2)}%`}
                  </strong>
                  <p className="chart-summary-card__copy">
                    Gap between expected shortfall and VaR (95%).
                  </p>
                </article>
              </div>

              <div className="tail-risk-ledger" role="table" aria-label="Tail risk ledger">
                <div className="tail-risk-ledger__row tail-risk-ledger__row--header" role="row">
                  <span role="columnheader">Metric</span>
                  <span role="columnheader">Value</span>
                  <span role="columnheader">Interpretation</span>
                </div>
                <div className="tail-risk-ledger__row" role="row">
                  <span role="cell">Worst distribution bucket</span>
                  <strong role="cell">
                    {tailRiskSnapshot.downsideBucketLabel} (
                    {tailRiskSnapshot.downsideBucketFrequencyRatio === null
                      ? "—"
                      : `${(tailRiskSnapshot.downsideBucketFrequencyRatio * 100).toFixed(2)}%`}
                    )
                  </strong>
                  <span role="cell">
                    Frequency concentration in the most negative return band.
                  </span>
                </div>
                <div className="tail-risk-ledger__row" role="row">
                  <span role="cell">VaR (95%) vs ES (95%)</span>
                  <strong role="cell">
                    {tailRiskSnapshot.valueAtRiskRatio === null
                      ? "—"
                      : `${(tailRiskSnapshot.valueAtRiskRatio * 100).toFixed(2)}%`} /{" "}
                    {tailRiskSnapshot.expectedShortfallRatio === null
                      ? "—"
                      : `${(tailRiskSnapshot.expectedShortfallRatio * 100).toFixed(2)}%`}
                  </strong>
                  <span role="cell">
                    Wider separation suggests deeper losses inside tail scenarios.
                  </span>
                </div>
              </div>
            </>
          )}
        </WorkspaceChartPanel>
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
