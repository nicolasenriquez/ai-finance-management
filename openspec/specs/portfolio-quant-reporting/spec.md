# portfolio-quant-reporting Specification

## Purpose
TBD - created by archiving change align-quantstats-phase2-home-resilience-and-reporting. Update Purpose after archive.
## Requirements
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

### Requirement: Quant reporting SHALL support simulation-aware diagnostics context
Quant reporting contracts SHALL support simulation-aware diagnostics metadata when Monte Carlo context is requested and safely computable.

#### Scenario: Simulation-aware report metadata is returned on successful generation
- **WHEN** a client generates a quant report with simulation context enabled for a supported scope
- **THEN** the report metadata includes simulation parameter context and summary diagnostics identifiers
- **THEN** retrieval contracts expose that simulation context as part of artifact interpretation metadata

### Requirement: Simulation context omission SHALL be explicit and non-fabricated
When simulation diagnostics cannot be computed safely, report contracts SHALL expose explicit omission metadata instead of fabricated simulation outputs.

#### Scenario: Simulation omission is explicit without blocking core report generation
- **WHEN** simulation diagnostics are unavailable for the requested report context
- **THEN** the report workflow returns explicit simulation-omission metadata with factual reason
- **THEN** core report lifecycle and non-simulation diagnostics remain valid if their contracts are satisfied

### Requirement: Simulation-aware report lifecycle SHALL remain explicit and deterministic
Report lifecycle states SHALL include deterministic simulation-context status to preserve explicit readiness/error semantics.

#### Scenario: Retrieval reflects simulation-context lifecycle state explicitly
- **WHEN** a client retrieves a generated quant report artifact
- **THEN** the payload includes explicit lifecycle status for simulation context (`ready`, `unavailable`, or `error`)
- **THEN** clients do not infer simulation availability from missing fields

### Requirement: Quant report diagnostics SHALL include health-summary context
Quant reporting contracts SHALL include a compact health-summary interpretation context so users can relate advanced diagnostics to overall portfolio condition.

#### Scenario: Retrieved report includes health-summary metadata and caveats
- **WHEN** a client retrieves a report artifact with available health synthesis context
- **THEN** the payload includes health label/score, profile posture, and top risk/support drivers used for interpretation
- **THEN** the response includes explicit caveats when health context is partial due to insufficient data or omitted benchmark fields
