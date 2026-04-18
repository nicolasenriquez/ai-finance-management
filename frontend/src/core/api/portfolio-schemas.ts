import { z } from "zod";

const numericLikeSchema = z.union([z.number(), z.string()]);
const nullableNumericLikeSchema = numericLikeSchema.nullable();

export const portfolioChartPeriodSchema = z.enum([
  "30D",
  "90D",
  "6M",
  "252D",
  "YTD",
  "MAX",
]);

export const portfolioQuantReportScopeSchema = z.enum([
  "portfolio",
  "instrument_symbol",
]);

export const portfolioHealthProfilePostureSchema = z.enum([
  "conservative",
  "balanced",
  "aggressive",
]);

export const portfolioDecisionStateSchema = z.enum([
  "ready",
  "unavailable",
  "stale",
]);

export const portfolioSummaryRowSchema = z.object({
  instrument_symbol: z.string(),
  open_quantity: numericLikeSchema,
  open_cost_basis_usd: numericLikeSchema,
  open_lot_count: z.number().int().nonnegative(),
  realized_proceeds_usd: numericLikeSchema,
  realized_cost_basis_usd: numericLikeSchema,
  realized_gain_usd: numericLikeSchema,
  dividend_gross_usd: numericLikeSchema,
  dividend_taxes_usd: numericLikeSchema,
  dividend_net_usd: numericLikeSchema,
  latest_close_price_usd: nullableNumericLikeSchema.optional(),
  market_value_usd: nullableNumericLikeSchema.optional(),
  unrealized_gain_usd: nullableNumericLikeSchema.optional(),
  unrealized_gain_pct: nullableNumericLikeSchema.optional(),
});

export const portfolioSummaryResponseSchema = z.object({
  as_of_ledger_at: z.string(),
  pricing_snapshot_key: z.string().nullable().optional(),
  pricing_snapshot_captured_at: z.string().nullable().optional(),
  rows: z.array(portfolioSummaryRowSchema),
});

export const portfolioCommandCenterInsightSchema = z.object({
  insight_id: z.string(),
  title: z.string(),
  message: z.string(),
  severity: z.enum(["info", "caution", "elevated_risk"]),
});

export const portfolioCommandCenterResponseSchema = z.object({
  state: portfolioDecisionStateSchema,
  state_reason_code: z.string(),
  state_reason_detail: z.string(),
  as_of_ledger_at: z.string(),
  as_of_market_at: z.string().nullable().optional(),
  evaluated_at: z.string(),
  freshness_policy: z.object({
    max_age_hours: z.number().int().positive(),
  }),
  net_worth_usd: numericLikeSchema,
  total_market_value_usd: numericLikeSchema,
  daily_pnl_usd: numericLikeSchema,
  concentration_top5_pct: numericLikeSchema,
  insights: z.array(portfolioCommandCenterInsightSchema),
});

export const portfolioHierarchyLotRowSchema = z.object({
  lot_id: z.number().int().positive(),
  opened_on: z.string(),
  original_qty: numericLikeSchema,
  remaining_qty: numericLikeSchema,
  unit_cost_basis_usd: numericLikeSchema,
  total_cost_basis_usd: numericLikeSchema,
  market_value_usd: numericLikeSchema,
  profit_loss_usd: numericLikeSchema,
});

export const portfolioHierarchyAssetRowSchema = z.object({
  instrument_symbol: z.string(),
  sector_label: z.string(),
  open_quantity: numericLikeSchema,
  open_cost_basis_usd: numericLikeSchema,
  avg_price_usd: numericLikeSchema,
  current_price_usd: numericLikeSchema,
  market_value_usd: numericLikeSchema,
  profit_loss_usd: numericLikeSchema,
  change_pct: nullableNumericLikeSchema.optional(),
  lot_count: z.number().int().nonnegative(),
  lots: z.array(portfolioHierarchyLotRowSchema),
});

export const portfolioHierarchyGroupRowSchema = z.object({
  group_key: z.string(),
  group_label: z.string(),
  asset_count: z.number().int().nonnegative(),
  total_market_value_usd: numericLikeSchema,
  total_profit_loss_usd: numericLikeSchema,
  total_change_pct: nullableNumericLikeSchema.optional(),
  assets: z.array(portfolioHierarchyAssetRowSchema),
});

export const portfolioHierarchyResponseSchema = z.object({
  as_of_ledger_at: z.string(),
  group_by: z.enum(["sector", "symbol"]),
  pricing_snapshot_key: z.string().nullable().optional(),
  pricing_snapshot_captured_at: z.string().nullable().optional(),
  groups: z.array(portfolioHierarchyGroupRowSchema),
});

export const portfolioContributionRowSchema = z.object({
  instrument_symbol: z.string(),
  contribution_pnl_usd: numericLikeSchema,
  contribution_pct: numericLikeSchema,
});

export const portfolioContributionResponseSchema = z.object({
  as_of_ledger_at: z.string(),
  period: portfolioChartPeriodSchema,
  rows: z.array(portfolioContributionRowSchema),
});

export const portfolioTimeSeriesPointSchema = z.object({
  captured_at: z.string(),
  portfolio_value_usd: numericLikeSchema,
  pnl_usd: numericLikeSchema,
  benchmark_sp500_value_usd: nullableNumericLikeSchema.optional(),
  benchmark_nasdaq100_value_usd: nullableNumericLikeSchema.optional(),
});

export const portfolioTimeSeriesResponseSchema = z.object({
  as_of_ledger_at: z.string(),
  period: portfolioChartPeriodSchema,
  frequency: z.string(),
  timezone: z.string(),
  points: z.array(portfolioTimeSeriesPointSchema),
});

export const lotDispositionDetailSchema = z.object({
  sell_transaction_id: z.number().int().positive(),
  disposition_date: z.string(),
  matched_qty: numericLikeSchema,
  matched_cost_basis_usd: numericLikeSchema,
  sell_gross_amount_usd: numericLikeSchema,
});

export const portfolioLotDetailRowSchema = z.object({
  lot_id: z.number().int().positive(),
  opened_on: z.string(),
  original_qty: numericLikeSchema,
  remaining_qty: numericLikeSchema,
  total_cost_basis_usd: numericLikeSchema,
  unit_cost_basis_usd: numericLikeSchema,
  dispositions: z.array(lotDispositionDetailSchema),
});

export const portfolioLotDetailResponseSchema = z.object({
  as_of_ledger_at: z.string(),
  instrument_symbol: z.string(),
  lots: z.array(portfolioLotDetailRowSchema),
});

export const portfolioHealthDriverSchema = z.object({
  metric_id: z.string(),
  label: z.string(),
  direction: z.enum(["supporting", "penalizing"]),
  impact_points: z.number().int().min(0).max(100),
  rationale: z.string(),
  value_display: z.string(),
});

export const portfolioHealthPillarMetricSchema = z.object({
  metric_id: z.string(),
  label: z.string(),
  value_display: z.string(),
  score: z.number().int().min(0).max(100),
  contribution: z.enum(["supporting", "neutral", "penalizing"]),
});

export const portfolioHealthPillarSchema = z.object({
  pillar_id: z.enum(["growth", "risk", "risk_adjusted_quality", "resilience"]),
  label: z.string(),
  score: z.number().int().min(0).max(100),
  status: z.enum(["favorable", "caution", "elevated_risk"]),
  metrics: z.array(portfolioHealthPillarMetricSchema),
});

export const portfolioHealthSynthesisResponseSchema = z.object({
  as_of_ledger_at: z.string(),
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().nullable().optional(),
  period: portfolioChartPeriodSchema,
  profile_posture: portfolioHealthProfilePostureSchema,
  health_score: z.number().int().min(0).max(100),
  health_label: z.enum(["healthy", "watchlist", "stressed"]),
  threshold_policy_version: z.string(),
  pillars: z.array(portfolioHealthPillarSchema),
  key_drivers: z.array(portfolioHealthDriverSchema),
  health_caveats: z.array(z.string()),
  core_metric_ids: z.array(z.string()),
  advanced_metric_ids: z.array(z.string()),
});

export type PortfolioChartPeriod = z.infer<typeof portfolioChartPeriodSchema>;
export type PortfolioQuantReportScope = z.infer<typeof portfolioQuantReportScopeSchema>;
export type PortfolioHealthProfilePosture = z.infer<
  typeof portfolioHealthProfilePostureSchema
>;
export type PortfolioDecisionState = z.infer<typeof portfolioDecisionStateSchema>;
export type PortfolioSummaryRow = z.infer<typeof portfolioSummaryRowSchema>;
export type PortfolioSummaryResponse = z.infer<typeof portfolioSummaryResponseSchema>;
export type PortfolioCommandCenterInsight = z.infer<
  typeof portfolioCommandCenterInsightSchema
>;
export type PortfolioCommandCenterResponse = z.infer<
  typeof portfolioCommandCenterResponseSchema
>;
export type PortfolioHierarchyLotRow = z.infer<typeof portfolioHierarchyLotRowSchema>;
export type PortfolioHierarchyAssetRow = z.infer<typeof portfolioHierarchyAssetRowSchema>;
export type PortfolioHierarchyGroupRow = z.infer<typeof portfolioHierarchyGroupRowSchema>;
export type PortfolioHierarchyResponse = z.infer<typeof portfolioHierarchyResponseSchema>;
export type PortfolioContributionRow = z.infer<typeof portfolioContributionRowSchema>;
export type PortfolioContributionResponse = z.infer<
  typeof portfolioContributionResponseSchema
>;
export type PortfolioTimeSeriesPoint = z.infer<typeof portfolioTimeSeriesPointSchema>;
export type PortfolioTimeSeriesResponse = z.infer<typeof portfolioTimeSeriesResponseSchema>;
export type PortfolioLotDetailRow = z.infer<typeof portfolioLotDetailRowSchema>;
export type PortfolioLotDetailResponse = z.infer<typeof portfolioLotDetailResponseSchema>;
export type PortfolioHealthDriver = z.infer<typeof portfolioHealthDriverSchema>;
export type PortfolioHealthPillarMetric = z.infer<
  typeof portfolioHealthPillarMetricSchema
>;
export type PortfolioHealthPillar = z.infer<typeof portfolioHealthPillarSchema>;
export type PortfolioHealthSynthesisResponse = z.infer<
  typeof portfolioHealthSynthesisResponseSchema
>;
