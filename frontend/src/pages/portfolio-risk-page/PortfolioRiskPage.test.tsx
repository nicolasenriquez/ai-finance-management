/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
  waitFor,
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
  PortfolioReturnDistributionResponse,
  PortfolioRiskEstimatorsResponse,
  PortfolioRiskEvolutionResponse,
} from "../../core/api/schemas";
import {
  usePortfolioHealthSynthesisQuery,
  usePortfolioReturnDistributionQuery,
  usePortfolioRiskEstimatorsScopedQuery,
  usePortfolioRiskEvolutionQuery,
} from "../../features/portfolio-workspace/hooks";
import { PortfolioRiskPage } from "./PortfolioRiskPage";

vi.mock("../../features/portfolio-workspace/hooks", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-workspace/hooks")
  >("../../features/portfolio-workspace/hooks");
  return {
    ...actual,
    usePortfolioHealthSynthesisQuery: vi.fn(),
    usePortfolioRiskEstimatorsScopedQuery: vi.fn(),
    usePortfolioRiskEvolutionQuery: vi.fn(),
    usePortfolioReturnDistributionQuery: vi.fn(),
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

const mockedUsePortfolioRiskEstimatorsScopedQuery = vi.mocked(
  usePortfolioRiskEstimatorsScopedQuery,
);
const mockedUsePortfolioHealthSynthesisQuery = vi.mocked(
  usePortfolioHealthSynthesisQuery,
);
const mockedUsePortfolioRiskEvolutionQuery = vi.mocked(
  usePortfolioRiskEvolutionQuery,
);
const mockedUsePortfolioReturnDistributionQuery = vi.mocked(
  usePortfolioReturnDistributionQuery,
);

const riskResponse: PortfolioRiskEstimatorsResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  window_days: 90,
  metrics: [
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
      unit: "ratio",
      interpretation_band: "favorable",
      timeline_series_id: "beta",
    },
  ],
  timeline_context: {
    available: true,
    scope: "portfolio",
    instrument_symbol: null,
    period: "90D",
  },
  guardrails: {
    mixed_units: false,
    unit_groups: ["ratio"],
    guidance: "Estimator units are comparable for shared-axis interpretation.",
  },
};

const riskEvolutionResponse: PortfolioRiskEvolutionResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  scope: "portfolio",
  instrument_symbol: null,
  period: "90D",
  rolling_window_days: 30,
  methodology: {
    drawdown_method: "running_peak_relative_decline",
    rolling_volatility_method: "rolling_std_x_sqrt_252",
    rolling_beta_method: "rolling_covariance_div_variance",
  },
  drawdown_path_points: [
    {
      captured_at: "2026-03-20T00:00:00Z",
      drawdown: "-0.040000",
    },
    {
      captured_at: "2026-03-21T00:00:00Z",
      drawdown: "-0.020000",
    },
  ],
  rolling_points: [
    {
      captured_at: "2026-03-20T00:00:00Z",
      volatility_annualized: "0.220000",
      beta: "0.980000",
    },
    {
      captured_at: "2026-03-21T00:00:00Z",
      volatility_annualized: "0.210000",
      beta: "0.950000",
    },
  ],
};

const returnDistributionResponse: PortfolioReturnDistributionResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  scope: "portfolio",
  instrument_symbol: null,
  period: "90D",
  sample_size: 90,
  bucket_policy: {
    method: "equal_width",
    bin_count: 12,
    min_return: "-0.040000",
    max_return: "0.050000",
  },
  buckets: [
    {
      bucket_index: 0,
      lower_bound: "-0.040000",
      upper_bound: "-0.032500",
      count: 2,
      frequency: "0.022222",
    },
    {
      bucket_index: 1,
      lower_bound: "-0.032500",
      upper_bound: "-0.025000",
      count: 5,
      frequency: "0.055556",
    },
  ],
};

const healthResponse: PortfolioHealthSynthesisResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  scope: "portfolio",
  instrument_symbol: null,
  period: "90D",
  profile_posture: "balanced",
  health_score: 68,
  health_label: "watchlist",
  threshold_policy_version: "health_v1_20260330",
  pillars: [
    {
      pillar_id: "growth",
      label: "Growth",
      score: 76,
      status: "favorable",
      metrics: [],
    },
    {
      pillar_id: "risk",
      label: "Risk",
      score: 52,
      status: "caution",
      metrics: [],
    },
    {
      pillar_id: "risk_adjusted_quality",
      label: "Risk-adjusted quality",
      score: 64,
      status: "caution",
      metrics: [],
    },
    {
      pillar_id: "resilience",
      label: "Resilience",
      score: 60,
      status: "caution",
      metrics: [],
    },
  ],
  key_drivers: [
    {
      metric_id: "max_drawdown",
      label: "Max Drawdown",
      direction: "penalizing",
      impact_points: 66,
      rationale: "Drawdown depth is materially above conservative tolerance.",
      value_display: "-22.00%",
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

function setRiskState(
  state: Partial<QueryState<PortfolioRiskEstimatorsResponse>>,
): void {
  const queryState: QueryState<PortfolioRiskEstimatorsResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioRiskEstimatorsScopedQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioRiskEstimatorsScopedQuery>,
  );
}

function setRiskEvolutionState(
  state: Partial<QueryState<PortfolioRiskEvolutionResponse>>,
): void {
  const queryState: QueryState<PortfolioRiskEvolutionResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };
  mockedUsePortfolioRiskEvolutionQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioRiskEvolutionQuery>,
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

function setReturnDistributionState(
  state: Partial<QueryState<PortfolioReturnDistributionResponse>>,
): void {
  const queryState: QueryState<PortfolioReturnDistributionResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };
  mockedUsePortfolioReturnDistributionQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioReturnDistributionQuery>,
  );
}

function renderRiskPage(path = "/portfolio/risk") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <PortfolioRiskPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioRiskPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    installMatchMediaMock(false);
    setRiskState({
      isSuccess: true,
      data: riskResponse,
    });
    setRiskEvolutionState({
      isSuccess: true,
      data: riskEvolutionResponse,
    });
    setReturnDistributionState({
      isSuccess: true,
      data: returnDistributionResponse,
    });
    setHealthState({
      isSuccess: true,
      data: healthResponse,
    });
  });

  it("renders loading state while risk estimators are pending", () => {
    setRiskState({ isLoading: true });

    const { container } = renderRiskPage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("renders explicit empty state when metric list is empty", () => {
    setRiskState({
      isSuccess: true,
      data: { ...riskResponse, metrics: [] },
    });

    renderRiskPage();

    expect(
      screen.getByRole("heading", { name: "No risk metrics for selected scope" }),
    ).toBeInTheDocument();
  });

  it("renders not-found warning state for missing risk scope", () => {
    setRiskState({
      isError: true,
      error: new AppApiError("Missing", {
        kind: "not_found",
        detail: "Risk estimator endpoint not found.",
      }),
    });

    renderRiskPage();

    expect(
      screen.getByRole("heading", { name: "Risk workspace unavailable not found" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Risk estimator endpoint not found.")).toBeInTheDocument();
  });

  it("renders explicit unsupported-scope messaging when backend rejects window", () => {
    setRiskState({
      isError: true,
      error: new AppApiError("Unsupported", {
        kind: "validation_error",
        detail: "Unsupported risk estimator window.",
      }),
    });

    renderRiskPage();

    expect(
      screen.getByRole("heading", { name: "Risk scope unsupported" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Unsupported risk estimator window.")).toBeInTheDocument();
  });

  it("renders success state with estimator cards and methodology metadata", () => {
    setRiskState({
      isSuccess: true,
      data: riskResponse,
    });

    renderRiskPage();

    expect(screen.getByRole("heading", { name: "Estimator metrics" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Health context bridge" })).toBeInTheDocument();
    expect(screen.getAllByText(/beta/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/window 90d/i)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Risk metrics chart" })).toBeInTheDocument();
    expect(
      screen.getByText(/risk-context interpretation/i),
    ).toBeInTheDocument();
  });

  it("maps chart period query to supported risk windows deterministically", () => {
    renderRiskPage("/portfolio/risk?period=MAX");
    expect(mockedUsePortfolioRiskEstimatorsScopedQuery).toHaveBeenCalledWith(252, {
      scope: "portfolio",
      instrumentSymbol: null,
      period: "MAX",
      enabled: true,
    });
  });

  it("does not force a default symbol when switching to instrument scope", async () => {
    const user = userEvent.setup();
    renderRiskPage("/portfolio/risk?period=252D");

    await user.selectOptions(
      screen.getByRole("combobox", { name: /select risk scope/i }),
      "instrument_symbol",
    );

    await waitFor(() => {
      expect(mockedUsePortfolioRiskEstimatorsScopedQuery).toHaveBeenLastCalledWith(252, {
        scope: "instrument_symbol",
        instrumentSymbol: null,
        period: "252D",
        enabled: false,
      });
    });
    expect(
      screen.getByRole("heading", { name: "Risk scope requires symbol" }),
    ).toBeInTheDocument();
  });

  it("gates instrument-scoped risk estimator query when symbol is missing", () => {
    renderRiskPage("/portfolio/risk?scope=instrument_symbol&period=90D");

    expect(mockedUsePortfolioRiskEstimatorsScopedQuery).toHaveBeenCalledWith(90, {
      scope: "instrument_symbol",
      instrumentSymbol: null,
      period: "90D",
      enabled: false,
    });
    expect(
      screen.getByRole("heading", { name: "Risk scope requires symbol" }),
    ).toBeInTheDocument();
  });

  it("renders drawdown, rolling-estimator, and return-distribution modules for interpretation depth", () => {
    setRiskState({
      isSuccess: true,
      data: riskResponse,
    });

    renderRiskPage();

    expect(
      screen.getByRole("heading", { name: /drawdown path timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /rolling estimator timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /return distribution/i }),
    ).toBeInTheDocument();
  });

  it("renders deterministic, keyboard-reachable timeline visibility toggles", () => {
    setRiskState({
      isSuccess: true,
      data: riskResponse,
    });

    renderRiskPage();

    const drawdownToggle = screen.getByRole("button", { name: /toggle drawdown series/i });
    const volatilityToggle = screen.getByRole("button", {
      name: /toggle rolling volatility series/i,
    });
    const betaToggle = screen.getByRole("button", { name: /toggle rolling beta series/i });

    expect(drawdownToggle).toHaveAttribute("aria-pressed");
    expect(volatilityToggle).toHaveAttribute("aria-pressed");
    expect(betaToggle).toHaveAttribute("aria-pressed");
  });
});
