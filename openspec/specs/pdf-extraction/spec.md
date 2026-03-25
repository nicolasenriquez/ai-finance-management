# pdf-extraction Specification

## Purpose
TBD - created by archiving change add-pdfplumber-extraction-for-dataset-1. Update Purpose after archive.
## Requirements
### Requirement: PDF extraction returns deterministic raw rows for stored uploads
The system SHALL provide a PDF extraction capability that reads an uploaded PDF from the configured storage root using its `storage_key` and returns deterministic row-wise raw extraction output for supported text-based broker statements.

#### Scenario: Stored dataset 1 PDF is extracted successfully
- **WHEN** a client requests extraction for a stored dataset 1 PDF using a valid `storage_key`
- **THEN** the system returns extraction metadata that identifies `pdfplumber` as the engine
- **THEN** the system returns the table columns in deterministic order
- **THEN** the system returns row-wise raw extraction output in source order without requiring PostgreSQL access

### Requirement: PDF extraction filters non-data table artifacts
The system SHALL remove repeated table headers and obvious footer artifacts before emitting extracted rows.

#### Scenario: Repeated headers are removed across pages
- **WHEN** the extracted table repeats the same header row on multiple pages
- **THEN** the system does not emit those repeated headers as data rows

#### Scenario: Footer artifacts are excluded from extracted rows
- **WHEN** the extracted table includes footer or non-transaction rows for dataset 1
- **THEN** the system excludes those rows from the emitted extraction output

### Requirement: PDF extraction preserves deterministic row provenance
The system SHALL preserve enough provenance for later validation and normalization work by recording a stable row identifier and source page for every emitted row.

#### Scenario: Extracted rows include provenance
- **WHEN** the system emits raw extracted rows
- **THEN** every row includes a deterministic `row_id`
- **THEN** every row includes `source_page`

### Requirement: PDF extraction fails explicitly for unsupported extraction inputs
The system SHALL fail explicitly instead of returning ambiguous or partial output when the stored upload cannot be resolved or no supported table shape can be extracted.

#### Scenario: Storage key does not resolve to a stored PDF
- **WHEN** a client requests extraction with a `storage_key` that does not exist under the configured upload root
- **THEN** the system rejects the request with an explicit client error

#### Scenario: No supported table shape is found
- **WHEN** the PDF does not yield the expected dataset 1 table structure after deterministic filtering
- **THEN** the system rejects extraction with an explicit failure explaining that no supported table data was found

### Requirement: PDF extraction keeps raw values separate from later normalization
The system SHALL preserve raw extracted string values in this slice and defer canonical mapping, numeric parsing, and persistence to later changes.

#### Scenario: Raw extraction output is emitted
- **WHEN** extraction succeeds
- **THEN** the emitted row fields preserve the raw source values needed for later mapping and parsing
- **THEN** the extraction result does not depend on normalization or persistence steps
