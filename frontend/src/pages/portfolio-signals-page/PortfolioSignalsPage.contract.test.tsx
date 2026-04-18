/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { PortfolioSignalsPage } from "./PortfolioSignalsPage";

describe("PortfolioSignalsPage contract", () => {
  it("4.4 exposes tactical review modules with trend regime, momentum ranking, technical table, and watchlist panel", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/signals"]}>
        <PortfolioSignalsPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 2, name: "Which opportunities deserve review?" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Trend regime summary" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Momentum ranking" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Technical signals table" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Watchlist panel" }),
    ).not.toBeNull();
    expect(
      screen.getAllByText(/Action state:/).length,
    ).toBeGreaterThan(0);
  });
});
