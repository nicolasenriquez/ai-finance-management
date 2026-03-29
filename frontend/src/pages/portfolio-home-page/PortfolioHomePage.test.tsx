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
  PortfolioHierarchyResponse,
  PortfolioQuantMetricsResponse,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportGenerateResponse,
  PortfolioSummaryResponse,
  PortfolioTimeSeriesResponse,
} from "../../core/api/schemas";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import {
  usePortfolioHierarchyQuery,
  usePortfolioQuantMetricsQuery,
  usePortfolioQuantReportGenerateMutation,
  usePortfolioQuantReportHtmlQuery,
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
    usePortfolioHierarchyQuery: vi.fn(),
    usePortfolioQuantMetricsQuery: vi.fn(),
    usePortfolioQuantReportGenerateMutation: vi.fn(),
    usePortfolioQuantReportHtmlQuery: vi.fn(),
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

type MutationState<TData, TVariables> = {
  isPending: boolean;
  isError: boolean;
  isSuccess: boolean;
  data?: TData;
  error?: unknown;
  mutateAsync: (variables: TVariables) => Promise<TData>;
};

const mockedUsePortfolioSummaryQuery = vi.mocked(usePortfolioSummaryQuery);
const mockedUsePortfolioHierarchyQuery = vi.mocked(usePortfolioHierarchyQuery);
const mockedUsePortfolioQuantMetricsQuery = vi.mocked(usePortfolioQuantMetricsQuery);
const mockedUsePortfolioQuantReportGenerateMutation = vi.mocked(
  usePortfolioQuantReportGenerateMutation,
);
const mockedUsePortfolioQuantReportHtmlQuery = vi.mocked(usePortfolioQuantReportHtmlQuery);
const mockedUsePortfolioTimeSeriesQuery = vi.mocked(usePortfolioTimeSeriesQuery);

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

const quantMetricsResponse: PortfolioQuantMetricsResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  period: "30D",
  benchmark_symbol: "SP500_PROXY",
  benchmark_context: {
    benchmark_symbol: "SP500_PROXY",
    omitted_metric_ids: [],
    omission_reason: null,
  },
  metrics: [
    {
      metric_id: "sharpe",
      label: "Sharpe Ratio",
      description: "Risk-adjusted return ratio.",
      value: "1.230000",
      display_as: "number",
    },
    {
      metric_id: "volatility",
      label: "Volatility",
      description: "Annualized return volatility estimate.",
      value: "0.180000",
      display_as: "percent",
    },
  ],
};

const quantReportGenerateResponse: PortfolioQuantReportGenerateResponse = {
  report_id: "report-001",
  report_url_path: "/api/portfolio/quant-reports/report-001",
  scope: "portfolio",
  instrument_symbol: null,
  period: "30D",
  benchmark_symbol: "SP500_PROXY",
  generated_at: "2026-03-28T00:00:00Z",
  expires_at: "2026-03-28T01:00:00Z",
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

function setQuantMetricsState(
  state: Partial<QueryState<PortfolioQuantMetricsResponse>>,
): void {
  const queryState: QueryState<PortfolioQuantMetricsResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioQuantMetricsQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioQuantMetricsQuery>,
  );
}

function setQuantReportGenerateState(
  state: Partial<
    MutationState<
      PortfolioQuantReportGenerateResponse,
      PortfolioQuantReportGenerateRequest
    >
  >,
): void {
  const mutationState: MutationState<
    PortfolioQuantReportGenerateResponse,
    PortfolioQuantReportGenerateRequest
  > = {
    isPending: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    mutateAsync: vi.fn().mockResolvedValue(quantReportGenerateResponse),
    ...state,
  };

  mockedUsePortfolioQuantReportGenerateMutation.mockReturnValue(
    mutationState as ReturnType<typeof usePortfolioQuantReportGenerateMutation>,
  );
}

function setQuantReportHtmlState(state: Partial<QueryState<string>>): void {
  const queryState: QueryState<string> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };
  mockedUsePortfolioQuantReportHtmlQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioQuantReportHtmlQuery>,
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
    setQuantReportGenerateState({});
    setQuantReportHtmlState({});
  });

  it("renders loading state while home analytics requests are pending", () => {
    setSummaryState({ isLoading: true });
    setTimeSeriesState({ isLoading: true });
    setQuantMetricsState({ isLoading: true });
    setHierarchyState({ isLoading: true });

    const { container } = renderHomePage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("renders empty state when either summary rows or trend points are empty", () => {
    setSummaryState({
      isSuccess: true,
      data: { ...summaryResponse, rows: [] },
    });
    setTimeSeriesState({
      isSuccess: true,
      data: timeSeriesResponse,
    });
    setQuantMetricsState({
      isSuccess: true,
      data: quantMetricsResponse,
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
    setQuantMetricsState({ isSuccess: false });
    setHierarchyState({ isSuccess: false });

    renderHomePage();

    expect(
      screen.getByRole("heading", { name: "Home analytics unavailable not found" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Home analytics endpoint was not found.")).toBeInTheDocument();
  });

  it("renders success state with KPI cards and trend preview", () => {
    setSummaryState({
      isSuccess: true,
      data: summaryResponse,
    });
    setTimeSeriesState({
      isSuccess: true,
      data: timeSeriesResponse,
    });
    setQuantMetricsState({
      isSuccess: true,
      data: quantMetricsResponse,
    });
    setHierarchyState({
      isSuccess: true,
      data: hierarchyResponse,
    });

    renderHomePage();

    expect(screen.getByRole("heading", { name: "Portfolio KPIs" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Quant metrics" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Trend preview" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Drill-down routes" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /analytics \+ quant preview route/i })).toHaveAttribute(
      "href",
      "/portfolio/analytics?period=30D",
    );
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
    setQuantMetricsState({
      isSuccess: true,
      data: quantMetricsResponse,
    });
    setHierarchyState({
      isSuccess: true,
      data: hierarchyResponse,
    });

    renderHomePage("/portfolio/home?period=BAD");

    expect(mockedUsePortfolioTimeSeriesQuery).toHaveBeenCalledWith("30D");
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Select analytics period" }),
      "90D",
    );
    expect(mockedUsePortfolioTimeSeriesQuery).toHaveBeenCalledWith("90D");
  });

  it("keeps core home modules visible when quant section fails while core data succeeds (fail-first)", () => {
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
    setQuantMetricsState({
      isError: true,
      error: new AppApiError("Quant unavailable", {
        kind: "server_error",
        detail: "Quant metrics are temporarily unavailable.",
      }),
    });

    renderHomePage();

    expect(screen.getByRole("heading", { name: "Portfolio KPIs" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Home analytics unavailable" })).toBeNull();
  });

  it("renders explicit quant-preview boundary labeling and benchmark omission context", () => {
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
    setQuantMetricsState({
      isSuccess: true,
      data: {
        ...quantMetricsResponse,
        benchmark_context: {
          benchmark_symbol: "SP500_PROXY",
          omitted_metric_ids: ["alpha", "beta"],
          omission_reason: "Benchmark series length is insufficient for selected period.",
        },
      },
    });

    renderHomePage();

    expect(
      screen.getByText(/preview only/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Optional benchmark metrics omitted" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/alpha, beta/i)).toBeInTheDocument();
  });

  it("renders quant-report controls with explicit action labels", () => {
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
    setQuantMetricsState({
      isSuccess: true,
      data: quantMetricsResponse,
    });

    renderHomePage();

    expect(
      screen.getByRole("heading", { name: "Quant report generation" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Generate HTML report" }),
    ).toBeInTheDocument();
  });

  it("submits quant report generation for instrument scope", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      ...quantReportGenerateResponse,
      scope: "instrument_symbol" as const,
      instrument_symbol: "AAPL",
    });
    setQuantReportGenerateState({
      mutateAsync,
    });
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
    setQuantMetricsState({
      isSuccess: true,
      data: quantMetricsResponse,
    });

    renderHomePage();

    await user.selectOptions(
      screen.getByRole("combobox", { name: /report scope/i }),
      "instrument_symbol",
    );
    await user.click(screen.getByRole("button", { name: "Generate HTML report" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      scope: "instrument_symbol",
      instrument_symbol: "AAPL",
      period: "30D",
    });
  });

  it("renders quant report ready-state metadata and html preview", () => {
    setQuantReportGenerateState({
      isSuccess: true,
      data: quantReportGenerateResponse,
    });
    setQuantReportHtmlState({
      isSuccess: true,
      data: "<html><body><h1>Report</h1></body></html>",
    });
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
    setQuantMetricsState({
      isSuccess: true,
      data: quantMetricsResponse,
    });

    renderHomePage();

    expect(
      screen.getByRole("link", { name: "Open full HTML report" }),
    ).toHaveAttribute("href", "/api/portfolio/quant-reports/report-001");
    expect(
      screen.getByTitle("Quant report HTML preview"),
    ).toBeInTheDocument();
  });
});
