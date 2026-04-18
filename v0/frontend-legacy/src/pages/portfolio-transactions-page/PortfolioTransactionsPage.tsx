import { Link } from "react-router-dom";
import { useMemo, useState } from "react";

import { EmptyState } from "../../components/empty-state/EmptyState";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { WorkspacePrimaryJobPanel } from "../../components/workspace-layout/WorkspacePrimaryJobPanel";
import { WorkspaceStateBanner } from "../../components/workspace-layout/WorkspaceStateBanner";
import { formatDateTimeLabel } from "../../core/lib/dates";
import { formatQuantity, formatUsdMoney } from "../../core/lib/formatters";
import { getCoreTenEntriesForRoute } from "../../features/portfolio-workspace/core-ten-catalog";
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
  const transactionsCoreTenMetrics = getCoreTenEntriesForRoute("home");
  const operatingPulse = useMemo(() => {
    const totalCashMagnitudeUsd = filteredEvents.reduce((accumulator, event) => {
      return accumulator + Math.abs(Number(event.cash_amount_usd));
    }, 0);
    const buyCount = filteredEvents.filter((event) => event.event_type === "buy").length;
    const sellCount = filteredEvents.filter((event) => event.event_type === "sell").length;
    const dividendCount = filteredEvents.filter(
      (event) => event.event_type === "dividend",
    ).length;
    return {
      totalCashMagnitudeUsd,
      buyCount,
      sellCount,
      dividendCount,
      latestPostedAt: filteredEvents[0]?.posted_at || null,
    };
  }, [filteredEvents]);
  const isEmpty = isSuccess && filteredEvents.length === 0;

  const errorCopy = resolveWorkspaceError(
    transactionsQuery.error,
    "Transactions route unavailable",
    "Transactions data could not be loaded from the ledger-history scope.",
  );

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Transactions route"
      title="Cash and ledger operating narrative"
      description="Cash/Transactions lens focused on deterministic ledger events, operating cash deltas, and concise filterable history."
      actions={
        <Link className="button-secondary" to="/portfolio/dashboard">
          Back to dashboard
        </Link>
      }
      freshnessTimestamp={transactionsQuery.data?.as_of_ledger_at}
      scopeLabel="Ledger events only (v1)"
      provenanceLabel="Persisted portfolio transactions API"
    >
      <WorkspacePrimaryJobPanel
        routeLabel="Cash/Transactions"
        jobTitle="Operating-console cashflow triage"
        jobDescription="Start with deterministic event flow to verify cash deployment, exits, and income receipts before deeper portfolio diagnostics."
        decisionTags={["income_monitoring", "allocation_review"]}
        coreTenMetrics={transactionsCoreTenMetrics}
        questionKey="cash-event-operating-console"
        widgetId="transactions-operating-job"
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
          <>
            <WorkspaceChartPanel
              title="Cashflow operating pulse"
              subtitle="Hero insight for latest event mix and cash magnitude before row-level scan."
              shortDescription="Operating-console summary for current filters."
              longDescription="Use this pulse to validate whether event mix and cash movement align with expected operating posture before stepping into individual ledger rows."
              hierarchy="hero"
              viewportRole="hero-insight"
              questionKey="transactions-ledger-operating-pulse"
              widgetId="transactions-ledger-pulse"
            >
              <div className="chart-summary-grid">
                <article className="chart-summary-card">
                  <span className="chart-summary-card__label">Filtered events</span>
                  <strong className="chart-summary-card__headline">{filteredEvents.length}</strong>
                  <p className="chart-summary-card__copy">
                    Latest event{" "}
                    {operatingPulse.latestPostedAt
                      ? formatDateTimeLabel(operatingPulse.latestPostedAt)
                      : "n/a"}
                    .
                  </p>
                </article>
                <article className="chart-summary-card chart-summary-card--signal">
                  <span className="chart-summary-card__label">Cash magnitude</span>
                  <strong className="chart-summary-card__headline">
                    {formatUsdMoney(operatingPulse.totalCashMagnitudeUsd.toFixed(2))}
                  </strong>
                  <p className="chart-summary-card__copy">
                    Sum of absolute cash movement in current filtered ledger.
                  </p>
                </article>
                <article className="chart-summary-card chart-summary-card--accent">
                  <span className="chart-summary-card__label">Event mix</span>
                  <strong className="chart-summary-card__headline">
                    B {operatingPulse.buyCount} · S {operatingPulse.sellCount} · D{" "}
                    {operatingPulse.dividendCount}
                  </strong>
                  <p className="chart-summary-card__copy">
                    Buy, sell, and dividend breakdown for current filters.
                  </p>
                </article>
              </div>
            </WorkspaceChartPanel>

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
          </>
        )
      ) : null}
    </PortfolioWorkspaceLayout>
  );
}
