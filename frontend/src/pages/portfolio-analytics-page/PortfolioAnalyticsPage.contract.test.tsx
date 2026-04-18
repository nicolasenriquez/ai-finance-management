/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { PortfolioAnalyticsPage } from "./PortfolioAnalyticsPage";

describe("PortfolioAnalyticsPage contract", () => {
  it("4.2 exposes explainability modules with curve, waterfall, leaders, heatmap, rolling chart, and drill-down table", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/analytics"]}>
        <PortfolioAnalyticsPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 2, name: "Why did the portfolio move?" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Performance curve" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Attribution waterfall" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Contribution leaders" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Monthly return heatmap" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Rolling return chart" }),
    ).not.toBeNull();
    expect(
      screen.getByRole("heading", { level: 3, name: "Drill-down contribution table" }),
    ).not.toBeNull();

    const advancedDisclosureSummary = screen.getByText("Advanced attribution disclosure");
    expect(advancedDisclosureSummary.tagName).toBe("SUMMARY");
    expect(
      screen.getByText("Deeper decomposition stays bounded so this route answers why first."),
    ).not.toBeNull();
  });
});
