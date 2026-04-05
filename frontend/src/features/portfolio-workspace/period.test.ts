import {
  describe,
  expect,
  it,
} from "vitest";

import {
  PORTFOLIO_CHART_PERIOD_OPTIONS,
  isPortfolioChartPeriod,
  resolvePortfolioChartPeriod,
} from "./period";

describe("portfolio workspace period helpers", () => {
  it("keeps chart period options constrained to backend-supported values", () => {
    expect(PORTFOLIO_CHART_PERIOD_OPTIONS).toEqual([
      "30D",
      "90D",
      "6M",
      "252D",
      "YTD",
      "MAX",
    ]);
  });

  it("detects supported chart period values", () => {
    expect(isPortfolioChartPeriod("30D")).toBe(true);
    expect(isPortfolioChartPeriod("6M")).toBe(true);
    expect(isPortfolioChartPeriod("YTD")).toBe(true);
    expect(isPortfolioChartPeriod("MAX")).toBe(true);
    expect(isPortfolioChartPeriod("45D")).toBe(false);
  });

  it("normalizes unsupported period values to deterministic fallback", () => {
    expect(resolvePortfolioChartPeriod("BAD")).toBe("30D");
    expect(resolvePortfolioChartPeriod(undefined, "252D")).toBe("252D");
  });
});
