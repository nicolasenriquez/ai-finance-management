/* @vitest-environment jsdom */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

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
  describe,
  expect,
  it,
} from "vitest";

import { AppProviders } from "./providers";
import { PortfolioAnalyticsPage } from "../pages/portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioAssetDetailPage } from "../pages/portfolio-asset-detail-page/PortfolioAssetDetailPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";
import { PortfolioRiskPage } from "../pages/portfolio-risk-page/PortfolioRiskPage";
import { PortfolioSignalsPage } from "../pages/portfolio-signals-page/PortfolioSignalsPage";

afterEach(() => {
  cleanup();
});

describe("accessibility contract", () => {
  it("4.13 keeps shell interactions keyboard reachable with semantic labeling and icon-button aria labels", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/portfolio/home"]}>
        <AppProviders>
          <PortfolioHomePage />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { level: 1, name: "Portfolio Home" })).not.toBeNull();
    expect(
      screen.getByRole("navigation", { name: "Compact dashboard routes" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("button", { name: "Toggle route decision journey" }),
    ).not.toBeNull();

    await user.click(screen.getByText("Compact report utility"));
    expect(
      screen.getByRole("button", { name: "Reset report date range" }),
    ).not.toBeNull();

    const activeRouteLink = screen.getByRole("link", { name: "Home" });
    expect(activeRouteLink.getAttribute("aria-current")).toBe("page");

    await user.tab();
    expect(document.activeElement?.textContent).toBe("Home");
  });

  it("4.13 keeps non-color-only state cues and semantic heading flow on all five routes", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/analytics"]}>
        <AppProviders>
          <PortfolioAnalyticsPage />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { level: 2, name: "Why did the portfolio move?" })).not.toBeNull();
    expect(screen.getByRole("columnheader", { name: "State cue" })).not.toBeNull();
    expect(screen.getAllByText("Strong (outperforming month)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Weak (underperforming month)").length).toBeGreaterThan(0);
  });

  it("4.13 preserves keyboard/semantic shell structure across risk, signals, and asset detail routes", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/risk"]}>
        <AppProviders>
          <PortfolioRiskPage />
        </AppProviders>
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 2, name: "How fragile is the portfolio?" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "Toggle route decision journey" })).not.toBeNull();

    cleanup();

    render(
      <MemoryRouter initialEntries={["/portfolio/signals"]}>
        <AppProviders>
          <PortfolioSignalsPage />
        </AppProviders>
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 2, name: "Which opportunities deserve review?" })).not.toBeNull();
    expect(screen.getAllByText("Availability cue: direct source extraction").length).toBeGreaterThan(0);

    cleanup();

    render(
      <MemoryRouter initialEntries={["/portfolio/asset-detail/msft"]}>
        <AppProviders>
          <Routes>
            <Route
              path="/portfolio/asset-detail/:ticker"
              element={<PortfolioAssetDetailPage />}
            />
          </Routes>
        </AppProviders>
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 2, name: "MSFT deep dive" })).not.toBeNull();
    expect(screen.getAllByText("Availability cue: direct source extraction").length).toBeGreaterThan(0);
  });

  it("4.13 defines visible focus treatment in route styles", () => {
    const stylesPath = resolve(process.cwd(), "src/app/styles.css");
    const stylesSource = readFileSync(stylesPath, "utf8");

    expect(stylesSource.includes(":focus-visible")).toBe(true);
    expect(stylesSource.includes("--focus-ring-color")).toBe(true);
  });
});
