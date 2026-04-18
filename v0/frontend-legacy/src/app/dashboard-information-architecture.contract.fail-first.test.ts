import {
  DASHBOARD_ROUTE_GOVERNANCE,
  countPrimaryWidgets,
  findDuplicatePrimaryQuestionKeys,
  findPromotedInsightGovernanceGaps,
  resolveChartFitRule,
  resolveFirstViewportTemplate,
  resolveWorkspaceShellDensityModeForPath,
} from "../features/portfolio-workspace/dashboard-governance";

import { describe, expect, it } from "vitest";

const AUDITED_ROUTE_KEYS = new Set([
  "home",
  "holdings",
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

  it("2.2 defines executive first-viewport templates for primary route families", () => {
    const routeKeys = ["home", "holdings", "analytics", "transactions"] as const;
    const routeLookup = new Map(
      DASHBOARD_ROUTE_GOVERNANCE.map((routeGovernance) => [
        routeGovernance.routeKey,
        routeGovernance,
      ]),
    );

    for (const routeKey of routeKeys) {
      const routeGovernance = routeLookup.get(routeKey);
      expect(
        routeGovernance,
        `Fail-first baseline: missing ${routeKey} governance route.`,
      ).toBeDefined();
      if (!routeGovernance) {
        continue;
      }
      const firstViewportTemplate = resolveFirstViewportTemplate(routeGovernance);
      expect(
        firstViewportTemplate,
        `Fail-first baseline: ${routeKey} requires executive first-viewport template metadata.`,
      ).not.toBeNull();
      if (!firstViewportTemplate) {
        continue;
      }
      expect(firstViewportTemplate.dominantJobWidgetId.trim().length > 0).toBe(true);
      expect(firstViewportTemplate.heroInsightWidgetId.trim().length > 0).toBe(true);
      expect(firstViewportTemplate.sequence).toEqual([
        "overview",
        "drill-down",
        "evidence",
      ]);
      expect(
        firstViewportTemplate.supportingModuleBudgetMin <=
          firstViewportTemplate.supportingModuleBudgetMax,
      ).toBe(true);
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
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/analytics")).toBe("standard");
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/risk")).toBe("compact");
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/reports")).toBe("compact");
    expect(resolveWorkspaceShellDensityModeForPath("/portfolio/transactions")).toBe(
      "standard",
    );
  });

  it("2.3 carries route support-rail and shell density notes in governance artifacts", () => {
    const auditedRoutes = DASHBOARD_ROUTE_GOVERNANCE.filter((routeGovernance) =>
      AUDITED_ROUTE_KEYS.has(routeGovernance.routeKey),
    );

    for (const routeGovernance of auditedRoutes) {
      expect(
        routeGovernance.supportRailPlacement,
        `Fail-first baseline: ${routeGovernance.routeKey} must define support-rail placement.`,
      ).toBe("adjacent_route_header_compact_support_rail");
      expect(
        routeGovernance.shellDensityNotes?.trim().length,
        `Fail-first baseline: ${routeGovernance.routeKey} must define shell density implementation notes.`,
      ).toBeGreaterThan(0);
    }
  });

  it("3.1/3.2/3.3 requires promoted insight metadata, chart-fit rationale, and accessible fallback", () => {
    const auditedRoutes = DASHBOARD_ROUTE_GOVERNANCE.filter((routeGovernance) =>
      AUDITED_ROUTE_KEYS.has(routeGovernance.routeKey),
    );

    for (const routeGovernance of auditedRoutes) {
      const governanceGaps = findPromotedInsightGovernanceGaps(routeGovernance);
      expect(
        governanceGaps,
        `Fail-first baseline: ${routeGovernance.routeKey} promoted insight metadata gaps: ${governanceGaps.join(", ")}`,
      ).toEqual([]);

      const primaryWidgets = routeGovernance.widgets.filter(
        (widgetGovernance) => widgetGovernance.priority === "primary",
      );
      for (const widgetGovernance of primaryWidgets) {
        if (!widgetGovernance.promotedInsight) {
          continue;
        }
        const chartFitRule = resolveChartFitRule(
          widgetGovernance.promotedInsight.chartRelationship,
        );
        expect(chartFitRule.rationale.trim().length > 0).toBe(true);
        expect(chartFitRule.accessibleFallback.length > 0).toBe(true);
      }
    }
  });
});
