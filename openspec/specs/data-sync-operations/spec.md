# data-sync-operations Specification

## Purpose
TBD - created by archiving change add-yfinance-data-sync-operations. Update Purpose after archive.
## Requirements
### Requirement: Data sync operations SHALL provide a local `dataset_1` bootstrap workflow
The system SHALL provide an operator-facing local workflow that executes the canonical `dataset_1` bootstrap pipeline (ingest -> persist -> ledger rebuild) through existing service boundaries.

#### Scenario: Operator runs dataset bootstrap successfully
- **WHEN** the operator triggers the `dataset_1` bootstrap workflow
- **THEN** the system executes ingestion, persistence, and ledger rebuild in the defined order
- **THEN** the workflow returns explicit success evidence including processed document/source identifiers

#### Scenario: Bootstrap step fails
- **WHEN** any bootstrap stage cannot complete safely
- **THEN** the workflow fails explicitly and exits non-zero
- **THEN** later bootstrap stages in that run are not executed

### Requirement: Data sync operations SHALL provide a local `yfinance` refresh workflow
The system SHALL provide an operator-facing local workflow that triggers market-data refresh through the existing `yfinance` service seam for one resolved supported-universe scope mode (`core`, `100`, or `200`).

#### Scenario: Operator runs market refresh successfully with explicit scope
- **WHEN** the operator triggers market refresh and passes a scope mode
- **THEN** the workflow invokes the market-data refresh orchestration for that selected scope mode
- **THEN** the run result includes provider/source identity, selected scope mode, and refresh counters

#### Scenario: Operator runs market refresh successfully with default scope
- **WHEN** the operator triggers market refresh without passing a scope mode
- **THEN** the workflow resolves the scope mode to `core`
- **THEN** the run result includes provider/source identity, selected scope mode, and refresh counters

#### Scenario: Market refresh rejects unsupported scope mode input
- **WHEN** the operator passes a refresh scope selector outside `core`, `100`, or `200`
- **THEN** the workflow fails explicitly before refresh execution starts
- **THEN** the failure response includes actionable validation context

#### Scenario: Refresh fails
- **WHEN** provider fetch or normalization fails for the selected refresh scope
- **THEN** the workflow reports explicit failure with actionable context
- **THEN** the workflow does not report partial success for the failed run

#### Scenario: Refresh failure preserves minimum scope-aware evidence
- **WHEN** market refresh fails at refresh stage
- **THEN** failure evidence includes `status`, `stage`, `status_code`, `error`, and `refresh_scope_mode`
- **THEN** the selected or default scope mode remains visible to operators for staged onboarding diagnostics

### Requirement: Data sync operations SHALL provide a deterministic combined local sync workflow
The system SHALL provide a combined local sync workflow that runs bootstrap and market refresh in one deterministic sequence and propagates the selected or default refresh scope mode to the refresh stage.

#### Scenario: Combined sync succeeds
- **WHEN** the operator triggers combined local sync with or without a refresh scope mode
- **THEN** bootstrap executes before market refresh
- **THEN** the refresh stage uses the resolved scope mode and the workflow reports combined success evidence for both stages

#### Scenario: Combined sync success preserves minimum scope-aware refresh evidence
- **WHEN** combined local sync completes successfully
- **THEN** nested market-refresh evidence includes `refresh_scope_mode`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, and `updated_prices`
- **THEN** operators can compare staged onboarding runs (`core`, `100`, `200`) using structured output only

#### Scenario: Combined sync fails in bootstrap stage
- **WHEN** bootstrap fails during combined sync
- **THEN** market refresh is not executed in that run
- **THEN** the workflow returns explicit failure state for the combined operation
