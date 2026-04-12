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

export const portfolioDecisionStateSchema = z.enum([
  "ready",
  "unavailable",
  "stale",
]);

export const portfolioDecisionFreshnessPolicySchema = z.object({
  max_age_hours: z.number().int().positive(),
});

export const portfolioCommandCenterInsightSchema = z.object({
  insight_id: z.string().min(1),
  title: z.string().min(1),
  message: z.string().min(1),
  severity: z.enum(["info", "caution", "elevated_risk"]),
});

export const portfolioCommandCenterResponseSchema = z.object({
  state: portfolioDecisionStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1).nullable(),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioDecisionFreshnessPolicySchema,
  net_worth_usd: decimalFieldSchema,
  total_market_value_usd: decimalFieldSchema,
  daily_pnl_usd: decimalFieldSchema,
  concentration_top5_pct: decimalFieldSchema,
  insights: z.array(portfolioCommandCenterInsightSchema),
});

export const portfolioExposureRowSchema = z.object({
  dimension: z.enum(["asset_class", "sector", "currency", "country"]),
  bucket_id: z.string().min(1),
  bucket_label: z.string().min(1),
  weight_pct: decimalFieldSchema,
  market_value_usd: decimalFieldSchema,
});

export const portfolioExposureResponseSchema = z.object({
  state: portfolioDecisionStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1).nullable(),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioDecisionFreshnessPolicySchema,
  rows: z.array(portfolioExposureRowSchema),
});

export const portfolioContributionToRiskMethodologySchema = z.object({
  methodology_id: z.string().min(1),
  risk_measure: z.string().min(1),
  lookback_days: z.number().int().positive(),
  annualization_basis: z.string().min(1),
});

export const portfolioContributionToRiskRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  contribution_to_risk_pct: decimalFieldSchema,
  volatility_annualized: nullableDecimalFieldSchema,
});

export const portfolioContributionToRiskResponseSchema = z.object({
  state: portfolioDecisionStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1).nullable(),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioDecisionFreshnessPolicySchema,
  methodology: portfolioContributionToRiskMethodologySchema,
  rows: z.array(portfolioContributionToRiskRowSchema),
});

export const portfolioCorrelationMatrixRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  correlations: z.record(z.string(), decimalFieldSchema),
});

export const portfolioCorrelationResponseSchema = z.object({
  state: portfolioDecisionStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1).nullable(),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioDecisionFreshnessPolicySchema,
  symbols: z.array(z.string().min(1)),
  guardrail_max_symbols: z.number().int().min(2),
  rows: z.array(portfolioCorrelationMatrixRowSchema),
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

export const portfolioEfficientFrontierMethodologySchema = z.object({
  optimization_model: z.string().min(1),
  sampling_method: z.string().min(1),
  annualization_basis: z.string().min(1),
});

export const portfolioEfficientFrontierPointSchema = z.object({
  point_id: z.string().min(1),
  expected_return: decimalFieldSchema,
  volatility: decimalFieldSchema,
  sharpe_ratio: decimalFieldSchema,
  is_max_sharpe: z.boolean(),
  is_min_volatility: z.boolean(),
});

export const portfolioEfficientFrontierAssetPointSchema = z.object({
  instrument_symbol: z.string().min(1),
  expected_return: decimalFieldSchema,
  volatility: decimalFieldSchema,
});

export const portfolioEfficientFrontierWeightSchema = z.object({
  instrument_symbol: z.string().min(1),
  weight: decimalFieldSchema,
});

export const portfolioEfficientFrontierResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  scope: z.enum(["portfolio", "instrument_symbol"]),
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  risk_free_rate_annual: decimalFieldSchema,
  methodology: portfolioEfficientFrontierMethodologySchema,
  frontier_points: z.array(portfolioEfficientFrontierPointSchema),
  asset_points: z.array(portfolioEfficientFrontierAssetPointSchema),
  max_sharpe_weights: z.array(portfolioEfficientFrontierWeightSchema),
  min_volatility_weights: z.array(portfolioEfficientFrontierWeightSchema),
});

export const portfolioMLScopeSchema = z.enum([
  "portfolio",
  "instrument_symbol",
]);
export const portfolioMLStateSchema = z.enum([
  "ready",
  "unavailable",
  "stale",
  "error",
]);
export const portfolioMLFreshnessPolicySchema = z.object({
  max_age_hours: z.number().int().positive(),
});
export const portfolioMLSignalRowSchema = z.object({
  signal_id: z.string().min(1),
  label: z.string().min(1),
  unit: z.string().min(1),
  interpretation_band: z.string().min(1),
  value: decimalFieldSchema,
});
export const portfolioMLCapmMetricsSchema = z.object({
  beta: nullableDecimalFieldSchema,
  alpha: nullableDecimalFieldSchema,
  expected_return: nullableDecimalFieldSchema,
  market_premium: nullableDecimalFieldSchema,
  benchmark_symbol: z.string().min(1).nullable(),
  risk_free_source: z.string().min(1).nullable(),
  annualization_factor: z.number().int().positive().nullable(),
});
export const portfolioMLSignalResponseSchema = z.object({
  state: portfolioMLStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  scope: portfolioMLScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioMLFreshnessPolicySchema,
  signals: z.array(portfolioMLSignalRowSchema),
  capm: portfolioMLCapmMetricsSchema,
});
export const portfolioMLForecastHorizonRowSchema = z.object({
  horizon_id: z.string().min(1),
  point_estimate: decimalFieldSchema,
  lower_bound: decimalFieldSchema,
  upper_bound: decimalFieldSchema,
  confidence_level: decimalFieldSchema,
  model_snapshot_ref: z.string().min(1),
  p10: nullableDecimalFieldSchema.optional(),
  p50: nullableDecimalFieldSchema.optional(),
  p90: nullableDecimalFieldSchema.optional(),
});
export const portfolioMLForecastResponseSchema = z.object({
  state: portfolioMLStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  scope: portfolioMLScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioMLFreshnessPolicySchema,
  model_snapshot_ref: z.string().min(1).nullable(),
  model_family: z.string().min(1).nullable(),
  training_window_start: z.string().min(1).nullable(),
  training_window_end: z.string().min(1).nullable(),
  horizons: z.array(portfolioMLForecastHorizonRowSchema),
});
export const portfolioMLRegistryRowSchema = z.object({
  snapshot_ref: z.string().min(1),
  scope: portfolioMLScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  model_family: z.string().min(1),
  lifecycle_state: portfolioMLStateSchema,
  feature_set_hash: z.string().min(1),
  feature_set_version: z.string().min(1).nullable().optional(),
  policy_version: z.string().min(1).nullable().optional(),
  family_state_reason_code: z.string().min(1).nullable().optional(),
  data_window_start: z.string().min(1),
  data_window_end: z.string().min(1),
  run_status: z.string().min(1),
  promoted_at: z.string().min(1).nullable(),
  expires_at: z.string().min(1).nullable(),
  replaced_snapshot_ref: z.string().min(1).nullable(),
  policy_result: z.record(z.string(), z.unknown()),
  metric_vector: z.record(z.string(), z.unknown()),
  baseline_comparator_metrics: z.record(z.string(), z.unknown()),
  snapshot_metadata: z.record(z.string(), z.unknown()).optional(),
});
export const portfolioMLRegistryResponseSchema = z.object({
  state: portfolioMLStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1),
  evaluated_at: z.string().min(1),
  rows: z.array(portfolioMLRegistryRowSchema),
});

export const portfolioMLClusterRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  cluster_id: z.string().min(1),
  cluster_label: z.string().min(1),
  return_30d: decimalFieldSchema,
  volatility_30d: decimalFieldSchema,
});

export const portfolioMLClustersResponseSchema = z.object({
  state: portfolioMLStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  scope: portfolioMLScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioMLFreshnessPolicySchema,
  model_family: z.string().min(1),
  feature_set_hash: z.string().min(1).nullable().optional(),
  policy_version: z.string().min(1).nullable().optional(),
  rows: z.array(portfolioMLClusterRowSchema),
});

export const portfolioMLAnomalyRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  event_at: z.string().min(1),
  anomaly_score: decimalFieldSchema,
  severity: z.string().min(1),
  reason_code: z.string().min(1),
});

export const portfolioMLAnomaliesResponseSchema = z.object({
  state: portfolioMLStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  scope: portfolioMLScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioMLFreshnessPolicySchema,
  model_family: z.string().min(1),
  feature_set_hash: z.string().min(1).nullable().optional(),
  policy_version: z.string().min(1).nullable().optional(),
  rows: z.array(portfolioMLAnomalyRowSchema),
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

export const portfolioRebalancingStateSchema = z.enum([
  "ready",
  "unavailable",
  "infeasible",
]);

export const portfolioRebalancingFreshnessPolicySchema = z.object({
  max_age_hours: z.number().int().positive(),
});

export const portfolioRebalancingStrategyIdSchema = z.enum([
  "mvo",
  "hrp",
  "black_litterman",
]);

export const portfolioRebalancingWeightRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  current_weight_pct: decimalFieldSchema,
  suggested_weight_pct: decimalFieldSchema,
  delta_weight_pct: decimalFieldSchema,
});

export const portfolioRebalancingStrategyRowSchema = z.object({
  strategy_id: portfolioRebalancingStrategyIdSchema,
  strategy_label: z.string().min(1),
  expected_return_annualized: decimalFieldSchema,
  expected_volatility_annualized: decimalFieldSchema,
  expected_sharpe: decimalFieldSchema,
  weights: z.array(portfolioRebalancingWeightRowSchema),
});

export const portfolioRebalancingStrategiesResponseSchema = z.object({
  state: portfolioRebalancingStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1).nullable(),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioRebalancingFreshnessPolicySchema,
  strategies: z.array(portfolioRebalancingStrategyRowSchema),
  caveats: z.array(z.string().min(1)),
});

export const portfolioRebalancingScenarioConstraintsSchema = z.object({
  max_position_weight_pct: nullableDecimalFieldSchema,
  max_turnover_pct: nullableDecimalFieldSchema,
  excluded_symbols: z.array(z.string().min(1)).max(25),
});

export const portfolioRebalancingScenarioRequestConstraintsSchema = z.object({
  max_position_weight_pct: nullableDecimalFieldSchema.optional(),
  max_turnover_pct: nullableDecimalFieldSchema.optional(),
  excluded_symbols: z.array(z.string().min(1)).max(25).default([]),
});

export const portfolioRebalancingScenarioRequestSchema = z.object({
  constraints: portfolioRebalancingScenarioRequestConstraintsSchema.default({}),
});

export const portfolioRebalancingScenarioResponseSchema = z.object({
  state: portfolioRebalancingStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1).nullable(),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioRebalancingFreshnessPolicySchema,
  applied_constraints: portfolioRebalancingScenarioConstraintsSchema,
  binding_constraints: z.array(z.string().min(1)),
  baseline_strategies: z.array(portfolioRebalancingStrategyRowSchema),
  constrained_strategies: z.array(portfolioRebalancingStrategyRowSchema),
  infeasible_cause: z.string().min(1).nullable(),
  caveats: z.array(z.string().min(1)),
});

export const portfolioNewsContextStateSchema = z.enum([
  "ready",
  "unavailable",
]);

export const portfolioNewsFreshnessPolicySchema = z.object({
  max_age_hours: z.number().int().positive(),
});

export const portfolioNewsSourceRowSchema = z.object({
  source_id: z.string().min(1),
  source_label: z.string().min(1),
  published_at: z.string().min(1),
  url: z.string().min(1),
});

export const portfolioNewsContextRowSchema = z.object({
  instrument_symbol: z.string().min(1),
  market_value_weight_pct: decimalFieldSchema,
  summary: z.string().min(1),
  impact_bias: z.string().min(1),
  caveats: z.array(z.string().min(1)),
  sources: z.array(portfolioNewsSourceRowSchema),
});

export const portfolioNewsContextResponseSchema = z.object({
  state: portfolioNewsContextStateSchema,
  state_reason_code: z.string().min(1),
  state_reason_detail: z.string().min(1),
  as_of_ledger_at: z.string().min(1),
  as_of_market_at: z.string().min(1).nullable(),
  evaluated_at: z.string().min(1),
  freshness_policy: portfolioNewsFreshnessPolicySchema,
  rows: z.array(portfolioNewsContextRowSchema),
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
export const portfolioCopilotOpportunityActionStateSchema = z.enum([
  "baseline_dca",
  "double_down_candidate",
  "watchlist",
  "hold_off",
]);
export const portfolioCopilotFundamentalsProxyStateSchema = z.enum([
  "passed",
  "failed",
  "inconclusive",
]);
export const portfolioCopilotOpportunityStrategyProfileSchema = z.enum([
  "dca_2x_v1",
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
  currently_held: z.boolean(),
  action_state: portfolioCopilotOpportunityActionStateSchema,
  action_multiplier: decimalFieldSchema,
  action_reason_codes: z.array(z.string().min(1)).max(8).default([]),
  fundamentals_proxy_state: portfolioCopilotFundamentalsProxyStateSchema,
  fundamentals_proxy_score: decimalFieldSchema,
  opportunity_score: decimalFieldSchema,
  discount_score: decimalFieldSchema,
  momentum_score: decimalFieldSchema,
  stability_score: decimalFieldSchema,
  latest_close_price_usd: decimalFieldSchema,
  rolling_90d_high_price_usd: decimalFieldSchema,
  rolling_52w_high_price_usd: decimalFieldSchema,
  drawdown_from_52w_high_pct: decimalFieldSchema,
  return_30d: decimalFieldSchema,
  return_90d: decimalFieldSchema,
  return_252d: decimalFieldSchema,
  volatility_30d: decimalFieldSchema,
});

export const portfolioCopilotChatRequestSchema = z.object({
  operation: portfolioCopilotOperationSchema.default("chat"),
  messages: z.array(portfolioCopilotConversationMessageSchema).min(1).max(8),
  period: portfolioChartPeriodSchema.default("90D"),
  scope: portfolioQuantReportScopeSchema.default("portfolio"),
  instrument_symbol: z.string().min(1).nullable().optional(),
  max_tool_calls: z.number().int().min(1).max(6).default(6),
  opportunity_strategy_profile:
    portfolioCopilotOpportunityStrategyProfileSchema.default("dca_2x_v1"),
  double_down_threshold_pct: decimalFieldSchema.default("0.20"),
  double_down_multiplier: decimalFieldSchema.default("2.0"),
  document_ids: z.array(z.number().int().positive()).max(8).default([]),
});

export const portfolioCopilotChatResponseSchema = z.object({
  state: portfolioCopilotResponseStateSchema,
  answer: z.string().optional().default(""),
  answer_text: z.string().optional().default(""),
  evidence: z.array(portfolioCopilotEvidenceReferenceSchema),
  assumptions: z.array(z.string().min(1)).max(8).default([]),
  caveats: z.array(z.string().min(1)).max(12).default([]),
  suggested_follow_ups: z.array(z.string().min(1)).max(6).default([]),
  limitations: z.array(z.string().min(1)).default([]),
  reason_code: portfolioCopilotReasonCodeSchema.nullable(),
  opportunity_candidates: z.array(portfolioCopilotOpportunityCandidateSchema),
  opportunity_narration: z.string().nullable(),
  prompt_suggestions: z.array(z.string().min(1)).max(4).default([]),
}).transform((payload) => {
  const answer =
    payload.answer.trim().length > 0
      ? payload.answer.trim()
      : payload.answer_text.trim();
  const caveats =
    payload.caveats.length > 0 ? payload.caveats : payload.limitations;
  const suggestedFollowUps =
    payload.suggested_follow_ups.length > 0
      ? payload.suggested_follow_ups
      : payload.prompt_suggestions.slice(0, 6);
  const promptSuggestions =
    payload.prompt_suggestions.length > 0
      ? payload.prompt_suggestions.slice(0, 4)
      : suggestedFollowUps.slice(0, 4);
  return {
    ...payload,
    answer,
    answer_text: answer,
    caveats,
    limitations: caveats,
    suggested_follow_ups: suggestedFollowUps.slice(0, 6),
    prompt_suggestions: promptSuggestions,
  };
});

export type PortfolioSummaryRow = z.infer<typeof portfolioSummaryRowSchema>;
export type PortfolioSummaryResponse = z.infer<typeof portfolioSummaryResponseSchema>;
export type PortfolioDecisionState = z.infer<typeof portfolioDecisionStateSchema>;
export type PortfolioDecisionFreshnessPolicy = z.infer<
  typeof portfolioDecisionFreshnessPolicySchema
>;
export type PortfolioCommandCenterInsight = z.infer<
  typeof portfolioCommandCenterInsightSchema
>;
export type PortfolioCommandCenterResponse = z.infer<
  typeof portfolioCommandCenterResponseSchema
>;
export type PortfolioExposureRow = z.infer<typeof portfolioExposureRowSchema>;
export type PortfolioExposureResponse = z.infer<typeof portfolioExposureResponseSchema>;
export type PortfolioContributionToRiskMethodology = z.infer<
  typeof portfolioContributionToRiskMethodologySchema
>;
export type PortfolioContributionToRiskRow = z.infer<
  typeof portfolioContributionToRiskRowSchema
>;
export type PortfolioContributionToRiskResponse = z.infer<
  typeof portfolioContributionToRiskResponseSchema
>;
export type PortfolioCorrelationMatrixRow = z.infer<
  typeof portfolioCorrelationMatrixRowSchema
>;
export type PortfolioCorrelationResponse = z.infer<
  typeof portfolioCorrelationResponseSchema
>;
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
export type PortfolioEfficientFrontierMethodology = z.infer<
  typeof portfolioEfficientFrontierMethodologySchema
>;
export type PortfolioEfficientFrontierPoint = z.infer<
  typeof portfolioEfficientFrontierPointSchema
>;
export type PortfolioEfficientFrontierAssetPoint = z.infer<
  typeof portfolioEfficientFrontierAssetPointSchema
>;
export type PortfolioEfficientFrontierWeight = z.infer<
  typeof portfolioEfficientFrontierWeightSchema
>;
export type PortfolioEfficientFrontierResponse = z.infer<
  typeof portfolioEfficientFrontierResponseSchema
>;
export type PortfolioMLScope = z.infer<typeof portfolioMLScopeSchema>;
export type PortfolioMLState = z.infer<typeof portfolioMLStateSchema>;
export type PortfolioMLFreshnessPolicy = z.infer<
  typeof portfolioMLFreshnessPolicySchema
>;
export type PortfolioMLSignalRow = z.infer<typeof portfolioMLSignalRowSchema>;
export type PortfolioMLCapmMetrics = z.infer<typeof portfolioMLCapmMetricsSchema>;
export type PortfolioMLSignalResponse = z.infer<
  typeof portfolioMLSignalResponseSchema
>;
export type PortfolioMLForecastHorizonRow = z.infer<
  typeof portfolioMLForecastHorizonRowSchema
>;
export type PortfolioMLForecastResponse = z.infer<
  typeof portfolioMLForecastResponseSchema
>;
export type PortfolioMLRegistryRow = z.infer<typeof portfolioMLRegistryRowSchema>;
export type PortfolioMLRegistryResponse = z.infer<
  typeof portfolioMLRegistryResponseSchema
>;
export type PortfolioMLClusterRow = z.infer<typeof portfolioMLClusterRowSchema>;
export type PortfolioMLClustersResponse = z.infer<
  typeof portfolioMLClustersResponseSchema
>;
export type PortfolioMLAnomalyRow = z.infer<typeof portfolioMLAnomalyRowSchema>;
export type PortfolioMLAnomaliesResponse = z.infer<
  typeof portfolioMLAnomaliesResponseSchema
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
export type PortfolioRebalancingState = z.infer<
  typeof portfolioRebalancingStateSchema
>;
export type PortfolioRebalancingFreshnessPolicy = z.infer<
  typeof portfolioRebalancingFreshnessPolicySchema
>;
export type PortfolioRebalancingStrategyId = z.infer<
  typeof portfolioRebalancingStrategyIdSchema
>;
export type PortfolioRebalancingWeightRow = z.infer<
  typeof portfolioRebalancingWeightRowSchema
>;
export type PortfolioRebalancingStrategyRow = z.infer<
  typeof portfolioRebalancingStrategyRowSchema
>;
export type PortfolioRebalancingStrategiesResponse = z.infer<
  typeof portfolioRebalancingStrategiesResponseSchema
>;
export type PortfolioRebalancingScenarioConstraints = z.infer<
  typeof portfolioRebalancingScenarioConstraintsSchema
>;
export type PortfolioRebalancingScenarioRequest = z.infer<
  typeof portfolioRebalancingScenarioRequestSchema
>;
export type PortfolioRebalancingScenarioResponse = z.infer<
  typeof portfolioRebalancingScenarioResponseSchema
>;
export type PortfolioNewsContextState = z.infer<
  typeof portfolioNewsContextStateSchema
>;
export type PortfolioNewsFreshnessPolicy = z.infer<
  typeof portfolioNewsFreshnessPolicySchema
>;
export type PortfolioNewsSourceRow = z.infer<typeof portfolioNewsSourceRowSchema>;
export type PortfolioNewsContextRow = z.infer<typeof portfolioNewsContextRowSchema>;
export type PortfolioNewsContextResponse = z.infer<
  typeof portfolioNewsContextResponseSchema
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
export type PortfolioCopilotOpportunityActionState = z.infer<
  typeof portfolioCopilotOpportunityActionStateSchema
>;
export type PortfolioCopilotFundamentalsProxyState = z.infer<
  typeof portfolioCopilotFundamentalsProxyStateSchema
>;
export type PortfolioCopilotOpportunityStrategyProfile = z.infer<
  typeof portfolioCopilotOpportunityStrategyProfileSchema
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
