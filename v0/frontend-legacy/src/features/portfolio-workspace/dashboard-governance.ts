import type { PersonalFinanceDecisionTag } from "./core-ten-catalog";

export type WorkspaceMonitoringLens =
  | "Overview"
  | "Holdings"
  | "Performance"
  | "Risk"
  | "Rebalancing"
  | "Cash/Transactions"
  | "Copilot";

export type WorkspaceShellDensityMode = "expanded" | "standard" | "compact";

export type DashboardWidgetPriority = "primary" | "advanced";
export type DashboardPanelHierarchy = "hero" | "standard" | "utility";
export type DashboardNarrativeSequenceStage = "overview" | "drill-down" | "evidence";
export type DashboardEvidenceDepth =
  | "first_surface_only"
  | "secondary_chart"
  | "companion_table"
  | "advanced_disclosure";
export type DashboardChartRelationship =
  | "trend"
  | "ranking"
  | "distribution"
  | "contribution"
  | "performance_vs_target"
  | "state_summary"
  | "ledger";

export type PromotedInsightGovernance = {
  decisionIntent: string;
  benchmarkOrTarget: string;
  evidenceDepth: DashboardEvidenceDepth;
  chartRelationship: DashboardChartRelationship;
  chartFitRationale: string;
  prohibitedAlternatives: string[];
  accessibleFallback: string[];
};

export type DashboardRouteFirstViewportTemplate = {
  dominantJobWidgetId: string;
  heroInsightWidgetId: string;
  supportingWidgetIds: string[];
  sequence: DashboardNarrativeSequenceStage[];
  supportingModuleBudgetMin: number;
  supportingModuleBudgetMax: number;
};

export type DashboardWidgetGovernanceEntry = {
  widgetId: string;
  title: string;
  questionKey: string;
  questionText: string;
  decisionTags: PersonalFinanceDecisionTag[];
  sourceContracts: string[];
  comparisonFrame: string;
  priority: DashboardWidgetPriority;
  visualizationType: string;
  panelHierarchy?: DashboardPanelHierarchy;
  promotedInsight?: PromotedInsightGovernance | null;
};

export type DashboardRouteGovernance = {
  routeKey:
    | "dashboard"
    | "holdings"
    | "performance"
    | "rebalancing"
    | "home"
    | "analytics"
    | "risk"
    | "reports"
    | "transactions"
    | "copilot";
  path: string;
  routeLabel: string;
  lens: WorkspaceMonitoringLens;
  dominantPrimaryJobQuestion: string;
  primaryModuleBudgetMax: number;
  shellDensityMode: WorkspaceShellDensityMode;
  progressiveDisclosureRequired: boolean;
  shellDensityNotes?: string;
  supportRailPlacement?: "adjacent_route_header_compact_support_rail";
  firstViewportTemplate?: DashboardRouteFirstViewportTemplate;
  widgets: DashboardWidgetGovernanceEntry[];
};

export type ChartFitRule = {
  rationale: string;
  prohibitedAlternatives: string[];
  accessibleFallback: string[];
  defaultEvidenceDepth: DashboardEvidenceDepth;
};

const CHART_FIT_RULES: Record<DashboardChartRelationship, ChartFitRule> = {
  trend: {
    rationale:
      "Line-based trend charts preserve sequence and slope interpretation for time-ordered movement.",
    prohibitedAlternatives: ["pie_chart", "radar_chart"],
    accessibleFallback: [
      "Direct point labels for latest and baseline values.",
      "Companion summary sentence with benchmark delta.",
    ],
    defaultEvidenceDepth: "secondary_chart",
  },
  ranking: {
    rationale:
      "Ranked bar/table structures preserve ordering and magnitude comparison across categories.",
    prohibitedAlternatives: ["stacked_area_chart", "decorative_donut"],
    accessibleFallback: [
      "Companion ranked table with exact magnitudes.",
      "Top/bottom leader summary copy.",
    ],
    defaultEvidenceDepth: "companion_table",
  },
  distribution: {
    rationale:
      "Histogram-style distribution reveals spread, skew, and tail mass required for risk interpretation.",
    prohibitedAlternatives: ["pie_chart", "stacked_line_chart"],
    accessibleFallback: [
      "Bucket table with lower/upper bounds and frequencies.",
      "Tail-mass summary text.",
    ],
    defaultEvidenceDepth: "companion_table",
  },
  contribution: {
    rationale:
      "Contribution views require signed magnitude comparison and concentration context by symbol.",
    prohibitedAlternatives: ["single_metric_gauge", "radial_progress"],
    accessibleFallback: [
      "Signed contribution ledger with net-share and absolute-share columns.",
      "Leader/drag summary sentence.",
    ],
    defaultEvidenceDepth: "companion_table",
  },
  performance_vs_target: {
    rationale:
      "Performance-versus-target visuals must keep benchmark/target references visible in title, legend, or subtitle.",
    prohibitedAlternatives: ["isolated_single_value_card_without_reference"],
    accessibleFallback: [
      "Visible benchmark/target value labels adjacent to reading.",
      "Target-gap summary copy.",
    ],
    defaultEvidenceDepth: "secondary_chart",
  },
  state_summary: {
    rationale:
      "State summaries prioritize decision framing and route orientation before deeper diagnostics.",
    prohibitedAlternatives: ["multi_axis_composite_without_focus"],
    accessibleFallback: [
      "Deterministic state sentence in plain language.",
      "Companion status table when multiple states are shown.",
    ],
    defaultEvidenceDepth: "first_surface_only",
  },
  ledger: {
    rationale:
      "Ledger layouts preserve deterministic event ordering and row-level evidence traceability.",
    prohibitedAlternatives: ["abstract_heatmap_without_rows"],
    accessibleFallback: [
      "Sortable table with direct labels for each row and value.",
      "Filter state summary above the table.",
    ],
    defaultEvidenceDepth: "companion_table",
  },
};

const FIRST_VIEWPORT_TEMPLATE_BY_ROUTE_KEY: Partial<
  Record<DashboardRouteGovernance["routeKey"], DashboardRouteFirstViewportTemplate>
> = {
  home: {
    dominantJobWidgetId: "home-primary-job",
    heroInsightWidgetId: "home-trend-preview",
    supportingWidgetIds: ["home-kpi-strip", "home-health-synthesis", "home-hierarchy"],
    sequence: ["overview", "drill-down", "evidence"],
    supportingModuleBudgetMin: 2,
    supportingModuleBudgetMax: 4,
  },
  dashboard: {
    dominantJobWidgetId: "home-primary-job",
    heroInsightWidgetId: "home-trend-preview",
    supportingWidgetIds: ["home-kpi-strip", "home-health-synthesis", "home-hierarchy"],
    sequence: ["overview", "drill-down", "evidence"],
    supportingModuleBudgetMin: 2,
    supportingModuleBudgetMax: 4,
  },
  holdings: {
    dominantJobWidgetId: "holdings-ledger-snapshot",
    heroInsightWidgetId: "holdings-ledger-pulse",
    supportingWidgetIds: ["holdings-ledger-snapshot"],
    sequence: ["overview", "drill-down", "evidence"],
    supportingModuleBudgetMin: 1,
    supportingModuleBudgetMax: 2,
  },
  analytics: {
    dominantJobWidgetId: "analytics-primary-job",
    heroInsightWidgetId: "analytics-trend",
    supportingWidgetIds: ["analytics-contribution-leaders"],
    sequence: ["overview", "drill-down", "evidence"],
    supportingModuleBudgetMin: 1,
    supportingModuleBudgetMax: 3,
  },
  performance: {
    dominantJobWidgetId: "analytics-primary-job",
    heroInsightWidgetId: "analytics-trend",
    supportingWidgetIds: ["analytics-contribution-leaders"],
    sequence: ["overview", "drill-down", "evidence"],
    supportingModuleBudgetMin: 1,
    supportingModuleBudgetMax: 3,
  },
  transactions: {
    dominantJobWidgetId: "transactions-operating-job",
    heroInsightWidgetId: "transactions-ledger-pulse",
    supportingWidgetIds: ["transactions-ledger-table"],
    sequence: ["overview", "drill-down", "evidence"],
    supportingModuleBudgetMin: 1,
    supportingModuleBudgetMax: 2,
  },
};

const SHELL_DENSITY_NOTES: Record<WorkspaceShellDensityMode, string> = {
  expanded:
    "Expanded mode keeps command surfaces visible for orientation-first routes with lower analytical density.",
  standard:
    "Standard mode preserves persistent navigation and trust context with moderate utility footprint.",
  compact:
    "Compact mode suppresses non-critical chrome so dense analytical panels dominate first viewport attention.",
};

function resolvePanelHierarchy(
  widgetGovernance: DashboardWidgetGovernanceEntry,
): DashboardPanelHierarchy {
  if (widgetGovernance.widgetId.includes("primary-job")) {
    return "hero";
  }
  if (widgetGovernance.priority === "advanced") {
    return "utility";
  }
  return "standard";
}

function resolveChartRelationship(
  widgetGovernance: DashboardWidgetGovernanceEntry,
): DashboardChartRelationship {
  const visualization = widgetGovernance.visualizationType.toLowerCase();
  const widgetId = widgetGovernance.widgetId.toLowerCase();
  if (widgetId.includes("ledger") || visualization.includes("table")) {
    return "ledger";
  }
  if (
    visualization.includes("trend") ||
    visualization.includes("line chart") ||
    visualization.includes("timeline")
  ) {
    return "trend";
  }
  if (
    visualization.includes("distribution") ||
    visualization.includes("histogram")
  ) {
    return "distribution";
  }
  if (
    visualization.includes("contribution") ||
    widgetId.includes("contribution")
  ) {
    return "contribution";
  }
  if (
    visualization.includes("bar chart") ||
    visualization.includes("ranking") ||
    widgetId.includes("leader")
  ) {
    return "ranking";
  }
  if (
    widgetGovernance.comparisonFrame.toLowerCase().includes("benchmark") ||
    widgetGovernance.comparisonFrame.toLowerCase().includes("target")
  ) {
    return "performance_vs_target";
  }
  return "state_summary";
}

function resolvePromotedInsightGovernance(
  widgetGovernance: DashboardWidgetGovernanceEntry,
): PromotedInsightGovernance | null {
  if (widgetGovernance.priority !== "primary") {
    return null;
  }
  const chartRelationship = resolveChartRelationship(widgetGovernance);
  const chartFitRule = CHART_FIT_RULES[chartRelationship];
  return {
    decisionIntent: widgetGovernance.questionText,
    benchmarkOrTarget: widgetGovernance.comparisonFrame,
    evidenceDepth: chartFitRule.defaultEvidenceDepth,
    chartRelationship,
    chartFitRationale: chartFitRule.rationale,
    prohibitedAlternatives: chartFitRule.prohibitedAlternatives,
    accessibleFallback: chartFitRule.accessibleFallback,
  };
}

function enrichRouteGovernance(
  routeGovernance: DashboardRouteGovernance,
): DashboardRouteGovernance {
  const firstViewportTemplate =
    routeGovernance.firstViewportTemplate ||
    FIRST_VIEWPORT_TEMPLATE_BY_ROUTE_KEY[routeGovernance.routeKey];
  return {
    ...routeGovernance,
    shellDensityNotes:
      routeGovernance.shellDensityNotes || SHELL_DENSITY_NOTES[routeGovernance.shellDensityMode],
    supportRailPlacement:
      routeGovernance.supportRailPlacement || "adjacent_route_header_compact_support_rail",
    firstViewportTemplate:
      firstViewportTemplate || routeGovernance.firstViewportTemplate,
    widgets: routeGovernance.widgets.map((widgetGovernance) => ({
      ...widgetGovernance,
      panelHierarchy: widgetGovernance.panelHierarchy || resolvePanelHierarchy(widgetGovernance),
      promotedInsight:
        widgetGovernance.promotedInsight ?? resolvePromotedInsightGovernance(widgetGovernance),
    })),
  };
}

export function resolveChartFitRule(
  chartRelationship: DashboardChartRelationship,
): ChartFitRule {
  return CHART_FIT_RULES[chartRelationship];
}

const LEGACY_DASHBOARD_ROUTE_GOVERNANCE: DashboardRouteGovernance[] = [
  {
    routeKey: "home",
    path: "/portfolio/home",
    routeLabel: "Home",
    lens: "Overview",
    dominantPrimaryJobQuestion: "How is the portfolio operating overall right now?",
    primaryModuleBudgetMax: 7,
    shellDensityMode: "expanded",
    progressiveDisclosureRequired: false,
    widgets: [
      {
        widgetId: "home-primary-job",
        title: "Portfolio operating posture",
        questionKey: "portfolio-operating-posture",
        questionText: "How healthy is the portfolio posture in this period?",
        decisionTags: ["allocation_review", "income_monitoring", "goal_progress"],
        sourceContracts: ["/api/portfolio/summary", "/api/portfolio/time-series"],
        comparisonFrame: "Current period versus prior observations",
        priority: "primary",
        visualizationType: "Primary job panel",
      },
      {
        widgetId: "home-kpi-strip",
        title: "Portfolio KPIs",
        questionKey: "portfolio-kpis",
        questionText: "What are the core value, gain, and income indicators?",
        decisionTags: ["allocation_review", "goal_progress", "income_monitoring"],
        sourceContracts: ["/api/portfolio/summary", "/api/portfolio/time-series"],
        comparisonFrame: "Current value and period movement",
        priority: "primary",
        visualizationType: "KPI cards",
      },
      {
        widgetId: "home-trend-preview",
        title: "Trend preview",
        questionKey: "trend-versus-benchmark",
        questionText: "Is trend direction aligned with benchmark context?",
        decisionTags: ["allocation_review", "risk_posture"],
        sourceContracts: ["/api/portfolio/time-series"],
        comparisonFrame: "Portfolio versus benchmark overlays",
        priority: "primary",
        visualizationType: "Line chart",
      },
      {
        widgetId: "home-health-synthesis",
        title: "Portfolio health synthesis",
        questionKey: "health-driver-explanation",
        questionText: "Which health pillars explain current posture?",
        decisionTags: ["goal_progress", "risk_posture"],
        sourceContracts: ["/api/portfolio/health-synthesis"],
        comparisonFrame: "Profile posture and pillar score bands",
        priority: "primary",
        visualizationType: "Scorecards + semantic table",
      },
      {
        widgetId: "home-hierarchy",
        title: "Hierarchy allocation snapshot",
        questionKey: "allocation-concentration-structure",
        questionText: "Where is allocation concentrated by hierarchy?",
        decisionTags: ["allocation_review", "risk_posture"],
        sourceContracts: ["/api/portfolio/hierarchy"],
        comparisonFrame: "Group-level market value and P&L spread",
        priority: "primary",
        visualizationType: "Hierarchy table",
      },
      {
        widgetId: "home-drilldown-routes",
        title: "Drill-down routes",
        questionKey: "next-best-route",
        questionText: "Which route answers the next analytical question?",
        decisionTags: ["allocation_review", "risk_posture"],
        sourceContracts: ["workspace route map"],
        comparisonFrame: "Route intent cards",
        priority: "primary",
        visualizationType: "Route decision cards",
      },
      {
        widgetId: "home-period-waterfall",
        title: "Period change waterfall",
        questionKey: "period-change-bridge",
        questionText: "What bridge explains period movement from start to current value?",
        decisionTags: ["allocation_review"],
        sourceContracts: ["/api/portfolio/time-series", "/api/portfolio/summary"],
        comparisonFrame: "Component bridge across period points",
        priority: "advanced",
        visualizationType: "Waterfall",
      },
    ],
  },
  {
    routeKey: "analytics",
    path: "/portfolio/analytics",
    routeLabel: "Analytics",
    lens: "Performance",
    dominantPrimaryJobQuestion: "Which contribution drivers explain this period outcome?",
    primaryModuleBudgetMax: 7,
    shellDensityMode: "standard",
    progressiveDisclosureRequired: true,
    widgets: [
      {
        widgetId: "analytics-primary-job",
        title: "Attribution concentration interpretation",
        questionKey: "attribution-priority-framing",
        questionText: "Which attribution question should be interpreted first?",
        decisionTags: ["allocation_review", "risk_posture"],
        sourceContracts: ["/api/portfolio/contribution"],
        comparisonFrame: "Absolute share versus net share",
        priority: "primary",
        visualizationType: "Primary job panel",
      },
      {
        widgetId: "analytics-trend",
        title: "Portfolio trend dataset",
        questionKey: "trend-versus-benchmark",
        questionText: "How has the portfolio trended against benchmark context?",
        decisionTags: ["allocation_review", "risk_posture"],
        sourceContracts: ["/api/portfolio/time-series"],
        comparisonFrame: "Portfolio versus benchmark overlays",
        priority: "primary",
        visualizationType: "Line chart",
      },
      {
        widgetId: "analytics-contribution-leaders",
        title: "Contribution leaders",
        questionKey: "attribution-concentration-interpretation",
        questionText: "Which symbols are the top positive and negative contributors?",
        decisionTags: ["allocation_review", "risk_posture"],
        sourceContracts: ["/api/portfolio/contribution"],
        comparisonFrame: "Contribution bars + share ledger",
        priority: "primary",
        visualizationType: "Bar chart + table",
      },
      {
        widgetId: "analytics-contribution-waterfall",
        title: "Contribution waterfall",
        questionKey: "attribution-concentration-interpretation",
        questionText: "How do contribution steps bridge to period impact?",
        decisionTags: ["allocation_review"],
        sourceContracts: ["/api/portfolio/contribution"],
        comparisonFrame: "Sequential contribution bridge",
        priority: "advanced",
        visualizationType: "Waterfall",
      },
    ],
  },
  {
    routeKey: "risk",
    path: "/portfolio/risk",
    routeLabel: "Risk",
    lens: "Risk",
    dominantPrimaryJobQuestion: "How severe is current downside risk posture?",
    primaryModuleBudgetMax: 7,
    shellDensityMode: "compact",
    progressiveDisclosureRequired: true,
    widgets: [
      {
        widgetId: "risk-primary-job",
        title: "Risk posture interpretation",
        questionKey: "risk-posture-summary",
        questionText: "What is the current risk posture for the selected scope?",
        decisionTags: ["risk_posture"],
        sourceContracts: ["/api/portfolio/risk-estimators"],
        comparisonFrame: "Estimator values versus interpretation bands",
        priority: "primary",
        visualizationType: "Primary job panel",
      },
      {
        widgetId: "risk-estimator-ledger",
        title: "Estimator metrics",
        questionKey: "risk-estimator-ledger",
        questionText: "What do estimator values and methods show right now?",
        decisionTags: ["risk_posture"],
        sourceContracts: ["/api/portfolio/risk-estimators"],
        comparisonFrame: "Mixed-unit guardrails and methodology metadata",
        priority: "primary",
        visualizationType: "Bar chart + metadata table",
      },
      {
        widgetId: "risk-health-bridge",
        title: "Health context bridge",
        questionKey: "risk-to-health-link",
        questionText: "How do risk conditions affect health posture?",
        decisionTags: ["risk_posture", "goal_progress"],
        sourceContracts: ["/api/portfolio/health-synthesis"],
        comparisonFrame: "Risk pillar versus full health score",
        priority: "primary",
        visualizationType: "Context cards",
      },
      {
        widgetId: "risk-drawdown",
        title: "Drawdown path timeline",
        questionKey: "drawdown-depth-persistence",
        questionText: "How deep and persistent has drawdown been?",
        decisionTags: ["risk_posture"],
        sourceContracts: ["/api/portfolio/risk-evolution"],
        comparisonFrame: "Current drawdown path across period",
        priority: "primary",
        visualizationType: "Drawdown line chart",
      },
      {
        widgetId: "risk-return-distribution",
        title: "Return distribution",
        questionKey: "return-distribution-shape",
        questionText: "How are returns distributed and where are tail concentrations?",
        decisionTags: ["risk_posture"],
        sourceContracts: ["/api/portfolio/return-distribution"],
        comparisonFrame: "Bucket policy and sample-size context",
        priority: "primary",
        visualizationType: "Histogram",
      },
      {
        widgetId: "risk-rolling-estimator",
        title: "Rolling estimator timeline",
        questionKey: "rolling-risk-regime-shifts",
        questionText: "Are rolling volatility and beta shifting regimes?",
        decisionTags: ["risk_posture"],
        sourceContracts: ["/api/portfolio/risk-evolution"],
        comparisonFrame: "Rolling estimator trend over same period",
        priority: "advanced",
        visualizationType: "Multi-series line chart",
      },
      {
        widgetId: "risk-correlation-network",
        title: "Correlation cluster network",
        questionKey: "co-movement-concentration",
        questionText: "Where does hidden concentration appear through co-movement?",
        decisionTags: ["risk_posture", "allocation_review"],
        sourceContracts: ["/api/portfolio/summary", "/api/portfolio/time-series"],
        comparisonFrame: "Pairwise return correlations",
        priority: "advanced",
        visualizationType: "Correlation matrix",
      },
      {
        widgetId: "risk-tail-diagnostics",
        title: "Tail risk diagnostics",
        questionKey: "tail-loss-severity",
        questionText: "How severe are left-tail scenarios relative to baseline tails?",
        decisionTags: ["risk_posture"],
        sourceContracts: ["/api/portfolio/risk-estimators", "/api/portfolio/return-distribution"],
        comparisonFrame: "VaR versus expected shortfall and tail mass",
        priority: "advanced",
        visualizationType: "Tail diagnostic cards + ledger",
      },
    ],
  },
  {
    routeKey: "reports",
    path: "/portfolio/reports",
    routeLabel: "Quant/Reports",
    lens: "Performance",
    dominantPrimaryJobQuestion: "Are performance outcomes robust enough for report export decisions?",
    primaryModuleBudgetMax: 7,
    shellDensityMode: "compact",
    progressiveDisclosureRequired: true,
    widgets: [
      {
        widgetId: "reports-primary-job",
        title: "Goal progress and confidence interpretation",
        questionKey: "goal-progress-confidence",
        questionText: "Do confidence and goal metrics support reporting decisions?",
        decisionTags: ["goal_progress", "forecast_interpretation"],
        sourceContracts: ["/api/portfolio/quant-metrics", "/api/portfolio/monte-carlo"],
        comparisonFrame: "Goal probability versus confidence context",
        priority: "primary",
        visualizationType: "Primary job panel",
      },
      {
        widgetId: "reports-quant-scorecards",
        title: "Quant scorecards",
        questionKey: "quant-scorecard-overview",
        questionText: "What do core quant diagnostics show for this period?",
        decisionTags: ["goal_progress", "forecast_interpretation"],
        sourceContracts: ["/api/portfolio/quant-metrics"],
        comparisonFrame: "Metric-level benchmark context and omissions",
        priority: "primary",
        visualizationType: "Metric cards + table",
      },
      {
        widgetId: "reports-lifecycle",
        title: "Quant report lifecycle",
        questionKey: "report-lifecycle-readiness",
        questionText: "Is the report artifact lifecycle ready and valid?",
        decisionTags: ["goal_progress"],
        sourceContracts: ["/api/portfolio/quant-reports", "/api/portfolio/quant-reports/{report_id}"],
        comparisonFrame: "Lifecycle states loading/error/unavailable/ready",
        priority: "primary",
        visualizationType: "Lifecycle panel",
      },
      {
        widgetId: "reports-monte-carlo",
        title: "Monte Carlo diagnostics",
        questionKey: "scenario-probability-bounds",
        questionText: "What are bounded scenario probabilities for bust and goal outcomes?",
        decisionTags: ["goal_progress", "risk_posture"],
        sourceContracts: ["/api/portfolio/monte-carlo"],
        comparisonFrame: "Bust versus goal thresholds and profile scenarios",
        priority: "primary",
        visualizationType: "Scenario cards + control form",
      },
      {
        widgetId: "reports-monthly-heatmap",
        title: "Monthly return heatmap",
        questionKey: "monthly-return-rhythm",
        questionText: "What monthly return rhythm appears in selected scope?",
        decisionTags: ["allocation_review"],
        sourceContracts: ["/api/portfolio/time-series"],
        comparisonFrame: "Month-over-month return color map",
        priority: "primary",
        visualizationType: "Heatmap",
      },
      {
        widgetId: "reports-symbol-focus",
        title: "Symbol contribution focus",
        questionKey: "symbol-contribution-priority",
        questionText: "Which symbols should be prioritized for deeper report scope?",
        decisionTags: ["allocation_review", "risk_posture"],
        sourceContracts: ["/api/portfolio/contribution"],
        comparisonFrame: "Top mover concentration",
        priority: "primary",
        visualizationType: "Contribution bars + table",
      },
      {
        widgetId: "reports-advanced-risk-lab",
        title: "Advanced risk lab",
        questionKey: "frontier-vs-contribution-tradeoff",
        questionText: "How do frontier allocations compare with contribution concentration?",
        decisionTags: ["risk_posture", "allocation_review"],
        sourceContracts: ["/api/portfolio/efficient-frontier", "/api/portfolio/contribution"],
        comparisonFrame: "Frontier profile spread and risk contribution budget",
        priority: "advanced",
        visualizationType: "Frontier plot + table",
      },
      {
        widgetId: "reports-ml-insights",
        title: "ML insights control tower",
        questionKey: "ml-readiness-governance",
        questionText: "Are ML signals, forecasts, and model governance states ready?",
        decisionTags: ["forecast_interpretation", "risk_posture"],
        sourceContracts: ["/api/portfolio/ml/signals", "/api/portfolio/ml/forecasts", "/api/portfolio/ml/registry"],
        comparisonFrame: "State readiness and model lineage",
        priority: "advanced",
        visualizationType: "Signal strip + forecast fan + registry table",
      },
      {
        widgetId: "reports-health-bridge",
        title: "Health scenario bridge",
        questionKey: "health-vs-scenario-alignment",
        questionText: "Does health posture align with scenario diagnostics?",
        decisionTags: ["goal_progress", "risk_posture"],
        sourceContracts: ["/api/portfolio/health-synthesis", "/api/portfolio/monte-carlo"],
        comparisonFrame: "Health score versus scenario signal",
        priority: "advanced",
        visualizationType: "Scenario bridge cards",
      },
    ],
  },
  {
    routeKey: "transactions",
    path: "/portfolio/transactions",
    routeLabel: "Transactions",
    lens: "Cash/Transactions",
    dominantPrimaryJobQuestion: "What cash and ledger events changed recently?",
    primaryModuleBudgetMax: 5,
    shellDensityMode: "standard",
    progressiveDisclosureRequired: false,
    widgets: [
      {
        widgetId: "transactions-operating-job",
        title: "Operating-console cashflow triage",
        questionKey: "cash-event-operating-console",
        questionText: "Which cashflow operating questions require immediate triage?",
        decisionTags: ["income_monitoring", "allocation_review"],
        sourceContracts: ["/api/portfolio/transactions"],
        comparisonFrame: "Current event mix versus expected operating flow",
        priority: "primary",
        visualizationType: "Primary job panel",
      },
      {
        widgetId: "transactions-ledger-pulse",
        title: "Cashflow operating pulse",
        questionKey: "transactions-ledger-operating-pulse",
        questionText: "How did event mix and cash magnitude shift in the latest ledger window?",
        decisionTags: ["income_monitoring", "allocation_review"],
        sourceContracts: ["/api/portfolio/transactions"],
        comparisonFrame: "Latest event counts and cash movement versus current filter scope",
        priority: "primary",
        visualizationType: "Summary cards",
      },
      {
        widgetId: "transactions-ledger-table",
        title: "Transactions table",
        questionKey: "cash-event-history",
        questionText: "What deterministic cash and quantity events were posted?",
        decisionTags: ["income_monitoring"],
        sourceContracts: ["/api/portfolio/transactions"],
        comparisonFrame: "Newest-first deterministic ordering with filters",
        priority: "primary",
        visualizationType: "Table",
      },
    ],
  },
  {
    routeKey: "copilot",
    path: "/portfolio/copilot",
    routeLabel: "Copilot",
    lens: "Copilot",
    dominantPrimaryJobQuestion: "What bounded answer can the copilot provide with evidence?",
    primaryModuleBudgetMax: 6,
    shellDensityMode: "compact",
    progressiveDisclosureRequired: false,
    widgets: [],
  },
];

function deriveDecisionLensRoute(
  routeGovernance: DashboardRouteGovernance,
): DashboardRouteGovernance | null {
  if (routeGovernance.routeKey === "home") {
    return {
      ...routeGovernance,
      routeKey: "dashboard",
      path: "/portfolio/dashboard",
      routeLabel: "Dashboard",
      primaryModuleBudgetMax: 6,
    };
  }
  if (routeGovernance.routeKey === "analytics") {
    return {
      ...routeGovernance,
      routeKey: "performance",
      path: "/portfolio/performance",
      routeLabel: "Performance",
    };
  }
  if (routeGovernance.routeKey === "reports") {
    return {
      ...routeGovernance,
      routeKey: "rebalancing",
      path: "/portfolio/rebalancing",
      routeLabel: "Rebalancing",
      lens: "Rebalancing",
      primaryModuleBudgetMax: 6,
    };
  }
  return null;
}

const DECISION_LENS_ROUTE_GOVERNANCE = LEGACY_DASHBOARD_ROUTE_GOVERNANCE.flatMap(
  (routeGovernance) => {
    const decisionLensRoute = deriveDecisionLensRoute(routeGovernance);
    return decisionLensRoute ? [decisionLensRoute] : [];
  },
);

const HOLDINGS_ROUTE_GOVERNANCE: DashboardRouteGovernance = {
  routeKey: "holdings",
  path: "/portfolio/holdings",
  routeLabel: "Holdings",
  lens: "Holdings",
  dominantPrimaryJobQuestion: "Which holdings and lot structures require attention now?",
  primaryModuleBudgetMax: 5,
  shellDensityMode: "standard",
  progressiveDisclosureRequired: false,
  widgets: [
    {
      widgetId: "holdings-ledger-snapshot",
      title: "Holdings ledger snapshot",
      questionKey: "holdings-allocation-ledger",
      questionText: "Which holdings and lots explain current portfolio structure?",
      decisionTags: ["allocation_review", "risk_posture"],
      sourceContracts: ["/api/portfolio/summary", "/api/portfolio/lots/{instrument_symbol}"],
      comparisonFrame: "Holdings-level value, gain/loss, and lot detail links",
      priority: "primary",
      visualizationType: "Holdings table",
    },
    {
      widgetId: "holdings-ledger-pulse",
      title: "Holdings ledger pulse",
      questionKey: "holdings-ledger-operating-pulse",
      questionText: "What first-view holdings pulse frames the next ledger drill-down?",
      decisionTags: ["allocation_review", "risk_posture"],
      sourceContracts: ["/api/portfolio/summary"],
      comparisonFrame: "Active positions, market value, and unrealized posture in current scope",
      priority: "primary",
      visualizationType: "Summary cards",
    },
  ],
};

export const DASHBOARD_ROUTE_GOVERNANCE: DashboardRouteGovernance[] = [
  ...LEGACY_DASHBOARD_ROUTE_GOVERNANCE,
  ...DECISION_LENS_ROUTE_GOVERNANCE,
  HOLDINGS_ROUTE_GOVERNANCE,
].map((routeGovernance) => enrichRouteGovernance(routeGovernance));

const DASHBOARD_ROUTE_GOVERNANCE_BY_PATH = new Map(
  DASHBOARD_ROUTE_GOVERNANCE.map((routeGovernance) => [
    routeGovernance.path,
    routeGovernance,
  ]),
);

export function resolveDashboardRouteGovernance(
  pathname: string,
): DashboardRouteGovernance | null {
  if (DASHBOARD_ROUTE_GOVERNANCE_BY_PATH.has(pathname)) {
    return DASHBOARD_ROUTE_GOVERNANCE_BY_PATH.get(pathname) || null;
  }
  if (pathname.startsWith("/portfolio/") && pathname !== "/portfolio/copilot") {
    const symbolCandidate = pathname.slice("/portfolio/".length);
    if (symbolCandidate.length > 0 && !symbolCandidate.includes("/")) {
      return {
        routeKey: "transactions",
        path: pathname,
        routeLabel: "Lot detail",
        lens: "Holdings",
        dominantPrimaryJobQuestion: "How do lots explain this holding?",
        primaryModuleBudgetMax: 6,
        shellDensityMode: "standard",
        progressiveDisclosureRequired: false,
        widgets: [],
      };
    }
  }
  return null;
}

export function resolveWorkspaceShellDensityModeForPath(
  pathname: string,
): WorkspaceShellDensityMode {
  const routeGovernance = resolveDashboardRouteGovernance(pathname);
  if (!routeGovernance) {
    return "standard";
  }
  return routeGovernance.shellDensityMode;
}

export function resolveWorkspaceLensLabel(pathname: string): WorkspaceMonitoringLens | null {
  const routeGovernance = resolveDashboardRouteGovernance(pathname);
  return routeGovernance ? routeGovernance.lens : null;
}

export function countPrimaryWidgets(
  routeGovernance: DashboardRouteGovernance,
): number {
  return routeGovernance.widgets.filter((widget) => widget.priority === "primary").length;
}

export function findDuplicatePrimaryQuestionKeys(
  routeGovernance: DashboardRouteGovernance,
): string[] {
  const seenQuestionKeys = new Set<string>();
  const duplicateQuestionKeys = new Set<string>();

  routeGovernance.widgets
    .filter((widget) => widget.priority === "primary")
    .forEach((widget) => {
      if (seenQuestionKeys.has(widget.questionKey)) {
        duplicateQuestionKeys.add(widget.questionKey);
      }
      seenQuestionKeys.add(widget.questionKey);
    });

  return Array.from(duplicateQuestionKeys);
}

export function resolveFirstViewportTemplate(
  routeGovernance: DashboardRouteGovernance,
): DashboardRouteFirstViewportTemplate | null {
  if (routeGovernance.firstViewportTemplate) {
    return routeGovernance.firstViewportTemplate;
  }
  return FIRST_VIEWPORT_TEMPLATE_BY_ROUTE_KEY[routeGovernance.routeKey] || null;
}

export function findPromotedInsightGovernanceGaps(
  routeGovernance: DashboardRouteGovernance,
): string[] {
  return routeGovernance.widgets
    .filter((widgetGovernance) => widgetGovernance.priority === "primary")
    .flatMap((widgetGovernance) => {
      const governance = widgetGovernance.promotedInsight;
      if (!governance) {
        return [`${widgetGovernance.widgetId}:missing_promoted_metadata`];
      }
      const gaps: string[] = [];
      if (governance.decisionIntent.trim().length === 0) {
        gaps.push(`${widgetGovernance.widgetId}:missing_decision_intent`);
      }
      if (governance.benchmarkOrTarget.trim().length === 0) {
        gaps.push(`${widgetGovernance.widgetId}:missing_benchmark_or_target`);
      }
      if (governance.chartFitRationale.trim().length === 0) {
        gaps.push(`${widgetGovernance.widgetId}:missing_chart_fit_rationale`);
      }
      if (governance.accessibleFallback.length === 0) {
        gaps.push(`${widgetGovernance.widgetId}:missing_accessible_fallback`);
      }
      return gaps;
    });
}
