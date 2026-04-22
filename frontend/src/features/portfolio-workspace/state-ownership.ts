export type DashboardStateOwner = "local_ui" | "url_state" | "server_state";

type DashboardStateKey =
  | "route_journey_visibility"
  | "module_state"
  | "report_scope"
  | "source_contracts"
  | "yfinance_adapter_rows";

const DASHBOARD_STATE_OWNERS: Record<DashboardStateKey, DashboardStateOwner> = {
  route_journey_visibility: "local_ui",
  module_state: "url_state",
  report_scope: "url_state",
  source_contracts: "server_state",
  yfinance_adapter_rows: "server_state",
};

export function resolveDashboardStateOwner(stateKey: string): DashboardStateOwner {
  if (stateKey in DASHBOARD_STATE_OWNERS) {
    return DASHBOARD_STATE_OWNERS[stateKey as DashboardStateKey];
  }
  return "local_ui";
}

export function shouldAllowPropDrillDepth(depth: number): boolean {
  return depth <= 3;
}
