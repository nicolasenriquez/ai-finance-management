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
        path: "reports",
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
        path: ":symbol",
        element: <PortfolioLotDetailPage />,
      },
    ],
  },
]);
