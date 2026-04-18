import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import { PortfolioAnalyticsPage } from "../pages/portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioCopilotPage } from "../pages/portfolio-copilot-page/PortfolioCopilotPage";
import { PortfolioHoldingsPage } from "../pages/portfolio-holdings-page/PortfolioHoldingsPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";
import { PortfolioLotDetailPage } from "../pages/portfolio-lot-detail-page/PortfolioLotDetailPage";
import { PortfolioReportsPage } from "../pages/portfolio-reports-page/PortfolioReportsPage";
import { PortfolioRiskPage } from "../pages/portfolio-risk-page/PortfolioRiskPage";
import { PortfolioTransactionsPage } from "../pages/portfolio-transactions-page/PortfolioTransactionsPage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/portfolio/dashboard" replace />,
  },
  {
    path: "/portfolio",
    children: [
      {
        index: true,
        element: <Navigate to="dashboard" replace />,
      },
      {
        path: "dashboard",
        element: <PortfolioHomePage />,
      },
      {
        path: "holdings",
        element: <PortfolioHoldingsPage />,
      },
      {
        path: "performance",
        element: <PortfolioAnalyticsPage />,
      },
      {
        path: "risk",
        element: <PortfolioRiskPage />,
      },
      {
        path: "rebalancing",
        element: <PortfolioReportsPage />,
      },
      {
        path: "copilot",
        element: <PortfolioCopilotPage />,
      },
      {
        path: "transactions",
        element: <PortfolioTransactionsPage />,
      },
      {
        path: "home",
        element: <Navigate to="/portfolio/dashboard" replace />,
      },
      {
        path: "analytics",
        element: <Navigate to="/portfolio/performance" replace />,
      },
      {
        path: "reports",
        element: <Navigate to="/portfolio/rebalancing" replace />,
      },
      {
        path: ":symbol",
        element: <PortfolioLotDetailPage />,
      },
    ],
  },
]);
