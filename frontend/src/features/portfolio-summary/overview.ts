import Decimal from "decimal.js";

import type { PortfolioSummaryRow } from "../../core/api/schemas";
import {
  compareDecimal,
  parseMoneyDecimal,
  parseQuantityDecimal,
} from "../../core/lib/decimal";

export type PortfolioSummaryOverview = {
  trackedSymbols: number;
  activePositions: number;
  openLots: number;
  realizedGainUsd: string;
  dividendNetUsd: string;
};

const ZERO_DECIMAL = new Decimal(0);

export function buildPortfolioSummaryOverview(
  rows: PortfolioSummaryRow[],
): PortfolioSummaryOverview {
  let activePositions = 0;
  let openLots = 0;
  let realizedGain = ZERO_DECIMAL;
  let dividendNet = ZERO_DECIMAL;

  for (const row of rows) {
    if (compareDecimal(parseQuantityDecimal(row.open_quantity), ZERO_DECIMAL) > 0) {
      activePositions += 1;
    }

    openLots += row.open_lot_count;
    realizedGain = realizedGain.plus(parseMoneyDecimal(row.realized_gain_usd));
    dividendNet = dividendNet.plus(parseMoneyDecimal(row.dividend_net_usd));
  }

  return {
    trackedSymbols: rows.length,
    activePositions,
    openLots,
    realizedGainUsd: realizedGain.toFixed(2),
    dividendNetUsd: dividendNet.toFixed(2),
  };
}
