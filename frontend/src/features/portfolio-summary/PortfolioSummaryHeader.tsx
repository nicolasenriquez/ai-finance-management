import { TimestampBadge } from "../../components/timestamp-badge/TimestampBadge";
import {
  formatUsdMoney,
  resolveMoneyTone,
} from "../../core/lib/formatters";
import type { PortfolioSummaryOverview } from "./overview";

type PortfolioSummaryHeaderProps = {
  asOfLedgerAt: string;
  overview: PortfolioSummaryOverview;
};

export function PortfolioSummaryHeader({
  asOfLedgerAt,
  overview,
}: PortfolioSummaryHeaderProps) {
  const realizedGainTone = resolveMoneyTone(overview.realizedGainUsd);
  const dividendTone = resolveMoneyTone(overview.dividendNetUsd);

  return (
    <div className="panel">
      <div className="panel__header">
        <div>
          <h2 className="panel__title">Portfolio summary</h2>
          <p className="panel__subtitle">
            Grouped ledger-backed metrics by instrument. No inferred market value
            or FX adjustments in this view.
          </p>
        </div>
        <div className="summary-meta">
          <TimestampBadge value={asOfLedgerAt} />
          <span className="scope-note">Ledger-only v1</span>
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
            <span className="overview-card__label">Open lots</span>
            <strong className="overview-card__value">{overview.openLots}</strong>
            <p className="overview-card__copy">
              Persisted lot count underlying the grouped summary rows.
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
