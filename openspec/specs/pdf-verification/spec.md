# pdf-verification Specification

## Purpose
TBD - created by archiving change add-dataset-1-canonical-normalization-and-verification. Update Purpose after archive.
## Requirements
### Requirement: PDF verification emits a deterministic dataset 1 report
The system SHALL provide a verification capability that compares dataset 1 normalized output against the checked-in golden set and emits a deterministic machine-readable report.

#### Scenario: Verification report is generated
- **WHEN** a client requests verification for a valid stored dataset 1 PDF
- **THEN** the system returns a report with deterministic summary counts
- **THEN** the report indicates whether verification passed or failed
- **THEN** the report can be produced without requiring PostgreSQL access

### Requirement: PDF verification records row-level and field-level mismatch evidence
The system SHALL include actionable evidence for every detected mismatch so regressions can be diagnosed quickly.

#### Scenario: Verification finds mismatched values
- **WHEN** a normalized record differs from the expected dataset 1 contract
- **THEN** the report includes the affected row or record identifier
- **THEN** the report includes the affected field name
- **THEN** the report includes expected and actual values together with available provenance

### Requirement: PDF verification depends on trusted normalization output
The system SHALL stop with an explicit failure when canonical normalization cannot produce valid records for verification.

#### Scenario: Normalization fails before verification
- **WHEN** the source PDF cannot be normalized into valid canonical records
- **THEN** the system rejects verification with an explicit error
- **THEN** it does not emit a misleading verification success result

