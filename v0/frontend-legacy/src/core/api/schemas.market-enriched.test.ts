import {
  describe,
  expect,
  it,
} from "vitest";

import {
  portfolioSummaryResponseSchema,
  portfolioSummaryRowSchema,
} from "./schemas";

describe("portfolio summary market-enriched contract", () => {
  it("requires bounded market-enriched valuation fields on summary rows", () => {
    const legacyLedgerOnlyRow = {
      instrument_symbol: "AAPL",
      open_quantity: "2.000000000",
      open_cost_basis_usd: "1000.00",
      open_lot_count: 2,
      realized_proceeds_usd: "400.00",
      realized_cost_basis_usd: "320.00",
      realized_gain_usd: "80.00",
      dividend_gross_usd: "18.00",
      dividend_taxes_usd: "3.00",
      dividend_net_usd: "15.00",
    };

    const parseResult = portfolioSummaryRowSchema.safeParse(legacyLedgerOnlyRow);
    expect(parseResult.success).toBe(false);
  });

  it("requires explicit pricing snapshot provenance on summary responses", () => {
    const summaryWithoutPricingProvenance = {
      as_of_ledger_at: "2026-03-27T03:00:00Z",
      rows: [
        {
          instrument_symbol: "AAPL",
          open_quantity: "2.000000000",
          open_cost_basis_usd: "1000.00",
          open_lot_count: 2,
          realized_proceeds_usd: "400.00",
          realized_cost_basis_usd: "320.00",
          realized_gain_usd: "80.00",
          dividend_gross_usd: "18.00",
          dividend_taxes_usd: "3.00",
          dividend_net_usd: "15.00",
          latest_close_price_usd: "190.00",
          market_value_usd: "380.00",
          unrealized_gain_usd: "60.00",
          unrealized_gain_pct: "18.75",
        },
      ],
    };

    const parseResult = portfolioSummaryResponseSchema.safeParse(
      summaryWithoutPricingProvenance,
    );
    expect(parseResult.success).toBe(false);
  });
});
