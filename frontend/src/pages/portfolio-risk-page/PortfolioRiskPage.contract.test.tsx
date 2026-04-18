/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { PortfolioRiskPage } from "./PortfolioRiskPage";

describe("PortfolioRiskPage contract", () => {
  it("4.3 exposes fragility modules with posture, drawdown, distribution, scatter, heatmap, and concentration table", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/risk"]}>
        <PortfolioRiskPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 2, name: "How fragile is the portfolio?" }),
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
      screen.getByText("Action state: de-risk concentration"),
    ).not.toBeNull();
    expect(
      screen.getByText("Advanced risk disclosure"),
    ).not.toBeNull();
  });
});
