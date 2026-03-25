## MODIFIED Requirements

### Requirement: Market-data operations SHALL provide a manual full-refresh workflow for the supported symbol universe
The system SHALL provide one explicit operator-facing workflow that refreshes market data for one selected supported-universe scope mode (`core`, `100`, or `200`) using the existing `yfinance` ingestion path.

#### Scenario: Operator runs a full refresh with explicit scope mode
- **WHEN** the operator triggers the market-data full-refresh workflow and selects a scope mode
- **THEN** the system requests the symbols resolved for that selected scope mode through the existing `yfinance` provider path
- **THEN** the resulting market-data writes are persisted through the existing market-data ingestion contract rather than a second write path

#### Scenario: Operator runs a full refresh without explicit scope mode
- **WHEN** the operator triggers the market-data full-refresh workflow without passing a scope mode
- **THEN** the system defaults the refresh scope mode to `core`
- **THEN** the system requests only the symbols resolved for `core`

#### Scenario: Refresh scope mode contract is validated
- **WHEN** the system receives a refresh-scope selector for operator full refresh
- **THEN** the selector is validated against the allowed typed set (`core`, `100`, `200`)
- **THEN** values outside that set are rejected explicitly before provider ingestion starts

### Requirement: Market-data operations SHALL use one explicit supported-symbol source
The system SHALL resolve full-refresh scope from one central supported-symbol contract aligned with current `dataset_1`-anchored market-data support rules, with deterministic mapping from scope mode to symbol set.

#### Scenario: Full refresh scope is resolved
- **WHEN** the system prepares a full market-data refresh for scope mode `core`, `100`, or `200`
- **THEN** it derives the requested symbols from one explicit supported-symbol source using the configured scope-to-universe mapping
- **THEN** it does not widen scope implicitly from provider responses or ad hoc operator input

### Requirement: Market-data operations SHALL expose explicit refresh outcome evidence
The system SHALL produce a structured outcome for each full-refresh run that identifies the selected scope mode, requested symbol scope, and resulting snapshot provenance.

#### Scenario: Full refresh completes or fails
- **WHEN** a full-refresh run finishes
- **THEN** the outcome identifies the selected scope mode, requested symbol scope, and provider used
- **THEN** the outcome includes explicit success or failure state plus snapshot provenance when a snapshot is created

#### Scenario: Full refresh success exposes minimum scope-aware evidence
- **WHEN** a full-refresh run completes successfully
- **THEN** the successful evidence includes `refresh_scope_mode`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, and `updated_prices`
- **THEN** the evidence remains deterministic for repeated runs against the same provider snapshot identity

#### Scenario: Full refresh failure exposes minimum scope-aware evidence
- **WHEN** a full-refresh run fails explicitly at refresh stage
- **THEN** the failure evidence includes `status`, `stage`, `status_code`, `error`, and `refresh_scope_mode`
- **THEN** the system does not report partial success for that refresh run

### Requirement: Market-data operations SHALL expose local operator entrypoints for refresh and sync workflows
The system SHALL expose explicit local operator entrypoints for market refresh and combined data sync without requiring a new public market-data API route in this slice, and those entrypoints SHALL support optional refresh scope mode selection.

#### Scenario: Operator runs local market refresh entrypoint
- **WHEN** an operator invokes the local market-refresh command workflow with or without a scope mode
- **THEN** the system executes the existing supported-universe refresh seam through `yfinance` for the resolved scope mode
- **THEN** the workflow returns structured outcome evidence for that refresh run

#### Scenario: Operator runs local combined sync entrypoint
- **WHEN** an operator invokes the local combined sync workflow with or without a scope mode
- **THEN** the system executes bootstrap and refresh in deterministic order
- **THEN** the refresh stage uses the resolved scope mode and the workflow reports explicit success or failure status for the overall operation

#### Scenario: Operator workflows fail fast
- **WHEN** a refresh or sync stage cannot complete safely
- **THEN** the workflow exits with explicit failure and actionable context
- **THEN** the system does not treat partially completed sync stages as a successful run
