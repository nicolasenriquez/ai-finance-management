## MODIFIED Requirements

### Requirement: Market-data operations SHALL define one approved operational smoke and blocker-evidence workflow
The system SHALL define one operator-facing verification workflow for `market-refresh-yfinance` and `data-sync-local` that keeps standalone `core` refresh evidence as the required live readiness gate, uses one deterministic representative non-core smoke lane as the default broader-than-core safeguard, treats full-scope `100` refresh as optional manual soak coverage, and excludes `200` from the current routine local-first readiness contract.

#### Scenario: Operator records required standalone core evidence
- **WHEN** an operator performs the approved live smoke workflow for current market-refresh readiness
- **THEN** the workflow records a standalone `core` refresh outcome with the invoked command, selected scope, invocation timestamp, and either typed refresh success evidence or structured blocker evidence
- **THEN** the resulting readiness posture treats that `core` outcome as the required live operational gate for the current portfolio-backed scope

#### Scenario: Operator records required combined sync evidence after core review
- **WHEN** an operator runs the approved `data-sync-local` smoke workflow after the standalone `core` review
- **THEN** the workflow records the command invoked, invocation timestamp, and the combined bootstrap-plus-refresh outcome
- **THEN** the evidence remains sufficient to compare combined sync behavior with the standalone `core` refresh contract without re-parsing logs

#### Scenario: Default broader-than-core verification uses representative non-core smoke
- **WHEN** the repository executes its default broader-than-core market-refresh verification lane
- **THEN** that lane uses `core` plus a deterministic representative non-core sample rather than requiring a full `100` or `200` refresh
- **THEN** the documented readiness contract treats that representative lane as the default safeguard for non-core coverage

#### Scenario: Full-scope 100 refresh remains optional manual soak coverage
- **WHEN** an operator intentionally runs a full `100` refresh outside the routine readiness workflow
- **THEN** the repository treats that execution as optional manual or soak evidence rather than a required local validation gate
- **THEN** current readiness documentation does not imply that full `100` completion is required before downstream work can proceed

#### Scenario: Routine 200 verification is excluded from current readiness posture
- **WHEN** the repository documents or executes the current routine local-first validation workflow
- **THEN** it does not require `200` refresh verification as part of the default readiness posture
- **THEN** the resulting documentation does not imply `200` readiness or routine local expectation in the current phase

#### Scenario: Blocked runs remain first-class evidence
- **WHEN** provider, network, runtime, or data conditions prevent a required or optional verification run from completing safely
- **THEN** the workflow records `status`, `stage`, `status_code`, and `error` plus the attempted scope and invocation timestamp
- **THEN** the runbook treats that blocked outcome as current evidence instead of masking it behind undocumented retries or implied success
