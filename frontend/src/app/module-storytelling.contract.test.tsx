/* @vitest-environment jsdom */

import {
  render,
  screen,
  within,
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

const STORY_CONTRACT_LABELS = [
  "What",
  "Why",
  "Action",
  "Evidence",
] as const;

function expectStoryContracts(minimumContracts: number): void {
  const storyContracts = screen.getAllByTestId("story-contract-block");
  expect(storyContracts.length >= minimumContracts).toBe(true);

  for (const storyContract of storyContracts) {
    for (const storyContractLabel of STORY_CONTRACT_LABELS) {
      expect(within(storyContract).getByText(storyContractLabel)).not.toBeNull();
    }
  }
}

describe("module storytelling contract", () => {
  it("3.8 applies what/why/action/evidence contract to primary blocks across all five routes", () => {
    const routeRenderers = [
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/home"]}>
            <PortfolioHomePage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/analytics"]}>
            <PortfolioAnalyticsPage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/risk"]}>
            <PortfolioRiskPage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/signals"]}>
            <PortfolioSignalsPage />
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/asset-detail/msft"]}>
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
      expectStoryContracts(3);
      routeRender.unmount();
    }
  });
});
