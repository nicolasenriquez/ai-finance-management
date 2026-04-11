import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { WorkspacePrimaryJobPanel } from "../../components/workspace-layout/WorkspacePrimaryJobPanel";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
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
            <PortfolioSummaryHeader
              asOfLedgerAt={summaryQuery.data.as_of_ledger_at}
              pricingSnapshotKey={summaryQuery.data.pricing_snapshot_key}
              pricingSnapshotCapturedAt={summaryQuery.data.pricing_snapshot_captured_at}
              overview={buildPortfolioSummaryOverview(summaryQuery.data.rows)}
            />
            <PortfolioSummaryTable rows={summaryQuery.data.rows} />
          </>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
