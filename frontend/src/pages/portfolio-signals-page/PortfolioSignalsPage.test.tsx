/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { AppProviders } from "../../app/providers";
import { PortfolioSignalsPage } from "./PortfolioSignalsPage";

describe("PortfolioSignalsPage", () => {
  it("renders opportunities heading", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/signals"]}>
        <AppProviders>
          <PortfolioSignalsPage />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: "Portfolio Signals" }),
    ).not.toBeNull();
  });
});
