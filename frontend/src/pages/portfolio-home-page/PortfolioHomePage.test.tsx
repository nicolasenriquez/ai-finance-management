/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import { ThemeProvider } from "../../app/theme";
import { AppApiError } from "../../core/api/errors";
import type {
  PortfolioHealthSynthesisResponse,
  PortfolioHierarchyResponse,
  PortfolioSummaryResponse,
  PortfolioTimeSeriesResponse,
} from "../../core/api/schemas";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import {
  usePortfolioHealthSynthesisQuery,
  usePortfolioHierarchyQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";
import { PortfolioHomePage } from "./PortfolioHomePage";

vi.mock("../../features/portfolio-summary/hooks", () => ({
  usePortfolioSummaryQuery: vi.fn(),
}));

vi.mock("../../features/portfolio-workspace/hooks", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-workspace/hooks")
  >("../../features/portfolio-workspace/hooks");
  return {
    ...actual,
    usePortfolioHealthSynthesisQuery: vi.fn(),
    usePortfolioHierarchyQuery: vi.fn(),
    usePortfolioTimeSeriesQuery: vi.fn(),
  };
});

type QueryState<TData> = {
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  data?: TData;
  error?: unknown;
  refetch: () => Promise<unknown>;
};

const mockedUsePortfolioSummaryQuery = vi.mocked(usePortfolioSummaryQuery);
const mockedUsePortfolioHierarchyQuery = vi.mocked(usePortfolioHierarchyQuery);
const mockedUsePortfolioTimeSeriesQuery = vi.mocked(usePortfolioTimeSeriesQuery);
const mockedUsePortfolioHealthSynthesisQuery = vi.mocked(usePortfolioHealthSynthesisQuery);

const summaryResponse: PortfolioSummaryResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  pricing_snapshot_key: "snapshot-key",
  pricing_snapshot_captured_at: "2026-03-28T00:00:00Z",
  rows: [
    {
      instrument_symbol: "AAPL",
      open_quantity: "1.000000000",
      open_cost_basis_usd: "100.00",
      open_lot_count: 1,
      realized_proceeds_usd: "0.00",
      realized_cost_basis_usd: "0.00",
      realized_gain_usd: "0.00",
      dividend_gross_usd: "0.00",
      dividend_taxes_usd: "0.00",
      dividend_net_usd: "0.00",
      latest_close_price_usd: "120.00",
      market_value_usd: "120.00",
      unrealized_gain_usd: "20.00",
      unrealized_gain_pct: "20.00",
    },
  ],
};

const timeSeriesResponse: PortfolioTimeSeriesResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  period: "30D",
  frequency: "1D",
  timezone: "UTC",
  points: [
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
  ],
};

const hierarchyResponse: PortfolioHierarchyResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  group_by: "sector",
  pricing_snapshot_key: "snapshot-key",
  pricing_snapshot_captured_at: "2026-03-28T00:00:00Z",
  groups: [
    {
      group_key: "Technology",
      group_label: "Technology",
      asset_count: 1,
      total_market_value_usd: "120.00",
      total_profit_loss_usd: "20.00",
      total_change_pct: "20.00",
      assets: [
        {
          instrument_symbol: "AAPL",
          sector_label: "Technology",
          open_quantity: "1.000000000",
          open_cost_basis_usd: "100.00",
          avg_price_usd: "100.00",
          current_price_usd: "120.00",
          market_value_usd: "120.00",
          profit_loss_usd: "20.00",
          change_pct: "20.00",
          lot_count: 1,
          lots: [
            {
              lot_id: 1,
              opened_on: "2026-03-20",
              original_qty: "1.000000000",
              remaining_qty: "1.000000000",
              unit_cost_basis_usd: "100.00",
              total_cost_basis_usd: "100.00",
              market_value_usd: "120.00",
              profit_loss_usd: "20.00",
            },
          ],
        },
      ],
    },
  ],
};

const healthResponse: PortfolioHealthSynthesisResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  scope: "portfolio",
  instrument_symbol: null,
  period: "30D",
  profile_posture: "balanced",
  health_score: 74,
  health_label: "healthy",
  threshold_policy_version: "health_v1_20260330",
  pillars: [
    {
      pillar_id: "growth",
      label: "Growth",
      score: 80,
      status: "favorable",
      metrics: [
        {
          metric_id: "cagr",
          label: "CAGR",
          value_display: "+14.00%",
          score: 80,
          contribution: "supporting",
        },
      ],
    },
    {
      pillar_id: "risk",
      label: "Risk",
      score: 58,
      status: "caution",
      metrics: [],
    },
    {
      pillar_id: "risk_adjusted_quality",
      label: "Risk-adjusted quality",
      score: 72,
      status: "favorable",
      metrics: [],
    },
    {
      pillar_id: "resilience",
      label: "Resilience",
      score: 68,
      status: "caution",
      metrics: [],
    },
  ],
  key_drivers: [
    {
      metric_id: "cagr",
      label: "CAGR",
      direction: "supporting",
      impact_points: 60,
      rationale: "Growth output is strong versus long-term target bands.",
      value_display: "+14.00%",
    },
  ],
  health_caveats: ["Health synthesis supports interpretation and is not financial advice."],
  core_metric_ids: ["cagr", "max_drawdown", "sharpe_ratio"],
  advanced_metric_ids: ["value_at_risk_95"],
};

function installMatchMediaMock(prefersDark: boolean): void {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: vi.fn().mockImplementation((query: string): MediaQueryList => {
      const matches =
        query === "(prefers-color-scheme: dark)" ? prefersDark : false;
      return {
        matches,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(() => false),
        addListener: vi.fn(),
        removeListener: vi.fn(),
      };
    }),
  });
}

function setSummaryState(state: Partial<QueryState<PortfolioSummaryResponse>>): void {
  const queryState: QueryState<PortfolioSummaryResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioSummaryQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioSummaryQuery>,
  );
}

function setTimeSeriesState(
  state: Partial<QueryState<PortfolioTimeSeriesResponse>>,
): void {
  const queryState: QueryState<PortfolioTimeSeriesResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioTimeSeriesQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioTimeSeriesQuery>,
  );
}

function setHierarchyState(
  state: Partial<QueryState<PortfolioHierarchyResponse>>,
): void {
  const queryState: QueryState<PortfolioHierarchyResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioHierarchyQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioHierarchyQuery>,
  );
}

function setHealthState(
  state: Partial<QueryState<PortfolioHealthSynthesisResponse>>,
): void {
  const queryState: QueryState<PortfolioHealthSynthesisResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioHealthSynthesisQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioHealthSynthesisQuery>,
  );
}

function renderHomePage(path = "/portfolio/home") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <PortfolioHomePage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioHomePage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    installMatchMediaMock(false);
    setHealthState({
      isSuccess: true,
      data: healthResponse,
    });
  });

  it("renders loading state while home analytics requests are pending", () => {
    setSummaryState({ isLoading: true });
    setTimeSeriesState({ isLoading: true });
    setHierarchyState({ isLoading: true });

    const { container } = renderHomePage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("renders empty state when either summary rows, trend points, or hierarchy groups are empty", () => {
    setSummaryState({
      isSuccess: true,
      data: { ...summaryResponse, rows: [] },
    });
    setTimeSeriesState({
      isSuccess: true,
      data: timeSeriesResponse,
    });
    setHierarchyState({
      isSuccess: true,
      data: hierarchyResponse,
    });

    renderHomePage();

    expect(
      screen.getByRole("heading", { name: "Home view has no portfolio context yet" }),
    ).toBeInTheDocument();
  });

  it("maps not-found responses to explicit warning error state", () => {
    setSummaryState({
      isError: true,
      error: new AppApiError("Missing scope", {
        kind: "not_found",
        detail: "Home analytics endpoint was not found.",
      }),
    });
    setTimeSeriesState({ isSuccess: false });
    setHierarchyState({ isSuccess: false });

    renderHomePage();

    expect(
      screen.getByRole("heading", { name: "Home analytics unavailable not found" }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Home analytics endpoint was not found.").length,
    ).toBeGreaterThan(0);
  });

  it("renders success state with KPI cards, trend preview, and deterministic drill-down routes", () => {
    setSummaryState({
      isSuccess: true,
      data: summaryResponse,
    });
    setTimeSeriesState({
      isSuccess: true,
      data: timeSeriesResponse,
    });
    setHierarchyState({
      isSuccess: true,
      data: hierarchyResponse,
    });

    renderHomePage();

    expect(screen.getByRole("heading", { name: "Portfolio KPIs" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Portfolio health synthesis" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Core 10 first")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Health pillar scores" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Period change waterfall" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Trend preview" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Drill-down routes" })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /quant\/reports route/i }),
    ).toHaveAttribute("href", "/portfolio/reports?period=30D");
    expect(
      screen.getByRole("link", { name: /analyze risk route/i }),
    ).toHaveAttribute("href", "/portfolio/risk?period=30D");
  });

  it("normalizes unsupported period query values before calling time-series hook", async () => {
    const user = userEvent.setup();
    setSummaryState({
      isSuccess: true,
      data: summaryResponse,
    });
    setTimeSeriesState({
      isSuccess: true,
      data: timeSeriesResponse,
    });
    setHierarchyState({
      isSuccess: true,
      data: hierarchyResponse,
    });

    renderHomePage("/portfolio/home?period=BAD");

    expect(mockedUsePortfolioTimeSeriesQuery).toHaveBeenCalledWith("30D");
    expect(mockedUsePortfolioHealthSynthesisQuery).toHaveBeenCalledWith("30D", {
      scope: "portfolio",
      profilePosture: "balanced",
    });
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Select analytics period" }),
      "90D",
    );
    expect(mockedUsePortfolioTimeSeriesQuery).toHaveBeenCalledWith("90D");
  });

  it("keeps Home route snapshot-only and sends report workflow to Quant/Reports route", () => {
    setSummaryState({
      isSuccess: true,
      data: summaryResponse,
    });
    setTimeSeriesState({
      isSuccess: true,
      data: timeSeriesResponse,
    });
    setHierarchyState({
      isSuccess: true,
      data: hierarchyResponse,
    });

    renderHomePage();

    expect(screen.queryByRole("heading", { name: /quant report lifecycle/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /generate html report/i })).toBeNull();
    expect(
      screen.getByRole("link", { name: /quant\/reports route/i }),
    ).toHaveAttribute("href", "/portfolio/reports?period=30D");
  });

  it("promoted KPI cards expose explainability affordances", () => {
    setSummaryState({
      isSuccess: true,
      data: summaryResponse,
    });
    setTimeSeriesState({
      isSuccess: true,
      data: timeSeriesResponse,
    });
    setHierarchyState({
      isSuccess: true,
      data: hierarchyResponse,
    });

    renderHomePage();

    expect(
      screen.getByRole("button", { name: /explain market value/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /explain unrealized gain/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /explain period change/i }),
    ).toBeInTheDocument();
  });
});
