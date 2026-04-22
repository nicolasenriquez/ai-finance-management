import {
  resolveUnavailableReasonCopy,
  type UnavailableReasonCode,
  type WorkspaceLifecycleState,
} from "./state-copy";

export type SourceContractCategory =
  | "market_prices"
  | "fundamentals"
  | "reference_metadata"
  | "derived_signals";

export type SourceContractFreshnessState =
  | "fresh"
  | "stale"
  | "delayed"
  | "unavailable";

export type SourceContractConfidenceState = "direct" | "derived" | "proxy";

export type SourceContractProviderHealth = "ok" | "timeout" | "failed";

export type SourceContractSession = "pre" | "regular" | "post" | "closed";

export type SourceContractRecord = {
  category: SourceContractCategory;
  source_id: string;
  as_of: string;
  freshness_state: SourceContractFreshnessState;
  confidence_state: SourceContractConfidenceState;
  timezone: string;
  session: SourceContractSession;
  provider_health: SourceContractProviderHealth;
};

export type SourceContractRegistry = Partial<
  Record<SourceContractCategory, SourceContractRecord>
>;

export type ResolveSourceContractHealthParams = {
  contracts: SourceContractRegistry;
  requiredCategories: SourceContractCategory[];
  expectedTimezone: string;
};

export type SourceContractHealth = {
  lifecycleState: WorkspaceLifecycleState;
  reasonCode?: UnavailableReasonCode;
  message: string;
  failingCategory?: SourceContractCategory;
};

function resolveMissingReasonCode(
  category: SourceContractCategory,
): UnavailableReasonCode {
  if (category === "fundamentals") {
    return "fundamental_contract_missing";
  }
  if (category === "derived_signals") {
    return "technical_contract_missing";
  }
  return "source_contract_missing";
}

function buildFailureHealth(
  lifecycleState: WorkspaceLifecycleState,
  reasonCode: UnavailableReasonCode,
  failingCategory: SourceContractCategory,
): SourceContractHealth {
  return {
    lifecycleState,
    reasonCode,
    failingCategory,
    message: resolveUnavailableReasonCopy(reasonCode),
  };
}

export function resolveSourceContractHealth({
  contracts,
  requiredCategories,
  expectedTimezone,
}: ResolveSourceContractHealthParams): SourceContractHealth {
  if (requiredCategories.length === 0) {
    return buildFailureHealth(
      "unavailable",
      "source_contract_missing",
      "reference_metadata",
    );
  }

  for (const category of requiredCategories) {
    const contract = contracts[category];
    if (!contract) {
      return buildFailureHealth(
        "unavailable",
        resolveMissingReasonCode(category),
        category,
      );
    }

    if (contract.provider_health === "timeout") {
      return buildFailureHealth("error", "provider_timeout", category);
    }

    if (contract.provider_health === "failed") {
      return buildFailureHealth("error", "provider_failure", category);
    }

    if (contract.timezone !== expectedTimezone) {
      return buildFailureHealth("blocked", "timezone_session_mismatch", category);
    }

    if (
      contract.freshness_state === "stale" ||
      contract.freshness_state === "delayed"
    ) {
      return buildFailureHealth("stale", "freshness_sla_expired", category);
    }

    if (contract.freshness_state === "unavailable") {
      return buildFailureHealth(
        "unavailable",
        resolveMissingReasonCode(category),
        category,
      );
    }
  }

  return {
    lifecycleState: "ready",
    message:
      "All required source contracts resolved with expected timezone and freshness posture.",
  };
}

export function listSourceContracts(
  contracts: SourceContractRegistry,
  orderedCategories: SourceContractCategory[],
): SourceContractRecord[] {
  const rows: SourceContractRecord[] = [];
  for (const category of orderedCategories) {
    const contract = contracts[category];
    if (contract) {
      rows.push(contract);
    }
  }
  return rows;
}

export function formatSourceContractEvidence(contract: SourceContractRecord): string {
  return [
    `source_id=${contract.source_id}`,
    `as_of=${contract.as_of}`,
    `freshness_state=${contract.freshness_state}`,
    `confidence_state=${contract.confidence_state}`,
  ].join(" | ");
}
