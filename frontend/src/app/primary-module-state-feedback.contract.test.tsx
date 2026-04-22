/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
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
import { PortfolioSignalsPage } from "../pages/portfolio-signals-page/PortfolioSignalsPage";

describe("primary module state feedback contract", () => {
  it("4.16 renders explicit empty/unavailable/success feedback states on primary modules", () => {
    const emptyRender = render(
      <MemoryRouter initialEntries={["/portfolio/home?module_state=empty"]}>
        <AppProviders>
          <PortfolioHomePage />
        </AppProviders>
      </MemoryRouter>,
    );
    expect(screen.getByText("No rows match current route scope.")).not.toBeNull();
    expect(screen.getByText("Module state: empty")).not.toBeNull();
    emptyRender.unmount();

    const unavailableRender = render(
      <MemoryRouter initialEntries={["/portfolio/signals?module_state=unavailable"]}>
        <AppProviders>
          <PortfolioSignalsPage />
        </AppProviders>
      </MemoryRouter>,
    );
    expect(screen.getByText("Required source contract is unavailable for this module.")).not.toBeNull();
    expect(screen.getByText("Module state: unavailable")).not.toBeNull();
    unavailableRender.unmount();

    const successRender = render(
      <MemoryRouter initialEntries={["/portfolio/asset-detail/aapl?module_state=success"]}>
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
    expect(screen.getByText("Module refresh completed successfully.")).not.toBeNull();
    expect(screen.getByText("Module state: success")).not.toBeNull();
    successRender.unmount();
  });

  it("4.16 provides retryable error feedback and recovers route modules to ready state", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/portfolio/home?module_state=error"]}>
        <AppProviders>
          <PortfolioHomePage />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(screen.getByText("Module request failed. Retry to reload route evidence.")).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "Retry module load" }));
    expect(screen.getByRole("heading", { level: 3, name: "Equity curve vs benchmark" })).not.toBeNull();
  });
});
