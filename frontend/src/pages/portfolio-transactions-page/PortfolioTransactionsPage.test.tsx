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
import type { PortfolioTransactionsResponse } from "../../features/portfolio-workspace/hooks";
import { usePortfolioTransactionsQuery } from "../../features/portfolio-workspace/hooks";
import { PortfolioTransactionsPage } from "./PortfolioTransactionsPage";

vi.mock("../../features/portfolio-workspace/hooks", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-workspace/hooks")
  >("../../features/portfolio-workspace/hooks");
  return {
    ...actual,
    usePortfolioTransactionsQuery: vi.fn(),
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

const mockedUsePortfolioTransactionsQuery = vi.mocked(usePortfolioTransactionsQuery);

const transactionsResponse: PortfolioTransactionsResponse = {
  as_of_ledger_at: "2026-03-28T00:00:00Z",
  events: [
    {
      id: "evt-2",
      posted_at: "2026-03-28T00:00:00Z",
      instrument_symbol: "AAPL",
      event_type: "buy",
      quantity: "1.000000000",
      cash_amount_usd: "100.00",
    },
    {
      id: "evt-1",
      posted_at: "2026-03-27T00:00:00Z",
      instrument_symbol: "VOO",
      event_type: "sell",
      quantity: "0.500000000",
      cash_amount_usd: "150.00",
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

function setTransactionsState(
  state: Partial<QueryState<PortfolioTransactionsResponse>>,
): void {
  const queryState: QueryState<PortfolioTransactionsResponse> = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioTransactionsQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioTransactionsQuery>,
  );
}

function renderTransactionsPage(path = "/portfolio/transactions") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <PortfolioTransactionsPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioTransactionsPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    installMatchMediaMock(false);
  });

  it("renders loading state while transactions request is pending", () => {
    setTransactionsState({ isLoading: true });

    const { container } = renderTransactionsPage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("renders explicit empty state when transactions list is empty", () => {
    setTransactionsState({
      isSuccess: true,
      data: { ...transactionsResponse, events: [] },
    });

    renderTransactionsPage();

    expect(
      screen.getByRole("heading", { name: "No ledger events available yet" }),
    ).toBeInTheDocument();
  });

  it("renders explicit error state for transactions failures", () => {
    setTransactionsState({
      isError: true,
      error: new AppApiError("Network", {
        kind: "network_error",
        detail: "Unable to reach transactions route.",
      }),
    });

    renderTransactionsPage();

    expect(
      screen.getByRole("heading", { name: "Transactions route unavailable" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Unable to reach transactions route.")).toBeInTheDocument();
  });

  it("renders deterministic sorted rows and filter behavior on success", async () => {
    const user = userEvent.setup();
    setTransactionsState({
      isSuccess: true,
      data: transactionsResponse,
    });

    renderTransactionsPage();

    const table = screen.getByRole("table", { name: "Transactions list" });
    const initialRows = table.querySelectorAll("tbody tr");
    expect(initialRows).toHaveLength(2);
    expect(initialRows[0]).toHaveTextContent("AAPL");
    expect(initialRows[1]).toHaveTextContent("VOO");

    await user.type(screen.getByPlaceholderText("Filter symbol"), "VOO");
    const symbolFilteredRows = table.querySelectorAll("tbody tr");
    expect(symbolFilteredRows).toHaveLength(1);
    expect(symbolFilteredRows[0]).toHaveTextContent("VOO");

    await user.clear(screen.getByPlaceholderText("Filter symbol"));
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Filter transaction event type" }),
      "buy",
    );
    const typeFilteredRows = table.querySelectorAll("tbody tr");
    expect(typeFilteredRows).toHaveLength(1);
    expect(typeFilteredRows[0]).toHaveTextContent("AAPL");
  });
});
