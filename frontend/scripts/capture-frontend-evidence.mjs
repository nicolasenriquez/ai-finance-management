import http from "node:http";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(projectRoot, "..");
const distRoot = path.join(projectRoot, "dist");
const reportRoot = path.join(repoRoot, "docs", "evidence", "frontend");
const indexHtmlPath = path.join(distRoot, "index.html");

const SERVER_HOST = "127.0.0.1";
const DEFAULT_LISTEN_PORT = 0;
const DEFAULT_SCREENSHOT_SETTLE_DELAY_MS = 1200;
const THEME_STORAGE_KEY = "ai-finance-management-theme";

const summaryPayload = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  pricing_snapshot_key: "yf|d1|1d|3mo|aa1rp1|2026-03-24|s2|a1b2c3d4e5f6",
  pricing_snapshot_captured_at: "2026-03-24T00:55:00Z",
  rows: [
    {
      instrument_symbol: "VOO",
      open_quantity: "4.000000000",
      open_cost_basis_usd: "900.00",
      open_lot_count: 1,
      realized_proceeds_usd: "500.00",
      realized_cost_basis_usd: "450.00",
      realized_gain_usd: "50.00",
      dividend_gross_usd: "10.00",
      dividend_taxes_usd: "2.00",
      dividend_net_usd: "8.00",
      latest_close_price_usd: "240.00",
      market_value_usd: "960.00",
      unrealized_gain_usd: "60.00",
      unrealized_gain_pct: "6.67",
    },
    {
      instrument_symbol: "PLTR",
      open_quantity: "2.000000000",
      open_cost_basis_usd: "1000.00",
      open_lot_count: 2,
      realized_proceeds_usd: "400.00",
      realized_cost_basis_usd: "320.00",
      realized_gain_usd: "80.00",
      dividend_gross_usd: "18.00",
      dividend_taxes_usd: "3.00",
      dividend_net_usd: "15.00",
      latest_close_price_usd: "530.00",
      market_value_usd: "1060.00",
      unrealized_gain_usd: "60.00",
      unrealized_gain_pct: "6.00",
    },
  ],
};

const lotDetailPayload = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  instrument_symbol: "VOO",
  lots: [
    {
      lot_id: 15,
      opened_on: "2025-12-01",
      original_qty: "4.000000000",
      remaining_qty: "2.000000000",
      total_cost_basis_usd: "900.00",
      unit_cost_basis_usd: "225.00",
      dispositions: [
        {
          sell_transaction_id: 88,
          disposition_date: "2026-01-10",
          matched_qty: "2.000000000",
          matched_cost_basis_usd: "450.00",
          sell_gross_amount_usd: "500.00",
        },
      ],
    },
  ],
};

const transactionsPayload = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  events: [
    {
      id: "trade:101",
      posted_at: "2026-03-24T00:00:00Z",
      instrument_symbol: "PLTR",
      event_type: "buy",
      quantity: "1.000000000",
      cash_amount_usd: "250.00",
    },
    {
      id: "dividend:51",
      posted_at: "2026-03-22T00:00:00Z",
      instrument_symbol: "VOO",
      event_type: "dividend",
      quantity: "0.000000000",
      cash_amount_usd: "6.00",
    },
    {
      id: "trade:99",
      posted_at: "2026-03-20T00:00:00Z",
      instrument_symbol: "VOO",
      event_type: "sell",
      quantity: "0.500000000",
      cash_amount_usd: "180.00",
    },
  ],
};

const supportedChartPeriods = ["30D", "90D", "252D", "MAX"];
const supportedHierarchyGroups = ["sector", "symbol"];
const supportedRiskWindows = [30, 90, 252];
const supportedHealthProfilePostures = ["conservative", "balanced", "aggressive"];

const hierarchyPayloadByGroup = {
  sector: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    group_by: "sector",
    pricing_snapshot_key: "yf|d1|1d|3mo|aa1rp1|2026-03-24|s2|a1b2c3d4e5f6",
    pricing_snapshot_captured_at: "2026-03-24T00:55:00Z",
    groups: [
      {
        group_key: "Technology",
        group_label: "Technology",
        asset_count: 2,
        total_market_value_usd: "1475.00",
        total_profit_loss_usd: "255.00",
        total_change_pct: "20.90",
        assets: [
          {
            instrument_symbol: "PLTR",
            sector_label: "Technology",
            open_quantity: "2.000000000",
            open_cost_basis_usd: "1000.00",
            avg_price_usd: "500.00",
            current_price_usd: "530.00",
            market_value_usd: "1060.00",
            profit_loss_usd: "60.00",
            change_pct: "6.00",
            lot_count: 2,
            lots: [
              {
                lot_id: 21,
                opened_on: "2025-12-20",
                original_qty: "1.000000000",
                remaining_qty: "1.000000000",
                unit_cost_basis_usd: "480.00",
                total_cost_basis_usd: "480.00",
                market_value_usd: "530.00",
                profit_loss_usd: "50.00",
              },
              {
                lot_id: 22,
                opened_on: "2026-01-05",
                original_qty: "1.000000000",
                remaining_qty: "1.000000000",
                unit_cost_basis_usd: "520.00",
                total_cost_basis_usd: "520.00",
                market_value_usd: "530.00",
                profit_loss_usd: "10.00",
              },
            ],
          },
          {
            instrument_symbol: "SCHD",
            sector_label: "Technology",
            open_quantity: "1.000000000",
            open_cost_basis_usd: "220.00",
            avg_price_usd: "220.00",
            current_price_usd: "415.00",
            market_value_usd: "415.00",
            profit_loss_usd: "195.00",
            change_pct: "88.64",
            lot_count: 1,
            lots: [
              {
                lot_id: 31,
                opened_on: "2025-11-01",
                original_qty: "1.000000000",
                remaining_qty: "1.000000000",
                unit_cost_basis_usd: "220.00",
                total_cost_basis_usd: "220.00",
                market_value_usd: "415.00",
                profit_loss_usd: "195.00",
              },
            ],
          },
        ],
      },
      {
        group_key: "Index",
        group_label: "Index",
        asset_count: 1,
        total_market_value_usd: "960.00",
        total_profit_loss_usd: "60.00",
        total_change_pct: "6.67",
        assets: [
          {
            instrument_symbol: "VOO",
            sector_label: "Index",
            open_quantity: "4.000000000",
            open_cost_basis_usd: "900.00",
            avg_price_usd: "225.00",
            current_price_usd: "240.00",
            market_value_usd: "960.00",
            profit_loss_usd: "60.00",
            change_pct: "6.67",
            lot_count: 1,
            lots: [
              {
                lot_id: 15,
                opened_on: "2025-12-01",
                original_qty: "4.000000000",
                remaining_qty: "4.000000000",
                unit_cost_basis_usd: "225.00",
                total_cost_basis_usd: "900.00",
                market_value_usd: "960.00",
                profit_loss_usd: "60.00",
              },
            ],
          },
        ],
      },
    ],
  },
  symbol: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    group_by: "symbol",
    pricing_snapshot_key: "yf|d1|1d|3mo|aa1rp1|2026-03-24|s2|a1b2c3d4e5f6",
    pricing_snapshot_captured_at: "2026-03-24T00:55:00Z",
    groups: [],
  },
};

function buildHealthSynthesisPayload({
  period,
  scope,
  profilePosture,
  instrumentSymbol,
}) {
  return {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    scope,
    instrument_symbol: scope === "instrument_symbol" ? instrumentSymbol : null,
    period,
    profile_posture: profilePosture,
    health_score: 84,
    health_label: "healthy",
    threshold_policy_version: "health_v1_20260330",
    pillars: [
      {
        pillar_id: "growth",
        label: "Growth",
        score: 100,
        status: "favorable",
        metrics: [
          {
            metric_id: "cagr",
            label: "CAGR",
            value_display: "+16.89%",
            score: 100,
            contribution: "supporting",
          },
        ],
      },
      {
        pillar_id: "risk",
        label: "Risk",
        score: 75,
        status: "favorable",
        metrics: [
          {
            metric_id: "max_drawdown",
            label: "Max Drawdown",
            value_display: "-23.00%",
            score: 75,
            contribution: "supporting",
          },
        ],
      },
      {
        pillar_id: "risk_adjusted_quality",
        label: "Risk-adjusted quality",
        score: 80,
        status: "favorable",
        metrics: [
          {
            metric_id: "sharpe_ratio",
            label: "Sharpe Ratio",
            value_display: "0.837",
            score: 80,
            contribution: "supporting",
          },
        ],
      },
      {
        pillar_id: "resilience",
        label: "Resilience",
        score: 80,
        status: "favorable",
        metrics: [
          {
            metric_id: "recovery_factor",
            label: "Recovery Factor",
            value_display: "3.689",
            score: 80,
            contribution: "supporting",
          },
        ],
      },
    ],
    key_drivers: [
      {
        metric_id: "three_year_annualized_return",
        label: "3Y Annualized Return",
        direction: "supporting",
        impact_points: 12,
        rationale: "Sustained annualized growth supports a stable health posture.",
        value_display: "+28.90%",
      },
      {
        metric_id: "recovery_factor",
        label: "Recovery Factor",
        direction: "supporting",
        impact_points: 8,
        rationale: "Recovery efficiency remains above threshold policy expectations.",
        value_display: "3.689",
      },
    ],
    health_caveats: [
      "Synthetic fixture payload used for deterministic frontend evidence capture.",
    ],
    core_metric_ids: ["cagr", "max_drawdown", "sharpe_ratio", "recovery_factor"],
    advanced_metric_ids: ["value_at_risk_95"],
  };
}

const timeSeriesPayloadByPeriod = {
  "30D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "30D",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2026-03-19T00:00:00Z", portfolio_value_usd: "1830.00", pnl_usd: "0.00" },
      { captured_at: "2026-03-20T00:00:00Z", portfolio_value_usd: "1850.00", pnl_usd: "20.00" },
      { captured_at: "2026-03-21T00:00:00Z", portfolio_value_usd: "1872.00", pnl_usd: "42.00" },
      { captured_at: "2026-03-22T00:00:00Z", portfolio_value_usd: "1905.00", pnl_usd: "75.00" },
      { captured_at: "2026-03-23T00:00:00Z", portfolio_value_usd: "1975.00", pnl_usd: "145.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "190.00" },
    ],
  },
  "90D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "90D",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2026-02-24T00:00:00Z", portfolio_value_usd: "1685.00", pnl_usd: "-45.00" },
      { captured_at: "2026-03-03T00:00:00Z", portfolio_value_usd: "1730.00", pnl_usd: "0.00" },
      { captured_at: "2026-03-10T00:00:00Z", portfolio_value_usd: "1782.00", pnl_usd: "52.00" },
      { captured_at: "2026-03-17T00:00:00Z", portfolio_value_usd: "1895.00", pnl_usd: "165.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "290.00" },
    ],
  },
  "252D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "252D",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2025-09-24T00:00:00Z", portfolio_value_usd: "1320.00", pnl_usd: "-120.00" },
      { captured_at: "2025-12-24T00:00:00Z", portfolio_value_usd: "1505.00", pnl_usd: "65.00" },
      { captured_at: "2026-01-24T00:00:00Z", portfolio_value_usd: "1620.00", pnl_usd: "180.00" },
      { captured_at: "2026-02-24T00:00:00Z", portfolio_value_usd: "1760.00", pnl_usd: "320.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "580.00" },
    ],
  },
  MAX: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "MAX",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2024-03-24T00:00:00Z", portfolio_value_usd: "940.00", pnl_usd: "-90.00" },
      { captured_at: "2024-09-24T00:00:00Z", portfolio_value_usd: "1110.00", pnl_usd: "80.00" },
      { captured_at: "2025-03-24T00:00:00Z", portfolio_value_usd: "1385.00", pnl_usd: "355.00" },
      { captured_at: "2025-09-24T00:00:00Z", portfolio_value_usd: "1575.00", pnl_usd: "545.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "990.00" },
    ],
  },
};

const contributionPayloadByPeriod = {
  "30D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "30D",
    rows: [
      { instrument_symbol: "PLTR", contribution_pnl_usd: "110.00", contribution_pct: "5.44" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "60.00", contribution_pct: "2.97" },
      { instrument_symbol: "SCHD", contribution_pnl_usd: "20.00", contribution_pct: "0.99" },
    ],
  },
  "90D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "90D",
    rows: [
      { instrument_symbol: "PLTR", contribution_pnl_usd: "150.00", contribution_pct: "7.43" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "105.00", contribution_pct: "5.20" },
      { instrument_symbol: "SCHD", contribution_pnl_usd: "35.00", contribution_pct: "1.73" },
    ],
  },
  "252D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "252D",
    rows: [
      { instrument_symbol: "PLTR", contribution_pnl_usd: "320.00", contribution_pct: "15.84" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "190.00", contribution_pct: "9.41" },
      { instrument_symbol: "SCHD", contribution_pnl_usd: "70.00", contribution_pct: "3.47" },
    ],
  },
  MAX: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "MAX",
    rows: [
      { instrument_symbol: "PLTR", contribution_pnl_usd: "540.00", contribution_pct: "26.73" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "330.00", contribution_pct: "16.34" },
      { instrument_symbol: "SCHD", contribution_pnl_usd: "120.00", contribution_pct: "5.94" },
    ],
  },
};

const riskPayloadByWindowDays = {
  30: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    window_days: 30,
    metrics: [
      {
        estimator_id: "annualized_volatility",
        value: "0.1625",
        window_days: 30,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "percent",
        interpretation_band: "favorable",
        timeline_series_id: "rolling_volatility",
      },
      {
        estimator_id: "max_drawdown",
        value: "-0.0810",
        window_days: 30,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "percent",
        interpretation_band: "favorable",
        timeline_series_id: "drawdown",
      },
      {
        estimator_id: "beta",
        value: "1.0420",
        window_days: 30,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "ratio",
        interpretation_band: "caution",
        timeline_series_id: "rolling_beta",
      },
    ],
    timeline_context: {
      available: true,
      scope: "portfolio",
      instrument_symbol: null,
      period: "30D",
    },
    guardrails: {
      mixed_units: true,
      unit_groups: ["percent", "ratio"],
      guidance: "Render grouped charts by unit to preserve interpretation fidelity.",
    },
  },
  90: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    window_days: 90,
    metrics: [
      {
        estimator_id: "annualized_volatility",
        value: "0.1740",
        window_days: 90,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "percent",
        interpretation_band: "caution",
        timeline_series_id: "rolling_volatility",
      },
      {
        estimator_id: "max_drawdown",
        value: "-0.1245",
        window_days: 90,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "percent",
        interpretation_band: "caution",
        timeline_series_id: "drawdown",
      },
      {
        estimator_id: "beta",
        value: "1.0180",
        window_days: 90,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "ratio",
        interpretation_band: "favorable",
        timeline_series_id: "rolling_beta",
      },
    ],
    timeline_context: {
      available: true,
      scope: "portfolio",
      instrument_symbol: null,
      period: "90D",
    },
    guardrails: {
      mixed_units: true,
      unit_groups: ["percent", "ratio"],
      guidance: "Render grouped charts by unit to preserve interpretation fidelity.",
    },
  },
  252: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    window_days: 252,
    metrics: [
      {
        estimator_id: "annualized_volatility",
        value: "0.1890",
        window_days: 252,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "percent",
        interpretation_band: "caution",
        timeline_series_id: "rolling_volatility",
      },
      {
        estimator_id: "max_drawdown",
        value: "-0.2015",
        window_days: 252,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "percent",
        interpretation_band: "elevated_risk",
        timeline_series_id: "drawdown",
      },
      {
        estimator_id: "beta",
        value: "0.9950",
        window_days: 252,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
        unit: "ratio",
        interpretation_band: "favorable",
        timeline_series_id: "rolling_beta",
      },
    ],
    timeline_context: {
      available: true,
      scope: "portfolio",
      instrument_symbol: null,
      period: "252D",
    },
    guardrails: {
      mixed_units: true,
      unit_groups: ["percent", "ratio"],
      guidance: "Render grouped charts by unit to preserve interpretation fidelity.",
    },
  },
};

const riskEvolutionPayloadByPeriod = {
  "30D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    scope: "portfolio",
    instrument_symbol: null,
    period: "30D",
    rolling_window_days: 30,
    methodology: {
      drawdown_method: "rolling peak-to-trough from cumulative simple-return path",
      rolling_volatility_method: "30-day rolling stdev annualized by sqrt(252)",
      rolling_beta_method: "30-day rolling covariance to benchmark / benchmark variance",
    },
    drawdown_path_points: [
      { captured_at: "2026-03-19T00:00:00Z", drawdown: "-0.0120" },
      { captured_at: "2026-03-20T00:00:00Z", drawdown: "-0.0180" },
      { captured_at: "2026-03-21T00:00:00Z", drawdown: "-0.0090" },
      { captured_at: "2026-03-22T00:00:00Z", drawdown: "-0.0150" },
      { captured_at: "2026-03-23T00:00:00Z", drawdown: "-0.0060" },
      { captured_at: "2026-03-24T00:00:00Z", drawdown: "0.0000" },
    ],
    rolling_points: [
      { captured_at: "2026-03-19T00:00:00Z", volatility_annualized: "0.1550", beta: "1.0300" },
      { captured_at: "2026-03-20T00:00:00Z", volatility_annualized: "0.1580", beta: "1.0360" },
      { captured_at: "2026-03-21T00:00:00Z", volatility_annualized: "0.1600", beta: "1.0400" },
      { captured_at: "2026-03-22T00:00:00Z", volatility_annualized: "0.1610", beta: "1.0410" },
      { captured_at: "2026-03-23T00:00:00Z", volatility_annualized: "0.1620", beta: "1.0420" },
      { captured_at: "2026-03-24T00:00:00Z", volatility_annualized: "0.1625", beta: "1.0420" },
    ],
  },
  "90D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    scope: "portfolio",
    instrument_symbol: null,
    period: "90D",
    rolling_window_days: 90,
    methodology: {
      drawdown_method: "rolling peak-to-trough from cumulative simple-return path",
      rolling_volatility_method: "90-day rolling stdev annualized by sqrt(252)",
      rolling_beta_method: "90-day rolling covariance to benchmark / benchmark variance",
    },
    drawdown_path_points: [
      { captured_at: "2026-02-24T00:00:00Z", drawdown: "-0.0580" },
      { captured_at: "2026-03-03T00:00:00Z", drawdown: "-0.0430" },
      { captured_at: "2026-03-10T00:00:00Z", drawdown: "-0.0360" },
      { captured_at: "2026-03-17T00:00:00Z", drawdown: "-0.0240" },
      { captured_at: "2026-03-24T00:00:00Z", drawdown: "-0.0100" },
    ],
    rolling_points: [
      { captured_at: "2026-02-24T00:00:00Z", volatility_annualized: "0.1700", beta: "1.0100" },
      { captured_at: "2026-03-03T00:00:00Z", volatility_annualized: "0.1710", beta: "1.0120" },
      { captured_at: "2026-03-10T00:00:00Z", volatility_annualized: "0.1725", beta: "1.0140" },
      { captured_at: "2026-03-17T00:00:00Z", volatility_annualized: "0.1735", beta: "1.0160" },
      { captured_at: "2026-03-24T00:00:00Z", volatility_annualized: "0.1740", beta: "1.0180" },
    ],
  },
  "252D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    scope: "portfolio",
    instrument_symbol: null,
    period: "252D",
    rolling_window_days: 252,
    methodology: {
      drawdown_method: "rolling peak-to-trough from cumulative simple-return path",
      rolling_volatility_method: "252-day rolling stdev annualized by sqrt(252)",
      rolling_beta_method: "252-day rolling covariance to benchmark / benchmark variance",
    },
    drawdown_path_points: [
      { captured_at: "2025-09-24T00:00:00Z", drawdown: "-0.2015" },
      { captured_at: "2025-12-24T00:00:00Z", drawdown: "-0.1320" },
      { captured_at: "2026-01-24T00:00:00Z", drawdown: "-0.0980" },
      { captured_at: "2026-02-24T00:00:00Z", drawdown: "-0.0700" },
      { captured_at: "2026-03-24T00:00:00Z", drawdown: "-0.0400" },
    ],
    rolling_points: [
      { captured_at: "2025-09-24T00:00:00Z", volatility_annualized: "0.1920", beta: "1.0040" },
      { captured_at: "2025-12-24T00:00:00Z", volatility_annualized: "0.1910", beta: "1.0010" },
      { captured_at: "2026-01-24T00:00:00Z", volatility_annualized: "0.1900", beta: "0.9990" },
      { captured_at: "2026-02-24T00:00:00Z", volatility_annualized: "0.1895", beta: "0.9970" },
      { captured_at: "2026-03-24T00:00:00Z", volatility_annualized: "0.1890", beta: "0.9950" },
    ],
  },
};

const returnDistributionPayloadByPeriod = {
  "30D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    scope: "portfolio",
    instrument_symbol: null,
    period: "30D",
    sample_size: 30,
    bucket_policy: {
      method: "equal_width",
      bin_count: 12,
      min_return: "-0.0350",
      max_return: "0.0410",
    },
    buckets: [
      { bucket_index: 0, lower_bound: "-0.0350", upper_bound: "-0.0287", count: 1, frequency: "0.0333" },
      { bucket_index: 1, lower_bound: "-0.0287", upper_bound: "-0.0223", count: 1, frequency: "0.0333" },
      { bucket_index: 2, lower_bound: "-0.0223", upper_bound: "-0.0160", count: 2, frequency: "0.0667" },
      { bucket_index: 3, lower_bound: "-0.0160", upper_bound: "-0.0097", count: 3, frequency: "0.1000" },
      { bucket_index: 4, lower_bound: "-0.0097", upper_bound: "-0.0033", count: 4, frequency: "0.1333" },
      { bucket_index: 5, lower_bound: "-0.0033", upper_bound: "0.0030", count: 5, frequency: "0.1667" },
      { bucket_index: 6, lower_bound: "0.0030", upper_bound: "0.0093", count: 4, frequency: "0.1333" },
      { bucket_index: 7, lower_bound: "0.0093", upper_bound: "0.0157", count: 4, frequency: "0.1333" },
      { bucket_index: 8, lower_bound: "0.0157", upper_bound: "0.0220", count: 3, frequency: "0.1000" },
      { bucket_index: 9, lower_bound: "0.0220", upper_bound: "0.0283", count: 2, frequency: "0.0667" },
      { bucket_index: 10, lower_bound: "0.0283", upper_bound: "0.0347", count: 1, frequency: "0.0333" },
      { bucket_index: 11, lower_bound: "0.0347", upper_bound: "0.0410", count: 0, frequency: "0.0000" },
    ],
  },
  "90D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    scope: "portfolio",
    instrument_symbol: null,
    period: "90D",
    sample_size: 90,
    bucket_policy: {
      method: "equal_width",
      bin_count: 12,
      min_return: "-0.0520",
      max_return: "0.0580",
    },
    buckets: [
      { bucket_index: 0, lower_bound: "-0.0520", upper_bound: "-0.0428", count: 2, frequency: "0.0222" },
      { bucket_index: 1, lower_bound: "-0.0428", upper_bound: "-0.0337", count: 4, frequency: "0.0444" },
      { bucket_index: 2, lower_bound: "-0.0337", upper_bound: "-0.0245", count: 6, frequency: "0.0667" },
      { bucket_index: 3, lower_bound: "-0.0245", upper_bound: "-0.0153", count: 8, frequency: "0.0889" },
      { bucket_index: 4, lower_bound: "-0.0153", upper_bound: "-0.0062", count: 11, frequency: "0.1222" },
      { bucket_index: 5, lower_bound: "-0.0062", upper_bound: "0.0030", count: 14, frequency: "0.1556" },
      { bucket_index: 6, lower_bound: "0.0030", upper_bound: "0.0122", count: 14, frequency: "0.1556" },
      { bucket_index: 7, lower_bound: "0.0122", upper_bound: "0.0213", count: 11, frequency: "0.1222" },
      { bucket_index: 8, lower_bound: "0.0213", upper_bound: "0.0305", count: 8, frequency: "0.0889" },
      { bucket_index: 9, lower_bound: "0.0305", upper_bound: "0.0397", count: 6, frequency: "0.0667" },
      { bucket_index: 10, lower_bound: "0.0397", upper_bound: "0.0488", count: 4, frequency: "0.0444" },
      { bucket_index: 11, lower_bound: "0.0488", upper_bound: "0.0580", count: 2, frequency: "0.0222" },
    ],
  },
  "252D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    scope: "portfolio",
    instrument_symbol: null,
    period: "252D",
    sample_size: 252,
    bucket_policy: {
      method: "equal_width",
      bin_count: 12,
      min_return: "-0.0900",
      max_return: "0.0850",
    },
    buckets: [
      { bucket_index: 0, lower_bound: "-0.0900", upper_bound: "-0.0754", count: 4, frequency: "0.0159" },
      { bucket_index: 1, lower_bound: "-0.0754", upper_bound: "-0.0608", count: 9, frequency: "0.0357" },
      { bucket_index: 2, lower_bound: "-0.0608", upper_bound: "-0.0463", count: 15, frequency: "0.0595" },
      { bucket_index: 3, lower_bound: "-0.0463", upper_bound: "-0.0317", count: 24, frequency: "0.0952" },
      { bucket_index: 4, lower_bound: "-0.0317", upper_bound: "-0.0171", count: 33, frequency: "0.1310" },
      { bucket_index: 5, lower_bound: "-0.0171", upper_bound: "-0.0025", count: 41, frequency: "0.1627" },
      { bucket_index: 6, lower_bound: "-0.0025", upper_bound: "0.0121", count: 43, frequency: "0.1706" },
      { bucket_index: 7, lower_bound: "0.0121", upper_bound: "0.0267", count: 33, frequency: "0.1310" },
      { bucket_index: 8, lower_bound: "0.0267", upper_bound: "0.0413", count: 24, frequency: "0.0952" },
      { bucket_index: 9, lower_bound: "0.0413", upper_bound: "0.0558", count: 15, frequency: "0.0595" },
      { bucket_index: 10, lower_bound: "0.0558", upper_bound: "0.0704", count: 7, frequency: "0.0278" },
      { bucket_index: 11, lower_bound: "0.0704", upper_bound: "0.0850", count: 4, frequency: "0.0159" },
    ],
  },
};

const mimeByExtension = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

function formatIsoDateForFile(value) {
  return value.replaceAll(":", "-");
}

function resolveListenPort() {
  const rawPort = process.env.CWV_PORT;
  if (!rawPort) {
    return DEFAULT_LISTEN_PORT;
  }

  const port = Number.parseInt(rawPort, 10);
  if (Number.isNaN(port) || port < 0 || port > 65535) {
    throw new Error(
      `Invalid CWV_PORT value "${rawPort}". Use an integer between 0 and 65535.`,
    );
  }

  return port;
}

function resolveScreenshotSettleDelayMs() {
  const rawDelay = process.env.FRONTEND_EVIDENCE_SCREENSHOT_SETTLE_MS;
  if (!rawDelay) {
    return DEFAULT_SCREENSHOT_SETTLE_DELAY_MS;
  }

  const delayMs = Number.parseInt(rawDelay, 10);
  if (Number.isNaN(delayMs) || delayMs < 0) {
    throw new Error(
      `Invalid FRONTEND_EVIDENCE_SCREENSHOT_SETTLE_MS value "${rawDelay}". Use an integer >= 0.`,
    );
  }
  return delayMs;
}

async function assertBuildArtifactsExist() {
  try {
    await readFile(indexHtmlPath);
  } catch (error) {
    throw new Error(
      "Missing frontend build artifacts at frontend/dist/index.html. Run `npm run build` before `npm run frontend:evidence`.",
      { cause: error },
    );
  }
}

async function closeServer(server) {
  if (!server.listening) {
    return;
  }

  await new Promise((resolve, reject) => {
    server.close((error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve(undefined);
    });
  });
}

async function listenServer(server, port) {
  await new Promise((resolve, reject) => {
    const onError = (error) => {
      server.off("listening", onListening);
      reject(error);
    };
    const onListening = () => {
      server.off("error", onError);
      resolve(undefined);
    };

    server.once("error", onError);
    server.once("listening", onListening);
    server.listen(port, SERVER_HOST);
  });

  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("Unable to resolve frontend evidence server address.");
  }

  return `http://${SERVER_HOST}:${address.port}`;
}

async function serveRequest(request, response) {
  const requestUrl = new URL(request.url || "/", "http://127.0.0.1");
  const pathname = requestUrl.pathname;

  if (pathname === "/api/portfolio/summary") {
    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(summaryPayload));
    return;
  }

  if (pathname === "/api/portfolio/time-series") {
    const requestedPeriod = (requestUrl.searchParams.get("period") || "30D").toUpperCase();
    if (!supportedChartPeriods.includes(requestedPeriod)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported chart period '${requestedPeriod}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    const selectedPayload = timeSeriesPayloadByPeriod[requestedPeriod];
    response.end(
      JSON.stringify({
        ...selectedPayload,
        points: selectedPayload.points.map((point) => ({
          benchmark_nasdaq100_value_usd: point.benchmark_nasdaq100_value_usd ?? null,
          benchmark_sp500_value_usd: point.benchmark_sp500_value_usd ?? null,
          ...point,
        })),
      }),
    );
    return;
  }

  if (pathname === "/api/portfolio/contribution") {
    const requestedPeriod = (requestUrl.searchParams.get("period") || "30D").toUpperCase();
    if (!supportedChartPeriods.includes(requestedPeriod)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported chart period '${requestedPeriod}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(contributionPayloadByPeriod[requestedPeriod]));
    return;
  }

  if (pathname === "/api/portfolio/risk-estimators") {
    const requestedWindow = Number.parseInt(
      requestUrl.searchParams.get("window_days") || "252",
      10,
    );
    if (!supportedRiskWindows.includes(requestedWindow)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({ detail: `Unsupported risk estimator window '${requestedWindow}'.` }),
      );
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(riskPayloadByWindowDays[requestedWindow]));
    return;
  }

  if (pathname === "/api/portfolio/risk-evolution") {
    const requestedPeriod = (requestUrl.searchParams.get("period") || "252D").toUpperCase();
    if (!supportedChartPeriods.includes(requestedPeriod)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported chart period '${requestedPeriod}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(riskEvolutionPayloadByPeriod[requestedPeriod]));
    return;
  }

  if (pathname === "/api/portfolio/return-distribution") {
    const requestedPeriod = (requestUrl.searchParams.get("period") || "252D").toUpperCase();
    if (!supportedChartPeriods.includes(requestedPeriod)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported chart period '${requestedPeriod}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(returnDistributionPayloadByPeriod[requestedPeriod]));
    return;
  }

  if (pathname === "/api/portfolio/health-synthesis") {
    const requestedPeriod = (requestUrl.searchParams.get("period") || "90D").toUpperCase();
    const requestedScope = (requestUrl.searchParams.get("scope") || "portfolio").toLowerCase();
    const requestedProfilePosture = (
      requestUrl.searchParams.get("profile_posture") || "balanced"
    ).toLowerCase();
    const requestedInstrumentSymbol = (
      requestUrl.searchParams.get("instrument_symbol") || "VOO"
    )
      .trim()
      .toUpperCase();

    if (!supportedChartPeriods.includes(requestedPeriod)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported chart period '${requestedPeriod}'.` }));
      return;
    }
    if (requestedScope !== "portfolio" && requestedScope !== "instrument_symbol") {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported health scope '${requestedScope}'.` }));
      return;
    }
    if (!supportedHealthProfilePostures.includes(requestedProfilePosture)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({ detail: `Unsupported profile posture '${requestedProfilePosture}'.` }),
      );
      return;
    }
    if (requestedScope === "instrument_symbol" && requestedInstrumentSymbol.length === 0) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: "Instrument symbol is required for health scope." }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(
      JSON.stringify(
        buildHealthSynthesisPayload({
          period: requestedPeriod,
          scope: requestedScope,
          profilePosture: requestedProfilePosture,
          instrumentSymbol: requestedInstrumentSymbol,
        }),
      ),
    );
    return;
  }

  if (pathname === "/api/portfolio/hierarchy") {
    const requestedGroup = (requestUrl.searchParams.get("group_by") || "sector").toLowerCase();
    if (!supportedHierarchyGroups.includes(requestedGroup)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported hierarchy group '${requestedGroup}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    const payload =
      requestedGroup === "symbol"
        ? {
            ...hierarchyPayloadByGroup.symbol,
            groups: hierarchyPayloadByGroup.sector.groups.flatMap((group) =>
              group.assets.map((asset) => ({
                group_key: asset.instrument_symbol,
                group_label: asset.instrument_symbol,
                asset_count: 1,
                total_market_value_usd: asset.market_value_usd,
                total_profit_loss_usd: asset.profit_loss_usd,
                total_change_pct: asset.change_pct,
                assets: [asset],
              })),
            ),
          }
        : hierarchyPayloadByGroup.sector;
    response.end(JSON.stringify(payload));
    return;
  }

  if (pathname.startsWith("/api/portfolio/lots/")) {
    const symbol = decodeURIComponent(pathname.slice("/api/portfolio/lots/".length))
      .trim()
      .toUpperCase();

    if (symbol === "VOO") {
      response.writeHead(200, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify(lotDetailPayload));
      return;
    }

    if (symbol === "ERR500") {
      response.writeHead(500, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({
          detail: "The portfolio lot-detail API is temporarily unavailable.",
        }),
      );
      return;
    }

    response.writeHead(404, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(
      JSON.stringify({
        detail: `Instrument ${symbol} was not found in the portfolio ledger.`,
      }),
    );
    return;
  }

  if (pathname === "/api/portfolio/transactions") {
    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(transactionsPayload));
    return;
  }

  let filePath = path.join(distRoot, pathname);
  if (pathname === "/" || pathname === "") {
    filePath = indexHtmlPath;
  }

  try {
    const fileBuffer = await readFile(filePath);
    const extension = path.extname(filePath);
    response.writeHead(200, {
      "Content-Type": mimeByExtension[extension] || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    response.end(fileBuffer);
    return;
  } catch {
    // Continue to SPA fallback.
  }

  const spaIndex = await readFile(indexHtmlPath);
  response.writeHead(200, {
    "Content-Type": mimeByExtension[".html"],
    "Cache-Control": "no-store",
  });
  response.end(spaIndex);
}

function toPosixRelativeRepoPath(absolutePath) {
  const relativePath = path.relative(repoRoot, absolutePath);
  return relativePath.split(path.sep).join("/");
}

async function captureScreenshot({
  browser,
  baseUrl,
  routePath,
  screenshotPath,
  viewport,
  waitForSelector,
  theme,
  fullPage,
  screenshotSettleDelayMs,
}) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();

  if (theme) {
    await page.addInitScript(
      ({ storageKey, storageTheme }) => {
        window.localStorage.setItem(storageKey, storageTheme);
        document.documentElement.dataset.theme = storageTheme;
      },
      {
        storageKey: THEME_STORAGE_KEY,
        storageTheme: theme,
      },
    );
  }

  await page.goto(`${baseUrl}${routePath}`, { waitUntil: "networkidle" });
  if (waitForSelector) {
    await page.waitForSelector(waitForSelector, { state: "visible" });
  }
  await page.waitForTimeout(screenshotSettleDelayMs);
  await page.screenshot({
    path: screenshotPath,
    fullPage,
  });

  await context.close();
}

async function collectRouteAccessibilityAudit(page, routeLabel) {
  const domChecks = await page.evaluate(() => {
    const normalize = (value) => value.replace(/\s+/g, " ").trim();

    const getAriaLabelledByText = (element) => {
      const labelledBy = element.getAttribute("aria-labelledby");
      if (!labelledBy) {
        return "";
      }

      return labelledBy
        .split(/\s+/)
        .map((id) => document.getElementById(id))
        .filter(Boolean)
        .map((node) => normalize(node.textContent || ""))
        .filter(Boolean)
        .join(" ");
    };

    const resolveAccessibleName = (element) => {
      const ariaLabel = normalize(element.getAttribute("aria-label") || "");
      if (ariaLabel) {
        return ariaLabel;
      }

      const labelledByText = getAriaLabelledByText(element);
      if (labelledByText) {
        return labelledByText;
      }

      return normalize(element.textContent || "");
    };

    const isFocusable = (element) => {
      if (!(element instanceof HTMLElement)) {
        return false;
      }

      if (element.tabIndex >= 0) {
        return true;
      }

      const tagName = element.tagName.toLowerCase();
      if (tagName === "a") {
        return element.hasAttribute("href");
      }

      if (
        tagName === "button" ||
        tagName === "input" ||
        tagName === "select" ||
        tagName === "textarea"
      ) {
        return !element.hasAttribute("disabled");
      }

      return false;
    };

    const describeElement = (element) => {
      if (!(element instanceof HTMLElement)) {
        return "(unknown)";
      }

      const tagName = element.tagName.toLowerCase();
      const id = element.id ? `#${element.id}` : "";
      const className = element.className
        ? `.${String(element.className).trim().replace(/\s+/g, ".")}`
        : "";
      return `${tagName}${id}${className}`;
    };

    const unnamedButtons = Array.from(document.querySelectorAll("button"))
      .filter((element) => resolveAccessibleName(element).length === 0)
      .map((element) => describeElement(element));

    const unnamedLinks = Array.from(document.querySelectorAll("a"))
      .filter((element) => resolveAccessibleName(element).length === 0)
      .map((element) => describeElement(element));

    const ariaHiddenFocusable = Array.from(document.querySelectorAll("[aria-hidden='true']"))
      .filter((element) => isFocusable(element))
      .map((element) => describeElement(element));

    const interactiveRows = Array.from(
      document.querySelectorAll("tr.data-table__row--interactive"),
    ).map((row) => ({
      label: row.getAttribute("aria-label"),
      role: row.getAttribute("role"),
      tabIndex: row.getAttribute("tabindex"),
      keyShortcuts: row.getAttribute("aria-keyshortcuts"),
    }));

    const statusBanners = Array.from(document.querySelectorAll("section.status-banner")).map(
      (banner) => ({
        role: banner.getAttribute("role"),
        title: normalize(
          banner.querySelector(".status-banner__title")?.textContent || "",
        ),
      }),
    );

    const implicitRoleByTag = {
      a: "link",
      button: "button",
      h1: "heading",
      h2: "heading",
      h3: "heading",
      h4: "heading",
      h5: "heading",
      h6: "heading",
      main: "main",
      table: "table",
      td: "cell",
      th: "columnheader",
      tr: "row",
    };

    const roleCounts = {};
    for (const element of document.querySelectorAll("*")) {
      if (!(element instanceof HTMLElement)) {
        continue;
      }

      const explicitRole = element.getAttribute("role");
      const implicitRole = implicitRoleByTag[element.tagName.toLowerCase()];
      const resolvedRole = explicitRole || implicitRole;
      if (!resolvedRole) {
        continue;
      }

      roleCounts[resolvedRole] = (roleCounts[resolvedRole] || 0) + 1;
    }

    return {
      h1Count: document.querySelectorAll("h1").length,
      mainCount: document.querySelectorAll("main").length,
      unnamedButtons,
      unnamedLinks,
      ariaHiddenFocusable,
      interactiveRows,
      statusBanners,
      roleCounts,
    };
  });

  const findings = [];
  if (domChecks.mainCount !== 1) {
    findings.push(`Expected exactly one main landmark, found ${domChecks.mainCount}.`);
  }
  if (domChecks.h1Count !== 1) {
    findings.push(`Expected exactly one h1, found ${domChecks.h1Count}.`);
  }
  if (domChecks.unnamedButtons.length > 0) {
    findings.push(`Unnamed buttons found: ${domChecks.unnamedButtons.join(", ")}.`);
  }
  if (domChecks.unnamedLinks.length > 0) {
    findings.push(`Unnamed links found: ${domChecks.unnamedLinks.join(", ")}.`);
  }
  if (domChecks.ariaHiddenFocusable.length > 0) {
    findings.push(
      `Focusable aria-hidden elements found: ${domChecks.ariaHiddenFocusable.join(", ")}.`,
    );
  }

  if (routeLabel === "/portfolio" && domChecks.interactiveRows.length === 0) {
    findings.push("Expected at least one keyboard-focusable summary row.");
  }

  if (routeLabel === "/portfolio/UNKNOWN") {
    const hasStatus = domChecks.statusBanners.some((banner) => banner.role === "status");
    if (!hasStatus) {
      findings.push("Expected 404 route to expose a status role banner.");
    }
  }

  if (routeLabel === "/portfolio/ERR500") {
    const hasAlert = domChecks.statusBanners.some((banner) => banner.role === "alert");
    if (!hasAlert) {
      findings.push("Expected 500 route to expose an alert role banner.");
    }
  }

  return {
    route: routeLabel,
    passed: findings.length === 0,
    findings,
    domChecks,
    roleCounts: domChecks.roleCounts,
  };
}

async function describeActiveElement(page) {
  return page.evaluate(() => {
    const element = document.activeElement;
    if (!element || !(element instanceof HTMLElement)) {
      return {
        selector: "(none)",
        role: null,
        label: null,
      };
    }

    const normalize = (value) => value.replace(/\s+/g, " ").trim();
    const ariaLabel = normalize(element.getAttribute("aria-label") || "");
    const textLabel = normalize(element.textContent || "");
    const label = ariaLabel || textLabel || null;
    const tagName = element.tagName.toLowerCase();
    const className = String(element.className || "").trim().replace(/\s+/g, ".");
    const selector = className ? `${tagName}.${className}` : tagName;

    return {
      selector,
      role: element.getAttribute("role"),
      label,
      className: String(element.className || ""),
    };
  });
}

async function tabUntil(page, predicate, maxTabs = 32) {
  const sequence = [];

  for (let index = 0; index < maxTabs; index += 1) {
    await page.keyboard.press("Tab");
    const activeElement = await describeActiveElement(page);
    sequence.push(activeElement);
    if (predicate(activeElement)) {
      return {
        found: true,
        sequence,
      };
    }
  }

  return {
    found: false,
    sequence,
  };
}

async function runKeyboardWalkthrough(browser, baseUrl) {
  const context = await browser.newContext({
    viewport: {
      width: 1440,
      height: 900,
    },
  });
  const page = await context.newPage();

  const report = {
    summaryToRowTabSequence: [],
    firstInteractiveRowFound: false,
    enterOnRowNavigatesToLotDetail: false,
    lotDetailBackLinkFound: false,
    backLinkReturnsToSummary: false,
    notFoundRetryFound: false,
    notFoundBackLinkFound: false,
    serverErrorRetryFound: false,
    serverErrorBackLinkFound: false,
    workspaceAnalyticsTabFound: false,
    workspaceAnalyticsTabNavigates: false,
    workspaceRiskTabFound: false,
    workspaceRiskTabNavigates: false,
    workspaceTransactionsTabFound: false,
    workspaceTransactionsTabNavigates: false,
  };

  await page.goto(`${baseUrl}/portfolio`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=Portfolio command home");

  const rowSequence = await tabUntil(
    page,
    (activeElement) =>
      typeof activeElement.className === "string" &&
      activeElement.className.includes("data-table__row--interactive"),
  );
  report.summaryToRowTabSequence = rowSequence.sequence;
  report.firstInteractiveRowFound = rowSequence.found;

  if (rowSequence.found) {
    await Promise.all([
      page.waitForURL(new RegExp(`${baseUrl}/portfolio/VOO$`), { timeout: 4000 }),
      page.keyboard.press("Enter"),
    ]);
    report.enterOnRowNavigatesToLotDetail = true;
  }

  const lotBackLink = await tabUntil(
    page,
    (activeElement) =>
      typeof activeElement.label === "string" &&
      activeElement.label.includes("Back to summary"),
  );
  report.lotDetailBackLinkFound = lotBackLink.found;

  if (lotBackLink.found) {
    await Promise.all([
      page.waitForURL(new RegExp(`${baseUrl}/portfolio$`), { timeout: 4000 }),
      page.keyboard.press("Enter"),
    ]);
    report.backLinkReturnsToSummary = true;
  }

  await page.goto(`${baseUrl}/portfolio/UNKNOWN`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=Instrument not found");
  const notFoundRetry = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Retry request",
  );
  report.notFoundRetryFound = notFoundRetry.found;
  const notFoundBackLink = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Back to summary",
  );
  report.notFoundBackLinkFound = notFoundBackLink.found;

  await page.goto(`${baseUrl}/portfolio/ERR500`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=Lot detail unavailable");
  const serverErrorRetry = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Retry request",
  );
  report.serverErrorRetryFound = serverErrorRetry.found;
  const serverErrorBackLink = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Back to summary",
  );
  report.serverErrorBackLinkFound = serverErrorBackLink.found;

  await page.goto(`${baseUrl}/portfolio/home`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=Portfolio command home");

  const analyticsTab = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Analytics",
  );
  report.workspaceAnalyticsTabFound = analyticsTab.found;
  if (analyticsTab.found) {
    await Promise.all([
      page.waitForURL(new RegExp(`${baseUrl}/portfolio/analytics`), { timeout: 4000 }),
      page.keyboard.press("Enter"),
    ]);
    report.workspaceAnalyticsTabNavigates = true;
  }

  const riskTab = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Risk",
  );
  report.workspaceRiskTabFound = riskTab.found;
  if (riskTab.found) {
    await Promise.all([
      page.waitForURL(new RegExp(`${baseUrl}/portfolio/risk`), { timeout: 4000 }),
      page.keyboard.press("Enter"),
    ]);
    report.workspaceRiskTabNavigates = true;
  }

  const transactionsTab = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Transactions",
  );
  report.workspaceTransactionsTabFound = transactionsTab.found;
  if (transactionsTab.found) {
    await Promise.all([
      page.waitForURL(new RegExp(`${baseUrl}/portfolio/transactions`), { timeout: 4000 }),
      page.keyboard.press("Enter"),
    ]);
    report.workspaceTransactionsTabNavigates = true;
  }

  await context.close();
  return report;
}

function toPassFail(value) {
  return value ? "PASS" : "FAIL";
}

async function writeAccessibilityMarkdown({
  dateLabel,
  markdownPath,
  accessibilityAudits,
}) {
  const routeRows = accessibilityAudits
    .map(
      (audit) =>
        `| \`${audit.route}\` | \`${toPassFail(audit.passed)}\` | ${
          audit.findings.length > 0 ? audit.findings.join(" ") : "No blocking findings."
        } |`,
    )
    .join("\n");

  const content = `# Frontend Accessibility Scan - ${dateLabel}

## Method

- Tooling: Playwright Chromium + DOM semantic checks + explicit role inventory.
- Scope: \`/portfolio\`, \`/portfolio/VOO\`, \`/portfolio/UNKNOWN\`, \`/portfolio/ERR500\`, \`/portfolio/home\`, \`/portfolio/analytics\`, \`/portfolio/risk\`, \`/portfolio/transactions\`.
- Focus: landmark/heading structure, interactive naming, keyboard-row semantics, workspace navigation tabs, and error-banner role mapping.

## Route Results

| Route | Verdict | Findings |
| --- | --- | --- |
${routeRows}

## WCAG Mapping Notes

- \`1.3.1 Info and Relationships\`: verified main landmark and heading structure per route.
- \`2.4.7 Focus Visible\`: paired with keyboard walkthrough evidence in \`docs/evidence/frontend/keyboard-walkthrough-${dateLabel}.md\`.
- \`3.3.1 Error Identification\`: verified dedicated \`status\` (\`404\`) and \`alert\` (\`500\`) banners.
- \`4.1.2 Name, Role, Value\`: verified button/link naming, interactive summary row semantics, and workspace-tab semantics.

## Raw Evidence

- JSON report: \`docs/evidence/frontend/accessibility-scan-${dateLabel}.json\`
`;

  await writeFile(markdownPath, content);
}

async function writeKeyboardMarkdown({
  dateLabel,
  markdownPath,
  keyboardReport,
}) {
  const firstSteps = keyboardReport.summaryToRowTabSequence
    .slice(0, 8)
    .map((step, index) => `${index + 1}. ${step.selector} | role=${step.role || "n/a"} | label=${step.label || "n/a"}`)
    .join("\n");

  const content = `# Frontend Keyboard Walkthrough - ${dateLabel}

## Scope

- Routes: \`/portfolio\`, \`/portfolio/VOO\`, \`/portfolio/UNKNOWN\`, \`/portfolio/ERR500\`
- Workspace routes: \`/portfolio/home\`, \`/portfolio/analytics\`, \`/portfolio/risk\`, \`/portfolio/transactions\`
- Viewport: desktop \`1440x900\`
- Source: automated tab-sequence and keyboard activation checks via Playwright

## Results

- First interactive summary row found by keyboard tabbing: \`${toPassFail(keyboardReport.firstInteractiveRowFound)}\`
- Enter on focused summary row navigates to lot detail: \`${toPassFail(keyboardReport.enterOnRowNavigatesToLotDetail)}\`
- Lot-detail back link is keyboard-reachable: \`${toPassFail(keyboardReport.lotDetailBackLinkFound)}\`
- Keyboard activation on back link returns to summary: \`${toPassFail(keyboardReport.backLinkReturnsToSummary)}\`
- 404 screen retry button is keyboard-reachable: \`${toPassFail(keyboardReport.notFoundRetryFound)}\`
- 404 screen back link is keyboard-reachable: \`${toPassFail(keyboardReport.notFoundBackLinkFound)}\`
- 500 screen retry button is keyboard-reachable: \`${toPassFail(keyboardReport.serverErrorRetryFound)}\`
- 500 screen back link is keyboard-reachable: \`${toPassFail(keyboardReport.serverErrorBackLinkFound)}\`
- Workspace analytics tab is keyboard-reachable: \`${toPassFail(keyboardReport.workspaceAnalyticsTabFound)}\`
- Enter on analytics tab navigates to analytics route: \`${toPassFail(keyboardReport.workspaceAnalyticsTabNavigates)}\`
- Workspace risk tab is keyboard-reachable: \`${toPassFail(keyboardReport.workspaceRiskTabFound)}\`
- Enter on risk tab navigates to risk route: \`${toPassFail(keyboardReport.workspaceRiskTabNavigates)}\`
- Workspace transactions tab is keyboard-reachable: \`${toPassFail(keyboardReport.workspaceTransactionsTabFound)}\`
- Enter on transactions tab navigates to transactions route: \`${toPassFail(keyboardReport.workspaceTransactionsTabNavigates)}\`

## Summary Tab Sequence (first 8 focus stops)

${firstSteps}

## Raw Evidence

- JSON report: \`docs/evidence/frontend/keyboard-walkthrough-${dateLabel}.json\`
`;

  await writeFile(markdownPath, content);
}

async function main() {
  await mkdir(reportRoot, { recursive: true });
  await assertBuildArtifactsExist();

  const now = new Date();
  const measuredAt = now.toISOString();
  const dateLabel = now.toISOString().slice(0, 10);
  const captureLabel = formatIsoDateForFile(measuredAt);
  const screenshotSettleDelayMs = resolveScreenshotSettleDelayMs();
  const screenshotRoot = path.join(reportRoot, `screenshots-${dateLabel}`);
  await mkdir(screenshotRoot, { recursive: true });

  const requestedPort = resolveListenPort();
  const server = http.createServer((request, response) => {
    void serveRequest(request, response).catch((error) => {
      response.writeHead(500, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({
          detail: "Frontend evidence fixture server failed to serve request.",
        }),
      );
      console.error(error);
    });
  });

  const baseUrl = await listenServer(server, requestedPort);
  let browser;
  try {
    browser = await chromium.launch({ headless: true });

    const screenshotSpecs = [
      {
        fileName: "desktop-summary-ledger-timestamp.png",
        routePath: "/portfolio",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Portfolio command home",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "desktop-summary-first-viewport.png",
        routePath: "/portfolio",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Portfolio command home",
        theme: "dark",
        fullPage: false,
      },
      {
        fileName: "desktop-summary-dark-theme.png",
        routePath: "/portfolio",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Portfolio command home",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "mobile-summary-responsive.png",
        routePath: "/portfolio",
        viewport: { width: 390, height: 844 },
        waitForSelector: "text=Portfolio command home",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "lot-detail-disposition-history.png",
        routePath: "/portfolio/VOO",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Disposition history",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "lot-detail-not-found-404.png",
        routePath: "/portfolio/UNKNOWN",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Instrument not found",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "lot-detail-server-error-500.png",
        routePath: "/portfolio/ERR500",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Lot detail unavailable",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "workspace-home.png",
        routePath: "/portfolio/home?period=30D",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Portfolio command home",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "workspace-analytics.png",
        routePath: "/portfolio/analytics?period=90D",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Performance and contribution analytics",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "workspace-risk.png",
        routePath: "/portfolio/risk?period=252D",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Bounded estimator workspace",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "workspace-transactions.png",
        routePath: "/portfolio/transactions",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Ledger event history",
        theme: "dark",
        fullPage: true,
      },
    ];

    for (const screenshotSpec of screenshotSpecs) {
      await captureScreenshot({
        browser,
        baseUrl,
        routePath: screenshotSpec.routePath,
        screenshotPath: path.join(screenshotRoot, screenshotSpec.fileName),
        viewport: screenshotSpec.viewport,
        waitForSelector: screenshotSpec.waitForSelector,
        theme: screenshotSpec.theme,
        fullPage: screenshotSpec.fullPage,
        screenshotSettleDelayMs,
      });
    }

    const accessibilityAudits = [];
    const accessibilityRoutes = [
      "/portfolio",
      "/portfolio/VOO",
      "/portfolio/UNKNOWN",
      "/portfolio/ERR500",
      "/portfolio/home?period=30D",
      "/portfolio/analytics?period=90D",
      "/portfolio/risk?period=252D",
      "/portfolio/transactions",
    ];
    const routeSelectorByPath = {
      "/portfolio": "text=Portfolio command home",
      "/portfolio/VOO": "text=Disposition history",
      "/portfolio/UNKNOWN": "text=Instrument not found",
      "/portfolio/ERR500": "text=Lot detail unavailable",
      "/portfolio/home?period=30D": "text=Portfolio command home",
      "/portfolio/analytics?period=90D": "text=Performance and contribution analytics",
      "/portfolio/risk?period=252D": "text=Bounded estimator workspace",
      "/portfolio/transactions": "text=Ledger event history",
    };
    for (const routePath of accessibilityRoutes) {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
      });
      const page = await context.newPage();
      await page.goto(`${baseUrl}${routePath}`, { waitUntil: "networkidle" });
      const waitSelector = routeSelectorByPath[routePath];
      if (waitSelector) {
        await page.waitForSelector(waitSelector);
      }
      accessibilityAudits.push(
        await collectRouteAccessibilityAudit(page, routePath),
      );
      await context.close();
    }

    const keyboardReport = await runKeyboardWalkthrough(browser, baseUrl);

    const accessibilityJsonPath = path.join(
      reportRoot,
      `accessibility-scan-${dateLabel}.json`,
    );
    const keyboardJsonPath = path.join(
      reportRoot,
      `keyboard-walkthrough-${dateLabel}.json`,
    );
    const accessibilityMarkdownPath = path.join(
      reportRoot,
      `accessibility-scan-${dateLabel}.md`,
    );
    const keyboardMarkdownPath = path.join(
      reportRoot,
      `keyboard-walkthrough-${dateLabel}.md`,
    );

    await writeFile(
      accessibilityJsonPath,
      `${JSON.stringify(
        {
          measuredAt,
          baseUrl,
          audits: accessibilityAudits,
        },
        null,
        2,
      )}\n`,
    );
    await writeFile(
      keyboardJsonPath,
      `${JSON.stringify(
        {
          measuredAt,
          baseUrl,
          keyboardReport,
        },
        null,
        2,
      )}\n`,
    );

    await writeAccessibilityMarkdown({
      dateLabel,
      markdownPath: accessibilityMarkdownPath,
      accessibilityAudits,
    });
    await writeKeyboardMarkdown({
      dateLabel,
      markdownPath: keyboardMarkdownPath,
      keyboardReport,
    });

    const screenshotEntries = [
      "desktop-summary-ledger-timestamp.png",
      "desktop-summary-first-viewport.png",
      "desktop-summary-dark-theme.png",
      "mobile-summary-responsive.png",
      "lot-detail-disposition-history.png",
      "lot-detail-not-found-404.png",
      "lot-detail-server-error-500.png",
      "workspace-home.png",
      "workspace-analytics.png",
      "workspace-risk.png",
      "workspace-transactions.png",
    ].map((fileName) =>
      toPosixRelativeRepoPath(path.join(screenshotRoot, fileName)),
    );

    console.log(
      JSON.stringify(
        {
          measuredAt,
          captureId: captureLabel,
          baseUrl,
          screenshots: screenshotEntries,
          accessibilityReport: toPosixRelativeRepoPath(accessibilityMarkdownPath),
          keyboardReport: toPosixRelativeRepoPath(keyboardMarkdownPath),
        },
        null,
        2,
      ),
    );
  } finally {
    if (browser) {
      await browser.close();
    }
    await closeServer(server);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
