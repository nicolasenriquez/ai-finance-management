import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import { PortfolioAnalyticsPage } from "../pages/portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioCopilotPage } from "../pages/portfolio-copilot-page/PortfolioCopilotPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";
import { PortfolioLotDetailPage } from "../pages/portfolio-lot-detail-page/PortfolioLotDetailPage";
import { PortfolioReportsPage } from "../pages/portfolio-reports-page/PortfolioReportsPage";
import { PortfolioRiskPage } from "../pages/portfolio-risk-page/PortfolioRiskPage";
import { PortfolioTransactionsPage } from "../pages/portfolio-transactions-page/PortfolioTransactionsPage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/portfolio/home" replace />,
  },
  {
    path: "/portfolio",
    element: <Navigate to="/portfolio/home" replace />,
  },
  {
    path: "/portfolio/home",
    element: <PortfolioHomePage />,
  },
  {
    path: "/portfolio/analytics",
    element: <PortfolioAnalyticsPage />,
  },
  {
    path: "/portfolio/risk",
    element: <PortfolioRiskPage />,
  },
  {
    path: "/portfolio/reports",
    element: <PortfolioReportsPage />,
  },
  {
    path: "/portfolio/copilot",
    element: <PortfolioCopilotPage />,
  },
  {
    path: "/portfolio/transactions",
    element: <PortfolioTransactionsPage />,
  },
  {
    path: "/portfolio/:symbol",
    element: <PortfolioLotDetailPage />,
  },
]);
