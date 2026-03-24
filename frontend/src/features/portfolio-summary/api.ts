import { fetchJson } from "../../core/api/client";
import {
  portfolioSummaryResponseSchema,
  type PortfolioSummaryResponse,
} from "../../core/api/schemas";

export function fetchPortfolioSummary(): Promise<PortfolioSummaryResponse> {
  return fetchJson({
    path: "/portfolio/summary",
    schema: portfolioSummaryResponseSchema,
  });
}
