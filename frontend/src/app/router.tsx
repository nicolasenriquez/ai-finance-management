import {
  type ReactNode,
  Suspense,
  lazy,
} from "react";
import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

const PortfolioHomePage = lazy(async () => ({
  default: (await import("../pages/portfolio-home-page/PortfolioHomePage")).PortfolioHomePage,
}));
const PortfolioAnalyticsPage = lazy(async () => ({
  default: (await import("../pages/portfolio-analytics-page/PortfolioAnalyticsPage")).PortfolioAnalyticsPage,
}));
const PortfolioRiskPage = lazy(async () => ({
  default: (await import("../pages/portfolio-risk-page/PortfolioRiskPage")).PortfolioRiskPage,
}));
const PortfolioSignalsPage = lazy(async () => ({
  default: (await import("../pages/portfolio-signals-page/PortfolioSignalsPage")).PortfolioSignalsPage,
}));
const PortfolioAssetDetailPage = lazy(async () => ({
  default: (await import("../pages/portfolio-asset-detail-page/PortfolioAssetDetailPage")).PortfolioAssetDetailPage,
}));

function withRouteSuspense(node: ReactNode): ReactNode {
  return (
    <Suspense
      fallback={(
        <section
          aria-live="polite"
          className="route-lazy-fallback"
          role="status"
        >
          Loading route module...
        </section>
      )}
    >
      {node}
    </Suspense>
  );
}

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/portfolio/home" replace />,
  },
  {
    path: "/portfolio",
    children: [
      {
        index: true,
        element: <Navigate to="home" replace />,
      },
      {
        path: "home",
        element: withRouteSuspense(<PortfolioHomePage />),
      },
      {
        path: "analytics",
        element: withRouteSuspense(<PortfolioAnalyticsPage />),
      },
      {
        path: "risk",
        element: withRouteSuspense(<PortfolioRiskPage />),
      },
      {
        path: "signals",
        element: withRouteSuspense(<PortfolioSignalsPage />),
      },
      {
        path: "asset-detail/:ticker",
        element: withRouteSuspense(<PortfolioAssetDetailPage />),
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/portfolio/home" replace />,
  },
]);
