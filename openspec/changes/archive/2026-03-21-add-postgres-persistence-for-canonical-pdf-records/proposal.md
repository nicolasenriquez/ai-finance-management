## Why

The repository now ingests PDFs, runs preflight, extracts deterministic rows, normalizes them into canonical records, and verifies those records against the golden set, but it still lacks the PostgreSQL system-of-record layer required by the MVP. This change is needed now because persistence, idempotency, and provenance retention are the prerequisite boundary before ledger modeling, analytics APIs, or frontend work can proceed safely.

## What Changes

- Add a PostgreSQL persistence capability for uploaded PDF metadata and normalized canonical dataset 1 records.
- Define database models and Alembic migrations for source documents, import jobs, and persisted canonical records with audit-ready provenance.
- Enforce document-level idempotency using the uploaded file SHA-256 hash.
- Enforce duplicate-safe transaction persistence using deterministic, versioned fingerprints scoped to the current PDF source system and derived from stable canonical business fields plus provenance fallback for dataset 1 event types.
- Reuse the existing ingestion and normalization pipeline rather than duplicating parsing logic inside the persistence layer, while keeping verification as a validation workflow rather than a runtime write prerequisite.
- Depend on the durable ingestion metadata manifest stored beside each uploaded PDF so persistence can recover upload metadata from `storage_key` without reparsing or inventing missing fields.
- Record `import_job` rows only for successful committed persistence runs, while treating failed attempts as structured-log events in this slice.
- Keep first-seen `source_document` metadata canonical when the same PDF bytes are uploaded again.
- Store a small structured query surface for persisted canonical records while preserving the full canonical payload, raw values, and provenance as JSON for audit and replay.
- Enforce duplicate safety with database uniqueness constraints and conflict-safe insert-or-reuse behavior so concurrent reruns do not create duplicate rows.
- Treat the stored PDF plus durable ingestion manifest as the replay source of truth for this phase; PostgreSQL persistence stores trusted canonical audit records but does not replace source-file retention.
- Add integration coverage for clean first-write behavior, duplicate document reprocessing, and duplicate transaction reprocessing.
- Keep this slice explicitly out of scope for portfolio analytics, lot derivation, market data storage, and frontend changes.

## Capabilities

### New Capabilities
- `pdf-persistence`: Persist uploaded document metadata and canonical dataset 1 records in PostgreSQL with duplicate-safe reprocessing behavior and preserved provenance.

### Modified Capabilities
- None.

## Impact

- Adds a new persistence-oriented feature slice under `app/` plus SQLAlchemy models, services, and tests.
- Introduces real Alembic schema changes for the first time beyond the empty initial migration baseline.
- Adds PostgreSQL-backed integration behavior and validation expectations for rerunning the same source PDF safely.
- Reuses existing `pdf_ingestion`, `pdf_normalization`, and verification-adjacent contracts as upstream dependencies without changing their public requirements.
- Relies on the newly durable `pdf_ingestion` sidecar metadata manifest as an upstream prerequisite for source-document persistence.
- Freezes first-pass persistence decisions for duplicate-safe fingerprints, first-seen document metadata, success-only import-job recording, and the minimum structured persistence surface.
- Freezes first-pass persistence decisions for source-scoped fingerprint versioning, concurrency-safe uniqueness constraints, and replay dependence on stored source files plus manifests.
- Requires documentation updates in validation and delivery-history files once implemented.
