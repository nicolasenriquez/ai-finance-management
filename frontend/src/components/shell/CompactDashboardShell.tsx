import {
  type PropsWithChildren,
  useCallback,
  useState,
} from "react";

import { useQueryClient } from "@tanstack/react-query";
import {
  Link,
  useLocation,
} from "react-router-dom";

import {
  fetchPortfolioCommandCenterResponse,
  fetchPortfolioContributionResponse,
  fetchPortfolioHierarchyResponse,
  fetchPortfolioLotDetailResponse,
  fetchPortfolioSummaryResponse,
  fetchPortfolioTimeSeriesResponse,
} from "../../core/api/portfolio";
import { prefetchPortfolioRouteQuery } from "../../core/api/portfolio-route-query";
import { ReportUtilityDock } from "../../features/report-utility/ReportUtilityDock";

type CompactDashboardShellProps = PropsWithChildren<{
  title: string;
  subtitle: string;
  assetDetailHref?: string;
}>;

type CompactRouteNavItem = {
  label: string;
  pathPattern: string;
  href: string;
  decisionQuestion: string;
};

type RouteDensity =
  | "ultra-compact"
  | "compact"
  | "balanced"
  | "comfortable"
  | "dense";

const COMPACT_ROUTE_NAV_ITEMS: CompactRouteNavItem[] = [
  {
    label: "Home",
    pathPattern: "/portfolio/home",
    href: "/portfolio/home",
    decisionQuestion: "How is my portfolio doing right now?",
  },
  {
    label: "Analytics",
    pathPattern: "/portfolio/analytics",
    href: "/portfolio/analytics",
    decisionQuestion: "Why did the portfolio move?",
  },
  {
    label: "Risk",
    pathPattern: "/portfolio/risk",
    href: "/portfolio/risk",
    decisionQuestion: "How fragile is the portfolio?",
  },
  {
    label: "Opportunities",
    pathPattern: "/portfolio/signals",
    href: "/portfolio/signals",
    decisionQuestion: "Which opportunities deserve review?",
  },
  {
    label: "Asset Detail",
    pathPattern: "/portfolio/asset-detail/:ticker",
    href: "/portfolio/asset-detail/UNKNOWN",
    decisionQuestion: "What is happening with this asset?",
  },
];

function resolveActive(pathname: string, targetPath: string): boolean {
  if (targetPath.includes(":")) {
    return pathname.startsWith("/portfolio/asset-detail/");
  }
  return pathname === targetPath;
}

function isAssetDetailRoute(pathname: string): boolean {
  return pathname.startsWith("/portfolio/asset-detail/");
}

function resolveRouteDensity(pathname: string, viewportWidth: number): RouteDensity {
  if (viewportWidth <= 320) {
    return "ultra-compact";
  }
  if (viewportWidth <= 768) {
    return "compact";
  }
  if (viewportWidth <= 1024) {
    return isAssetDetailRoute(pathname) ? "compact" : "balanced";
  }
  if (viewportWidth <= 1440) {
    return isAssetDetailRoute(pathname) ? "dense" : "comfortable";
  }
  return isAssetDetailRoute(pathname) ? "dense" : "comfortable";
}

function resolveAssetDetailTicker(href: string): string | null {
  if (!href.startsWith("/portfolio/asset-detail/")) {
    return null;
  }

  const rawTicker = href.replace("/portfolio/asset-detail/", "").trim().toUpperCase();
  if (rawTicker.length === 0 || rawTicker === "UNKNOWN") {
    return null;
  }

  return rawTicker;
}

export function CompactDashboardShell({
  title,
  subtitle,
  assetDetailHref = "/portfolio/asset-detail/UNKNOWN",
  children,
}: CompactDashboardShellProps) {
  const queryClient = useQueryClient();
  const location = useLocation();
  const [isJourneyVisible, setIsJourneyVisible] = useState(true);
  const viewportWidth = typeof window === "undefined" ? 1440 : window.innerWidth;
  const routeDensity = resolveRouteDensity(location.pathname, viewportWidth);
  const compactRouteNavItems: CompactRouteNavItem[] = COMPACT_ROUTE_NAV_ITEMS.map((item) =>
    item.pathPattern === "/portfolio/asset-detail/:ticker"
      ? { ...item, href: assetDetailHref }
      : item,
  );
  const prefetchRoute = useCallback(
    (href: string) => {
      if (href === "/portfolio/home") {
        void Promise.all([
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/command-center",
            loader: fetchPortfolioCommandCenterResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/summary",
            loader: fetchPortfolioSummaryResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/hierarchy",
            query: { group_by: "sector" },
            loader: fetchPortfolioHierarchyResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/time-series",
            query: { period: "90D", scope: "portfolio" },
            loader: () => fetchPortfolioTimeSeriesResponse("90D", "portfolio"),
          }),
        ]);
        return;
      }

      if (href === "/portfolio/analytics") {
        void Promise.all([
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/summary",
            loader: fetchPortfolioSummaryResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/hierarchy",
            query: { group_by: "sector" },
            loader: fetchPortfolioHierarchyResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/contribution",
            query: { period: "YTD" },
            loader: () => fetchPortfolioContributionResponse("YTD"),
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/time-series",
            query: { period: "90D", scope: "portfolio" },
            loader: () => fetchPortfolioTimeSeriesResponse("90D", "portfolio"),
          }),
        ]);
        return;
      }

      if (href === "/portfolio/risk") {
        void Promise.all([
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/summary",
            loader: fetchPortfolioSummaryResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/command-center",
            loader: fetchPortfolioCommandCenterResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/hierarchy",
            query: { group_by: "sector" },
            loader: fetchPortfolioHierarchyResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/time-series",
            query: { period: "90D", scope: "portfolio" },
            loader: () => fetchPortfolioTimeSeriesResponse("90D", "portfolio"),
          }),
        ]);
        return;
      }

      if (href === "/portfolio/signals") {
        void Promise.all([
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/summary",
            loader: fetchPortfolioSummaryResponse,
          }),
          prefetchPortfolioRouteQuery({
            queryClient,
            path: "/portfolio/hierarchy",
            query: { group_by: "sector" },
            loader: fetchPortfolioHierarchyResponse,
          }),
        ]);
        return;
      }

      const ticker = resolveAssetDetailTicker(href);
      if (ticker === null) {
        return;
      }

      void Promise.all([
        prefetchPortfolioRouteQuery({
          queryClient,
          path: `/portfolio/lots/${ticker}`,
          loader: () => fetchPortfolioLotDetailResponse(ticker),
        }),
        prefetchPortfolioRouteQuery({
          queryClient,
          path: "/portfolio/time-series",
          query: {
            period: "90D",
            scope: "instrument_symbol",
            instrument_symbol: ticker,
          },
          loader: () => fetchPortfolioTimeSeriesResponse("90D", "instrument_symbol", ticker),
        }),
      ]);
    },
    [queryClient],
  );

  return (
    <div className="compact-shell" data-route-density={routeDensity}>
      <div className="compact-shell__frame">
        <header className="compact-shell__header">
          <p className="route-kicker">Portfolio Intelligence Workspace</p>
          <h1 className="compact-shell__title">{title}</h1>
          <p className="compact-shell__subtitle">{subtitle}</p>
          <nav className="compact-shell__nav" aria-label="Compact dashboard routes">
            {compactRouteNavItems.map((item) => {
              const isActive = resolveActive(location.pathname, item.pathPattern);
              return (
                <Link
                  key={item.pathPattern}
                  className={`compact-shell__nav-link${isActive ? " is-active" : ""}`}
                  to={item.href}
                  onFocus={() => prefetchRoute(item.href)}
                  onMouseEnter={() => prefetchRoute(item.href)}
                  aria-current={isActive ? "page" : undefined}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <button
            aria-label="Toggle route decision journey"
            aria-pressed={isJourneyVisible}
            className="compact-shell__journey-toggle"
            onClick={() => setIsJourneyVisible((previousState) => !previousState)}
            type="button"
          >
            ☰
          </button>
          <ol
            className="compact-shell__journey"
            aria-label="Route decision journey"
            hidden={!isJourneyVisible}
          >
            {compactRouteNavItems.map((item) => {
              const isActive = resolveActive(location.pathname, item.pathPattern);
              return (
                <li
                  key={item.pathPattern}
                  className={`compact-shell__journey-item${isActive ? " is-active" : ""}`}
                >
                  <span className="compact-shell__journey-route">{item.label}</span>
                  <span className="compact-shell__journey-question">
                    {item.decisionQuestion}
                  </span>
                </li>
              );
            })}
          </ol>
          <div className="compact-shell__support-rail">
            <span>Route lens: {title}</span>
            <span>Shell mode: compact-first</span>
            <span>Trust context: explicit ledger-backed provenance</span>
          </div>
        </header>

        <main
          className="compact-shell__content"
          data-overflow-contract="no-horizontal-overflow"
          id="compact-shell-main-content"
        >
          {children}
          <details className="panel disclosure-panel compact-shell__utility-disclosure">
            <summary>Compact report utility</summary>
            <ReportUtilityDock />
          </details>
        </main>
      </div>
    </div>
  );
}
