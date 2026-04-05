/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  render,
  screen,
  waitFor,
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
import type {
  PortfolioCopilotChatRequest,
  PortfolioCopilotChatResponse,
} from "../../core/api/schemas";
import { usePortfolioCopilotChatMutation } from "../../features/portfolio-copilot/hooks";
import { PortfolioCopilotWorkspaceProvider } from "../../features/portfolio-copilot/workspace-session";
import { PortfolioCopilotPage } from "../../pages/portfolio-copilot-page/PortfolioCopilotPage";
import { PortfolioWorkspaceLayout } from "./PortfolioWorkspaceLayout";

vi.mock("../../features/portfolio-copilot/hooks", () => ({
  usePortfolioCopilotChatMutation: vi.fn(),
}));

type CopilotMutationState = {
  isPending: boolean;
  mutateAsync: (
    request: PortfolioCopilotChatRequest,
  ) => Promise<PortfolioCopilotChatResponse>;
};

const mockedUsePortfolioCopilotChatMutation = vi.mocked(
  usePortfolioCopilotChatMutation,
);

function installMatchMediaMock(isDesktop: boolean): void {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: vi.fn().mockImplementation((query: string): MediaQueryList => {
      const matches = query === "(min-width: 1024px)" ? isDesktop : false;
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

function setMutationState(state: CopilotMutationState): void {
  mockedUsePortfolioCopilotChatMutation.mockReturnValue(
    state as ReturnType<typeof usePortfolioCopilotChatMutation>,
  );
}

function WorkspaceHarness() {
  return (
    <PortfolioWorkspaceLayout
      eyebrow="Workspace"
      title="Launcher contract"
      description="copilot launcher test harness"
      periodLabel="90D"
      provenanceLabel="Provenance"
      scopeLabel="Scope"
    >
      <p>Body</p>
    </PortfolioWorkspaceLayout>
  );
}

function renderLauncher(path: string) {
  return render(
    <ThemeProvider>
      <PortfolioCopilotWorkspaceProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/portfolio/home" element={<WorkspaceHarness />} />
            <Route path="/portfolio/risk" element={<WorkspaceHarness />} />
          </Routes>
        </MemoryRouter>
      </PortfolioCopilotWorkspaceProvider>
    </ThemeProvider>,
  );
}

function renderLauncherWithExpandedCopilotRoute(path: string) {
  return render(
    <ThemeProvider>
      <PortfolioCopilotWorkspaceProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/portfolio/home" element={<WorkspaceHarness />} />
            <Route path="/portfolio/copilot" element={<PortfolioCopilotPage />} />
          </Routes>
        </MemoryRouter>
      </PortfolioCopilotWorkspaceProvider>
    </ThemeProvider>,
  );
}

describe("workspace copilot launcher fail-first contract", () => {
  beforeEach(() => {
    installMatchMediaMock(true);
    setMutationState({
      isPending: false,
      mutateAsync: vi.fn().mockResolvedValue({
        state: "ready",
        answer_text: "Continuity answer from docked panel.",
        evidence: [],
        limitations: ["Read-only analytical copilot."],
        reason_code: null,
        opportunity_candidates: [],
        opportunity_narration: null,
        prompt_suggestions: [],
      }),
    });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("4.1 renders one persistent workspace copilot entry and opens desktop docked panel", async () => {
    const user = userEvent.setup();
    renderLauncher("/portfolio/home");

    await user.click(screen.getByRole("button", { name: "Open workspace copilot" }));

    expect(
      screen.getByLabelText("Workspace copilot docked panel"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Collapse copilot panel" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open expanded copilot surface" }),
    ).toBeInTheDocument();
  });

  it("4.1 preserves answer continuity across collapse and re-expand on desktop", async () => {
    const user = userEvent.setup();
    renderLauncher("/portfolio/home");

    await user.click(screen.getByRole("button", { name: "Open workspace copilot" }));
    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Summarize risk posture.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() =>
      expect(screen.getByText("Continuity answer from docked panel.")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: "Collapse copilot panel" }));
    await user.click(screen.getByRole("button", { name: "Expand copilot panel" }));

    expect(screen.getByText("Continuity answer from docked panel.")).toBeInTheDocument();
  });

  it("4.1 uses full-screen copilot presentation on mobile viewport", async () => {
    const user = userEvent.setup();
    installMatchMediaMock(false);
    renderLauncher("/portfolio/home");

    await user.click(screen.getByRole("button", { name: "Open workspace copilot" }));

    expect(
      screen.getByRole("dialog", { name: "Workspace copilot mobile panel" }),
    ).toBeInTheDocument();
  });

  it("4.1 applies route context handoff into composer state when launched from one scoped route", async () => {
    const user = userEvent.setup();
    renderLauncher(
      "/portfolio/risk?period=252D&scope=instrument_symbol&instrument_symbol=AAPL",
    );

    await user.click(screen.getByRole("button", { name: "Open workspace copilot" }));

    expect(screen.getByText(/Route \/portfolio\/risk/i)).toBeInTheDocument();
    expect(screen.getByText(/Period 252D/i)).toBeInTheDocument();
    expect(screen.getByText(/Scope instrument AAPL/i)).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Copilot instrument symbol" }),
    ).toHaveValue("AAPL");
  });

  it("closes docked launcher after workspace route navigation", async () => {
    const user = userEvent.setup();
    renderLauncher("/portfolio/home");

    await user.click(screen.getByRole("button", { name: "Open workspace copilot" }));
    expect(
      screen.getByLabelText("Workspace copilot docked panel"),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Risk" }));

    await waitFor(() =>
      expect(
        screen.queryByLabelText("Workspace copilot docked panel"),
      ).not.toBeInTheDocument(),
    );
    expect(screen.getByRole("link", { name: "Risk" })).toHaveClass(
      "workspace-nav__link--active",
    );
  });

  it("6.1 restores keyboard focus to launcher trigger after closing docked panel", async () => {
    const user = userEvent.setup();
    renderLauncher("/portfolio/home");

    const launcherTrigger = screen.getByRole("button", {
      name: "Open workspace copilot",
    });
    await user.click(launcherTrigger);
    await user.click(screen.getByRole("button", { name: "Close workspace copilot" }));

    await waitFor(() => expect(launcherTrigger).toHaveFocus());
  });

  it("4.1 preserves answer/evidence/limitation continuity when moving from docked panel to expanded route", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockResolvedValue({
        state: "ready",
        answer_text: "Continuity across presentation modes.",
        evidence: [
          {
            tool_id: "portfolio_risk_estimators",
            metric_id: "metrics",
            as_of_ledger_at: "2026-04-05T00:00:00Z",
          },
        ],
        limitations: ["Read-only analytical copilot; no trade execution."],
        reason_code: null,
        opportunity_candidates: [],
        opportunity_narration: null,
        prompt_suggestions: [],
      });
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderLauncherWithExpandedCopilotRoute("/portfolio/home");

    await user.click(screen.getByRole("button", { name: "Open workspace copilot" }));
    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Carry this response forward.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() =>
      expect(
        screen.getAllByText("Continuity across presentation modes.").length,
      ).toBeGreaterThan(0),
    );
    await user.click(screen.getByRole("link", { name: "Open expanded copilot surface" }));

    await waitFor(() =>
      expect(
        screen.getAllByText("Continuity across presentation modes.").length,
      ).toBeGreaterThan(0),
    );
    expect(screen.getByText("portfolio_risk_estimators")).toBeInTheDocument();
    expect(
      screen.getByText("Read-only analytical copilot; no trade execution."),
    ).toBeInTheDocument();
  });
});
