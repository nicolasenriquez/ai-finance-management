import { fetchJson } from "../../core/api/client";
import {
  portfolioLotDetailResponseSchema,
  type PortfolioLotDetailResponse,
} from "../../core/api/schemas";

export function fetchPortfolioLotDetail(
  symbol: string,
): Promise<PortfolioLotDetailResponse> {
  return fetchJson({
    path: `/portfolio/lots/${encodeURIComponent(symbol)}`,
    schema: portfolioLotDetailResponseSchema,
  });
}
