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

import { AppProviders } from "./providers";
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

async function expectStoryContracts(minimumContracts: number): Promise<void> {
  const storyContracts = await screen.findAllByTestId("story-contract-block");
  expect(storyContracts.length >= minimumContracts).toBe(true);

  for (const storyContract of storyContracts) {
    for (const storyContractLabel of STORY_CONTRACT_LABELS) {
      expect(within(storyContract).getByText(storyContractLabel)).not.toBeNull();
    }
  }
}

describe("module storytelling contract", () => {
  it("3.8 applies what/why/action/evidence contract to primary blocks across all five routes", async () => {
    const routeRenderers = [
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/home"]}>
            <AppProviders>
              <PortfolioHomePage />
            </AppProviders>
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/analytics"]}>
            <AppProviders>
              <PortfolioAnalyticsPage />
            </AppProviders>
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/risk"]}>
            <AppProviders>
              <PortfolioRiskPage />
            </AppProviders>
          </MemoryRouter>,
        ),
      () =>
        render(
          <MemoryRouter initialEntries={["/portfolio/signals"]}>
            <AppProviders>
              <PortfolioSignalsPage />
            </AppProviders>
          </MemoryRouter>,
        ),
      () =>
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
        ),
    ];

    for (const renderRoute of routeRenderers) {
      const routeRender = renderRoute();
      await expectStoryContracts(3);
      routeRender.unmount();
    }
  });
});
