/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  MemoryRouter,
  Route,
  Routes,
} from "react-router-dom";
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
import type { PortfolioLotDetailResponse } from "../../core/api/schemas";
import { usePortfolioLotDetailQuery } from "../../features/portfolio-lot-detail/hooks";
import { PortfolioLotDetailPage } from "./PortfolioLotDetailPage";

vi.mock("../../features/portfolio-lot-detail/hooks", () => ({
  usePortfolioLotDetailQuery: vi.fn(),
}));

type LotDetailQueryState = {
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  data?: PortfolioLotDetailResponse;
  error?: unknown;
  refetch: () => Promise<unknown>;
};

const mockedUsePortfolioLotDetailQuery = vi.mocked(usePortfolioLotDetailQuery);

const lotDetailSuccess: PortfolioLotDetailResponse = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  instrument_symbol: "VOO",
  lots: [
    {
      lot_id: 15,
      opened_on: "2025-12-01",
      original_qty: "4.000000000",
      remaining_qty: "2.000000000",
      total_cost_basis_usd: "900.00",
      unit_cost_basis_usd: "225.00",
      dispositions: [
        {
          sell_transaction_id: 88,
          disposition_date: "2026-01-10",
          matched_qty: "2.000000000",
          matched_cost_basis_usd: "450.00",
          sell_gross_amount_usd: "500.00",
        },
      ],
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

function setLotDetailQueryState(state: Partial<LotDetailQueryState>): void {
  const queryState: LotDetailQueryState = {
    isLoading: false,
    isError: false,
    isSuccess: false,
    data: undefined,
    error: undefined,
    refetch: vi.fn().mockResolvedValue(undefined),
    ...state,
  };

  mockedUsePortfolioLotDetailQuery.mockReturnValue(
    queryState as ReturnType<typeof usePortfolioLotDetailQuery>,
  );
}

function renderLotDetailPage(path = "/portfolio/VOO") {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/portfolio/:symbol" element={<PortfolioLotDetailPage />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("PortfolioLotDetailPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    installMatchMediaMock(false);
  });

  it("renders loading state while lot detail request is pending", () => {
    setLotDetailQueryState({
      isLoading: true,
    });

    const { container } = renderLotDetailPage();

    expect(container.querySelector(".skeleton-table")).toBeInTheDocument();
  });

  it("maps not-found responses to warning state with retry and back navigation", async () => {
    const user = userEvent.setup();
    const refetch = vi.fn().mockResolvedValue(undefined);

    setLotDetailQueryState({
      isError: true,
      error: new AppApiError("Not found", {
        kind: "not_found",
        detail: "Instrument VOO was not found in the portfolio ledger.",
      }),
      refetch,
    });

    renderLotDetailPage();

    expect(
      screen.getByRole("heading", { name: "Instrument not found" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Instrument VOO was not found in the portfolio ledger."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to summary" })).toHaveAttribute(
      "href",
      "/portfolio",
    );

    await user.click(screen.getByRole("button", { name: "Retry request" }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("renders empty state when symbol resolves without lot rows", () => {
    setLotDetailQueryState({
      isSuccess: true,
      data: {
        ...lotDetailSuccess,
        lots: [],
      },
    });

    renderLotDetailPage();

    expect(
      screen.getByRole("heading", { name: "No lots found for this instrument" }),
    ).toBeInTheDocument();
  });

  it("renders lot detail success state with canonical symbol content", () => {
    setLotDetailQueryState({
      isSuccess: true,
      data: lotDetailSuccess,
    });

    renderLotDetailPage();

    expect(
      screen.getByRole("heading", { name: "Lot detail" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("VOO").length).toBeGreaterThan(0);
    expect(screen.getByText("Lot #15")).toBeInTheDocument();
  });

  it("normalizes route symbol input before querying lot detail data", () => {
    setLotDetailQueryState({
      isLoading: true,
    });

    renderLotDetailPage("/portfolio/%20voo%20");

    expect(mockedUsePortfolioLotDetailQuery).toHaveBeenCalledWith("VOO");
  });
});
