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
      activeLabel: "Transactions",
      path: "/portfolio/transactions",
    },
  ])("maps route state to active navigation link for $path", ({ activeLabel, path }) => {
    renderWorkspaceRoute(path);

    const links = ["Home", "Analytics (Preview)", "Risk (Interpretation)", "Transactions"].map((label) =>
      screen.getByRole("link", { name: label }),
    );

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
    const riskLink = screen.getByRole("link", { name: "Risk (Interpretation)" });

    for (let index = 0; index < 8; index += 1) {
      await user.tab();
      if (homeLink === document.activeElement) {
        break;
      }
    }
    expect(homeLink).toHaveFocus();

    for (let index = 0; index < 4; index += 1) {
      await user.tab();
      if (analyticsLink === document.activeElement) {
        break;
      }
    }
    expect(analyticsLink).toHaveFocus();

    for (let index = 0; index < 4; index += 1) {
      await user.tab();
      if (riskLink === document.activeElement) {
        break;
      }
    }
    expect(riskLink).toHaveFocus();

    await user.keyboard("{Enter}");

    expect(screen.getByTestId("workspace-current-path")).toHaveTextContent(
      "/portfolio/risk",
    );
    expect(screen.getByRole("link", { name: "Risk (Interpretation)" })).toHaveClass(
      "workspace-nav__link--active",
    );
  });
});
