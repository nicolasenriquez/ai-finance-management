/* @vitest-environment jsdom */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { ReportUtilityDock } from "../report-utility/ReportUtilityDock";
import {
  resolveDashboardStateOwner,
  shouldAllowPropDrillDepth,
} from "./state-ownership";

describe("dashboard state ownership contract", () => {
  it("4.17 codifies local-ui, URL-state, and server-state ownership boundaries", () => {
    expect(resolveDashboardStateOwner("route_journey_visibility")).toBe("local_ui");
    expect(resolveDashboardStateOwner("module_state")).toBe("url_state");
    expect(resolveDashboardStateOwner("report_scope")).toBe("url_state");
    expect(resolveDashboardStateOwner("source_contracts")).toBe("server_state");
    expect(resolveDashboardStateOwner("yfinance_adapter_rows")).toBe("server_state");
  });

  it("4.17 keeps prop-drill depth bounded to three levels", () => {
    expect(shouldAllowPropDrillDepth(1)).toBe(true);
    expect(shouldAllowPropDrillDepth(3)).toBe(true);
    expect(shouldAllowPropDrillDepth(4)).toBe(false);
  });

  it("4.17 persists report controls as URL state for shareable views", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/portfolio/home"]}>
        <ReportUtilityDock />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText("Scope"), "symbol");
    await user.type(screen.getByLabelText("Symbol (optional)"), "nvda");
    await user.clear(screen.getByLabelText("Start date"));
    await user.type(screen.getByLabelText("Start date"), "2026-03-01");

    expect(screen.getByText(/scope=symbol/i)).not.toBeNull();
    expect(screen.getByText(/symbol=NVDA/i)).not.toBeNull();
    expect(screen.getByText(/start=2026-03-01/i)).not.toBeNull();
  });

  it("4.17 avoids introducing global store dependencies for rebuilt dashboard routes", () => {
    const sourceFiles = [
      "src/app/providers.tsx",
      "src/app/router.tsx",
      "src/pages/portfolio-home-page/PortfolioHomePage.tsx",
      "src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx",
      "src/pages/portfolio-risk-page/PortfolioRiskPage.tsx",
      "src/pages/portfolio-signals-page/components/PortfolioSignalsRouteContainer.tsx",
      "src/pages/portfolio-asset-detail-page/components/PortfolioAssetDetailRouteContainer.tsx",
    ];

    const globalStorePattern = /redux|zustand|jotai|recoil/i;

    for (const sourceFile of sourceFiles) {
      const source = readFileSync(resolve(process.cwd(), sourceFile), "utf8");
      expect(globalStorePattern.test(source)).toBe(false);
    }
  });
});
