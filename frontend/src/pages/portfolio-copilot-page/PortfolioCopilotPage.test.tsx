/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
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
      <MemoryRouter initialEntries={[path]}>
        <PortfolioCopilotPage />
      </MemoryRouter>
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
    expect(screen.getByText("Evidence panel")).toBeInTheDocument();
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
            opportunity_score: "0.810000",
            discount_score: "0.920000",
            momentum_score: "0.700000",
            stability_score: "0.720000",
            latest_close_price_usd: "95.00",
            rolling_90d_high_price_usd: "120.00",
            return_30d: "0.040000",
            volatility_30d: "0.180000",
          },
        ],
        opportunity_narration: "AAA leads due to larger discount and positive momentum.",
      }));
    setMutationState({
      isPending: false,
      mutateAsync,
    });

    renderCopilotPage();

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Copilot operation" }),
      "opportunity_scan",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Copilot user message" }),
      "Find discounted opportunity candidates.",
    );
    await user.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() => expect(screen.getByText("AAA")).toBeInTheDocument());
    expect(screen.getByText("AI narration")).toBeInTheDocument();
    expect(
      screen.getByText("AAA leads due to larger discount and positive momentum."),
    ).toBeInTheDocument();
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
