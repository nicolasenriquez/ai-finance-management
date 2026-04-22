export type DashboardRouteKey =
  | "home"
  | "analytics"
  | "risk"
  | "signals"
  | "asset-detail";

export type DashboardNarrativeSequenceStage = "overview" | "drill-down" | "evidence";

export type DashboardRouteFirstViewportTemplate = {
  dominantJobWidgetId: string;
  heroInsightWidgetId: string;
  supportingWidgetIds: string[];
  sequence: DashboardNarrativeSequenceStage[];
  supportingModuleBudgetMin: number;
  supportingModuleBudgetMax: number;
  firstViewportHeightBudgetPx: number;
  nonScrollFirstDecisionVisible: boolean;
};

export type DashboardRouteGovernance = {
  routeKey: DashboardRouteKey;
  path: string;
  progressiveDisclosureRequired: boolean;
  firstViewportTemplate: DashboardRouteFirstViewportTemplate;
};

export const DASHBOARD_ROUTE_GOVERNANCE: DashboardRouteGovernance[] = [
  {
    routeKey: "home",
    path: "/portfolio/home",
    progressiveDisclosureRequired: false,
    firstViewportTemplate: {
      dominantJobWidgetId: "home-primary-job",
      heroInsightWidgetId: "home-hero",
      supportingWidgetIds: ["home-kpis", "home-evidence"],
      sequence: ["overview", "drill-down", "evidence"],
      supportingModuleBudgetMin: 2,
      supportingModuleBudgetMax: 4,
      firstViewportHeightBudgetPx: 900,
      nonScrollFirstDecisionVisible: true,
    },
  },
  {
    routeKey: "analytics",
    path: "/portfolio/analytics",
    progressiveDisclosureRequired: true,
    firstViewportTemplate: {
      dominantJobWidgetId: "analytics-primary-job",
      heroInsightWidgetId: "analytics-hero",
      supportingWidgetIds: ["analytics-contribution", "analytics-evidence"],
      sequence: ["overview", "drill-down", "evidence"],
      supportingModuleBudgetMin: 2,
      supportingModuleBudgetMax: 4,
      firstViewportHeightBudgetPx: 900,
      nonScrollFirstDecisionVisible: true,
    },
  },
  {
    routeKey: "risk",
    path: "/portfolio/risk",
    progressiveDisclosureRequired: true,
    firstViewportTemplate: {
      dominantJobWidgetId: "risk-primary-job",
      heroInsightWidgetId: "risk-hero",
      supportingWidgetIds: ["risk-distribution", "risk-evidence"],
      sequence: ["overview", "drill-down", "evidence"],
      supportingModuleBudgetMin: 2,
      supportingModuleBudgetMax: 4,
      firstViewportHeightBudgetPx: 900,
      nonScrollFirstDecisionVisible: true,
    },
  },
  {
    routeKey: "signals",
    path: "/portfolio/signals",
    progressiveDisclosureRequired: true,
    firstViewportTemplate: {
      dominantJobWidgetId: "signals-primary-job",
      heroInsightWidgetId: "signals-hero",
      supportingWidgetIds: ["signals-ranking", "signals-evidence"],
      sequence: ["overview", "drill-down", "evidence"],
      supportingModuleBudgetMin: 2,
      supportingModuleBudgetMax: 4,
      firstViewportHeightBudgetPx: 900,
      nonScrollFirstDecisionVisible: true,
    },
  },
  {
    routeKey: "asset-detail",
    path: "/portfolio/asset-detail/:ticker",
    progressiveDisclosureRequired: true,
    firstViewportTemplate: {
      dominantJobWidgetId: "asset-detail-primary-job",
      heroInsightWidgetId: "asset-detail-hero",
      supportingWidgetIds: ["asset-detail-context", "asset-detail-evidence"],
      sequence: ["overview", "drill-down", "evidence"],
      supportingModuleBudgetMin: 2,
      supportingModuleBudgetMax: 4,
      firstViewportHeightBudgetPx: 900,
      nonScrollFirstDecisionVisible: true,
    },
  },
];

export function resolveFirstViewportTemplate(
  routeGovernance: DashboardRouteGovernance,
): DashboardRouteFirstViewportTemplate | null {
  return routeGovernance.firstViewportTemplate || null;
}
