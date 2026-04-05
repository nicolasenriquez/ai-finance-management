import { z } from "zod";

const decimalFieldSchema = z.string().min(1);
const nullableDecimalFieldSchema = z.union([decimalFieldSchema, z.null()]);
export const portfolioChartPeriodSchema = z.enum([
  "30D",
  "90D",
  "6M",
  "252D",
  "YTD",
  "MAX",
]);
export const portfolioTimeSeriesScopeSchema = z.enum([
  "portfolio",
  "instrument_symbol",
]);
export const portfolioHierarchyGroupBySchema = z.enum(["sector", "symbol"]);

export const portfolioSummaryRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  open_quantity: decimalFieldSchema,
  open_cost_basis_usd: decimalFieldSchema,
  open_lot_count: z.number().int().nonnegative(),
  realized_proceeds_usd: decimalFieldSchema,
  realized_cost_basis_usd: decimalFieldSchema,
  realized_gain_usd: decimalFieldSchema,
  dividend_gross_usd: decimalFieldSchema,
  dividend_taxes_usd: decimalFieldSchema,
  dividend_net_usd: decimalFieldSchema,
  latest_close_price_usd: nullableDecimalFieldSchema,
  market_value_usd: nullableDecimalFieldSchema,
  unrealized_gain_usd: nullableDecimalFieldSchema,
  unrealized_gain_pct: nullableDecimalFieldSchema,
});

export const portfolioSummaryResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  pricing_snapshot_key: z.string().min(1).nullable(),
  pricing_snapshot_captured_at: z.string().min(1).nullable(),
  rows: z.array(portfolioSummaryRowSchema),
});

export const lotDispositionDetailSchema = z.object({
  sell_transaction_id: z.number().int().positive(),
  disposition_date: z.string().min(1),
  matched_qty: decimalFieldSchema,
  matched_cost_basis_usd: decimalFieldSchema,
  sell_gross_amount_usd: decimalFieldSchema,
});

export const portfolioLotDetailRowSchema = z.object({
  lot_id: z.number().int().positive(),
  opened_on: z.string().min(1),
  original_qty: decimalFieldSchema,
  remaining_qty: decimalFieldSchema,
  total_cost_basis_usd: decimalFieldSchema,
  unit_cost_basis_usd: decimalFieldSchema,
  dispositions: z.array(lotDispositionDetailSchema),
});

export const portfolioLotDetailResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  instrument_symbol: z.string().min(1),
  lots: z.array(portfolioLotDetailRowSchema),
});

export const portfolioTimeSeriesPointSchema = z.object({
  captured_at: z.string().min(1),
  portfolio_value_usd: decimalFieldSchema,
  pnl_usd: decimalFieldSchema,
  benchmark_sp500_value_usd: nullableDecimalFieldSchema,
  benchmark_nasdaq100_value_usd: nullableDecimalFieldSchema,
});

export const portfolioTimeSeriesResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  period: portfolioChartPeriodSchema,
  frequency: z.string().min(1),
  timezone: z.string().min(1),
  points: z.array(portfolioTimeSeriesPointSchema),
});

export const portfolioContributionRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  contribution_pnl_usd: decimalFieldSchema,
  contribution_pct: decimalFieldSchema,
});

export const portfolioContributionResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  period: portfolioChartPeriodSchema,
  rows: z.array(portfolioContributionRowSchema),
});

export const portfolioAnnualizationBasisSchema = z.object({
  kind: z.literal("trading_days"),
  value: z.number().int().positive(),
});

export const portfolioRiskEstimatorMetricSchema = z.object({
  estimator_id: z.string().min(1),
  value: decimalFieldSchema,
  window_days: z.number().int().positive(),
  return_basis: z.enum(["simple", "log"]),
  annualization_basis: portfolioAnnualizationBasisSchema,
  as_of_timestamp: z.string().min(1),
  unit: z.enum(["percent", "ratio", "unitless"]),
  interpretation_band: z.enum(["favorable", "caution", "elevated_risk"]),
  timeline_series_id: z.string().min(1).nullable(),
});

export const portfolioRiskTimelineContextSchema = z.object({
  available: z.boolean(),
  scope: z.enum(["portfolio", "instrument_symbol"]),
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
});

export const portfolioRiskRenderGuardrailsSchema = z.object({
  mixed_units: z.boolean(),
  unit_groups: z.array(z.string().min(1)),
  guidance: z.string().min(1),
});

export const portfolioRiskEstimatorsResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  window_days: z.number().int().positive(),
  metrics: z.array(portfolioRiskEstimatorMetricSchema),
  timeline_context: portfolioRiskTimelineContextSchema.nullable(),
  guardrails: portfolioRiskRenderGuardrailsSchema.nullable(),
});

export const portfolioRiskEvolutionMethodologySchema = z.object({
  drawdown_method: z.string().min(1),
  rolling_volatility_method: z.string().min(1),
  rolling_beta_method: z.string().min(1),
});

export const portfolioRiskDrawdownPointSchema = z.object({
  captured_at: z.string().min(1),
  drawdown: decimalFieldSchema,
});

export const portfolioRiskRollingPointSchema = z.object({
  captured_at: z.string().min(1),
  volatility_annualized: nullableDecimalFieldSchema,
  beta: nullableDecimalFieldSchema,
});

export const portfolioRiskEvolutionResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  scope: z.enum(["portfolio", "instrument_symbol"]),
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  rolling_window_days: z.number().int().min(2),
  methodology: portfolioRiskEvolutionMethodologySchema,
  drawdown_path_points: z.array(portfolioRiskDrawdownPointSchema),
  rolling_points: z.array(portfolioRiskRollingPointSchema),
});

export const portfolioReturnDistributionBucketPolicySchema = z.object({
  method: z.literal("equal_width"),
  bin_count: z.number().int().min(2),
  min_return: decimalFieldSchema,
  max_return: decimalFieldSchema,
});

export const portfolioReturnDistributionBucketSchema = z.object({
  bucket_index: z.number().int().nonnegative(),
  lower_bound: decimalFieldSchema,
  upper_bound: decimalFieldSchema,
  count: z.number().int().nonnegative(),
  frequency: decimalFieldSchema,
});

export const portfolioReturnDistributionResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  scope: z.enum(["portfolio", "instrument_symbol"]),
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  sample_size: z.number().int().nonnegative(),
  bucket_policy: portfolioReturnDistributionBucketPolicySchema,
  buckets: z.array(portfolioReturnDistributionBucketSchema),
});

export const portfolioQuantMetricSchema = z.object({
  metric_id: z.string().min(1),
  label: z.string().min(1),
  description: z.string().min(1),
  value: decimalFieldSchema,
  display_as: z.enum(["percent", "number"]),
});

export const portfolioQuantBenchmarkContextSchema = z.object({
  benchmark_symbol: z.string().min(1).nullable(),
  omitted_metric_ids: z.array(z.string().min(1)),
  omission_reason: z.string().min(1).nullable(),
});

export const portfolioQuantMetricsResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  period: portfolioChartPeriodSchema,
  benchmark_symbol: z.string().min(1).nullable(),
  benchmark_context: portfolioQuantBenchmarkContextSchema,
  metrics: z.array(portfolioQuantMetricSchema),
});

export const portfolioQuantReportScopeSchema = z.enum([
  "portfolio",
  "instrument_symbol",
]);
export const portfolioQuantReportLifecycleStatusSchema = z.enum([
  "ready",
  "expired",
  "unavailable",
]);

export const portfolioQuantReportGenerateRequestSchema = z.object({
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  include_simulation_context: z.boolean().optional(),
});

export const portfolioSimulationContextStatusSchema = z.enum([
  "ready",
  "unavailable",
  "error",
]);

export const portfolioQuantReportGenerateResponseSchema = z.object({
  report_id: z.string().min(1),
  report_url_path: z.string().min(1),
  lifecycle_status: portfolioQuantReportLifecycleStatusSchema,
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  benchmark_symbol: z.string().min(1).nullable(),
  generated_at: z.string().min(1),
  expires_at: z.string().min(1),
  simulation_context_status: portfolioSimulationContextStatusSchema,
  simulation_context_reason: z.string().min(1).nullable(),
  health_summary: z.lazy(() => portfolioHealthSynthesisResponseSchema).nullable().optional(),
});

export const portfolioMonteCarloRequestSchema = z.object({
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().min(1).nullable().optional(),
  period: portfolioChartPeriodSchema,
  sims: z.number().int().min(250).max(5000),
  horizon_days: z.number().int().min(5).max(756).nullable().optional(),
  bust_threshold: z.number().min(-0.95).max(0).nullable().optional(),
  goal_threshold: z.number().min(0).max(3).nullable().optional(),
  seed: z.number().int().min(0).max(2_147_483_647).nullable().optional(),
  enable_profile_comparison: z.boolean().optional(),
  calibration_basis: z.enum(["monthly", "annual", "manual"]).optional(),
});

export const portfolioMonteCarloSimulationSchema = z.object({
  sims: z.number().int().min(250).max(5000),
  horizon_days: z.number().int().min(5).max(756),
  seed: z.number().int().min(0).max(2_147_483_647),
  bust_threshold: nullableDecimalFieldSchema,
  goal_threshold: nullableDecimalFieldSchema,
});

export const portfolioMonteCarloAssumptionsSchema = z.object({
  model: z.literal("quantstats_shuffled_returns"),
  notes: z.array(z.string().min(1)),
});

export const portfolioMonteCarloSummarySchema = z.object({
  start_value_usd: decimalFieldSchema,
  median_ending_value_usd: decimalFieldSchema,
  mean_ending_return: decimalFieldSchema,
  bust_probability: nullableDecimalFieldSchema,
  goal_probability: nullableDecimalFieldSchema,
  interpretation_signal: z.enum([
    "monitor",
    "balanced",
    "downside_caution",
    "upside_favorable",
  ]),
});

export const portfolioMonteCarloPercentilePointSchema = z.object({
  percentile: z.number().int().min(0).max(100),
  value: decimalFieldSchema,
});

export const portfolioMonteCarloCalibrationContextSchema = z.object({
  requested_basis: z.enum(["monthly", "annual", "manual"]),
  effective_basis: z.enum(["monthly", "annual", "manual"]),
  sample_size: z.number().int().nonnegative(),
  lookback_start: z.string().min(1).nullable(),
  lookback_end: z.string().min(1).nullable(),
  used_fallback: z.boolean(),
  fallback_reason: z.string().min(1).nullable(),
});

export const portfolioMonteCarloProfileScenarioSchema = z.object({
  profile_id: z.enum(["conservative", "balanced", "growth"]),
  label: z.string().min(1),
  bust_threshold: decimalFieldSchema,
  goal_threshold: decimalFieldSchema,
  bust_probability: nullableDecimalFieldSchema,
  goal_probability: nullableDecimalFieldSchema,
  interpretation_signal: z.enum([
    "monitor",
    "balanced",
    "downside_caution",
    "upside_favorable",
  ]),
});

export const portfolioMonteCarloResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  simulation: portfolioMonteCarloSimulationSchema,
  assumptions: portfolioMonteCarloAssumptionsSchema,
  summary: portfolioMonteCarloSummarySchema,
  ending_return_percentiles: z.array(portfolioMonteCarloPercentilePointSchema),
  profile_comparison_enabled: z.boolean(),
  calibration_context: portfolioMonteCarloCalibrationContextSchema,
  profile_scenarios: z.array(portfolioMonteCarloProfileScenarioSchema),
});

export const portfolioHealthProfilePostureSchema = z.enum([
  "conservative",
  "balanced",
  "aggressive",
]);

export const portfolioHealthLabelSchema = z.enum([
  "healthy",
  "watchlist",
  "stressed",
]);

export const portfolioHealthPillarStatusSchema = z.enum([
  "favorable",
  "caution",
  "elevated_risk",
]);

export const portfolioHealthDriverSchema = z.object({
  metric_id: z.string().min(1),
  label: z.string().min(1),
  direction: z.enum(["supporting", "penalizing"]),
  impact_points: z.number().int().min(0).max(100),
  rationale: z.string().min(1),
  value_display: z.string().min(1),
});

export const portfolioHealthPillarMetricSchema = z.object({
  metric_id: z.string().min(1),
  label: z.string().min(1),
  value_display: z.string().min(1),
  score: z.number().int().min(0).max(100),
  contribution: z.enum(["supporting", "neutral", "penalizing"]),
});

export const portfolioHealthPillarSchema = z.object({
  pillar_id: z.enum(["growth", "risk", "risk_adjusted_quality", "resilience"]),
  label: z.string().min(1),
  score: z.number().int().min(0).max(100),
  status: portfolioHealthPillarStatusSchema,
  metrics: z.array(portfolioHealthPillarMetricSchema),
});

export const portfolioHealthSynthesisResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  profile_posture: portfolioHealthProfilePostureSchema,
  health_score: z.number().int().min(0).max(100),
  health_label: portfolioHealthLabelSchema,
  threshold_policy_version: z.string().min(1),
  pillars: z.array(portfolioHealthPillarSchema),
  key_drivers: z.array(portfolioHealthDriverSchema),
  health_caveats: z.array(z.string().min(1)),
  core_metric_ids: z.array(z.string().min(1)),
  advanced_metric_ids: z.array(z.string().min(1)),
});

export const portfolioTransactionEventSchema = z.object({
  id: z.string().min(1),
  posted_at: z.string().min(1),
  instrument_symbol: z.string().min(1),
  event_type: z.string().min(1),
  quantity: decimalFieldSchema,
  cash_amount_usd: decimalFieldSchema,
});

export const portfolioTransactionsResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  events: z.array(portfolioTransactionEventSchema),
});

export const portfolioHierarchyLotRowSchema = z.object({
  lot_id: z.number().int().positive(),
  opened_on: z.string().min(1),
  original_qty: decimalFieldSchema,
  remaining_qty: decimalFieldSchema,
  unit_cost_basis_usd: decimalFieldSchema,
  total_cost_basis_usd: decimalFieldSchema,
  market_value_usd: decimalFieldSchema,
  profit_loss_usd: decimalFieldSchema,
});

export const portfolioHierarchyAssetRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  sector_label: z.string().min(1),
  open_quantity: decimalFieldSchema,
  open_cost_basis_usd: decimalFieldSchema,
  avg_price_usd: decimalFieldSchema,
  current_price_usd: decimalFieldSchema,
  market_value_usd: decimalFieldSchema,
  profit_loss_usd: decimalFieldSchema,
  change_pct: nullableDecimalFieldSchema,
  lot_count: z.number().int().nonnegative(),
  lots: z.array(portfolioHierarchyLotRowSchema),
});

export const portfolioHierarchyGroupRowSchema = z.object({
  group_key: z.string().min(1),
  group_label: z.string().min(1),
  asset_count: z.number().int().nonnegative(),
  total_market_value_usd: decimalFieldSchema,
  total_profit_loss_usd: decimalFieldSchema,
  total_change_pct: nullableDecimalFieldSchema,
  assets: z.array(portfolioHierarchyAssetRowSchema),
});

export const portfolioHierarchyResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  group_by: portfolioHierarchyGroupBySchema,
  pricing_snapshot_key: z.string().min(1).nullable(),
  pricing_snapshot_captured_at: z.string().min(1).nullable(),
  groups: z.array(portfolioHierarchyGroupRowSchema),
});

export const portfolioCopilotOperationSchema = z.enum([
  "chat",
  "opportunity_scan",
]);
export const portfolioCopilotConversationRoleSchema = z.enum([
  "user",
  "assistant",
]);
export const portfolioCopilotResponseStateSchema = z.enum([
  "ready",
  "blocked",
  "error",
]);
export const portfolioCopilotReasonCodeSchema = z.enum([
  "boundary_restricted",
  "insufficient_context",
  "provider_blocked_policy",
  "rate_limited",
  "provider_misconfigured",
  "provider_unavailable",
]);

export const portfolioCopilotConversationMessageSchema = z.object({
  role: portfolioCopilotConversationRoleSchema,
  content: z.string().min(1).max(2000),
});

export const portfolioCopilotEvidenceReferenceSchema = z.object({
  tool_id: z.string().min(1),
  metric_id: z.string().nullable().optional(),
  as_of_ledger_at: z.string().nullable().optional(),
});

export const portfolioCopilotOpportunityCandidateSchema = z.object({
  symbol: z.string().min(1),
  opportunity_score: decimalFieldSchema,
  discount_score: decimalFieldSchema,
  momentum_score: decimalFieldSchema,
  stability_score: decimalFieldSchema,
  latest_close_price_usd: decimalFieldSchema,
  rolling_90d_high_price_usd: decimalFieldSchema,
  return_30d: decimalFieldSchema,
  volatility_30d: decimalFieldSchema,
});

export const portfolioCopilotChatRequestSchema = z.object({
  operation: portfolioCopilotOperationSchema.default("chat"),
  messages: z.array(portfolioCopilotConversationMessageSchema).min(1).max(8),
  period: portfolioChartPeriodSchema.default("90D"),
  scope: portfolioQuantReportScopeSchema.default("portfolio"),
  instrument_symbol: z.string().min(1).nullable().optional(),
  max_tool_calls: z.number().int().min(1).max(6).default(6),
});

export const portfolioCopilotChatResponseSchema = z.object({
  state: portfolioCopilotResponseStateSchema,
  answer_text: z.string(),
  evidence: z.array(portfolioCopilotEvidenceReferenceSchema),
  limitations: z.array(z.string().min(1)),
  reason_code: portfolioCopilotReasonCodeSchema.nullable(),
  opportunity_candidates: z.array(portfolioCopilotOpportunityCandidateSchema),
  opportunity_narration: z.string().nullable(),
});

export type PortfolioSummaryRow = z.infer<typeof portfolioSummaryRowSchema>;
export type PortfolioSummaryResponse = z.infer<typeof portfolioSummaryResponseSchema>;
export type LotDispositionDetail = z.infer<typeof lotDispositionDetailSchema>;
export type PortfolioLotDetailRow = z.infer<typeof portfolioLotDetailRowSchema>;
export type PortfolioLotDetailResponse = z.infer<typeof portfolioLotDetailResponseSchema>;
export type PortfolioChartPeriod = z.infer<typeof portfolioChartPeriodSchema>;
export type PortfolioTimeSeriesScope = z.infer<typeof portfolioTimeSeriesScopeSchema>;
export type PortfolioHierarchyGroupBy = z.infer<typeof portfolioHierarchyGroupBySchema>;
export type PortfolioTimeSeriesPoint = z.infer<typeof portfolioTimeSeriesPointSchema>;
export type PortfolioTimeSeriesResponse = z.infer<typeof portfolioTimeSeriesResponseSchema>;
export type PortfolioContributionRow = z.infer<typeof portfolioContributionRowSchema>;
export type PortfolioContributionResponse = z.infer<typeof portfolioContributionResponseSchema>;
export type PortfolioAnnualizationBasis = z.infer<typeof portfolioAnnualizationBasisSchema>;
export type PortfolioRiskEstimatorMetric = z.infer<
  typeof portfolioRiskEstimatorMetricSchema
>;
export type PortfolioRiskTimelineContext = z.infer<
  typeof portfolioRiskTimelineContextSchema
>;
export type PortfolioRiskRenderGuardrails = z.infer<
  typeof portfolioRiskRenderGuardrailsSchema
>;
export type PortfolioRiskEstimatorsResponse = z.infer<
  typeof portfolioRiskEstimatorsResponseSchema
>;
export type PortfolioRiskEvolutionMethodology = z.infer<
  typeof portfolioRiskEvolutionMethodologySchema
>;
export type PortfolioRiskDrawdownPoint = z.infer<
  typeof portfolioRiskDrawdownPointSchema
>;
export type PortfolioRiskRollingPoint = z.infer<
  typeof portfolioRiskRollingPointSchema
>;
export type PortfolioRiskEvolutionResponse = z.infer<
  typeof portfolioRiskEvolutionResponseSchema
>;
export type PortfolioReturnDistributionBucketPolicy = z.infer<
  typeof portfolioReturnDistributionBucketPolicySchema
>;
export type PortfolioReturnDistributionBucket = z.infer<
  typeof portfolioReturnDistributionBucketSchema
>;
export type PortfolioReturnDistributionResponse = z.infer<
  typeof portfolioReturnDistributionResponseSchema
>;
export type PortfolioQuantMetric = z.infer<typeof portfolioQuantMetricSchema>;
export type PortfolioQuantBenchmarkContext = z.infer<
  typeof portfolioQuantBenchmarkContextSchema
>;
export type PortfolioQuantMetricsResponse = z.infer<
  typeof portfolioQuantMetricsResponseSchema
>;
export type PortfolioQuantReportScope = z.infer<
  typeof portfolioQuantReportScopeSchema
>;
export type PortfolioQuantReportLifecycleStatus = z.infer<
  typeof portfolioQuantReportLifecycleStatusSchema
>;
export type PortfolioQuantReportGenerateRequest = z.infer<
  typeof portfolioQuantReportGenerateRequestSchema
>;
export type PortfolioSimulationContextStatus = z.infer<
  typeof portfolioSimulationContextStatusSchema
>;
export type PortfolioQuantReportGenerateResponse = z.infer<
  typeof portfolioQuantReportGenerateResponseSchema
>;
export type PortfolioMonteCarloRequest = z.infer<
  typeof portfolioMonteCarloRequestSchema
>;
export type PortfolioMonteCarloSimulation = z.infer<
  typeof portfolioMonteCarloSimulationSchema
>;
export type PortfolioMonteCarloAssumptions = z.infer<
  typeof portfolioMonteCarloAssumptionsSchema
>;
export type PortfolioMonteCarloSummary = z.infer<
  typeof portfolioMonteCarloSummarySchema
>;
export type PortfolioMonteCarloPercentilePoint = z.infer<
  typeof portfolioMonteCarloPercentilePointSchema
>;
export type PortfolioMonteCarloCalibrationContext = z.infer<
  typeof portfolioMonteCarloCalibrationContextSchema
>;
export type PortfolioMonteCarloProfileScenario = z.infer<
  typeof portfolioMonteCarloProfileScenarioSchema
>;
export type PortfolioMonteCarloResponse = z.infer<
  typeof portfolioMonteCarloResponseSchema
>;
export type PortfolioHealthProfilePosture = z.infer<
  typeof portfolioHealthProfilePostureSchema
>;
export type PortfolioHealthLabel = z.infer<typeof portfolioHealthLabelSchema>;
export type PortfolioHealthPillarStatus = z.infer<
  typeof portfolioHealthPillarStatusSchema
>;
export type PortfolioHealthDriver = z.infer<typeof portfolioHealthDriverSchema>;
export type PortfolioHealthPillarMetric = z.infer<
  typeof portfolioHealthPillarMetricSchema
>;
export type PortfolioHealthPillar = z.infer<typeof portfolioHealthPillarSchema>;
export type PortfolioHealthSynthesisResponse = z.infer<
  typeof portfolioHealthSynthesisResponseSchema
>;
export type PortfolioTransactionEvent = z.infer<
  typeof portfolioTransactionEventSchema
>;
export type PortfolioTransactionsResponse = z.infer<
  typeof portfolioTransactionsResponseSchema
>;
export type PortfolioHierarchyLotRow = z.infer<
  typeof portfolioHierarchyLotRowSchema
>;
export type PortfolioHierarchyAssetRow = z.infer<
  typeof portfolioHierarchyAssetRowSchema
>;
export type PortfolioHierarchyGroupRow = z.infer<
  typeof portfolioHierarchyGroupRowSchema
>;
export type PortfolioHierarchyResponse = z.infer<
  typeof portfolioHierarchyResponseSchema
>;
export type PortfolioCopilotOperation = z.infer<
  typeof portfolioCopilotOperationSchema
>;
export type PortfolioCopilotConversationRole = z.infer<
  typeof portfolioCopilotConversationRoleSchema
>;
export type PortfolioCopilotResponseState = z.infer<
  typeof portfolioCopilotResponseStateSchema
>;
export type PortfolioCopilotReasonCode = z.infer<
  typeof portfolioCopilotReasonCodeSchema
>;
export type PortfolioCopilotConversationMessage = z.infer<
  typeof portfolioCopilotConversationMessageSchema
>;
export type PortfolioCopilotEvidenceReference = z.infer<
  typeof portfolioCopilotEvidenceReferenceSchema
>;
export type PortfolioCopilotOpportunityCandidate = z.infer<
  typeof portfolioCopilotOpportunityCandidateSchema
>;
export type PortfolioCopilotChatRequest = z.infer<
  typeof portfolioCopilotChatRequestSchema
>;
export type PortfolioCopilotChatResponse = z.infer<
  typeof portfolioCopilotChatResponseSchema
>;
