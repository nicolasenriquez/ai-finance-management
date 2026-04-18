import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { z } from "zod";

import { getFrontendEnv } from "../config/env";
import { formatQuantity, formatUsdMoney } from "../lib/formatters";
import { fetchJson } from "./client";
import {
  portfolioCommandCenterResponseSchema,
  portfolioContributionResponseSchema,
  portfolioHealthSynthesisResponseSchema,
  portfolioHierarchyResponseSchema,
  portfolioLotDetailResponseSchema,
  portfolioSummaryResponseSchema,
  portfolioTimeSeriesResponseSchema,
  type PortfolioChartPeriod,
  type PortfolioCommandCenterResponse,
  type PortfolioContributionResponse,
  type PortfolioHealthProfilePosture,
  type PortfolioHealthSynthesisResponse,
  type PortfolioHierarchyResponse,
  type PortfolioLotDetailResponse,
  type PortfolioQuantReportScope,
  type PortfolioSummaryResponse,
  type PortfolioTimeSeriesResponse,
} from "./portfolio-schemas";

type NumericLike = string | number | null | undefined;

type PortfolioApiFixtureMap = Record<string, unknown>;

type PortfolioResourceStatus = "loading" | "ready" | "empty" | "error";

type PortfolioResourceState<T> = {
  status: PortfolioResourceStatus;
  data: T | null;
  errorMessage: string | null;
  reload: () => void;
};

type PortfolioResourceOptions<T> = {
  fixtureKey: string;
  loader: () => Promise<T>;
  isEmpty?: (data: T) => boolean;
};

function isPortfolioSummaryEmpty(response: PortfolioSummaryResponse): boolean {
  return response.rows.length === 0;
}

function isPortfolioHierarchyEmpty(response: PortfolioHierarchyResponse): boolean {
  return response.groups.length === 0;
}

function isPortfolioContributionEmpty(response: PortfolioContributionResponse): boolean {
  return response.rows.length === 0;
}

function isPortfolioTimeSeriesEmpty(response: PortfolioTimeSeriesResponse): boolean {
  return response.points.length === 0;
}

function isPortfolioLotDetailEmpty(response: PortfolioLotDetailResponse): boolean {
  return response.lots.length === 0;
}

function isPortfolioHealthSynthesisEmpty(
  response: PortfolioHealthSynthesisResponse,
): boolean {
  return response.pillars.length === 0;
}

function buildQueryString(
  query: Record<string, string | undefined>,
): string {
  const entries = Object.entries(query).filter(([, value]) => value !== undefined);
  if (entries.length === 0) {
    return "";
  }

  entries.sort(([leftKey], [rightKey]) => leftKey.localeCompare(rightKey));
  return `?${new URLSearchParams(entries as [string, string][]).toString()}`;
}

export function buildPortfolioApiPath(
  path: string,
  query: Record<string, string | undefined> = {},
): string {
  return `${path}${buildQueryString(query)}`;
}

export function buildPortfolioApiFixtureKey(
  path: string,
  query: Record<string, string | undefined> = {},
): string {
  const { apiPrefix } = getFrontendEnv();
  return `GET ${apiPrefix}${buildPortfolioApiPath(path, query)}`;
}

function resolveGlobalFixtureMap(): PortfolioApiFixtureMap | undefined {
  const globalFixture = globalThis as typeof globalThis & {
    __PORTFOLIO_API_FIXTURE__?: PortfolioApiFixtureMap;
  };
  return globalFixture.__PORTFOLIO_API_FIXTURE__;
}

export function resolvePortfolioApiFixture<T>(
  fixtureKey: string,
): T | undefined {
  const fixtureMap = resolveGlobalFixtureMap();
  if (!fixtureMap) {
    return undefined;
  }

  const fixtureValue = fixtureMap[fixtureKey];
  if (fixtureValue === undefined) {
    return undefined;
  }

  return fixtureValue as T;
}

function normalizeNumericLike(value: NumericLike): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  const normalized = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(normalized)) {
    return null;
  }

  return normalized;
}

function formatMoneyLike(value: NumericLike): string {
  const normalized = normalizeNumericLike(value);
  if (normalized === null) {
    return "Unavailable";
  }

  return formatUsdMoney(normalized.toString());
}

function formatPercentLike(
  value: NumericLike,
  fractionDigits = 1,
): string {
  const normalized = normalizeNumericLike(value);
  if (normalized === null) {
    return "Unavailable";
  }

  return `${normalized.toFixed(fractionDigits)}%`;
}

function formatQuantityLike(value: NumericLike): string {
  const normalized = normalizeNumericLike(value);
  if (normalized === null) {
    return "Unavailable";
  }

  return formatQuantity(normalized.toString());
}

function sortByNumericValueDescending<T>(
  rows: T[],
  selector: (row: T) => NumericLike,
): T[] {
  return [...rows].sort((leftRow, rightRow) => {
    const leftValue = normalizeNumericLike(selector(leftRow)) ?? Number.NEGATIVE_INFINITY;
    const rightValue = normalizeNumericLike(selector(rightRow)) ?? Number.NEGATIVE_INFINITY;
    return rightValue - leftValue;
  });
}

async function sendPortfolioJsonRequest<T>(
  path: string,
  schema: z.ZodType<T>,
): Promise<T> {
  return fetchJson({
    path,
    schema,
  });
}

function usePortfolioResource<T>({
  fixtureKey,
  loader,
  isEmpty,
}: PortfolioResourceOptions<T>): PortfolioResourceState<T> {
  const fixtureData = useMemo(() => resolvePortfolioApiFixture<T>(fixtureKey), [fixtureKey]);
  const [resourceState, setResourceState] = useState<PortfolioResourceState<T>>(() => {
    if (fixtureData !== undefined) {
      return {
        status: isEmpty?.(fixtureData) ? "empty" : "ready",
        data: fixtureData,
        errorMessage: null,
        reload: () => undefined,
      };
    }

    return {
      status: "loading",
      data: null,
      errorMessage: null,
      reload: () => undefined,
    };
  });
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (fixtureData !== undefined) {
      setResourceState({
        status: isEmpty?.(fixtureData) ? "empty" : "ready",
        data: fixtureData,
        errorMessage: null,
        reload: () => setReloadToken((previous) => previous + 1),
      });
      return;
    }

    let isActive = true;
    setResourceState((previousState) => ({
      ...previousState,
      status: "loading",
      errorMessage: null,
    }));

    void loader()
      .then((data) => {
        if (!isActive) {
          return;
        }
        setResourceState({
          status: isEmpty?.(data) ? "empty" : "ready",
          data,
          errorMessage: null,
          reload: () => setReloadToken((previous) => previous + 1),
        });
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }
        setResourceState({
          status: "error",
          data: null,
          errorMessage: error instanceof Error ? error.message : "Unable to load portfolio data.",
          reload: () => setReloadToken((previous) => previous + 1),
        });
      });

    return () => {
      isActive = false;
    };
  }, [fixtureData, isEmpty, loader, reloadToken]);

  return resourceState;
}

export function usePortfolioCommandCenterResource(): PortfolioResourceState<PortfolioCommandCenterResponse> {
  const loader = useCallback(
    () =>
      sendPortfolioJsonRequest(
        buildPortfolioApiPath("/portfolio/command-center"),
        portfolioCommandCenterResponseSchema,
      ),
    [],
  );

  return usePortfolioResource({
    fixtureKey: buildPortfolioApiFixtureKey("/portfolio/command-center"),
    loader,
  });
}

export function usePortfolioSummaryResource(): PortfolioResourceState<PortfolioSummaryResponse> {
  const loader = useCallback(
    () =>
      sendPortfolioJsonRequest(
        buildPortfolioApiPath("/portfolio/summary"),
        portfolioSummaryResponseSchema,
      ),
    [],
  );

  return usePortfolioResource({
    fixtureKey: buildPortfolioApiFixtureKey("/portfolio/summary"),
    loader,
    isEmpty: isPortfolioSummaryEmpty,
  });
}

export function usePortfolioHierarchyResource(): PortfolioResourceState<PortfolioHierarchyResponse> {
  const loader = useCallback(
    () =>
      sendPortfolioJsonRequest(
        buildPortfolioApiPath("/portfolio/hierarchy", { group_by: "sector" }),
        portfolioHierarchyResponseSchema,
      ),
    [],
  );

  return usePortfolioResource({
    fixtureKey: buildPortfolioApiFixtureKey("/portfolio/hierarchy", {
      group_by: "sector",
    }),
    loader,
    isEmpty: isPortfolioHierarchyEmpty,
  });
}

export function usePortfolioContributionResource(
  period: PortfolioChartPeriod,
): PortfolioResourceState<PortfolioContributionResponse> {
  const loader = useCallback(
    () =>
      sendPortfolioJsonRequest(
        buildPortfolioApiPath("/portfolio/contribution", { period }),
        portfolioContributionResponseSchema,
      ),
    [period],
  );

  return usePortfolioResource({
    fixtureKey: buildPortfolioApiFixtureKey("/portfolio/contribution", { period }),
    loader,
    isEmpty: isPortfolioContributionEmpty,
  });
}

export function usePortfolioTimeSeriesResource(
  period: PortfolioChartPeriod,
  scope: PortfolioQuantReportScope,
  instrumentSymbol?: string,
): PortfolioResourceState<PortfolioTimeSeriesResponse> {
  const loader = useCallback(
    () =>
      sendPortfolioJsonRequest(
        buildPortfolioApiPath("/portfolio/time-series", {
          period,
          scope,
          instrument_symbol: instrumentSymbol,
        }),
        portfolioTimeSeriesResponseSchema,
      ),
    [instrumentSymbol, period, scope],
  );

  return usePortfolioResource({
    fixtureKey: buildPortfolioApiFixtureKey("/portfolio/time-series", {
      period,
      scope,
      instrument_symbol: instrumentSymbol,
    }),
    loader,
    isEmpty: isPortfolioTimeSeriesEmpty,
  });
}

export function usePortfolioLotDetailResource(
  ticker: string,
): PortfolioResourceState<PortfolioLotDetailResponse> {
  const normalizedTicker = ticker.trim().toUpperCase();
  const loader = useCallback(
    () =>
      sendPortfolioJsonRequest(
        buildPortfolioApiPath(`/portfolio/lots/${normalizedTicker}`),
        portfolioLotDetailResponseSchema,
      ),
    [normalizedTicker],
  );

  return usePortfolioResource({
    fixtureKey: buildPortfolioApiFixtureKey(`/portfolio/lots/${normalizedTicker}`),
    loader,
    isEmpty: isPortfolioLotDetailEmpty,
  });
}

export function usePortfolioHealthSynthesisResource(
  period: PortfolioChartPeriod,
  scope: PortfolioQuantReportScope,
  instrumentSymbol?: string,
  profilePosture: PortfolioHealthProfilePosture = "balanced",
): PortfolioResourceState<PortfolioHealthSynthesisResponse> {
  const loader = useCallback(
    () =>
      sendPortfolioJsonRequest(
        buildPortfolioApiPath("/portfolio/health-synthesis", {
          period,
          scope,
          instrument_symbol: instrumentSymbol,
          profile_posture: profilePosture,
        }),
        portfolioHealthSynthesisResponseSchema,
      ),
    [instrumentSymbol, period, profilePosture, scope],
  );

  return usePortfolioResource({
    fixtureKey: buildPortfolioApiFixtureKey("/portfolio/health-synthesis", {
      period,
      scope,
      instrument_symbol: instrumentSymbol,
      profile_posture: profilePosture,
    }),
    loader,
    isEmpty: isPortfolioHealthSynthesisEmpty,
  });
}

export function getPortfolioSummaryRowsByMarketValue(
  rows: PortfolioSummaryResponse["rows"],
): PortfolioSummaryResponse["rows"] {
  return sortByNumericValueDescending(rows, (row) => row.market_value_usd);
}

export function getPortfolioSummaryRowsByContribution(
  rows: PortfolioSummaryResponse["rows"],
): PortfolioSummaryResponse["rows"] {
  return sortByNumericValueDescending(rows, (row) => row.unrealized_gain_usd);
}

export function getPortfolioContributionRowsByImpact(
  rows: PortfolioContributionResponse["rows"],
): PortfolioContributionResponse["rows"] {
  return sortByNumericValueDescending(rows, (row) => row.contribution_pnl_usd);
}

export function resolvePortfolioAssetDetailHref(
  summaryResponse: PortfolioSummaryResponse | null,
  fallbackTicker: string = "UNKNOWN",
): string {
  const firstHolding = summaryResponse
    ? getPortfolioSummaryRowsByMarketValue(summaryResponse.rows)[0]
    : null;

  if (!firstHolding) {
    return `/portfolio/asset-detail/${fallbackTicker}`;
  }

  return `/portfolio/asset-detail/${firstHolding.instrument_symbol}`;
}

export function resolvePortfolioSummaryKpis(
  commandCenter: PortfolioCommandCenterResponse | null,
  summaryResponse: PortfolioSummaryResponse | null,
): {
  portfolioValue: string;
  dailyPnl: string;
  unrealizedPnl: string;
  dividendRunRate: string;
} {
  const topLevelMarketValue = commandCenter
    ? formatMoneyLike(commandCenter.total_market_value_usd)
    : "Unavailable";
  const dailyPnl = commandCenter
    ? formatMoneyLike(commandCenter.daily_pnl_usd)
    : "Unavailable";
  const unrealizedPnl = summaryResponse
    ? formatMoneyLike(
        summaryResponse.rows.reduce(
          (runningTotal, row) => runningTotal + (normalizeNumericLike(row.unrealized_gain_usd) ?? 0),
          0,
        ),
      )
    : "Unavailable";
  const dividendRunRate = summaryResponse
    ? formatMoneyLike(
        summaryResponse.rows.reduce(
          (runningTotal, row) => runningTotal + (normalizeNumericLike(row.dividend_net_usd) ?? 0),
          0,
        ),
      )
    : "Unavailable";

  return {
    portfolioValue: topLevelMarketValue,
    dailyPnl,
    unrealizedPnl,
    dividendRunRate,
  };
}

export function resolvePortfolioKpiChange(
  dailyPnl: string,
  concentrationTop5Pct: NumericLike,
): string {
  const concentration = formatPercentLike(concentrationTop5Pct, 1);
  return `${dailyPnl} · Top 5 ${concentration}`;
}

export function resolveTickerActionState(
  unrealizedGainPct: NumericLike,
): string {
  const normalizedGain = normalizeNumericLike(unrealizedGainPct);
  if (normalizedGain === null) {
    return "Hold";
  }

  if (normalizedGain < 0) {
    return "Wait";
  }

  if (normalizedGain >= 20) {
    return "Add on pullback";
  }

  return "Hold";
}

export function formatPortfolioQuantity(value: NumericLike): string {
  return formatQuantityLike(value);
}

export function formatPortfolioMoney(value: NumericLike): string {
  return formatMoneyLike(value);
}

export function formatPortfolioPercent(value: NumericLike, fractionDigits = 1): string {
  return formatPercentLike(value, fractionDigits);
}

export function resolvePortfolioHoldingsBySector(
  hierarchyResponse: PortfolioHierarchyResponse | null,
): PortfolioHierarchyResponse["groups"] {
  return hierarchyResponse?.groups ?? [];
}
