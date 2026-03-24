import { Link, useParams } from "react-router-dom";

import { AppShell } from "../../components/app-shell/AppShell";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { AppApiError } from "../../core/api/errors";
import { PortfolioLotHeader } from "../../features/portfolio-lot-detail/PortfolioLotHeader";
import { PortfolioLotTable } from "../../features/portfolio-lot-detail/PortfolioLotTable";
import { usePortfolioLotDetailQuery } from "../../features/portfolio-lot-detail/hooks";
import { buildPortfolioLotOverview } from "../../features/portfolio-lot-detail/overview";

function resolveLotDetailError(error: unknown): {
  title: string;
  message: string;
  variant: "error" | "warning";
} {
  if (error instanceof AppApiError && error.kind === "not_found") {
    return {
      title: "Instrument not found",
      message:
        error.detail ||
        "The requested instrument was not found in the current portfolio ledger.",
      variant: "warning",
    };
  }

  if (error instanceof AppApiError && error.detail) {
    return {
      title: "Lot detail unavailable",
      message: error.detail,
      variant: "error",
    };
  }

  return {
    title: "Lot detail unavailable",
    message: "The lot-detail view could not be loaded from the current ledger state.",
    variant: "error",
  };
}

function normalizeRouteSymbol(symbol: string | undefined): string {
  return (symbol || "").trim().toUpperCase();
}

export function PortfolioLotDetailPage() {
  const params = useParams();
  const symbol = normalizeRouteSymbol(params.symbol);
  const lotDetailQuery = usePortfolioLotDetailQuery(symbol);
  const errorCopy = resolveLotDetailError(lotDetailQuery.error);

  return (
    <AppShell
      eyebrow="Lot detail"
      title="Lot-level attribution without guesswork."
      description="Inspect persisted lots, remaining basis, and recorded sell-side matches for the selected instrument."
      actions={
        <Link className="button-secondary" to="/portfolio">
          Return to grouped summary
        </Link>
      }
    >
      {lotDetailQuery.isLoading ? <LoadingTableSkeleton rows={4} /> : null}

      {lotDetailQuery.isError ? (
        <ErrorBanner
          title={errorCopy.title}
          message={errorCopy.message}
          variant={errorCopy.variant}
          actions={
            <>
              <button
                className="button-primary"
                onClick={() => void lotDetailQuery.refetch()}
                type="button"
              >
                Retry request
              </button>
              <Link className="button-secondary" to="/portfolio">
                Back to summary
              </Link>
            </>
          }
        />
      ) : null}

      {lotDetailQuery.isSuccess ? (
        <>
          <PortfolioLotHeader
            asOfLedgerAt={lotDetailQuery.data.as_of_ledger_at}
            overview={buildPortfolioLotOverview(lotDetailQuery.data.lots)}
            symbol={lotDetailQuery.data.instrument_symbol}
          />
          {lotDetailQuery.data.lots.length === 0 ? (
            <EmptyState
              title="No lots found for this instrument"
              message="The request resolved to an instrument symbol, but no lot rows were returned by the analytics API."
              actions={
                <Link className="button-secondary" to="/portfolio">
                  Back to summary
                </Link>
              }
            />
          ) : (
            <PortfolioLotTable lots={lotDetailQuery.data.lots} />
          )}
        </>
      ) : null}
    </AppShell>
  );
}
