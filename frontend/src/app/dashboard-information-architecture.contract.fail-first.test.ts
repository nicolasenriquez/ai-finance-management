import {
  DASHBOARD_ROUTE_GOVERNANCE,
  countPrimaryWidgets,
  findDuplicatePrimaryQuestionKeys,
  resolveWorkspaceShellDensityModeForPath,
} from "../features/portfolio-workspace/dashboard-governance";

import { describe, expect, it } from "vitest";

const AUDITED_ROUTE_KEYS = new Set([
  "home",
  "analytics",
  "risk",
  "reports",
  "transactions",
]);

describe("dashboard information architecture contract", () => {
  it("2.1 enforces one dominant primary job and bounded first-surface module budgets", () => {
    const auditedRoutes = DASHBOARD_ROUTE_GOVERNANCE.filter((routeGovernance) =>
      AUDITED_ROUTE_KEYS.has(routeGovernance.routeKey),
    );

    for (const routeGovernance of auditedRoutes) {
      expect(
        routeGovernance.dominantPrimaryJobQuestion.trim().length > 0,
        `Fail-first baseline: ${routeGovernance.routeKey} must define one dominant primary analytical question.`,
      ).toBe(true);

      const primaryWidgetCount = countPrimaryWidgets(routeGovernance);
      expect(
        primaryWidgetCount,
        `Fail-first baseline: ${routeGovernance.routeKey} requires at least one primary module.`,
      ).toBeGreaterThan(0);
      expect(
        primaryWidgetCount <= routeGovernance.primaryModuleBudgetMax,
        `Fail-first baseline: ${routeGovernance.routeKey} exceeds primary module budget ${routeGovernance.primaryModuleBudgetMax}.`,
      ).toBe(true);
    }
  });

  it("2.2 blocks duplicate equal-priority visuals for the same analytical question", () => {
    const auditedRoutes = DASHBOARD_ROUTE_GOVERNANCE.filter((routeGovernance) =>
      AUDITED_ROUTE_KEYS.has(routeGovernance.routeKey),
    );

    for (const routeGovernance of auditedRoutes) {
      const duplicateQuestionKeys = findDuplicatePrimaryQuestionKeys(routeGovernance);
      expect(
        duplicateQuestionKeys,
        `Fail-first baseline: ${routeGovernance.routeKey} has duplicate primary question keys: ${duplicateQuestionKeys.join(", ")}.`,
      ).toEqual([]);
    }
  });

  it("2.4 requires progressive-disclosure contracts on high-density analytical routes", () => {
    const highDensityRouteKeys = new Set(["risk", "reports"]);
    const highDensityRoutes = DASHBOARD_ROUTE_GOVERNANCE.filter((routeGovernance) =>
      highDensityRouteKeys.has(routeGovernance.routeKey),
    );

    for (const routeGovernance of highDensityRoutes) {
      const advancedWidgetCount = routeGovernance.widgets.filter(
        (widgetGovernance) => widgetGovernance.priority === "advanced",
      ).length;
      expect(
        routeGovernance.progressiveDisclosureRequired,
        `Fail-first baseline: ${routeGovernance.routeKey} must require progressive disclosure.`,
      ).toBe(true);
      expect(
        advancedWidgetCount > 0,
        `Fail-first baseline: ${routeGovernance.routeKey} must classify at least one advanced module for disclosure.`,
      ).toBe(true);
    }
  });

  it("2.3 defines deterministic shell density policies by route path", () => {
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/home")).toBe("expanded");
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/analytics")).toBe("balanced");
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/risk")).toBe("compact");
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/reports")).toBe("compact");
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/transactions")).toBe(
      "balanced",
    );
  });
});
