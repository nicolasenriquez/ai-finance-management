/* @vitest-environment jsdom */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  cleanup,
  render,
  screen,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
import { PortfolioAssetDetailPage } from "../pages/portfolio-asset-detail-page/PortfolioAssetDetailPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";

describe("compact preserved behaviors contract", () => {
  it("3.7 keeps report utility compact in bounded disclosure and out of standalone routing", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/home"]}>
        <AppProviders>
          <PortfolioHomePage />
        </AppProviders>
      </MemoryRouter>,
    );

    const utilitySummary = screen.getByText("Compact report utility");
    expect(utilitySummary.tagName).toBe("SUMMARY");

    const routerSourcePath = resolve(process.cwd(), "src/app/router.tsx");
    expect(existsSync(routerSourcePath)).toBe(true);
    const routerSource = readFileSync(routerSourcePath, "utf8");
    expect(/path:\s*"reports"/.test(routerSource)).toBe(false);
  });

  it(
    "3.7 preserves grouped-row hierarchy pivot expand/collapse for holdings and position detail",
    async () => {
      cleanup();
      const user = userEvent.setup();

      const homeRender = render(
        <MemoryRouter initialEntries={["/portfolio/home"]}>
          <AppProviders>
            <PortfolioHomePage />
          </AppProviders>
        </MemoryRouter>,
      );

      await user.click(screen.getAllByText("Holdings summary pivot")[0]);
      await user.click(screen.getByRole("button", { name: /show technology \(2 positions\)/i }));
      const holdingsPivotTable = screen.getByRole("table", {
        name: "Home holdings hierarchy pivot",
      });
      expect(within(holdingsPivotTable).getByText("MSFT")).not.toBeNull();
      expect(within(holdingsPivotTable).getByText("AMD")).not.toBeNull();

      await user.click(screen.getByRole("button", { name: /hide technology \(2 positions\)/i }));
      expect(within(holdingsPivotTable).queryByText("MSFT")).toBeNull();

      homeRender.unmount();

      render(
        <MemoryRouter initialEntries={["/portfolio/asset-detail/aapl"]}>
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

      await user.click(screen.getByText("Position detail pivot"));
      await user.click(screen.getByRole("button", { name: /show core lots \(2 positions\)/i }));

      expect(screen.getByText("Lot A · opened 2024-01-12")).not.toBeNull();
      expect(screen.getByText("Lot B · opened 2024-07-03")).not.toBeNull();
    },
    20000,
  );
});
