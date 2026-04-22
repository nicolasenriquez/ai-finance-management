import { PortfolioSignalsRouteView } from "./PortfolioSignalsRouteView";
import { usePortfolioSignalsRouteState } from "../hooks/usePortfolioSignalsRouteState";

export function PortfolioSignalsRouteContainer() {
  const routeState = usePortfolioSignalsRouteState();
  return <PortfolioSignalsRouteView routeState={routeState} />;
}
