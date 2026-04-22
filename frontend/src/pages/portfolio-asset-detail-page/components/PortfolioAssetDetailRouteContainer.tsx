import { PortfolioAssetDetailRouteView } from "./PortfolioAssetDetailRouteView";
import { usePortfolioAssetDetailRouteState } from "../hooks/usePortfolioAssetDetailRouteState";

export function PortfolioAssetDetailRouteContainer() {
  const routeState = usePortfolioAssetDetailRouteState();
  return <PortfolioAssetDetailRouteView routeState={routeState} />;
}
