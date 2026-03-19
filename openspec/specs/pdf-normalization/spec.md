# pdf-normalization Specification

## Purpose
TBD - created by archiving change add-dataset-1-canonical-normalization-and-verification. Update Purpose after archive.
## Requirements
### Requirement: PDF normalization returns canonical records for stored dataset 1 uploads
The system SHALL provide a normalization capability that reads a stored dataset 1 PDF through its `storage_key`, reuses deterministic extraction output, and returns canonical typed records without requiring PostgreSQL access.

#### Scenario: Stored dataset 1 PDF is normalized successfully
- **WHEN** a client requests normalization for a valid stored dataset 1 PDF
- **THEN** the system returns canonical records for the supported dataset 1 event types
- **THEN** the system preserves deterministic output order
- **THEN** the normalization flow completes without requiring database connectivity

### Requirement: PDF normalization preserves raw values and provenance alongside typed fields
The system SHALL preserve the extracted raw source values and row provenance while emitting typed canonical fields so later persistence and debugging remain explainable.

#### Scenario: Normalized records include audit context
- **WHEN** the system emits normalized records
- **THEN** each record includes its raw source values
- **THEN** each record includes deterministic provenance such as `table_name`, `row_id`, and `source_page`
- **THEN** each record includes typed canonical fields separate from raw values

### Requirement: PDF normalization parses dataset 1 values deterministically
The system SHALL normalize dataset 1 dates, currency strings, decimal-comma numbers, and blank cells using deterministic rules.

#### Scenario: Locale-specific values are normalized
- **WHEN** a dataset 1 row contains locale-formatted dates, money values, quantities, or blanks
- **THEN** the system converts those values into the expected typed canonical representation
- **THEN** blank source cells become `null`
- **THEN** no missing value is inferred beyond what the source row determines explicitly

### Requirement: PDF normalization rejects ambiguous or invalid rows explicitly
The system SHALL fail explicitly when a row cannot be mapped or validated deterministically under the canonical schema.

#### Scenario: Row violates normalization invariants
- **WHEN** a row has an ambiguous or invalid combination of fields for its canonical event type
- **THEN** the system rejects the row with an actionable validation error
- **THEN** the system does not silently coerce the row into a canonical record

