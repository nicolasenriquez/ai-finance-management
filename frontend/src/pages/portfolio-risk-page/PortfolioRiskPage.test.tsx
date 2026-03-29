/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
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
import type { PortfolioRiskEstimatorsResponse } from "../../core/api/schemas";
import { usePortfolioRiskEstimatorsQuery } from "../../features/portfolio-workspace/hooks";
import { PortfolioRiskPage } from "./PortfolioRiskPage";

vi.mock("../../features/portfolio-workspace/hooks", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-workspace/hooks")
  >("../../features/portfolio-workspace/hooks");
  return {
    ...actual,
    usePortfolioRiskEstimatorsQuery: vi.fn(),
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

const mockedUsePortfolioRiskEstimatorsQuery = vi.mocked(
  usePortfolioRiskEstimatorsQuery,
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
    },
  ],
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

  mockedUsePortfolioRiskEstimatorsQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioRiskEstimatorsQuery>,
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
    expect(screen.getAllByText("beta").length).toBeGreaterThan(0);
    expect(screen.getByText(/window 90d/i)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Risk metrics chart" })).toBeInTheDocument();
    expect(
      screen.getByText(/risk-context interpretation/i),
    ).toBeInTheDocument();
  });

  it("maps chart period query to supported risk windows deterministically", () => {
    setRiskState({
      isSuccess: true,
      data: riskResponse,
    });

    renderRiskPage("/portfolio/risk?period=MAX");
    expect(mockedUsePortfolioRiskEstimatorsQuery).toHaveBeenCalledWith(252);
  });
});
