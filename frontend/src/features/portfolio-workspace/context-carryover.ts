import type {
  PortfolioChartPeriod,
  PortfolioTimeSeriesScope,
} from "../../core/api/schemas";

export const INCOMPATIBLE_CONTEXT_RESET_REASON = "incompatible_context_reset";

type RouteContextSupport = {
  supportsPeriod: boolean;
  supportsScope: boolean;
  supportsInstrumentSymbol: boolean;
};

export type WorkspaceNavigationContext = {
  period: PortfolioChartPeriod | null;
  scope: PortfolioTimeSeriesScope;
  instrumentSymbol: string | null;
  sourceRoute: string;
};

type ExtractWorkspaceContextParams = {
  pathname: string;
  searchParams: URLSearchParams;
};

type BuildWorkspaceNavigationTargetParams = {
  destinationPath: string;
  currentContext: WorkspaceNavigationContext;
  contextOverrides?: Partial<WorkspaceNavigationContext>;
};

const DEFAULT_SCOPE: PortfolioTimeSeriesScope = "portfolio";

const ROUTE_CONTEXT_SUPPORT: Record<string, RouteContextSupport> = {
  "/portfolio/dashboard": {
    supportsPeriod: true,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
  "/portfolio/holdings": {
    supportsPeriod: false,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
  "/portfolio/performance": {
    supportsPeriod: true,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
  "/portfolio/risk": {
    supportsPeriod: true,
    supportsScope: true,
    supportsInstrumentSymbol: true,
  },
  "/portfolio/rebalancing": {
    supportsPeriod: true,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
  "/portfolio/copilot": {
    supportsPeriod: true,
    supportsScope: true,
    supportsInstrumentSymbol: true,
  },
  "/portfolio/transactions": {
    supportsPeriod: false,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
  "/portfolio/home": {
    supportsPeriod: true,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
  "/portfolio/analytics": {
    supportsPeriod: true,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
  "/portfolio/reports": {
    supportsPeriod: true,
    supportsScope: false,
    supportsInstrumentSymbol: false,
  },
};

function resolveSupportForPath(pathname: string): RouteContextSupport {
  return (
    ROUTE_CONTEXT_SUPPORT[pathname] || {
      supportsPeriod: false,
      supportsScope: false,
      supportsInstrumentSymbol: false,
    }
  );
}

function normalizeScope(
  requestedScope: string | null,
): PortfolioTimeSeriesScope {
  return requestedScope === "instrument_symbol"
    ? "instrument_symbol"
    : DEFAULT_SCOPE;
}

export function extractWorkspaceContext({
  pathname,
  searchParams,
}: ExtractWorkspaceContextParams): WorkspaceNavigationContext {
  const normalizedPeriod = searchParams.get("period");
  const normalizedSymbolRaw = searchParams.get("instrument_symbol");
  const normalizedSymbol = normalizedSymbolRaw
    ? normalizedSymbolRaw.trim().toUpperCase()
    : "";
  const scope = normalizeScope(searchParams.get("scope"));

  return {
    period:
      normalizedPeriod && normalizedPeriod.trim().length > 0
        ? (normalizedPeriod as PortfolioChartPeriod)
        : null,
    scope,
    instrumentSymbol: normalizedSymbol.length > 0 ? normalizedSymbol : null,
    sourceRoute: pathname,
  };
}

function applyContextToDestination(
  destinationPath: string,
  context: WorkspaceNavigationContext,
): {
  searchParams: URLSearchParams;
  contextResetReason: string | null;
} {
  const support = resolveSupportForPath(destinationPath);
  const searchParams = new URLSearchParams();
  let contextResetReason: string | null = null;

  if (support.supportsPeriod && context.period !== null) {
    searchParams.set("period", context.period);
  }

  if (support.supportsScope) {
    if (context.scope === "instrument_symbol" && support.supportsInstrumentSymbol) {
      if (context.instrumentSymbol) {
        searchParams.set("scope", "instrument_symbol");
        searchParams.set("instrument_symbol", context.instrumentSymbol);
      } else {
        searchParams.set("scope", DEFAULT_SCOPE);
        contextResetReason = INCOMPATIBLE_CONTEXT_RESET_REASON;
      }
    } else {
      searchParams.set("scope", DEFAULT_SCOPE);
      if (context.scope === "instrument_symbol") {
        contextResetReason = INCOMPATIBLE_CONTEXT_RESET_REASON;
      }
    }
  } else if (context.scope === "instrument_symbol" || context.instrumentSymbol !== null) {
    contextResetReason = INCOMPATIBLE_CONTEXT_RESET_REASON;
  }

  if (contextResetReason !== null) {
    searchParams.set("context_reset", contextResetReason);
  }

  return {
    searchParams,
    contextResetReason,
  };
}

export function buildWorkspaceNavigationTarget({
  destinationPath,
  currentContext,
  contextOverrides,
}: BuildWorkspaceNavigationTargetParams): {
  to: string;
  contextResetReason: string | null;
} {
  const mergedContext: WorkspaceNavigationContext = {
    ...currentContext,
    ...contextOverrides,
  };
  const { searchParams, contextResetReason } = applyContextToDestination(
    destinationPath,
    mergedContext,
  );
  const queryString = searchParams.toString();

  return {
    to: queryString.length > 0 ? `${destinationPath}?${queryString}` : destinationPath,
    contextResetReason,
  };
}

export function resolveContextResetCopy(reasonCode: string | null): string | null {
  if (reasonCode === INCOMPATIBLE_CONTEXT_RESET_REASON) {
    return "Scope or symbol context was reset because this destination does not support the prior selection.";
  }
  return null;
}
