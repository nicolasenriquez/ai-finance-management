import {
  buildWorkspaceNavigationTarget,
  type WorkspaceNavigationContext,
} from "./context-carryover";

export type CommandPaletteDestinationKind =
  | "route_jump"
  | "symbol_lookup"
  | "analytical_action"
  | "watchlist_action";

export type CommandPaletteDestination = {
  id: string;
  kind: CommandPaletteDestinationKind;
  label: string;
  hint: string;
  destinationPath: string;
  contextOverrides?: Partial<WorkspaceNavigationContext>;
  watchlistSymbol?: string;
  watchlistAction?: "add" | "remove";
};

type ResolveCommandPaletteDestinationsParams = {
  query: string;
  currentContext: WorkspaceNavigationContext;
  availableSymbols?: readonly string[];
  watchlistSymbols?: readonly string[];
};

const ROUTE_JUMP_DESTINATIONS: CommandPaletteDestination[] = [
  {
    id: "route-home",
    kind: "route_jump",
    label: "Go to Home",
    hint: "Route jump",
    destinationPath: "/portfolio/home",
  },
  {
    id: "route-analytics",
    kind: "route_jump",
    label: "Go to Analytics",
    hint: "Route jump",
    destinationPath: "/portfolio/analytics",
  },
  {
    id: "route-risk",
    kind: "route_jump",
    label: "Go to Risk",
    hint: "Route jump",
    destinationPath: "/portfolio/risk",
  },
  {
    id: "route-reports",
    kind: "route_jump",
    label: "Go to Quant/Reports",
    hint: "Route jump",
    destinationPath: "/portfolio/reports",
  },
  {
    id: "route-copilot",
    kind: "route_jump",
    label: "Go to Copilot",
    hint: "Route jump",
    destinationPath: "/portfolio/copilot",
  },
  {
    id: "route-transactions",
    kind: "route_jump",
    label: "Go to Transactions",
    hint: "Route jump",
    destinationPath: "/portfolio/transactions",
  },
];

const DEFAULT_SYMBOL_LOOKUP: readonly string[] = [
  "AAPL",
  "MSFT",
  "NVDA",
  "TSLA",
  "GOOGL",
  "AMZN",
  "META",
  "BRK.B",
];

function normalizeQuery(query: string): string {
  return query.trim().toLowerCase();
}

function buildSymbolLookupDestinations(
  currentContext: WorkspaceNavigationContext,
  availableSymbols: readonly string[],
  watchlistSymbols: readonly string[],
): CommandPaletteDestination[] {
  const candidateSymbols = new Set<string>([
    ...DEFAULT_SYMBOL_LOOKUP,
    ...availableSymbols,
    ...watchlistSymbols,
  ]);
  if (currentContext.instrumentSymbol) {
    candidateSymbols.add(currentContext.instrumentSymbol);
  }

  const sortedSymbols = Array.from(candidateSymbols).sort((left, right) =>
    left.localeCompare(right),
  );

  return sortedSymbols.flatMap((symbol) => [
    {
      id: `symbol-risk-${symbol}`,
      kind: "symbol_lookup" as const,
      label: `Open risk for ${symbol}`,
      hint: "Symbol lookup",
      destinationPath: "/portfolio/risk",
      contextOverrides: {
        scope: "instrument_symbol",
        instrumentSymbol: symbol,
      },
    },
    {
      id: `symbol-copilot-${symbol}`,
      kind: "symbol_lookup" as const,
      label: `Open copilot for ${symbol}`,
      hint: "Symbol lookup",
      destinationPath: "/portfolio/copilot",
      contextOverrides: {
        scope: "instrument_symbol",
        instrumentSymbol: symbol,
      },
    },
  ]);
}

function buildWatchlistActionDestinations(
  symbols: readonly string[],
  watchlistSymbols: readonly string[],
): CommandPaletteDestination[] {
  const watchlistSet = new Set(watchlistSymbols);
  return symbols.slice(0, 16).map((symbol) => {
    const isWatchlisted = watchlistSet.has(symbol);
    return {
      id: `watchlist-${isWatchlisted ? "remove" : "add"}-${symbol}`,
      kind: "watchlist_action" as const,
      label: isWatchlisted
        ? `Remove ${symbol} from watchlist`
        : `Add ${symbol} to watchlist`,
      hint: "Watchlist",
      destinationPath: "/portfolio/home",
      watchlistSymbol: symbol,
      watchlistAction: isWatchlisted ? "remove" : "add",
    };
  });
}

function buildAnalyticalActionDestinations(
  currentContext: WorkspaceNavigationContext,
): CommandPaletteDestination[] {
  return [
    {
      id: "action-reports-current-period",
      kind: "analytical_action",
      label: "Open reports for current period",
      hint: "Analytical action",
      destinationPath: "/portfolio/reports",
      contextOverrides: {
        period: currentContext.period,
      },
    },
    {
      id: "action-copilot-current-context",
      kind: "analytical_action",
      label: "Open copilot with current context",
      hint: "Analytical action",
      destinationPath: "/portfolio/copilot",
    },
  ];
}

export function resolveCommandPaletteDestinations({
  query,
  currentContext,
  availableSymbols = [],
  watchlistSymbols = [],
}: ResolveCommandPaletteDestinationsParams): CommandPaletteDestination[] {
  const normalized = normalizeQuery(query);
  const combinedSymbolSet = new Set<string>([
    ...availableSymbols.map((symbol) => symbol.trim().toUpperCase()),
    ...watchlistSymbols.map((symbol) => symbol.trim().toUpperCase()),
  ]);
  if (currentContext.instrumentSymbol) {
    combinedSymbolSet.add(currentContext.instrumentSymbol);
  }
  const sortedSymbols = Array.from(combinedSymbolSet)
    .filter((symbol) => symbol.length > 0)
    .sort((left, right) => left.localeCompare(right));
  const destinations = [
    ...ROUTE_JUMP_DESTINATIONS,
    ...buildSymbolLookupDestinations(
      currentContext,
      sortedSymbols,
      watchlistSymbols,
    ),
    ...buildWatchlistActionDestinations(sortedSymbols, watchlistSymbols),
    ...buildAnalyticalActionDestinations(currentContext),
  ];

  if (normalized.length === 0) {
    return destinations.slice(0, 12);
  }

  return destinations.filter((destination) => {
    const searchable = `${destination.label} ${destination.hint}`.toLowerCase();
    return searchable.includes(normalized);
  });
}

export function resolveCommandDestinationTarget(
  destination: CommandPaletteDestination,
  currentContext: WorkspaceNavigationContext,
): {
  to: string;
  contextResetReason: string | null;
} {
  return buildWorkspaceNavigationTarget({
    destinationPath: destination.destinationPath,
    currentContext,
    contextOverrides: destination.contextOverrides,
  });
}
