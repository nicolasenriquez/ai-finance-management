/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { PortfolioHomePage } from "./PortfolioHomePage";

describe("PortfolioHomePage contract", () => {
  it("4.1 exposes executive home modules with KPI, curve, attention, movers, allocation, and holdings table", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/home"]}>
        <PortfolioHomePage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 2, name: "How is my portfolio doing right now?" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Equity curve vs benchmark" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Needs attention immediately" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Top movers" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Allocation snapshot" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Holdings summary table" }),
    ).not.toBeNull();
    expect(
      screen.getByText("Action state: wait"),
    ).not.toBeNull();
  });
});
