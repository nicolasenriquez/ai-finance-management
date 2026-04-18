import { Link } from "react-router-dom";

import { TimestampBadge } from "../../components/timestamp-badge/TimestampBadge";
import {
  formatQuantity,
  formatUsdMoney,
} from "../../core/lib/formatters";
import type { PortfolioLotOverview } from "./overview";

type PortfolioLotHeaderProps = {
  symbol: string;
  asOfLedgerAt: string;
  overview: PortfolioLotOverview;
};

export function PortfolioLotHeader({
  symbol,
  asOfLedgerAt,
  overview,
}: PortfolioLotHeaderProps) {
  return (
    <div className="panel">
      <div className="panel__header">
        <div>
          <h2 className="panel__title">Lot detail</h2>
          <p className="panel__subtitle">
            Explainable lot state and sell-side dispositions for{" "}
            <strong>{symbol}</strong>.
          </p>
        </div>
        <div className="summary-meta">
          <TimestampBadge value={asOfLedgerAt} />
          <Link className="button-secondary" to="/portfolio">
            Back to summary
          </Link>
        </div>
      </div>
      <div className="panel__body">
        <div className="overview-grid">
          <article className="overview-card">
            <span className="overview-card__label">Open lots in view</span>
            <strong className="overview-card__value">{overview.lotCount}</strong>
            <p className="overview-card__copy">
              Individual tax lots tied to the canonical symbol returned by the API.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Fully open lots</span>
            <strong className="overview-card__value">{overview.fullyOpenLots}</strong>
            <p className="overview-card__copy">
              Lots with no sell-side consumption in the persisted ledger snapshot.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Remaining quantity</span>
            <strong className="overview-card__value">
              {formatQuantity(overview.remainingQuantity)}
            </strong>
            <p className="overview-card__copy">
              Total still held across all lots for <strong>{symbol}</strong>.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Remaining basis</span>
            <strong className="overview-card__value">
              {formatUsdMoney(overview.remainingBasisUsd)}
            </strong>
            <p className="overview-card__copy">
              Sum of remaining cost basis across every displayed lot.
            </p>
          </article>
          <article className="overview-card">
            <span className="overview-card__label">Recorded dispositions</span>
            <strong className="overview-card__value">{overview.dispositionCount}</strong>
            <p className="overview-card__copy">
              Sell-side matches are shown explicitly; nothing is inferred in the client.
            </p>
          </article>
          <article className="overview-card overview-card--definition">
            <span className="overview-card__label">Review guidance</span>
            <strong className="overview-card__value">Audit lot lineage quickly</strong>
            <p className="overview-card__copy">
              Start with remaining quantity and basis, then open the disposition table to
              confirm which sell transaction consumed each lot segment.
            </p>
          </article>
        </div>
      </div>
    </div>
  );
}
