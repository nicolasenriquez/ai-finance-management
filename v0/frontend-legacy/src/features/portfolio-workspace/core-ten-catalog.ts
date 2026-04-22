export type CoreTenRouteOwner =
  | "home"
  | "analytics"
  | "risk"
  | "reports";

export type PersonalFinanceDecisionTag =
  | "allocation_review"
  | "income_monitoring"
  | "goal_progress"
  | "risk_posture"
  | "forecast_interpretation";

export type KpiInterpretationTier = "core_10" | "advanced";

export type CoreTenMetricCatalogEntry = {
  metricId: string;
  label: string;
  tier: KpiInterpretationTier;
  routeOwner: CoreTenRouteOwner;
  decisionTags: PersonalFinanceDecisionTag[];
  interpretation: string;
};

export const CORE_TEN_METRIC_CATALOG: readonly CoreTenMetricCatalogEntry[] = [
  {
    metricId: "market_value_usd",
    label: "Market value",
    tier: "core_10",
    routeOwner: "home",
    decisionTags: ["allocation_review"],
    interpretation: "Current portfolio scale and open-position exposure.",
  },
  {
    metricId: "unrealized_gain_pct",
    label: "Unrealized gain %",
    tier: "core_10",
    routeOwner: "home",
    decisionTags: ["allocation_review", "risk_posture"],
    interpretation: "Open-position posture versus cost basis.",
  },
  {
    metricId: "realized_gain_usd",
    label: "Realized gain",
    tier: "core_10",
    routeOwner: "home",
    decisionTags: ["goal_progress"],
    interpretation: "Locked gains/losses relevant for goal tracking.",
  },
  {
    metricId: "dividend_net_usd",
    label: "Dividend net",
    tier: "core_10",
    routeOwner: "home",
    decisionTags: ["income_monitoring"],
    interpretation: "Net dividend income contribution.",
  },
  {
    metricId: "top_contribution_concentration_pct",
    label: "Contribution concentration",
    tier: "core_10",
    routeOwner: "analytics",
    decisionTags: ["allocation_review", "risk_posture"],
    interpretation: "How concentrated period impact is in top movers.",
  },
  {
    metricId: "max_drawdown_pct",
    label: "Max drawdown",
    tier: "core_10",
    routeOwner: "risk",
    decisionTags: ["risk_posture"],
    interpretation: "Peak-to-trough stress magnitude for selected window.",
  },
  {
    metricId: "volatility_annualized_pct",
    label: "Annualized volatility",
    tier: "core_10",
    routeOwner: "risk",
    decisionTags: ["risk_posture"],
    interpretation: "Realized dispersion and risk-budget pressure.",
  },
  {
    metricId: "beta_ratio",
    label: "Beta ratio",
    tier: "core_10",
    routeOwner: "risk",
    decisionTags: ["risk_posture"],
    interpretation: "Market sensitivity versus benchmark context.",
  },
  {
    metricId: "goal_hit_probability_pct",
    label: "Goal hit probability",
    tier: "core_10",
    routeOwner: "reports",
    decisionTags: ["goal_progress"],
    interpretation: "Probability of reaching configured target threshold.",
  },
  {
    metricId: "forecast_confidence_pct",
    label: "Forecast confidence",
    tier: "core_10",
    routeOwner: "reports",
    decisionTags: ["forecast_interpretation"],
    interpretation: "Confidence quality for promoted forecast outputs.",
  },
  {
    metricId: "sharpe_ratio",
    label: "Sharpe ratio",
    tier: "advanced",
    routeOwner: "reports",
    decisionTags: ["risk_posture"],
    interpretation:
      "Risk-adjusted excess return efficiency relative to realized volatility.",
  },
  {
    metricId: "sortino_ratio",
    label: "Sortino ratio",
    tier: "advanced",
    routeOwner: "reports",
    decisionTags: ["risk_posture"],
    interpretation:
      "Downside-risk-adjusted return quality for asymmetric risk review.",
  },
  {
    metricId: "value_at_risk_95",
    label: "VaR 95%",
    tier: "advanced",
    routeOwner: "risk",
    decisionTags: ["risk_posture"],
    interpretation:
      "Estimated one-tail loss threshold under the selected confidence policy.",
  },
  {
    metricId: "expected_shortfall_95",
    label: "Expected shortfall 95%",
    tier: "advanced",
    routeOwner: "risk",
    decisionTags: ["risk_posture"],
    interpretation:
      "Average loss when outcomes breach the 95% VaR threshold.",
  },
] as const;

export function getCoreTenEntriesForRoute(
  routeOwner: CoreTenRouteOwner,
): CoreTenMetricCatalogEntry[] {
  return CORE_TEN_METRIC_CATALOG.filter(
    (entry) => entry.routeOwner === routeOwner && entry.tier === "core_10",
  );
}

export function getGovernedKpiEntriesForRoute(
  routeOwner: CoreTenRouteOwner,
): CoreTenMetricCatalogEntry[] {
  return CORE_TEN_METRIC_CATALOG.filter((entry) => entry.routeOwner === routeOwner);
}
