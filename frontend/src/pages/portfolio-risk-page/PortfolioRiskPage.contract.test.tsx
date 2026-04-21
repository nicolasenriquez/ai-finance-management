/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { AppProviders } from "../../app/providers";
import { PortfolioRiskPage } from "./PortfolioRiskPage";

describe("PortfolioRiskPage contract", () => {
  it("4.3 exposes fragility modules with posture, drawdown, distribution, scatter, heatmap, and concentration table", async () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/risk"]}>
        <AppProviders>
          <PortfolioRiskPage />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "How fragile is the portfolio?" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Risk posture" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Drawdown timeline" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Return distribution" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Risk/return scatter" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Correlation heatmap" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Concentration table" }),
    ).not.toBeNull();
    expect(
      screen.getAllByText(/Action state:/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("Advanced risk disclosure"),
    ).not.toBeNull();
  });
});
