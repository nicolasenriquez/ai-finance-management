/* @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  describe,
  expect,
  it,
} from "vitest";

import { AppProviders } from "./providers";
import { CompactDashboardShell } from "../components/shell/CompactDashboardShell";

describe("compact dashboard information architecture contract", () => {
  it("3.1 keeps exactly five primary compact routes with one decision job per route", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio/home"]}>
        <AppProviders>
          <CompactDashboardShell
            title="Portfolio Home"
            subtitle="Executive view"
          >
            <section>Test content</section>
          </CompactDashboardShell>
        </AppProviders>
      </MemoryRouter>,
    );

    const routeLinks = screen.getAllByRole("link");
    expect(routeLinks).toHaveLength(5);
    expect(routeLinks.map((link) => link.textContent?.trim())).toEqual([
      "Home",
      "Analytics",
      "Risk",
      "Opportunities",
      "Asset Detail",
    ]);

    const journeyRail = screen.getByRole("list", { name: "Route decision journey" });
    expect(journeyRail.textContent).toContain("How is my portfolio doing right now?");
    expect(journeyRail.textContent).toContain("Why did the portfolio move?");
    expect(journeyRail.textContent).toContain("How fragile is the portfolio?");
    expect(journeyRail.textContent).toContain("Which opportunities deserve review?");
    expect(journeyRail.textContent).toContain("What is happening with this asset?");
  });
});
