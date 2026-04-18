import {
  describe,
  expect,
  it,
} from "vitest";

import {
  resolveSourceContractHealth,
  type SourceContractRecord,
  type SourceContractRegistry,
} from "./source-contracts";

type CompleteSourceContracts = {
  market_prices: SourceContractRecord;
  fundamentals: SourceContractRecord;
  reference_metadata: SourceContractRecord;
  derived_signals: SourceContractRecord;
};

const BASE_SOURCE_CONTRACTS: CompleteSourceContracts = {
  market_prices: {
    category: "market_prices",
    source_id: "yfinance.prices.ohlcv",
    as_of: "2026-04-18T14:30:00-04:00",
    freshness_state: "fresh",
    confidence_state: "direct",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
  fundamentals: {
    category: "fundamentals",
    source_id: "yfinance.fundamentals.ratios",
    as_of: "2026-04-17T20:15:00-04:00",
    freshness_state: "delayed",
    confidence_state: "direct",
    timezone: "America/New_York",
    session: "closed",
    provider_health: "ok",
  },
  reference_metadata: {
    category: "reference_metadata",
    source_id: "yfinance.reference.metadata",
    as_of: "2026-04-18T09:40:00-04:00",
    freshness_state: "fresh",
    confidence_state: "direct",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
  derived_signals: {
    category: "derived_signals",
    source_id: "pandas.derived.signals.v1",
    as_of: "2026-04-18T14:31:00-04:00",
    freshness_state: "fresh",
    confidence_state: "derived",
    timezone: "America/New_York",
    session: "regular",
    provider_health: "ok",
  },
};

describe("source contract reliability contract", () => {
  it("4.7 degrades to stale when required contracts violate freshness policy", () => {
    const staleContracts: SourceContractRegistry = {
      ...BASE_SOURCE_CONTRACTS,
      market_prices: {
        ...BASE_SOURCE_CONTRACTS.market_prices,
        freshness_state: "stale",
      },
    };

    const health = resolveSourceContractHealth({
      contracts: staleContracts,
      requiredCategories: ["market_prices", "derived_signals"],
      expectedTimezone: "America/New_York",
    });

    expect(health.lifecycleState).toBe("stale");
    expect(health.reasonCode).toBe("freshness_sla_expired");
  });

  it("4.7 marks module unavailable when required contracts are missing", () => {
    const contractsWithoutFundamentals: SourceContractRegistry = {
      market_prices: BASE_SOURCE_CONTRACTS.market_prices,
      reference_metadata: BASE_SOURCE_CONTRACTS.reference_metadata,
      derived_signals: BASE_SOURCE_CONTRACTS.derived_signals,
    };

    const health = resolveSourceContractHealth({
      contracts: contractsWithoutFundamentals,
      requiredCategories: ["market_prices", "fundamentals"],
      expectedTimezone: "America/New_York",
    });

    expect(health.lifecycleState).toBe("unavailable");
    expect(health.reasonCode).toBe("fundamental_contract_missing");
    expect(health.failingCategory).toBe("fundamentals");
  });

  it("4.7 blocks modules on timezone/session mismatch to avoid false precision", () => {
    const timezoneMismatchContracts: SourceContractRegistry = {
      ...BASE_SOURCE_CONTRACTS,
      market_prices: {
        ...BASE_SOURCE_CONTRACTS.market_prices,
        timezone: "UTC",
      },
    };

    const health = resolveSourceContractHealth({
      contracts: timezoneMismatchContracts,
      requiredCategories: ["market_prices", "derived_signals"],
      expectedTimezone: "America/New_York",
    });

    expect(health.lifecycleState).toBe("blocked");
    expect(health.reasonCode).toBe("timezone_session_mismatch");
    expect(health.failingCategory).toBe("market_prices");
  });

  it("4.7 keeps provider failures localized to module-level error state", () => {
    const providerFailureContracts: SourceContractRegistry = {
      ...BASE_SOURCE_CONTRACTS,
      derived_signals: {
        ...BASE_SOURCE_CONTRACTS.derived_signals,
        provider_health: "failed",
      },
    };

    const health = resolveSourceContractHealth({
      contracts: providerFailureContracts,
      requiredCategories: ["market_prices", "derived_signals"],
      expectedTimezone: "America/New_York",
    });

    expect(health.lifecycleState).toBe("error");
    expect(health.reasonCode).toBe("provider_failure");
    expect(health.failingCategory).toBe("derived_signals");
  });
});
