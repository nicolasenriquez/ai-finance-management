import {
  describe,
  expect,
  it,
} from "vitest";

import {
  createDashboardResearchControls,
  resolveDecisionStateWithResearchControls,
  resolveResearchModuleGate,
} from "./feature-flags";

describe("research feature flags and kill-switch contract", () => {
  it("4.8 keeps technical signals gated until `advanced_signals_enabled` is true", () => {
    const controls = createDashboardResearchControls({
      flags: {
        advanced_signals_enabled: false,
        fundamentals_contract_v1: true,
      },
      kill_switches: {
        high_risk_research_modules_disabled: false,
        advanced_decision_states_disabled: false,
      },
    });

    const moduleGate = resolveResearchModuleGate("technical_signals_table", controls);

    expect(moduleGate.enabled).toBe(false);
    expect(moduleGate.reason).toContain("advanced_signals_enabled");
  });

  it("4.8 kill-switch disables high-risk modules even when feature flags are on", () => {
    const controls = createDashboardResearchControls({
      flags: {
        advanced_signals_enabled: true,
        fundamentals_contract_v1: true,
      },
      kill_switches: {
        high_risk_research_modules_disabled: true,
        advanced_decision_states_disabled: false,
      },
    });

    const technicalGate = resolveResearchModuleGate("technical_signals_table", controls);
    const fundamentalsGate = resolveResearchModuleGate("watchlist_fundamentals_overlay", controls);

    expect(technicalGate.enabled).toBe(false);
    expect(fundamentalsGate.enabled).toBe(false);
    expect(technicalGate.reason).toContain("kill-switch");
    expect(fundamentalsGate.reason).toContain("kill-switch");
  });

  it("4.8 downgrades buy/add decisions when advanced decision state kill-switch is active", () => {
    const controls = createDashboardResearchControls({
      flags: {
        advanced_signals_enabled: true,
        fundamentals_contract_v1: true,
      },
      kill_switches: {
        high_risk_research_modules_disabled: false,
        advanced_decision_states_disabled: true,
      },
    });

    const downgradedBuy = resolveDecisionStateWithResearchControls("buy", controls);
    const downgradedAdd = resolveDecisionStateWithResearchControls("add", controls);

    expect(downgradedBuy.state).toBe("wait");
    expect(downgradedAdd.state).toBe("wait");
    expect(downgradedBuy.reason).toContain("advanced decision state");
  });
});
