import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import { PortfolioAnalyticsPage } from "../pages/portfolio-analytics-page/PortfolioAnalyticsPage";
import { PortfolioHomePage } from "../pages/portfolio-home-page/PortfolioHomePage";
import { PortfolioLotDetailPage } from "../pages/portfolio-lot-detail-page/PortfolioLotDetailPage";
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
    path: "/portfolio/transactions",
    element: <PortfolioTransactionsPage />,
  },
  {
    path: "/portfolio/:symbol",
    element: <PortfolioLotDetailPage />,
  },
]);
