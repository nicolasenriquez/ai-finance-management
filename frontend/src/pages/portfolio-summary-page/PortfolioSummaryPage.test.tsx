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
import type { PortfolioSummaryResponse } from "../../core/api/schemas";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";
import { PortfolioSummaryPage } from "./PortfolioSummaryPage";

vi.mock("../../features/portfolio-summary/hooks", () => ({
  usePortfolioSummaryQuery: vi.fn(),
}));

type SummaryQueryState = {
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  data?: PortfolioSummaryResponse;
  error?: unknown;
  refetch: () => Promise<unknown>;
};

const mockedUsePortfolioSummaryQuery = vi.mocked(usePortfolioSummaryQuery);

const summaryWithRows: PortfolioSummaryResponse = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  pricing_snapshot_key: "yf|d1|1d|3mo|aa1rp1|2026-03-24|s2|a1b2c3d4e5f6",
  pricing_snapshot_captured_at: "2026-03-24T00:55:00Z",
  rows: [
    {
      instrument_symbol: "AAPL",
      open_quantity: "2.000000000",
      open_cost_basis_usd: "1000.00",
      open_lot_count: 2,
      realized_proceeds_usd: "400.00",
      realized_cost_basis_usd: "320.00",
      realized_gain_usd: "80.00",
      dividend_gross_usd: "18.00",
      dividend_taxes_usd: "3.00",
      dividend_net_usd: "15.00",
      latest_close_price_usd: "530.00",
      market_value_usd: "1060.00",
      unrealized_gain_usd: "60.00",
      unrealized_gain_pct: "6.00",
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

function setSummaryQueryState(state: Partial<SummaryQueryState>): void {
  const queryState: SummaryQueryState = {
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

function renderSummaryPage() {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={["/portfolio"]}>
        <PortfolioSummaryPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioSummaryPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    installMatchMediaMock(false);
  });

  it("renders loading state while summary request is pending", () => {
    setSummaryQueryState({
      isLoading: true,
    });

    const { container } = renderSummaryPage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
    expect(screen.queryByText("Summary unavailable")).not.toBeInTheDocument();
  });

  it("renders empty state when summary is successful with zero rows", () => {
    setSummaryQueryState({
      isSuccess: true,
      data: {
        ...summaryWithRows,
        rows: [],
      },
    });

    renderSummaryPage();

    expect(
      screen.getByRole("heading", {
        name: "No portfolio ledger activity found",
      }),
    ).toBeInTheDocument();
  });

  it("maps API errors to an explicit error state with retry action", async () => {
    const user = userEvent.setup();
    const refetch = vi.fn().mockResolvedValue(undefined);

    setSummaryQueryState({
      isError: true,
      error: new AppApiError("Invalid request", {
        kind: "validation_error",
        detail: "Requested symbol payload is invalid.",
      }),
      refetch,
    });

    renderSummaryPage();

    expect(
      screen.getByRole("heading", { name: "Summary unavailable" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Requested symbol payload is invalid."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry request" }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("renders grouped summary content on success", () => {
    setSummaryQueryState({
      isSuccess: true,
      data: summaryWithRows,
    });

    renderSummaryPage();

    expect(
      screen.getByRole("heading", { name: "Portfolio summary" }),
    ).toBeInTheDocument();
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("Inspect lots")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Market-enriched valuation with explicit pricing snapshot provenance.",
      ),
    ).toBeInTheDocument();
  });

  it("keeps theme preference stable across summary state transitions", async () => {
    const user = userEvent.setup();
    let queryState: SummaryQueryState = {
      isLoading: true,
      isError: false,
      isSuccess: false,
      data: undefined,
      error: undefined,
      refetch: vi.fn().mockResolvedValue(undefined),
    };

    mockedUsePortfolioSummaryQuery.mockImplementation(
      () => queryState as ReturnType<typeof usePortfolioSummaryQuery>,
    );

    const view = renderSummaryPage();

    await user.click(
      screen.getByRole("button", {
        name: "Switch to dark theme",
      }),
    );
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage.getItem("ai-finance-management-theme")).toBe(
      "dark",
    );

    queryState = {
      isLoading: false,
      isError: true,
      isSuccess: false,
      data: undefined,
      error: new AppApiError("Server unavailable", {
        kind: "server_error",
        detail: "Portfolio analytics is temporarily unavailable.",
      }),
      refetch: vi.fn().mockResolvedValue(undefined),
    };

    view.rerender(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/portfolio"]}>
          <PortfolioSummaryPage />
        </MemoryRouter>
      </ThemeProvider>,
    );

    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage.getItem("ai-finance-management-theme")).toBe(
      "dark",
    );
    expect(
      screen.getByRole("button", { name: "Switch to light theme" }),
    ).toBeInTheDocument();
  });
});
