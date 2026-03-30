/* @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import {
  render,
  screen,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { ThemeProvider } from "../../app/theme";
import { AppShell } from "./AppShell";

function installMatchMediaMock(prefersDark: boolean): void {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: (query: string): MediaQueryList => ({
      matches:
        query === "(prefers-color-scheme: dark)" ? prefersDark : false,
      media: query,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
      addListener: () => undefined,
      removeListener: () => undefined,
    }),
  });
}

describe("AppShell", () => {
  it("renders compact route framing without the old explainer hero cards", () => {
    installMatchMediaMock(false);

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/portfolio"]}>
          <AppShell
            actions={<a href="/portfolio/VOO">Inspect VOO</a>}
            description="Grouped portfolio metrics from persisted ledger state."
            eyebrow="Portfolio analytics"
            title="Portfolio ledger workspace"
          >
            <div>Body content</div>
          </AppShell>
        </MemoryRouter>
      </ThemeProvider>,
    );

    expect(
      screen.getByRole("heading", { name: "Portfolio ledger workspace" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Body content")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Inspect VOO" })).toBeInTheDocument();
    expect(screen.queryByText("Ledger-only v1")).not.toBeInTheDocument();
    expect(screen.queryByText("Source posture")).not.toBeInTheDocument();
    expect(screen.queryByText("UX baseline")).not.toBeInTheDocument();
  });
});
