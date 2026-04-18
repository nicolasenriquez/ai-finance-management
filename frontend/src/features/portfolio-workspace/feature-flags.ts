export type DashboardResearchFlags = {
  advanced_signals_enabled: boolean;
  fundamentals_contract_v1: boolean;
};

export type DashboardResearchKillSwitches = {
  high_risk_research_modules_disabled: boolean;
  advanced_decision_states_disabled: boolean;
};

export type DashboardResearchControls = {
  flags: DashboardResearchFlags;
  kill_switches: DashboardResearchKillSwitches;
};

export type DashboardResearchControlsOverrides = {
  flags?: Partial<DashboardResearchFlags>;
  kill_switches?: Partial<DashboardResearchKillSwitches>;
};

export type ResearchModuleKey =
  | "technical_signals_table"
  | "watchlist_fundamentals_overlay"
  | "advanced_decision_state";

export type ResearchModuleGate = {
  enabled: boolean;
  reason: string;
};

export type RouteDecisionState = "buy" | "add" | "wait" | "avoid" | "unavailable";

export type RouteDecisionResolution = {
  state: RouteDecisionState;
  reason: string;
};

function parseBooleanEnv(value: string | undefined, fallback: boolean): boolean {
  if (!value) {
    return fallback;
  }
  const normalized = value.trim().toLowerCase();
  if (normalized === "true" || normalized === "1" || normalized === "yes") {
    return true;
  }
  if (normalized === "false" || normalized === "0" || normalized === "no") {
    return false;
  }
  return fallback;
}

const DEFAULT_CONTROLS: DashboardResearchControls = {
  flags: {
    advanced_signals_enabled: false,
    fundamentals_contract_v1: false,
  },
  kill_switches: {
    high_risk_research_modules_disabled: false,
    advanced_decision_states_disabled: false,
  },
};

export function createDashboardResearchControls(
  overrides?: DashboardResearchControlsOverrides,
): DashboardResearchControls {
  return {
    flags: {
      ...DEFAULT_CONTROLS.flags,
      ...overrides?.flags,
    },
    kill_switches: {
      ...DEFAULT_CONTROLS.kill_switches,
      ...overrides?.kill_switches,
    },
  };
}

export function getDashboardResearchControls(): DashboardResearchControls {
  return createDashboardResearchControls({
    flags: {
      advanced_signals_enabled: parseBooleanEnv(
        import.meta.env.VITE_ADVANCED_SIGNALS_ENABLED,
        DEFAULT_CONTROLS.flags.advanced_signals_enabled,
      ),
      fundamentals_contract_v1: parseBooleanEnv(
        import.meta.env.VITE_FUNDAMENTALS_CONTRACT_V1,
        DEFAULT_CONTROLS.flags.fundamentals_contract_v1,
      ),
    },
    kill_switches: {
      high_risk_research_modules_disabled: parseBooleanEnv(
        import.meta.env.VITE_KILL_SWITCH_HIGH_RISK_RESEARCH,
        DEFAULT_CONTROLS.kill_switches.high_risk_research_modules_disabled,
      ),
      advanced_decision_states_disabled: parseBooleanEnv(
        import.meta.env.VITE_KILL_SWITCH_ADVANCED_DECISION_STATES,
        DEFAULT_CONTROLS.kill_switches.advanced_decision_states_disabled,
      ),
    },
  });
}

export function resolveResearchModuleGate(
  moduleKey: ResearchModuleKey,
  controls: DashboardResearchControls,
): ResearchModuleGate {
  if (controls.kill_switches.high_risk_research_modules_disabled) {
    return {
      enabled: false,
      reason:
        "high-risk research module kill-switch is active. Module rendering is explicitly disabled.",
    };
  }

  if (
    moduleKey === "technical_signals_table" &&
    !controls.flags.advanced_signals_enabled
  ) {
    return {
      enabled: false,
      reason:
        "`advanced_signals_enabled` is false. Technical signals remain unavailable until explicitly enabled.",
    };
  }

  if (
    moduleKey === "watchlist_fundamentals_overlay" &&
    !controls.flags.fundamentals_contract_v1
  ) {
    return {
      enabled: false,
      reason:
        "`fundamentals_contract_v1` is false. Fundamentals overlays remain unavailable until contract v1 is enabled.",
    };
  }

  if (moduleKey === "advanced_decision_state") {
    if (controls.kill_switches.advanced_decision_states_disabled) {
      return {
        enabled: false,
        reason:
          "advanced decision state kill-switch is active. Buy/Add promotion is disabled.",
      };
    }
    if (
      !controls.flags.advanced_signals_enabled ||
      !controls.flags.fundamentals_contract_v1
    ) {
      return {
        enabled: false,
        reason:
          "advanced decision state requires both `advanced_signals_enabled` and `fundamentals_contract_v1`.",
      };
    }
  }

  return {
    enabled: true,
    reason: "module gate passed",
  };
}

export function resolveDecisionStateWithResearchControls(
  requestedState: RouteDecisionState,
  controls: DashboardResearchControls,
): RouteDecisionResolution {
  if (requestedState !== "buy" && requestedState !== "add") {
    return {
      state: requestedState,
      reason: "requested state does not require advanced decision promotion.",
    };
  }

  const advancedDecisionGate = resolveResearchModuleGate(
    "advanced_decision_state",
    controls,
  );

  if (!advancedDecisionGate.enabled) {
    return {
      state: "wait",
      reason: `advanced decision state downgraded: ${advancedDecisionGate.reason}`,
    };
  }

  return {
    state: requestedState,
    reason: "advanced decision state is enabled for this route.",
  };
}
