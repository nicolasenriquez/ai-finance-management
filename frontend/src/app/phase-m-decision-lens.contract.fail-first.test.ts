/* @vitest-environment jsdom */

import { describe, expect, it } from "vitest";

import { appRouter } from "./router";
import { resolveCommandPaletteDestinations } from "../features/portfolio-workspace/command-palette";
import { DASHBOARD_ROUTE_GOVERNANCE } from "../features/portfolio-workspace/dashboard-governance";
import type { WorkspaceNavigationContext } from "../features/portfolio-workspace/context-carryover";

type RouterLikeNode = {
  path?: string;
  children?: RouterLikeNode[];
};

function findTopLevelPortfolioShellRoute():
  | (RouterLikeNode & { children: RouterLikeNode[] })
  | undefined {
  return appRouter.routes.find((route) => {
    const typedRoute = route as RouterLikeNode;
    return typedRoute.path === "/portfolio" && Array.isArray(typedRoute.children);
  }) as (RouterLikeNode & { children: RouterLikeNode[] }) | undefined;
}

const REQUIRED_DECISION_LENS_CHILD_PATHS = [
  "dashboard",
  "holdings",
  "performance",
  "risk",
  "rebalancing",
  "copilot",
  "transactions",
] as const;

describe("phase-m decision-lens information architecture fail-first contract", () => {
  it("1.4 requires router decision-lens children under /portfolio shell", () => {
    const shellRoute = findTopLevelPortfolioShellRoute();
    expect(
      shellRoute,
      "Fail-first baseline: router must expose one `/portfolio` parent route with decision-lens children for phase-m.",
    ).toBeDefined();

    const childPaths = new Set(
      (shellRoute?.children || [])
        .map((childRoute) => childRoute.path)
        .filter((pathValue): pathValue is string => typeof pathValue === "string"),
    );

    expect(
      Array.from(childPaths),
      "Fail-first baseline: `/portfolio` shell route must include dashboard/holdings/performance/risk/rebalancing/copilot/transactions child paths.",
    ).toEqual(expect.arrayContaining([...REQUIRED_DECISION_LENS_CHILD_PATHS]));
  });

  it("1.4 requires governance registry entries for dashboard and rebalancing routes", () => {
    const routeKeys = new Set(
      DASHBOARD_ROUTE_GOVERNANCE.map((routeGovernance) => String(routeGovernance.routeKey)),
    );

    expect(
      Array.from(routeKeys),
      "Fail-first baseline: dashboard governance must include dedicated dashboard and rebalancing route entries in phase-m.",
    ).toEqual(expect.arrayContaining(["dashboard", "rebalancing"]));

    const decisionRoutes = DASHBOARD_ROUTE_GOVERNANCE.filter(
      (routeGovernance) => {
        const routeKey = String(routeGovernance.routeKey);
        return routeKey === "dashboard" || routeKey === "rebalancing";
      },
    );

    expect(
      decisionRoutes.length,
      "Fail-first baseline: missing dashboard/rebalancing governance rows for first-viewport budget checks.",
    ).toBeGreaterThan(0);

    for (const decisionRoute of decisionRoutes) {
      expect(
        decisionRoute.primaryModuleBudgetMax <= 6,
        `Fail-first baseline: ${decisionRoute.routeKey} exceeds phase-m first-viewport primary budget 6.`,
      ).toBe(true);
    }
  });

  it("1.4 requires command palette route jumps for dashboard and rebalancing lenses", () => {
    const currentContext: WorkspaceNavigationContext = {
      period: "90D",
      scope: "portfolio",
      instrumentSymbol: null,
      sourceRoute: "/portfolio/dashboard",
    };

    const destinations = resolveCommandPaletteDestinations({
      query: "",
      currentContext,
      availableSymbols: ["AAPL", "MSFT"],
      watchlistSymbols: ["NVDA"],
    });

    const labels = destinations.map((destination) => destination.label.toLowerCase());
    expect(
      labels,
      "Fail-first baseline: command palette must include dashboard lens route jump in phase-m.",
    ).toEqual(expect.arrayContaining([expect.stringContaining("dashboard")]));
    expect(
      labels,
      "Fail-first baseline: command palette must include rebalancing lens route jump in phase-m.",
    ).toEqual(expect.arrayContaining([expect.stringContaining("rebalancing")]));
  });
});
