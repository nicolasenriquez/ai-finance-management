## ADDED Requirements

### Requirement: Market-data operations SHALL expose local operator entrypoints for refresh and sync workflows
The system SHALL expose explicit local operator entrypoints for market refresh and combined data sync without requiring a new public market-data API route in this slice.

#### Scenario: Operator runs local market refresh entrypoint
- **WHEN** an operator invokes the local market-refresh command workflow
- **THEN** the system executes the existing supported-universe refresh seam through `yfinance`
- **THEN** the workflow returns structured outcome evidence for that refresh run

#### Scenario: Operator runs local combined sync entrypoint
- **WHEN** an operator invokes the local combined sync workflow
- **THEN** the system executes bootstrap and refresh in deterministic order
- **THEN** it reports explicit success/failure status for the overall operation

#### Scenario: Operator workflows fail fast
- **WHEN** a refresh or sync stage cannot complete safely
- **THEN** the workflow exits with explicit failure and actionable context
- **THEN** the system does not treat partially completed sync stages as a successful run
