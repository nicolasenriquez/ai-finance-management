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
  PortfolioContributionResponse,
  PortfolioQuantMetricsResponse,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportGenerateResponse,
  PortfolioSummaryResponse,
  PortfolioTimeSeriesResponse,
} from "../../core/api/schemas";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import {
  usePortfolioContributionQuery,
  usePortfolioQuantMetricsQuery,
  usePortfolioQuantReportGenerateMutation,
  usePortfolioQuantReportHtmlQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";
import { PortfolioReportsPage } from "./PortfolioReportsPage";

vi.mock("../../features/portfolio-summary/hooks", () => ({
  usePortfolioSummaryQuery: vi.fn(),
}));

vi.mock("../../features/portfolio-workspace/hooks", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-workspace/hooks")
  >("../../features/portfolio-workspace/hooks");
  return {
    ...actual,
    usePortfolioContributionQuery: vi.fn(),
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
const mockedUsePortfolioTimeSeriesQuery = vi.mocked(usePortfolioTimeSeriesQuery);
const mockedUsePortfolioContributionQuery = vi.mocked(usePortfolioContributionQuery);
const mockedUsePortfolioQuantMetricsQuery = vi.mocked(usePortfolioQuantMetricsQuery);
const mockedUsePortfolioQuantReportGenerateMutation = vi.mocked(
  usePortfolioQuantReportGenerateMutation,
);
const mockedUsePortfolioQuantReportHtmlQuery = vi.mocked(usePortfolioQuantReportHtmlQuery);

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
  period: "90D",
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

const contributionResponse: PortfolioContributionResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  period: "90D",
  rows: [
    {
      instrument_symbol: "AAPL",
      contribution_pnl_usd: "30.00",
      contribution_pct: "60.00",
    },
    {
      instrument_symbol: "VOO",
      contribution_pnl_usd: "20.00",
      contribution_pct: "40.00",
    },
  ],
};

const quantMetricsResponse: PortfolioQuantMetricsResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  period: "90D",
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
  lifecycle_status: "ready",
  scope: "portfolio",
  instrument_symbol: null,
  period: "90D",
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

function setContributionState(
  state: Partial<QueryState<PortfolioContributionResponse>>,
): void {
  const queryState: QueryState<PortfolioContributionResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioContributionQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioContributionQuery>,
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

function renderReportsPage(path = "/portfolio/reports") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <PortfolioReportsPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioReportsPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    installMatchMediaMock(false);
    setSummaryState({ isSuccess: true, data: summaryResponse });
    setTimeSeriesState({ isSuccess: true, data: timeSeriesResponse });
    setContributionState({ isSuccess: true, data: contributionResponse });
    setQuantMetricsState({ isSuccess: true, data: quantMetricsResponse });
    setQuantReportGenerateState({});
    setQuantReportHtmlState({});
  });

  it("renders loading state while quant metrics request is pending", () => {
    setQuantMetricsState({ isLoading: true });

    const { container } = renderReportsPage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("renders error state when quant metrics request fails", () => {
    setQuantMetricsState({
      isError: true,
      error: new AppApiError("Quant unavailable", {
        kind: "server_error",
        detail: "Quant diagnostics are unavailable.",
      }),
    });

    renderReportsPage();

    expect(
      screen.getByRole("heading", { name: "Quant diagnostics unavailable" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Quant diagnostics are unavailable.")).toBeInTheDocument();
  });

  it("renders empty unavailable state before report generation", () => {
    renderReportsPage();

    expect(
      screen.getByRole("heading", { name: "Report lifecycle: unavailable" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/generate a report/i)).toBeInTheDocument();
  });

  it("normalizes unsupported period query values before calling time-series hook", () => {
    renderReportsPage("/portfolio/reports?period=BAD");

    expect(mockedUsePortfolioTimeSeriesQuery).toHaveBeenCalledWith("90D", {
      scope: "portfolio",
      instrumentSymbol: null,
      enabled: true,
    });
  });

  it("allows switching heatmap scope to instrument and dispatches scoped time-series query options", async () => {
    const user = userEvent.setup();
    renderReportsPage();

    await user.selectOptions(screen.getByRole("combobox", { name: /heatmap scope/i }), "instrument_symbol");
    await user.selectOptions(
      screen.getByRole("combobox", { name: /heatmap instrument symbol/i }),
      "AAPL",
    );

    expect(mockedUsePortfolioTimeSeriesQuery).toHaveBeenLastCalledWith("90D", {
      scope: "instrument_symbol",
      instrumentSymbol: "AAPL",
      enabled: true,
    });
  });

  it("renders symbol contribution focus from contribution endpoint rows instead of summary unrealized fields", () => {
    setSummaryState({
      isSuccess: true,
      data: {
        ...summaryResponse,
        rows: summaryResponse.rows.map((row) => ({
          ...row,
          unrealized_gain_usd: "-999.00",
          unrealized_gain_pct: "-999.00",
        })),
      },
    });
    setContributionState({
      isSuccess: true,
      data: contributionResponse,
    });

    renderReportsPage();

    expect(screen.getByRole("heading", { name: "Symbol contribution focus" })).toBeInTheDocument();
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("$30.00")).toBeInTheDocument();
    expect(screen.getByText("+60.00%")).toBeInTheDocument();
    expect(screen.queryByText("-999.00")).not.toBeInTheDocument();
  });

  it("renders ready state metadata and html preview for generated report", () => {
    setQuantReportGenerateState({
      isSuccess: true,
      data: quantReportGenerateResponse,
    });
    setQuantReportHtmlState({
      isSuccess: true,
      data: "<html><body><h1>Report</h1></body></html>",
    });

    renderReportsPage();

    expect(screen.getByText(/lifecycle: ready/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open full HTML report" }),
    ).toHaveAttribute("href", "/api/portfolio/quant-reports/report-001");
    expect(screen.getByTitle("Quant report HTML preview")).toBeInTheDocument();
  });

  it("renders lifecycle loading state while html preview is pending", () => {
    setQuantReportGenerateState({
      isSuccess: true,
      data: quantReportGenerateResponse,
    });
    setQuantReportHtmlState({
      isLoading: true,
    });

    renderReportsPage();

    expect(
      screen.getByText("Lifecycle: loading"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Report metadata is ready; loading HTML artifact preview."),
    ).toBeInTheDocument();
  });

  it("renders lifecycle warning for unavailable html artifacts", () => {
    setQuantReportGenerateState({
      isSuccess: true,
      data: {
        ...quantReportGenerateResponse,
        lifecycle_status: "unavailable",
      },
    });
    setQuantReportHtmlState({
      isError: true,
      error: new AppApiError("Unavailable", {
        kind: "not_found",
        detail: "Report artifact unavailable.",
      }),
    });

    renderReportsPage();

    expect(
      screen.getByRole("heading", { name: "Report lifecycle: unavailable" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Report artifact unavailable.")).toBeInTheDocument();
  });

  it("validates instrument-scope requests without symbol input", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(quantReportGenerateResponse);
    setSummaryState({
      isSuccess: true,
      data: { ...summaryResponse, rows: [] },
    });
    setQuantReportGenerateState({ mutateAsync });

    renderReportsPage();

    await user.selectOptions(screen.getByRole("combobox", { name: /report scope/i }), "instrument_symbol");
    await user.click(screen.getByRole("button", { name: /generate html report/i }));

    expect(screen.getByText(/instrument symbol is required/i)).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });
});
