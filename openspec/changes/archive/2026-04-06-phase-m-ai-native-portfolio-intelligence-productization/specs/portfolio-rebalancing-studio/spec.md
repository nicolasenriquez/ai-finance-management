## ADDED Requirements

### Requirement: Rebalancing studio SHALL expose strategy-comparison outputs for approved v1 methods
The system SHALL expose deterministic portfolio rebalancing outputs for approved v1 strategies `MVO`, `HRP`, and `Black-Litterman` using typed constraints and explicit methodology metadata.

#### Scenario: Strategy comparison returns current and candidate allocations
- **WHEN** a client requests rebalancing diagnostics for a supported scope and period
- **THEN** the response includes current weights and candidate weights for each approved strategy
- **THEN** each strategy includes expected risk/return, concentration context, and methodology identifiers

#### Scenario: Unsupported strategy is requested
- **WHEN** a client requests a strategy outside the approved v1 allowlist
- **THEN** the request is rejected with explicit validation failure
- **THEN** no fallback strategy is executed silently

### Requirement: Rebalancing studio SHALL support bounded scenario constraints
The system SHALL support typed scenario constraints (for example max position weight, turnover bounds, or symbol exclusions) and SHALL expose applied constraints in results.

#### Scenario: Valid constraints are applied
- **WHEN** a scenario request includes valid constraints
- **THEN** the optimizer output includes applied-constraint metadata and any binding constraints by symbol
- **THEN** users can compare constrained results to unconstrained baseline outputs deterministically

#### Scenario: Constraint set is infeasible
- **WHEN** constraints create an infeasible optimization problem
- **THEN** the response returns explicit infeasible-state metadata with factual cause context
- **THEN** the system does not return fabricated candidate weights

### Requirement: Rebalancing outputs SHALL remain read-only and non-executional
The system SHALL keep rebalancing endpoints analytical-only and SHALL not trigger orders, broker mutations, or autonomous rebalance actions.

#### Scenario: Rebalancing request remains analytical
- **WHEN** a client requests strategy comparison or scenario analysis
- **THEN** the request path computes and returns diagnostics only
- **THEN** no execution side effects are produced in external broker or internal ledger state
