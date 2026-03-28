import { z } from "zod";

const decimalFieldSchema = z.string().min(1);
const nullableDecimalFieldSchema = z.union([decimalFieldSchema, z.null()]);

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

export type PortfolioSummaryRow = z.infer<typeof portfolioSummaryRowSchema>;
export type PortfolioSummaryResponse = z.infer<typeof portfolioSummaryResponseSchema>;
export type LotDispositionDetail = z.infer<typeof lotDispositionDetailSchema>;
export type PortfolioLotDetailRow = z.infer<typeof portfolioLotDetailRowSchema>;
export type PortfolioLotDetailResponse = z.infer<typeof portfolioLotDetailResponseSchema>;
