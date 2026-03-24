# pdf-ingestion Specification

## Purpose

Define the PDF ingestion contract for uploading broker statements, enforcing safe
input limits, writing accepted files to controlled storage, and returning
deterministic metadata plus preflight analysis results.

## Requirements

### Requirement: PDF ingestion accepts multipart uploads
The system SHALL provide a PDF ingestion endpoint that accepts a broker statement as a multipart file upload and returns a typed ingestion result.

#### Scenario: Valid PDF upload is accepted
- **WHEN** a client uploads a valid PDF file through the ingestion endpoint
- **THEN** the system returns a success response with document metadata and preflight analysis

### Requirement: PDF ingestion enforces upload constraints
The system SHALL reject uploads that do not satisfy configured MIME, file-size, or page-count constraints before extraction begins.

#### Scenario: Non-PDF upload is rejected
- **WHEN** the uploaded file is not identified as a PDF by request metadata or PDF parsing
- **THEN** the system rejects the request with an explicit client error

#### Scenario: Oversized PDF upload is rejected
- **WHEN** the uploaded PDF exceeds the configured maximum byte size
- **THEN** the system rejects the request with an explicit client error

#### Scenario: Over-page-limit PDF upload is rejected
- **WHEN** the uploaded PDF exceeds the configured maximum page count
- **THEN** the system rejects the request with an explicit client error

### Requirement: PDF ingestion records deterministic file metadata
The system SHALL compute deterministic metadata for every accepted PDF upload so later phases can audit and persist the document safely.

#### Scenario: Accepted upload returns document metadata
- **WHEN** a PDF upload is accepted
- **THEN** the response includes a generated document identifier
- **THEN** the response includes the file SHA-256 hash
- **THEN** the response includes the original filename and page count
- **THEN** the response includes a relative `storage_key` for the stored file
- **THEN** the response does not expose an absolute filesystem path

### Requirement: PDF ingestion stores accepted files safely on disk
The system SHALL store accepted PDFs under a configured storage root using safe generated filenames rather than client-provided paths.

#### Scenario: Accepted PDF is written to configured storage
- **WHEN** a PDF upload passes validation
- **THEN** the system writes the PDF bytes to the configured storage root
- **THEN** the stored filename is derived from system-generated metadata rather than the original filename

### Requirement: PDF ingestion ships with conservative default limits
The system SHALL provide default PDF upload limits of `10 MB` and `50` pages until configuration overrides them.

#### Scenario: Ingestion uses initial default limits
- **WHEN** the application starts without explicit ingestion limit overrides
- **THEN** the maximum upload size defaults to `10 MB`
- **THEN** the maximum page count defaults to `50`

### Requirement: PDF ingestion invokes preflight automatically
The system SHALL run the existing PDF preflight analysis as part of ingestion and include the resulting extractability decision in the ingestion response.

#### Scenario: Accepted upload reports preflight result
- **WHEN** a PDF upload is accepted and analyzed
- **THEN** the response includes the current preflight status and diagnostic metadata for that document

### Requirement: PDF ingestion remains independent from database persistence
The system SHALL complete the upload, storage, and preflight flow without requiring PostgreSQL connectivity or database writes.

#### Scenario: Ingestion succeeds without database access
- **WHEN** the backend handles a valid PDF upload in an environment without local PostgreSQL
- **THEN** the upload flow completes using filesystem storage and in-process preflight only
