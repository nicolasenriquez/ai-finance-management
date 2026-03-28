import { TimestampBadge } from "../../components/timestamp-badge/TimestampBadge";
import {
  formatDateTimeLabel,
  formatUtcDateTimeLabel,
} from "../../core/lib/dates";
import {
  formatUsdMoney,
  resolveMoneyTone,
} from "../../core/lib/formatters";
import type { PortfolioSummaryOverview } from "./overview";

type PortfolioSummaryHeaderProps = {
  asOfLedgerAt: string;
  pricingSnapshotKey: string | null;
  pricingSnapshotCapturedAt: string | null;
  overview: PortfolioSummaryOverview;
};

export function PortfolioSummaryHeader({
  asOfLedgerAt,
  pricingSnapshotKey,
  pricingSnapshotCapturedAt,
  overview,
}: PortfolioSummaryHeaderProps) {
  const marketValueTone = resolveMoneyTone(overview.marketValueUsd);
  const unrealizedTone = resolveMoneyTone(overview.unrealizedGainUsd);
  const realizedGainTone = resolveMoneyTone(overview.realizedGainUsd);
  const dividendTone = resolveMoneyTone(overview.dividendNetUsd);
  const hasPricingProvenance =
    pricingSnapshotKey !== null && pricingSnapshotCapturedAt !== null;
  const scopeLabel = hasPricingProvenance
    ? "Market-enriched (USD-only)"
    : "Ledger-only (no open positions)";

  return (
    <div className="panel">
      <div className="panel__header">
        <div>
          <h2 className="panel__title">Portfolio summary</h2>
          <p className="panel__subtitle">
            Grouped ledger-backed metrics with bounded market valuation from one
            persisted pricing snapshot.
          </p>
        </div>
        <div className="summary-meta">
          <TimestampBadge value={asOfLedgerAt} />
          {pricingSnapshotCapturedAt !== null ? (
            <span
              className="timestamp-badge"
              title={
                pricingSnapshotKey === null
                  ? `UTC ${formatUtcDateTimeLabel(pricingSnapshotCapturedAt)}`
                  : `Snapshot ${pricingSnapshotKey} · UTC ${formatUtcDateTimeLabel(
                      pricingSnapshotCapturedAt,
                    )}`
              }
            >
              <span className="timestamp-badge__label">Pricing snapshot</span>
              <strong className="timestamp-badge__value">
                {formatDateTimeLabel(pricingSnapshotCapturedAt)}
              </strong>
            </span>
          ) : null}
          <span className="scope-note">{scopeLabel}</span>
        </div>
      </div>
      <div className="panel__body">
        <div className="overview-grid">
          <article className="overview-card">
            <span className="overview-card__label">Tracked symbols</span>
            <strong className="overview-card__value">{overview.trackedSymbols}</strong>
            <p className="overview-card__copy">One grouped row per canonical instrument.</p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Symbols with open quantity</span>
            <strong className="overview-card__value">{overview.activePositions}</strong>
            <p className="overview-card__copy">
              Active holdings still represented in the current ledger snapshot.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Market-valued symbols</span>
            <strong className="overview-card__value">{overview.marketValuedSymbols}</strong>
            <p className="overview-card__copy">
              Symbols with open quantity and pricing coverage in the selected
              snapshot.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Open lots</span>
            <strong className="overview-card__value">{overview.openLots}</strong>
            <p className="overview-card__copy">
              Persisted lot count underlying the grouped summary rows.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Market value across rows</span>
            <strong className={`overview-card__value tone-${marketValueTone}`}>
              {formatUsdMoney(overview.marketValueUsd)}
            </strong>
            <p className="overview-card__copy">
              Open-position market value from one persisted pricing snapshot.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Unrealized gain across rows</span>
            <strong className={`overview-card__value tone-${unrealizedTone}`}>
              {formatUsdMoney(overview.unrealizedGainUsd)}
            </strong>
            <p className="overview-card__copy">
              Sum of market value minus open cost basis for market-valued rows.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Realized gain across rows</span>
            <strong className={`overview-card__value tone-${realizedGainTone}`}>
              {formatUsdMoney(overview.realizedGainUsd)}
            </strong>
            <p className="overview-card__copy">
              Derived only from the visible grouped analytics returned by the API.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Dividend net across rows</span>
            <strong className={`overview-card__value tone-${dividendTone}`}>
              {formatUsdMoney(overview.dividendNetUsd)}
            </strong>
            <p className="overview-card__copy">
              Cashflow view stays ledger-bound and excludes any market revaluation.
            </p>
          </article>
          <article className="overview-card overview-card--definition">
            <span className="overview-card__label">How to read this screen</span>
            <strong className="overview-card__value">Trust scope before speed</strong>
            <p className="overview-card__copy">
              Use the summary to identify the instrument, then inspect lot detail for
              deterministic cost-basis attribution and sell-side history.
            </p>
          </article>
        </div>
      </div>
    </div>
  );
}
