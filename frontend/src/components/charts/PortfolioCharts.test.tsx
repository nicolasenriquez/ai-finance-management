/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  PortfolioContributionRow,
  PortfolioRiskEstimatorMetric,
  PortfolioTimeSeriesPoint,
} from "../../core/api/schemas";
import { PortfolioContributionChart } from "./PortfolioContributionChart";
import { PortfolioRiskChart } from "./PortfolioRiskChart";
import { PortfolioTrendChart } from "./PortfolioTrendChart";

const trendPoints: PortfolioTimeSeriesPoint[] = [
  {
    captured_at: "2026-03-27T00:00:00Z",
    portfolio_value_usd: "100.00",
    pnl_usd: "0.00",
    benchmark_sp500_value_usd: "100.00",
    benchmark_nasdaq100_value_usd: null,
  },
  {
    captured_at: "2026-03-28T00:00:00Z",
    portfolio_value_usd: "120.00",
    pnl_usd: "20.00",
    benchmark_sp500_value_usd: "110.00",
    benchmark_nasdaq100_value_usd: null,
  },
];

const contributionRows: PortfolioContributionRow[] = [
  {
    instrument_symbol: "AAPL",
    contribution_pnl_usd: "15.00",
    contribution_pct: "4.20",
  },
  {
    instrument_symbol: "VOO",
    contribution_pnl_usd: "-5.00",
    contribution_pct: "-1.40",
  },
];

const riskMetrics: PortfolioRiskEstimatorMetric[] = [
  {
    estimator_id: "beta",
    value: "1.03",
    window_days: 90,
    return_basis: "simple",
    annualization_basis: {
      kind: "trading_days",
      value: 252,
    },
    as_of_timestamp: "2026-03-28T00:00:00Z",
  },
  {
    estimator_id: "volatility_annualized",
    value: "0.10",
    window_days: 90,
    return_basis: "simple",
    annualization_basis: {
      kind: "trading_days",
      value: 252,
    },
    as_of_timestamp: "2026-03-28T00:00:00Z",
  },
];

describe("portfolio workspace chart foundation", () => {
  it("renders Recharts trend visual", () => {
    const { container } = render(<PortfolioTrendChart points={trendPoints} />);
    expect(
      screen.getByRole("img", { name: "Portfolio trend chart" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "S&P 500" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "NASDAQ-100" }),
    ).toBeInTheDocument();
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });

  it("renders Recharts contribution visual", () => {
    const { container } = render(
      <PortfolioContributionChart rows={contributionRows} />,
    );
    expect(
      screen.getByRole("img", { name: "Contribution by symbol chart" }),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("renders Recharts risk visual", () => {
    render(<PortfolioRiskChart metrics={riskMetrics} />);
    expect(screen.getByRole("img", { name: "Risk metrics chart" })).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();
    expect(screen.getByText("Volatility Annualized")).toBeInTheDocument();
  });
});
