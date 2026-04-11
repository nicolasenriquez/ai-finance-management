# portfolio-decision-command-center Specification

## Purpose
TBD - created by archiving change phase-m-ai-native-portfolio-intelligence-productization. Update Purpose after archive.
## Requirements
### Requirement: Command center SHALL expose a decision-first portfolio posture summary
The system SHALL provide a command-center contract that surfaces net worth, return posture, drawdown context, concentration, and top risk posture indicators in one first-pass payload.

#### Scenario: Command-center payload is ready
- **WHEN** persisted ledger and market snapshots satisfy minimum freshness and coverage requirements
- **THEN** the payload includes net worth, period returns (`1D`, `WTD`, `MTD`, `YTD`), current drawdown, and concentration indicators
- **THEN** the payload includes explicit as-of timestamps and scope metadata for interpretation

#### Scenario: Required inputs are incomplete
- **WHEN** required summary or market coverage is missing for one or more command-center indicators
- **THEN** the endpoint returns explicit unavailable or partial-state metadata with factual missing-input reasons
- **THEN** the system does not silently fabricate default metric values

### Requirement: Command center SHALL include explainable insight cards with provenance
The system SHALL generate bounded insight cards that explain portfolio posture changes using deterministic analytics context and explicit provenance metadata.

#### Scenario: Insight cards are generated from deterministic context
- **WHEN** command-center insights are returned
- **THEN** each insight includes a stable insight type, evidence references, and confidence/coverage context
- **THEN** insights avoid guaranteed-return language and keep non-advice posture explicit

#### Scenario: Insight generation has insufficient context
- **WHEN** the insight engine cannot meet minimum evidence coverage for one insight family
- **THEN** the response states the insight family as unavailable with explicit reason metadata
- **THEN** remaining valid insights continue to render without masking the unavailable state

### Requirement: Command center SHALL expose benchmark-relative context explicitly
The system SHALL expose benchmark-relative performance context in command-center responses using approved benchmark identifiers and explicit comparability metadata.

#### Scenario: Benchmark comparison is available
- **WHEN** selected benchmark history is available for the requested period
- **THEN** the payload includes portfolio vs benchmark return deltas and benchmark identifier metadata
- **THEN** the payload includes comparability caveats when trading-calendar or coverage mismatches exist

#### Scenario: Benchmark comparison is unavailable
- **WHEN** benchmark history is missing or below required coverage
- **THEN** benchmark fields are marked unavailable with factual reason metadata
- **THEN** the system does not infer synthetic benchmark values
