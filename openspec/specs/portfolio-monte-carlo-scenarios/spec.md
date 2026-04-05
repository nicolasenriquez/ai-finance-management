# portfolio-monte-carlo-scenarios Specification

## Purpose
TBD - created by archiving change phase-g-quantstats-monte-carlo-and-risk-evolution. Update Purpose after archive.
## Requirements
### Requirement: Portfolio Monte Carlo simulation SHALL support deterministic scope-bounded execution
The system SHALL expose Monte Carlo simulation for approved scopes (`portfolio` or `instrument_symbol`) using persisted return history and explicit parameter handling.

#### Scenario: Portfolio-scope simulation returns deterministic summary output
- **WHEN** a client requests Monte Carlo for `portfolio` scope with valid parameters
- **THEN** the API returns simulation summary statistics and percentile outputs for the requested horizon
- **THEN** the response includes explicit scope, period, and seed metadata

#### Scenario: Instrument-scope simulation is supported with explicit symbol binding
- **WHEN** a client requests Monte Carlo for `instrument_symbol` scope with a valid symbol
- **THEN** the simulation uses only the persisted return history for that symbol scope
- **THEN** the response echoes the resolved symbol and scope context

### Requirement: Monte Carlo request parameters SHALL be explicitly validated and bounded
The system SHALL reject simulation requests that violate approved parameter bounds for simulation count, horizon, or threshold semantics.

#### Scenario: Invalid simulation parameters are rejected explicitly
- **WHEN** a client submits unsupported values for `sims`, horizon, `bust`, or `goal`
- **THEN** the API returns explicit client-facing validation failure
- **THEN** the service does not run a partial or coerced simulation

### Requirement: Monte Carlo output SHALL expose assumptions and probability context
Simulation responses SHALL include explicit assumption metadata and probability outputs required for interpretation.

#### Scenario: Bust and goal probabilities are reported with assumptions
- **WHEN** simulation executes successfully with configured `bust` and `goal` thresholds
- **THEN** the response includes `bust_probability` and `goal_probability` outputs
- **THEN** the response includes assumption metadata indicating shuffled-return simulation semantics

### Requirement: Monte Carlo simulation requests SHALL remain read-only over portfolio truth
Simulation execution SHALL not mutate canonical, ledger, lot, or market-data state.

#### Scenario: Simulation request performs no state mutation
- **WHEN** a client requests Monte Carlo output
- **THEN** the service reads persisted state and returns computed simulation payloads
- **THEN** no insert, update, or delete occurs in canonical, ledger, lot, or market-data tables

### Requirement: Monte Carlo diagnostics SHALL support deterministic profile-scenario comparison outputs
The system SHALL support a deterministic three-profile scenario matrix (`Conservative`, `Balanced`, `Growth`) evaluated from one simulation context so users can compare bust/goal outcomes side by side.

#### Scenario: One simulation context yields three deterministic profile outcomes
- **WHEN** a client requests Monte Carlo diagnostics with profile comparison enabled
- **THEN** the response includes `profile_scenarios[]` with exactly three profile rows and their threshold/probability outcomes
- **THEN** profile outputs are derived from the same scope, period, horizon, seed, and simulation path set used for the request

### Requirement: Profile thresholds SHALL support historical calibration basis with explicit metadata
The system SHALL support threshold calibration from persisted realized returns using approved basis values (`monthly`, `annual`, `manual`) and SHALL expose calibration metadata for interpretation.

#### Scenario: Historical calibration basis is explicit in response metadata
- **WHEN** a client requests profile comparison with `monthly` or `annual` calibration
- **THEN** response metadata includes basis, sample size, lookback span, and effective threshold values per profile
- **THEN** thresholds remain bounded by the existing Monte Carlo validation envelope

### Requirement: Calibration insufficiency SHALL fail-fast or fall back explicitly without silent behavior
When historical observations are insufficient for a requested calibration basis, the service SHALL not silently fabricate calibrated thresholds.

#### Scenario: Insufficient historical sample exposes explicit fallback reason
- **WHEN** the requested calibration basis lacks sufficient observations
- **THEN** the response includes explicit fallback metadata (`fallback_reason`, effective basis/default policy)
- **THEN** clients can distinguish calibrated and fallback profile scenarios deterministically

### Requirement: Monte Carlo outputs SHALL include health-sensitivity bridge metadata
Simulation responses SHALL include deterministic bridge metadata so clients can explain how scenario probabilities reinforce or challenge current portfolio-health interpretation.

#### Scenario: Profile probabilities expose health-sensitivity signal
- **WHEN** profile comparison is enabled and simulation succeeds
- **THEN** each profile output includes a qualitative sensitivity signal derived from bust/goal probabilities under current thresholds
- **THEN** metadata is explicit and non-prescriptive, allowing clients to render health-context explanations without hidden heuristics
