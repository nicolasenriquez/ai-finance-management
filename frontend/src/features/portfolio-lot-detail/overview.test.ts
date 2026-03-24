import {
  describe,
  expect,
  it,
} from "vitest";

import { buildPortfolioLotOverview } from "./overview";

describe("buildPortfolioLotOverview", () => {
  it("summarizes lots from the API without inventing unsupported values", () => {
    const overview = buildPortfolioLotOverview([
      {
        lot_id: 1,
        opened_on: "2026-01-10",
        original_qty: "2.000000000",
        remaining_qty: "1.250000000",
        total_cost_basis_usd: "150.00",
        unit_cost_basis_usd: "120.000000000",
        dispositions: [
          {
            sell_transaction_id: 11,
            disposition_date: "2026-02-05",
            matched_qty: "0.750000000",
            matched_cost_basis_usd: "90.00",
            sell_gross_amount_usd: "100.00",
          },
        ],
      },
      {
        lot_id: 2,
        opened_on: "2026-02-20",
        original_qty: "1.000000000",
        remaining_qty: "1.000000000",
        total_cost_basis_usd: "110.00",
        unit_cost_basis_usd: "110.000000000",
        dispositions: [],
      },
    ]);

    expect(overview).toEqual({
      lotCount: 2,
      fullyOpenLots: 1,
      dispositionCount: 1,
      remainingQuantity: "2.250000000",
      remainingBasisUsd: "260.00",
    });
  });
});
