import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import { PortfolioLotDetailPage } from "../pages/portfolio-lot-detail-page/PortfolioLotDetailPage";
import { PortfolioSummaryPage } from "../pages/portfolio-summary-page/PortfolioSummaryPage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/portfolio" replace />,
  },
  {
    path: "/portfolio",
    element: <PortfolioSummaryPage />,
  },
  {
    path: "/portfolio/:symbol",
    element: <PortfolioLotDetailPage />,
  },
]);
