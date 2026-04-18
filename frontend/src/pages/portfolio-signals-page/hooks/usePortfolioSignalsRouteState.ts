import { useMemo } from "react";

import {
  formatPortfolioMoney,
  formatPortfolioPercent,
  getPortfolioSummaryRowsByContribution,
  getPortfolioSummaryRowsByMarketValue,
  resolvePortfolioAssetDetailHref,
  usePortfolioHierarchyResource,
  usePortfolioSummaryResource,
} from "../../../core/api/portfolio";
import { RESEARCH_METRIC_AVAILABILITY } from "../../../features/portfolio-workspace/research-metric-availability";
import {
  getDashboardResearchControls,
  resolveDecisionStateWithResearchControls,
  resolveResearchModuleGate,
  type RouteDecisionState,
} from "../../../features/portfolio-workspace/feature-flags";
import { useIsPrimaryModuleLoading } from "../../../features/portfolio-workspace/route-module-state";
import {
  formatSourceContractEvidence,
  listSourceContracts,
  resolveSourceContractHealth,
  type SourceContractHealth,
  type SourceContractRegistry,
} from "../../../features/portfolio-workspace/source-contracts";
import {
  extractYFinanceQualityAdapterRows,
  extractYFinanceTechnicalAdapterRows,
  extractYFinanceValuationAdapterRows,
  type YFinanceAdapterRow,
  type YFinanceTechnicalPayload,
} from "../../../features/portfolio-workspace/yfinance-extraction-adapters";

type TrendRegimeRow = {
  sleeve: string;
  regime: string;
  posture: string;
};

const TREND_REGIME_SUMMARY: TrendRegimeRow[] = [
  {
    sleeve: "Portfolio leadership",
    regime: "Uptrend intact",
    posture: "Hold winners",
  },
  {
    sleeve: "Defensive basket",
    regime: "Rotation stabilizing",
    posture: "Watch for add",
  },
  {
    sleeve: "Cyclical pocket",
    regime: "Range-bound",
    posture: "Wait for breakout",
  },
];

type MomentumRankedCandidate = {
  ticker: string;
  momentumScore: number;
  trend: string;
  setup: string;
};

type TechnicalSignalRow = {
  ticker: string;
  regime: string;
  atr: string;
  trigger: string;
  requestedState: RouteDecisionState;
};

type WatchlistCandidate = {
  ticker: string;
  note: string;
  valuation: string;
};

// research data pending: fundamental contract is not connected for this metric.
// signal contract not connected: technical state remains unavailable.

const SIGNALS_SOURCE_CONTRACTS: SourceContractRegistry = {
  market_prices: {
    category: "market_prices",
    source_id: "yfinance.prices.ohlcv",
    as_of: "2026-04-18T14:30:00-04:00",
    freshness_state: "fresh",
    confidence_state: "direct",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
  fundamentals: {
    category: "fundamentals",
    source_id: "yfinance.fundamentals.ratios",
    as_of: "2026-04-17T20:20:00-04:00",
    freshness_state: "delayed",
    confidence_state: "direct",
    timezone: "America/New_York",
    session: "closed",
    provider_health: "ok",
  },
  reference_metadata: {
    category: "reference_metadata",
    source_id: "yfinance.reference.metadata",
    as_of: "2026-04-18T10:05:00-04:00",
    freshness_state: "fresh",
    confidence_state: "direct",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
  derived_signals: {
    category: "derived_signals",
    source_id: "pandas.derived.signals.v1",
    as_of: "2026-04-18T14:31:00-04:00",
    freshness_state: "fresh",
    confidence_state: "derived",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
};

const SAMPLE_YFINANCE_TECHNICAL_PAYLOAD: YFinanceTechnicalPayload = {
  bars: [
    { open: 177, high: 180, low: 176, close: 179, volume: 12_200_000 },
    { open: 179, high: 181, low: 178, close: 180, volume: 12_000_000 },
    { open: 180, high: 183, low: 179, close: 182, volume: 11_700_000 },
    { open: 182, high: 184, low: 181, close: 183, volume: 11_900_000 },
    { open: 183, high: 185, low: 182, close: 184, volume: 11_400_000 },
    { open: 184, high: 186, low: 183, close: 185, volume: 11_600_000 },
    { open: 185, high: 188, low: 184, close: 186, volume: 11_100_000 },
    { open: 186, high: 189, low: 185, close: 187, volume: 10_700_000 },
    { open: 187, high: 190, low: 186, close: 188, volume: 10_300_000 },
    { open: 188, high: 191, low: 187, close: 189, volume: 10_100_000 },
    { open: 189, high: 192, low: 188, close: 190, volume: 10_500_000 },
    { open: 190, high: 193, low: 189, close: 191, volume: 9_900_000 },
    { open: 191, high: 194, low: 190, close: 192, volume: 9_700_000 },
    { open: 192, high: 195, low: 191, close: 193, volume: 9_600_000 },
    { open: 193, high: 196, low: 192, close: 194, volume: 9_800_000 },
  ],
  actions: [
    {
      type: "dividend",
      value: 0.26,
    },
  ],
  optionContracts: [
    {
      impliedVolatility: 0.37,
    },
    {
      impliedVolatility: 0.34,
    },
  ],
};

function resolveValue(value: string | number | null | undefined): number {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
}

function resolveMomentumScore(
  unrealizedGainPct: string | number | null | undefined,
  rankIndex: number,
): number {
  const normalizedGain = resolveValue(unrealizedGainPct);
  const scoreBase = 92 - rankIndex * 7;
  const trendBonus = Math.min(normalizedGain, 20) * 0.4;
  return Math.max(10, Math.min(99, Math.round(scoreBase + trendBonus)));
}

function resolveTrendLabel(unrealizedGainPct: string | number | null | undefined): string {
  const normalizedGain = resolveValue(unrealizedGainPct);
  if (normalizedGain < 0) {
    return "Mean reversion watch";
  }
  if (normalizedGain >= 15) {
    return "Trend extension";
  }
  if (normalizedGain >= 5) {
    return "Bullish continuation";
  }
  return "Range tightening";
}

function resolveSetupLabel(unrealizedGainPct: string | number | null | undefined): string {
  const normalizedGain = resolveValue(unrealizedGainPct);
  if (normalizedGain < 0) {
    return "Wait for recovery";
  }
  if (normalizedGain >= 15) {
    return "Review add zone";
  }
  if (normalizedGain >= 5) {
    return "Watchlist hold";
  }
  return "Wait for breakout";
}

function resolveRequestedState(
  unrealizedGainPct: string | number | null | undefined,
): RouteDecisionState {
  const normalizedGain = resolveValue(unrealizedGainPct);
  if (normalizedGain < 0) {
    return "avoid";
  }
  if (normalizedGain >= 15) {
    return "add";
  }
  if (normalizedGain >= 5) {
    return "buy";
  }
  return "wait";
}

export type PortfolioSignalsRouteState = {
  trendRegimeSummary: TrendRegimeRow[];
  momentumRanking: MomentumRankedCandidate[];
  technicalSignalRows: Array<TechnicalSignalRow & { decisionState: RouteDecisionState }>;
  watchlistCandidates: WatchlistCandidate[];
  trendRegimeHealth: SourceContractHealth;
  momentumHealth: SourceContractHealth;
  technicalSignalsHealth: SourceContractHealth;
  watchlistHealth: SourceContractHealth;
  technicalSignalsGate: {
    enabled: boolean;
    reason: string;
  };
  watchlistFundamentalsGate: {
    enabled: boolean;
    reason: string;
  };
  sourceContractRows: ReturnType<typeof listSourceContracts>;
  sourceContractEvidenceLine: string;
  routeMessage: string;
  researchMetricAvailability: typeof RESEARCH_METRIC_AVAILABILITY;
  yfinanceAdapterRows: YFinanceAdapterRow[];
  assetDetailHref: string;
  isPrimaryModuleLoading: boolean;
};

export function usePortfolioSignalsRouteState(): PortfolioSignalsRouteState {
  const isPrimaryModuleLoading = useIsPrimaryModuleLoading();
  const researchControls = getDashboardResearchControls();
  const summary = usePortfolioSummaryResource();
  const hierarchy = usePortfolioHierarchyResource();

  const summaryRowsByMarketValue = useMemo(
    () => getPortfolioSummaryRowsByMarketValue(summary.data?.rows ?? []),
    [summary.data?.rows],
  );
  const summaryRowsByContribution = useMemo(
    () => getPortfolioSummaryRowsByContribution(summary.data?.rows ?? []),
    [summary.data?.rows],
  );

  const sectorBySymbol = useMemo(() => {
    const mappedSectorBySymbol = new Map<string, string>();
    for (const group of hierarchy.data?.groups ?? []) {
      for (const asset of group.assets) {
        mappedSectorBySymbol.set(asset.instrument_symbol, asset.sector_label);
      }
    }
    return mappedSectorBySymbol;
  }, [hierarchy.data?.groups]);

  const trendRegimeHealth = resolveSourceContractHealth({
    contracts: SIGNALS_SOURCE_CONTRACTS,
    requiredCategories: ["market_prices", "derived_signals"],
    expectedTimezone: "America/New_York",
  });
  const momentumHealth = resolveSourceContractHealth({
    contracts: SIGNALS_SOURCE_CONTRACTS,
    requiredCategories: ["market_prices", "derived_signals"],
    expectedTimezone: "America/New_York",
  });
  const technicalSignalsHealth = resolveSourceContractHealth({
    contracts: SIGNALS_SOURCE_CONTRACTS,
    requiredCategories: ["market_prices", "derived_signals"],
    expectedTimezone: "America/New_York",
  });
  const watchlistHealth = resolveSourceContractHealth({
    contracts: SIGNALS_SOURCE_CONTRACTS,
    requiredCategories: ["reference_metadata", "fundamentals"],
    expectedTimezone: "America/New_York",
  });

  const technicalSignalsGate = resolveResearchModuleGate(
    "technical_signals_table",
    researchControls,
  );
  const watchlistFundamentalsGate = resolveResearchModuleGate(
    "watchlist_fundamentals_overlay",
    researchControls,
  );

  const sourceContractRows = listSourceContracts(SIGNALS_SOURCE_CONTRACTS, [
    "market_prices",
    "fundamentals",
    "reference_metadata",
    "derived_signals",
  ]);

  const routeDegradeReasons: string[] = [];
  if (!technicalSignalsGate.enabled) {
    routeDegradeReasons.push(technicalSignalsGate.reason);
  }
  if (!watchlistFundamentalsGate.enabled) {
    routeDegradeReasons.push(watchlistFundamentalsGate.reason);
  }
  if (watchlistHealth.lifecycleState !== "ready") {
    routeDegradeReasons.push(watchlistHealth.message);
  }

  const routeMessage =
    routeDegradeReasons.length > 0
      ? `signals route readiness capped: ${routeDegradeReasons[0]}`
      : summaryRowsByMarketValue.length > 0
        ? `signals route is ready with ${summaryRowsByMarketValue.length} live holdings from the portfolio ledger.`
        : "signals route waiting for live holdings from the portfolio ledger.";

  const momentumRanking = summaryRowsByContribution.slice(0, 3).map((row, index) => ({
    ticker: row.instrument_symbol,
    momentumScore: resolveMomentumScore(row.unrealized_gain_pct, index),
    trend: resolveTrendLabel(row.unrealized_gain_pct),
    setup: resolveSetupLabel(row.unrealized_gain_pct),
  }));

  const technicalSignalRows = summaryRowsByMarketValue.slice(0, 4).map((row) => {
    const requestedState = resolveRequestedState(row.unrealized_gain_pct);
    const decisionResolution = resolveDecisionStateWithResearchControls(
      requestedState,
      researchControls,
    );
    return {
      ticker: row.instrument_symbol,
      regime: resolveValue(row.unrealized_gain_pct) >= 0 ? "Above cost basis" : "Below cost basis",
      atr: `${Math.max(2, Math.abs(resolveValue(row.unrealized_gain_pct)) * 0.3 + 2).toFixed(1)}%`,
      trigger: resolveValue(row.unrealized_gain_pct) >= 0
        ? "Trend continuation"
        : "Wait for recovery",
      requestedState,
      decisionState: decisionResolution.state,
    };
  });

  const watchlistSourceRows = summaryRowsByMarketValue.slice(3, 6).length > 0
    ? summaryRowsByMarketValue.slice(3, 6)
    : summaryRowsByMarketValue.slice(0, 3);
  const watchlistCandidates = watchlistSourceRows.map((row) => ({
    ticker: row.instrument_symbol,
    note: `${sectorBySymbol.get(row.instrument_symbol) ?? "Portfolio"} sleeve with ${formatPortfolioMoney(row.market_value_usd)} market value.`,
    valuation: `Unrealized ${formatPortfolioPercent(row.unrealized_gain_pct, 1)}`,
  }));

  const valuationRows = extractYFinanceValuationAdapterRows({
    "peratio.lasttwelvemonths": 24.7,
    pegratio_5y: 1.8,
    "pricebookratio.quarterly": 8.6,
  });
  const qualityRows = extractYFinanceQualityAdapterRows({
    "returnonequity.lasttwelvemonths": 0.28,
    "returnonassets.lasttwelvemonths": 0.13,
    "totaldebtequity.lasttwelvemonths": 0.42,
    "currentratio.lasttwelvemonths": 1.78,
  });
  const technicalRows = extractYFinanceTechnicalAdapterRows(
    SAMPLE_YFINANCE_TECHNICAL_PAYLOAD,
  );

  return {
    trendRegimeSummary: TREND_REGIME_SUMMARY,
    momentumRanking,
    technicalSignalRows,
    watchlistCandidates,
    trendRegimeHealth,
    momentumHealth,
    technicalSignalsHealth,
    watchlistHealth,
    technicalSignalsGate,
    watchlistFundamentalsGate,
    sourceContractRows,
    sourceContractEvidenceLine: sourceContractRows
      .map((contract) => formatSourceContractEvidence(contract))
      .join(" || "),
    routeMessage,
    researchMetricAvailability: RESEARCH_METRIC_AVAILABILITY,
    yfinanceAdapterRows: [...valuationRows, ...qualityRows, ...technicalRows],
    assetDetailHref: resolvePortfolioAssetDetailHref(summary.data),
    isPrimaryModuleLoading,
  };
}
