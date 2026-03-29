import { z } from "zod";

const decimalFieldSchema = z.string().min(1);
const nullableDecimalFieldSchema = z.union([decimalFieldSchema, z.null()]);
export const portfolioChartPeriodSchema = z.enum(["30D", "90D", "252D", "MAX"]);
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
});

export const portfolioRiskEstimatorsResponseSchema = z.object({
  as_of_ledger_at: z.string().min(1),
  window_days: z.number().int().positive(),
  metrics: z.array(portfolioRiskEstimatorMetricSchema),
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

export const portfolioQuantReportGenerateRequestSchema = z.object({
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
});

export const portfolioQuantReportGenerateResponseSchema = z.object({
  report_id: z.string().min(1),
  report_url_path: z.string().min(1),
  scope: portfolioQuantReportScopeSchema,
  instrument_symbol: z.string().min(1).nullable(),
  period: portfolioChartPeriodSchema,
  benchmark_symbol: z.string().min(1).nullable(),
  generated_at: z.string().min(1),
  expires_at: z.string().min(1),
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

export type PortfolioSummaryRow = z.infer<typeof portfolioSummaryRowSchema>;
export type PortfolioSummaryResponse = z.infer<typeof portfolioSummaryResponseSchema>;
export type LotDispositionDetail = z.infer<typeof lotDispositionDetailSchema>;
export type PortfolioLotDetailRow = z.infer<typeof portfolioLotDetailRowSchema>;
export type PortfolioLotDetailResponse = z.infer<typeof portfolioLotDetailResponseSchema>;
export type PortfolioChartPeriod = z.infer<typeof portfolioChartPeriodSchema>;
export type PortfolioHierarchyGroupBy = z.infer<typeof portfolioHierarchyGroupBySchema>;
export type PortfolioTimeSeriesPoint = z.infer<typeof portfolioTimeSeriesPointSchema>;
export type PortfolioTimeSeriesResponse = z.infer<typeof portfolioTimeSeriesResponseSchema>;
export type PortfolioContributionRow = z.infer<typeof portfolioContributionRowSchema>;
export type PortfolioContributionResponse = z.infer<typeof portfolioContributionResponseSchema>;
export type PortfolioAnnualizationBasis = z.infer<typeof portfolioAnnualizationBasisSchema>;
export type PortfolioRiskEstimatorMetric = z.infer<
  typeof portfolioRiskEstimatorMetricSchema
>;
export type PortfolioRiskEstimatorsResponse = z.infer<
  typeof portfolioRiskEstimatorsResponseSchema
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
export type PortfolioQuantReportGenerateRequest = z.infer<
  typeof portfolioQuantReportGenerateRequestSchema
>;
export type PortfolioQuantReportGenerateResponse = z.infer<
  typeof portfolioQuantReportGenerateResponseSchema
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
