import {
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
  type ReactNode,
} from "react";
import {
  NavLink,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { AppShell } from "../app-shell/AppShell";
import { TimestampBadge } from "../timestamp-badge/TimestampBadge";
import {
  resolveCommandDestinationTarget,
  resolveCommandPaletteDestinations,
} from "../../features/portfolio-workspace/command-palette";
import {
  resolveWorkspaceLensLabel,
  resolveWorkspaceShellDensityModeForPath,
  type WorkspaceShellDensityMode,
} from "../../features/portfolio-workspace/dashboard-governance";
import {
  buildWorkspaceNavigationTarget,
  extractWorkspaceContext,
  resolveContextResetCopy,
} from "../../features/portfolio-workspace/context-carryover";
import { formatUsdMoney } from "../../core/lib/formatters";
import { useOptionalPortfolioCopilotWorkspace } from "../../features/portfolio-copilot/workspace-session";
import { fetchPortfolioSummary } from "../../features/portfolio-summary/api";
import { fetchPortfolioTimeSeries } from "../../features/portfolio-workspace/api";
import { WorkspaceCopilotLauncher } from "./WorkspaceCopilotLauncher";

type PortfolioWorkspaceLayoutProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  freshnessTimestamp?: string;
  scopeLabel: string;
  provenanceLabel: string;
  provenanceTooltip?: string;
  periodLabel?: string;
  frequencyLabel?: string;
  timezoneLabel?: string;
  layoutVariant?: "default" | "chat";
  shellDensityMode?: WorkspaceShellDensityMode;
  showCommandPaletteTools?: boolean;
  showMarketPulse?: boolean;
  showTrustPanel?: boolean;
}>;

type WorkspaceRoute = {
  label: string;
  path: string;
  lens: string;
};

const WORKSPACE_ROUTES: WorkspaceRoute[] = [
  { label: "Dashboard", path: "/portfolio/dashboard", lens: "Overview" },
  { label: "Holdings", path: "/portfolio/holdings", lens: "Holdings" },
  { label: "Performance", path: "/portfolio/performance", lens: "Performance" },
  { label: "Risk", path: "/portfolio/risk", lens: "Risk" },
  { label: "Rebalancing", path: "/portfolio/rebalancing", lens: "Rebalancing" },
  { label: "Copilot", path: "/portfolio/copilot", lens: "Copilot" },
  { label: "Transactions", path: "/portfolio/transactions", lens: "Cash/Transactions" },
];

const WORKSPACE_WATCHLIST_STORAGE_KEY = "portfolio.workspace.watchlist.v1";

function normalizeSymbol(symbol: string): string {
  return symbol.trim().toUpperCase();
}

function toFiniteNumber(value: string | null): number | null {
  if (value === null) {
    return null;
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function useDesktopViewport(): boolean {
  const [isDesktopViewport, setIsDesktopViewport] = useState<boolean>(() => {
    return window.matchMedia("(min-width: 1024px)").matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia("(min-width: 1024px)");
    function handleViewportChange(event: MediaQueryListEvent): void {
      setIsDesktopViewport(event.matches);
    }
    setIsDesktopViewport(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleViewportChange);
    return () => {
      mediaQuery.removeEventListener("change", handleViewportChange);
    };
  }, []);

  return isDesktopViewport;
}

type WorkspaceMarketPulseSnapshot = {
  availableSymbols: string[];
  totalMarketValue: number | null;
  topMoverLabel: string;
  trend30dReturnRatio: number | null;
};

function resolveTopMoverLabel(
  symbols: Array<{ symbol: string; unrealizedGainPct: number }>,
): string {
  if (symbols.length === 0) {
    return "No live mover";
  }
  const topMover = symbols.reduce((leader, current) => {
    if (Math.abs(current.unrealizedGainPct) > Math.abs(leader.unrealizedGainPct)) {
      return current;
    }
    return leader;
  });
  const percentValue = topMover.unrealizedGainPct;
  const signPrefix = percentValue > 0 ? "+" : "";
  return `${topMover.symbol} ${signPrefix}${percentValue.toFixed(2)}%`;
}

export function PortfolioWorkspaceLayout({
  eyebrow,
  title,
  description,
  actions,
  freshnessTimestamp,
  scopeLabel,
  provenanceLabel,
  provenanceTooltip,
  periodLabel,
  frequencyLabel,
  timezoneLabel,
  layoutVariant = "default",
  shellDensityMode,
  showCommandPaletteTools,
  showMarketPulse,
  showTrustPanel,
  children,
}: PortfolioWorkspaceLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const copilotWorkspace = useOptionalPortfolioCopilotWorkspace();
  const isDesktopViewport = useDesktopViewport();
  const routePolicyDensityMode = resolveWorkspaceShellDensityModeForPath(location.pathname);
  const resolvedShellDensityMode = shellDensityMode || routePolicyDensityMode;
  const resolvedShowCommandPaletteTools =
    showCommandPaletteTools ?? resolvedShellDensityMode !== "compact";
  const resolvedShowMarketPulse =
    showMarketPulse ?? resolvedShellDensityMode === "expanded";
  const resolvedShowTrustPanel = showTrustPanel ?? true;
  const routeLensLabel = resolveWorkspaceLensLabel(location.pathname);
  const shouldReserveDockColumn =
    !!copilotWorkspace?.state.isLauncherOpen &&
    isDesktopViewport &&
    location.pathname !== "/portfolio/copilot";

  function navigateWithFallback(target: string): void {
    navigate(target);
    if (typeof navigator !== "undefined" && /jsdom/i.test(navigator.userAgent)) {
      return;
    }
    window.setTimeout(() => {
      const current = `${window.location.pathname}${window.location.search}`;
      if (current !== target) {
        window.location.href = target;
      }
    }, 80);
  }
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isWatchlistManagerOpen, setIsWatchlistManagerOpen] = useState(false);
  const [watchlistDraftSymbol, setWatchlistDraftSymbol] = useState("");
  const [commandPaletteQuery, setCommandPaletteQuery] = useState("");
  const [watchlistSymbols, setWatchlistSymbols] = useState<string[]>([]);
  const [marketPulseSnapshot, setMarketPulseSnapshot] =
    useState<WorkspaceMarketPulseSnapshot>({
      availableSymbols: [],
      totalMarketValue: null,
      topMoverLabel: "No live mover",
      trend30dReturnRatio: null,
    });
  const searchParams = useMemo(
    () => new URLSearchParams(location.search),
    [location.search],
  );
  const currentContext = useMemo(
    () =>
      extractWorkspaceContext({
        pathname: location.pathname,
        searchParams,
      }),
    [location.pathname, searchParams],
  );
  const availableSymbols = marketPulseSnapshot.availableSymbols;
  const commandPaletteDestinations = useMemo(
    () =>
      resolveCommandPaletteDestinations({
        query: commandPaletteQuery,
        currentContext,
        availableSymbols,
        watchlistSymbols,
      }),
    [availableSymbols, commandPaletteQuery, currentContext, watchlistSymbols],
  );
  const contextResetReasonCode = searchParams.get("context_reset");
  const contextResetCopy = resolveContextResetCopy(contextResetReasonCode);

  useEffect(() => {
    const rawWatchlist = window.localStorage.getItem(WORKSPACE_WATCHLIST_STORAGE_KEY);
    if (!rawWatchlist) {
      return;
    }
    try {
      const parsed = JSON.parse(rawWatchlist);
      if (!Array.isArray(parsed)) {
        return;
      }
      const normalized = parsed
        .map((candidate) => (typeof candidate === "string" ? normalizeSymbol(candidate) : ""))
        .filter((symbol, index, array) => symbol.length > 0 && array.indexOf(symbol) === index)
        .slice(0, 20);
      setWatchlistSymbols(normalized);
    } catch {
      return;
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      WORKSPACE_WATCHLIST_STORAGE_KEY,
      JSON.stringify(watchlistSymbols),
    );
  }, [watchlistSymbols]);

  useEffect(() => {
    let isActive = true;
    async function hydrateMarketPulse(): Promise<void> {
      const [summaryResult, timeSeriesResult] = await Promise.allSettled([
        fetchPortfolioSummary(),
        fetchPortfolioTimeSeries("30D"),
      ]);
      if (!isActive) {
        return;
      }

      const nextSnapshot: WorkspaceMarketPulseSnapshot = {
        availableSymbols: [],
        totalMarketValue: null,
        topMoverLabel: "No live mover",
        trend30dReturnRatio: null,
      };

      if (summaryResult.status === "fulfilled") {
        const summaryRows = summaryResult.value.rows;
        nextSnapshot.availableSymbols = summaryRows
          .map((row) => normalizeSymbol(row.instrument_symbol))
          .filter((symbol, index, array) => {
            return symbol.length > 0 && array.indexOf(symbol) === index;
          });
        nextSnapshot.totalMarketValue = summaryRows.reduce((accumulator, row) => {
          const numericValue = toFiniteNumber(row.market_value_usd);
          return accumulator + (numericValue ?? 0);
        }, 0);
        const moverCandidates = summaryRows
          .map((row) => ({
            symbol: row.instrument_symbol,
            unrealizedGainPct: toFiniteNumber(row.unrealized_gain_pct) ?? 0,
          }))
          .filter((row) => row.symbol.trim().length > 0);
        nextSnapshot.topMoverLabel = resolveTopMoverLabel(moverCandidates);
      }

      if (timeSeriesResult.status === "fulfilled") {
        const points = timeSeriesResult.value.points;
        if (points.length >= 2) {
          const firstPoint = Number(points[0].portfolio_value_usd);
          const lastPoint = Number(points[points.length - 1].portfolio_value_usd);
          if (Number.isFinite(firstPoint) && Number.isFinite(lastPoint) && firstPoint > 0) {
            nextSnapshot.trend30dReturnRatio = (lastPoint - firstPoint) / firstPoint;
          }
        }
      }
      setMarketPulseSnapshot(nextSnapshot);
    }
    void hydrateMarketPulse();
    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    function handleKeyboardToggle(event: KeyboardEvent): void {
      const keyNormalized = event.key.toLowerCase();
      const shouldTogglePalette =
        keyNormalized === "k" && (event.metaKey || event.ctrlKey);
      if (!shouldTogglePalette) {
        return;
      }
      event.preventDefault();
      setIsCommandPaletteOpen((previous) => !previous);
    }

    window.addEventListener("keydown", handleKeyboardToggle);
    return () => {
      window.removeEventListener("keydown", handleKeyboardToggle);
    };
  }, []);

  function closeCommandPalette(): void {
    setIsCommandPaletteOpen(false);
    setCommandPaletteQuery("");
  }

  function addWatchlistSymbol(symbolCandidate: string): void {
    const watchlistSymbol = normalizeSymbol(symbolCandidate);
    if (watchlistSymbol.length === 0) {
      return;
    }
    setWatchlistSymbols((previousSymbols) => {
      if (previousSymbols.includes(watchlistSymbol)) {
        return previousSymbols;
      }
      return [...previousSymbols, watchlistSymbol].slice(0, 20);
    });
    setWatchlistDraftSymbol("");
  }

  function removeWatchlistSymbol(symbolCandidate: string): void {
    const watchlistSymbol = normalizeSymbol(symbolCandidate);
    if (watchlistSymbol.length === 0) {
      return;
    }
    setWatchlistSymbols((previousSymbols) => {
      return previousSymbols.filter((symbol) => symbol !== watchlistSymbol);
    });
  }

  function navigateToPaletteDestination(destinationId: string): void {
    const destination = commandPaletteDestinations.find(
      (candidate) => candidate.id === destinationId,
    );
    if (!destination) {
      return;
    }
    if (
      destination.kind === "watchlist_action" &&
      destination.watchlistSymbol &&
      destination.watchlistAction
    ) {
      const watchlistSymbol = destination.watchlistSymbol;
      const watchlistAction = destination.watchlistAction;
      setWatchlistSymbols((previousSymbols) => {
        if (watchlistAction === "add") {
          if (previousSymbols.includes(watchlistSymbol)) {
            return previousSymbols;
          }
          return [...previousSymbols, watchlistSymbol].slice(0, 20);
        }
        return previousSymbols.filter((symbol) => symbol !== watchlistSymbol);
      });
      closeCommandPalette();
      return;
    }
    const navigationTarget = resolveCommandDestinationTarget(
      destination,
      currentContext,
    );
    navigateWithFallback(navigationTarget.to);
    closeCommandPalette();
  }

  function navigateToWatchlistSymbol(symbol: string): void {
    const navigationTarget = buildWorkspaceNavigationTarget({
      destinationPath: "/portfolio/risk",
      currentContext,
      contextOverrides: {
        scope: "instrument_symbol",
        instrumentSymbol: symbol,
      },
    });
    navigateWithFallback(navigationTarget.to);
    closeCommandPalette();
  }

  return (
    <AppShell
      eyebrow={eyebrow}
      title={title}
      description={description}
      actions={actions}
      headerVariant={layoutVariant}
    >
      <section
        className={`workspace-layout workspace-layout--${resolvedShellDensityMode}${
          shouldReserveDockColumn ? " workspace-layout--with-docked-copilot" : ""
        }`}
        data-shell-density-mode={resolvedShellDensityMode}
      >
        <nav
          className={
            layoutVariant === "chat"
              ? "panel workspace-nav workspace-nav--chat"
              : "panel workspace-nav"
          }
          aria-label="Portfolio analytics workspace navigation"
        >
          <div className="workspace-nav__tools">
            <div className="workspace-nav__tools-actions">
              {resolvedShowCommandPaletteTools ? (
                <button
                  aria-haspopup="dialog"
                  aria-expanded={isCommandPaletteOpen}
                  aria-controls="workspace-command-palette"
                  className="button-secondary workspace-nav__palette-trigger workspace-nav__utility-action"
                  onClick={() => setIsCommandPaletteOpen(true)}
                  type="button"
                >
                  Open command palette
                </button>
              ) : null}
              <button
                aria-expanded={isWatchlistManagerOpen}
                aria-controls="workspace-watchlist-manager"
                className="button-secondary workspace-nav__watchlist-trigger workspace-nav__utility-action"
                onClick={() => setIsWatchlistManagerOpen((previous) => !previous)}
                type="button"
              >
                Watchlist ({watchlistSymbols.length})
              </button>
              <WorkspaceCopilotLauncher
                currentContext={currentContext}
                routePathname={location.pathname}
                symbolSuggestions={availableSymbols}
              />
            </div>
            <div className="workspace-nav__tools-meta">
              <span className="workspace-nav__hint">
                {resolvedShowCommandPaletteTools
                  ? "Command palette supports route jump and symbol lookup."
                  : "Compact shell mode prioritizes route content over utility chrome."}
              </span>
              {watchlistSymbols.length > 0 ? (
                <span className="workspace-nav__watchlist">
                  {watchlistSymbols.slice(0, 4).join(", ")}
                  {watchlistSymbols.length > 4 ? "..." : ""}
                </span>
              ) : null}
            </div>
          </div>
          {isWatchlistManagerOpen ? (
            <section
              aria-label="Watchlist manager"
              className="workspace-watchlist-manager"
              id="workspace-watchlist-manager"
            >
              <div className="workspace-watchlist-manager__row">
                <input
                  aria-label="Watchlist symbol input"
                  className="transactions-filters__input"
                  maxLength={16}
                  onChange={(event) => setWatchlistDraftSymbol(event.currentTarget.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      addWatchlistSymbol(watchlistDraftSymbol);
                    }
                  }}
                  placeholder="Add symbol (e.g. AAPL)"
                  value={watchlistDraftSymbol}
                />
                <button
                  className="button-secondary"
                  onClick={() => addWatchlistSymbol(watchlistDraftSymbol)}
                  type="button"
                >
                  Add
                </button>
              </div>
              {watchlistSymbols.length > 0 ? (
                <div className="workspace-watchlist-manager__chips">
                  {watchlistSymbols.map((symbol) => (
                    <button
                      aria-label={`Remove ${symbol} from watchlist`}
                      className="workspace-watchlist-manager__chip"
                      key={symbol}
                      onClick={() => removeWatchlistSymbol(symbol)}
                      type="button"
                    >
                      {symbol} ×
                    </button>
                  ))}
                </div>
              ) : (
                <p className="workspace-watchlist-manager__empty">
                  No symbols in watchlist yet.
                </p>
              )}
              {availableSymbols.length > 0 ? (
                <div className="workspace-watchlist-manager__quick-add">
                  {availableSymbols
                    .filter((symbol) => !watchlistSymbols.includes(symbol))
                    .slice(0, 12)
                    .map((symbol) => (
                      <button
                        className="workspace-watchlist-manager__quick-add-chip"
                        key={symbol}
                        onClick={() => addWatchlistSymbol(symbol)}
                        type="button"
                      >
                        + {symbol}
                      </button>
                    ))}
                </div>
              ) : null}
            </section>
          ) : null}
          <ul className="workspace-nav__list">
            {WORKSPACE_ROUTES.map((route) => (
              <li key={route.path}>
                {(() => {
                  const navigationTarget = buildWorkspaceNavigationTarget({
                    destinationPath: route.path,
                    currentContext,
                  });
                  return (
                    <NavLink
                      to={navigationTarget.to}
                      onClick={(event) => {
                        // Fallback navigation keeps route changes deterministic even if
                        // browser-level anchor handling is interrupted by layered UI state.
                        event.preventDefault();
                        navigateWithFallback(navigationTarget.to);
                      }}
                      className={({ isActive }) =>
                        isActive
                          ? "workspace-nav__link workspace-nav__link--active"
                          : "workspace-nav__link"
                      }
                    >
                      <span>{route.label}</span>
                      <span aria-hidden="true" className="workspace-nav__route-lens">
                        {route.lens}
                      </span>
                    </NavLink>
                  );
                })()}
              </li>
            ))}
          </ul>
          <p className="workspace-nav__lens-copy">
            Monitoring lens: {routeLensLabel || "Workspace"}
          </p>
        </nav>

        {isCommandPaletteOpen && resolvedShowCommandPaletteTools ? (
          <section
            aria-label="Workspace command palette"
            className="panel workspace-command-palette"
            id="workspace-command-palette"
            role="dialog"
          >
            <div className="workspace-command-palette__header">
              <h2>Command palette</h2>
              <button
                className="button-secondary"
                onClick={closeCommandPalette}
                type="button"
              >
                Close
              </button>
            </div>
            <p className="workspace-command-palette__copy">
              Route jump, symbol lookup, and approved analytical actions.
            </p>
            <label className="workspace-command-palette__field">
              <span>Search commands</span>
              <input
                aria-label="Command palette query"
                autoFocus
                className="transactions-filters__input"
                onChange={(event) => setCommandPaletteQuery(event.currentTarget.value)}
                placeholder="Try: risk, reports, AAPL"
                value={commandPaletteQuery}
              />
            </label>
            {watchlistSymbols.length > 0 ? (
              <section className="workspace-command-palette__watchlist" aria-label="Watchlist quick jump">
                <h3>Watchlist quick jump</h3>
                <div className="workspace-command-palette__watchlist-row">
                  {watchlistSymbols.slice(0, 8).map((symbol) => (
                    <button
                      className="workspace-command-palette__watchlist-chip"
                      key={symbol}
                      onClick={() => navigateToWatchlistSymbol(symbol)}
                      type="button"
                    >
                      {symbol}
                    </button>
                  ))}
                </div>
              </section>
            ) : null}
            <ul className="workspace-command-palette__results">
              {commandPaletteDestinations.map((destination) => (
                <li key={destination.id}>
                  <button
                    className="workspace-command-palette__result"
                    onClick={() => navigateToPaletteDestination(destination.id)}
                    type="button"
                  >
                    <span>{destination.label}</span>
                    <small>{destination.hint}</small>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {resolvedShowMarketPulse ? (
          <section className="panel workspace-market-pulse" aria-label="Market pulse">
            <header className="workspace-market-pulse__header">
              <h2>Market pulse</h2>
              <p>Live overview of holdings breadth, 30D trend, and concentration signal.</p>
            </header>
            <div className="workspace-market-pulse__grid">
              <article className="workspace-market-pulse__card">
                <span className="workspace-market-pulse__label">Tracked symbols</span>
                <strong className="workspace-market-pulse__value">
                  {availableSymbols.length > 0 ? availableSymbols.length : "—"}
                </strong>
              </article>
              <article className="workspace-market-pulse__card">
                <span className="workspace-market-pulse__label">Watchlist</span>
                <strong className="workspace-market-pulse__value">{watchlistSymbols.length}</strong>
              </article>
              <article className="workspace-market-pulse__card">
                <span className="workspace-market-pulse__label">Total market value</span>
                <strong className="workspace-market-pulse__value">
                  {marketPulseSnapshot.totalMarketValue === null
                    ? "—"
                    : formatUsdMoney(marketPulseSnapshot.totalMarketValue.toFixed(2))}
                </strong>
              </article>
              <article className="workspace-market-pulse__card">
                <span className="workspace-market-pulse__label">30D trend</span>
                <strong className="workspace-market-pulse__value">
                  {marketPulseSnapshot.trend30dReturnRatio === null
                    ? "—"
                    : `${marketPulseSnapshot.trend30dReturnRatio > 0 ? "+" : ""}${(marketPulseSnapshot.trend30dReturnRatio * 100).toFixed(2)}%`}
                </strong>
              </article>
              <article className="workspace-market-pulse__card workspace-market-pulse__card--wide">
                <span className="workspace-market-pulse__label">Top mover</span>
                <strong className="workspace-market-pulse__value">
                  {marketPulseSnapshot.topMoverLabel}
                </strong>
              </article>
            </div>
          </section>
        ) : null}

        {contextResetCopy ? (
          <section
            className="panel workspace-context-reset-banner"
            role="status"
            aria-live="polite"
          >
            <p>{contextResetCopy}</p>
          </section>
        ) : null}

        {resolvedShowTrustPanel ? (
          <section className="panel workspace-trust" aria-label="Data trust context">
            <div className="workspace-trust__row workspace-trust__row--primary">
              {freshnessTimestamp ? (
                <TimestampBadge value={freshnessTimestamp} />
              ) : (
                <span className="workspace-trust__token workspace-trust__token--neutral">
                  Freshness: awaiting response
                </span>
              )}

              {periodLabel ? (
                <span className="workspace-trust__token">
                  <span className="workspace-trust__key">Period</span>
                  <span className="workspace-trust__value">{periodLabel}</span>
                </span>
              ) : null}
              {frequencyLabel ? (
                <span className="workspace-trust__token">
                  <span className="workspace-trust__key">Frequency</span>
                  <span className="workspace-trust__value">{frequencyLabel}</span>
                </span>
              ) : null}
              {timezoneLabel ? (
                <span className="workspace-trust__token">
                  <span className="workspace-trust__key">Timezone</span>
                  <span className="workspace-trust__value">{timezoneLabel}</span>
                </span>
              ) : null}
            </div>

            <div className="workspace-trust__row workspace-trust__row--secondary">
              <span className="workspace-trust__token workspace-trust__token--scope">
                <span className="workspace-trust__key">Scope</span>
                <span className="workspace-trust__value">{scopeLabel}</span>
              </span>

              <span
                aria-label="Data provenance"
                className="workspace-trust__token workspace-trust__token--provenance"
              >
                <span className="workspace-trust__key">Provenance</span>
                <span
                  className="workspace-trust__value workspace-trust__value--truncate"
                  title={provenanceTooltip || provenanceLabel}
                >
                  {provenanceLabel}
                </span>
              </span>
            </div>
          </section>
        ) : null}

        {children}
      </section>
    </AppShell>
  );
}
