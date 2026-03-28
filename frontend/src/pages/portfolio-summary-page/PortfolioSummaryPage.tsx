import { AppApiError } from "../../core/api/errors";
import { AppShell } from "../../components/app-shell/AppShell";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioSummaryHeader } from "../../features/portfolio-summary/PortfolioSummaryHeader";
import { PortfolioSummaryTable } from "../../features/portfolio-summary/PortfolioSummaryTable";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import { buildPortfolioSummaryOverview } from "../../features/portfolio-summary/overview";

function resolveSummaryErrorMessage(error: unknown): string {
  if (error instanceof AppApiError && error.detail) {
    return error.detail;
  }

  return "The portfolio summary could not be loaded from the current ledger state.";
}

export function PortfolioSummaryPage() {
  const summaryQuery = usePortfolioSummaryQuery();

  return (
    <AppShell
      eyebrow="Portfolio analytics"
      title="Portfolio ledger at a glance."
      description="Market-enriched valuation with explicit pricing snapshot provenance."
    >
      {summaryQuery.isLoading ? <LoadingTableSkeleton rows={6} /> : null}

      {summaryQuery.isError ? (
        <ErrorBanner
          title="Summary unavailable"
          message={resolveSummaryErrorMessage(summaryQuery.error)}
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

      {summaryQuery.isSuccess ? (
        <>
          <PortfolioSummaryHeader
            asOfLedgerAt={summaryQuery.data.as_of_ledger_at}
            pricingSnapshotKey={summaryQuery.data.pricing_snapshot_key}
            pricingSnapshotCapturedAt={summaryQuery.data.pricing_snapshot_captured_at}
            overview={buildPortfolioSummaryOverview(summaryQuery.data.rows)}
          />
          {summaryQuery.data.rows.length === 0 ? (
            <EmptyState
              title="No portfolio ledger activity found"
              message="The analytics API returned no grouped rows. Confirm that persisted ledger state exists before using this view."
            />
          ) : (
            <PortfolioSummaryTable rows={summaryQuery.data.rows} />
          )}
        </>
      ) : null}
    </AppShell>
  );
}
