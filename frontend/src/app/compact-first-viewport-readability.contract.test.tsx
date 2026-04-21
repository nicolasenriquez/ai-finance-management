/* @vitest-environment jsdom */

import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { AppProviders } from "./providers";
import { PortfolioAnalyticsPage } from "../pages/portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";
import { PortfolioRiskPage } from "../pages/portfolio-risk-page/PortfolioRiskPage";
import { PortfolioSignalsPage } from "../pages/portfolio-signals-page/PortfolioSignalsPage";

function setViewportWidth(width: number): void {
  Object.defineProperty(window, "innerWidth", {
    value: width,
    writable: true,
    configurable: true,
  });
  window.dispatchEvent(new Event("resize"));
}

type RouteReadabilityCase = {
  path: string;
  heading: string;
  render: () => ReactElement;
};

const ROUTE_CASES: RouteReadabilityCase[] = [
  {
    path: "/portfolio/home",
    heading: "How is my portfolio doing right now?",
    render: () => <PortfolioHomePage />,
  },
  {
    path: "/portfolio/analytics",
    heading: "Why did the portfolio move?",
    render: () => <PortfolioAnalyticsPage />,
  },
  {
    path: "/portfolio/risk",
    heading: "How fragile is the portfolio?",
    render: () => <PortfolioRiskPage />,
  },
  {
    path: "/portfolio/signals",
    heading: "Which opportunities deserve review?",
    render: () => <PortfolioSignalsPage />,
  },
];

describe("compact first-viewport readability contract", () => {
  it("5.3 keeps first-viewport route heading and overflow contract readable on 320/768/1024/1440 widths", async () => {
    const viewportWidths = [320, 768, 1024, 1440];

    for (const viewportWidth of viewportWidths) {
      setViewportWidth(viewportWidth);

      for (const routeCase of ROUTE_CASES) {
        const routeRender = render(
          <MemoryRouter initialEntries={[routeCase.path]}>
            <AppProviders>{routeCase.render()}</AppProviders>
          </MemoryRouter>,
        );

        expect(
          await screen.findByRole("heading", { level: 2, name: routeCase.heading }),
        ).not.toBeNull();
        const shellContent = routeRender.container.querySelector(".compact-shell__content");
        expect(shellContent?.getAttribute("data-overflow-contract")).toBe("no-horizontal-overflow");
        routeRender.unmount();
      }
    }
  });
});
