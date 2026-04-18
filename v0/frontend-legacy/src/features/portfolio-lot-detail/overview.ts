import Decimal from "decimal.js";

import type { PortfolioLotDetailRow } from "../../core/api/schemas";
import { parseMoneyDecimal, parseQuantityDecimal } from "../../core/lib/decimal";

export type PortfolioLotOverview = {
  lotCount: number;
  fullyOpenLots: number;
  dispositionCount: number;
  remainingQuantity: string;
  remainingBasisUsd: string;
};

const ZERO_DECIMAL = new Decimal(0);

export function buildPortfolioLotOverview(
  lots: PortfolioLotDetailRow[],
): PortfolioLotOverview {
  let fullyOpenLots = 0;
  let dispositionCount = 0;
  let remainingQuantity = ZERO_DECIMAL;
  let remainingBasisUsd = ZERO_DECIMAL;

  for (const lot of lots) {
    if (lot.dispositions.length === 0) {
      fullyOpenLots += 1;
    }

    dispositionCount += lot.dispositions.length;
    remainingQuantity = remainingQuantity.plus(parseQuantityDecimal(lot.remaining_qty));
    remainingBasisUsd = remainingBasisUsd.plus(
      parseMoneyDecimal(lot.total_cost_basis_usd),
    );
  }

  return {
    lotCount: lots.length,
    fullyOpenLots,
    dispositionCount,
    remainingQuantity: remainingQuantity.toFixed(9),
    remainingBasisUsd: remainingBasisUsd.toFixed(2),
  };
}
