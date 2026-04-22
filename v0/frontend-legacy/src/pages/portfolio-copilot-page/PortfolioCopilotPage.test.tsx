/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "../../app/theme";
import { AppApiError } from "../../core/api/errors";
import type {
  PortfolioCopilotChatRequest,
  PortfolioCopilotChatResponse,
} from "../../core/api/schemas";
import { usePortfolioCopilotChatMutation } from "../../features/portfolio-copilot/hooks";
import { PortfolioCopilotWorkspaceProvider } from "../../features/portfolio-copilot/workspace-session";
import { PortfolioCopilotPage } from "./PortfolioCopilotPage";

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

function setMutationState(state: CopilotMutationState): void {
  mockedUsePortfolioCopilotChatMutation.mockReturnValue(
    state as ReturnType<typeof usePortfolioCopilotChatMutation>,
  );
}

function renderCopilotPage(path = "/portfolio/copilot") {
  return render(
    <ThemeProvider>
      <PortfolioCopilotWorkspaceProvider>
        <MemoryRouter initialEntries={[path]}>
          <PortfolioCopilotPage />
        </MemoryRouter>
      </PortfolioCopilotWorkspaceProvider>
    </ThemeProvider>,
  );
}

describe("PortfolioCopilotPage", () => {
  beforeEach(() => {
    installMatchMediaMock(false);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders idle state before first request", () => {
    setMutationState({
      isPending: false,
      mutateAsync: vi.fn(),
    });

    renderCopilotPage();

    expect(
      screen.getByText("idle: waiting for one bounded read-only request."),
    ).toBeInTheDocument();
    expect(screen.getByText("Evidence and handoff panel")).toBeInTheDocument();
  });

  it("renders ready state with evidence and limitations after successful chat response", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockImplementation(async (_request: PortfolioCopilotChatRequest) => ({
        state: "ready",
        answer_text: "Risk concentration increased in one technology position.",
        evidence: [
          {
            tool_id: "portfolio_risk_estimators",
            metric_id: "metrics",
            as_of_ledger_at: "2026-04-01T00:00:00Z",
          },
        ],
        limitations: [
          "Read-only analytical copilot; no trade execution.",
          "Not financial advice.",
        ],
        reason_code: null,
        opportunity_candidates: [],
        opportunity_narration: null,
        prompt_suggestions: [],
      }));
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Explain my latest risk posture changes.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "ready" })).toBeInTheDocument(),
    );
    expect(screen.getByText("portfolio_risk_estimators")).toBeInTheDocument();
    expect(screen.getByText("Not financial advice.")).toBeInTheDocument();
  });

  it("renders markdown table structure in ready response text", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockImplementation(async (_request: PortfolioCopilotChatRequest) => ({
        state: "ready",
        answer_text: [
          "### Snapshot",
          "",
          "| Metric | Value |",
          "|--------|-------|",
          "| Sharpe ratio | -0.44 |",
        ].join("\n"),
        evidence: [],
        limitations: ["Read-only analytical copilot; no trade execution."],
        reason_code: null,
        opportunity_candidates: [],
        opportunity_narration: null,
        prompt_suggestions: [],
      }));
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Render markdown table please.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1));
    expect(screen.getAllByRole("columnheader", { name: "Metric" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("columnheader", { name: "Value" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("cell", { name: "Sharpe ratio" }).length).toBeGreaterThan(0);
  });

  it("renders blocked state with stable reason messaging", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockImplementation(async (_request: PortfolioCopilotChatRequest) => ({
        state: "blocked",
        answer_text: "",
        evidence: [],
        limitations: ["Request blocked by provider policy."],
        reason_code: "provider_blocked_policy",
        opportunity_candidates: [],
        opportunity_narration: null,
        prompt_suggestions: [],
      }));
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Do this automatically for me.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() =>
      expect(screen.getByText(/blocked:/i)).toHaveTextContent(
        "Provider policy or permission blocked this request.",
      ),
    );
  });

  it("renders deterministic opportunity candidates separately from AI narration", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockImplementation(async (_request: PortfolioCopilotChatRequest) => ({
        state: "ready",
        answer_text: "Two discounted candidates remain after deterministic filtering.",
        evidence: [],
        limitations: ["Deterministic candidate scoring precedes narration."],
        reason_code: null,
        opportunity_candidates: [
          {
            symbol: "AAA",
            currently_held: true,
            action_state: "double_down_candidate",
            action_multiplier: "2.000000",
            action_reason_codes: [
              "strategy_profile_dca_2x_v1",
              "double_down_threshold_met",
            ],
            fundamentals_proxy_state: "passed",
            fundamentals_proxy_score: "1.000000",
            opportunity_score: "0.810000",
            discount_score: "0.920000",
            momentum_score: "0.700000",
            stability_score: "0.720000",
            latest_close_price_usd: "95.00",
            rolling_90d_high_price_usd: "120.00",
            rolling_52w_high_price_usd: "125.00",
            drawdown_from_52w_high_pct: "0.240000",
            return_30d: "0.040000",
            return_90d: "0.080000",
            return_252d: "0.150000",
            volatility_30d: "0.180000",
          },
        ],
        opportunity_narration: [
          "### Drivers",
          "",
          "- AAA leads due to larger discount and positive momentum.",
        ].join("\n"),
        prompt_suggestions: [],
      }));
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    await user.selectOptions(
      screen.getAllByRole("combobox", { name: "Copilot operation" })[0],
      "opportunity_scan",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Find discounted opportunity candidates.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() => expect(screen.getByText("AAA")).toBeInTheDocument());
    expect(screen.getByText("AI narration")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Drivers" })).toBeInTheDocument();
    expect(
      screen.getByText("AAA leads due to larger discount and positive momentum."),
    ).toBeInTheDocument();
  });

  it("4.5 renders bounded suggestion chips and sends suggestion directly as a new chat message", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockImplementation(async (_request: PortfolioCopilotChatRequest) => ({
        state: "ready",
        answer_text: "Suggestion metadata loaded.",
        evidence: [],
        limitations: ["Read-only analytical copilot."],
        reason_code: null,
        opportunity_candidates: [],
        opportunity_narration: null,
        prompt_suggestions: [
          "Compare risk posture versus last month.",
          "Summarize concentration changes by symbol.",
          "What evidence supports this conclusion?",
          "List limitations for this answer.",
        ],
      }));
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Show me something",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() =>
      expect(
        screen.getAllByRole("button", {
          name: "Compare risk posture versus last month.",
        }).length,
      ).toBeGreaterThan(0),
    );

    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "draft to replace",
    );
    const compareRiskButtons = screen.getAllByRole("button", {
      name: "Compare risk posture versus last month.",
    });
    await user.click(compareRiskButtons[0]);
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(2));
    expect(mutateAsync).toHaveBeenLastCalledWith(
      expect.objectContaining({
        messages: expect.arrayContaining([
          expect.objectContaining({
            content: "Compare risk posture versus last month.",
            role: "user",
          }),
        ]),
      }),
    );
  });

  it("4.6 uses Shift+Enter for submit and hides document reference controls in expanded chat", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockImplementation(async (_request: PortfolioCopilotChatRequest) => ({
        state: "ready",
        answer_text: "Attached references accepted.",
        evidence: [],
        limitations: ["Read-only analytical copilot."],
        reason_code: null,
        opportunity_candidates: [],
        opportunity_narration: null,
        prompt_suggestions: [],
      }));
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    expect(screen.queryByText("Document references")).not.toBeInTheDocument();
    const messageBox = screen.getByRole("textbox", { name: "Copilot user message" });
    await user.type(messageBox, "Use attached report context.");
    fireEvent.keyDown(messageBox, { key: "Enter", shiftKey: true });

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1));
    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        document_ids: [],
      }),
    );
  });

  it("renders error banner when request throws one API error", async () => {
    const user = userEvent.setup();
    const mutateAsync: CopilotMutationState["mutateAsync"] = vi
      .fn()
      .mockRejectedValue(
        new AppApiError("Provider unavailable.", {
          kind: "server_error",
          detail: "Provider unavailable.",
        }),
      );
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Summarize current risk context.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() =>
      expect(screen.getByText("Copilot error")).toBeInTheDocument(),
    );
    expect(screen.getByText("Provider unavailable.")).toBeInTheDocument();
  });
});
