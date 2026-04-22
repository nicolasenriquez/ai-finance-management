/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  MemoryRouter,
  Route,
  Routes,
  useLocation,
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
import type {
  PortfolioSummaryResponse,
  PortfolioTimeSeriesResponse,
} from "../../core/api/schemas";
import { fetchPortfolioSummary } from "../../features/portfolio-summary/api";
import { fetchPortfolioTimeSeries } from "../../features/portfolio-workspace/api";
import { PortfolioWorkspaceLayout } from "./PortfolioWorkspaceLayout";

vi.mock("../../features/portfolio-summary/api", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-summary/api")
  >("../../features/portfolio-summary/api");
  return {
    ...actual,
    fetchPortfolioSummary: vi.fn(),
  };
});

vi.mock("../../features/portfolio-workspace/api", async () => {
  const actual = await vi.importActual<
    typeof import("../../features/portfolio-workspace/api")
  >("../../features/portfolio-workspace/api");
  return {
    ...actual,
    fetchPortfolioTimeSeries: vi.fn(),
  };
});

const mockedFetchPortfolioSummary = vi.mocked(fetchPortfolioSummary);
const mockedFetchPortfolioTimeSeries = vi.mocked(fetchPortfolioTimeSeries);

function WorkspacePathIndicator() {
  const location = useLocation();
  return <p data-testid="workspace-current-path">{location.pathname}</p>;
}

function WorkspaceHarness() {
  return (
    <>
      <WorkspacePathIndicator />
      <PortfolioWorkspaceLayout
        eyebrow="Workspace"
        title="Workspace route"
        description="Route test harness"
        scopeLabel="Scope"
        provenanceLabel="Provenance"
      >
        <p>Workspace content</p>
      </PortfolioWorkspaceLayout>
    </>
  );
}

function renderWorkspaceRoute(path: string) {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/portfolio/dashboard" element={<WorkspaceHarness />} />
          <Route path="/portfolio/holdings" element={<WorkspaceHarness />} />
          <Route path="/portfolio/performance" element={<WorkspaceHarness />} />
          <Route path="/portfolio/home" element={<WorkspaceHarness />} />
          <Route path="/portfolio/analytics" element={<WorkspaceHarness />} />
          <Route path="/portfolio/risk" element={<WorkspaceHarness />} />
          <Route path="/portfolio/rebalancing" element={<WorkspaceHarness />} />
          <Route path="/portfolio/reports" element={<WorkspaceHarness />} />
          <Route path="/portfolio/copilot" element={<WorkspaceHarness />} />
          <Route path="/portfolio/transactions" element={<WorkspaceHarness />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

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

function buildEmptySummaryResponse(): PortfolioSummaryResponse {
  return {
    as_of_ledger_at: "2026-04-05T00:00:00Z",
    pricing_snapshot_key: null,
    pricing_snapshot_captured_at: null,
    rows: [],
  };
}

function buildEmptyTimeSeriesResponse(): PortfolioTimeSeriesResponse {
  return {
    as_of_ledger_at: "2026-04-05T00:00:00Z",
    period: "30D",
    frequency: "daily",
    timezone: "UTC",
    points: [],
  };
}

describe("PortfolioWorkspaceLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    installMatchMediaMock(false);
    mockedFetchPortfolioSummary.mockResolvedValue(buildEmptySummaryResponse());
    mockedFetchPortfolioTimeSeries.mockResolvedValue(buildEmptyTimeSeriesResponse());
  });

  afterEach(() => {
    cleanup();
  });

  it.each([
    {
      activeLabel: "Dashboard",
      path: "/portfolio/dashboard",
    },
    {
      activeLabel: "Holdings",
      path: "/portfolio/holdings",
    },
    {
      activeLabel: "Performance",
      path: "/portfolio/performance",
    },
    {
      activeLabel: "Risk",
      path: "/portfolio/risk",
    },
    {
      activeLabel: "Rebalancing",
      path: "/portfolio/rebalancing",
    },
    {
      activeLabel: "Copilot",
      path: "/portfolio/copilot",
    },
    {
      activeLabel: "Transactions",
      path: "/portfolio/transactions",
    },
  ])("maps route state to active navigation link for $path", ({ activeLabel, path }) => {
    renderWorkspaceRoute(path);

    const navigation = screen.getByRole("navigation", {
      name: "Portfolio analytics workspace navigation",
    });
    const links = [
      "Dashboard",
      "Holdings",
      "Performance",
      "Risk",
      "Rebalancing",
      "Copilot",
      "Transactions",
    ].map((label) => within(navigation).getByRole("link", { name: label }));

    for (const link of links) {
      if (link.textContent?.includes(activeLabel)) {
        expect(link).toHaveClass("workspace-nav__link--active");
        expect(link).toHaveAttribute("aria-current", "page");
      } else {
        expect(link).not.toHaveClass("workspace-nav__link--active");
        expect(link).not.toHaveAttribute("aria-current", "page");
      }
    }
  });

  it("supports keyboard tab navigation and enter activation between workspace routes", async () => {
    const user = userEvent.setup();
    renderWorkspaceRoute("/portfolio/dashboard");

    const dashboardLink = screen.getByRole("link", { name: "Dashboard" });
    const performanceLink = screen.getByRole("link", { name: "Performance" });
    const copilotLink = screen.getByRole("link", { name: "Copilot" });
    const riskLink = screen.getByRole("link", { name: "Risk" });

    async function tabUntilFocus(target: HTMLElement, maxTabs = 24): Promise<void> {
      for (let index = 0; index < maxTabs; index += 1) {
        await user.tab();
        if (target === document.activeElement) {
          return;
        }
      }
    }

    await tabUntilFocus(dashboardLink);
    expect(dashboardLink).toHaveFocus();

    await tabUntilFocus(performanceLink);
    expect(performanceLink).toHaveFocus();

    await tabUntilFocus(copilotLink);
    expect(copilotLink).toHaveFocus();

    await tabUntilFocus(riskLink);
    expect(riskLink).toHaveFocus();

    await user.keyboard("{Enter}");

    expect(screen.getByTestId("workspace-current-path")).toHaveTextContent(
      "/portfolio/risk",
    );
    expect(screen.getByRole("link", { name: "Risk" })).toHaveClass(
      "workspace-nav__link--active",
    );
  });

  it("renders compact trust metadata with dedicated provenance row", () => {
    renderWorkspaceRoute("/portfolio/dashboard");

    expect(screen.getAllByText("Scope").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Provenance").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Data provenance")).toBeInTheDocument();
  });

  it("applies deterministic shell density mode by route across navigation transitions", async () => {
    const user = userEvent.setup();
    renderWorkspaceRoute("/portfolio/dashboard");

    const shellContainer = document.querySelector("[data-shell-density-mode]");
    expect(shellContainer).toHaveAttribute("data-shell-density-mode", "expanded");

    await user.click(screen.getByRole("link", { name: "Risk" }));
    expect(screen.getByTestId("workspace-current-path")).toHaveTextContent("/portfolio/risk");
    expect(shellContainer).toHaveAttribute("data-shell-density-mode", "compact");

    await user.click(screen.getByRole("link", { name: "Performance" }));
    expect(screen.getByTestId("workspace-current-path")).toHaveTextContent(
      "/portfolio/performance",
    );
    expect(shellContainer).toHaveAttribute("data-shell-density-mode", "standard");
  });

  it("exposes explicit active-lens attribute for shell orientation", () => {
    renderWorkspaceRoute("/portfolio/transactions");

    const shellContainer = document.querySelector("[data-workspace-lens]");
    expect(shellContainer).toHaveAttribute("data-workspace-lens", "cash-transactions");
    expect(screen.getByText(/active lens orientation/i)).toBeInTheDocument();
  });

  it("renders top mover percent without double scaling summary percentage values", async () => {
    mockedFetchPortfolioSummary.mockResolvedValue({
      as_of_ledger_at: "2026-04-05T00:00:00Z",
      pricing_snapshot_key: "snapshot-1",
      pricing_snapshot_captured_at: "2026-04-05T00:00:00Z",
      rows: [
        {
          instrument_symbol: "PLTR",
          open_quantity: "10.000000000",
          open_cost_basis_usd: "1000.00",
          open_lot_count: 1,
          realized_proceeds_usd: "0.00",
          realized_cost_basis_usd: "0.00",
          realized_gain_usd: "0.00",
          dividend_gross_usd: "0.00",
          dividend_taxes_usd: "0.00",
          dividend_net_usd: "0.00",
          latest_close_price_usd: "156.83",
          market_value_usd: "1568.30",
          unrealized_gain_usd: "568.30",
          unrealized_gain_pct: "56.83",
        },
      ],
    });

    renderWorkspaceRoute("/portfolio/dashboard");

    expect(await screen.findByText("PLTR +56.83%")).toBeInTheDocument();
    expect(screen.queryByText("PLTR +5683.00%")).not.toBeInTheDocument();
  });
});
