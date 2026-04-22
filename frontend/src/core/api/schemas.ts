import { z } from "zod";

export const workspaceLifecycleStateSchema = z.enum([
  "loading",
  "empty",
  "ready",
  "stale",
  "unavailable",
  "blocked",
  "error",
]);

export const reportLifecycleStateSchema = z.enum([
  "requested",
  "generated",
  "preview_ready",
  "error",
  "unavailable",
]);

export const reportScopeSchema = z.enum(["portfolio", "symbol"]);

export const compactRouteSchema = z.enum([
  "home",
  "analytics",
  "risk",
  "signals",
  "asset_detail",
]);

export const sourceContractCategorySchema = z.enum([
  "market_prices",
  "fundamentals",
  "reference_metadata",
  "derived_signals",
]);

export const sourceContractFreshnessStateSchema = z.enum([
  "fresh",
  "stale",
  "delayed",
  "unavailable",
]);

export const sourceContractConfidenceStateSchema = z.enum([
  "direct",
  "derived",
  "proxy",
]);

export const sourceContractProviderHealthSchema = z.enum([
  "ok",
  "timeout",
  "failed",
]);

export const sourceContractSessionSchema = z.enum([
  "pre",
  "regular",
  "post",
  "closed",
]);

export const sourceContractSchema = z.object({
  category: sourceContractCategorySchema,
  source_id: z.string(),
  as_of: z.string(),
  freshness_state: sourceContractFreshnessStateSchema,
  confidence_state: sourceContractConfidenceStateSchema,
  timezone: z.string(),
  session: sourceContractSessionSchema,
  provider_health: sourceContractProviderHealthSchema,
});

export const sourceContractRegistrySchema = z.object({
  market_prices: sourceContractSchema.optional(),
  fundamentals: sourceContractSchema.optional(),
  reference_metadata: sourceContractSchema.optional(),
  derived_signals: sourceContractSchema.optional(),
});

export const dashboardResearchControlsSchema = z.object({
  flags: z.object({
    advanced_signals_enabled: z.boolean(),
    fundamentals_contract_v1: z.boolean(),
  }),
  kill_switches: z.object({
    high_risk_research_modules_disabled: z.boolean(),
    advanced_decision_states_disabled: z.boolean(),
  }),
});

export const routeModuleStateSchema = z.object({
  route: compactRouteSchema,
  lifecycle_state: workspaceLifecycleStateSchema,
  as_of: z.string().nullable(),
  provenance: z.string().nullable(),
});

export type WorkspaceLifecycleState = z.infer<typeof workspaceLifecycleStateSchema>;
export type ReportLifecycleState = z.infer<typeof reportLifecycleStateSchema>;
export type ReportScope = z.infer<typeof reportScopeSchema>;
export type CompactRoute = z.infer<typeof compactRouteSchema>;
export type SourceContractCategory = z.infer<typeof sourceContractCategorySchema>;
export type SourceContractFreshnessState = z.infer<typeof sourceContractFreshnessStateSchema>;
export type SourceContractConfidenceState = z.infer<typeof sourceContractConfidenceStateSchema>;
export type SourceContractProviderHealth = z.infer<typeof sourceContractProviderHealthSchema>;
export type SourceContractSession = z.infer<typeof sourceContractSessionSchema>;
export type SourceContract = z.infer<typeof sourceContractSchema>;
export type SourceContractRegistry = z.infer<typeof sourceContractRegistrySchema>;
export type DashboardResearchControls = z.infer<typeof dashboardResearchControlsSchema>;
export type RouteModuleState = z.infer<typeof routeModuleStateSchema>;
