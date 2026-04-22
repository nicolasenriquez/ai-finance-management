/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
} from "@testing-library/react";
import {
  afterEach,
  describe,
  expect,
  it,
} from "vitest";

import { PortfolioContributionChart } from "./PortfolioContributionChart";
import { PortfolioRiskChart } from "./PortfolioRiskChart";
import type {
  PortfolioContributionRow,
  PortfolioRiskEstimatorMetric,
} from "../../core/api/schemas";

const contributionRows: PortfolioContributionRow[] = [
  {
    instrument_symbol: "AAPL",
    contribution_pnl_usd: "12.00",
    contribution_pct: "1.20",
  },
];

const riskMetrics: PortfolioRiskEstimatorMetric[] = [
  {
    estimator_id: "volatility_annualized",
    value: "0.180000",
    window_days: 30,
    return_basis: "simple",
    annualization_basis: {
      kind: "trading_days",
      value: 252,
    },
    as_of_timestamp: "2026-03-28T00:00:00Z",
    unit: "percent",
    interpretation_band: "caution",
    timeline_series_id: "volatility_annualized",
  },
];

describe("Workspace chart composition fail-first baseline", () => {
  afterEach(() => {
    cleanup();
  });

  it("requires contribution chart to use responsive container contract", () => {
    const { container } = render(
      <PortfolioContributionChart rows={contributionRows} />,
    );

    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("renders redesigned risk-range chart contract", () => {
    const { container } = render(
      <PortfolioRiskChart metrics={riskMetrics} />,
    );

    expect(
      container.querySelector(".risk-range-chart"),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".risk-range-chart__row"),
    ).toBeInTheDocument();
  });
});
