## ADDED Requirements

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
The system SHALL provide an operator-facing local workflow that triggers supported-universe market-data refresh through the existing `yfinance` service seam.

#### Scenario: Operator runs market refresh successfully
- **WHEN** the operator triggers market refresh
- **THEN** the workflow invokes the supported-universe refresh through existing market-data orchestration
- **THEN** the run result includes provider/source identity and refresh counters

#### Scenario: Refresh fails
- **WHEN** provider fetch or normalization fails for the refresh scope
- **THEN** the workflow reports explicit failure with actionable context
- **THEN** the workflow does not report partial success for the failed run

### Requirement: Data sync operations SHALL provide a deterministic combined local sync workflow
The system SHALL provide a combined local sync workflow that runs bootstrap and market refresh in one deterministic sequence.

#### Scenario: Combined sync succeeds
- **WHEN** the operator triggers combined local sync
- **THEN** bootstrap executes before market refresh
- **THEN** the workflow reports combined success evidence for both stages

#### Scenario: Combined sync fails in bootstrap stage
- **WHEN** bootstrap fails during combined sync
- **THEN** market refresh is not executed in that run
- **THEN** the workflow returns explicit failure state for the combined operation
