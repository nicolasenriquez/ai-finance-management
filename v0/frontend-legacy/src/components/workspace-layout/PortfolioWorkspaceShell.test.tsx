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
import { PortfolioWorkspaceLayout } from "./PortfolioWorkspaceLayout";

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

function WorkspaceRouteHarness() {
  return (
    <PortfolioWorkspaceLayout
      eyebrow="Workspace"
      title="Shell"
      description="Shell contract test"
      scopeLabel="Scope"
      provenanceLabel="Provenance"
      periodLabel="90D"
    >
      <p>Workspace body</p>
    </PortfolioWorkspaceLayout>
  );
}

function renderShell(path: string) {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/portfolio/dashboard" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/holdings" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/performance" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/home" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/analytics" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/risk" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/rebalancing" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/reports" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/copilot" element={<WorkspaceRouteHarness />} />
          <Route path="/portfolio/transactions" element={<WorkspaceRouteHarness />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Portfolio workspace shell", () => {
  beforeEach(() => {
    installMatchMediaMock(false);
  });

  afterEach(() => {
    cleanup();
  });

  it("renders stable navigation + context strip framing", () => {
    renderShell("/portfolio/performance");

    expect(
      screen.getByRole("navigation", {
        name: "Portfolio analytics workspace navigation",
      }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Data trust context")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Route support rail" })).toBeInTheDocument();
    expect(screen.getByText(/active lens orientation/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Performance" })).toHaveClass(
      "workspace-nav__link--active",
    );
  });

  it("opens and closes command palette from shell trigger", async () => {
    const user = userEvent.setup();
    renderShell("/portfolio/dashboard");

    await user.click(
      screen.getByRole("button", { name: "Open command palette" }),
    );
    expect(
      screen.getByRole("dialog", { name: "Workspace command palette" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(
      screen.queryByRole("dialog", { name: "Workspace command palette" }),
    ).not.toBeInTheDocument();
  });
});
