import {
  describe,
  expect,
  it,
} from "vitest";

import { buildPortfolioSummaryOverview } from "./overview";

describe("buildPortfolioSummaryOverview", () => {
  it("aggregates grouped summary rows without losing decimal precision intent", () => {
    const overview = buildPortfolioSummaryOverview([
      {
        instrument_symbol: "AAPL",
        open_quantity: "2.500000000",
        open_cost_basis_usd: "500.00",
        open_lot_count: 2,
        realized_proceeds_usd: "120.00",
        realized_cost_basis_usd: "100.00",
        realized_gain_usd: "20.00",
        dividend_gross_usd: "5.00",
        dividend_taxes_usd: "1.00",
        dividend_net_usd: "4.00",
        latest_close_price_usd: "230.00",
        market_value_usd: "575.00",
        unrealized_gain_usd: "75.00",
        unrealized_gain_pct: "15.00",
      },
      {
        instrument_symbol: "MSFT",
        open_quantity: "0.000000000",
        open_cost_basis_usd: "0.00",
        open_lot_count: 0,
        realized_proceeds_usd: "80.00",
        realized_cost_basis_usd: "95.00",
        realized_gain_usd: "-15.00",
        dividend_gross_usd: "0.00",
        dividend_taxes_usd: "0.00",
        dividend_net_usd: "0.00",
        latest_close_price_usd: null,
        market_value_usd: null,
        unrealized_gain_usd: null,
        unrealized_gain_pct: null,
      },
    ]);

    expect(overview).toEqual({
      trackedSymbols: 2,
      activePositions: 1,
      marketValuedSymbols: 1,
      openLots: 2,
      marketValueUsd: "575.00",
      unrealizedGainUsd: "75.00",
      realizedGainUsd: "5.00",
      dividendNetUsd: "4.00",
    });
  });
});
