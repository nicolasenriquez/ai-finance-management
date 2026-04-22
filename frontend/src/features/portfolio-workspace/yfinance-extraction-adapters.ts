export type YFinanceAdapterAvailability = "direct" | "derived" | "unavailable";

export type YFinanceValuationMetricId = "pe_ratio" | "peg_ratio" | "price_to_book";
export type YFinanceQualityMetricId =
  | "return_on_equity"
  | "return_on_assets"
  | "debt_to_equity"
  | "current_ratio";
export type YFinanceTechnicalMetricId =
  | "latest_close"
  | "latest_volume"
  | "corporate_actions_count"
  | "option_implied_volatility"
  | "atr_14";

export type YFinanceAdapterMetricId =
  | YFinanceValuationMetricId
  | YFinanceQualityMetricId
  | YFinanceTechnicalMetricId;

export type YFinanceAdapterRow = {
  metricId: YFinanceAdapterMetricId;
  label: string;
  availability: YFinanceAdapterAvailability;
  value: number | null;
  unit: "ratio" | "percent" | "price" | "count" | "volume";
  sourceField: string;
  reason: string;
  confidenceState: "direct" | "derived";
};

export type YFinanceScreenerField =
  | "peratio.lasttwelvemonths"
  | "pegratio_5y"
  | "pricebookratio.quarterly"
  | "returnonequity.lasttwelvemonths"
  | "returnonassets.lasttwelvemonths"
  | "totaldebtequity.lasttwelvemonths"
  | "currentratio.lasttwelvemonths";

export type YFinanceScreenerSnapshot = Partial<
  Record<YFinanceScreenerField, number | null | undefined>
>;

export type YFinanceOhlcvBar = {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type YFinanceCorporateAction = {
  type: "dividend" | "split" | "other";
  value: number;
};

export type YFinanceOptionContract = {
  impliedVolatility: number | null | undefined;
};

export type YFinanceTechnicalPayload = {
  bars: YFinanceOhlcvBar[];
  actions: YFinanceCorporateAction[];
  optionContracts: YFinanceOptionContract[];
};

type ValuationFieldDefinition = {
  metricId: YFinanceValuationMetricId;
  label: string;
  sourceField: YFinanceScreenerField;
};

type QualityFieldDefinition = {
  metricId: YFinanceQualityMetricId;
  label: string;
  sourceField: YFinanceScreenerField;
};

const VALUATION_FIELD_DEFINITIONS: ValuationFieldDefinition[] = [
  {
    metricId: "pe_ratio",
    label: "P/E",
    sourceField: "peratio.lasttwelvemonths",
  },
  {
    metricId: "peg_ratio",
    label: "PEG",
    sourceField: "pegratio_5y",
  },
  {
    metricId: "price_to_book",
    label: "P/B",
    sourceField: "pricebookratio.quarterly",
  },
];

const QUALITY_FIELD_DEFINITIONS: QualityFieldDefinition[] = [
  {
    metricId: "return_on_equity",
    label: "ROE",
    sourceField: "returnonequity.lasttwelvemonths",
  },
  {
    metricId: "return_on_assets",
    label: "ROA",
    sourceField: "returnonassets.lasttwelvemonths",
  },
  {
    metricId: "debt_to_equity",
    label: "Debt-to-equity",
    sourceField: "totaldebtequity.lasttwelvemonths",
  },
  {
    metricId: "current_ratio",
    label: "Current ratio",
    sourceField: "currentratio.lasttwelvemonths",
  },
];

function resolveFiniteNumber(value: number | null | undefined): number | null {
  if (typeof value !== "number") {
    return null;
  }
  if (!Number.isFinite(value)) {
    return null;
  }
  return value;
}

function buildDirectScreenerRow(
  metricId: YFinanceValuationMetricId | YFinanceQualityMetricId,
  label: string,
  sourceField: YFinanceScreenerField,
  snapshot: YFinanceScreenerSnapshot,
): YFinanceAdapterRow {
  const resolvedValue = resolveFiniteNumber(snapshot[sourceField]);

  if (resolvedValue === null) {
    return {
      metricId,
      label,
      availability: "unavailable",
      value: null,
      unit: "ratio",
      sourceField,
      reason: `Direct screener field missing: ${sourceField}.`,
      confidenceState: "direct",
    };
  }

  return {
    metricId,
    label,
    availability: "direct",
    value: resolvedValue,
    unit: "ratio",
    sourceField,
    reason: "Direct yfinance screener field resolved.",
    confidenceState: "direct",
  };
}

function resolveAtr14(bars: YFinanceOhlcvBar[]): number | null {
  if (bars.length < 15) {
    return null;
  }

  const trueRanges: number[] = [];
  for (let index = 1; index < bars.length; index += 1) {
    const currentBar = bars[index];
    const previousBar = bars[index - 1];
    const trueRange = Math.max(
      currentBar.high - currentBar.low,
      Math.abs(currentBar.high - previousBar.close),
      Math.abs(currentBar.low - previousBar.close),
    );
    trueRanges.push(trueRange);
  }

  const atrWindow = trueRanges.slice(-14);
  if (atrWindow.length < 14) {
    return null;
  }
  const atrValue =
    atrWindow.reduce((sum, windowValue) => sum + windowValue, 0) / atrWindow.length;
  return Number(atrValue.toFixed(4));
}

function resolveAverageImpliedVolatility(
  optionContracts: YFinanceOptionContract[],
): number | null {
  const impliedVolatilityValues = optionContracts
    .map((contract) => resolveFiniteNumber(contract.impliedVolatility))
    .filter((value): value is number => value !== null);

  if (impliedVolatilityValues.length === 0) {
    return null;
  }

  const averageValue =
    impliedVolatilityValues.reduce((sum, value) => sum + value, 0) /
    impliedVolatilityValues.length;
  return Number(averageValue.toFixed(4));
}

export function extractYFinanceValuationAdapterRows(
  snapshot: YFinanceScreenerSnapshot,
): YFinanceAdapterRow[] {
  return VALUATION_FIELD_DEFINITIONS.map((definition) =>
    buildDirectScreenerRow(
      definition.metricId,
      definition.label,
      definition.sourceField,
      snapshot,
    ),
  );
}

export function extractYFinanceQualityAdapterRows(
  snapshot: YFinanceScreenerSnapshot,
): YFinanceAdapterRow[] {
  return QUALITY_FIELD_DEFINITIONS.map((definition) =>
    buildDirectScreenerRow(
      definition.metricId,
      definition.label,
      definition.sourceField,
      snapshot,
    ),
  );
}

export function extractYFinanceTechnicalAdapterRows(
  payload: YFinanceTechnicalPayload,
): YFinanceAdapterRow[] {
  const latestBar = payload.bars.length > 0 ? payload.bars[payload.bars.length - 1] : null;
  const atr14 = resolveAtr14(payload.bars);
  const impliedVolatility = resolveAverageImpliedVolatility(payload.optionContracts);

  return [
    {
      metricId: "latest_close",
      label: "Latest close",
      availability: latestBar ? "direct" : "unavailable",
      value: latestBar?.close ?? null,
      unit: "price",
      sourceField: "Ticker.history().close",
      reason: latestBar
        ? "Direct OHLCV close from yfinance history."
        : "OHLCV bars missing from yfinance history.",
      confidenceState: "direct",
    },
    {
      metricId: "latest_volume",
      label: "Latest volume",
      availability: latestBar ? "direct" : "unavailable",
      value: latestBar?.volume ?? null,
      unit: "volume",
      sourceField: "Ticker.history().volume",
      reason: latestBar
        ? "Direct OHLCV volume from yfinance history."
        : "OHLCV bars missing from yfinance history.",
      confidenceState: "direct",
    },
    {
      metricId: "corporate_actions_count",
      label: "Corporate actions count",
      availability: "direct",
      value: payload.actions.length,
      unit: "count",
      sourceField: "Ticker.actions / Ticker.dividends / Ticker.splits",
      reason: "Direct corporate-action rows resolved from yfinance.",
      confidenceState: "direct",
    },
    {
      metricId: "option_implied_volatility",
      label: "Option implied volatility",
      availability: impliedVolatility === null ? "unavailable" : "direct",
      value: impliedVolatility,
      unit: "percent",
      sourceField: "Ticker.option_chain(...).calls/puts.impliedVolatility",
      reason:
        impliedVolatility === null
          ? "Option contracts missing impliedVolatility values."
          : "Direct option-chain impliedVolatility extraction.",
      confidenceState: "direct",
    },
    {
      metricId: "atr_14",
      label: "ATR (14)",
      availability: atr14 === null ? "unavailable" : "derived",
      value: atr14,
      unit: "price",
      sourceField: "Derived from OHLCV bars (14-period ATR)",
      reason:
        atr14 === null
          ? "Insufficient OHLCV history for ATR derivation."
          : "Deterministic ATR derivation from direct OHLCV bars.",
      confidenceState: "derived",
    },
  ];
}
