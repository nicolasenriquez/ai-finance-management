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
import type { PortfolioSummaryResponse } from "../../core/api/schemas";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import { PortfolioHoldingsPage } from "./PortfolioHoldingsPage";

vi.mock("../../features/portfolio-summary/hooks", () => ({
  usePortfolioSummaryQuery: vi.fn(),
}));

type QueryState<TData> = {
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  data?: TData;
  error?: unknown;
  refetch: () => Promise<unknown>;
};

const mockedUsePortfolioSummaryQuery = vi.mocked(usePortfolioSummaryQuery);

const summaryResponse: PortfolioSummaryResponse = {
  as_of_ledger_at: "2026-04-11T00:00:00Z",
  pricing_snapshot_key: "snapshot-2026-04-11",
  pricing_snapshot_captured_at: "2026-04-11T00:00:00Z",
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

function renderHoldingsPage(path = "/portfolio/holdings") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <PortfolioHoldingsPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioHoldingsPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    installMatchMediaMock(false);
  });

  it("renders loading state while holdings query is pending", () => {
    setSummaryState({ isLoading: true });

    const { container } = renderHoldingsPage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("renders explicit empty state when holdings rows are unavailable", () => {
    setSummaryState({
      isSuccess: true,
      data: { ...summaryResponse, rows: [] },
    });

    renderHoldingsPage();

    expect(
      screen.getByRole("heading", { name: "No holdings are available yet" }),
    ).toBeInTheDocument();
  });

  it("renders explicit error state for holdings failures", () => {
    setSummaryState({
      isError: true,
      error: new AppApiError("Network", {
        kind: "network_error",
        detail: "Holdings summary request failed.",
      }),
    });

    renderHoldingsPage();

    expect(screen.getByRole("heading", { name: "Holdings unavailable" })).toBeInTheDocument();
    expect(screen.getAllByText("Holdings summary request failed.").length).toBeGreaterThan(0);
  });

  it("renders ledger-first success modules with dominant-job and hero-insight viewport roles", () => {
    setSummaryState({
      isSuccess: true,
      data: summaryResponse,
    });

    const { container } = renderHoldingsPage();

    expect(screen.getByRole("heading", { name: "Holdings ledger pulse" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Portfolio summary" })).toBeInTheDocument();
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(
      container.querySelector('[data-first-viewport-role="dominant-job"]'),
    ).toBeInTheDocument();
    expect(
      container.querySelector('[data-first-viewport-role="hero-insight"]'),
    ).toBeInTheDocument();
  });
});
