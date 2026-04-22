import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { WorkspacePrimaryJobPanel } from "../../components/workspace-layout/WorkspacePrimaryJobPanel";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import { formatUsdMoney } from "../../core/lib/formatters";
import { formatPricingSnapshotProvenanceLabel } from "../../core/lib/provenance";
import { getCoreTenEntriesForRoute } from "../../features/portfolio-workspace/core-ten-catalog";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import { PortfolioSummaryHeader } from "../../features/portfolio-summary/PortfolioSummaryHeader";
import { PortfolioSummaryTable } from "../../features/portfolio-summary/PortfolioSummaryTable";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import { buildPortfolioSummaryOverview } from "../../features/portfolio-summary/overview";

export function PortfolioHoldingsPage() {
  const summaryQuery = usePortfolioSummaryQuery();
  const isLoading = summaryQuery.isLoading;
  const isError = summaryQuery.isError;
  const isSuccess = summaryQuery.isSuccess;
  const isEmpty = isSuccess && summaryQuery.data.rows.length === 0;
  const errorCopy = resolveWorkspaceError(
    summaryQuery.error,
    "Holdings unavailable",
    "Holdings data could not be loaded from persisted summary rows.",
  );
  const holdingsCoreTenMetrics = getCoreTenEntriesForRoute("home");
  const holdingsOverview = isSuccess
    ? buildPortfolioSummaryOverview(summaryQuery.data.rows)
    : null;

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Holdings lens"
      title="Holdings and lot structure"
      description="Deterministic holdings table with direct lot drill-down links and valuation provenance."
      freshnessTimestamp={summaryQuery.data?.as_of_ledger_at}
      scopeLabel="Grouped holdings from persisted ledger + pricing snapshots"
      provenanceLabel={
        summaryQuery.data?.pricing_snapshot_key
          ? formatPricingSnapshotProvenanceLabel(summaryQuery.data.pricing_snapshot_key)
          : "Persisted portfolio summary"
      }
      provenanceTooltip={summaryQuery.data?.pricing_snapshot_key || undefined}
    >
      <WorkspacePrimaryJobPanel
        routeLabel="Holdings"
        jobTitle="Holdings structure and lot traceability"
        jobDescription="Validate holdings concentration and lot-level attribution before tactical risk or rebalancing decisions."
        decisionTags={["allocation_review", "risk_posture"]}
        coreTenMetrics={holdingsCoreTenMetrics}
        questionKey="holdings-allocation-ledger"
        widgetId="holdings-ledger-snapshot"
        viewportRole="dominant-job"
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
              onClick={() => void summaryQuery.refetch()}
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
            title="No holdings are available yet"
            message="The holdings summary returned no rows for the current persisted scope."
          />
        ) : (
          <>
            {holdingsOverview ? (
              <WorkspaceChartPanel
                title="Holdings ledger pulse"
                subtitle="Hero insight summarizing active positions, market value, and unrealized posture before row-level scan."
                shortDescription="Ledger-first operating pulse for current holdings scope."
                longDescription="This hero insight anchors first-view interpretation before navigating through individual rows and lots."
                hierarchy="hero"
                viewportRole="hero-insight"
                questionKey="holdings-ledger-operating-pulse"
                widgetId="holdings-ledger-pulse"
              >
                <div className="chart-summary-grid">
                  <article className="chart-summary-card">
                    <span className="chart-summary-card__label">Active positions</span>
                    <strong className="chart-summary-card__headline">
                      {holdingsOverview.activePositions}
                    </strong>
                    <p className="chart-summary-card__copy">
                      Out of {holdingsOverview.trackedSymbols} tracked symbols.
                    </p>
                  </article>
                  <article className="chart-summary-card chart-summary-card--signal">
                    <span className="chart-summary-card__label">Market value</span>
                    <strong className="chart-summary-card__headline">
                      {formatUsdMoney(holdingsOverview.marketValueUsd)}
                    </strong>
                    <p className="chart-summary-card__copy">
                      Portfolio-level holdings value in current scope.
                    </p>
                  </article>
                  <article className="chart-summary-card chart-summary-card--accent">
                    <span className="chart-summary-card__label">Unrealized gain</span>
                    <strong className="chart-summary-card__headline">
                      {formatUsdMoney(holdingsOverview.unrealizedGainUsd)}
                    </strong>
                    <p className="chart-summary-card__copy">
                      Open-position gain/loss before lot-level drill-down.
                    </p>
                  </article>
                </div>
              </WorkspaceChartPanel>
            ) : null}

            <PortfolioSummaryHeader
              asOfLedgerAt={summaryQuery.data.as_of_ledger_at}
              pricingSnapshotKey={summaryQuery.data.pricing_snapshot_key}
              pricingSnapshotCapturedAt={summaryQuery.data.pricing_snapshot_captured_at}
              overview={holdingsOverview || buildPortfolioSummaryOverview(summaryQuery.data.rows)}
            />
            <PortfolioSummaryTable rows={summaryQuery.data.rows} />
          </>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
