import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import { PortfolioAnalyticsPage } from "../pages/portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioAssetDetailPage } from "../pages/portfolio-asset-detail-page/PortfolioAssetDetailPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";
import { PortfolioRiskPage } from "../pages/portfolio-risk-page/PortfolioRiskPage";
import { PortfolioSignalsPage } from "../pages/portfolio-signals-page/PortfolioSignalsPage";

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
        element: <PortfolioHomePage />,
      },
      {
        path: "analytics",
        element: <PortfolioAnalyticsPage />,
      },
      {
        path: "risk",
        element: <PortfolioRiskPage />,
      },
      {
        path: "signals",
        element: <PortfolioSignalsPage />,
      },
      {
        path: "asset-detail/:ticker",
        element: <PortfolioAssetDetailPage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/portfolio/home" replace />,
  },
]);
