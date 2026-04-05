import {
  Link,
  useSearchParams,
} from "react-router-dom";
import {
  useEffect,
  useState,
} from "react";

import { PortfolioMonthlyReturnsHeatmap } from "../../components/charts/AnalystVisualModules";
import { WorkspaceChartPanel } from "../../components/charts/WorkspaceChartPanel";
import { EmptyState } from "../../components/empty-state/EmptyState";
import { ErrorBanner } from "../../components/error-banner/ErrorBanner";
import { MetricExplainabilityPopover } from "../../components/metric-explainability/MetricExplainabilityPopover";
import { LoadingTableSkeleton } from "../../components/skeletons/LoadingTableSkeleton";
import { PortfolioWorkspaceLayout } from "../../components/workspace-layout/PortfolioWorkspaceLayout";
import { AppApiError } from "../../core/api/errors";
import type {
  PortfolioChartPeriod,
  PortfolioContributionRow,
  PortfolioHealthProfilePosture,
  PortfolioMonteCarloProfileScenario,
  PortfolioMonteCarloRequest,
  PortfolioQuantMetric,
  PortfolioQuantReportGenerateRequest,
  PortfolioQuantReportScope,
  PortfolioTimeSeriesScope,
} from "../../core/api/schemas";
import { formatUsdMoney } from "../../core/lib/formatters";
import { PortfolioChartPeriodControl } from "../../features/portfolio-workspace/PortfolioChartPeriodControl";
import { resolveWorkspaceError } from "../../features/portfolio-workspace/errors";
import {
  usePortfolioContributionQuery,
  usePortfolioHealthSynthesisQuery,
  usePortfolioQuantMetricsQuery,
  usePortfolioMonteCarloMutation,
  usePortfolioQuantReportGenerateMutation,
  usePortfolioQuantReportHtmlQuery,
  usePortfolioTimeSeriesQuery,
} from "../../features/portfolio-workspace/hooks";
import {
  buildQuantMetricCards,
  topContributionRows,
} from "../../features/portfolio-workspace/overview";
import { resolvePortfolioChartPeriod } from "../../features/portfolio-workspace/period";
import { usePortfolioSummaryQuery } from "../../features/portfolio-summary/hooks";

function resolvePeriodFromSearchParams(searchParams: URLSearchParams) {
  return resolvePortfolioChartPeriod(searchParams.get("period"), "90D");
}

const MONTE_CARLO_RECOMMENDED_HORIZON_BY_PERIOD: Record<
  PortfolioChartPeriod,
  number
> = {
  "30D": 20,
  "90D": 60,
  "6M": 84,
  "252D": 126,
  YTD: 60,
  MAX: 252,
};

const MONTE_CARLO_MAX_HORIZON_BY_PERIOD: Record<
  PortfolioChartPeriod,
  number
> = {
  "30D": 29,
  "90D": 89,
  "6M": 125,
  "252D": 251,
  YTD: 251,
  MAX: 756,
};

type MonteCarloCalibrationBasis = "monthly" | "annual" | "manual";
type MonteCarloProfileId = "conservative" | "balanced" | "growth";
type MonteCarloSignal =
  | "monitor"
  | "balanced"
  | "downside_caution"
  | "upside_favorable";

const MONTE_CARLO_PROFILE_PRESETS: Record<
  MonteCarloProfileId,
  { bust: string; goal: string; label: string }
> = {
  conservative: { bust: "-0.10", goal: "0.12", label: "Conservative" },
  balanced: { bust: "-0.20", goal: "0.27", label: "Balanced" },
  growth: { bust: "-0.30", goal: "0.45", label: "Growth" },
};

function resolveContributionTone(
  contributionPnlUsd: string,
): "positive" | "negative" | "neutral" {
  const numericValue = Number(contributionPnlUsd);
  if (!Number.isFinite(numericValue)) {
    return "neutral";
  }
  if (numericValue > 0) {
    return "positive";
  }
  if (numericValue < 0) {
    return "negative";
  }
  return "neutral";
}

function formatSignedPercent(value: string): string {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return `${value}%`;
  }
  const signPrefix = numericValue > 0 ? "+" : "";
  return `${signPrefix}${numericValue.toFixed(2)}%`;
}

function toFiniteRatio(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const numericValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numericValue)) {
    return null;
  }
  return numericValue;
}

function formatRatioPercent(
  value: string | number | null | undefined,
  options?: { signed?: boolean },
): string {
  const numericValue = toFiniteRatio(value);
  if (numericValue === null) {
    return "—";
  }
  const percentValue = numericValue * 100;
  const signed = options?.signed ?? false;
  const signPrefix = signed && percentValue > 0 ? "+" : "";
  return `${signPrefix}${percentValue.toFixed(2)}%`;
}

function formatBoundedPercent(value: string | number | null | undefined): string {
  const numericValue = toFiniteRatio(value);
  if (numericValue === null) {
    return "—";
  }
  const boundedValue = Math.max(0, Math.min(1, numericValue));
  return `${(boundedValue * 100).toFixed(2)}%`;
}

function formatScopeNarrative(
  scope: PortfolioQuantReportScope,
  instrumentSymbol: string | null,
  period: string,
  horizonDays: number,
): string {
  const scopeLabel =
    scope === "instrument_symbol" && instrumentSymbol
      ? `${instrumentSymbol} instrument scope`
      : "Portfolio scope";
  return `${scopeLabel} · ${period} window · ${horizonDays}-day horizon.`;
}

function resolveMonteCarloSignalLabel(
  bustProbabilityRatio: number | null,
  goalProbabilityRatio: number | null,
): MonteCarloSignal {
  if (bustProbabilityRatio === null && goalProbabilityRatio === null) {
    return "monitor";
  }
  if (bustProbabilityRatio !== null && bustProbabilityRatio >= 0.25) {
    return "downside_caution";
  }
  if (goalProbabilityRatio !== null && goalProbabilityRatio >= 0.5) {
    return "upside_favorable";
  }
  return "balanced";
}

function formatMonteCarloSignalLabel(signal: MonteCarloSignal): string {
  if (signal === "downside_caution") {
    return "Downside caution";
  }
  if (signal === "upside_favorable") {
    return "Upside favorable";
  }
  if (signal === "balanced") {
    return "Balanced";
  }
  return "Monitor";
}

function formatCalibrationBasisLabel(basis: MonteCarloCalibrationBasis): string {
  if (basis === "monthly") {
    return "Monthly";
  }
  if (basis === "annual") {
    return "Annual";
  }
  return "Manual";
}

function formatThresholdInputValue(value: string | number | null | undefined): string {
  const ratio = toFiniteRatio(value);
  if (ratio === null) {
    return "";
  }
  return ratio.toFixed(2);
}

function resolveProfileScenarioById(
  profileRows: PortfolioMonteCarloProfileScenario[] | undefined,
  profileId: MonteCarloProfileId,
): PortfolioMonteCarloProfileScenario | null {
  if (!profileRows || profileRows.length === 0) {
    return null;
  }
  return profileRows.find((row) => row.profile_id === profileId) ?? null;
}

function buildContributionRows(rows: PortfolioContributionRow[]): {
  rows: Array<{
    instrumentSymbol: string;
    contributionPnlUsd: string;
    netSharePct: number;
    absSharePct: number;
    tone: "positive" | "negative" | "neutral";
    widthPct: number;
  }>;
  positiveLeader: string | null;
  negativeLeader: string | null;
  concentrationPct: string;
} {
  const sortedRows = topContributionRows(rows);
  const maxAbsContribution = Math.max(
    1,
    ...sortedRows.map((row) => Math.abs(Number(row.contribution_pnl_usd))),
  );
  const totalAbsContribution = sortedRows.reduce((accumulator, row) => {
    return accumulator + Math.abs(Number(row.contribution_pnl_usd));
  }, 0);
  const totalNetContribution = sortedRows.reduce((accumulator, row) => {
    return accumulator + Number(row.contribution_pnl_usd);
  }, 0);

  const positiveLeader = sortedRows.find(
    (row) => Number(row.contribution_pnl_usd) > 0,
  );
  const negativeLeader = sortedRows.find(
    (row) => Number(row.contribution_pnl_usd) < 0,
  );
  const concentrationNumerator =
    sortedRows.length > 0 ? Math.abs(Number(sortedRows[0].contribution_pnl_usd)) : 0;
  const concentrationPct =
    totalAbsContribution > 0
      ? ((concentrationNumerator / totalAbsContribution) * 100).toFixed(2)
      : "0.00";

  return {
    rows: sortedRows.map((row) => {
      const contributionNumericValue = Number(row.contribution_pnl_usd);
      const netSharePct =
        totalNetContribution === 0
          ? 0
          : (contributionNumericValue / totalNetContribution) * 100;
      const absSharePct =
        totalAbsContribution === 0
          ? 0
          : (Math.abs(contributionNumericValue) / totalAbsContribution) * 100;
      const contributionAbs = Math.abs(Number(row.contribution_pnl_usd));
      const widthPct = Math.max(
        8,
        Math.round((contributionAbs / maxAbsContribution) * 100),
      );
      return {
        instrumentSymbol: row.instrument_symbol,
        contributionPnlUsd: row.contribution_pnl_usd,
        netSharePct,
        absSharePct,
        tone: resolveContributionTone(row.contribution_pnl_usd),
        widthPct,
      };
    }),
    positiveLeader: positiveLeader
      ? `${positiveLeader.instrument_symbol} ${formatUsdMoney(positiveLeader.contribution_pnl_usd)}`
      : null,
    negativeLeader: negativeLeader
      ? `${negativeLeader.instrument_symbol} ${formatUsdMoney(negativeLeader.contribution_pnl_usd)}`
      : null,
    concentrationPct,
  };
}

function resolveReportPreviewError(error: unknown): {
  title: string;
  variant: "error" | "warning";
  message: string;
} {
  if (error instanceof AppApiError && error.detail) {
    const detail = error.detail.toLowerCase();
    if (detail.includes("unavailable") || detail.includes("expired")) {
      return {
        title: "Report lifecycle: unavailable",
        variant: "warning",
        message: error.detail,
      };
    }
  }

  return resolveWorkspaceError(
    error,
    "Report lifecycle: error",
    "The generated HTML artifact is not available right now.",
  );
}

function formatQuantLensMetricValue(metric: PortfolioQuantMetric | undefined): string {
  if (!metric) {
    return "—";
  }
  const numericValue = Number(metric.value);
  if (!Number.isFinite(numericValue)) {
    return String(metric.value);
  }
  if (metric.display_as === "percent") {
    const percentValue = numericValue * 100;
    const signPrefix = percentValue > 0 ? "+" : "";
    return `${signPrefix}${percentValue.toFixed(2)}%`;
  }
  return numericValue.toFixed(3);
}

type ReportLifecycleUiState =
  | "invalid_request"
  | "loading"
  | "ready"
  | "unavailable"
  | "error";

type MonteCarloLifecycleUiState =
  | "invalid_request"
  | "loading"
  | "ready"
  | "unavailable"
  | "error";

type OptionalThresholdParseResult =
  | { kind: "empty" }
  | { kind: "valid"; value: number }
  | { kind: "invalid" };

function parseOptionalThreshold(value: string): OptionalThresholdParseResult {
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return { kind: "empty" };
  }
  const numeric = Number(trimmed);
  if (!Number.isFinite(numeric)) {
    return { kind: "invalid" };
  }
  return { kind: "valid", value: numeric };
}

function resolveMonteCarloErrorCopy(error: unknown): {
  title: string;
  message: string;
  variant: "error" | "warning";
} {
  if (
    error instanceof AppApiError &&
    error.kind === "validation_error" &&
    error.statusCode === 409 &&
    typeof error.detail === "string" &&
    error.detail.toLowerCase().includes("insufficient persisted history")
  ) {
    return {
      title: "Simulation lifecycle: unavailable for selected horizon",
      message: `${error.detail} Reduce horizon days or use a longer period.`,
      variant: "warning",
    };
  }

  return resolveWorkspaceError(
    error,
    "Simulation lifecycle: error",
    "Monte Carlo simulation failed for selected scope.",
  );
}

export function PortfolioReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedPeriod = resolvePeriodFromSearchParams(searchParams);
  const [reportScope, setReportScope] = useState<PortfolioQuantReportScope>("portfolio");
  const [reportInstrumentSymbol, setReportInstrumentSymbol] = useState("");
  const [heatmapScope, setHeatmapScope] = useState<PortfolioTimeSeriesScope>("portfolio");
  const [heatmapInstrumentSymbol, setHeatmapInstrumentSymbol] = useState("");
  const [reportValidationError, setReportValidationError] = useState<string | null>(null);
  const [activeReportId, setActiveReportId] = useState<string | null>(null);
  const [healthProfilePosture, setHealthProfilePosture] =
    useState<PortfolioHealthProfilePosture>("balanced");
  const [monteCarloSims, setMonteCarloSims] = useState("1000");
  const [monteCarloHorizonDays, setMonteCarloHorizonDays] = useState(
    String(MONTE_CARLO_RECOMMENDED_HORIZON_BY_PERIOD[selectedPeriod]),
  );
  const [monteCarloHorizonTouched, setMonteCarloHorizonTouched] = useState(false);
  const [monteCarloBustThreshold, setMonteCarloBustThreshold] = useState("-0.20");
  const [monteCarloGoalThreshold, setMonteCarloGoalThreshold] = useState("0.30");
  const [monteCarloSeed, setMonteCarloSeed] = useState("20260330");
  const [monteCarloProfileComparisonEnabled, setMonteCarloProfileComparisonEnabled] =
    useState(true);
  const [monteCarloCalibrationBasis, setMonteCarloCalibrationBasis] =
    useState<MonteCarloCalibrationBasis>("monthly");
  const [monteCarloValidationError, setMonteCarloValidationError] = useState<string | null>(null);

  const summaryQuery = usePortfolioSummaryQuery();
  const normalizedReportInstrumentSymbol = reportInstrumentSymbol.trim().toUpperCase();
  const isReportInstrumentScope = reportScope === "instrument_symbol";
  const isHealthScopeReady =
    !isReportInstrumentScope || normalizedReportInstrumentSymbol.length > 0;
  const normalizedHeatmapInstrumentSymbol = heatmapInstrumentSymbol.trim().toUpperCase();
  const isInstrumentHeatmapScope = heatmapScope === "instrument_symbol";
  const isHeatmapScopeReady =
    !isInstrumentHeatmapScope || normalizedHeatmapInstrumentSymbol.length > 0;
  const timeSeriesQuery = usePortfolioTimeSeriesQuery(selectedPeriod, {
    scope: heatmapScope,
    instrumentSymbol: isInstrumentHeatmapScope ? normalizedHeatmapInstrumentSymbol : null,
    enabled: isHeatmapScopeReady,
  });
  const contributionQuery = usePortfolioContributionQuery(selectedPeriod);
  const quantMetricsQuery = usePortfolioQuantMetricsQuery(selectedPeriod);
  const quantMetrics30Query = usePortfolioQuantMetricsQuery("30D");
  const quantMetrics90Query = usePortfolioQuantMetricsQuery("90D");
  const quantMetrics252Query = usePortfolioQuantMetricsQuery("252D");
  const quantReportGenerateMutation = usePortfolioQuantReportGenerateMutation();
  const quantReportHtmlQuery = usePortfolioQuantReportHtmlQuery(activeReportId);
  const monteCarloMutation = usePortfolioMonteCarloMutation();
  const healthQuery = usePortfolioHealthSynthesisQuery(selectedPeriod, {
    scope: reportScope,
    instrumentSymbol: isReportInstrumentScope ? normalizedReportInstrumentSymbol : null,
    profilePosture: healthProfilePosture,
    enabled: isHealthScopeReady,
  });

  const quantErrorCopy = resolveWorkspaceError(
    quantMetricsQuery.error,
    "Quant diagnostics unavailable",
    "Quant diagnostics could not be loaded for this period.",
  );
  const quantReportGenerateErrorCopy = resolveWorkspaceError(
    quantReportGenerateMutation.error,
    "Report lifecycle: error",
    "Report generation failed for the selected scope and period.",
  );
  const contributionErrorCopy = resolveWorkspaceError(
    contributionQuery.error,
    "Contribution focus unavailable",
    "Contribution rows could not be loaded for this period.",
  );
  const quantReportPreviewErrorCopy = resolveReportPreviewError(quantReportHtmlQuery.error);
  const monteCarloErrorCopy = resolveMonteCarloErrorCopy(monteCarloMutation.error);

  const availableInstrumentSymbols = summaryQuery.isSuccess
    ? summaryQuery.data.rows.map((row) => row.instrument_symbol)
    : [];

  useEffect(() => {
    if (
      reportScope === "instrument_symbol" &&
      availableInstrumentSymbols.length > 0 &&
      reportInstrumentSymbol.length === 0
    ) {
      setReportInstrumentSymbol(availableInstrumentSymbols[0]);
    }
  }, [availableInstrumentSymbols, reportInstrumentSymbol.length, reportScope]);

  useEffect(() => {
    if (
      heatmapScope === "instrument_symbol" &&
      availableInstrumentSymbols.length > 0 &&
      heatmapInstrumentSymbol.length === 0
    ) {
      setHeatmapInstrumentSymbol(availableInstrumentSymbols[0]);
    }
  }, [availableInstrumentSymbols, heatmapInstrumentSymbol.length, heatmapScope]);

  useEffect(() => {
    if (monteCarloHorizonTouched) {
      return;
    }
    setMonteCarloHorizonDays(
      String(MONTE_CARLO_RECOMMENDED_HORIZON_BY_PERIOD[selectedPeriod]),
    );
  }, [monteCarloHorizonTouched, selectedPeriod]);

  function handlePeriodChange(nextPeriod: PortfolioChartPeriod): void {
    setSearchParams((previous) => {
      const next = new URLSearchParams(previous);
      next.set("period", nextPeriod);
      return next;
    });
  }

  async function generateQuantReport(): Promise<void> {
    const normalizedSymbol = reportInstrumentSymbol.trim().toUpperCase();
    if (reportScope === "instrument_symbol" && normalizedSymbol.length === 0) {
      setReportValidationError("Instrument symbol is required for instrument-scoped reports.");
      return;
    }

    setReportValidationError(null);
    setActiveReportId(null);
    const request: PortfolioQuantReportGenerateRequest = {
      scope: reportScope,
      instrument_symbol: reportScope === "instrument_symbol" ? normalizedSymbol : null,
      period: selectedPeriod,
    };

    try {
      const generatedReport = await quantReportGenerateMutation.mutateAsync(request);
      setActiveReportId(generatedReport.report_id);
    } catch {
      setActiveReportId(null);
    }
  }

  function applyMonteCarloProfile(profileId: MonteCarloProfileId): void {
    const profileFromResponse = resolveProfileScenarioById(
      monteCarloMutation.data?.profile_scenarios,
      profileId,
    );
    const profilePreset = MONTE_CARLO_PROFILE_PRESETS[profileId];
    const nextBustThreshold = profileFromResponse
      ? formatThresholdInputValue(profileFromResponse.bust_threshold)
      : profilePreset.bust;
    const nextGoalThreshold = profileFromResponse
      ? formatThresholdInputValue(profileFromResponse.goal_threshold)
      : profilePreset.goal;

    setMonteCarloBustThreshold(nextBustThreshold);
    setMonteCarloGoalThreshold(nextGoalThreshold);
    setMonteCarloValidationError(null);
  }

  async function runMonteCarloSimulation(): Promise<void> {
    const normalizedSymbol = reportInstrumentSymbol.trim().toUpperCase();
    if (reportScope === "instrument_symbol" && normalizedSymbol.length === 0) {
      setMonteCarloValidationError(
        "Instrument symbol is required for instrument-scoped simulation.",
      );
      return;
    }

    const parsedSims = Number(monteCarloSims);
    const parsedHorizonDays = Number(monteCarloHorizonDays);
    const parsedSeed = Number(monteCarloSeed);
    const periodMaxHorizon = MONTE_CARLO_MAX_HORIZON_BY_PERIOD[selectedPeriod];
    if (!Number.isInteger(parsedSims) || parsedSims < 250 || parsedSims > 5000) {
      setMonteCarloValidationError("Sims must be an integer between 250 and 5000.");
      return;
    }
    if (
      !Number.isInteger(parsedHorizonDays) ||
      parsedHorizonDays < 5 ||
      parsedHorizonDays > periodMaxHorizon
    ) {
      setMonteCarloValidationError(
        `For ${selectedPeriod} period, horizon days must be an integer between 5 and ${periodMaxHorizon} return days.`,
      );
      return;
    }
    if (
      !Number.isInteger(parsedSeed) ||
      parsedSeed < 0 ||
      parsedSeed > 2_147_483_647
    ) {
      setMonteCarloValidationError(
        "Seed must be an integer between 0 and 2,147,483,647.",
      );
      return;
    }

    const parsedBustThreshold = parseOptionalThreshold(monteCarloBustThreshold);
    if (parsedBustThreshold.kind === "invalid") {
      setMonteCarloValidationError(
        "Bust threshold must be a valid number or left empty.",
      );
      return;
    }
    const parsedGoalThreshold = parseOptionalThreshold(monteCarloGoalThreshold);
    if (parsedGoalThreshold.kind === "invalid") {
      setMonteCarloValidationError(
        "Goal threshold must be a valid number or left empty.",
      );
      return;
    }
    const bustThresholdValue =
      parsedBustThreshold.kind === "valid" ? parsedBustThreshold.value : null;
    const goalThresholdValue =
      parsedGoalThreshold.kind === "valid" ? parsedGoalThreshold.value : null;
    if (
      bustThresholdValue !== null &&
      goalThresholdValue !== null &&
      bustThresholdValue >= goalThresholdValue
    ) {
      setMonteCarloValidationError("Bust threshold must be lower than goal threshold.");
      return;
    }

    setMonteCarloValidationError(null);
    const request: PortfolioMonteCarloRequest = {
      scope: reportScope,
      instrument_symbol:
        reportScope === "instrument_symbol" ? normalizedSymbol : null,
      period: selectedPeriod,
      sims: parsedSims,
      horizon_days: parsedHorizonDays,
      bust_threshold: bustThresholdValue,
      goal_threshold: goalThresholdValue,
      seed: parsedSeed,
      enable_profile_comparison: monteCarloProfileComparisonEnabled,
      calibration_basis: monteCarloCalibrationBasis,
    };

    try {
      await monteCarloMutation.mutateAsync(request);
    } catch {
      return;
    }
  }

  const quantMetricCards = quantMetricsQuery.isSuccess
    ? buildQuantMetricCards(quantMetricsQuery.data.metrics)
    : [];
  const contributionFocus =
    contributionQuery.isSuccess && contributionQuery.data.rows.length > 0
      ? buildContributionRows(contributionQuery.data.rows)
      : null;

  const quantBenchmarkContext = quantMetricsQuery.data?.benchmark_context;
  const omittedMetricIds = quantBenchmarkContext?.omitted_metric_ids || [];
  const omittedMetricsSummary = omittedMetricIds.length > 0 ? omittedMetricIds.join(", ") : "";
  const quantLensMetricIds = [
    "sharpe",
    "sortino",
    "calmar",
    "volatility",
    "max_drawdown",
    "win_rate",
  ];
  const quantMetricsByPeriod: Record<string, PortfolioQuantMetric[]> = {
    "30D": quantMetrics30Query.data?.metrics || [],
    "90D": quantMetrics90Query.data?.metrics || [],
    "252D": quantMetrics252Query.data?.metrics || [],
  };
  const quantLensRows = quantLensMetricIds.map((metricId) => {
    const metric30 = quantMetricsByPeriod["30D"].find((metric) => metric.metric_id === metricId);
    const metric90 = quantMetricsByPeriod["90D"].find((metric) => metric.metric_id === metricId);
    const metric252 = quantMetricsByPeriod["252D"].find((metric) => metric.metric_id === metricId);
    return {
      metricId,
      label: metric90?.label || metric252?.label || metric30?.label || metricId,
      v30: formatQuantLensMetricValue(metric30),
      v90: formatQuantLensMetricValue(metric90),
      v252: formatQuantLensMetricValue(metric252),
    };
  });

  let reportLifecycleState: ReportLifecycleUiState = "unavailable";
  if (reportValidationError) {
    reportLifecycleState = "invalid_request";
  } else if (quantReportGenerateMutation.isPending || quantReportHtmlQuery.isLoading) {
    reportLifecycleState = "loading";
  } else if (quantReportGenerateMutation.isError) {
    reportLifecycleState = "error";
  } else if (quantReportHtmlQuery.isError) {
    reportLifecycleState = quantReportPreviewErrorCopy.variant === "warning" ? "unavailable" : "error";
  } else if (quantReportHtmlQuery.isSuccess) {
    reportLifecycleState = "ready";
  } else if (quantReportGenerateMutation.data?.lifecycle_status === "ready") {
    reportLifecycleState = "ready";
  } else if (quantReportGenerateMutation.data?.lifecycle_status === "unavailable") {
    reportLifecycleState = "unavailable";
  }

  const lifecyclePillToneClass =
    reportLifecycleState === "ready"
      ? "status-pill--positive"
      : reportLifecycleState === "error"
        ? "status-pill--negative"
        : "status-pill--neutral";

  const lifecycleLabelMap: Record<ReportLifecycleUiState, string> = {
    invalid_request: "invalid request",
    loading: "loading",
    ready: "ready",
    unavailable: "unavailable",
    error: "error",
  };
  const lifecycleStepStatuses = {
    requested:
      reportLifecycleState === "loading" ||
      reportLifecycleState === "ready" ||
      reportLifecycleState === "unavailable",
    generated:
      reportLifecycleState === "ready" ||
      (quantReportGenerateMutation.data?.lifecycle_status === "ready" &&
        reportLifecycleState !== "error"),
    preview:
      reportLifecycleState === "ready" && quantReportHtmlQuery.isSuccess,
  };

  let monteCarloLifecycleState: MonteCarloLifecycleUiState = "unavailable";
  if (monteCarloValidationError) {
    monteCarloLifecycleState = "invalid_request";
  } else if (monteCarloMutation.isPending) {
    monteCarloLifecycleState = "loading";
  } else if (monteCarloMutation.isError) {
    monteCarloLifecycleState = "error";
  } else if (monteCarloMutation.isSuccess) {
    monteCarloLifecycleState = "ready";
  }

  const monteCarloLifecycleLabelMap: Record<MonteCarloLifecycleUiState, string> = {
    invalid_request: "invalid request",
    loading: "loading",
    ready: "ready",
    unavailable: "unavailable",
    error: "error",
  };
  const monteCarloLifecycleToneClass =
    monteCarloLifecycleState === "ready"
      ? "status-pill--positive"
      : monteCarloLifecycleState === "error"
        ? "status-pill--negative"
        : "status-pill--neutral";
  const monteCarloP5 = monteCarloMutation.data?.ending_return_percentiles.find(
    (point) => point.percentile === 5,
  );
  const monteCarloP50 = monteCarloMutation.data?.ending_return_percentiles.find(
    (point) => point.percentile === 50,
  );
  const monteCarloP95 = monteCarloMutation.data?.ending_return_percentiles.find(
    (point) => point.percentile === 95,
  );
  const monteCarloRecommendedHorizonDays =
    MONTE_CARLO_RECOMMENDED_HORIZON_BY_PERIOD[selectedPeriod];
  const monteCarloMaxHorizonDays = MONTE_CARLO_MAX_HORIZON_BY_PERIOD[selectedPeriod];
  const monteCarloP5Ratio = toFiniteRatio(monteCarloP5?.value);
  const monteCarloP50Ratio = toFiniteRatio(monteCarloP50?.value);
  const monteCarloP95Ratio = toFiniteRatio(monteCarloP95?.value);
  const monteCarloBustThresholdRatio = toFiniteRatio(
    monteCarloMutation.data?.simulation.bust_threshold ?? null,
  );
  const monteCarloGoalThresholdRatio = toFiniteRatio(
    monteCarloMutation.data?.simulation.goal_threshold ?? null,
  );
  const monteCarloBustProbabilityRatio = toFiniteRatio(
    monteCarloMutation.data?.summary.bust_probability ?? null,
  );
  const monteCarloGoalProbabilityRatio = toFiniteRatio(
    monteCarloMutation.data?.summary.goal_probability ?? null,
  );
  const monteCarloSignal = (
    monteCarloMutation.data?.summary.interpretation_signal ??
    resolveMonteCarloSignalLabel(
      monteCarloBustProbabilityRatio,
      monteCarloGoalProbabilityRatio,
    )
  ) as MonteCarloSignal;
  const monteCarloSignalLabel = formatMonteCarloSignalLabel(monteCarloSignal);
  const monteCarloScopeNarrative = monteCarloMutation.data
    ? formatScopeNarrative(
        monteCarloMutation.data.scope,
        monteCarloMutation.data.instrument_symbol,
        monteCarloMutation.data.period,
        monteCarloMutation.data.simulation.horizon_days,
      )
    : null;
  const monteCarloPercentileSpread =
    monteCarloP5Ratio !== null && monteCarloP95Ratio !== null
      ? Math.abs(monteCarloP95Ratio - monteCarloP5Ratio)
      : null;
  const monteCarloPercentilesCollapsed =
    monteCarloPercentileSpread !== null && monteCarloPercentileSpread < 0.0001;
  const monteCarloEnvelopeValues = [
    monteCarloP5Ratio,
    monteCarloP50Ratio,
    monteCarloP95Ratio,
    monteCarloBustThresholdRatio,
    monteCarloGoalThresholdRatio,
  ].filter((value): value is number => value !== null);
  const monteCarloEnvelopeDomainMin =
    monteCarloEnvelopeValues.length > 0
      ? Math.min(-0.35, ...monteCarloEnvelopeValues) - 0.03
      : -0.4;
  const monteCarloEnvelopeDomainMax =
    monteCarloEnvelopeValues.length > 0
      ? Math.max(0.35, ...monteCarloEnvelopeValues) + 0.03
      : 0.4;
  const monteCarloEnvelopeDomainSpan = Math.max(
    0.1,
    monteCarloEnvelopeDomainMax - monteCarloEnvelopeDomainMin,
  );

  function resolveEnvelopePosition(value: number | null): number | null {
    if (value === null) {
      return null;
    }
    const normalized =
      ((value - monteCarloEnvelopeDomainMin) / monteCarloEnvelopeDomainSpan) * 100;
    return Math.max(0, Math.min(100, normalized));
  }

  const monteCarloP5Position = resolveEnvelopePosition(monteCarloP5Ratio);
  const monteCarloP50Position = resolveEnvelopePosition(monteCarloP50Ratio);
  const monteCarloP95Position = resolveEnvelopePosition(monteCarloP95Ratio);
  const monteCarloBustThresholdPosition = resolveEnvelopePosition(
    monteCarloBustThresholdRatio,
  );
  const monteCarloGoalThresholdPosition = resolveEnvelopePosition(
    monteCarloGoalThresholdRatio,
  );
  const monteCarloRangeLeft =
    monteCarloP5Position !== null && monteCarloP95Position !== null
      ? Math.min(monteCarloP5Position, monteCarloP95Position)
      : null;
  const monteCarloRangeWidth =
    monteCarloP5Position !== null && monteCarloP95Position !== null
      ? Math.max(2, Math.abs(monteCarloP95Position - monteCarloP5Position))
      : null;
  const monteCarloProfileRows = (
    ["conservative", "balanced", "growth"] as const
  )
    .map((profileId) =>
      resolveProfileScenarioById(
        monteCarloMutation.data?.profile_scenarios,
        profileId,
      ),
    )
    .filter((profile): profile is PortfolioMonteCarloProfileScenario => profile !== null);
  const monteCarloCalibrationBasisLabel = monteCarloMutation.data
    ? formatCalibrationBasisLabel(
        monteCarloMutation.data.calibration_context.effective_basis as MonteCarloCalibrationBasis,
      )
    : formatCalibrationBasisLabel(monteCarloCalibrationBasis);

  return (
    <PortfolioWorkspaceLayout
      eyebrow="Quant/Reports route"
      title="Quant diagnostics and report lifecycle"
      description="Dedicated analytical surface for QuantStats diagnostics, report lifecycle states, and deterministic artifact access."
      actions={
        <>
          <PortfolioChartPeriodControl
            value={selectedPeriod}
            onChange={handlePeriodChange}
          />
          <Link className="button-secondary" to="/portfolio/home">
            Back to home
          </Link>
        </>
      }
      freshnessTimestamp={
        quantMetricsQuery.data?.as_of_ledger_at || timeSeriesQuery.data?.as_of_ledger_at
      }
      scopeLabel="Quant diagnostics + report artifact lifecycle"
      provenanceLabel={
        quantMetricsQuery.data?.benchmark_symbol || "QuantStats + persisted analytics APIs"
      }
      periodLabel={selectedPeriod}
      frequencyLabel={timeSeriesQuery.data?.frequency}
      timezoneLabel={timeSeriesQuery.data?.timezone}
    >
      <WorkspaceChartPanel
        title="Quant scorecards"
        subtitle="Analyst diagnostics with explicit benchmark-context omission handling."
        shortDescription="Primary diagnostics for risk-adjusted performance interpretation."
        longDescription="Interpret these metrics together; isolated values can be misleading when period coverage or benchmark context is incomplete."
      >
        {quantMetricsQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}

        {quantMetricsQuery.isError ? (
          <ErrorBanner
            title={quantErrorCopy.title}
            message={quantErrorCopy.message}
            variant={quantErrorCopy.variant}
            actions={
              <button
                className="button-primary"
                onClick={() => void quantMetricsQuery.refetch()}
                type="button"
              >
                Retry quant diagnostics
              </button>
            }
          />
        ) : null}

        {quantMetricsQuery.isSuccess && quantMetricCards.length === 0 ? (
          <EmptyState
            title="No quant diagnostics for selected period"
            message="The quant endpoint returned no metrics for this period."
          />
        ) : null}

        {quantMetricsQuery.isSuccess && quantMetricCards.length > 0 ? (
          <>
            {omittedMetricIds.length > 0 ? (
              <section className="context-banner context-banner--info" aria-live="polite">
                <h3 className="context-banner__title">Benchmark context partially unavailable</h3>
                <p className="context-banner__copy">
                  {quantBenchmarkContext?.omission_reason
                    ? `${quantBenchmarkContext.omission_reason} Omitted: ${omittedMetricsSummary}.`
                    : `Optional benchmark metrics were omitted for this request: ${omittedMetricsSummary}.`}
                </p>
              </section>
            ) : null}

            <div className="overview-grid">
              {quantMetricCards.map((metric) => (
                <article className="overview-card" key={metric.label}>
                  <div className="overview-card__meta">
                    <span className="overview-card__label">{metric.label}</span>
                    <MetricExplainabilityPopover
                      label={metric.label}
                      shortDefinition={metric.explainability.shortDefinition}
                      whyItMatters={metric.explainability.whyItMatters}
                      interpretation={metric.explainability.interpretation}
                      formulaOrBasis={metric.explainability.formulaOrBasis}
                      comparisonContext={metric.explainability.comparisonContext}
                      caveats={metric.explainability.caveats}
                      currentContextNote={metric.explainability.currentContextNote}
                    />
                  </div>
                  <strong className={`overview-card__value tone-${metric.tone}`}>
                    {metric.value}
                  </strong>
                  <p className="overview-card__copy">{metric.hint}</p>
                </article>
              ))}
            </div>

            <table className="quant-lens-table" aria-label="Quant period lens">
              <thead>
                <tr className="quant-lens-table__header">
                  <th scope="col">Metric</th>
                  <th className="numeric" scope="col">
                    30D
                  </th>
                  <th className="numeric" scope="col">
                    90D
                  </th>
                  <th className="numeric" scope="col">
                    252D
                  </th>
                </tr>
              </thead>
              <tbody>
                {quantLensRows.map((row) => (
                  <tr className="quant-lens-table__row" key={row.metricId}>
                    <th className="quant-lens-table__metric" scope="row">
                      {row.label}
                    </th>
                    <td className="quant-lens-table__value numeric">{row.v30}</td>
                    <td className="quant-lens-table__value numeric">{row.v90}</td>
                    <td className="quant-lens-table__value numeric">{row.v252}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Quant report lifecycle"
        subtitle="Loading, error, unavailable, and ready states are explicit and keyboard reachable."
        shortDescription="Generate and preview report artifacts from one stable action surface."
        longDescription="Report actions are persistent here; no workflow actions are hidden inside transient chart tooltips."
      >
        <div className="quant-lifecycle-controls">
          <div className="quant-lifecycle-controls__row">
            <div className="transactions-filters transactions-filters--compact">
              <label className="transactions-filters__field">
                <span>Report scope</span>
                <select
                  aria-label="Report scope"
                  className="transactions-filters__select"
                  onChange={(event) => {
                    setReportScope(event.target.value as PortfolioQuantReportScope);
                    setReportValidationError(null);
                  }}
                  value={reportScope}
                >
                  <option value="portfolio">Portfolio</option>
                  <option value="instrument_symbol">Instrument</option>
                </select>
              </label>
              {reportScope === "instrument_symbol" ? (
                <label className="transactions-filters__field">
                  <span>Instrument symbol</span>
                  <input
                    className="transactions-filters__input"
                    list="quant-report-symbols"
                    onChange={(event) => {
                      setReportInstrumentSymbol(event.target.value.toUpperCase());
                      setReportValidationError(null);
                    }}
                    placeholder="AAPL"
                    value={reportInstrumentSymbol}
                  />
                  <datalist id="quant-report-symbols">
                    {availableInstrumentSymbols.map((symbol) => (
                      <option key={symbol} value={symbol} />
                    ))}
                  </datalist>
                </label>
              ) : null}
            </div>

            <button
              className={`button-primary ${quantReportGenerateMutation.isPending ? "button-primary--loading" : ""}`}
              disabled={quantReportGenerateMutation.isPending}
              onClick={() => void generateQuantReport()}
              type="button"
            >
              {quantReportGenerateMutation.isPending ? (
                <span className="button-spinner" aria-hidden="true" />
              ) : null}
              {quantReportGenerateMutation.isPending ? "Generating report..." : "Generate HTML report"}
            </button>
          </div>

          <div className="quant-lifecycle-controls__meta">
            <div className="lifecycle-pill-row" role="status" aria-live="polite">
              <span className={`status-pill ${lifecyclePillToneClass}`}>
                Lifecycle: {lifecycleLabelMap[reportLifecycleState]}
              </span>
            </div>

            <ol className="lifecycle-stepper" aria-label="Quant report lifecycle steps">
              <li className={`lifecycle-stepper__step ${lifecycleStepStatuses.requested ? "is-active" : ""}`}>
                Requested
              </li>
              <li className={`lifecycle-stepper__step ${lifecycleStepStatuses.generated ? "is-active" : ""}`}>
                Generated
              </li>
              <li className={`lifecycle-stepper__step ${lifecycleStepStatuses.preview ? "is-active" : ""}`}>
                Preview ready
              </li>
            </ol>
          </div>
        </div>

        {reportLifecycleState === "invalid_request" && reportValidationError ? (
          <ErrorBanner
            title="Report lifecycle: invalid request"
            message={reportValidationError}
            variant="warning"
          />
        ) : null}

        {reportLifecycleState === "error" ? (
          <ErrorBanner
            title={
              quantReportGenerateMutation.isError
                ? quantReportGenerateErrorCopy.title
                : quantReportPreviewErrorCopy.title
            }
            message={
              quantReportGenerateMutation.isError
                ? quantReportGenerateErrorCopy.message
                : quantReportPreviewErrorCopy.message
            }
            variant={
              quantReportGenerateMutation.isError
                ? quantReportGenerateErrorCopy.variant
                : quantReportPreviewErrorCopy.variant
            }
            actions={
              quantReportGenerateMutation.isError ? undefined : (
                <button
                  className="button-primary"
                  onClick={() => void quantReportHtmlQuery.refetch()}
                  type="button"
                >
                  Retry report preview
                </button>
              )
            }
          />
        ) : null}

        {quantReportGenerateMutation.data ? (
          <div className="chart-summary-grid quant-report-summary-grid">
            <article className="chart-summary-card">
              <span className="chart-summary-card__label">Scope</span>
              <strong className="chart-summary-card__value">
                {quantReportGenerateMutation.data.scope}
              </strong>
              <p className="chart-summary-card__copy">Period {quantReportGenerateMutation.data.period}</p>
            </article>
            <article className="chart-summary-card chart-summary-card--accent">
              <span className="chart-summary-card__label">Lifecycle status</span>
              <strong className="chart-summary-card__value">
                {quantReportGenerateMutation.data.lifecycle_status}
              </strong>
              <p className="chart-summary-card__copy">Report id {quantReportGenerateMutation.data.report_id}</p>
            </article>
            <article className="chart-summary-card chart-summary-card--signal">
              <span className="chart-summary-card__label">Artifact</span>
              <a
                className="row-link quant-report-summary-grid__artifact-link"
                href={quantReportGenerateMutation.data.report_url_path}
                rel="noreferrer"
                target="_blank"
              >
                Open full HTML report
              </a>
            </article>
          </div>
        ) : null}

        {reportLifecycleState === "loading" ? (
          <div className="quant-report-preview quant-report-preview--loading" role="status" aria-live="polite">
            <span className="quant-report-preview__pulse" />
            <p>Report metadata is ready; loading HTML artifact preview.</p>
          </div>
        ) : null}

        {reportLifecycleState === "unavailable" && quantReportHtmlQuery.isError ? (
          <ErrorBanner
            title={quantReportPreviewErrorCopy.title}
            message={quantReportPreviewErrorCopy.message}
            variant={quantReportPreviewErrorCopy.variant}
            actions={
              <button
                className="button-primary"
                onClick={() => void quantReportHtmlQuery.refetch()}
                type="button"
              >
                Retry report preview
              </button>
            }
          />
        ) : null}

        {reportLifecycleState === "ready" && quantReportHtmlQuery.isSuccess ? (
          <iframe
            className="quant-report-preview"
            srcDoc={quantReportHtmlQuery.data}
            title="Quant report HTML preview"
          />
        ) : null}

        {reportLifecycleState === "unavailable" && !quantReportHtmlQuery.isError ? (
          <EmptyState
            title="Report lifecycle: unavailable"
            message="Generate a report to create a previewable artifact for this period and scope."
          />
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Monte Carlo diagnostics"
        subtitle="Bounded QuantStats simulation controls with explicit workflow states."
        shortDescription="Scenario module for probability context under deterministic seed and bounded simulation envelope."
        longDescription="Monte Carlo diagnostics shuffle historical returns and do not forecast markets. Use these outputs for scenario awareness, not prediction certainty."
      >
        <div className="monte-carlo-form">
          <div className="monte-carlo-form__control-row">
            <label className="monte-carlo-form__toggle">
              <input
                aria-label="Enable profile compare"
                checked={monteCarloProfileComparisonEnabled}
                onChange={(event) => {
                  setMonteCarloProfileComparisonEnabled(event.target.checked);
                }}
                type="checkbox"
              />
              <span>Enable profile compare</span>
            </label>
            <label className="monte-carlo-form__basis">
              <span className="monte-carlo-form__label">Calibration basis</span>
              <select
                aria-label="Calibration basis"
                className="transactions-filters__select"
                onChange={(event) => {
                  setMonteCarloCalibrationBasis(
                    event.target.value as MonteCarloCalibrationBasis,
                  );
                }}
                value={monteCarloCalibrationBasis}
              >
                <option value="monthly">Monthly (recommended)</option>
                <option value="annual">Annual</option>
                <option value="manual">Manual</option>
              </select>
            </label>
          </div>
          <div className="monte-carlo-form__profile-actions">
            <span className="monte-carlo-form__label">Apply profile</span>
            <div className="monte-carlo-form__profile-buttons">
              <button
                className="button-secondary"
                onClick={() => applyMonteCarloProfile("conservative")}
                type="button"
              >
                Apply profile Conservative
              </button>
              <button
                className="button-secondary"
                onClick={() => applyMonteCarloProfile("balanced")}
                type="button"
              >
                Apply profile Balanced
              </button>
              <button
                className="button-secondary"
                onClick={() => applyMonteCarloProfile("growth")}
                type="button"
              >
                Apply profile Growth
              </button>
            </div>
          </div>
          <div className="monte-carlo-form__grid">
            <label className="monte-carlo-form__field">
              <span className="monte-carlo-form__label">Sims</span>
              <input
                aria-label="Simulation count"
                className="transactions-filters__input monte-carlo-form__input"
                inputMode="numeric"
                onChange={(event) => setMonteCarloSims(event.target.value)}
                value={monteCarloSims}
              />
              <span className="monte-carlo-form__meta">Envelope: 250 to 5000 runs</span>
            </label>
            <label className="monte-carlo-form__field">
              <span className="monte-carlo-form__label">Horizon days</span>
              <input
                aria-label="Simulation horizon days"
                className="transactions-filters__input monte-carlo-form__input"
                inputMode="numeric"
                onChange={(event) => {
                  setMonteCarloHorizonDays(event.target.value);
                  setMonteCarloHorizonTouched(true);
                }}
                value={monteCarloHorizonDays}
              />
              <span className="monte-carlo-form__meta">
                Suggested {monteCarloRecommendedHorizonDays}D · Max {monteCarloMaxHorizonDays}D
                for {selectedPeriod}
              </span>
            </label>
            <label className="monte-carlo-form__field">
              <span className="monte-carlo-form__label">Bust threshold</span>
              <input
                aria-label="Bust threshold"
                className="transactions-filters__input monte-carlo-form__input"
                onChange={(event) => setMonteCarloBustThreshold(event.target.value)}
                value={monteCarloBustThreshold}
              />
              <span className="monte-carlo-form__meta">Downside trigger (ratio, e.g. -0.20)</span>
            </label>
            <label className="monte-carlo-form__field">
              <span className="monte-carlo-form__label">Goal threshold</span>
              <input
                aria-label="Goal threshold"
                className="transactions-filters__input monte-carlo-form__input"
                onChange={(event) => setMonteCarloGoalThreshold(event.target.value)}
                value={monteCarloGoalThreshold}
              />
              <span className="monte-carlo-form__meta">Target trigger (ratio, e.g. 0.30)</span>
            </label>
            <label className="monte-carlo-form__field">
              <span className="monte-carlo-form__label">Seed</span>
              <input
                aria-label="Simulation seed"
                className="transactions-filters__input monte-carlo-form__input"
                inputMode="numeric"
                onChange={(event) => setMonteCarloSeed(event.target.value)}
                value={monteCarloSeed}
              />
              <span className="monte-carlo-form__meta">Deterministic replay for same inputs</span>
            </label>
          </div>
          <div className="monte-carlo-form__actions">
            <button
              className="button-secondary"
              onClick={() => {
                setMonteCarloHorizonTouched(false);
                setMonteCarloHorizonDays(String(monteCarloRecommendedHorizonDays));
              }}
              type="button"
            >
              Use suggested horizon ({monteCarloRecommendedHorizonDays}D)
            </button>
          </div>
        </div>

        <section className="context-banner context-banner--info">
          <h3 className="context-banner__title">Profile guide</h3>
          <p className="context-banner__copy">
            Conservative favors tighter drawdown limits, Balanced tracks central thresholds,
            and Growth allows wider downside for higher upside triggers.
          </p>
        </section>

        <div className="status-banner__actions">
          <button
            className={`button-primary ${monteCarloMutation.isPending ? "button-primary--loading" : ""}`}
            disabled={monteCarloMutation.isPending}
            onClick={() => void runMonteCarloSimulation()}
            type="button"
          >
            {monteCarloMutation.isPending ? (
              <span className="button-spinner" aria-hidden="true" />
            ) : null}
            {monteCarloMutation.isPending
              ? "Running simulation..."
              : "Run Monte Carlo simulation"}
          </button>
        </div>

        <div className="lifecycle-pill-row" role="status" aria-live="polite">
          <span className={`status-pill ${monteCarloLifecycleToneClass}`}>
            Simulation lifecycle: {monteCarloLifecycleLabelMap[monteCarloLifecycleState]}
          </span>
        </div>

        {monteCarloLifecycleState === "invalid_request" && monteCarloValidationError ? (
          <ErrorBanner
            title="Simulation lifecycle: invalid request"
            message={monteCarloValidationError}
            variant="warning"
          />
        ) : null}

        {monteCarloLifecycleState === "loading" ? (
          <div className="quant-report-preview quant-report-preview--loading" role="status" aria-live="polite">
            <span className="quant-report-preview__pulse" />
            <p>Running bounded QuantStats Monte Carlo scenarios.</p>
          </div>
        ) : null}

        {monteCarloLifecycleState === "error" ? (
          <ErrorBanner
            title={monteCarloErrorCopy.title}
            message={monteCarloErrorCopy.message}
            variant={monteCarloErrorCopy.variant}
          />
        ) : null}

        {monteCarloLifecycleState === "ready" && monteCarloMutation.data ? (
          <>
            <div className="chart-summary-grid">
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Simulation scope</span>
                <strong className="chart-summary-card__headline">
                  {monteCarloMutation.data.scope === "instrument_symbol" &&
                  monteCarloMutation.data.instrument_symbol
                    ? monteCarloMutation.data.instrument_symbol
                    : "Portfolio"}
                </strong>
                <p className="chart-summary-card__copy">
                  {monteCarloScopeNarrative}
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--accent">
                <span className="chart-summary-card__label">Threshold guardrails</span>
                <strong className="chart-summary-card__headline">
                  {formatRatioPercent(monteCarloMutation.data.simulation.bust_threshold)} /{" "}
                  {formatRatioPercent(monteCarloMutation.data.simulation.goal_threshold)}
                </strong>
                <p className="chart-summary-card__copy">
                  Bust vs goal return thresholds for this run.
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--signal">
                <span className="chart-summary-card__label">Interpretation signal</span>
                <strong className="chart-summary-card__headline">{monteCarloSignalLabel}</strong>
                <p className="chart-summary-card__copy">
                  Uses bust and goal probabilities as quick decision context.
                </p>
              </article>
            </div>

            {monteCarloMutation.data.profile_comparison_enabled &&
            monteCarloProfileRows.length > 0 ? (
              <section className="monte-carlo-profile-matrix" aria-live="polite">
                <header className="monte-carlo-profile-matrix__header">
                  <h3 className="monte-carlo-profile-matrix__title">
                    Profile scenario comparison
                  </h3>
                  <p className="monte-carlo-profile-matrix__meta">
                    Calibration basis: {monteCarloCalibrationBasisLabel}
                  </p>
                </header>
                <div className="monte-carlo-profile-matrix__table" role="table" aria-label="Profile scenario comparison">
                  <div className="monte-carlo-profile-matrix__row monte-carlo-profile-matrix__row--header" role="row">
                    <span role="columnheader">Profile</span>
                    <span role="columnheader">Thresholds</span>
                    <span role="columnheader">Bust prob.</span>
                    <span role="columnheader">Goal prob.</span>
                    <span role="columnheader">Signal</span>
                  </div>
                  {monteCarloProfileRows.map((profileRow) => (
                    <div
                      className="monte-carlo-profile-matrix__row"
                      data-testid="monte-carlo-profile-row"
                      key={profileRow.profile_id}
                      role="row"
                    >
                      <span role="cell">{profileRow.label}</span>
                      <span role="cell">
                        {formatRatioPercent(profileRow.bust_threshold)} /{" "}
                        {formatRatioPercent(profileRow.goal_threshold)}
                      </span>
                      <span role="cell">{formatBoundedPercent(profileRow.bust_probability)}</span>
                      <span role="cell">{formatBoundedPercent(profileRow.goal_probability)}</span>
                      <span role="cell">
                        {formatMonteCarloSignalLabel(
                          profileRow.interpretation_signal as MonteCarloSignal,
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            <div className="monte-carlo-envelope" role="img" aria-label="Monte Carlo outcome envelope">
              <div className="monte-carlo-envelope__track">
                {monteCarloRangeLeft !== null && monteCarloRangeWidth !== null ? (
                  <span
                    aria-hidden="true"
                    className="monte-carlo-envelope__range"
                    style={{
                      left: `${monteCarloRangeLeft}%`,
                      width: `${monteCarloRangeWidth}%`,
                    }}
                  />
                ) : null}
                {monteCarloBustThresholdPosition !== null ? (
                  <span
                    aria-hidden="true"
                    className="monte-carlo-envelope__marker monte-carlo-envelope__marker--bust"
                    style={{ left: `${monteCarloBustThresholdPosition}%` }}
                  />
                ) : null}
                {monteCarloP50Position !== null ? (
                  <span
                    aria-hidden="true"
                    className="monte-carlo-envelope__marker monte-carlo-envelope__marker--median"
                    style={{ left: `${monteCarloP50Position}%` }}
                  />
                ) : null}
                {monteCarloGoalThresholdPosition !== null ? (
                  <span
                    aria-hidden="true"
                    className="monte-carlo-envelope__marker monte-carlo-envelope__marker--goal"
                    style={{ left: `${monteCarloGoalThresholdPosition}%` }}
                  />
                ) : null}
              </div>
              <div className="monte-carlo-envelope__legend">
                <span>
                  Bust {formatRatioPercent(monteCarloMutation.data.simulation.bust_threshold)}
                </span>
                <span>P50 {formatRatioPercent(monteCarloP50?.value, { signed: true })}</span>
                <span>
                  Goal {formatRatioPercent(monteCarloMutation.data.simulation.goal_threshold)}
                </span>
              </div>
            </div>

            <div className="monte-carlo-probabilities" aria-label="Simulation probability bars">
              <div className="monte-carlo-probabilities__row">
                <div className="monte-carlo-probabilities__label-group">
                  <span className="monte-carlo-probabilities__label">Bust probability</span>
                  <strong className="monte-carlo-probabilities__value">
                    {formatBoundedPercent(monteCarloMutation.data.summary.bust_probability)}
                  </strong>
                </div>
                <div className="monte-carlo-probabilities__track" aria-hidden="true">
                  <span
                    className="monte-carlo-probabilities__fill monte-carlo-probabilities__fill--negative"
                    style={{
                      width: `${Math.max(
                        0,
                        Math.min(
                          100,
                          (monteCarloBustProbabilityRatio ?? 0) * 100,
                        ),
                      )}%`,
                    }}
                  />
                </div>
              </div>
              <div className="monte-carlo-probabilities__row">
                <div className="monte-carlo-probabilities__label-group">
                  <span className="monte-carlo-probabilities__label">Goal probability</span>
                  <strong className="monte-carlo-probabilities__value">
                    {formatBoundedPercent(monteCarloMutation.data.summary.goal_probability)}
                  </strong>
                </div>
                <div className="monte-carlo-probabilities__track" aria-hidden="true">
                  <span
                    className="monte-carlo-probabilities__fill monte-carlo-probabilities__fill--positive"
                    style={{
                      width: `${Math.max(
                        0,
                        Math.min(
                          100,
                          (monteCarloGoalProbabilityRatio ?? 0) * 100,
                        ),
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </div>

            {monteCarloPercentilesCollapsed ? (
              <section className="context-banner context-banner--info" aria-live="polite">
                <h3 className="context-banner__title">Terminal percentile spread collapsed</h3>
                <p className="context-banner__copy">
                  QuantStats shuffled-return runs can converge at the terminal step for this horizon.
                  Use bust and goal probabilities with drawdown context for decision support.
                </p>
              </section>
            ) : null}

            <div className="chart-summary-grid">
              <article className="chart-summary-card">
                <div className="overview-card__meta">
                  <span className="chart-summary-card__label">P5 ending return</span>
                  <MetricExplainabilityPopover
                    label="P5 ending return"
                    shortDefinition="5th percentile of simulated ending returns."
                    whyItMatters="Represents a pessimistic but plausible downside tail outcome."
                    interpretation="Lower values indicate deeper downside in adverse simulation paths."
                    formulaOrBasis="Quantile 5 of terminal cumulative return distribution."
                    comparisonContext="Compare against bust threshold and max drawdown tolerance."
                    caveats="Simulation shuffles historical returns and is not predictive."
                    currentContextNote={`Current P5 is ${formatRatioPercent(monteCarloP5?.value, { signed: true })}.`}
                  />
                </div>
                <strong className="chart-summary-card__headline">
                  {formatRatioPercent(monteCarloP5?.value, { signed: true })}
                </strong>
                <p className="chart-summary-card__copy">Lower-tail simulation percentile.</p>
              </article>
              <article className="chart-summary-card chart-summary-card--signal">
                <div className="overview-card__meta">
                  <span className="chart-summary-card__label">P50 ending return</span>
                  <MetricExplainabilityPopover
                    label="P50 ending return"
                    shortDefinition="Median simulated ending return."
                    whyItMatters="Central scenario outcome across bounded simulation paths."
                    interpretation="Represents midpoint scenario where half paths end above and half below."
                    formulaOrBasis="Quantile 50 of terminal cumulative return distribution."
                    comparisonContext="Compare with realized period return and benchmark-relative spread."
                    caveats="Path-order dependencies are removed by shuffled-return simulation."
                    currentContextNote={`Current P50 is ${formatRatioPercent(monteCarloP50?.value, { signed: true })}.`}
                  />
                </div>
                <strong className="chart-summary-card__headline">
                  {formatRatioPercent(monteCarloP50?.value, { signed: true })}
                </strong>
                <p className="chart-summary-card__copy">Median scenario outcome.</p>
              </article>
              <article className="chart-summary-card chart-summary-card--accent">
                <div className="overview-card__meta">
                  <span className="chart-summary-card__label">P95 ending return</span>
                  <MetricExplainabilityPopover
                    label="P95 ending return"
                    shortDefinition="95th percentile of simulated ending returns."
                    whyItMatters="Optimistic tail outcome under bounded scenario assumptions."
                    interpretation="Higher values indicate stronger upside tail potential."
                    formulaOrBasis="Quantile 95 of terminal cumulative return distribution."
                    comparisonContext="Compare against goal threshold to assess upside likelihood."
                    caveats="Tail outcomes are sensitive to available history and chosen horizon."
                    currentContextNote={`Current P95 is ${formatRatioPercent(monteCarloP95?.value, { signed: true })}.`}
                  />
                </div>
                <strong className="chart-summary-card__headline">
                  {formatRatioPercent(monteCarloP95?.value, { signed: true })}
                </strong>
                <p className="chart-summary-card__copy">Upper-tail scenario percentile.</p>
              </article>
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Bust probability</span>
                <strong className="chart-summary-card__headline">
                  {formatBoundedPercent(monteCarloMutation.data.summary.bust_probability)}
                </strong>
                <p className="chart-summary-card__copy">
                  Probability of breaching configured bust threshold.
                </p>
              </article>
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Goal probability</span>
                <strong className="chart-summary-card__headline">
                  {formatBoundedPercent(monteCarloMutation.data.summary.goal_probability)}
                </strong>
                <p className="chart-summary-card__copy">
                  Probability of reaching configured goal threshold.
                </p>
              </article>
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Median ending value</span>
                <strong className="chart-summary-card__headline">
                  {formatUsdMoney(
                    monteCarloMutation.data.summary.median_ending_value_usd,
                  )}
                </strong>
                <p className="chart-summary-card__copy">
                  Median ending value from selected simulations.
                </p>
              </article>
            </div>
          </>
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Monthly return heatmap"
        subtitle="Calendar-heatmap style rhythm view for period returns."
        shortDescription="Pattern-first module to spot recurring positive/negative months quickly."
        longDescription="Heatmap values are derived from available period points and should be paired with precise metric cards for decisions."
      >
        <div className="transactions-filters">
          <label className="transactions-filters__field">
            <span>Heatmap scope</span>
            <select
              aria-label="Heatmap scope"
              className="transactions-filters__select"
              onChange={(event) => {
                setHeatmapScope(event.target.value as PortfolioTimeSeriesScope);
              }}
              value={heatmapScope}
            >
              <option value="portfolio">Portfolio</option>
              <option value="instrument_symbol">Instrument</option>
            </select>
          </label>
          {heatmapScope === "instrument_symbol" ? (
            <label className="transactions-filters__field">
              <span>Heatmap instrument symbol</span>
              <select
                aria-label="Heatmap instrument symbol"
                className="transactions-filters__select"
                onChange={(event) => {
                  setHeatmapInstrumentSymbol(event.target.value);
                }}
                value={heatmapInstrumentSymbol}
              >
                {availableInstrumentSymbols.length === 0 ? (
                  <option value="">No symbols available</option>
                ) : null}
                {availableInstrumentSymbols.map((symbol) => (
                  <option key={symbol} value={symbol}>
                    {symbol}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
        </div>

        {heatmapScope === "instrument_symbol" && availableInstrumentSymbols.length === 0 ? (
          <EmptyState
            title="No symbols available for instrument heatmap"
            message="Load summary rows with open positions before requesting instrument-scoped monthly return heatmap."
          />
        ) : null}

        {timeSeriesQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}

        {timeSeriesQuery.isError ? (
          <ErrorBanner
            title="Heatmap unavailable"
            message="Time-series data is unavailable for monthly heatmap rendering."
            variant="warning"
            actions={
              <button
                className="button-primary"
                onClick={() => void timeSeriesQuery.refetch()}
                type="button"
              >
                Retry heatmap
              </button>
            }
          />
        ) : null}

        {timeSeriesQuery.isSuccess && isHeatmapScopeReady ? (
          <PortfolioMonthlyReturnsHeatmap points={timeSeriesQuery.data.points} />
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Health scenario bridge"
        subtitle="Profile-weighted health synthesis linked with Monte Carlo sensitivity context."
        shortDescription="Connect executive health interpretation with scenario probability diagnostics."
        longDescription="Use this bridge to verify whether scenario outcomes reinforce or challenge the current health posture."
      >
        <div className="transactions-filters">
          <label className="transactions-filters__field">
            <span>Health profile posture</span>
            <select
              aria-label="Health profile posture"
              className="transactions-filters__select"
              onChange={(event) => {
                setHealthProfilePosture(event.target.value as PortfolioHealthProfilePosture);
              }}
              value={healthProfilePosture}
            >
              <option value="conservative">Conservative</option>
              <option value="balanced">Balanced</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </label>
        </div>

        {!isHealthScopeReady ? (
          <ErrorBanner
            title="Health bridge requires symbol"
            message="Provide instrument symbol for instrument-scoped health bridge context."
            variant="warning"
          />
        ) : null}

        {healthQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}

        {healthQuery.isError ? (
          <ErrorBanner
            title="Health bridge unavailable"
            message="Health synthesis could not be loaded for selected scope and posture."
            variant="warning"
            actions={
              <button
                className="button-primary"
                onClick={() => void healthQuery.refetch()}
                type="button"
              >
                Retry health bridge
              </button>
            }
          />
        ) : null}

        {healthQuery.isSuccess ? (
          <>
            <div className="chart-summary-grid">
              <article className="chart-summary-card chart-summary-card--signal">
                <span className="chart-summary-card__label">Health label</span>
                <strong className="chart-summary-card__headline">
                  {healthQuery.data.health_label}
                </strong>
                <p className="chart-summary-card__copy">
                  Score {healthQuery.data.health_score}/100 ({healthQuery.data.profile_posture} posture).
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--accent">
                <span className="chart-summary-card__label">Scenario sensitivity</span>
                <strong className="chart-summary-card__headline">
                  {monteCarloSignalLabel}
                </strong>
                <p className="chart-summary-card__copy">
                  Bust {formatBoundedPercent(monteCarloMutation.data?.summary.bust_probability)} · Goal{" "}
                  {formatBoundedPercent(monteCarloMutation.data?.summary.goal_probability)}
                </p>
              </article>
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Top risk driver</span>
                <strong className="chart-summary-card__headline">
                  {healthQuery.data.key_drivers.find((driver) => driver.direction === "penalizing")
                    ?.label || "No dominant penalizing driver"}
                </strong>
                <p className="chart-summary-card__copy">
                  {healthQuery.data.key_drivers.find((driver) => driver.direction === "penalizing")
                    ?.rationale || "Current profile has no dominant penalizing metric signal."}
                </p>
              </article>
            </div>
          </>
        ) : null}
      </WorkspaceChartPanel>

      <WorkspaceChartPanel
        title="Symbol contribution focus"
        subtitle="Top movers to contextualize report scope decisions."
        shortDescription="Contribution endpoint highlights largest period drivers and draggers with directional weighting."
        longDescription="Use this module to decide whether a portfolio report is sufficient or whether one instrument deserves deeper report scope."
      >
        {contributionQuery.isLoading ? <LoadingTableSkeleton rows={2} /> : null}

        {contributionQuery.isError ? (
          <ErrorBanner
            title={contributionErrorCopy.title}
            message={contributionErrorCopy.message}
            variant={contributionErrorCopy.variant}
            actions={
              <button
                className="button-primary"
                onClick={() => void contributionQuery.refetch()}
                type="button"
              >
                Retry contribution focus
              </button>
            }
          />
        ) : null}

        {contributionQuery.isSuccess && contributionQuery.data.rows.length === 0 ? (
          <EmptyState
            title="No contribution rows for selected period"
            message="Contribution endpoint returned no rows for this period."
          />
        ) : null}

        {contributionFocus ? (
          <div className="contribution-focus">
            <div className="chart-summary-grid">
              <article className="chart-summary-card">
                <span className="chart-summary-card__label">Top positive</span>
                <strong className="chart-summary-card__headline tone-positive">
                  {contributionFocus.positiveLeader || "No positive movers"}
                </strong>
                <p className="chart-summary-card__copy">
                  Largest positive symbol contribution in selected period.
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--signal">
                <span className="chart-summary-card__label">Top drag</span>
                <strong className="chart-summary-card__headline tone-negative">
                  {contributionFocus.negativeLeader || "No negative movers"}
                </strong>
                <p className="chart-summary-card__copy">
                  Largest negative symbol contribution in selected period.
                </p>
              </article>
              <article className="chart-summary-card chart-summary-card--accent">
                <span className="chart-summary-card__label">Concentration</span>
                <strong className="chart-summary-card__headline">
                  {contributionFocus.concentrationPct}%
                </strong>
                <p className="chart-summary-card__copy">
                  Share of absolute move explained by the top-ranked symbol.
                </p>
              </article>
            </div>

            <div
              className="contribution-focus__table"
              role="table"
              aria-label="Symbol contribution focus table"
            >
              <div className="contribution-focus__header" role="row">
                <span role="columnheader">Symbol</span>
                <span role="columnheader">Magnitude</span>
                <span role="columnheader">Signed contribution</span>
                <span role="columnheader">Net share (vs net period)</span>
                <span role="columnheader">Absolute share</span>
              </div>
              {contributionFocus.rows.map((row) => (
                <div className="contribution-focus__row" key={row.instrumentSymbol} role="row">
                  <span className="contribution-focus__symbol" role="cell">
                    {row.instrumentSymbol}
                  </span>
                  <span className="contribution-focus__magnitude" role="cell">
                    <span className="contribution-focus__bar-shell" aria-hidden="true">
                      <span
                        className={`contribution-focus__bar contribution-focus__bar--${row.tone}`}
                        style={{ width: `${row.widthPct}%` }}
                      />
                    </span>
                  </span>
                  <span className={`contribution-focus__value tone-${row.tone}`} role="cell">
                    {formatUsdMoney(row.contributionPnlUsd)}
                  </span>
                  <span className={`contribution-focus__value tone-${row.tone}`} role="cell">
                    {formatSignedPercent(row.netSharePct.toString())}
                  </span>
                  <span className="contribution-focus__value" role="cell">
                    {row.absSharePct.toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </WorkspaceChartPanel>
    </PortfolioWorkspaceLayout>
  );
}
