/* @vitest-environment jsdom */

import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import {
  MemoryRouter,
  Route,
  Routes,
} from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { AppProviders } from "../../app/providers";
import { PortfolioAnalyticsPage } from "../portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioHomePage } from "../portfolio-home-page/PortfolioHomePage";
import { PortfolioRiskPage } from "../portfolio-risk-page/PortfolioRiskPage";
import { PortfolioSignalsPage } from "../portfolio-signals-page/PortfolioSignalsPage";
import { PortfolioAssetDetailPage } from "./PortfolioAssetDetailPage";

describe("PortfolioAssetDetailPage contract", () => {
  it("4.5 exposes asset deep-dive modules for hero, price action, price-volume combo, detail, benchmark, risk, and narrative notes", () => {
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

    expect(
      screen.getByRole("heading", { level: 2, name: "MSFT deep dive" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Asset hero" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Price action" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Price-volume combo" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Position detail" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Benchmark-relative chart" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Asset risk metrics" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Narrative notes" }),
    ).not.toBeNull();
  });

  it("3.6 keeps candlestick treatment out of executive routes", () => {
    cleanup();
    const executiveRoutes = [
      <PortfolioHomePage key="home" />,
      <PortfolioAnalyticsPage key="analytics" />,
      <PortfolioRiskPage key="risk" />,
      <PortfolioSignalsPage key="signals" />,
    ];

    for (const executiveRouteElement of executiveRoutes) {
      const { queryByText, unmount } = render(
        <MemoryRouter>
          <AppProviders>{executiveRouteElement}</AppProviders>
        </MemoryRouter>,
      );
      expect(queryByText(/candlestick/i)).toBeNull();
      unmount();
    }
  });
});
