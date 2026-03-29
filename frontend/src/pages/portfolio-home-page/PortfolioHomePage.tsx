import { Link, useSearchParams } from "react-router-dom";
import {
  useEffect,
  useState,
} from "react";

import { PortfolioTrendChart } from "../../components/charts/PortfolioTrendChart";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { PortfolioHierarchyTable } from "../../features/portfolio-hierarchy/PortfolioHierarchyTable";
import type {
  PortfolioHierarchyGroupBy,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportScope,
} from "../../core/api/schemas";
import {
  buildHomeMetricCards,
  buildQuantMetricCards,
} from "../../features/portfolio-workspace/overview";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import {
  usePortfolioHierarchyQuery,
  usePortfolioQuantMetricsQuery,
  usePortfolioQuantReportGenerateMutation,
  usePortfolioQuantReportHtmlQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"));
}

export function PortfolioHomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [hierarchyGroupBy, setHierarchyGroupBy] =
    useState<PortfolioHierarchyGroupBy>("sector");
  const [reportScope, setReportScope] = useState<PortfolioQuantReportScope>("portfolio");
  const [reportInstrumentSymbol, setReportInstrumentSymbol] = useState("");
  const [reportValidationError, setReportValidationError] = useState<string | null>(null);
  const [activeReportId, setActiveReportId] = useState<string | null>(null);
  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const summaryQuery = usePortfolioSummaryQuery();
  const timeSeriesQuery = usePortfolioTimeSeriesQuery(selectedPeriod);
  const quantMetricsQuery = usePortfolioQuantMetricsQuery(selectedPeriod);
  const hierarchyQuery = usePortfolioHierarchyQuery(hierarchyGroupBy);
  const quantReportGenerateMutation = usePortfolioQuantReportGenerateMutation();
  const quantReportHtmlQuery = usePortfolioQuantReportHtmlQuery(activeReportId);

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
  const isQuantLoading = quantMetricsQuery.isLoading;
  const isQuantError = quantMetricsQuery.isError;
  const isQuantSuccess = quantMetricsQuery.isSuccess;
  const isQuantEmpty = isQuantSuccess && quantMetricsQuery.data.metrics.length === 0;

  const coreErrorCopy = resolveWorkspaceError(
    summaryQuery.error ||
    timeSeriesQuery.error ||
    hierarchyQuery.error,
    "Home analytics unavailable",
    "Home analytics could not be loaded from persisted workspace data.",
  );
  const quantErrorCopy = resolveWorkspaceError(
    quantMetricsQuery.error,
    "Quant preview unavailable",
    "Quant preview metrics are temporarily unavailable.",
  );
  const quantReportGenerateErrorCopy = resolveWorkspaceError(
    quantReportGenerateMutation.error,
    "Quant report generation failed",
    "The QuantStats report could not be generated for the selected scope.",
  );
  const quantReportPreviewErrorCopy = resolveWorkspaceError(
    quantReportHtmlQuery.error,
    "Quant report preview unavailable",
    "Generated report metadata is available, but the HTML preview could not be loaded.",
  );

  function handlePeriodChange(nextPeriod: "30D" | "90D" | "252D" | "MAX"): void {
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

  const availableInstrumentSymbols = isCoreSuccess
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

  const metricCards = isCoreSuccess
    ? buildHomeMetricCards(summaryQuery.data.rows, timeSeriesQuery.data.points)
    : [];
  const quantMetricCards = isQuantSuccess
    ? buildQuantMetricCards(quantMetricsQuery.data.metrics)
    : [];
  const quantBenchmarkContext = quantMetricsQuery.data?.benchmark_context;
  const omittedMetricIds = quantBenchmarkContext?.omitted_metric_ids || [];
  const omittedMetricsSummary = omittedMetricIds.length > 0
    ? omittedMetricIds.join(", ")
    : "";

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

  async function retryQuantPreview(): Promise<void> {
    await quantMetricsQuery.refetch();
  }

  async function retryQuantReportPreview(): Promise<void> {
    await quantReportHtmlQuery.refetch();
  }

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
                <h2 className="panel__title">Quant metrics</h2>
                <p className="panel__subtitle">
                  QuantStats-derived supplemental preview metrics for {selectedPeriod}. Preview
                  only; risk-context interpretation remains on the Risk route.
                </p>
              </header>
              <div className="panel__body">
                {isQuantLoading ? <LoadingTableSkeleton rows={2} /> : null}

                {isQuantError ? (
                  <ErrorBanner
                    title={quantErrorCopy.title}
                    message={quantErrorCopy.message}
                    variant={quantErrorCopy.variant}
                    actions={
                      <button
                        className="button-primary"
                        onClick={() => void retryQuantPreview()}
                        type="button"
                      >
                        Retry quant preview
                      </button>
                    }
                  />
                ) : null}

                {isQuantSuccess ? (
                  isQuantEmpty ? (
                    <EmptyState
                      title="Quant preview has no metrics for this period"
                      message="QuantStats returned no preview rows for the selected period."
                    />
                  ) : (
                    <>
                      {omittedMetricIds.length > 0 ? (
                        <ErrorBanner
                          title="Optional benchmark metrics omitted"
                          message={
                            quantBenchmarkContext?.omission_reason
                              ? `${quantBenchmarkContext.omission_reason} Omitted: ${omittedMetricsSummary}.`
                              : `Optional benchmark metrics were omitted for this request: ${omittedMetricsSummary}.`
                          }
                          variant="warning"
                        />
                      ) : null}
                      <div className="overview-grid">
                        {quantMetricCards.map((metric) => (
                          <article className="overview-card" key={metric.label}>
                            <span className="overview-card__label">{metric.label}</span>
                            <strong className={`overview-card__value tone-${metric.tone}`}>
                              {metric.value}
                            </strong>
                            <p className="overview-card__copy">{metric.hint}</p>
                          </article>
                        ))}
                      </div>
                    </>
                  )
                ) : null}
              </div>
            </section>

            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Quant report generation</h2>
                <p className="panel__subtitle">
                  Generate bounded QuantStats HTML reports with explicit scope and lifecycle
                  states.
                </p>
              </header>
              <div className="panel__body">
                <div className="transactions-filters">
                  <label className="transactions-filters__field">
                    <span>Report scope</span>
                    <select
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
                    className="button-primary"
                    onClick={() => void generateQuantReport()}
                    type="button"
                  >
                    {quantReportGenerateMutation.isPending
                      ? "Generating report..."
                      : "Generate HTML report"}
                  </button>
                </div>

                {reportValidationError ? (
                  <ErrorBanner
                    title="Quant report request invalid"
                    message={reportValidationError}
                    variant="warning"
                  />
                ) : null}

                {quantReportGenerateMutation.isError ? (
                  <ErrorBanner
                    title={quantReportGenerateErrorCopy.title}
                    message={quantReportGenerateErrorCopy.message}
                    variant={quantReportGenerateErrorCopy.variant}
                  />
                ) : null}

                {quantReportGenerateMutation.data ? (
                  <div className="chart-summary-grid quant-report-summary-grid">
                    <article className="chart-summary-card">
                      <span className="chart-summary-card__label">Scope</span>
                      <strong className="chart-summary-card__value">
                        {quantReportGenerateMutation.data.scope}
                      </strong>
                      <p className="chart-summary-card__copy">
                        Period {quantReportGenerateMutation.data.period}
                      </p>
                    </article>
                    <article className="chart-summary-card chart-summary-card--accent">
                      <span className="chart-summary-card__label">Report id</span>
                      <strong className="chart-summary-card__value">
                        {quantReportGenerateMutation.data.report_id}
                      </strong>
                      <p className="chart-summary-card__copy">
                        Expires {quantReportGenerateMutation.data.expires_at}
                      </p>
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

                {quantReportHtmlQuery.isLoading ? <LoadingTableSkeleton rows={3} /> : null}

                {quantReportHtmlQuery.isError ? (
                  <ErrorBanner
                    title={quantReportPreviewErrorCopy.title}
                    message={quantReportPreviewErrorCopy.message}
                    variant={quantReportPreviewErrorCopy.variant}
                    actions={
                      <button
                        className="button-primary"
                        onClick={() => void retryQuantReportPreview()}
                        type="button"
                      >
                        Retry preview
                      </button>
                    }
                  />
                ) : null}

                {quantReportHtmlQuery.isSuccess ? (
                  <iframe
                    className="quant-report-preview"
                    srcDoc={quantReportHtmlQuery.data}
                    title="Quant report HTML preview"
                  />
                ) : null}
              </div>
            </section>

            <section className="panel">
              <header className="panel__header">
                <h2 className="panel__title">Trend preview</h2>
                <p className="panel__subtitle">
                  Latest points from portfolio time-series with optional benchmark overlays.
                </p>
              </header>
              <div className="panel__body">
                <PortfolioTrendChart points={timeSeriesQuery.data.points} />
              </div>
            </section>

            <PortfolioHierarchyTable
              groupBy={hierarchyGroupBy}
              groups={hierarchyQuery.data.groups}
              onGroupByChange={setHierarchyGroupBy}
            />

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
                    <span className="drilldown-link__label">Analytics + quant preview route</span>
                    <span className="drilldown-link__copy">
                      Open trend and contribution context; preview metrics are supplemental.
                    </span>
                  </Link>
                  <Link
                    className="drilldown-link"
                    to={`/portfolio/risk?period=${selectedPeriod}`}
                  >
                    <span className="drilldown-link__label">Risk interpretation route</span>
                    <span className="drilldown-link__copy">
                      Inspect methodology-sensitive estimators and interpretation context.
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
