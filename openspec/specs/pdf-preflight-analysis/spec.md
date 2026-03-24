# pdf-preflight-analysis Specification

## Purpose

Define the preflight analysis contract that classifies PDF extractability before
extraction and returns diagnostic metadata for explicit, fail-fast decisions.

## Requirements

### Requirement: Preflight returns an explicit extractability status
The system SHALL provide a PDF preflight capability that inspects a submitted PDF and returns a machine-readable extractability status before extraction begins.

#### Scenario: Text PDF is extractable
- **WHEN** a non-encrypted PDF contains enough extractable text for the current pipeline
- **THEN** the system returns an `extractable` status
- **THEN** the response includes a clear message that extraction can proceed

### Requirement: Encrypted PDFs are rejected during preflight
The system SHALL detect encrypted PDFs and mark them as not extractable by the current pipeline.

#### Scenario: Encrypted document is submitted
- **WHEN** the submitted PDF is encrypted
- **THEN** the system returns an `encrypted` status
- **THEN** the response explains that extraction cannot proceed without decryption support

### Requirement: Likely scanned PDFs require OCR
The system SHALL detect PDFs with insufficient extractable text and mark them as requiring OCR when OCR support is not enabled.

#### Scenario: Low-text document is submitted
- **WHEN** the submitted PDF has no extractable text or falls below the configured text threshold
- **THEN** the system returns an `ocr_required` status
- **THEN** the response explains that extraction stops because OCR is not supported

### Requirement: Preflight reports diagnostic metadata
The system SHALL return enough metadata for clients and tests to understand why a document was or was not extractable.

#### Scenario: Preflight completes
- **WHEN** the system evaluates a PDF
- **THEN** the response includes page count when it can be determined safely
- **THEN** the response includes extracted text character count
- **THEN** the response includes whether the document was encrypted
