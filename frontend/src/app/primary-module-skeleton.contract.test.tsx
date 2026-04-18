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

import { PortfolioAnalyticsPage } from "../pages/portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioAssetDetailPage } from "../pages/portfolio-asset-detail-page/PortfolioAssetDetailPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";
import { PortfolioRiskPage } from "../pages/portfolio-risk-page/PortfolioRiskPage";
import { PortfolioSignalsPage } from "../pages/portfolio-signals-page/PortfolioSignalsPage";

function assertPrimarySkeletonContract(): void {
  const skeletons = screen.getAllByTestId("primary-module-skeleton");
  expect(skeletons.length).toBeGreaterThan(0);
  for (const skeleton of skeletons) {
    expect(skeleton.getAttribute("data-loading-contract")).toBe("primary-module");
    expect(skeleton.getAttribute("data-skeleton-height-token")).toBe("module-height-compact");
  }
}

describe("primary module skeleton contract", () => {
  it("4.11 keeps stable skeleton geometry for all five primary routes", () => {
    const routeRenderers = [
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/home?module_state=loading"]}>
            <PortfolioHomePage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/analytics?module_state=loading"]}>
            <PortfolioAnalyticsPage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/risk?module_state=loading"]}>
            <PortfolioRiskPage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/signals?module_state=loading"]}>
            <PortfolioSignalsPage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/asset-detail/aapl?module_state=loading"]}>
            <Routes>
              <Route
                path="/portfolio/asset-detail/:ticker"
                element={<PortfolioAssetDetailPage />}
              />
            </Routes>
          </MemoryRouter>,
        ),
    ];

    for (const renderRoute of routeRenderers) {
      const routeRender = renderRoute();
      assertPrimarySkeletonContract();
      routeRender.unmount();
      cleanup();
    }
  });
});
