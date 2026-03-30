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
  PortfolioHealthSynthesisResponse,
  PortfolioMonteCarloRequest,
  PortfolioMonteCarloResponse,
  PortfolioQuantMetricsResponse,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportGenerateResponse,
  PortfolioSummaryResponse,
  PortfolioTimeSeriesResponse,
} from "../../core/api/schemas";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import {
  usePortfolioContributionQuery,
  usePortfolioHealthSynthesisQuery,
  usePortfolioMonteCarloMutation,
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
    usePortfolioHealthSynthesisQuery: vi.fn(),
    usePortfolioMonteCarloMutation: vi.fn(),
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
const mockedUsePortfolioHealthSynthesisQuery = vi.mocked(
  usePortfolioHealthSynthesisQuery,
);
const mockedUsePortfolioQuantMetricsQuery = vi.mocked(usePortfolioQuantMetricsQuery);
const mockedUsePortfolioMonteCarloMutation = vi.mocked(usePortfolioMonteCarloMutation);
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
  simulation_context_status: "unavailable",
  simulation_context_reason: null,
};

const monteCarloResponse: PortfolioMonteCarloResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  scope: "portfolio",
  instrument_symbol: null,
  period: "90D",
  simulation: {
    sims: 1000,
    horizon_days: 90,
    seed: 20260330,
    bust_threshold: "-0.200000",
    goal_threshold: "0.300000",
  },
  assumptions: {
    model: "quantstats_shuffled_returns",
    notes: ["Simulation shuffles historical returns."],
  },
  summary: {
    start_value_usd: "10000.00",
    median_ending_value_usd: "10420.00",
    mean_ending_return: "0.041000",
    bust_probability: "0.080000",
    goal_probability: "0.310000",
    interpretation_signal: "balanced",
  },
  ending_return_percentiles: [
    { percentile: 5, value: "-0.190000" },
    { percentile: 50, value: "0.040000" },
    { percentile: 95, value: "0.270000" },
  ],
  profile_comparison_enabled: true,
  calibration_context: {
    requested_basis: "monthly",
    effective_basis: "monthly",
    sample_size: 48,
    lookback_start: "2022-01-31T00:00:00Z",
    lookback_end: "2026-03-31T00:00:00Z",
    used_fallback: false,
    fallback_reason: null,
  },
  profile_scenarios: [
    {
      profile_id: "conservative",
      label: "Conservative",
      bust_threshold: "-0.100000",
      goal_threshold: "0.120000",
      bust_probability: "0.140000",
      goal_probability: "0.510000",
      interpretation_signal: "upside_favorable",
    },
    {
      profile_id: "balanced",
      label: "Balanced",
      bust_threshold: "-0.200000",
      goal_threshold: "0.270000",
      bust_probability: "0.080000",
      goal_probability: "0.310000",
      interpretation_signal: "balanced",
    },
    {
      profile_id: "growth",
      label: "Growth",
      bust_threshold: "-0.300000",
      goal_threshold: "0.450000",
      bust_probability: "0.040000",
      goal_probability: "0.190000",
      interpretation_signal: "balanced",
    },
  ],
};

const healthResponse: PortfolioHealthSynthesisResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  scope: "portfolio",
  instrument_symbol: null,
  period: "90D",
  profile_posture: "balanced",
  health_score: 72,
  health_label: "healthy",
  threshold_policy_version: "health_v1_20260330",
  pillars: [
    {
      pillar_id: "growth",
      label: "Growth",
      score: 82,
      status: "favorable",
      metrics: [],
    },
    {
      pillar_id: "risk",
      label: "Risk",
      score: 60,
      status: "caution",
      metrics: [],
    },
    {
      pillar_id: "risk_adjusted_quality",
      label: "Risk-adjusted quality",
      score: 70,
      status: "favorable",
      metrics: [],
    },
    {
      pillar_id: "resilience",
      label: "Resilience",
      score: 66,
      status: "caution",
      metrics: [],
    },
  ],
  key_drivers: [
    {
      metric_id: "sharpe_ratio",
      label: "Sharpe Ratio",
      direction: "supporting",
      impact_points: 52,
      rationale: "Risk-adjusted efficiency supports the current return profile.",
      value_display: "0.860",
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

function setMonteCarloState(
  state: Partial<MutationState<PortfolioMonteCarloResponse, PortfolioMonteCarloRequest>>,
): void {
  const mutationState: MutationState<
    PortfolioMonteCarloResponse,
    PortfolioMonteCarloRequest
  > = {
    isPending: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    mutateAsync: vi.fn().mockResolvedValue(monteCarloResponse),
    ...state,
  };

  mockedUsePortfolioMonteCarloMutation.mockReturnValue(
    mutationState as ReturnType<typeof usePortfolioMonteCarloMutation>,
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
    setHealthState({ isSuccess: true, data: healthResponse });
    setQuantMetricsState({ isSuccess: true, data: quantMetricsResponse });
    setQuantReportGenerateState({});
    setQuantReportHtmlState({});
    setMonteCarloState({});
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

  it("renders quant lens as semantic table and compact lifecycle controls (fail-first)", () => {
    const { container } = renderReportsPage();

    expect(container.querySelector("table.quant-lens-table")).toBeInTheDocument();
    expect(container.querySelector(".quant-lifecycle-controls")).toBeInTheDocument();
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

  it("validates horizon against selected period capacity before dispatching Monte Carlo request", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(monteCarloResponse);
    setMonteCarloState({ mutateAsync });

    renderReportsPage("/portfolio/reports?period=30D");

    const horizonInput = screen.getByRole("textbox", {
      name: /simulation horizon days/i,
    });
    await user.clear(horizonInput);
    await user.type(horizonInput, "30");
    await user.click(screen.getByRole("button", { name: /run monte carlo simulation/i }));

    expect(
      screen.getByText(
        "For 30D period, horizon days must be an integer between 5 and 29 return days.",
      ),
    ).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("rejects non-numeric bust threshold input before dispatching Monte Carlo request", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(monteCarloResponse);
    setMonteCarloState({ mutateAsync });

    renderReportsPage();

    const bustThresholdInput = screen.getByRole("textbox", { name: /bust threshold/i });
    await user.clear(bustThresholdInput);
    await user.type(bustThresholdInput, "abc");
    await user.click(screen.getByRole("button", { name: /run monte carlo simulation/i }));

    expect(
      screen.getByText("Bust threshold must be a valid number or left empty."),
    ).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("rejects non-numeric goal threshold input before dispatching Monte Carlo request", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(monteCarloResponse);
    setMonteCarloState({ mutateAsync });

    renderReportsPage();

    const goalThresholdInput = screen.getByRole("textbox", { name: /goal threshold/i });
    await user.clear(goalThresholdInput);
    await user.type(goalThresholdInput, "xyz");
    await user.click(screen.getByRole("button", { name: /run monte carlo simulation/i }));

    expect(
      screen.getByText("Goal threshold must be a valid number or left empty."),
    ).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("renders Monte Carlo module with explicit unavailable state before first simulation", () => {
    renderReportsPage();

    expect(
      screen.getByRole("heading", { name: /Monte Carlo diagnostics/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Health scenario bridge/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Simulation lifecycle: unavailable/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Run Monte Carlo simulation/i }),
    ).toBeInTheDocument();
  });

  it("renders Monte Carlo loading state with explicit progress copy", () => {
    setMonteCarloState({
      isPending: true,
    });

    renderReportsPage();

    expect(screen.getByText(/Simulation lifecycle: loading/i)).toBeInTheDocument();
    expect(
      screen.getByText(/running bounded quantstats monte carlo scenarios/i),
    ).toBeInTheDocument();
  });

  it("renders Monte Carlo error state with retry affordance", () => {
    setMonteCarloState({
      isError: true,
      error: new AppApiError("Monte Carlo failure", {
        kind: "server_error",
        detail: "Monte Carlo simulation failed for selected scope.",
      }),
    });

    renderReportsPage();

    expect(
      screen.getByRole("heading", { name: /Simulation lifecycle: error/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Monte Carlo simulation failed for selected scope."),
    ).toBeInTheDocument();
  });

  it("handles rejected Monte Carlo submission without unhandled rejection", async () => {
    const user = userEvent.setup();
    const mutationError = new AppApiError("Monte Carlo failure", {
      kind: "server_error",
      detail: "Monte Carlo simulation failed for selected scope.",
    });
    const mutateAsync = vi.fn().mockRejectedValue(mutationError);
    setMonteCarloState({
      isError: true,
      error: mutationError,
      mutateAsync,
    });

    renderReportsPage();

    await user.click(screen.getByRole("button", { name: /run monte carlo simulation/i }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(
      screen.getByRole("heading", { name: /Simulation lifecycle: error/i }),
    ).toBeInTheDocument();
  });

  it("renders Monte Carlo ready state summary cards", () => {
    setMonteCarloState({
      isSuccess: true,
      data: monteCarloResponse,
    });

    renderReportsPage();

    expect(screen.getByText(/Simulation lifecycle: ready/i)).toBeInTheDocument();
    expect(screen.getByText(/Simulation scope/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Portfolio scope · 90D window · 90-day horizon\./i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/P50 ending return/i).length).toBeGreaterThan(0);
    expect(screen.getByText("+4.00%")).toBeInTheDocument();
    expect(screen.getAllByText(/Bust probability/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("8.00%").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Goal probability/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("31.00%").length).toBeGreaterThan(0);
  });

  it("renders panoramic profile scenario comparison with fixed profile order", () => {
    setMonteCarloState({
      isSuccess: true,
      data: monteCarloResponse,
    });

    renderReportsPage();

    expect(screen.getByRole("heading", { name: /profile scenario comparison/i })).toBeInTheDocument();
    const profileRows = screen.getAllByTestId("monte-carlo-profile-row");
    expect(profileRows).toHaveLength(3);
    expect(profileRows[0]).toHaveTextContent("Conservative");
    expect(profileRows[1]).toHaveTextContent("Balanced");
    expect(profileRows[2]).toHaveTextContent("Growth");
    expect(screen.getByText(/Calibration basis: monthly/i)).toBeInTheDocument();
  });

  it("supports profile controls while preserving manual input workflow", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(monteCarloResponse);
    setMonteCarloState({ mutateAsync });

    renderReportsPage();

    await user.selectOptions(
      screen.getByRole("combobox", { name: /calibration basis/i }),
      "annual",
    );
    await user.click(screen.getByRole("button", { name: /apply profile growth/i }));
    await user.click(screen.getByRole("button", { name: /run monte carlo simulation/i }));

    const request = mutateAsync.mock.calls[0]?.[0] as PortfolioMonteCarloRequest;
    expect(request.calibration_basis).toBe("annual");
    expect(request.enable_profile_comparison).toBe(true);
    expect(request.bust_threshold).not.toBeNull();
    expect(request.goal_threshold).not.toBeNull();
  });

  it("allows disabling profile comparison and sends explicit request toggle", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(monteCarloResponse);
    setMonteCarloState({ mutateAsync });

    renderReportsPage();

    await user.click(screen.getByRole("checkbox", { name: /enable profile compare/i }));
    await user.click(screen.getByRole("button", { name: /run monte carlo simulation/i }));

    const request = mutateAsync.mock.calls[0]?.[0] as PortfolioMonteCarloRequest;
    expect(request.enable_profile_comparison).toBe(false);
  });
});
