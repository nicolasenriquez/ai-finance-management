/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import type { ReactNode } from "react";
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type { PortfolioTimeSeriesPoint } from "../../core/api/schemas";
import { PortfolioTrendChart } from "./PortfolioTrendChart";

vi.mock("recharts", () => {
  return {
    CartesianGrid: () => null,
    Line: () => null,
    LineChart: ({ children }: { children?: ReactNode }) => <div>{children}</div>,
    ResponsiveContainer: ({ children }: { children?: ReactNode }) => (
      <div className="recharts-responsive-container">{children}</div>
    ),
    Tooltip: ({ content }: { content?: (raw: unknown) => ReactNode }) => (
      <div>
        {content?.({
          active: true,
          payload: [
            {
              payload: {
                capturedAt: "2026-03-28T00:00:00Z",
                portfolioValue: 120.0,
                pnl: 20.0,
                trendline: 114.0,
                benchmarkSp500: 111.0,
                benchmarkNasdaq100: 109.0,
              },
            },
          ],
        })}
      </div>
    ),
    XAxis: () => null,
    YAxis: () => null,
  };
});

const trendPoints: PortfolioTimeSeriesPoint[] = [
  {
    captured_at: "2026-03-27T00:00:00Z",
    portfolio_value_usd: "100.00",
    pnl_usd: "0.00",
    benchmark_sp500_value_usd: "100.00",
    benchmark_nasdaq100_value_usd: "100.00",
  },
  {
    captured_at: "2026-03-28T00:00:00Z",
    portfolio_value_usd: "120.00",
    pnl_usd: "20.00",
    benchmark_sp500_value_usd: "111.00",
    benchmark_nasdaq100_value_usd: "109.00",
  },
];

describe("PortfolioTrendChart explainability fail-first baseline", () => {
  afterEach(() => {
    cleanup();
  });

  it("does not allow tooltip-only dead workflow actions", () => {
    render(<PortfolioTrendChart points={trendPoints} />);

    expect(screen.queryByRole("button", { name: "Analyze Risk" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Export CSV" })).toBeNull();
  });

  it("requires explainability affordance for tooltip metrics", () => {
    render(<PortfolioTrendChart points={trendPoints} />);

    expect(
      screen.getByRole("button", { name: /explain unrealized p&l vs cost basis/i }),
    ).toBeInTheDocument();
  });
});
