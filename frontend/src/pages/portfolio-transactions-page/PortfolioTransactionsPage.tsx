import { Link } from "react-router-dom";
import { useMemo, useState } from "react";

import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { formatDateTimeLabel } from "../../core/lib/dates";
import { formatQuantity, formatUsdMoney } from "../../core/lib/formatters";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import { usePortfolioTransactionsQuery } from "../../features/portfolio-workspace/hooks";
import {
  filterTransactions,
  sortTransactionsDeterministically,
} from "../../features/portfolio-workspace/overview";

export function PortfolioTransactionsPage() {
  const [symbolFilter, setSymbolFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("all");
  const transactionsQuery = usePortfolioTransactionsQuery();
  const isLoading = transactionsQuery.isLoading;
  const isError = transactionsQuery.isError;
  const isSuccess = transactionsQuery.isSuccess;
  const orderedEvents = useMemo(
    () =>
      isSuccess
        ? sortTransactionsDeterministically(transactionsQuery.data.events)
        : [],
    [isSuccess, transactionsQuery.data?.events],
  );
  const filteredEvents = useMemo(
    () => filterTransactions(orderedEvents, symbolFilter, eventTypeFilter),
    [eventTypeFilter, orderedEvents, symbolFilter],
  );
  const isEmpty = isSuccess && filteredEvents.length === 0;

  const errorCopy = resolveWorkspaceError(
    transactionsQuery.error,
    "Transactions route unavailable",
    "Transactions data could not be loaded from the ledger-history scope.",
  );

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Transactions route"
      title="Ledger event history"
      description="v1 route remains scoped to ledger events only. Market-refresh diagnostics are deferred."
      actions={
        <Link className="button-secondary" to="/portfolio/home">
          Back to home
        </Link>
      }
      freshnessTimestamp={transactionsQuery.data?.as_of_ledger_at}
      scopeLabel="Ledger events only (v1)"
      provenanceLabel="Transactions route placeholder feed"
    >
      {isLoading ? <LoadingTableSkeleton rows={5} /> : null}

      {isError ? (
        <ErrorBanner
          title={errorCopy.title}
          message={errorCopy.message}
          variant={errorCopy.variant}
          actions={
            <button
              className="button-primary"
              onClick={() => void transactionsQuery.refetch()}
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
            title="No ledger events available yet"
            message="Transactions v1 is active, but no ledger events were returned for display."
          />
        ) : (
          <section className="panel">
            <header className="panel__header">
              <h2 className="panel__title">Transactions</h2>
              <p className="panel__subtitle">
                Deterministic newest-first ordering across ledger events.
              </p>
            </header>
            <div className="panel__body">
              <div className="transactions-filters">
                <label className="transactions-filters__field">
                  <span>Symbol</span>
                  <input
                    className="transactions-filters__input"
                    onChange={(event) => setSymbolFilter(event.currentTarget.value)}
                    placeholder="Filter symbol"
                    type="text"
                    value={symbolFilter}
                  />
                </label>
                <label className="transactions-filters__field">
                  <span>Type</span>
                  <select
                    aria-label="Filter transaction event type"
                    className="transactions-filters__select"
                    onChange={(event) => setEventTypeFilter(event.currentTarget.value)}
                    value={eventTypeFilter}
                  >
                    <option value="all">All</option>
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                    <option value="dividend">Dividend</option>
                  </select>
                </label>
              </div>

              <div className="table-shell">
                <table className="data-table" aria-label="Transactions list">
                  <thead>
                    <tr>
                      <th>Posted at</th>
                      <th>Symbol</th>
                      <th>Event type</th>
                      <th className="numeric">Quantity</th>
                      <th className="numeric">Cash amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEvents.map((event) => (
                      <tr className="data-table__row" key={event.id}>
                        <td>{formatDateTimeLabel(event.posted_at)}</td>
                        <td>{event.instrument_symbol}</td>
                        <td>{event.event_type}</td>
                        <td className="numeric">{formatQuantity(event.quantity)}</td>
                        <td className="numeric">{formatUsdMoney(event.cash_amount_usd)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
