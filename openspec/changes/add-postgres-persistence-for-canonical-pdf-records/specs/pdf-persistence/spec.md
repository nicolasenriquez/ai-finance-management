## ADDED Requirements

### Requirement: PDF persistence stores deduplicated source-document metadata for a stored upload
The system SHALL provide a persistence capability that accepts a stored PDF `storage_key`, resolves the uploaded document metadata, and stores a single deduplicated source-document record in PostgreSQL using the uploaded file SHA-256 hash as the document idempotency key.

#### Scenario: First persistence request creates a source document
- **WHEN** a client requests persistence for a valid stored dataset 1 PDF that has not been persisted before
- **THEN** the system creates a source-document record with deterministic upload metadata
- **THEN** the source-document record preserves the `storage_key`, original filename, page-count metadata, and SHA-256 hash
- **THEN** the persistence result indicates that a new source-document record was created

#### Scenario: Reprocessing the same stored PDF reuses the source document
- **WHEN** a client requests persistence again for a stored PDF whose SHA-256 hash is already present in PostgreSQL
- **THEN** the system reuses the existing source-document record
- **THEN** the system does not create a duplicate source-document row
- **THEN** the existing source-document row remains the canonical record for first-seen metadata
- **THEN** the persistence result indicates that the document already existed

### Requirement: PDF persistence stores canonical dataset 1 records with duplicate-safe behavior
The system SHALL persist trusted canonical dataset 1 records in PostgreSQL using deterministic record fingerprints derived from stable canonical business fields so rerunning the same source does not create duplicate stored records.

#### Scenario: First persistence request inserts canonical records
- **WHEN** a client requests persistence for a valid stored dataset 1 PDF whose normalized canonical records are not yet stored
- **THEN** the system inserts persisted canonical records for the supported dataset 1 event types
- **THEN** each stored record includes its deterministic record fingerprint
- **THEN** the persistence result reports how many canonical records were inserted

#### Scenario: Reprocessing the same canonical records skips duplicates safely
- **WHEN** a client requests persistence for a stored PDF whose canonical records are already present in PostgreSQL
- **THEN** the system skips inserting duplicate canonical records
- **THEN** the system does not create extra rows for records with matching deterministic fingerprints
- **THEN** the persistence result reports how many canonical records were skipped as duplicates

### Requirement: PDF persistence preserves raw values, canonical payload, and provenance for audit
The system SHALL preserve the normalized canonical payload, raw source values, and provenance metadata for every stored canonical record so later debugging, replay, and ledger derivation remain explainable.

#### Scenario: Persisted record retains audit evidence
- **WHEN** the system stores a canonical dataset 1 record
- **THEN** the stored row includes the canonical event type and normalized value payload
- **THEN** the stored row includes raw source values from normalization
- **THEN** the stored row includes provenance such as `table_name`, `row_id`, `row_index`, and `source_page`

### Requirement: PDF persistence records an explicit import job for each persistence attempt
The system SHALL create an import-job record for every successful committed persistence request so reruns remain auditable even when the source document and canonical records already exist.

#### Scenario: Persistence attempt is auditable
- **WHEN** a client requests persistence for a valid stored PDF
- **THEN** the system creates an import-job record linked to the relevant source document
- **THEN** the import-job record captures the persistence attempt timestamp and result summary
- **THEN** the response includes enough metadata to identify the import job that handled the request

### Requirement: PDF persistence depends on trusted normalization and fails transactionally
The system SHALL reuse trusted normalization output before writing to PostgreSQL and SHALL fail the persistence request without partial writes when canonical normalization fails or persistence cannot complete safely. Verification reporting SHALL remain a validation workflow and not a runtime write prerequisite for this capability.

#### Scenario: Normalization fails before persistence
- **WHEN** the source PDF cannot be normalized into valid canonical records
- **THEN** the system rejects the persistence request with an explicit failure
- **THEN** the system does not commit a partial source-document, import-job, or canonical-record write set

#### Scenario: Persistence does not require runtime verification
- **WHEN** canonical normalization succeeds for a valid stored PDF
- **THEN** the system may persist the canonical records without first requiring a verification report to pass
- **THEN** verification remains available as a separate validation workflow

#### Scenario: Database write fails during persistence
- **WHEN** PostgreSQL rejects part of the persistence transaction
- **THEN** the system reports an explicit failure
- **THEN** the system rolls back the persistence transaction
- **THEN** the database does not contain a partial import from the failed request
