import type { KeyboardEvent } from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  formatQuantity,
  formatUsdMoney,
  resolveMoneyTone,
  resolveQuantityTone,
} from "../../core/lib/formatters";
import type { PortfolioSummaryRow } from "../../core/api/schemas";

type PortfolioSummaryTableProps = {
  rows: PortfolioSummaryRow[];
};

export function PortfolioSummaryTable({ rows }: PortfolioSummaryTableProps) {
  const navigate = useNavigate();

  function openLotDetail(symbol: string): void {
    void navigate(`/portfolio/${encodeURIComponent(symbol)}`);
  }

  function handleRowKeyDown(
    event: KeyboardEvent<HTMLTableRowElement>,
    symbol: string,
  ): void {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    openLotDetail(symbol);
  }

  return (
    <div className="panel">
      <div className="panel__body table-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th>Instrument</th>
              <th className="numeric">Open Qty</th>
              <th className="numeric">Open Basis</th>
              <th className="numeric">Open Lots</th>
              <th className="numeric">Realized Proceeds</th>
              <th className="numeric">Realized Cost</th>
              <th className="numeric">Realized Gain</th>
              <th className="numeric">Dividend Net</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const quantityTone = resolveQuantityTone(row.open_quantity);
              const realizedTone = resolveMoneyTone(row.realized_gain_usd);
              const dividendTone = resolveMoneyTone(row.dividend_net_usd);
              const positionLabel =
                quantityTone === "positive" ? "Open position" : "Closed position";

              return (
                <tr
                  key={row.instrument_symbol}
                  aria-label={`Open lot detail for ${row.instrument_symbol}`}
                  className="data-table__row data-table__row--interactive"
                  onClick={() => openLotDetail(row.instrument_symbol)}
                  onKeyDown={(event) => handleRowKeyDown(event, row.instrument_symbol)}
                  role="link"
                  tabIndex={0}
                >
                  <td>
                    <div className="symbol-cell">
                      <div className="symbol-cell__primary">
                        <span className="symbol-chip">{row.instrument_symbol}</span>
                        <span className={`status-pill status-pill--${quantityTone}`}>
                          {positionLabel}
                        </span>
                      </div>
                      <span className="metric-hint">
                        Ledger-backed grouped analytics
                      </span>
                    </div>
                  </td>
                  <td className="numeric">{formatQuantity(row.open_quantity)}</td>
                  <td className="numeric">
                    {formatUsdMoney(row.open_cost_basis_usd)}
                  </td>
                  <td className="numeric">{row.open_lot_count}</td>
                  <td className="numeric">
                    {formatUsdMoney(row.realized_proceeds_usd)}
                  </td>
                  <td className="numeric">
                    {formatUsdMoney(row.realized_cost_basis_usd)}
                  </td>
                  <td className={`numeric tone-${realizedTone}`}>
                    {formatUsdMoney(row.realized_gain_usd)}
                  </td>
                  <td className={`numeric tone-${dividendTone}`}>
                    {formatUsdMoney(row.dividend_net_usd)}
                  </td>
                  <td>
                    <span className="row-link">Inspect lots</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
