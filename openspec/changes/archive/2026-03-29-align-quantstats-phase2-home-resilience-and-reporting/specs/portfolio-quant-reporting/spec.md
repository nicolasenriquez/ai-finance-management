## ADDED Requirements

### Requirement: Portfolio quant reporting SHALL support bounded HTML tearsheet generation
The system SHALL generate QuantStats HTML tearsheets for explicitly requested scopes (`portfolio` or one explicit `instrument_symbol`) with deterministic parameter handling and explicit validation failures.

#### Scenario: HTML tearsheet is generated for portfolio scope
- **WHEN** a client requests quant reporting for `portfolio` scope with supported parameters
- **THEN** the API returns report metadata and a retrievable HTML report artifact reference
- **THEN** the response identifies report scope, generation timestamp, and selected benchmark context

#### Scenario: Unsupported report scope is rejected explicitly
- **WHEN** a client requests report generation with unsupported scope or malformed parameters
- **THEN** the API returns explicit client-facing validation failure
- **THEN** the service does not generate partial or implicit fallback reports

### Requirement: Quant report generation SHALL remain read-only over portfolio and market truth
Quant report requests SHALL consume persisted ledger and market data without mutating canonical records, ledger rows, lots, or market snapshots.

#### Scenario: Report generation performs no state mutation
- **WHEN** a quant report is generated
- **THEN** the service reads persisted state only
- **THEN** no canonical, ledger, lot, or market-data writes occur as side effects

### Requirement: Quant report artifacts SHALL use explicit lifecycle controls
The system SHALL enforce explicit lifecycle controls for generated report artifacts, including deterministic naming, bounded retention, and explicit retrieval failure when artifact state is unavailable.

#### Scenario: Expired or missing report artifact fails explicitly
- **WHEN** a client tries to retrieve an unavailable report artifact
- **THEN** the API returns explicit not-found or expired-state failure
- **THEN** the response does not return stale or unrelated report content
