# market-data-operations Specification

## Purpose
TBD - created by archiving change add-yfinance-market-data-operations. Update Purpose after archive.
## Requirements
### Requirement: Market-data operations SHALL provide a manual full-refresh workflow for the supported symbol universe
The system SHALL provide one explicit operator-facing workflow that refreshes market data for the current supported symbol universe using the existing `yfinance` ingestion path.

#### Scenario: Operator runs a full refresh successfully
- **WHEN** the operator triggers the market-data full-refresh workflow
- **THEN** the system requests the full current supported symbol universe through the existing `yfinance` provider path
- **THEN** the resulting market-data writes are persisted through the existing market-data ingestion contract rather than a second write path

### Requirement: Market-data operations SHALL use one explicit supported-symbol source
The system SHALL resolve full-refresh scope from one central supported-symbol contract aligned with current `dataset_1`-anchored market-data support rules.

#### Scenario: Full refresh scope is resolved
- **WHEN** the system prepares a full market-data refresh
- **THEN** it derives the requested symbols from one explicit supported-symbol source
- **THEN** it does not widen scope implicitly from provider responses or ad hoc operator input

### Requirement: Market-data operations SHALL fail fast on incomplete full-refresh results
The system SHALL reject a full-refresh run if any requested symbol cannot be fetched or normalized safely into the existing market-data contract.

#### Scenario: One symbol in the full refresh is unsafe
- **WHEN** one requested symbol in a full refresh is missing, unmappable, or lacks required pricing metadata
- **THEN** the full refresh fails explicitly
- **THEN** the system does not persist a partial full-refresh snapshot that omits the rejected symbol

### Requirement: Market-data operations SHALL expose explicit refresh outcome evidence
The system SHALL produce a structured outcome for each full-refresh run that identifies what scope was requested and what snapshot provenance resulted.

#### Scenario: Full refresh completes or fails
- **WHEN** a full-refresh run finishes
- **THEN** the outcome identifies the requested symbol scope and provider used
- **THEN** the outcome includes explicit success or failure state plus snapshot provenance when a snapshot is created
