export type ResearchMetricAvailability = "direct" | "derived" | "unavailable";

export type ResearchMetricAvailabilityEntry = {
  metricId: string;
  label: string;
  availability: ResearchMetricAvailability;
  reason: string;
};

export const RESEARCH_METRIC_AVAILABILITY: ResearchMetricAvailabilityEntry[] = [
  {
    metricId: "pe_ratio",
    label: "P/E",
    availability: "direct",
    reason: "yfinance screener field path available for supported symbols.",
  },
  {
    metricId: "peg_ratio",
    label: "PEG",
    availability: "direct",
    reason: "yfinance screener field `pegratio_5y` available for supported symbols.",
  },
  {
    metricId: "price_to_book",
    label: "P/B",
    availability: "direct",
    reason: "yfinance screener field `pricebookratio.quarterly` is directly extractable.",
  },
  {
    metricId: "return_on_equity",
    label: "ROE",
    availability: "direct",
    reason: "yfinance screener field `returnonequity.lasttwelvemonths` is directly extractable.",
  },
  {
    metricId: "return_on_assets",
    label: "ROA",
    availability: "direct",
    reason: "yfinance screener field `returnonassets.lasttwelvemonths` is directly extractable.",
  },
  {
    metricId: "debt_to_equity",
    label: "Debt-to-equity",
    availability: "direct",
    reason: "yfinance screener field `totaldebtequity.lasttwelvemonths` is directly extractable.",
  },
  {
    metricId: "current_ratio",
    label: "Current ratio",
    availability: "direct",
    reason: "yfinance screener field `currentratio.lasttwelvemonths` is directly extractable.",
  },
  {
    metricId: "rule_of_40",
    label: "Rule of 40",
    availability: "unavailable",
    reason: "research data pending: requires explicit custom contract.",
  },
  {
    metricId: "atr",
    label: "ATR",
    availability: "derived",
    reason: "deterministic derivation from OHLCV bars.",
  },
  {
    metricId: "implied_volatility",
    label: "Implied volatility",
    availability: "direct",
    reason: "direct option-chain `impliedVolatility` extraction is available when chain coverage exists.",
  },
  {
    metricId: "j5",
    label: "J5",
    availability: "unavailable",
    reason: "signal contract not connected.",
  },
  {
    metricId: "jr4",
    label: "JR4",
    availability: "unavailable",
    reason: "signal contract not connected.",
  },
  {
    metricId: "volume_profile",
    label: "Volume profile",
    availability: "unavailable",
    reason: "no native yfinance profile contract in baseline scope.",
  },
  {
    metricId: "iv_percentile",
    label: "Historical IV percentile",
    availability: "unavailable",
    reason: "no first-class yfinance percentile endpoint in baseline scope.",
  },
];
