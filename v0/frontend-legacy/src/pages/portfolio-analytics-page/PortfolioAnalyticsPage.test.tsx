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
  PortfolioTimeSeriesResponse,
} from "../../core/api/schemas";
import {
  usePortfolioContributionQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";
import { PortfolioAnalyticsPage } from "./PortfolioAnalyticsPage";

vi.mock("../../features/portfolio-workspace/hooks", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-workspace/hooks")
  >("../../features/portfolio-workspace/hooks");
  return {
    ...actual,
    usePortfolioContributionQuery: vi.fn(),
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

const mockedUsePortfolioTimeSeriesQuery = vi.mocked(usePortfolioTimeSeriesQuery);
const mockedUsePortfolioContributionQuery = vi.mocked(usePortfolioContributionQuery);

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
  ],
};

const contributionResponse: PortfolioContributionResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  period: "30D",
  rows: [
    {
      instrument_symbol: "AAPL",
      contribution_pnl_usd: "15.00",
      contribution_pct: "4.20",
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

function renderAnalyticsPage(path = "/portfolio/analytics") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <PortfolioAnalyticsPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioAnalyticsPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    installMatchMediaMock(false);
  });

  it("renders loading state while analytics requests are pending", () => {
    setTimeSeriesState({ isLoading: true });
    setContributionState({ isLoading: true });

    const { container } = renderAnalyticsPage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("renders explicit empty state for missing trend or contribution rows", () => {
    setTimeSeriesState({ isSuccess: true, data: timeSeriesResponse });
    setContributionState({
      isSuccess: true,
      data: { ...contributionResponse, rows: [] },
    });

    renderAnalyticsPage();

    expect(
      screen.getByRole("heading", {
        name: "Analytics route returned no chartable rows",
      }),
    ).toBeInTheDocument();
  });

  it("renders error state with API detail when analytics request fails", () => {
    setTimeSeriesState({
      isError: true,
      error: new AppApiError("Validation error", {
        kind: "validation_error",
        detail: "Unsupported period value.",
      }),
    });
    setContributionState({ isSuccess: false });

    renderAnalyticsPage();

    expect(
      screen.getByRole("heading", { name: "Analytics workspace unavailable" }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Unsupported period value.").length,
    ).toBeGreaterThan(0);
  });

  it("renders success modules for trend and contribution", () => {
    setTimeSeriesState({ isSuccess: true, data: timeSeriesResponse });
    setContributionState({ isSuccess: true, data: contributionResponse });

    renderAnalyticsPage();

    expect(
      screen.getByRole("heading", { name: "Portfolio trend dataset" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Contribution leaders" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Portfolio trend chart" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Contribution by symbol chart" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/benchmark-aware overview/i),
    ).toBeInTheDocument();
  });

  it("renders contribution leaders table with explicit directional semantics labels (fail-first)", () => {
    setTimeSeriesState({ isSuccess: true, data: timeSeriesResponse });
    setContributionState({ isSuccess: true, data: contributionResponse });

    renderAnalyticsPage();

    expect(screen.getByRole("columnheader", { name: "Net share (vs net period)" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Absolute share" })).toBeInTheDocument();
  });

  it("hides duplicate attribution bridge visuals until advanced disclosure is explicitly opened", async () => {
    const user = userEvent.setup();
    setTimeSeriesState({ isSuccess: true, data: timeSeriesResponse });
    setContributionState({ isSuccess: true, data: contributionResponse });

    renderAnalyticsPage();

    expect(
      screen.queryByRole("heading", { name: "Contribution waterfall" }),
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: /show attribution bridge/i }),
    );

    expect(
      screen.getByRole("heading", { name: "Contribution waterfall" }),
    ).toBeInTheDocument();
  });

  it("limits period selector values to backend-supported enum options", () => {
    setTimeSeriesState({ isSuccess: true, data: timeSeriesResponse });
    setContributionState({ isSuccess: true, data: contributionResponse });

    renderAnalyticsPage("/portfolio/analytics?period=WEIRD");

    expect(mockedUsePortfolioTimeSeriesQuery).toHaveBeenCalledWith("30D");
    const optionValues = screen
      .getAllByRole("option")
      .map((option) => option.getAttribute("value"));
    expect(optionValues).toEqual(["30D", "90D", "6M", "252D", "YTD", "MAX"]);
  });
});
