/* @vitest-environment jsdom */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { render, screen } from "@testing-library/react";
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

import { PortfolioAssetDetailPage } from "../pages/portfolio-asset-detail-page/PortfolioAssetDetailPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";

function setViewportWidth(width: number): void {
  Object.defineProperty(window, "innerWidth", {
    value: width,
    writable: true,
    configurable: true,
  });
  window.dispatchEvent(new Event("resize"));
}

describe("responsive layout contract", () => {
  it("4.14 applies route-aware density adaptation at 320/768/1024/1440 breakpoints", () => {
    const breakpointWidths = [320, 768, 1024, 1440];
    const expectedHomeDensity = [
      "ultra-compact",
      "compact",
      "balanced",
      "comfortable",
    ];
    const expectedAssetDensity = [
      "ultra-compact",
      "compact",
      "compact",
      "dense",
    ];

    breakpointWidths.forEach((breakpointWidth, index) => {
      setViewportWidth(breakpointWidth);
      const homeRender = render(
        <MemoryRouter initialEntries={["/portfolio/home"]}>
          <PortfolioHomePage />
        </MemoryRouter>,
      );
      const homeShell = homeRender.container.querySelector(".compact-shell");
      expect(homeShell?.getAttribute("data-route-density")).toBe(
        expectedHomeDensity[index],
      );
      homeRender.unmount();

      const assetRender = render(
        <MemoryRouter initialEntries={["/portfolio/asset-detail/aapl"]}>
          <Routes>
            <Route
              path="/portfolio/asset-detail/:ticker"
              element={<PortfolioAssetDetailPage />}
            />
          </Routes>
        </MemoryRouter>,
      );
      const assetShell = assetRender.container.querySelector(".compact-shell");
      expect(assetShell?.getAttribute("data-route-density")).toBe(
        expectedAssetDensity[index],
      );
      assetRender.unmount();
    });
  });

  it("4.14 keeps route rendering within no-horizontal-overflow shell contract", () => {
    setViewportWidth(320);
    const routeRender = render(
      <MemoryRouter initialEntries={["/portfolio/home"]}>
        <PortfolioHomePage />
      </MemoryRouter>,
    );
    const shellContent = routeRender.container.querySelector(".compact-shell__content");
    expect(shellContent?.getAttribute("data-overflow-contract")).toBe("no-horizontal-overflow");
    expect(screen.getByRole("heading", { level: 2, name: "How is my portfolio doing right now?" })).not.toBeNull();
  });

  it("4.14 defines explicit 320/768/1024/1440 responsive media contracts in styles", () => {
    const stylesPath = resolve(process.cwd(), "src/app/styles.css");
    const stylesSource = readFileSync(stylesPath, "utf8");

    expect(stylesSource.includes("@media (max-width: 1440px)")).toBe(true);
    expect(stylesSource.includes("@media (max-width: 1024px)")).toBe(true);
    expect(stylesSource.includes("@media (max-width: 768px)")).toBe(true);
    expect(stylesSource.includes("@media (max-width: 320px)")).toBe(true);
    expect(stylesSource.includes("overflow-x: hidden")).toBe(true);
  });
});
