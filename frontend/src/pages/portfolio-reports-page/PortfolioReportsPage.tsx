import {
  Link,
  useSearchParams,
} from "react-router-dom";
import {
  useEffect,
  useState,
} from "react";

import { PortfolioMonthlyReturnsHeatmap } from "../../components/charts/AnalystVisualModules";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { MetricExplainabilityPopover } from "../../components/metric-explainability/MetricExplainabilityPopover";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { AppApiError } from "../../core/api/errors";
import type {
  PortfolioContributionRow,
  PortfolioQuantMetric,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportScope,
  PortfolioTimeSeriesScope,
} from "../../core/api/schemas";
import { formatUsdMoney } from "../../core/lib/formatters";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import {
  usePortfolioContributionQuery,
  usePortfolioQuantMetricsQuery,
  usePortfolioQuantReportGenerateMutation,
  usePortfolioQuantReportHtmlQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";
import {
  buildQuantMetricCards,
  topContributionRows,
} from "../../features/portfolio-workspace/overview";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"), "90D");
}

function resolveContributionTone(
  contributionPnlUsd: string,
): "positive" | "negative" | "neutral" {
  const numericValue = Number(contributionPnlUsd);
  if (!Number.isFinite(numericValue)) {
    return "neutral";
  }
  if (numericValue > 0) {
    return "positive";
  }
  if (numericValue < 0) {
    return "negative";
  }
  return "neutral";
}

function formatSignedPercent(value: string): string {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return `${value}%`;
  }
  const signPrefix = numericValue > 0 ? "+" : "";
  return `${signPrefix}${numericValue.toFixed(2)}%`;
}

function buildContributionRows(rows: PortfolioContributionRow[]): {
  rows: Array<{
    instrumentSymbol: string;
    contributionPnlUsd: string;
    contributionPct: string;
    tone: "positive" | "negative" | "neutral";
    widthPct: number;
  }>;
  positiveLeader: string | null;
  negativeLeader: string | null;
  concentrationPct: string;
} {
  const sortedRows = topContributionRows(rows);
  const maxAbsContribution = Math.max(
    1,
    ...sortedRows.map((row) => Math.abs(Number(row.contribution_pnl_usd))),
  );
  const totalAbsContribution = sortedRows.reduce((accumulator, row) => {
    return accumulator + Math.abs(Number(row.contribution_pnl_usd));
  }, 0);

  const positiveLeader = sortedRows.find(
    (row) => Number(row.contribution_pnl_usd) > 0,
  );
  const negativeLeader = sortedRows.find(
    (row) => Number(row.contribution_pnl_usd) < 0,
  );
  const concentrationNumerator =
    sortedRows.length > 0 ? Math.abs(Number(sortedRows[0].contribution_pnl_usd)) : 0;
  const concentrationPct =
    totalAbsContribution > 0
      ? ((concentrationNumerator / totalAbsContribution) * 100).toFixed(2)
      : "0.00";

  return {
    rows: sortedRows.map((row) => {
      const contributionAbs = Math.abs(Number(row.contribution_pnl_usd));
      const widthPct = Math.max(
        8,
        Math.round((contributionAbs / maxAbsContribution) * 100),
      );
      return {
        instrumentSymbol: row.instrument_symbol,
        contributionPnlUsd: row.contribution_pnl_usd,
        contributionPct: row.contribution_pct,
        tone: resolveContributionTone(row.contribution_pnl_usd),
        widthPct,
      };
    }),
    positiveLeader: positiveLeader
      ? `${positiveLeader.instrument_symbol} ${formatUsdMoney(positiveLeader.contribution_pnl_usd)}`
      : null,
    negativeLeader: negativeLeader
      ? `${negativeLeader.instrument_symbol} ${formatUsdMoney(negativeLeader.contribution_pnl_usd)}`
      : null,
    concentrationPct,
  };
}

function resolveReportPreviewError(error: unknown): {
  title: string;
  variant: "error" | "warning";
  message: string;
} {
  if (error instanceof AppApiError && error.detail) {
    const detail = error.detail.toLowerCase();
    if (detail.includes("unavailable") || detail.includes("expired")) {
      return {
        title: "Report lifecycle: unavailable",
        variant: "warning",
        message: error.detail,
      };
    }
  }

  return resolveWorkspaceError(
    error,
    "Report lifecycle: error",
    "The generated HTML artifact is not available right now.",
  );
}

function formatQuantLensMetricValue(metric: PortfolioQuantMetric | undefined): string {
  if (!metric) {
    return "—";
  }
  const numericValue = Number(metric.value);
  if (!Number.isFinite(numericValue)) {
    return String(metric.value);
  }
  if (metric.display_as === "percent") {
    const percentValue = numericValue * 100;
    const signPrefix = percentValue > 0 ? "+" : "";
    return `${signPrefix}${percentValue.toFixed(2)}%`;
  }
  return numericValue.toFixed(3);
}

type ReportLifecycleUiState =
  | "invalid_request"
  | "loading"
  | "ready"
  | "unavailable"
  | "error";

export function PortfolioReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const [reportScope, setReportScope] = useState<PortfolioQuantReportScope>("portfolio");
  const [reportInstrumentSymbol, setReportInstrumentSymbol] = useState("");
  const [heatmapScope, setHeatmapScope] = useState<PortfolioTimeSeriesScope>("portfolio");
  const [heatmapInstrumentSymbol, setHeatmapInstrumentSymbol] = useState("");
  const [reportValidationError, setReportValidationError] = useState<string | null>(null);
  const [activeReportId, setActiveReportId] = useState<string | null>(null);

  const summaryQuery = usePortfolioSummaryQuery();
  const normalizedHeatmapInstrumentSymbol = heatmapInstrumentSymbol.trim().toUpperCase();
  const isInstrumentHeatmapScope = heatmapScope === "instrument_symbol";
  const isHeatmapScopeReady =
    !isInstrumentHeatmapScope || normalizedHeatmapInstrumentSymbol.length > 0;
  const timeSeriesQuery = usePortfolioTimeSeriesQuery(selectedPeriod, {
    scope: heatmapScope,
    instrumentSymbol: isInstrumentHeatmapScope ? normalizedHeatmapInstrumentSymbol : null,
    enabled: isHeatmapScopeReady,
  });
  const contributionQuery = usePortfolioContributionQuery(selectedPeriod);
  const quantMetricsQuery = usePortfolioQuantMetricsQuery(selectedPeriod);
  const quantMetrics30Query = usePortfolioQuantMetricsQuery("30D");
  const quantMetrics90Query = usePortfolioQuantMetricsQuery("90D");
  const quantMetrics252Query = usePortfolioQuantMetricsQuery("252D");
  const quantReportGenerateMutation = usePortfolioQuantReportGenerateMutation();
  const quantReportHtmlQuery = usePortfolioQuantReportHtmlQuery(activeReportId);

  const quantErrorCopy = resolveWorkspaceError(
    quantMetricsQuery.error,
    "Quant diagnostics unavailable",
    "Quant diagnostics could not be loaded for this period.",
  );
  const quantReportGenerateErrorCopy = resolveWorkspaceError(
    quantReportGenerateMutation.error,
    "Report lifecycle: error",
    "Report generation failed for the selected scope and period.",
  );
  const contributionErrorCopy = resolveWorkspaceError(
    contributionQuery.error,
    "Contribution focus unavailable",
    "Contribution rows could not be loaded for this period.",
  );
  const quantReportPreviewErrorCopy = resolveReportPreviewError(quantReportHtmlQuery.error);

  const availableInstrumentSymbols = summaryQuery.isSuccess
    ? summaryQuery.data.rows.map((row) => row.instrument_symbol)
    : [];

  useEffect(() => {
    if (
      reportScope === "instrument_symbol" &&
      availableInstrumentSymbols.length > 0 &&
      reportInstrumentSymbol.length === 0
    ) {
      setReportInstrumentSymbol(availableInstrumentSymbols[0]);
    }
  }, [availableInstrumentSymbols, reportInstrumentSymbol.length, reportScope]);

  useEffect(() => {
    if (
      heatmapScope === "instrument_symbol" &&
      availableInstrumentSymbols.length > 0 &&
      heatmapInstrumentSymbol.length === 0
    ) {
      setHeatmapInstrumentSymbol(availableInstrumentSymbols[0]);
    }
  }, [availableInstrumentSymbols, heatmapInstrumentSymbol.length, heatmapScope]);

  function handlePeriodChange(nextPeriod: "30D" | "90D" | "252D" | "MAX"): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("period", nextPeriod);
      return next;
    });
  }

  async function generateQuantReport(): Promise<void> {
    const normalizedSymbol = reportInstrumentSymbol.trim().toUpperCase();
    if (reportScope === "instrument_symbol" && normalizedSymbol.length === 0) {
      setReportValidationError("Instrument symbol is required for instrument-scoped reports.");
      return;
    }

    setReportValidationError(null);
    setActiveReportId(null);
    const request: PortfolioQuantReportGenerateRequest = {
      scope: reportScope,
      instrument_symbol: reportScope === "instrument_symbol" ? normalizedSymbol : null,
      period: selectedPeriod,
    };

    try {
      const generatedReport = await quantReportGenerateMutation.mutateAsync(request);
      setActiveReportId(generatedReport.report_id);
    } catch {
      setActiveReportId(null);
    }
  }

  const quantMetricCards = quantMetricsQuery.isSuccess
    ? buildQuantMetricCards(quantMetricsQuery.data.metrics)
    : [];
  const contributionFocus =
    contributionQuery.isSuccess && contributionQuery.data.rows.length > 0
      ? buildContributionRows(contributionQuery.data.rows)
      : null;

  const quantBenchmarkContext = quantMetricsQuery.data?.benchmark_context;
  const omittedMetricIds = quantBenchmarkContext?.omitted_metric_ids || [];
  const omittedMetricsSummary = omittedMetricIds.length > 0 ? omittedMetricIds.join(", ") : "";
  const quantLensMetricIds = [
    "sharpe",
    "sortino",
    "calmar",
    "volatility",
    "max_drawdown",
    "win_rate",
  ];
  const quantMetricsByPeriod: Record<string, PortfolioQuantMetric[]> = {
    "30D": quantMetrics30Query.data?.metrics || [],
    "90D": quantMetrics90Query.data?.metrics || [],
    "252D": quantMetrics252Query.data?.metrics || [],
  };
  const quantLensRows = quantLensMetricIds.map((metricId) => {
    const metric30 = quantMetricsByPeriod["30D"].find((metric) => metric.metric_id === metricId);
    const metric90 = quantMetricsByPeriod["90D"].find((metric) => metric.metric_id === metricId);
    const metric252 = quantMetricsByPeriod["252D"].find((metric) => metric.metric_id === metricId);
    return {
      metricId,
      label: metric90?.label || metric252?.label || metric30?.label || metricId,
      v30: formatQuantLensMetricValue(metric30),
      v90: formatQuantLensMetricValue(metric90),
      v252: formatQuantLensMetricValue(metric252),
    };
  });

  let reportLifecycleState: ReportLifecycleUiState = "unavailable";
  if (reportValidationError) {
    reportLifecycleState = "invalid_request";
  } else if (quantReportGenerateMutation.isPending || quantReportHtmlQuery.isLoading) {
    reportLifecycleState = "loading";
  } else if (quantReportGenerateMutation.isError) {
    reportLifecycleState = "error";
  } else if (quantReportHtmlQuery.isError) {
    reportLifecycleState = quantReportPreviewErrorCopy.variant === "warning" ? "unavailable" : "error";
  } else if (quantReportHtmlQuery.isSuccess) {
    reportLifecycleState = "ready";
  } else if (quantReportGenerateMutation.data?.lifecycle_status === "ready") {
    reportLifecycleState = "ready";
  } else if (quantReportGenerateMutation.data?.lifecycle_status === "unavailable") {
    reportLifecycleState = "unavailable";
  }

  const lifecyclePillToneClass =
    reportLifecycleState === "ready"
      ? "status-pill--positive"
      : reportLifecycleState === "error"
        ? "status-pill--negative"
        : "status-pill--neutral";

  const lifecycleLabelMap: Record<ReportLifecycleUiState, string> = {
    invalid_request: "invalid request",
    loading: "loading",
    ready: "ready",
    unavailable: "unavailable",
    error: "error",
  };
  const lifecycleStepStatuses = {
    requested:
      reportLifecycleState === "loading" ||
      reportLifecycleState === "ready" ||
      reportLifecycleState === "unavailable",
    generated:
      reportLifecycleState === "ready" ||
      (quantReportGenerateMutation.data?.lifecycle_status === "ready" &&
        reportLifecycleState !== "error"),
    preview:
      reportLifecycleState === "ready" && quantReportHtmlQuery.isSuccess,
  };

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Quant/Reports route"
      title="Quant diagnostics and report lifecycle"
      description="Dedicated analytical surface for QuantStats diagnostics, report lifecycle states, and deterministic artifact access."
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
      freshnessTimestamp={
        quantMetricsQuery.data?.as_of_ledger_at || timeSeriesQuery.data?.as_of_ledger_at
      }
      scopeLabel="Quant diagnostics + report artifact lifecycle"
      provenanceLabel={
        quantMetricsQuery.data?.benchmark_symbol || "QuantStats + persisted analytics APIs"
      }
      periodLabel={selectedPeriod}
      frequencyLabel={timeSeriesQuery.data?.frequency}
      timezoneLabel={timeSeriesQuery.data?.timezone}
    >
      <WorkspaceChartPanel
        title="Quant scorecards"
        subtitle="Analyst diagnostics with explicit benchmark-context omission handling."
        shortDescription="Primary diagnostics for risk-adjusted performance interpretation."
        longDescription="Interpret these metrics together; isolated values can be misleading when period coverage or benchmark context is incomplete."
      >
        {quantMetricsQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}

        {quantMetricsQuery.isError ? (
          <ErrorBanner
            title={quantErrorCopy.title}
            message={quantErrorCopy.message}
            variant={quantErrorCopy.variant}
            actions={
              <button
                className="button-primary"
                onClick={() => void quantMetricsQuery.refetch()}
                type="button"
              >
                Retry quant diagnostics
              </button>
            }
          />
        ) : null}

        {quantMetricsQuery.isSuccess && quantMetricCards.length === 0 ? (
          <EmptyState
            title="No quant diagnostics for selected period"
            message="The quant endpoint returned no metrics for this period."
          />
        ) : null}

        {quantMetricsQuery.isSuccess && quantMetricCards.length > 0 ? (
          <>
            {omittedMetricIds.length > 0 ? (
              <section className="context-banner context-banner--info" aria-live="polite">
                <h3 className="context-banner__title">Benchmark context partially unavailable</h3>
                <p className="context-banner__copy">
                  {quantBenchmarkContext?.omission_reason
                    ? `${quantBenchmarkContext.omission_reason} Omitted: ${omittedMetricsSummary}.`
                    : `Optional benchmark metrics were omitted for this request: ${omittedMetricsSummary}.`}
                </p>
              </section>
            ) : null}

            <div className="overview-grid">
              {quantMetricCards.map((metric) => (
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

            <div className="quant-lens-table" role="table" aria-label="Quant period lens">
              <div className="quant-lens-table__header" role="row">
                <span role="columnheader">Metric</span>
                <span role="columnheader">30D</span>
                <span role="columnheader">90D</span>
                <span role="columnheader">252D</span>
              </div>
              {quantLensRows.map((row) => (
                <div className="quant-lens-table__row" key={row.metricId} role="row">
                  <span className="quant-lens-table__metric" role="cell">
                    {row.label}
                  </span>
                  <span className="quant-lens-table__value" role="cell">
                    {row.v30}
                  </span>
                  <span className="quant-lens-table__value" role="cell">
                    {row.v90}
                  </span>
                  <span className="quant-lens-table__value" role="cell">
                    {row.v252}
                  </span>
                </div>
              ))}
            </div>
          </>
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Quant report lifecycle"
        subtitle="Loading, error, unavailable, and ready states are explicit and keyboard reachable."
        shortDescription="Generate and preview report artifacts from one stable action surface."
        longDescription="Report actions are persistent here; no workflow actions are hidden inside transient chart tooltips."
      >
        <div className="transactions-filters">
          <label className="transactions-filters__field">
            <span>Report scope</span>
            <select
              aria-label="Report scope"
              className="transactions-filters__select"
              onChange={(event) => {
                setReportScope(event.target.value as PortfolioQuantReportScope);
                setReportValidationError(null);
              }}
              value={reportScope}
            >
              <option value="portfolio">Portfolio</option>
              <option value="instrument_symbol">Instrument</option>
            </select>
          </label>
          {reportScope === "instrument_symbol" ? (
            <label className="transactions-filters__field">
              <span>Instrument symbol</span>
              <input
                className="transactions-filters__input"
                list="quant-report-symbols"
                onChange={(event) => {
                  setReportInstrumentSymbol(event.target.value.toUpperCase());
                  setReportValidationError(null);
                }}
                placeholder="AAPL"
                value={reportInstrumentSymbol}
              />
              <datalist id="quant-report-symbols">
                {availableInstrumentSymbols.map((symbol) => (
                  <option key={symbol} value={symbol} />
                ))}
              </datalist>
            </label>
          ) : null}
        </div>

        <div className="status-banner__actions">
          <button
            className={`button-primary ${quantReportGenerateMutation.isPending ? "button-primary--loading" : ""}`}
            disabled={quantReportGenerateMutation.isPending}
            onClick={() => void generateQuantReport()}
            type="button"
          >
            {quantReportGenerateMutation.isPending ? (
              <span className="button-spinner" aria-hidden="true" />
            ) : null}
            {quantReportGenerateMutation.isPending ? "Generating report..." : "Generate HTML report"}
          </button>
        </div>

        <div className="lifecycle-pill-row" role="status" aria-live="polite">
          <span className={`status-pill ${lifecyclePillToneClass}`}>
            Lifecycle: {lifecycleLabelMap[reportLifecycleState]}
          </span>
        </div>

        <ol className="lifecycle-stepper" aria-label="Quant report lifecycle steps">
          <li className={`lifecycle-stepper__step ${lifecycleStepStatuses.requested ? "is-active" : ""}`}>
            Requested
          </li>
          <li className={`lifecycle-stepper__step ${lifecycleStepStatuses.generated ? "is-active" : ""}`}>
            Generated
          </li>
          <li className={`lifecycle-stepper__step ${lifecycleStepStatuses.preview ? "is-active" : ""}`}>
            Preview ready
          </li>
        </ol>

        {reportLifecycleState === "invalid_request" && reportValidationError ? (
          <ErrorBanner
            title="Report lifecycle: invalid request"
            message={reportValidationError}
            variant="warning"
          />
        ) : null}

        {reportLifecycleState === "error" ? (
          <ErrorBanner
            title={
              quantReportGenerateMutation.isError
                ? quantReportGenerateErrorCopy.title
                : quantReportPreviewErrorCopy.title
            }
            message={
              quantReportGenerateMutation.isError
                ? quantReportGenerateErrorCopy.message
                : quantReportPreviewErrorCopy.message
            }
            variant={
              quantReportGenerateMutation.isError
                ? quantReportGenerateErrorCopy.variant
                : quantReportPreviewErrorCopy.variant
            }
            actions={
              quantReportGenerateMutation.isError ? undefined : (
                <button
                  className="button-primary"
                  onClick={() => void quantReportHtmlQuery.refetch()}
                  type="button"
                >
                  Retry report preview
                </button>
              )
            }
          />
        ) : null}

        {quantReportGenerateMutation.data ? (
          <div className="chart-summary-grid quant-report-summary-grid">
            <article className="chart-summary-card">
              <span className="chart-summary-card__label">Scope</span>
              <strong className="chart-summary-card__value">
                {quantReportGenerateMutation.data.scope}
              </strong>
              <p className="chart-summary-card__copy">Period {quantReportGenerateMutation.data.period}</p>
            </article>
            <article className="chart-summary-card chart-summary-card--accent">
              <span className="chart-summary-card__label">Lifecycle status</span>
              <strong className="chart-summary-card__value">
                {quantReportGenerateMutation.data.lifecycle_status}
              </strong>
              <p className="chart-summary-card__copy">Report id {quantReportGenerateMutation.data.report_id}</p>
            </article>
            <article className="chart-summary-card chart-summary-card--signal">
              <span className="chart-summary-card__label">Artifact</span>
              <a
                className="row-link"
                href={quantReportGenerateMutation.data.report_url_path}
                rel="noreferrer"
                target="_blank"
              >
                Open full HTML report
              </a>
            </article>
          </div>
        ) : null}

        {reportLifecycleState === "loading" ? (
          <div className="quant-report-preview quant-report-preview--loading" role="status" aria-live="polite">
            <span className="quant-report-preview__pulse" />
            <p>Report metadata is ready; loading HTML artifact preview.</p>
          </div>
        ) : null}

        {reportLifecycleState === "unavailable" && quantReportHtmlQuery.isError ? (
          <ErrorBanner
            title={quantReportPreviewErrorCopy.title}
            message={quantReportPreviewErrorCopy.message}
            variant={quantReportPreviewErrorCopy.variant}
            actions={
              <button
                className="button-primary"
                onClick={() => void quantReportHtmlQuery.refetch()}
                type="button"
              >
                Retry report preview
              </button>
            }
          />
        ) : null}

        {reportLifecycleState === "ready" && quantReportHtmlQuery.isSuccess ? (
          <iframe
            className="quant-report-preview"
            srcDoc={quantReportHtmlQuery.data}
            title="Quant report HTML preview"
          />
        ) : null}

        {reportLifecycleState === "unavailable" && !quantReportHtmlQuery.isError ? (
          <EmptyState
            title="Report lifecycle: unavailable"
            message="Generate a report to create a previewable artifact for this period and scope."
          />
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Monthly return heatmap"
        subtitle="Calendar-heatmap style rhythm view for period returns."
        shortDescription="Pattern-first module to spot recurring positive/negative months quickly."
        longDescription="Heatmap values are derived from available period points and should be paired with precise metric cards for decisions."
      >
        <div className="transactions-filters">
          <label className="transactions-filters__field">
            <span>Heatmap scope</span>
            <select
              aria-label="Heatmap scope"
              className="transactions-filters__select"
              onChange={(event) => {
                setHeatmapScope(event.target.value as PortfolioTimeSeriesScope);
              }}
              value={heatmapScope}
            >
              <option value="portfolio">Portfolio</option>
              <option value="instrument_symbol">Instrument</option>
            </select>
          </label>
          {heatmapScope === "instrument_symbol" ? (
            <label className="transactions-filters__field">
              <span>Heatmap instrument symbol</span>
              <select
                aria-label="Heatmap instrument symbol"
                className="transactions-filters__select"
                onChange={(event) => {
                  setHeatmapInstrumentSymbol(event.target.value);
                }}
                value={heatmapInstrumentSymbol}
              >
                {availableInstrumentSymbols.length === 0 ? (
                  <option value="">No symbols available</option>
                ) : null}
                {availableInstrumentSymbols.map((symbol) => (
                  <option key={symbol} value={symbol}>
                    {symbol}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
        </div>

        {heatmapScope === "instrument_symbol" && availableInstrumentSymbols.length === 0 ? (
          <EmptyState
            title="No symbols available for instrument heatmap"
            message="Load summary rows with open positions before requesting instrument-scoped monthly return heatmap."
          />
        ) : null}

        {timeSeriesQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}

        {timeSeriesQuery.isError ? (
          <ErrorBanner
            title="Heatmap unavailable"
            message="Time-series data is unavailable for monthly heatmap rendering."
            variant="warning"
            actions={
              <button
                className="button-primary"
                onClick={() => void timeSeriesQuery.refetch()}
                type="button"
              >
                Retry heatmap
              </button>
            }
          />
        ) : null}

        {timeSeriesQuery.isSuccess && isHeatmapScopeReady ? (
          <PortfolioMonthlyReturnsHeatmap points={timeSeriesQuery.data.points} />
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Symbol contribution focus"
        subtitle="Top movers to contextualize report scope decisions."
        shortDescription="Contribution endpoint highlights largest period drivers and draggers with directional weighting."
        longDescription="Use this module to decide whether a portfolio report is sufficient or whether one instrument deserves deeper report scope."
      >
        {contributionQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}

        {contributionQuery.isError ? (
          <ErrorBanner
            title={contributionErrorCopy.title}
            message={contributionErrorCopy.message}
            variant={contributionErrorCopy.variant}
            actions={
              <button
                className="button-primary"
                onClick={() => void contributionQuery.refetch()}
                type="button"
              >
                Retry contribution focus
              </button>
            }
          />
        ) : null}

        {contributionQuery.isSuccess && contributionQuery.data.rows.length === 0 ? (
          <EmptyState
            title="No contribution rows for selected period"
            message="Contribution endpoint returned no rows for this period."
          />
        ) : null}

        {contributionFocus ? (
          <div className="contribution-focus">
            <div className="chart-summary-grid">
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Top positive</span>
                <strong className="chart-summary-card__headline tone-positive">
                  {contributionFocus.positiveLeader || "No positive movers"}
                </strong>
                <p className="chart-summary-card__copy">
                  Largest positive symbol contribution in selected period.
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--signal">
                <span className="chart-summary-card__label">Top drag</span>
                <strong className="chart-summary-card__headline tone-negative">
                  {contributionFocus.negativeLeader || "No negative movers"}
                </strong>
                <p className="chart-summary-card__copy">
                  Largest negative symbol contribution in selected period.
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--accent">
                <span className="chart-summary-card__label">Concentration</span>
                <strong className="chart-summary-card__headline">
                  {contributionFocus.concentrationPct}%
                </strong>
                <p className="chart-summary-card__copy">
                  Share of absolute move explained by the top-ranked symbol.
                </p>
              </article>
            </div>

            <div
              className="contribution-focus__table"
              role="table"
              aria-label="Symbol contribution focus table"
            >
              <div className="contribution-focus__header" role="row">
                <span role="columnheader">Symbol</span>
                <span role="columnheader">Magnitude</span>
                <span role="columnheader">Contribution</span>
                <span role="columnheader">Share of move</span>
              </div>
              {contributionFocus.rows.map((row) => (
                <div className="contribution-focus__row" key={row.instrumentSymbol} role="row">
                  <span className="contribution-focus__symbol" role="cell">
                    {row.instrumentSymbol}
                  </span>
                  <span className="contribution-focus__magnitude" role="cell">
                    <span className="contribution-focus__bar-shell" aria-hidden="true">
                      <span
                        className={`contribution-focus__bar contribution-focus__bar--${row.tone}`}
                        style={{ width: `${row.widthPct}%` }}
                      />
                    </span>
                  </span>
                  <span className={`contribution-focus__value tone-${row.tone}`} role="cell">
                    {formatUsdMoney(row.contributionPnlUsd)}
                  </span>
                  <span className={`contribution-focus__value tone-${row.tone}`} role="cell">
                    {formatSignedPercent(row.contributionPct)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </WorkspaceChartPanel>
    </PortfolioWorkspaceLayout>
  );
}
