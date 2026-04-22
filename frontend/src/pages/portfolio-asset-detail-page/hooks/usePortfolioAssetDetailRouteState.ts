import { useMemo } from "react";
import { useParams } from "react-router-dom";

import {
  formatPortfolioMoney,
  formatPortfolioPercent,
  formatPortfolioQuantity,
  getPortfolioSummaryRowsByMarketValue,
  usePortfolioHealthSynthesisResource,
  usePortfolioLotDetailResource,
  usePortfolioSummaryResource,
  usePortfolioTimeSeriesResource,
} from "../../../core/api/portfolio";
import {
  type PortfolioHealthSynthesisResponse,
  type PortfolioLotDetailResponse,
  type PortfolioTimeSeriesResponse,
} from "../../../core/api/portfolio-schemas";
import {
  getDashboardResearchControls,
  resolveDecisionStateWithResearchControls,
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
import { type HierarchyPivotGroup } from "../../../features/portfolio-hierarchy/HierarchyPivotTable";

function resolveTickerLabel(rawTicker: string | undefined): string {
  if (!rawTicker || rawTicker.trim().length === 0) {
    return "UNKNOWN";
  }
  return rawTicker.toUpperCase();
}

function resolveValue(value: string | number | null | undefined): number {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
}

type PriceBar = {
  day: string;
  open: string;
  high: string;
  low: string;
  close: string;
};

type PriceVolumeComboRow = {
  label: string;
  value: string;
  context: string;
};

type BenchmarkRelativePoint = {
  window: string;
  asset: string;
  benchmark: string;
  spread: string;
};

type AssetRiskMetric = {
  metric: string;
  value: string;
  interpretation: string;
};

type NarrativeNote = {
  title: string;
  detail: string;
};

type AssetDetailStatus = "loading" | "ready" | "empty" | "error";

const FALLBACK_PRICE_BARS: PriceBar[] = [
  {
    day: "Mon",
    open: "418.2",
    high: "423.5",
    low: "416.9",
    close: "422.7",
  },
  {
    day: "Tue",
    open: "422.7",
    high: "425.9",
    low: "419.4",
    close: "420.5",
  },
  {
    day: "Wed",
    open: "420.5",
    high: "427.1",
    low: "419.7",
    close: "426.2",
  },
  {
    day: "Thu",
    open: "426.2",
    high: "429.0",
    low: "423.1",
    close: "424.4",
  },
];

const FALLBACK_PRICE_VOLUME_COMBO: PriceVolumeComboRow[] = [
  {
    label: "20D average volume",
    value: "Unavailable",
    context: "Live market volume is sourced from backend adapters.",
  },
  {
    label: "Session volume",
    value: "Unavailable",
    context: "Pending direct market price payload.",
  },
  {
    label: "Volume confirmation",
    value: "Neutral",
    context: "No conviction burst available from current contract set.",
  },
];

const FALLBACK_BENCHMARK_RELATIVE_CHART: BenchmarkRelativePoint[] = [
  { window: "30D", asset: "+3.4%", benchmark: "+1.9%", spread: "+150 bps" },
  { window: "90D", asset: "+7.8%", benchmark: "+4.2%", spread: "+360 bps" },
  { window: "180D", asset: "+12.4%", benchmark: "+8.1%", spread: "+430 bps" },
];

const FALLBACK_ASSET_RISK_METRICS: AssetRiskMetric[] = [
  {
    metric: "Beta (1Y)",
    value: "Unavailable",
    interpretation: "Awaiting live health synthesis.",
  },
  {
    metric: "Max drawdown (252D)",
    value: "Unavailable",
    interpretation: "Awaiting live health synthesis.",
  },
  {
    metric: "1D 95% VaR",
    value: "Unavailable",
    interpretation: "Awaiting live health synthesis.",
  },
];

const FALLBACK_ASSET_NARRATIVE_NOTES: NarrativeNote[] = [
  {
    title: "Earnings follow-through",
    detail: "Awaiting live ledger-backed synthesis for this symbol.",
  },
  {
    title: "Position sizing",
    detail: "Awaiting live ledger-backed synthesis for this symbol.",
  },
  {
    title: "Risk caveat",
    detail: "Awaiting live ledger-backed synthesis for this symbol.",
  },
];

const ASSET_SOURCE_CONTRACTS: SourceContractRegistry = {
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
    source_id: "yfinance.fundamentals.summary",
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
    as_of: "2026-04-18T09:58:00-04:00",
    freshness_state: "fresh",
    confidence_state: "direct",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
  derived_signals: {
    category: "derived_signals",
    source_id: "pandas.derived.risk.v1",
    as_of: "2026-04-18T14:32:00-04:00",
    freshness_state: "fresh",
    confidence_state: "derived",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
};

function buildPriceBars(points: PortfolioTimeSeriesResponse["points"]): PriceBar[] {
  const recentPoints = points.slice(-5);
  if (recentPoints.length === 0) {
    return FALLBACK_PRICE_BARS;
  }

  return recentPoints.map((point, index) => {
    const currentValue = resolveValue(point.portfolio_value_usd);
    const previousValue =
      index === 0
        ? currentValue
        : resolveValue(recentPoints[index - 1].portfolio_value_usd);
    const barOpen = previousValue;
    const barHigh = Math.max(previousValue, currentValue);
    const barLow = Math.min(previousValue, currentValue);

    return {
      day: point.captured_at.slice(5, 10),
      open: barOpen.toFixed(2),
      high: barHigh.toFixed(2),
      low: barLow.toFixed(2),
      close: currentValue.toFixed(2),
    };
  });
}

function buildBenchmarkRelativeChart(
  points: PortfolioTimeSeriesResponse["points"],
): BenchmarkRelativePoint[] {
  if (points.length === 0) {
    return FALLBACK_BENCHMARK_RELATIVE_CHART;
  }

  const sampleIndexes = Array.from(
    new Set([0, Math.max(0, Math.floor((points.length - 1) / 2)), points.length - 1]),
  );
  const firstPoint = points[0];
  const assetStart = resolveValue(firstPoint.portfolio_value_usd) || 1;
  const benchmarkStart =
    resolveValue(firstPoint.benchmark_sp500_value_usd ?? firstPoint.benchmark_nasdaq100_value_usd) || 1;

  return sampleIndexes.map((index) => {
    const point = points[index];
    const assetValue = resolveValue(point.portfolio_value_usd);
    const benchmarkValue = resolveValue(
      point.benchmark_sp500_value_usd ?? point.benchmark_nasdaq100_value_usd,
    );
    const assetChange = ((assetValue - assetStart) / assetStart) * 100;
    const benchmarkChange = ((benchmarkValue - benchmarkStart) / benchmarkStart) * 100;
    const spread = assetChange - benchmarkChange;

    return {
      window: point.captured_at.slice(0, 10),
      asset: `${assetChange >= 0 ? "+" : ""}${assetChange.toFixed(1)}%`,
      benchmark: `${benchmarkChange >= 0 ? "+" : ""}${benchmarkChange.toFixed(1)}%`,
      spread: `${spread >= 0 ? "+" : ""}${spread.toFixed(1)}%`,
    };
  });
}

function buildPositionPivotGroups(
  lotDetail: PortfolioLotDetailResponse | null,
  heroDecisionState: RouteDecisionState,
): HierarchyPivotGroup[] {
  if (!lotDetail || lotDetail.lots.length === 0) {
    return [
      {
        id: "core-lots",
        label: "Core lots",
        rows: [],
      },
    ];
  }

  const totalRemainingQty = lotDetail.lots.reduce(
    (runningTotal, lot) => runningTotal + resolveValue(lot.remaining_qty),
    0,
  );
  const openLotRows = lotDetail.lots.map((lot, index) => ({
    id: `lot-${lot.lot_id}`,
    label: `Lot ${String.fromCharCode(65 + index)} · opened ${lot.opened_on}`,
    weight:
      totalRemainingQty > 0
        ? formatPortfolioPercent((resolveValue(lot.remaining_qty) / totalRemainingQty) * 100, 1)
        : formatPortfolioQuantity(lot.remaining_qty),
    unrealized: `Cost ${formatPortfolioMoney(lot.total_cost_basis_usd)}`,
    action: lot.dispositions.length > 0 ? "Review disposals" : heroDecisionState,
  }));

  const dispositionRows = lotDetail.lots.flatMap((lot) =>
    lot.dispositions.map((disposition) => ({
      id: `lot-${lot.lot_id}-sell-${disposition.sell_transaction_id}`,
      label: `Sell #${disposition.sell_transaction_id} · ${disposition.disposition_date}`,
      weight: `Qty ${formatPortfolioQuantity(disposition.matched_qty)}`,
      unrealized: `Matched ${formatPortfolioMoney(disposition.matched_cost_basis_usd)}`,
      action: "Disposition",
    })),
  );

  const groups: HierarchyPivotGroup[] = [
    {
      id: "core-lots",
      label: "Core lots",
      rows: openLotRows,
    },
  ];

  if (dispositionRows.length > 0) {
    groups.push({
      id: "disposition-history",
      label: "Disposition history",
      rows: dispositionRows,
    });
  }

  return groups;
}

function buildAssetRiskMetrics(
  healthResponse: PortfolioHealthSynthesisResponse | null,
): AssetRiskMetric[] {
  if (healthResponse) {
    const metricRows = healthResponse.key_drivers.slice(0, 3).map((driver) => ({
      metric: driver.label,
      value: driver.value_display,
      interpretation: driver.rationale,
    }));
    if (metricRows.length > 0) {
      return metricRows;
    }
  }
  return FALLBACK_ASSET_RISK_METRICS;
}

function buildNarrativeNotes(
  healthResponse: PortfolioHealthSynthesisResponse | null,
): NarrativeNote[] {
  if (healthResponse) {
    const caveatNotes = healthResponse.health_caveats.slice(0, 3).map((caveat, index) => ({
      title: `Caveat ${index + 1}`,
      detail: caveat,
    }));
    if (caveatNotes.length > 0) {
      return caveatNotes;
    }
    return healthResponse.pillars.slice(0, 3).map((pillar) => ({
      title: pillar.label,
      detail: `${pillar.status} posture with ${pillar.score}/100 score.`,
    }));
  }
  return FALLBACK_ASSET_NARRATIVE_NOTES;
}

export type PortfolioAssetDetailRouteState = {
  status: AssetDetailStatus;
  errorMessage: string | null;
  reload: () => void;
  ticker: string;
  heroHealth: SourceContractHealth;
  priceActionHealth: SourceContractHealth;
  benchmarkHealth: SourceContractHealth;
  riskMetricHealth: SourceContractHealth;
  routeMessage: string;
  heroDecisionState: string;
  sourceContractRows: ReturnType<typeof listSourceContracts>;
  sourceContractEvidenceLine: string;
  assetWeight: string;
  marketValue: string;
  openLotCount: number;
  priceBars: PriceBar[];
  priceVolumeCombo: PriceVolumeComboRow[];
  benchmarkRelativeChart: BenchmarkRelativePoint[];
  assetRiskMetrics: AssetRiskMetric[];
  narrativeNotes: NarrativeNote[];
  positionPivotGroups: HierarchyPivotGroup[];
  isPrimaryModuleLoading: boolean;
};

export function usePortfolioAssetDetailRouteState(): PortfolioAssetDetailRouteState {
  const params = useParams<{ ticker: string }>();
  const ticker = resolveTickerLabel(params.ticker);
  const researchControls = getDashboardResearchControls();
  const isPrimaryModuleLoading = useIsPrimaryModuleLoading();
  const summary = usePortfolioSummaryResource();
  const lotDetail = usePortfolioLotDetailResource(ticker);
  const healthSynthesis = usePortfolioHealthSynthesisResource(
    "90D",
    "instrument_symbol",
    ticker,
  );
  const timeSeries = usePortfolioTimeSeriesResource("90D", "instrument_symbol", ticker);

  const summaryRows = useMemo(
    () => getPortfolioSummaryRowsByMarketValue(summary.data?.rows ?? []),
    [summary.data?.rows],
  );
  const matchingSummaryRow = useMemo(
    () => summaryRows.find((row) => row.instrument_symbol === ticker) ?? null,
    [summaryRows, ticker],
  );
  const totalMarketValue = useMemo(
    () =>
      summaryRows.reduce((runningTotal, row) => runningTotal + resolveValue(row.market_value_usd), 0),
    [summaryRows],
  );
  const assetWeight =
    matchingSummaryRow && totalMarketValue > 0
      ? formatPortfolioPercent(
          (resolveValue(matchingSummaryRow.market_value_usd) / totalMarketValue) * 100,
          1,
        )
      : "Unavailable";
  const marketValue =
    matchingSummaryRow !== null
      ? formatPortfolioMoney(matchingSummaryRow.market_value_usd)
      : "Unavailable";
  const openLotCount = lotDetail.data?.lots.length ?? 0;

  const heroHealth = resolveSourceContractHealth({
    contracts: ASSET_SOURCE_CONTRACTS,
    requiredCategories: ["market_prices", "fundamentals", "reference_metadata"],
    expectedTimezone: "America/New_York",
  });
  const priceActionHealth = resolveSourceContractHealth({
    contracts: ASSET_SOURCE_CONTRACTS,
    requiredCategories: ["market_prices"],
    expectedTimezone: "America/New_York",
  });
  const benchmarkHealth = resolveSourceContractHealth({
    contracts: ASSET_SOURCE_CONTRACTS,
    requiredCategories: ["market_prices", "reference_metadata"],
    expectedTimezone: "America/New_York",
  });
  const riskMetricHealth = resolveSourceContractHealth({
    contracts: ASSET_SOURCE_CONTRACTS,
    requiredCategories: ["market_prices", "derived_signals"],
    expectedTimezone: "America/New_York",
  });

  const heroRequestedState: RouteDecisionState =
    healthSynthesis.data?.health_label === "healthy"
      ? "buy"
      : healthSynthesis.data?.health_label === "watchlist"
        ? "wait"
        : "avoid";
  const heroDecision = resolveDecisionStateWithResearchControls(
    heroRequestedState,
    researchControls,
  );

  const priceBars = useMemo(
    () => buildPriceBars(timeSeries.data?.points ?? []),
    [timeSeries.data?.points],
  );
  const benchmarkRelativeChart = useMemo(
    () => buildBenchmarkRelativeChart(timeSeries.data?.points ?? []),
    [timeSeries.data?.points],
  );
  const priceVolumeCombo = useMemo<PriceVolumeComboRow[]>(
    () => [
      {
        label: "Market value",
        value: marketValue,
        context: "Live ledger position",
      },
      {
        label: "Open lots",
        value: openLotCount.toString(),
        context: "Ledger-open slices",
      },
      {
        label: "Health score",
        value: healthSynthesis.data ? healthSynthesis.data.health_score.toString() : "Unavailable",
        context: healthSynthesis.data ? `Profile posture ${healthSynthesis.data.profile_posture}` : "Awaiting synthesis",
      },
    ],
    [healthSynthesis.data, marketValue, openLotCount],
  );
  const assetRiskMetrics = useMemo(
    () => buildAssetRiskMetrics(healthSynthesis.data ?? null),
    [healthSynthesis.data],
  );
  const narrativeNotes = useMemo(
    () => buildNarrativeNotes(healthSynthesis.data ?? null),
    [healthSynthesis.data],
  );
  const positionPivotGroups = useMemo(
    () => buildPositionPivotGroups(lotDetail.data ?? null, heroDecision.state),
    [heroDecision.state, lotDetail.data],
  );
  const sourceContractRows = useMemo(
    () =>
      listSourceContracts(ASSET_SOURCE_CONTRACTS, [
        "market_prices",
        "fundamentals",
        "reference_metadata",
        "derived_signals",
      ]),
    [],
  );

  const status: AssetDetailStatus = useMemo(() => {
    if (
      summary.status === "loading" ||
      lotDetail.status === "loading" ||
      healthSynthesis.status === "loading" ||
      timeSeries.status === "loading"
    ) {
      return "loading";
    }
    if (
      summary.status === "error" ||
      lotDetail.status === "error" ||
      healthSynthesis.status === "error" ||
      timeSeries.status === "error"
    ) {
      return "error";
    }
    if (
      summary.status === "empty" ||
      lotDetail.status === "empty" ||
      healthSynthesis.status === "empty" ||
      timeSeries.status === "empty" ||
      matchingSummaryRow === null
    ) {
      return "empty";
    }
    return "ready";
  }, [
    healthSynthesis.status,
    lotDetail.status,
    matchingSummaryRow,
    summary.status,
    timeSeries.status,
  ]);

  const errorMessage =
    lotDetail.errorMessage ??
    summary.errorMessage ??
    healthSynthesis.errorMessage ??
    timeSeries.errorMessage;

  const routeMessage =
    status === "ready"
      ? `Asset deep dive for ${ticker} is ready from live ledger data with ${openLotCount} open lots and ${assetWeight} portfolio weight.`
      : status === "empty"
        ? `No open-position ledger row was found for ${ticker}.`
        : `Asset deep dive degraded: ${errorMessage ?? heroHealth.message}`;

  const reload = (): void => {
    summary.reload();
    lotDetail.reload();
    healthSynthesis.reload();
    timeSeries.reload();
  };

  return {
    status,
    errorMessage,
    reload,
    ticker,
    heroHealth,
    priceActionHealth,
    benchmarkHealth,
    riskMetricHealth,
    routeMessage,
    heroDecisionState: heroDecision.state,
    sourceContractRows,
    sourceContractEvidenceLine: sourceContractRows
      .map((contract) => formatSourceContractEvidence(contract))
      .join(" || "),
    assetWeight,
    marketValue,
    openLotCount,
    priceBars,
    priceVolumeCombo,
    benchmarkRelativeChart,
    assetRiskMetrics,
    narrativeNotes,
    positionPivotGroups,
    isPrimaryModuleLoading,
  };
}
