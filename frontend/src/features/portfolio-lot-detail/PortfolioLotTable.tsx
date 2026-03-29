import type { PortfolioLotDetailRow } from "../../core/api/schemas";
import {
  formatDateLabel,
} from "../../core/lib/dates";
import {
  formatQuantity,
  formatUsdMoney,
  resolveQuantityTone,
} from "../../core/lib/formatters";

type PortfolioLotTableProps = {
  lots: PortfolioLotDetailRow[];
};

export function PortfolioLotTable({ lots }: PortfolioLotTableProps) {
  return (
    <div className="lot-card-grid">
      {lots.map((lot) => {
        const remainingTone = resolveQuantityTone(lot.remaining_qty);
        const lotStatus =
          remainingTone === "positive"
            ? lot.dispositions.length === 0
              ? "Fully open"
              : "Partially realized"
            : "Closed";

        return (
          <article key={lot.lot_id} className="lot-card">
            <div className="lot-card__header">
              <div>
                <div className="symbol-cell__primary">
                  <span className="symbol-chip">Lot #{lot.lot_id}</span>
                  <span className={`status-pill status-pill--${remainingTone}`}>
                    {lotStatus}
                  </span>
                </div>
                <p className="lot-meta">Opened on {formatDateLabel(lot.opened_on)}</p>
              </div>
              <span className="scope-note">
                {lot.dispositions.length} disposition
                {lot.dispositions.length === 1 ? "" : "s"}
              </span>
            </div>
            <div className="lot-card__body">
              <div className="lot-metrics">
                <div className="metric-card">
                  <span className="metric-card__label">Original quantity</span>
                  <span className="metric-card__value">
                    {formatQuantity(lot.original_qty)}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-card__label">Remaining quantity</span>
                  <span className={`metric-card__value tone-${remainingTone}`}>
                    {formatQuantity(lot.remaining_qty)}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-card__label">Total basis</span>
                  <span className="metric-card__value">
                    {formatUsdMoney(lot.total_cost_basis_usd)}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-card__label">Unit basis</span>
                  <span className="metric-card__value">
                    {formatUsdMoney(lot.unit_cost_basis_usd)}
                  </span>
                </div>
              </div>

              {lot.dispositions.length > 0 ? (
                <details className="lot-dispositions" open={lot.dispositions.length === 1}>
                  <summary className="lot-dispositions__summary">
                    <span className="lot-dispositions__title">Disposition history</span>
                    <span className="metric-hint">
                      Expand to inspect matched basis lineage.
                    </span>
                  </summary>
                  <div className="lot-dispositions__header">
                    <p className="definition-copy">
                      Each row links a sell transaction back to the matched cost basis.
                    </p>
                  </div>
                  <div className="table-shell">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Disposition date</th>
                          <th className="numeric">Matched Qty</th>
                          <th className="numeric">Matched Cost</th>
                          <th className="numeric">Sell Gross</th>
                          <th className="numeric">Sell Tx ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lot.dispositions.map((disposition) => (
                          <tr
                            key={`${lot.lot_id}-${disposition.sell_transaction_id}-${disposition.disposition_date}`}
                          >
                            <td>{formatDateLabel(disposition.disposition_date)}</td>
                            <td className="numeric">
                              {formatQuantity(disposition.matched_qty)}
                            </td>
                            <td className="numeric">
                              {formatUsdMoney(disposition.matched_cost_basis_usd)}
                            </td>
                            <td className="numeric">
                              {formatUsdMoney(disposition.sell_gross_amount_usd)}
                            </td>
                            <td className="numeric">
                              {disposition.sell_transaction_id}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              ) : (
                <div className="empty-state empty-state--compact">
                  <h3 className="empty-state__title">No sell-side dispositions</h3>
                  <p className="empty-state__copy">
                    This lot remains fully open in the persisted ledger state.
                  </p>
                </div>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
