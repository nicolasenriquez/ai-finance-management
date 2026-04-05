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
import { PortfolioWorkspaceLayout } from "./PortfolioWorkspaceLayout";

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
          <Route path="/portfolio/home" element={<WorkspaceHarness />} />
          <Route path="/portfolio/analytics" element={<WorkspaceHarness />} />
          <Route path="/portfolio/risk" element={<WorkspaceHarness />} />
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

describe("PortfolioWorkspaceLayout", () => {
  beforeEach(() => {
    installMatchMediaMock(false);
  });

  afterEach(() => {
    cleanup();
  });

  it.each([
    {
      activeLabel: "Home",
      path: "/portfolio/home",
    },
    {
      activeLabel: "Analytics (Preview)",
      path: "/portfolio/analytics",
    },
    {
      activeLabel: "Risk (Interpretation)",
      path: "/portfolio/risk",
    },
    {
      activeLabel: "Quant/Reports",
      path: "/portfolio/reports",
    },
    {
      activeLabel: "Copilot (Read-only)",
      path: "/portfolio/copilot",
    },
    {
      activeLabel: "Transactions",
      path: "/portfolio/transactions",
    },
  ])("maps route state to active navigation link for $path", ({ activeLabel, path }) => {
    renderWorkspaceRoute(path);

    const links = [
      "Home",
      "Analytics (Preview)",
      "Risk (Interpretation)",
      "Quant/Reports",
      "Copilot (Read-only)",
      "Transactions",
    ].map((label) => screen.getByRole("link", { name: label }));

    for (const link of links) {
      if (link.textContent === activeLabel) {
        expect(link).toHaveClass("workspace-nav__link--active");
      } else {
        expect(link).not.toHaveClass("workspace-nav__link--active");
      }
    }
  });

  it("supports keyboard tab navigation and enter activation between workspace routes", async () => {
    const user = userEvent.setup();
    renderWorkspaceRoute("/portfolio/home");

    const homeLink = screen.getByRole("link", { name: "Home" });
    const analyticsLink = screen.getByRole("link", { name: "Analytics (Preview)" });
    const copilotLink = screen.getByRole("link", { name: "Copilot (Read-only)" });
    const riskLink = screen.getByRole("link", { name: "Risk (Interpretation)" });

    async function tabUntilFocus(target: HTMLElement, maxTabs = 24): Promise<void> {
      for (let index = 0; index < maxTabs; index += 1) {
        await user.tab();
        if (target === document.activeElement) {
          return;
        }
      }
    }

    await tabUntilFocus(homeLink);
    expect(homeLink).toHaveFocus();

    await tabUntilFocus(analyticsLink);
    expect(analyticsLink).toHaveFocus();

    await tabUntilFocus(copilotLink);
    expect(copilotLink).toHaveFocus();

    await tabUntilFocus(riskLink);
    expect(riskLink).toHaveFocus();

    await user.keyboard("{Enter}");

    expect(screen.getByTestId("workspace-current-path")).toHaveTextContent(
      "/portfolio/risk",
    );
    expect(screen.getByRole("link", { name: "Risk (Interpretation)" })).toHaveClass(
      "workspace-nav__link--active",
    );
  });

  it("renders compact trust metadata with dedicated provenance row", () => {
    renderWorkspaceRoute("/portfolio/home");

    expect(screen.getAllByText("Scope").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Provenance").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Data provenance")).toBeInTheDocument();
  });
});
